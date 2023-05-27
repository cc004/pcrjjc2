import os

import jinja2
import hoshino
from hoshino import config
from quart import Blueprint

public_address = config.public_address if config.public_address else f"{config.IP}:{config.PORT}"

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


hoshino.get_bot().server_app.register_blueprint(geetest_validate)
