import os

import jinja2
from quart import Blueprint

import hoshino
from hoshino import config
# from hoshino import config, aiorequests

template_folder = os.path.join(os.path.dirname(__file__), 'geetest')
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_folder),
    enable_async=True
)


async def render_template(template, **kwargs):
    t = env.get_template(template)
    return await t.render_async(**kwargs)


geetest_validate = Blueprint('geetest_validate', __name__)


@geetest_validate.route('/geetest')
async def geetest():
    return await render_template('geetest.html')


bot_ = hoshino.get_bot()
bot_.server_app.register_blueprint(geetest_validate)


@bot_.on_startup
async def get_real_ip() -> str:
    public_address = f"127.0.0.1:{config.PORT}"
    try:
        if config.public_address:
            public_address = config.public_address
        elif config.IP:
            public_address = f"{config.IP}:{config.PORT}"
    except AttributeError:
        # from . import send_to_admin
        # try:
        #     resp = await aiorequests.get(url="https://4.ipw.cn", timeout=3)
        #     real_ip = await resp.text
        #     public_address = f"{real_ip}:{config.PORT}"
        #     hoshino.logger.info(f"using fetched real ip as public address: {public_address}")
        #     await send_to_admin(f"成功获取公网IP：{real_ip}\n注意：本IP仅在你有公网IP时才有效！如果你没有公网IP，请使用127.0.0.1作为你的IP！")
        # except Exception as e:
        #     hoshino.logger.error(f"获取公网IP失败\n{e}")
        #     await send_to_admin(f"获取公网IP失败，使用默认IP\n{e}")
        pass
    hoshino.logger.info(f"current public address: {public_address}")
    return public_address


async def get_public_address():
    return await get_real_ip()
    
