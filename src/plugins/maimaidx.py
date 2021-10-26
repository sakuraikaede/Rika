from collections import defaultdict

from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters import Event, Bot
from nonebot.adapters.cqhttp import Message, MessageSegment, GroupMessageEvent, PrivateMessageEvent

from src.libraries.tool import hash
from src.libraries.maimaidx_music import *
from src.libraries.image import *
from src.libraries.maimai_best_40 import generate, get_player_data
import re
import datetime
import time

from src.libraries.maimaidx_guess import GuessObject
from nonebot.permission import Permission
from nonebot.log import logger
import requests
import json
import random
from urllib import parse
import asyncio

from src.libraries.config import Config

driver = get_driver()
@driver.on_startup
def _():
    logger.info("Kiba Kernel -> Load \"Driver\" successfully")

def song_txt(music: Music):
    return Message([
        {
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/covers/{music.id}.jpg"
            }
        },
        {
            "type": "text",
            "data": {
                "text": f"Track ID: {music.id} | Type: {music.type} >\n"
            }
        },
        {
            "type": "text",
            "data": {
                "text": f"{music.title}"
            }
        },
        {
            "type": "text",
            "data": {
                "text": f"\n分类 > {music.genre}\n等级 > {' | '.join(music.level)}"
            }
        }
    ])


def inner_level_q(ds1, ds2=None):
    result_set = []
    diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']
    if ds2 is not None:
        music_data = total_list.filter(ds=(ds1, ds2))
    else:
        music_data = total_list.filter(ds=ds1)
    for music in sorted(music_data, key = lambda i: int(i['id'])):
        for i in music.diff:
            result_set.append((music['id'], music['title'], music['ds'][i], diff_label[i], music['level'][i]))
    return result_set


inner_level = on_command('inner_level ', aliases={'定数查歌 '})


@inner_level.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    if len(argv) > 2 or len(argv) == 0:
        await inner_level.finish("命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>")
        return
    if len(argv) == 1:
        result_set = inner_level_q(float(argv[0]))
        s = f"> 定数查歌结果 定数: {float(argv[0])}"
    else:
        result_set = inner_level_q(float(argv[0]), float(argv[1]))
        s = f"> 定数查歌结果 定数: {float(argv[0])} - {float(argv[1])}"
    if len(result_set) > 50:
        await inner_level.finish(f"结果过多（{len(result_set)} 条），请缩小搜索范围。")
        return
    resultnum = 0
    for elem in result_set:
        resultnum += 1
        s += f"\nNo: {resultnum} | Track ID {elem[0]} >\n{elem[1]} {elem[3]} {elem[4]}({elem[2]})"
    await inner_level.finish(s.strip())


pandora_list = ['我觉得您打白潘不如先去打一下白茄子。', '别潘了，别潘了，滴蜡熊快被潘跑了。', '没有精神！！转圈掉的那么多还想打15!!', '在您玩白潘之前，请您先想一下：截止2021/9，国内SSS+ 4人，SSS 18人，SS 69人。这和您有关吗？不，一点关系都没有。', '潘你🐎', '机厅老板笑着管你收砸坏键子的损失费。', '潘小鬼是吧？', '你不许潘了！']
spec_rand = on_regex(r"^随个(?:dx|sd|标准)?[绿黄红紫白]?[0-9]+\+?")


@spec_rand.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    level_labels = ['绿', '黄', '红', '紫', '白']
    regex = "随个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)"
    res = re.match(regex, str(event.get_message()).lower())
    try:
        if res.groups()[0] == "dx":
            tp = ["DX"]
        elif res.groups()[0] == "sd" or res.groups()[0] == "标准":
            tp = ["SD"]
        else:
            tp = ["SD", "DX"]
        level = res.groups()[2]
        if res.groups()[1] == "":
            music_data = total_list.filter(level=level, type=tp)
        else:
            music_data = total_list.filter(level=level, diff=['绿黄红紫白'.index(res.groups()[1])], type=tp)
        if len(music_data) == 0:
            rand_result = f'{nickname}，最低是1，最高是15，您这整了个{level}......故意找茬的吧？'
        else:
            rand_result = f'> To {nickname} | Rand Track\n' + song_txt(music_data.random())
            if level == '15':
                rand_result += "\n\n" + pandora_list[random.randint(0,7)]
        await spec_rand.send(rand_result)
    except Exception as e:
        print(e)
        await spec_rand.finish("随机命令出错了...检查一下语法吧？如果不是语法错误请快点告诉 BlitzR 让他来修 Bug。")

mr = on_regex(r".*maimai.*什么")


@mr.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await mr.finish(song_txt(total_list.random()))


spec_rand_multi = on_regex(r"^随([1-9]\d*)首(?:dx|sd|标准)?[绿黄红紫白]?[0-9]+\+?[至]?([0-9]+\+?)?")

@spec_rand_multi.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    level_labels = ['绿', '黄', '红', '紫', '白']
    regex = "随([1-9]\d*)首((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)([至]?)([0-9]+\+?)?"   
    res = re.match(regex, str(event.get_message()).lower())
    cf_list = [f'国行DX最多就四首，所以我们不能随{res.groups()[0]}首。', f'如果你真的想打{res.groups()[0]}首歌还不喘气的话，你应该去霓虹打超新超热去，这最多就4首，你要不要吧！╰(艹皿艹 )', f'这个指令不能对日本玩家服务....这里只能支持四首，{res.groups()[0]}真的太多了。']
    try:
        if int(res.groups()[0]) > 4:
            rand_result = cf_list[random.randint(0,2)]
            await spec_rand_multi.send(rand_result)
        else:
            if res.groups()[3] == '15' and res.groups()[4] is None:
                rand_result = f'WDNMD....{res.groups()[0]}首白潘是吧？\n(╯‵□′)╯︵┻━┻\n 自己查 id834 去！！'
                await spec_rand_multi.send(rand_result)
            else:
                rand_result = f'> To {nickname} | Rand Tracks\n'
                for i in range(int(res.groups()[0])):
                    if res.groups()[1] == "dx":
                        tp = ["DX"]
                    elif res.groups()[1] == "sd" or res.groups()[0] == "标准":
                        tp = ["SD"]
                    else:
                        tp = ["SD", "DX"]
                    if res.groups()[4] is not None:
                        level = [res.groups()[3], res.groups()[5]]
                    else:
                        level = res.groups()[3]
                    if res.groups()[2] == "":
                        music_data = total_list.filter(level=level, type=tp)
                    else:
                        music_data = total_list.filter(level=level, diff=['绿黄红紫白'.index(res.groups()[2])], type=tp)
                    if len(music_data) == 0:
                        rand_result = f'{nickname}，最低是1，最高是15，您这整了个{level}......故意找茬的吧？\n <(* ￣︿￣)'
                    else:
                        rand_result += f'\n----- Track {i + 1} / {res.groups()[0]} -----\n' + song_txt(music_data.random())
                await spec_rand_multi.send(rand_result)
    except Exception as e:
        print(e)
        await spec_rand_multi.finish("随机命令出错了...检查一下语法吧？如果不是语法错误请快点告诉 BlitzR 让他来修 Bug。")


search_music = on_regex(r"^查歌.+")


@search_music.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "查歌(.+)"
    name = re.match(regex, str(event.get_message())).groups()[0].strip()
    if name == "":
        return
    res = total_list.filter(title_search=name)
    if len(res) == 0:
        await search_music.send("没有找到这样的乐曲。")
    elif len(res) < 50:
        search_result = "> 搜索结果"
        resultnum = 0
        for music in sorted(res, key = lambda i: int(i['id'])):
            resultnum += 1
            search_result += f"\nNo: {resultnum} | Track ID: {music['id']} >\n{music['title']}"
        await search_music.finish(Message([
            {"type": "text",
                "data": {
                    "text": search_result.strip()
                }}]))
    else:
        await search_music.send(f"结果太多啦...一共我查到{len(res)} 条符合条件的歌!\n缩小一下查询范围吧。")


query_chart = on_regex(r"^([绿黄红紫白]?)id([0-9]+)")


@query_chart.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([绿黄红紫白]?)id([0-9]+)"
    groups = re.match(regex, str(event.get_message())).groups()
    level_labels = ['绿', '黄', '红', '紫', '白']
    if groups[0] != "":
        try:
            level_index = level_labels.index(groups[0])
            level_name = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']
            name = groups[1]
            music = total_list.by_id(name)
            chart = music['charts'][level_index]
            ds = music['ds'][level_index]
            level = music['level'][level_index]
            file = f"https://www.diving-fish.com/covers/{music['id']}.jpg"
            if len(chart['notes']) == 4:
                msg = f'''Standard >\n{level_name[level_index]} > Lv {level} Base -> {ds}
ALL> {chart['notes'][0] + chart['notes'][1] + chart['notes'][2] + chart['notes'][3]}
TAP> {chart['notes'][0]}
HOLD> {chart['notes'][1]}
SLIDE> {chart['notes'][2]}
BREAK> {chart['notes'][3]}
Notes Designer> {chart['charter']}'''
            else:
                msg = f'''DX >\n{level_name[level_index]} > Lv {level} Base -> {ds}
ALL> {chart['notes'][0] + chart['notes'][1] + chart['notes'][2] + chart['notes'][3] + chart['notes'][4]}
TAP> {chart['notes'][0]}
HOLD> {chart['notes'][1]}
SLIDE>  {chart['notes'][2]}
TOUCH> {chart['notes'][3]}
BREAK> {chart['notes'][4]}
Notes Designer> {chart['charter']}'''
            await query_chart.send(Message([
                {
                    "type": "image",
                    "data": {
                        "file": f"{file}"
                    }
                },
                {
                    "type": "text",
                    "data": {
                        "text": f"{music['title']}\n"
                    }
                },
                {
                    "type": "text",
                    "data": {
                        "text": f"Track ID: {music['id']} | Type: "
                    }
                },
                {
                    "type": "text",
                    "data": {
                        "text": msg
                    }
                }
            ]))
        except Exception:
            await query_chart.send("啊这，我没有找到该谱面......")
    else:
        name = groups[1]
        music = total_list.by_id(name)
        try:
            file = f"https://www.diving-fish.com/covers/{music['id']}.jpg"
            await query_chart.send(Message([
                {
                    "type": "image",
                    "data": {
                        "file": f"{file}"
                    }
                },
                {
                    "type": "text",
                    "data": {
                        "text": f"Track ID: {music['id']} | Type: {music['type']} >\n"
                    }
                }, 
                {
                    "type": "text",
                    "data": {
                        "text": f"{music['title']}\n"
                    }
                },  
                {
                    "type": "text",
                    "data": {
                        "text": f"Artists > {music['basic_info']['artist']}\n分类 > {music['basic_info']['genre']}\nBPM > {music['basic_info']['bpm']}\n版本 > {music['basic_info']['from']}\n等级 [当前版本定数] >\n{' | '.join(music['level'])}\n{''.join(str(music['ds']))}"
                    }
                }
            ]))
        except Exception:
            await query_chart.send("啊这...我没有找到这个歌。\n换一个试试吧。")

xp_list = ['滴蜡熊', '幸隐', '14+', '白潘', '紫潘', 'PANDORA BOXXX', '排队区', '旧框', '干饭', '超常maimai', '收歌', '福瑞', '削除', 'HAPPY', '谱面-100号', 'lbw', '茄子卡狗', '打五把CSGO', '一姬', '打麻将', '光吉猛修', '怒锤', '暴漫', '鼓动', '鼓动(红)']

jrxp = on_command('jrxp', aliases={'今日性癖'})


@jrxp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    nickname = event.sender.nickname
    h = hash(qq)
    rp = h % 100
    xp = random.randint(0,24)
    s = f"> 今日性癖\n{nickname}今天的性癖是{xp_list[xp]}，人品值是{rp}%.\n不满意的话再随一个吧！"
    await jrxp.finish(Message([
        {"type": "text", "data": {"text": s}}
    ]))


wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌', '理论值', '打东方曲', '打索尼克曲']
bwm_list_perfect = ['拆机:然后您被机修当场处决', '女装:怎么这么好康！（然后受到了欢迎）', '耍帅:看我耍帅还AP+', '击剑:Alea jacta est!(SSS+)', '打滴蜡熊:看我今天不仅推了分，还收了歌！', '日麻:看我三倍役满!!!你们三家全都起飞!!!', '出勤:不出则已，一出惊人，当场AP，羡煞众人。', '看手元:哦原来是这样！看了手元果真推分了。', '霸机:这么久群友都没来，霸机一整天不是梦！', '打Maipad: Maipad上收歌了，上机也收了。', '唱打: Let the bass kick! O-oooooooooo AAAAE-A-A-I-A-U- JO-oooooooooooo AAE-O-A-A-U-U-A- E-eee-ee-eee AAAAE-A-E-I-E-A- JO-ooo-oo-oo-oo EEEEO-A-AAA-AAAA O-oooooooooo AAAAE-A-A-I-A-U-......']
bwm_list_bad = ['拆机:不仅您被机修当场处决，还被人尽皆知。', '女装:杰哥说你怎么这么好康！让我康康！！！（被堵在卫生间角落）', '耍帅:星星全都粉掉了......', '击剑:Alea jacta est!(指在线下真实击剑)', '打滴蜡熊:滴蜡熊打你。', '日麻:我居然立直放铳....等等..三倍役满??????', '出勤:当场分数暴毙，惊呆众人。', '看手元:手法很神奇，根本学不来。', '霸机:......群友曰:"霸机是吧？踢了！"', '打Maipad: 上机还是不大会......', '唱打: 被路人拍下上传到了某音。']
tips_list = ['在游戏过程中,请您不要大力拍打或滑动机器!', '建议您常多备一副手套！如果游玩时手套破裂或许会有大用！', '游玩时注意手指安全！意外戳到边框时若引发剧烈疼痛请立刻下机以休息手指，必要时可以选择就医。', '游玩过程中注意财物安全。自己的财物远比一个SSS+要更有价值。', '底力不够？建议下埋！不要强行越级，手癖难解。', '文明游玩，游戏要排队，不要做不遵守游戏规则的玩家！', '人品值和宜忌每天0点都会刷新，不喜欢总体运势可以通过这个指令再随一次。', '疫情防护，人人有责。在游玩结束后请主动佩戴口罩！', '出勤时注意交通安全，身体安全永远在第一位！', '迪拉熊不断吃绝赞？去找机修教训它。']

jrwm = on_command('今日运势', aliases={'今日舞萌'})

@jrwm.handle()
async def _(bot: Bot, event: Event, state: T_State):   
    qq = int(event.get_user_id())
    nickname = event.sender.nickname
    h = hash(qq)
    rp = h % 100
    luck = hash(int((h * 4) / 3)) % 100
    ap = hash(int(((luck * 100) * (rp) * (hash(qq) / 4 % 100)))) % 100
    wm_value = []
    good_value = {}
    bad_value = {}
    good_count = 0
    bad_count = 0
    dwm_value_1 = random.randint(0,10)
    dwm_value_2 = random.randint(0,10)
    tips_value = random.randint(0,9)
    now = datetime.datetime.now()  
    for i in range(14):
        wm_value.append(h & 3)
        h >>= 2
    s = f"> 👨 {nickname} | 舞萌运势\n⏲️ | {now.year}/{now.month}/{now.day} {now.hour}:{now.strftime('%M')}:{now.strftime('%S')}\n"
    s += f"\n-> 运势概览 | Overview\n"
    if rp >= 50 and rp < 70:
        s += "末吉"
    elif rp >= 70 and rp < 90:
        s += "吉"
    elif rp >= 90:
        s += "大吉"
    elif rp >= 30 and rp < 50:
        s += "小凶"
    elif rp >= 10 and rp < 30:
        s += "凶"
    else:
        s += "大凶"
    s += f" | 人品值: {rp}%"
    s += f" | 幸运度: {luck}%\n"
    s += f"\n-> 日常运势 | Daily\n"

    if dwm_value_1 == dwm_value_2:
        s += f'平 | 今天总体上平平无常。向北走有财运，向南走运不佳....等一下，这句话好像在哪儿听过？\n'
    else:
        s += f'宜 | {bwm_list_perfect[dwm_value_1]}\n'
        s += f'忌 | {bwm_list_bad[dwm_value_2]}\n'
    s += f"\n-> 舞萌运势 | Maimai\n今日收歌指数 -> {ap}%\n"
    for i in range(14):
        if wm_value[i] == 3:
            good_value[good_count] = i
            good_count = good_count + 1
        elif wm_value[i] == 0:
            bad_value[bad_count] = i
            bad_count = bad_count + 1
    if good_count == 0:
        s += "宜 | 🚫 诸事不宜"
    else:
        s += f'宜 | 共 {good_count} 项 >\n'
        for i in range(good_count):
            s += f'{wm_list[good_value[i]]} '
    if bad_count == 0:
        s += '\n忌 | ✔️ 无所畏忌\n'
    else:
        s += f'\n忌 | 共 {bad_count} 项 >\n'
        for i in range(bad_count):
            s += f'{wm_list[bad_value[i]]} '
    s += f'\n\n-> 犽之锦囊 | Kiba\'s Hints\n游玩提示:\n{tips_list[tips_value]}\n\n'
    s += "运势歌曲:\n"
    music = total_list[hash(qq * luck * ap * 100 * rp * 100) % len(total_list)]
    await jrwm.finish(Message([{"type": "text", "data": {"text": s}}] + song_txt(music)))

jrrp = on_command('jrrp', aliases={'人品值'})

@jrrp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    nickname = event.sender.nickname
    h = hash(qq)
    rp = h % 100
    luck = hash(int((h * 4) / 3)) % 100
    ap = hash(int(((luck * 100) * (rp) * (hash(qq) / 4 % 100)))) % 100
    s = f"> For {nickname} | 人品签\n----------------------\n"
    s += f"人品值: {rp}%\n"
    s += f"幸运度: {luck}%"
    if rp >= 50 and rp < 70:
        s += "            小吉!\n"
    elif rp >= 70 and rp < 90:
        s += "             吉!\n"
    elif rp >= 90:
        s += "            大吉!\n"
    elif rp >= 30 and rp < 50:
        s += "            小凶!\n"
    elif rp >= 10 and rp < 30:
        s += "             凶!\n"
    else:
        s += "            大凶!\n"
    s += f"收歌率: {ap}%\n----------------------\n更多请查看今日运势或今日性癖。"
    await jrrp.finish(Message([
        {"type": "text", "data": {"text": s}}
    ]))

jrgq = on_command('今天打什么歌')

@jrgq.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    nickname = event.sender.nickname
    h = hash(qq)
    rp = h % 100
    s = f"> To {nickname} | 推荐\n来打这个吧：\n"
    music = total_list[(h * 4) % len(total_list)]
    await jrgq.finish(Message([
        {"type": "text", "data": {"text": s}}
    ] + song_txt(music)))

music_aliases = defaultdict(list)
f = open('src/static/aliases.csv', 'r', encoding='utf-8')
tmp = f.readlines()
f.close()
for t in tmp:
    arr = t.strip().split('\t')
    for i in range(len(arr)):
        if arr[i] != "":
            music_aliases[arr[i].lower()].append(arr[0])


find_song = on_regex(r".+是什么歌")


@find_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "(.+)是什么歌"
    name = re.match(regex, str(event.get_message())).groups()[0].strip().lower()
    nickname = event.sender.nickname
    if name not in music_aliases:
        await find_song.finish(f"> To {nickname} | 别名查歌: 错误\n这个别称太新了，我找不到这首歌啦。\n但是您可以帮助我收集歌曲的别名！戳链接加入 Kiba 歌曲别名收集计划:\nhttps://kdocs.cn/l/cdzsTdqaPFye")
        return
    result_set = music_aliases[name]
    if len(result_set) == 1:
        music = total_list.by_title(result_set[0])
        await find_song.finish(Message([{"type": "text", "data": {"text": f"> To {nickname} | 别名查歌\n您说的应该是：\n"}}] + song_txt(music)))
    else:
        s = '\n'.join(result_set)
        await find_song.finish(f"> To {nickname} | 别名查歌: 多个结果\n您要找的可能是以下歌曲中的其中一首：\n{ s }")


query_score = on_command('分数线')


@query_score.handle()
async def _(bot: Bot, event: Event, state: T_State):
    r = "([绿黄红紫白])(id)?([0-9]+)"
    argv = str(event.get_message()).strip().split(" ")
    if len(argv) == 1 and argv[0] == '帮助':
        s = '''> 分数线 帮助
这个功能为你提供达到某首歌分数线的最低标准而设计的~~~
命令格式：分数线 <难度+歌曲id> <分数线>
例如：分数线 紫799 100
命令将返回分数线允许的 TAP GREAT 容错以及 BREAK 50落等价的 TAP GREAT 数。
以下为 TAP GREAT 的对应表：
GREAT/GOOD/MISS
TAP\t1/2.5/5
HOLD\t2/5/10
SLIDE\t3/7.5/15
TOUCH\t1/2.5/5
BREAK\t5/12.5/25(外加200落)'''
        await query_score.send(Message([{
            "type": "image",
            "data": {
                "file": f"base64://{str(image_to_base64(text_to_image(s)), encoding='utf-8')}"
            }
        }]))
    elif len(argv) == 2:
        try:
            grp = re.match(r, argv[0]).groups()
            level_labels = ['绿', '黄', '红', '紫', '白']
            level_labels2 = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
            level_index = level_labels.index(grp[0])
            chart_id = grp[2]
            line = float(argv[1])
            music = total_list.by_id(chart_id)
            chart: Dict[Any] = music['charts'][level_index]
            tap = int(chart['notes'][0])
            slide = int(chart['notes'][2])
            hold = int(chart['notes'][1])
            touch = int(chart['notes'][3]) if len(chart['notes']) == 5 else 0
            brk = int(chart['notes'][-1])
            total_score = 500 * tap + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            await query_chart.send(f'''> 分数线\n{music['title']} | {level_labels2[level_index]}\n 分数线: {line}% 最低要求 >\n
Tap Great 最低损失量 /个 |\n {(total_score * reduce / 10000):.2f}\n
每 Tap Great 损失的完成度 |\n {10000 / total_score:.4f}%\n
每 50 落的损失的完成度 |\n {break_50_reduce / total_score * 100:.4f}%
50 落等价 Tap Great 数量 /个 | {(break_50_reduce / 100):.3f}\n
Break 数量 /个 | {brk}\n
具体情况的换算您可以查看帮助来帮助您换算。''')
        except Exception:
            await query_chart.send("格式错误，输入 “分数线 帮助” 以查看帮助信息")


best_40_pic = on_command('b40', aliases={'B40'})


@best_40_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    nickname = event.sender.nickname
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    img, success = await generate(payload)
    if success == 400:
        await best_40_pic.send(f"> To {nickname} | Best 40: 错误\n此玩家 ID 没有找到。\n请检查一下您的用户名是否输入正确或有无注册查分器系统？如您没有输入ID，请检查您的QQ是否与查分器绑定正确。\n若需要确认设置，请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/")
    elif success == 403:
        await best_40_pic.send(f'> To {nickname} | Best 40: 被禁止\n{username} 不允许使用此方式查询 Best 40。\n如果是您的账户，请检查您的QQ是否与查分器绑定正确后直接输入“b40”。\n您需要修改查分器设置吗？请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/')
    else:
        if username == "":
            text = f'> To {nickname} | Best 40\n您的 Best 40 如图所示。\n若您需要修改查分器数据，请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/'
        else:
            text = f'> To {nickname} | Best 40\n您查询的 ID: {username} 已找到。此 ID 的 Best 40 如图所示。\n'
        await best_40_pic.send(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(text),
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        ]))

best_50_pic = on_command('b50', aliases={'B50'})

@best_50_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    nickname = event.sender.nickname
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    payload['b50'] = True
    img, success = await generate(payload)
    if success == 400:
        await best_50_pic.send(f"> To {nickname} | Best 50 Simulator: 错误\n您输入的玩家 ID 没有找到。\n请检查一下您的用户名是否输入正确或有无注册查分器系统？如您没有输入ID，请检查您的QQ是否与查分器绑定正确。\n若需要确认设置，请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/")
    elif success == 403:
        await best_50_pic.send(f'> To {nickname} | Best 50 Simulator: 被禁止\n{username} 不允许使用此方式查询 Best 50。\n如果是您的账户，请检查您的QQ是否与查分器绑定正确后直接输入“b50”。\n您需要修改查分器设置吗？请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/')
    else:
        if username == "":
            text = f'> To {nickname} | Best 50 Simulator\n您的 Best 50 如图所示。\nBest 50 是 DX Splash Plus 及以后版本的定数方法，与当前版本的定数方法不相同。若您需要当前版本定数，请使用 Best 40。\n若您需要修改查分器数据，请参阅:\nhttps://www.diving-fish.com/maimaidx/prober/'
        else:
            text = f'> To {nickname} | Best 50 Simulator\n您查询的 ID: {username} 已找到。此 ID 的 Best 50 如图所示。\nBest 50 是 DX Splash Plus 及以后版本的定数方法，与当前版本的定数方法不相同。若您需要当前版本定数，请使用 Best 40。'
        await best_50_pic.send(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(text),
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        ]))
        
guess_dict: Dict[Tuple[str, str], GuessObject] = {}
guess_cd_dict: Dict[Tuple[str, str], float] = {}
guess_music = on_command('猜歌', priority=0)



async def guess_music_loop(bot: Bot, event: Event, state: T_State):
    await asyncio.sleep(10)
    guess: GuessObject = state["guess_object"]
    if guess.is_end:
        return
    cycle = state["cycle"]
    if cycle < 6:
        asyncio.create_task(bot.send(event, f"> 猜歌提示 | 第 {cycle + 1} 个 / 共 7 个\n这首歌" + guess.guess_options[cycle]))
    else:
        asyncio.create_task(bot.send(event, Message([
            MessageSegment.text("> 猜歌提示 | 第 7 个 / 共 7 个\n这首歌封面的一部分是："),
            MessageSegment.image("base64://" + str(guess.b64image, encoding="utf-8")),
            MessageSegment.text("快和群里的小伙伴猜一下吧！\n提示: 30 秒内可以回答这首歌的ID、歌曲标题或歌曲标题的大于5个字的连续片段，超时我将揭晓答案。")
        ])))
        asyncio.create_task(give_answer(bot, event, state))
        return
    state["cycle"] += 1
    asyncio.create_task(guess_music_loop(bot, event, state))


async def give_answer(bot: Bot, event: Event, state: T_State):
    await asyncio.sleep(30)
    guess: GuessObject = state["guess_object"]
    if guess.is_end:
        return
    asyncio.create_task(bot.send(event, Message([MessageSegment.text("> 答案\n都没有猜到吗......那现在揭晓答案！\nTrack ID:" + f"{guess.music['id']} > {guess.music['title']}\n"), MessageSegment.image(f"https://www.diving-fish.com/covers/{guess.music['id']}.jpg")])))
    del guess_dict[state["k"]]


@guess_music.handle()
async def _(bot: Bot, event: Event, state: T_State):
    mt = event.message_type
    k = (mt, event.user_id if mt == "private" else event.group_id)
    whitelists = get_driver().config.whitelists
    guess = GuessObject()
    guess_dict[k] = guess
    state["k"] = k
    state["guess_object"] = guess
    state["cycle"] = 0
    guess_cd_dict[k] = time.time() + 600
    await guess_music.send("> 猜歌\n我将从热门乐曲中选择一首歌，并描述它的一些特征。大家可以猜一下！\n知道答案的话，可以告诉我谱面ID、歌曲标题或者标题中连续5个以上的片段来向我阐述答案！\n猜歌时查歌等其他命令依然可用，这个命令可能会很刷屏。")
    asyncio.create_task(guess_music_loop(bot, event, state))

guess_music_solve = on_message(priority=20)

@guess_music_solve.handle()
async def _(bot: Bot, event: Event, state: T_State):
    mt = event.message_type
    k = (mt, event.user_id if mt == "private" else event.group_id)
    if k not in guess_dict:
        return
    ans = str(event.get_message())
    guess = guess_dict[k]
    # await guess_music_solve.send(ans + "|" + guess.music['id'])
    if ans == guess.music['id'] or (ans.lower() == guess.music['title'].lower()) or (len(ans) >= 5 and ans.lower() in guess.music['title'].lower()):
        guess.is_end = True
        del guess_dict[k]
        await guess_music_solve.finish(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("> 答案\n您猜对了！答案就是：\n" + f"Track ID: {guess.music['id']} > {guess.music['title']}\n"),
            MessageSegment.image(f"https://www.diving-fish.com/covers/{guess.music['id']}.jpg")
        ]))

waiting = on_command("人数")
@waiting.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    db = get_driver().config.db
    c = await db.cursor()
    err = 0
    if len(argv) == 1 and argv[0] == "":
        await c.execute(f"select * from waiting_table")
        data = await c.fetchone()
        if data is None:
            await waiting.send("当前没有任何店铺被添加，无法获取当前人数。")
        else:
            s = f"> 所有店铺出勤情况"
            while True:
                s += f"\n{data[1]} 出勤人数:{data[2]}"
                data = await c.fetchone()
                if data is None:
                    break
            await waiting.send(s)
            return
    elif len(argv) == 1 and argv[0] == "帮助":
        help_str = "人数 [店铺名/帮助] [加一/+1/减一/-1/清空/任意数字]\n- 帮助:显示此帮助文本\n- 加一/+1:需要在前面加店铺名。操作后此店铺的游玩人数记录+1。\n- 减一/-1:需要在前面加店铺名。操作后此店铺的游玩人数记录-1。\n- 清空:需要在前面家店铺名。操作后此店铺游玩人数纪录将重置。\n- 任意数字:需要在前面加店铺名。操作后此店铺游玩人数为自定义的人数。\n注意！所有店铺在 Kiba 加入的所有群之间是共享状态的，请不要轻易执行后两者操作。"
        await waiting.send(help_str)
        return
    elif len(argv) == 1 and argv[0] == "初始化":
        if str(event.get_user_id()) == Config.superuser:
            await c.execute(f'delete from waiting_table')
            await waiting.finish("店铺出勤人数的全部信息已重置。")
            return
        else:
            await waiting.finish("只有犽(Kiba)的运营者才可以执行此命令。")
            return
    elif len(argv) == 1:
        await c.execute(f'select * from waiting_table where shop="{argv[0]}"')
        data = await c.fetchone()
        if data is None:
            await waiting.send("当前店铺没有被添加，无法获取当前人数。如果是在店铺后面直接加了人数的话，您需要在它俩之间加个空格。")
        else:
            s = f"此店铺有 {data[2]} 人出勤。"
            await waiting.send(s)
            return
    elif len(argv) == 2:
        if argv[1] == "加一" or argv[1] == "+1":
            await c.execute(f'select * from waiting_table where shop="{argv[0]}"')
            data = await c.fetchone()
            if data is None:
                try:
                    await c.execute(f'insert into waiting_table values ({event.group_id}, "{argv[0]}", 1)')
                    await waiting.send(f"收到！当前 {argv[0]} 有 1 人出勤。")
                except Exception:
                    err = 1
                    await waiting.finish("现在没有店铺信息，需要您先在群内再发布一次才能添加店铺信息。")
            else:
                await c.execute(f'update waiting_table set waiting={data[2] + 1} where shop="{argv[0]}"')
                await waiting.send(f"收到！当前 {argv[0]} 有 {data[2] + 1} 人出勤。")
        elif argv[1] == "减一" or argv[1] == "-1":
            await c.execute(f'select * from waiting_table where shop="{argv[0]}"')
            data = await c.fetchone()
            if data is None:
                await waiting.send(f"收到！但是当前没有人报告此店铺或此店铺现在无人游玩。")
            else:
                if data[2] - 1 <= 0:
                    await c.execute(f'delete from waiting_table where shop="{argv[0]}"')
                    await waiting.send(f"收到！当前 {argv[0]} 无人出勤。")
                else:
                    await c.execute(f'update waiting_table set waiting={data[2] - 1} where shop="{argv[0]}"')
                    await waiting.send(f"收到！当前 {argv[0]} 有 {data[2] - 1} 人出勤。")
        elif argv[1] == "清空":
            await c.execute(f'delete from waiting_table where shop="{argv[0]}"')
            await waiting.send(f"收到！{argv[0]}的出勤人数已重置完成。\n警告:店铺的玩家数量在所有群之间是通用的。")
        else:
            try:
                if int(argv[1]) <= 0:
                    await c.execute(f'delete from waiting_table where shop="{argv[0]}"')
                    await waiting.send(f"收到！当前 {argv[0]} 无人出勤。")
                else:
                    await c.execute(f'select * from waiting_table where shop="{argv[0]}"')
                    data = await c.fetchone()
                    if data is None:
                        try:
                            await c.execute(f'insert into waiting_table values ({event.group_id}, "{argv[0]}", {int(argv[1])})')
                            await waiting.send(f"收到！当前 {argv[0]} 有 {int(argv[1])} 人出勤。")
                        except Exception:
                            err = 2
                            await waiting.finish("现在没有店铺信息，需要您先在群内再发布一次才能添加店铺信息。")
                    else:
                        await c.execute(f'update waiting_table set waiting={int(argv[1])} where shop="{argv[0]}"')
                        await waiting.send(f"收到！当前 {argv[0]} 有 {int(argv[1])} 人出勤。")
            except Exception:
                if err == 1 or err == 2:
                    return
                else:
                    await waiting.finish("出勤人数需要使用纯数字，不要掺杂或者完全使用一些奇奇怪怪的汉字秋梨膏！")

rand_ranking = on_command("段位模式")

@rand_ranking.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    argv = str(event.get_message()).strip().split(" ")
    try:
        if argv[0] == "帮助":
            rand_result = "> 段位模式帮助\n命令是:\n段位模式 <Expert/Master> <初级/中级/上级/超上级*>\n* 注意:超上级选项只对Master有效。"
        else:
            rand_result = f'> To {nickname} | Rand-Rank Tracks\nRank: {argv[0]} {argv[1]}\n'
            if argv[0] == "Expert" or argv[0] == "expert" or argv[0] == "EXPERT":
                if argv[1] == "初级":
                    level = ['7', '9']
                    life = 700
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 50
                elif argv[1] == "中级":
                    level = ['8', '10']
                    life = 600
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 50
                elif argv[1] == "上级":
                    level = ['10+', '12+']
                    life = 500
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 50
                else:
                    rand_ranking.send(f"> To {nickname} | Rand-Rank Tracks 错误\n寄，Expert 等级只有初级、中级、上级！")
                    return
            elif argv[0] == "Master" or argv[0] == "master" or argv[0] == "MASTER":
                if argv[1] == "初级":
                    level = ["10", "12"]
                    life = 700
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 50
                elif argv[1] == "中级":
                    level = ["12", "13"]
                    life = 500
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 50
                elif argv[1] == "上级":
                    level = ['13', '14']
                    life = 300
                    gr = -2
                    gd = -2
                    miss = -5
                    clear = 20
                elif argv[1] == "超上级":
                    level = ['14', '14+']
                    life = 100
                    gr = -2
                    gd = -3
                    miss = -5
                    clear = 10
                else:
                    rand_ranking.send(f"> To {nickname} | Rand-Rank Tracks 错误\n寄，Master 等级只有初级、中级、上级、超上级！")
                    return
            else:
                rand_ranking.send(f"> To {nickname} | Rand-Rank Tracks 错误\n寄，大等级只有Master、Expert！")
                return
            rand_result += f"\n本段位血量规则如下:\nLife: {life} -> Clear: +{clear}\nGreat: {gr} Good: {gd} Miss: {miss}\n\n"
            for i in range(4):
                music_data = total_list.filter(level=level, type=["SD", "DX"])
                rand_result += f'\n----- Track {i + 1} / 4 -----\n' + song_txt(music_data.random())
        await rand_ranking.send(rand_result)
    except Exception as e:
        await rand_ranking.finish("语法有错。如果您需要帮助请对我说‘段位模式 帮助’。")
