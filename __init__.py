from json import load, dump
from nonebot import get_bot
from hoshino import Service, priv
from hoshino.typing import NoticeSession
from .pcrclient import pcrclient, ApiException
from asyncio import Lock
from os.path import dirname, join, exists
from copy import deepcopy

sv_help = '''
[竞技场绑定 uid] 绑定竞技场排名变动推送，默认双场均启用
[竞技场查询 (uid)] 查询竞技场简要信息
[停止竞技场订阅] 停止战斗竞技场排名变动推送
[停止公主竞技场订阅] 停止公主竞技场排名变动推送
[启用竞技场订阅] 启用战斗竞技场排名变动推送
[启用公主竞技场订阅] 启用公主竞技场排名变动推送
[删除竞技场订阅] 删除竞技场排名变动推送绑定
[竞技场订阅状态] 查看排名变动推送绑定状态
'''

sv = Service('竞技场推送',help_=sv_help, bundle='pcr查询')

@sv.on_fullmatch('jjc帮助', only_to_me=False)
async def send_jjchelp(bot, ev):
    await bot.send(ev, sv_help)

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

with open(join(curpath, 'account.json')) as fp:
    client = pcrclient(load(fp))

qlck = Lock()
async def query(id:str):
    await qlck.acquire()
    try:
        while client.shouldLogin:
            await client.login()
        print(f'query got{id}')
        res = (await client.callapi('/profile/get_profile', {
                'target_viewer_id': int(id)
            }))['user_info']
        print(f'query ret{res}')
        return res
    finally:
        qlck.release()

def save_binds():
    with open(config, 'w') as fp:
        dump(root, fp, indent=4)

@sv.on_rex(r'^竞技场绑定 ?(\d{13})$')
async def on_arena_bind(bot, ev):
    global binds, lck

    try:
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
    finally:
        lck.release()

    await bot.finish(ev, '竞技场绑定成功', at_sender=True)

@sv.on_rex(r'^竞技场查询 ?(\d{13})?$')
async def on_query_arena(bot, ev):
    global binds, lck

    robj = ev['match']
    id = robj.group(1)

    await lck.acquire()
    try:
        if id == None:
            uid = str(ev['user_id'])
            if not uid in binds:
                await bot.finish(ev, '您还未绑定竞技场', at_sender=True)
                return
            else:
                id = binds[uid]['id']
        try:
            res = await query(id)
            await bot.finish(ev, 
f'''
竞技场排名：{res["arena_rank"]}
公主竞技场排名：{res["grand_arena_rank"]}''', at_sender=True)
        except ApiException as e:
            await bot.finish(ev, f'查询出错，{e}', at_sender=True)
    finally:
        lck.release()


@sv.on_rex('(启用|停止)(公主)?竞技场订阅')
async def change_arena_sub(bot, ev):
    global binds, lck

    key = 'arena_on' if ev['match'].group(2) is None else 'grand_arena_on'
    uid = str(ev['user_id'])
    await lck.acquire()
    try:
        if not uid in binds:
            await bot.send(ev,'您还未绑定竞技场',at_sender=True)
        else:
            binds[uid][key] = ev['match'].group(1) == '启用'
            save_binds()
            await bot.finish(ev, f'{ev["match"].group(0)}成功', at_sender=True)
    finally:
        lck.release()


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

    await lck.acquire()
    try:
        if not uid in binds:
            await bot.finish(ev, '未绑定竞技场', at_sender=True)
            return

        binds.pop(uid)
        save_binds()

        await bot.finish(ev, '删除竞技场订阅成功', at_sender=True)
    finally:
        lck.release()


@sv.on_fullmatch('竞技场订阅状态')
async def send_arena_sub_status(bot,ev):
    global binds, lck
    uid = str(ev['user_id'])

    await lck.acquire()
    try:
        if not uid in binds:
            await bot.send(ev,'您还未绑定竞技场', at_sender=True)
        else:
            info = binds[uid]
            await bot.finish(ev,
    f'''
    当前竞技场绑定ID：{info['id']}
    竞技场订阅：{'开启' if info['arena_on'] else '关闭'}
    公主竞技场订阅：{'开启' if info['grand_arena_on'] else '关闭'}''',at_sender=True)
    finally:
        lck.release()


@sv.scheduled_job('interval', minutes=.01)
async def on_arena_schedule():
    global cache, binds, lck
    bot = get_bot()
    
    bind_cache = {}

    await lck.acquire()
    try:
        bind_cache = deepcopy(binds)
    finally:
        lck.release()


    for user in bind_cache:
        info = bind_cache[user]
        try:
            sv.logger.info(f'querying {info["id"]} for {info["uid"]}')
            res = await query(info['id'])
            print(f'get res{res}')
            res = (res['arena_rank'], res['grand_arena_rank'])

            if user not in cache:
                cache[user] = res
                continue

            last = cache[user]
            cache[user] = res

            if res[0] != last[0] and info['arena_on']:
                await bot.send_group_msg(
                    group_id = int(info['gid']),
                    message = f'[CQ:at,qq={info["uid"]}]您的竞技场排名发生变化：{last[0]}->{res[0]}'
                )

            if res[1] != last[1] and info['grand_arena_on']:
                await bot.send_group_msg(
                    group_id = int(info['gid']),
                    message = f'[CQ:at,qq={info["uid"]}]您的公主竞技场排名发生变化：{last[1]}->{res[1]}'
                )
        except ApiException as e:
            sv.logger.info(f'对{info["id"]}的检查出错\n{e}')
            if e.code == 6:
                await lck.acquire()
                try:
                    binds.pop(user)
                    save_binds()
                finally:
                    lck.release()
                sv.logger.info(f'已经自动删除错误的uid={info["id"]}')
        except Exception as e:
            sv.logger.info(f'对{info["id"]}的检查出错\n{e}')

@sv.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    global lck, binds
    uid = str(session.ctx['user_id'])
    await lck.acquire()
    try:
        if uid in binds:
            binds.pop(uid)
            save_binds()
    finally:
        lck.release()
