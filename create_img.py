from PIL import Image, ImageDraw, ImageFont, ImageColor
from ..priconne import chara
import time
from pathlib import Path
import zhconv
from hoshino.aiorequests import run_sync_func

path = Path(__file__).parent # 获取文件所在目录的绝对路径
font_cn_path = str(path / 'fonts' / 'SourceHanSansCN-Medium.otf')  # Path是路径对象，必须转为str之后ImageFont才能读取
font_tw_path = str(path / 'fonts' / 'pcrtwfont.ttf')

server_name = 'bilibili官方服务器' # 设置服务器名称

def _TraditionalToSimplified(hant_str: str):
    '''
    Function: 将 hant_str 由繁体转化为简体
    '''
    return zhconv.convert(str(hant_str), 'zh-hans')

def _cut_str(obj: str, sec: int):
    """
    按步长分割字符串
    """
    return [obj[i: i+sec] for i in range(0, len(obj), sec)]

def _generate_info_pic_internal(data):
    '''
    个人资料卡生成
    '''
    im = Image.open(path / 'img' / 'template.png') # 图片模板
    im_frame = Image.open(path / 'img' / 'frame.png') # 头像框
    try:
        id_favorite = int(str(data['favorite_unit']['id'])[0:4]) # 截取第1位到第4位的字符
    except:
        id_favorite = 1000 # 一个？角色
    pic_dir = chara.fromid(id_favorite).icon.path
    user_avatar = Image.open(pic_dir)
    user_avatar = user_avatar.resize((90, 90))
    im.paste(user_avatar, (44, 150), mask=user_avatar)
    im_frame = im_frame.resize((100, 100))
    im.paste(im=im_frame, box=(39, 145), mask=im_frame)

    cn_font = ImageFont.truetype(font_cn_path, 18) # Path是路径对象，必须转为str之后ImageFont才能读取
    # tw_font = ImageFont.truetype(str(font_tw_path), 18) # 字体有点问题，暂时别用
    
    font = cn_font # 选择字体
    
    cn_font_resize = ImageFont.truetype(font_cn_path, 16)
    # tw_font_resize = ImageFont.truetype(font_tw_path, 16) # 字体有点问题，暂时别用
    
    font_resize = cn_font_resize #选择字体

    draw = ImageDraw.Draw(im)
    font_black = (77, 76, 81, 255)

    # 资料卡 个人信息
    user_name_text = _TraditionalToSimplified(data["user_info"]["user_name"])
    team_level_text = _TraditionalToSimplified(data["user_info"]["team_level"])
    total_power_text = _TraditionalToSimplified(
        data["user_info"]["total_power"])
    clan_name_text = _TraditionalToSimplified(data["clan_name"])
    user_comment_arr = _cut_str(_TraditionalToSimplified(
        data["user_info"]["user_comment"]), 25)
    last_login_time_text = _TraditionalToSimplified(time.strftime(
        "%Y/%m/%d %H:%M:%S", time.localtime(data["user_info"]["last_login_time"]))).split(' ')

    draw.text((194, 120), user_name_text, font_black, font)

    w, h = font_resize.getsize(team_level_text)
    draw.text((568 - w, 168), team_level_text, font_black, font_resize)
    w, h = font_resize.getsize(total_power_text)
    draw.text((568 - w, 210), total_power_text, font_black, font_resize)
    w, h = font_resize.getsize(clan_name_text)
    draw.text((568 - w, 250), clan_name_text, font_black, font_resize)
    for index, value in enumerate(user_comment_arr):
        draw.text((170, 310 + (index * 22)), value, font_black, font_resize)
    draw.text((34, 350), last_login_time_text[0] + "\n" +
              last_login_time_text[1], font_black, font_resize)
    draw.text((34, 392), server_name, font_black, font_resize)

    # 资料卡 冒险经历
    normal_quest_text = _TraditionalToSimplified(
        data["quest_info"]["normal_quest"][2])
    hard_quest_text = _TraditionalToSimplified(
        data["quest_info"]["hard_quest"][2])
    very_hard_quest_text = _TraditionalToSimplified(
        data["quest_info"]["very_hard_quest"][2])

    w, h = font_resize.getsize(normal_quest_text)
    draw.text((550 - w, 498), normal_quest_text, font_black, font_resize)
    w, h = font_resize.getsize("H" + hard_quest_text +
                           " / VH" + very_hard_quest_text)
    draw.text((550 - w, 530), "H" + hard_quest_text +
              " / VH", font_black, font_resize)
    w, h = font_resize.getsize(very_hard_quest_text)
    draw.text((550 - w, 530), very_hard_quest_text, font_black, font_resize)

    arena_group_text = _TraditionalToSimplified(
        data["user_info"]["arena_group"])
    arena_time_text = _TraditionalToSimplified(time.strftime(
        "%Y/%m/%d", time.localtime(data["user_info"]["arena_time"])))
    arena_rank_text = _TraditionalToSimplified(data["user_info"]["arena_rank"])
    grand_arena_group_text = _TraditionalToSimplified(
        data["user_info"]["grand_arena_group"])
    grand_arena_time_text = _TraditionalToSimplified(time.strftime(
        "%Y/%m/%d", time.localtime(data["user_info"]["grand_arena_time"])))
    grand_arena_rank_text = _TraditionalToSimplified(
        data["user_info"]["grand_arena_rank"])

    w, h = font_resize.getsize(arena_time_text)
    draw.text((550 - w, 598), arena_time_text, font_black, font_resize)
    w, h = font_resize.getsize(arena_group_text+"场")
    draw.text((550 - w, 630), arena_group_text+"场", font_black, font_resize)
    w, h = font_resize.getsize(arena_rank_text+"名")
    draw.text((550 - w, 662), arena_rank_text+"名", font_black, font_resize)
    w, h = font_resize.getsize(grand_arena_time_text)
    draw.text((550 - w, 704), grand_arena_time_text, font_black, font_resize)
    w, h = font_resize.getsize(grand_arena_group_text+"场")
    draw.text((550 - w, 738), grand_arena_group_text+"场", font_black, font_resize)
    w, h = font_resize.getsize(grand_arena_rank_text+"名")
    draw.text((550 - w, 772), grand_arena_rank_text+"名", font_black, font_resize)

    unit_num_text = _TraditionalToSimplified(data["user_info"]["unit_num"])
    open_story_num_text = _TraditionalToSimplified(
        data["user_info"]["open_story_num"])

    w, h = font_resize.getsize(unit_num_text)
    draw.text((550 - w, 844), unit_num_text, font_black, font_resize)
    w, h = font_resize.getsize(open_story_num_text)
    draw.text((550 - w, 880), open_story_num_text, font_black, font_resize)

    tower_cleared_floor_num_text = _TraditionalToSimplified(
        data["user_info"]["tower_cleared_floor_num"])
    tower_cleared_ex_quest_count_text = _TraditionalToSimplified(
        data["user_info"]["tower_cleared_ex_quest_count"])

    w, h = font_resize.getsize(tower_cleared_floor_num_text+"阶")
    draw.text((550 - w, 949), tower_cleared_floor_num_text +
              "阶", font_black, font_resize)
    w, h = font_resize.getsize(tower_cleared_ex_quest_count_text)
    draw.text((550 - w, 984), tower_cleared_ex_quest_count_text,
              font_black, font_resize)

    viewer_id_arr = _cut_str(_TraditionalToSimplified(
        data["user_info"]["viewer_id"]), 3)

    w, h = font.getsize(
        viewer_id_arr[0] + "  " + viewer_id_arr[1] + "  " + viewer_id_arr[2])
    draw.text((138 + (460 - 138) / 2 - w / 2, 1058),
              viewer_id_arr[0] + "  " + viewer_id_arr[1] + "  " + viewer_id_arr[2], (255, 255, 255, 255), font)

    return im

def _friend_support_position(fr_data, im, fnt, rgb, im_frame, bbox):
    '''
    好友支援位
    '''
    # 合成头像
    im_yuansu = Image.open(path / 'img' / 'yuansu.png') # 一个支援ui模板
    id_friend_support = int(str(fr_data['unit_data']['id'])[0:4])
    pic_dir = chara.fromid(id_friend_support).icon.path
    avatar = Image.open(pic_dir)
    avatar = avatar.resize((115, 115))
    im_yuansu.paste(im=avatar, box=(28, 78), mask=avatar)
    im_frame = im_frame.resize((128, 128))
    im_yuansu.paste(im=im_frame, box=(22, 72), mask=im_frame)

    # 合成文字信息
    yuansu_draw = ImageDraw.Draw(im_yuansu)
    icon_name_text = _TraditionalToSimplified(chara.fromid(id_friend_support).name)
    icon_LV_text = str(fr_data['unit_data']['unit_level']) # 写入文本必须是str格式
    icon_rank_text = str(fr_data['unit_data']['promotion_level'])
    yuansu_draw.text(xy=(167, 36.86), text=icon_name_text, font=fnt, fill=rgb)
    yuansu_draw.text(xy=(340, 101.8), text=icon_LV_text, font=fnt, fill=rgb)
    yuansu_draw.text(xy=(340, 159.09), text=icon_rank_text, font=fnt, fill=rgb)
    im.paste(im=im_yuansu, box=bbox) # 无A通道的图不能输入mask

    return im

def _clan_support_position(clan_data, im, fnt, rgb, im_frame, bbox):
    '''
    地下城及战队支援位
    '''
    # 合成头像
    im_yuansu = Image.open(path / 'img' / 'yuansu.png') # 一个支援ui模板
    id_clan_support = int(str(clan_data['unit_data']['id'])[0:4])
    pic_dir = chara.fromid(id_clan_support).icon.path
    avatar = Image.open(pic_dir)
    avatar = avatar.resize((115, 115))
    im_yuansu.paste(im=avatar, box=(28, 78), mask=avatar)
    im_frame = im_frame.resize((128, 128))
    im_yuansu.paste(im=im_frame, box=(22, 72), mask=im_frame)

    # 合成文字信息
    yuansu_draw = ImageDraw.Draw(im_yuansu)
    icon_name_text = _TraditionalToSimplified(chara.fromid(id_clan_support).name)
    icon_LV_text = str(clan_data['unit_data']['unit_level']) # 写入文本必须是str格式
    icon_rank_text = str(clan_data['unit_data']['promotion_level'])
    yuansu_draw.text(xy=(167, 36.86), text=icon_name_text, font=fnt, fill=rgb)
    yuansu_draw.text(xy=(340, 101.8), text=icon_LV_text, font=fnt, fill=rgb)
    yuansu_draw.text(xy=(340, 159.09), text=icon_rank_text, font=fnt, fill=rgb)
    im.paste(im=im_yuansu, box=bbox) # 无A通道的图不能输入mask

    return im

def _generate_support_pic_internal(data):
    '''
    支援界面图片合成
    '''
    im = Image.open(path / 'img' / 'support.png') # 支援图片模板
    im_frame = Image.open(path / 'img' / 'frame.png') # 头像框

    fnt = ImageFont.truetype(font=font_cn_path, size=30)
    rgb = ImageColor.getrgb('#4e4e4e')

    # 判断玩家设置的支援角色应该存在的位置
    for fr_data in data['friend_support_units']: # 若列表为空，则不会进行循环
        if fr_data['position'] == 1: # 好友支援位1
            bbox = (1284, 156)
            im = _friend_support_position(fr_data, im, fnt, rgb, im_frame, bbox)
        elif fr_data['position'] == 2: # 好友支援位2
            bbox = (1284, 459)
            im = _friend_support_position(fr_data, im, fnt, rgb, im_frame, bbox)

    for clan_data in data['clan_support_units']:
        if clan_data['position'] == 1: # 地下城位置1
            bbox = (43, 156)
            im = _clan_support_position(clan_data, im, fnt, rgb, im_frame, bbox)
        elif clan_data['position'] == 2: # 地下城位置2
            bbox = (43, 459)
            im = _clan_support_position(clan_data, im, fnt, rgb, im_frame, bbox)
        elif clan_data['position'] == 3: # 战队位置1
            bbox = (665, 156)
            im = _clan_support_position(clan_data, im, fnt, rgb, im_frame, bbox)
        elif clan_data['position'] == 4: # 战队位置2
            bbox = (665, 459)
            im = _clan_support_position(clan_data, im, fnt, rgb, im_frame, bbox)
    
    return im

async def generate_support_pic(*args, **kwargs):
    return await run_sync_func(_generate_support_pic_internal, *args, **kwargs)

async def generate_info_pic(*args, **kwargs):
    return await run_sync_func(_generate_info_pic_internal, *args, **kwargs)
