import json
import random
import time
from asyncio import Lock, sleep
from copy import deepcopy
from json import load, dump, loads
from os.path import dirname, join, exists
from traceback import format_exc

import hoshino
from hoshino import priv, util
from hoshino.typing import NoticeSession, MessageSegment
from hoshino.util import pic2b64
from nonebot import get_bot, on_command

from .aiorequests import get
from .create_img import generate_info_pic, generate_support_pic
from .geetest import public_address
from .jjchistory import *
from .pcrclient import pcrclient, ApiException, bsdkclient
from .safeservice import SafeService

sv_help = '''
[竞技场绑定 uid] 绑定竞技场排名变动推送，默认双场均启用，仅排名降低时推送
[竞技场查询 (uid)] 查询竞技场简要信息
[停止竞技场订阅] 停止战斗竞技场排名变动推送
[停止公主竞技场订阅] 停止公主竞技场排名变动推送
[启用竞技场订阅] 启用战斗竞技场排名变动推送
[启用公主竞技场订阅] 启用公主竞技场排名变动推送
[竞技场历史] 查询战斗竞技场变化记录（战斗竞技场订阅开启有效，可保留10条）
[公主竞技场历史] 查询公主竞技场变化记录（公主竞技场订阅开启有效，可保留10条）
[删除竞技场订阅] 删除竞技场排名变动推送绑定
[竞技场订阅状态] 查看排名变动推送绑定状态
[详细查询 (uid)] 查询账号详细信息
[查询群数] 查询bot所在群的数目
[查询竞技场订阅数] 查询绑定账号的总数量
[查询头像框] 查看自己设置的详细查询里的角色头像框
[更换头像框] 更换详细查询生成的头像框，默认彩色
[清空竞技场订阅] 清空所有绑定的账号(仅限主人)
'''.strip()

sv = SafeService('竞技场推送', help_=sv_help, bundle='pcr查询')


@sv.on_fullmatch('竞技场帮助', only_to_me=False)
async def send_jjchelp(bot, ev):
    await bot.send(ev, f'{sv_help}')


curpath = dirname(__file__)
config = join(curpath, 'binds.json')
root = {
    'arena_bind': {}
}

cache = {}
client = None
lck = Lock()

if exists(config):
    with open(config) as fp:
        root = load(fp)

binds = root['arena_bind']

captcha_lck = Lock()

with open(join(curpath, 'account.json')) as fp:
    acinfo = load(fp)

# 数据库对象初始化
JJCH = JJCHistoryStorage()

bot = get_bot()
validate = None
validating = False
acfirst = False


async def sendToAdmin(msg):
    sid = [x for x in hoshino.get_self_ids()]  # 获取bot账号列表
    if acinfo['admin'] == 0:
        bot.logger.error('captcha is required while admin qq is not set')
    else:
        if len(sid) > 0:  # 若bot账号数量大于0，则随机选择一个号向管理员QQ发送私聊消息（记得先加bot好友！）
            sid = random.choice(sid)
            try:
                await bot.send_private_msg(
                    self_id=sid,
                    user_id=acinfo['admin'],
                    message=msg
                )
            except Exception as e:
                hoshino.logger.error(f'向管理员QQ发送私聊验证码消息失败：{type(e)}')


async def captchaVerifierV2(gt, challenge, userid):
    global validating

    validating = True
    captcha_cnt = 0
    while captcha_cnt < 5:
        captcha_cnt += 1
        try:
            print(f'测试新版自动过码中，当前尝试第{captcha_cnt}次。')

            await sleep(1)
            uuid = loads(await (await get(url="https://pcrd.tencentbot.top/geetest")).content)["uuid"]
            print(f'uuid={uuid}')

            ccnt = 0
            while ccnt < 3:
                ccnt += 1
                await sleep(5)
                res = await (await get(url=f"https://pcrd.tencentbot.top/check/{uuid}")).content
                res = loads(res)
                if "queue_num" in res:
                    nu = res["queue_num"]
                    print(f"queue_num={nu}")
                    tim = min(int(nu), 3) * 5
                    print(f"sleep={tim}")
                    await sleep(tim)
                else:
                    info = res["info"]
                    if info in ["fail", "url invalid"]:
                        break
                    elif info == "in running":
                        await sleep(5)
                    else:
                        print(f'info={info}')
                        validating = False
                        return info["challenge"], info["gt_user_id"], info["validate"]
        except:
            pass

    await sendToAdmin(
        f'自动过码多次尝试失败，可能为服务器错误，自动切换为手动。\n确实服务器无误后，可发送/pcrval重新触发自动过码。')
    validate = await captchaVerifier(gt, challenge, userid)
    validating = False
    return challenge, userid, validate


async def captchaVerifier(gt, challenge, userid):
    global acfirst
    if not acfirst:
        await captcha_lck.acquire()
        acfirst = True

    online_url_head = "https://cc004.github.io/geetest/geetest.html"
    local_url_head = f"{public_address}/geetest"
    url = f"?captcha_type=1&challenge={challenge}&gt={gt}&userid={userid}&gs=1"
    await sendToAdmin(
        f'pcr账号登录需要验证码，请完成以下链接中的验证内容后将第一行validate=后面的内容复制，'
        f'并用指令/pcrval xxxx将内容发送给机器人完成验证'
        f'\n验证链接头：{local_url_head}链接{url}，备用链接头：{online_url_head}'
        f'\n为避免tx网页安全验证使验证码过期，请手动拼接链接头和链接'
    )

    await captcha_lck.acquire()
    return validate


async def errlogger(msg):
    await bot.send_private_msg(
        user_id=acinfo['admin'],
        message=f'pcrjjc2登录错误：{msg}'
    )


bclient = bsdkclient(acinfo, captchaVerifierV2, errlogger)
client = pcrclient(bclient)

qlck = Lock()

# 头像框设置文件不存在就创建文件，并且默认彩色
current_dir = os.path.join(os.path.dirname(__file__), 'frame.json')
if not os.path.exists(current_dir):
    data = {
        "default_frame": "color.png",
        "customize": {}
    }
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


async def query(id: str):
    if validating:
        raise ApiException('账号被风控，请联系管理员输入验证码并重新登录', -1)
    async with qlck:
        while client.shouldLogin:
            await client.login()
        res = (await client.callapi('/profile/get_profile', {
            'target_viewer_id': int(id)
        }))
        return res


def save_binds():
    with open(config, 'w') as fp:
        dump(root, fp, indent=4)


@sv.on_fullmatch('查询群数', only_to_me=False)
async def group_num(bot, ev):
    global binds, lck
    gid = int(ev['group_id'])

    async with lck:
        for sid in hoshino.get_self_ids():
            gl = await bot.get_group_list(self_id=sid)
            gl = [g['group_id'] for g in gl]
            try:
                await bot.send_group_msg(
                    self_id=sid,
                    group_id=gid,
                    message=f"本Bot目前正在为【{len(gl)}】个群服务"
                )
                break
            except Exception as e:
                sv.logger.info(f'bot账号{sid}不在群{gid}中，将忽略该消息')


@sv.on_fullmatch('查询竞技场订阅数', only_to_me=False)
async def pcrjjc_number(bot, ev):
    global binds, lck

    async with lck:
        await bot.send(ev, f'当前竞技场已订阅的账号数量为【{len(binds)}】个')


@sv.on_fullmatch('清空竞技场订阅', only_to_me=False)
async def pcrjjc_del(bot, ev):
    global binds, lck

    async with lck:
        if not priv.check_priv(ev, priv.SUPERUSER):
            await bot.send(ev, '抱歉，您的权限不足，只有bot主人才能进行该操作！')
            return
        else:
            num = len(binds)
            bind_cache = deepcopy(binds)
            for uid in bind_cache:
                JJCH._remove(binds[uid]['id'])
            binds.clear()
            save_binds()
            await bot.send(ev, f'已清空全部【{num}】个已订阅账号！')


@sv.on_rex(r'^竞技场绑定 ?(\d{13})$')
async def on_arena_bind(bot, ev):
    global binds, lck

    async with lck:
        uid = str(ev['user_id'])
        last = binds[uid] if uid in binds else None

        binds[uid] = {
            'id': ev['match'].group(1),
            'uid': uid,
            'gid': str(ev['group_id']),
            'arena_on': last is None or last['arena_on'],
            'grand_arena_on': last is None or last['grand_arena_on'],
        }
        save_binds()

    await bot.finish(ev, '竞技场绑定成功', at_sender=True)


@sv.on_rex(r'^竞技场查询 ?(\d{13})?$')
async def on_query_arena(bot, ev):
    global binds, lck

    robj = ev['match']
    id = robj.group(1)

    async with lck:
        if id == None:
            uid = str(ev['user_id'])
            if not uid in binds:
                await bot.finish(ev, '您还未绑定竞技场', at_sender=True)
                return
            else:
                id = binds[uid]['id']
        try:
            res = await query(id)

            last_login_time = int(res['user_info']['last_login_time'])
            last_login_date = time.localtime(last_login_time)
            last_login_str = time.strftime('%Y-%m-%d %H:%M:%S', last_login_date)

            await bot.finish(ev,
                             f'''昵称：{util.filt_message(str(res['user_info']["user_name"]))}
jjc排名：{res['user_info']["arena_rank"]}
pjjc排名：{res['user_info']["grand_arena_rank"]}
最后登录：{last_login_str}''', at_sender=False)
        except ApiException as e:
            await bot.finish(ev, f'查询出错，{e}', at_sender=True)


@sv.on_prefix('竞技场历史')
async def send_arena_history(bot, ev):
    '''
    竞技场历史记录
    '''
    global binds, lck
    uid = str(ev['user_id'])
    if uid not in binds:
        await bot.send(ev, '未绑定竞技场', at_sender=True)
    else:
        ID = binds[uid]['id']
        msg = f'\n{JJCH._select(ID, 1)}'
        await bot.finish(ev, msg, at_sender=True)


@sv.on_prefix('公主竞技场历史')
async def send_parena_history(bot, ev):
    global binds, lck
    uid = str(ev['user_id'])
    if uid not in binds:
        await bot.send(ev, '未绑定竞技场', at_sender=True)
    else:
        ID = binds[uid]['id']
        msg = f'\n{JJCH._select(ID, 0)}'
        await bot.finish(ev, msg, at_sender=True)


@sv.on_rex(r'^详细查询 ?(\d{13})?$')
async def on_query_arena_all(bot, ev):
    global binds, lck

    robj = ev['match']
    id = robj.group(1)
    uid = str(ev['user_id'])

    async with lck:
        if id == None:
            if not uid in binds:
                await bot.finish(ev, '您还未绑定竞技场', at_sender=True)
                return
            else:
                id = binds[uid]['id']
        try:
            res = await query(id)
            sv.logger.info('开始生成竞技场查询图片...')  # 通过log显示信息
            # result_image = await generate_info_pic(res, cx)
            result_image = await generate_info_pic(res, uid)
            result_image = pic2b64(result_image)  # 转base64发送，不用将图片存本地
            result_image = MessageSegment.image(result_image)
            result_support = await generate_support_pic(res, uid)
            result_support = pic2b64(result_support)  # 转base64发送，不用将图片存本地
            result_support = MessageSegment.image(result_support)
            sv.logger.info('竞技场查询图片已准备完毕！')
            try:
                await bot.finish(ev, f"\n{str(result_image)}\n{result_support}", at_sender=True)
            except Exception as e:
                sv.logger.info("do nothing")
        except ApiException as e:
            await bot.finish(ev, f'查询出错，{e}', at_sender=True)


@sv.on_rex('(启用|停止)(公主)?竞技场订阅')
async def change_arena_sub(bot, ev):
    global binds, lck

    key = 'arena_on' if ev['match'].group(2) is None else 'grand_arena_on'
    uid = str(ev['user_id'])

    async with lck:
        if not uid in binds:
            await bot.send(ev, '您还未绑定竞技场', at_sender=True)
        else:
            binds[uid][key] = ev['match'].group(1) == '启用'
            save_binds()
            await bot.finish(ev, f'{ev["match"].group(0)}成功', at_sender=True)


@on_command('/pcrval')
async def validate(session):
    global binds, lck, validate
    if session.ctx['user_id'] == acinfo['admin']:
        validate = session.ctx['message'].extract_plain_text().strip()[8:]
        captcha_lck.release()


def delete_arena(uid):
    '''
    订阅删除方法
    '''
    JJCH._remove(binds[uid]['id'])
    binds.pop(uid)
    save_binds()


@sv.on_prefix('删除竞技场订阅')
async def delete_arena_sub(bot, ev):
    global binds, lck

    uid = str(ev['user_id'])

    if ev.message[0].type == 'at':
        if not priv.check_priv(ev, priv.SUPERUSER):
            await bot.finish(ev, '删除他人订阅请联系维护', at_sender=True)
            return
        uid = str(ev.message[0].data['qq'])
    elif len(ev.message) == 1 and ev.message[0].type == 'text' and not ev.message[0].data['text']:
        uid = str(ev['user_id'])

    if not uid in binds:
        await bot.finish(ev, '未绑定竞技场', at_sender=True)
        return

    async with lck:
        delete_arena(uid)

    await bot.finish(ev, '删除竞技场订阅成功', at_sender=True)


@sv.on_fullmatch('竞技场订阅状态')
async def send_arena_sub_status(bot, ev):
    global binds, lck
    uid = str(ev['user_id'])

    if not uid in binds:
        await bot.send(ev, '您还未绑定竞技场', at_sender=True)
    else:
        info = binds[uid]
        await bot.finish(ev,
                         f'''
    当前竞技场绑定ID：{info['id']}
    竞技场订阅：{'开启' if info['arena_on'] else '关闭'}
    公主竞技场订阅：{'开启' if info['grand_arena_on'] else '关闭'}''', at_sender=True)


@sv.scheduled_job('interval', minutes=1)  # minutes是刷新频率，可按自身服务器性能输入其他数值，可支持整数、小数
async def on_arena_schedule():
    global cache, binds, lck
    bot = get_bot()

    bind_cache = {}

    async with lck:
        bind_cache = deepcopy(binds)

    for uid in bind_cache:
        info = bind_cache[uid]
        try:
            sv.logger.info(f'querying {info["id"]} for {info["uid"]}')
            res = await query(info['id'])
            res = (res['user_info']['arena_rank'], res['user_info']['grand_arena_rank'])

            if uid not in cache:
                cache[uid] = res
                continue

            last = cache[uid]
            cache[uid] = res

            # 两次间隔排名变化且开启了相关订阅就记录到数据库
            if res[0] != last[0] and info['arena_on']:
                JJCH._add(int(info["id"]), 1, last[0], res[0])
                JJCH._refresh(int(info["id"]), 1)
                sv.logger.info(f"{info['id']}: JJC {last[0]}->{res[0]}")
            if res[1] != last[1] and info['grand_arena_on']:
                JJCH._add(int(info["id"]), 0, last[1], res[1])
                JJCH._refresh(int(info["id"]), 0)
                sv.logger.info(f"{info['id']}: PJJC {last[1]}->{res[1]}")

            if res[0] > last[0] and info['arena_on']:
                for sid in hoshino.get_self_ids():
                    try:
                        await bot.send_group_msg(
                            self_id=sid,
                            group_id=int(info['gid']),
                            message=f'[CQ:at,qq={info["uid"]}]jjc：{last[0]}->{res[0]} ▼{res[0] - last[0]}'
                        )
                        break
                    except Exception as e:
                        gid = int(info['gid'])
                        sv.logger.info(f'bot账号{sid}不在群{gid}中，将忽略该消息')

            if res[1] > last[1] and info['grand_arena_on']:
                for sid in hoshino.get_self_ids():
                    try:
                        await bot.send_group_msg(
                            self_id=sid,
                            group_id=int(info['gid']),
                            message=f'[CQ:at,qq={info["uid"]}]pjjc：{last[1]}->{res[1]} ▼{res[1] - last[1]}'
                        )
                        break
                    except Exception as e:
                        gid = int(info['gid'])
                        sv.logger.info(f'bot账号{sid}不在群{gid}中，将忽略该消息')

        except ApiException as e:
            sv.logger.info(f'对{info["id"]}的检查出错\n{format_exc()}')
            if e.code == 6:
                async with lck:
                    delete_arena(uid)
                sv.logger.info(f'已经自动删除错误的uid={info["id"]}')
        except:
            sv.logger.info(f'对{info["id"]}的检查出错\n{format_exc()}')


@sv.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    global lck, binds
    uid = str(session.ctx['user_id'])
    gid = str(session.ctx['group_id'])
    bot = get_bot()
    if uid not in binds:
        return
    async with lck:
        bind_cache = deepcopy(binds)
        info = bind_cache[uid]
        if info['gid'] == gid:
            delete_arena(uid)
            await bot.send_group_msg(
                group_id=int(info['gid']),
                message=f'{uid}退群了，已自动删除其绑定在本群的竞技场订阅推送'
            )


@sv.on_prefix('竞技场换头像框', '更换竞技场头像框', '更换头像框')
async def change_frame(bot, ev):
    user_id = ev.user_id
    frame_tmp = ev.message.extract_plain_text()
    path = os.path.join(os.path.dirname(__file__), 'img/frame/')
    frame_list = os.listdir(path)
    if not frame_list:
        await bot.finish(ev, 'img/frame/路径下没有任何头像框，请联系维护组检查目录')
    if frame_tmp not in frame_list:
        msg = f'文件名输入错误，命令样例：\n更换头像框 color.png\n目前可选文件有：\n' + '\n'.join(frame_list)
        await bot.finish(ev, msg)
    data = {str(user_id): frame_tmp}
    current_dir = os.path.join(os.path.dirname(__file__), 'frame.json')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    f_data['customize'] = data
    with open(current_dir, 'w', encoding='UTF-8') as rf:
        json.dump(f_data, rf, indent=4, ensure_ascii=False)
    await bot.send(ev, f'已成功选择头像框:{frame_tmp}')
    frame_path = os.path.join(os.path.dirname(__file__), f'img/frame/{frame_tmp}')
    msg = MessageSegment.image(f'file:///{os.path.abspath(frame_path)}')
    await bot.send(ev, msg)


# see_a_see（
@sv.on_fullmatch('查竞技场头像框', '查询竞技场头像框', '查询头像框')
async def see_a_see_frame(bot, ev):
    user_id = str(ev.user_id)
    current_dir = os.path.join(os.path.dirname(__file__), 'frame.json')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    id_list = list(f_data['customize'].keys())
    if user_id not in id_list:
        frame_tmp = f_data['default_frame']
    else:
        frame_tmp = f_data['customize'][user_id]
    path = os.path.join(os.path.dirname(__file__), f'img/frame/{frame_tmp}')
    msg = MessageSegment.image(f'file:///{os.path.abspath(path)}')
    await bot.send(ev, msg)
