from json import load, dump
from tkinter.messagebox import NO
from nonebot import get_bot, on_command
from hoshino import priv
from hoshino.typing import NoticeSession
from .pcrclient import pcrclient, ApiException
from asyncio import Lock
from os.path import dirname, join, exists
from copy import deepcopy
from traceback import format_exc
from .safeservice import SafeService
from .playerpref import decryptxml
from ..priconne import chara
import time

sv_help = '''
[竞技场绑定 uid] 绑定竞技场排名变动推送，默认双场均启用，仅排名降低时推送
[竞技场查询 (uid)] 查询竞技场简要信息
[停止竞技场订阅] 停止战斗竞技场排名变动推送
[停止公主竞技场订阅] 停止公主竞技场排名变动推送
[启用竞技场订阅] 启用战斗竞技场排名变动推送
[启用公主竞技场订阅] 启用公主竞技场排名变动推送
[删除竞技场订阅] 删除竞技场排名变动推送绑定
[竞技场订阅状态] 查看排名变动推送绑定状态
[详细查询 (uid)] 查询账号详细信息
[查询群数] 查询bot所在群的数目
[查询竞技场订阅数] 查询绑定账号的总数量
[清空竞技场订阅] 清空所有绑定的账号(仅限主人)
'''.strip()

sv = SafeService('竞技场推送_tw', help_=sv_help, bundle='pcr查询')

@sv.on_fullmatch('竞技场帮助', only_to_me=False)
async def send_jjchelp(bot, ev):
    await bot.send(ev, f'{sv_help}')

@sv.on_fullmatch('查询群数', only_to_me=False)
async def group_num(bot, ev):
    self_ids = bot._wsr_api_clients.keys()
    for sid in self_ids:
        gl = await bot.get_group_list(self_id=sid)
        msg = f"本Bot目前正在为【{len(gl)}】个群服务"
    await bot.send(ev, f'{msg}')

curpath = dirname(__file__)
config = join(curpath, 'binds.json')
root = {
    'arena_bind' : {}
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
    pinfo = load(fp)

acinfo = decryptxml(join(curpath, 'tw.sonet.princessconnect.v2.playerprefs.xml'))

client = pcrclient(acinfo['UDID'], acinfo['SHORT_UDID'], acinfo['VIEWER_ID'], acinfo['TW_SERVER_ID'], pinfo['proxy'])

qlck = Lock()

async def query(id: str):
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
            binds.clear()
            save_binds()
            await bot.send(ev, f'已清空全部【{num}】个已订阅账号！')

@sv.on_rex(r'^竞技场绑定 ?(\d{9})$')
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

@sv.on_rex(r'^竞技场查询 ?(\d{9})?$')
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
            
            last_login_time = int (res['user_info']['last_login_time'])
            last_login_date = time.localtime(last_login_time)
            last_login_str = time.strftime('%Y-%m-%d %H:%M:%S',last_login_date)
            
            await bot.finish(ev, 
f'''昵称：{res['user_info']["user_name"]}
jjc排名：{res['user_info']["arena_rank"]}
pjjc排名：{res['user_info']["grand_arena_rank"]}
最后登录：{last_login_str}
''', at_sender=False)
        except ApiException as e:
            await bot.finish(ev, f'查询出错，{e}', at_sender=True)

@sv.on_rex(r'^详细查询 ?(\d{9})?$')
async def on_query_arena_all(bot, ev):
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
            arena_time = int (res['user_info']['arena_time'])
            arena_date = time.localtime(arena_time)
            arena_str = time.strftime('%Y-%m-%d',arena_date)

            grand_arena_time = int (res['user_info']['grand_arena_time'])
            grand_arena_date = time.localtime(grand_arena_time)
            grand_arena_str = time.strftime('%Y-%m-%d',grand_arena_date)
            
            last_login_time = int (res['user_info']['last_login_time'])
            last_login_date = time.localtime(last_login_time)
            last_login_str = time.strftime('%Y-%m-%d %H:%M:%S',last_login_date)

            # 获取支援角色信息，若玩家未设置则留空
            try:    
                id_favorite = int(str(res['favorite_unit']['id'])[0:4]) # 截取第1位到第4位的字符
                c_favorite = chara.fromid(id_favorite)
                msg_f = f'{c_favorite.name}{c_favorite.icon.cqcode}'
            except IndexError:
                msg_f = ''
            try:
                id_friend_support1 = int(str(res['friend_support_units'][0]['unit_data']['id'])[0:4])
                c_friend_support1 = chara.fromid(id_friend_support1)
                msg_fr1 = f'{c_friend_support1.name}{c_friend_support1.icon.cqcode}'
            except IndexError:
                msg_fr1 = ''
            try:
                id_friend_support2 = int(str(res['friend_support_units'][1]['unit_data']['id'])[0:4])
                c_friend_support2 = chara.fromid(id_friend_support2)
                msg_fr2 = f'{c_friend_support2.name}{c_friend_support2.icon.cqcode}'
            except IndexError:
                msg_fr2 = ''
            try:
                id_clan_support1 = int(str(res['clan_support_units'][0]['unit_data']['id'])[0:4])
                c_clan_support1 = chara.fromid(id_clan_support1)
                msg_cl1 = f'{c_clan_support1.name}{c_clan_support1.icon.cqcode}'
            except IndexError:
                msg_cl1 = ''
            try:
                id_clan_support2 = int(str(res['clan_support_units'][1]['unit_data']['id'])[0:4])
                c_clan_support2 = chara.fromid(id_clan_support2)
                msg_cl2 = f'{c_clan_support2.name}{c_clan_support2.icon.cqcode}'
            except IndexError:
                msg_cl2 = ''
            try:
                id_clan_support3 = int(str(res['clan_support_units'][2]['unit_data']['id'])[0:4])
                c_clan_support3 = chara.fromid(id_clan_support3)
                msg_cl3 = f'{c_clan_support3.name}{c_clan_support3.icon.cqcode}'
            except IndexError:
                msg_cl3 = ''
            try:
                id_clan_support4 = int(str(res['clan_support_units'][3]['unit_data']['id'])[0:4])
                c_clan_support4 = chara.fromid(id_clan_support4)
                msg_cl4 = f'{c_clan_support4.name}{c_clan_support4.icon.cqcode}'
            except IndexError:
                msg_cl4 = ''
            
            await bot.finish(ev, 
f'''id：{res['user_info']['viewer_id']}
昵称：{res['user_info']['user_name']}
公会：{res['clan_name']}
简介：{res['user_info']['user_comment']}
最后登录：{last_login_str}
jjc排名：{res['user_info']['arena_rank']}
pjjc排名：{res['user_info']['grand_arena_rank']}
战力：{res['user_info']['total_power']}
等级：{res['user_info']['team_level']}
jjc场次：{res['user_info']['arena_group']}
jjc创建日：{arena_str}
pjjc场次：{res['user_info']['grand_arena_group']}
pjjc创建日：{grand_arena_str}
角色数：{res['user_info']['unit_num']}
【最爱的角色】
{msg_f}
【好友支援角色】
{msg_fr1}{msg_fr2}
【地下城支援角色】
{msg_cl1}{msg_cl2}
【战队支援角色】
{msg_cl3}{msg_cl4}
''', at_sender=False)
        except ApiException as e:
            await bot.finish(ev, f'查询出错，{e}', at_sender=True)

@sv.on_rex('(启用|停止)(公主)?竞技场订阅')
async def change_arena_sub(bot, ev):
    global binds, lck

    key = 'arena_on' if ev['match'].group(2) is None else 'grand_arena_on'
    uid = str(ev['user_id'])

    async with lck:
        if not uid in binds:
            await bot.send(ev,'您还未绑定竞技场',at_sender=True)
        else:
            binds[uid][key] = ev['match'].group(1) == '启用'
            save_binds()
            await bot.finish(ev, f'{ev["match"].group(0)}成功', at_sender=True)

# @on_command('/pcrval') # 台服建议注释掉该命令，以防止与b服的验证码输入产生冲突，导致验证码输入无响应。
async def validate(session):
    global binds, lck, validate
    if session.ctx['user_id'] == acinfo['admin']:
        validate = session.ctx['message'].extract_plain_text().strip()[8:]
        captcha_lck.release()

@sv.on_prefix('删除竞技场订阅')
async def delete_arena_sub(bot,ev):
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
        binds.pop(uid)
        save_binds()

    await bot.finish(ev, '删除竞技场订阅成功', at_sender=True)

@sv.on_fullmatch('竞技场订阅状态')
async def send_arena_sub_status(bot,ev):
    global binds, lck
    uid = str(ev['user_id'])

    
    if not uid in binds:
        await bot.send(ev,'您还未绑定竞技场', at_sender=True)
    else:
        info = binds[uid]
        await bot.finish(ev,
    f'''
    当前竞技场绑定ID：{info['id']}
    竞技场订阅：{'开启' if info['arena_on'] else '关闭'}
    公主竞技场订阅：{'开启' if info['grand_arena_on'] else '关闭'}''',at_sender=True)


@sv.scheduled_job('interval', minutes=3) # minutes是刷新频率，可按自身服务器性能输入其他数值，可支持整数、小数
async def on_arena_schedule():
    global cache, binds, lck
    bot = get_bot()
    
    bind_cache = {}

    async with lck:
        bind_cache = deepcopy(binds)


    for user in bind_cache:
        info = bind_cache[user]
        try:
            sv.logger.info(f'querying {info["id"]} for {info["uid"]}')
            res = await query(info['id'])
            res = (res['user_info']['arena_rank'], res['user_info']['grand_arena_rank'])

            if user not in cache:
                cache[user] = res
                continue

            last = cache[user]
            cache[user] = res

            if res[0] > last[0] and info['arena_on']:
                await bot.send_group_msg(
                    group_id = int(info['gid']),
                    message = f'[CQ:at,qq={info["uid"]}]jjc：{last[0]}->{res[0]} ▼{res[0]-last[0]}'
                )

            if res[1] > last[1] and info['grand_arena_on']:
                await bot.send_group_msg(
                    group_id = int(info['gid']),
                    message = f'[CQ:at,qq={info["uid"]}]pjjc：{last[1]}->{res[1]} ▼{res[1]-last[1]}'
                )
        except ApiException as e:
            sv.logger.info(f'对{info["id"]}的检查出错\n{format_exc()}')
            if e.code == 6:

                async with lck:
                    binds.pop(user)
                    save_binds()
                sv.logger.info(f'已经自动删除错误的uid={info["id"]}')
        except:
            sv.logger.info(f'对{info["id"]}的检查出错\n{format_exc()}')

@sv.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    global lck, binds
    uid = str(session.ctx['user_id'])
    
    async with lck:
        if uid in binds:
            binds.pop(uid)
            save_binds()
