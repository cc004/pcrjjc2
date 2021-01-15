from threading import Lock
from os.path import join
from asyncio import set_event_loop, new_event_loop, sleep
from threading import Thread
from traceback import format_exc
from json import load
from .pcrclient import pcrclient

query_param = None
queryin_sig = Lock()
queryout_sig = Lock()
queryin_sig.acquire()

async def query(sv, curpath):
    with open(join(curpath, 'account.json')) as fp:
        client = pcrclient(load(fp))
    while True:
        queryin_sig.acquire()
        try:
            id, callback = query_param
            while client.shouldLogin:
                await client.login()
            res = (await client.callapi('/profile/get_profile', {
                    'target_viewer_id': int(id)
                }))['user_info']
            await callback(res)
        except:
            sv.logger.error(format_exc())
        queryout_sig.release()

async def schedule_query(id, callback):
    global query_param
    while not queryout_sig.acquire(blocking=False):
        await sleep(0.05)
    query_param = id, callback
    queryin_sig.release()

def run_coroutine(sv, curpath):
    loop = new_event_loop()
    set_event_loop(loop)
    loop.run_until_complete(query(sv, curpath))

def query_init(sv, curpath):
    Thread(target=lambda: run_coroutine(sv, curpath)).start()
