from collections import defaultdict

from nonebot import on_command, on_regex
from nonebot.typing import T_State
from nonebot.adapters import Event, Bot
from nonebot.adapters.cqhttp import Message, MessageSegment, GroupMessageEvent, PrivateMessageEvent

from src.libraries.tool import hash
from src.libraries.maimaidx_music import *
from src.libraries.image import *
from src.libraries.maimai_best_40 import generate
import re

import datetime


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
                "text": f" 🆔 {music.id} >> {music.title}\n谱面对应等级:"
            }
        },
        {
            "type": "text",
            "data": {
                "text": f"\n{' | '.join(music.level)}"
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
    else:
        result_set = inner_level_q(float(argv[0]), float(argv[1]))
    if len(result_set) > 50:
        await inner_level.finish(f"结果过多（{len(result_set)} 条），请缩小搜索范围。")
        return
    s = ""
    for elem in result_set:
        s += f"{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
    await inner_level.finish(s.strip())


spec_rand = on_regex(r"^随个(?:dx|sd|标准)?[绿黄红紫白]?[0-9]+\+?")


@spec_rand.handle()
async def _(bot: Bot, event: Event, state: T_State):
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
            rand_result = "啊....没有这样的乐曲啦。"
        else:
            rand_result = song_txt(music_data.random())
        await spec_rand.send(rand_result)
    except Exception as e:
        print(e)
        await spec_rand.finish("随机命令出错了...检查一下语法吧？")



mr = on_regex(r".*maimai.*什么")


@mr.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await mr.finish(song_txt(total_list.random()))


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
        search_result = ""
        for music in sorted(res, key = lambda i: int(i['id'])):
            search_result += f"搜索到以下内容:\n{music['id']}. {music['title']}\n"
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
            level_name = ['Basic', 'Advanced', 'Expert', 'Master', 'Re: MASTER']
            name = groups[1]
            music = total_list.by_id(name)
            chart = music['charts'][level_index]
            ds = music['ds'][level_index]
            level = music['level'][level_index]
            file = f"https://www.diving-fish.com/covers/{music['id']}.jpg"
            if len(chart['notes']) == 4:
                msg = f'''Standard | {level_name[level_index]} > Lv {level}
Base> {ds}
ALL> {chart['notes'][0] + chart['notes'][1] + chart['notes'][2] + chart['notes'][3]}
TAP> {chart['notes'][0]}
HOLD> {chart['notes'][1]}
SLIDE> {chart['notes'][2]}
BREAK> {chart['notes'][3]}
Notes Designer> {chart['charter']}'''
            else:
                msg = f'''DX | {level_name[level_index]} > Lv {level}
Base> {ds}
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
                        "text": f"🆔{music['id']} >> {music['title']}\n"
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
                        "text": f"🆔 {music['id']} >> {music['title']}\n"
                    }
                },  
                {
                    "type": "text",
                    "data": {
                        "text": f"曲师/演唱> {music['basic_info']['artist']}\n分类> {music['basic_info']['genre']}\nBPM> {music['basic_info']['bpm']}\n版本> {music['basic_info']['from']}\n谱面难度> {' | '.join(music['level'])}"
                    }
                }
            ]))
        except Exception:
            await query_chart.send("啊这...我没有找到这个歌。\n换一个试试吧。")

xp_list = ['滴蜡熊', '幸隐', '14+', '白潘', '紫潘', 'PANDORA BOXXX', '排队区', '旧框', '干饭', '超常maimai', '收歌', '福瑞', '削除', 'HAPPY', '谱面-100号', 'lbw', '茄子卡狗', '打五把CSGO', '一姬', '打麻将', '光吉猛修', '怒锤', '暴漫']

jrxp = on_command('jrxp', aliases={'今日性癖'})


@jrxp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    h = hash(qq)
    rp = h % 100
    xp = random.randint(0,22)
    s = f"今天你的人品大约是 {rp}% !\n"
    s += f"容我算一下.....\n你今天的XP是{xp_list[xp]}! \n不满意的话再随一个也是没有问题的。"
    await jrxp.finish(Message([
        {"type": "text", "data": {"text": s}}
    ]))


wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌', '理论值', '打东方曲', '打索尼克曲']
bwm_list_perfect = ['拆机:然后您被机修当场处决', '女装:怎么这么好康！（然后受到了欢迎）', '耍帅:看我耍帅还AP+', '击剑:Alea jacta est!(SSS+)', '打滴蜡熊:看我今天不仅推了分，还收了歌！', '日麻:看我三倍役满!!!你们三家全都起飞!!!', '出勤:不出则已，一出惊人，当场AP，羡煞众人。', '看手元:哦原来是这样！看了手元果真推分了。', '霸机:这么久群友都没来，霸机一整天不是梦！']
bwm_list_bad = ['拆机:不仅您被机修当场处决，还被人尽皆知。', '女装:杰哥说你怎么这么好康！让我康康！！！（被堵在卫生间角落）', '耍帅:星星全都粉掉了......', '击剑:Alea jacta est!(指在线下真实击剑)', '打滴蜡熊:滴蜡熊打你。', '日麻:我居然立直放铳....等等..三倍役满??????', '出勤:当场分数暴毙，惊呆众人。', '看手元:手法很神奇，根本学不来。', '霸机:......群友曰:"霸机是吧？踢了！"']
tips_list = ['在游戏过程中,请您不要大力拍打或滑动机器!', '建议您常多备一副手套！如果游玩时手套破裂或许会有大用！', '游玩时注意手指安全！意外戳到边框时若引发剧烈疼痛请立刻下机以休息手指，必要时可以选择就医。', '游玩过程中注意财物安全。自己的财物远比一个SSS+要更有价值。', '底力不够？建议下埋！不要强行越级，手癖难解。', '文明游玩，游戏要排队，不要做不遵守游戏规则的玩家！', '人品值和宜忌每天0点都会刷新，不喜欢总体运势可以通过这个指令再随一次。', '疫情防护，人人有责。在游玩结束后请主动佩戴口罩！', '出勤时注意交通安全，身体安全永远在第一位！']

jrwm = on_command('今日运势', aliases={'今日舞萌'})

@jrwm.handle()
async def _(bot: Bot, event: Event, state: T_State):   
    qq = int(event.get_user_id())
    nickname = event.sender.nickname
    h = hash(qq)
    rp = h % 100
    luck = int((rp * 4 + 23) / 3 % 100)
    ap = int((luck * 4) / 6 * 9 % 100)
    wm_value = []
    good_value = {}
    bad_value = {}
    good_count = 0
    bad_count = 0
    dwm_value_1 = random.randint(0,8)
    dwm_value_2 = random.randint(0,8)
    tips_value = random.randint(0,8)
    now = datetime.datetime.now()  
    for i in range(14):
        wm_value.append(h & 3)
        h >>= 2
    s = f"⏲️ → {now.year}/{now.month}/{now.day} {now.hour}:{now.strftime('%M')}:{now.strftime('%S')}\n👨‍ → {nickname}"
    s += f"\n\n今日运势 | Date Fortune →\n\n运气之签 ↓\n--------------------\n"
    s += f"人品值: {rp}%\n"
    s += f"幸运度: {luck}%\n"
    if rp >= 50 and rp < 70:
        s += "            小吉\n"
    elif rp >= 70 and rp < 90:
        s += "             吉\n"
    elif rp >= 90:
        s += "            大吉\n"
    elif rp >= 30 and rp < 50:
        s += "            小凶\n"
    elif rp >= 10 and rp < 30:
        s += "             凶\n"
    else:
        s += "            大凶\n"
    s += f"收歌率: {ap}%\n--------------------\n\n日常运势 ↓\n"

    if dwm_value_1 == dwm_value_2:
        s += f'平 > 今天总体上平平无常。向北走有财运，向南走运不佳....等一下，这句话好像在哪儿听过？\n'
    else:
        s += f'宜 > {bwm_list_perfect[dwm_value_1]}\n'
        s += f'忌 > {bwm_list_bad[dwm_value_2]}\n'
    s += "\n舞萌运势 | Maimai Fortune →\n"
    for i in range(14):
        if wm_value[i] == 3:
            good_value[good_count] = i
            good_count = good_count + 1
        elif wm_value[i] == 0:
            bad_value[bad_count] = i
            bad_count = bad_count + 1
    if good_count == 0:
        s += "宜 | 🚫 今日诸事不宜"
    else:
        s += f'宜 | 共 {good_count} 项 >\n'
        for i in range(good_count):
            s += f'{wm_list[good_value[i]]} '
    if bad_count == 0:
        s += '\n忌 | ✔️ 今日无所畏忌\n'
    else:
        s += f'\n忌 | 共 {bad_count} 项 >\n'
        for i in range(bad_count):
            s += f'{wm_list[bad_value[i]]} '
    s += f"\n\nKiba Tips →\n{tips_list[tips_value]}\n"
    s += "\n运势推荐 | Recommendation →\n"
    music = total_list[h % len(total_list)]
    await jrwm.finish(Message([
        {"type": "text", "data": {"text": s}}
    ] + song_txt(music)))

jrrp = on_command('jrrp', aliases={'今日人品'})

@jrrp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    h = hash(qq)
    rp = h % 100
    wm_value = []
    dwm_value_1 = random.randint(0,6)
    dwm_value_2 = random.randint(0,6)
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    s = f"今天的人品值是 {rp}%\n可以看看jrxp或者运势吼。"
    await jrrp.finish(Message([
        {"type": "text", "data": {"text": s}}
    ]))

jrgq = on_command('今日推荐')

@jrgq.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = int(event.get_user_id())
    h = hash(qq)
    rp = h % 100
    s = "我算算哈...今天推荐你这首歌吧:\n"
    music = total_list[h % len(total_list)]
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
    if name not in music_aliases:
        await find_song.finish("可能这个别称太新了.....抱歉我找不到这首歌啦.....")
        return
    result_set = music_aliases[name]
    if len(result_set) == 1:
        music = total_list.by_title(result_set[0])
        await find_song.finish(Message([{"type": "text", "data": {"text": "OHHH!! 我猜您要找的应该是：\n"}}] + song_txt(music)))
    else:
        s = '\n'.join(result_set)
        await find_song.finish(f"您要找的可能是以下歌曲中的其中一首：\n{ s }")


query_score = on_command('分数线')


@query_score.handle()
async def _(bot: Bot, event: Event, state: T_State):
    r = "([绿黄红紫白])(id)?([0-9]+)"
    argv = str(event.get_message()).strip().split(" ")
    if len(argv) == 1 and argv[0] == '帮助':
        s = '''这个功能为你提供达到某首歌分数线的最低标准而设计的~~~
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
            await query_chart.send(f'''{music['title']} {level_labels2[level_index]}这首歌，如果想要达到 {line}% 的话,
可以允许有 {(total_score * reduce / 10000):.2f}个TAP GREAT(每个损失 {10000 / total_score:.4f}% 达成率),
其中，这首歌的BREAK 50落(本谱面共{brk}个BREAK)等价于 {(break_50_reduce / 100):.3f} 个 TAP GREAT(每个50落损失 {break_50_reduce / total_score * 100:.4f}% 达成率)
具体情况的换算您可以查看帮助来帮助您换算。''')
        except Exception:
            await query_chart.send("格式错误，输入“分数线 帮助”以查看帮助信息")


best_40_pic = on_command('b40')


@best_40_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    img, success = await generate(payload)
    if success == 400:
        await best_40_pic.send("没有找到此玩家....请确保此玩家的用户名和查分器中的用户名相同。\n需要修改查分器数据吗？请参阅 https://www.diving-fish.com/maimaidx/prober/")
    elif success == 403:
        await best_40_pic.send("用户禁止了其他人获取数据。需要修改查分器数据吗？请参阅 https://www.diving-fish.com/maimaidx/prober/")
    else:
        await best_40_pic.send(Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text("下方是查询结果。需要修改查分器数据吗？请参阅 https://www.diving-fish.com/maimaidx/prober/"),
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        ]))

