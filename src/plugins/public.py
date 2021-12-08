import random
import re

from PIL import Image
from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from src.libraries.image import *
from random import randint
import asyncio
from nonebot.adapters.cqhttp import Message, MessageSegment, GroupMessageEvent, PrivateMessageEvent

from nonebot.rule import to_me
from src.libraries.image import image_to_base64, path, draw_text, get_jlpx, text_to_image
from src.libraries.tool import hash

import time
import datetime
from collections import defaultdict
from src.libraries.config import Config

driver = get_driver()

scheduler = require("nonebot_plugin_apscheduler").scheduler

helper = on_command('help', aliases={'about'})

@helper.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await helper.send("☆>> 关于\n犽(Kiba) | Gon Plus\n版本: 2.7 (2.70.211209)\n----------------------\nGithub:\nhttps://github.com/Killua-Blitz/Kiba\nProject Kiba Credits:\n@Killua Blitz\n@Diving-Fish (Mai-Bot)\n@BlueDeer233 (maimaiDX)\n@Yuri-YuzuChaN (maimaiDX)\n----------------------\n☆>> 帮助\n查询舞萌模块帮助 maimai.help\n查询跑团模块帮助 coc.help\n查询其它模块帮助 others.help")
   
help_others = on_command('others.help')

@help_others.handle()
async def _(bot: Bot, event: Event, state: T_State):
    help_str = '''☆>> 其它模块可用命令 | Commands For Others                                              
------------------------------------------------------------------------------------------------------------------------------
戳一戳                                                                                  来戳戳我？

本群戳一戳情况                                                                    查看一下群里有几位杰出的无聊人

今日雀魂                                                                               查看今天的雀魂运势

mjxp                                                                                     看看你今天要做什么牌捏？

低情商<str1>高情商<str2>                                                 生成一张低情商高情商图片，
                                                                                              把str1/2换成自己的话。

gocho <str1> <str2>                                                         生成一张gocho图。

金龙盘旋 <str1> <str2> <str3>                                         生成一张金龙盘旋图。

投骰子<数量>                                                                       在线投骰子(?)
投百面骰子<数量>                                                             * 可以选择六面/百面

                                                                                              这个功能可以随机禁言你1-600秒，前提小犽是管理员。
烟我                                                                                    * 注意:为防止误触发，
                                                                                              这个功能你需要at一下小犽再说这个命令才能执行。

                                                                                               群里摇人。
随个[男/女]群友                                                                      你也可以不带参数直接说“随个”然后后面加啥都可以。
                                                                                               当然小犽容易骂你就是了。

帮选                                                                                      帮你选 

扔瓶子                                                                                   扔个瓶子给犽。说不定会被别人读到哦。

捞瓶子                                                                                    捞一个瓶子，看看上面留言什么了？


扔瓶子                                                                                   扔个瓶子给犽。说不定会被别人读到哦。

捞瓶子                                                                                   捞一个瓶子，看看上面留言什么了？

回复瓶子 <漂流瓶 ID>                                                         给这个瓶子做评论吧！
 
看回复 <漂流瓶 ID>                                                             查看漂流瓶下面的回复！


删瓶子 <漂流瓶 ID>                                                             删除您发布的漂流瓶。
                                                                                             * 管理员使用此指令可删除其他人瓶子。

当前瓶子数量                                                                        查询社区当前漂流瓶子数量，此命令不受社区限制。

我的漂流瓶                                                                           我的漂流社区情况
------------------------------------------------------------------------------------------------------------------------------

☆>> 管理员模块控制 | Administrative
------------------------------------------------------------------------------------------------------------------------------
设置漂流社区: 漂流瓶设置 <完全启(禁)用/启(禁)用扔瓶子/启(禁)用捞瓶子/启(禁)用扔瓶子/启(禁)用回复> <QQ号(可选)> <群号(可选)>
社区设置帮助请直接输入"漂流瓶设置"

设置戳一戳: 戳一戳设置 <启用/限制 (时间-秒)/禁用>
戳一戳帮助请直接输入"戳一戳设置"

删瓶子: 见上表可用命令中的说明，管理员允许删除任何人的漂流瓶。

------------------------------------------------------------------------------------------------------------------------------'''
    await help_others.send(Message([{
        "type": "image",
        "data": {
            "file": f"base64://{str(image_to_base64(text_to_image(help_str)), encoding='utf-8')}"
        }
    }]))


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and event.target_id == int(bot.self_id))
    return value


poke = on_notice(rule=_group_poke, priority=10, block=True)
poke_dict = defaultdict(lambda: defaultdict(int))

async def invoke_poke(group_id, user_id) -> str:
    db = get_driver().config.db
    ret = "default"
    ts = int(time.time())
    c = await db.cursor()
    await c.execute(f"select * from group_poke_table where group_id={group_id}")
    data = await c.fetchone()
    if data is None:
        await c.execute(f'insert into group_poke_table values ({group_id}, {ts}, 1, 0, "default")')
    else:
        t2 = ts
        if data[3] == 1:
            return "disabled"
        if data[4].startswith("limited"):
            duration = int(data[4][7:])
            if ts - duration < data[1]:
                ret = "limited"
                t2 = data[1]
        await c.execute(f'update group_poke_table set last_trigger_time={t2}, triggered={data[2] + 1} where group_id={group_id}')
    await c.execute(f"select * from user_poke_table where group_id={group_id} and user_id={user_id}")
    data2 = await c.fetchone()
    if data2 is None:
        await c.execute(f'insert into user_poke_table values ({user_id}, {group_id}, 1)')
    else:
        await c.execute(f'update user_poke_table set triggered={data2[2] + 1} where user_id={user_id} and group_id={group_id}')
    await db.commit()
    return ret

@poke.handle()
async def _(bot: Bot, event: Event, state: T_State):
    v = "default"
    if event.__getattribute__('group_id') is None:
        event.__delattr__('group_id')
    else:
        group_dict = poke_dict[event.__getattribute__('group_id')]
        group_dict[event.sender_id] += 1
        if v == "disabled":
            await poke.finish()
            return
    r = randint(1, 20)
    if v == "limited":
        await poke.send(Message([{
            "type": "poke",
            "data": {
                "qq": f"{event.sender_id}"
            }
        }]))
    elif r == 2:
        await poke.send(Message('戳你🐎'))
    elif r == 3:
        url = await get_jlpx('戳', '你妈', '闲着没事干')
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": url
            }
        }]))
    elif r == 4:
        img_p = Image.open(path)
        draw_text(img_p, '戳你妈', 0)
        draw_text(img_p, '有尝试过玩Cytus II吗', 400)
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": f"base64://{str(image_to_base64(img_p), encoding='utf-8')}"
            }
        }]))
    elif r == 5:
        await poke.send(Message('呜呜呜...不要再戳啦...'))
    elif r <= 7 and r > 5:
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/images/poke/{r - 5}.gif",
            }
        }]))
    elif r <= 12 and r > 7:
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/images/poke/{r - 7}.jpg",
            }
        }]))
    elif r <= 17 and r > 12:
        await poke.send(Message(f'好的....大家请各位戳刚刚戳我的那位。'))
    elif r <= 19 and r > 17:
        t = random.randint(60,90)
        try:
            await bot.set_group_ban(group_id=event.__getattribute__('group_id'), user_id=event.sender_id, duration=t)
            await poke.send(f'别戳了！！烟你{t}秒冷静一下。')
        except Exception as e:
            print(e)
            await poke.send(Message('一天到晚就知道戳戳戳，你不许戳了！(╬▔皿▔)╯'))
    elif r == 1:
        await poke.send(Message('一天到晚就知道戳戳戳，戳自己肚皮不行吗？'))
    else:
        await poke.send(Message([{
            "type": "poke",
            "data": {
                "qq": f"{event.sender_id}"
            }
        }]))

async def send_poke_stat(group_id: int, bot: Bot):
    if group_id not in poke_dict:
        return
    else:
        group_stat = poke_dict[group_id]
        sorted_dict = {k: v for k, v in sorted(group_stat.items(), key=lambda item: item[1], reverse=True)}
        index = 0
        data = []
        for k in sorted_dict:
            data.append((k, sorted_dict[k]))
            index += 1
            if index == 3:
                break
        await bot.send_msg(group_id=group_id, message="☆>> 戳一戳总结\n欢迎来到“金中指奖”的颁奖现场！\n接下来公布一下上次重启以来，本群最JB闲着没事 -- 干玩戳一戳的获奖者。")
        await asyncio.sleep(1)
        if len(data) == 3:
            await bot.send_msg(group_id=group_id, message=Message([
                {"type": "text", "data": {"text": "☆>> 戳一戳总结 - 铜牌\n铜中指奖的获得者是"}},
                {"type": "at", "data": {"qq": f"{data[2][0]}"}},
                {"type": "text", "data": {"text": f"!!\n累计戳了 {data[2][1]} 次！\n让我们恭喜这位闲的没事干的家伙！"}},
            ]))
            await asyncio.sleep(1)
        if len(data) >= 2:
            await bot.send_msg(group_id=group_id, message=Message([
                {"type": "text", "data": {"text": "☆>> 戳一戳总结 - 银牌\n银中指奖的获得者是"}},
                {"type": "at", "data": {"qq": f"{data[1][0]}"}},
                {"type": "text", "data": {"text": f"!!\n累计戳了 {data[1][1]} 次！\n这太几把闲得慌了，请用中指戳戳自己肚皮解闷!"}},
            ]))
            await asyncio.sleep(1)
        await bot.send_msg(group_id=group_id, message=Message([
            {"type": "text", "data": {"text": "☆>> 戳一戳总结 - 金牌\n最JB离谱的!!金中指奖的获得者是"}},
            {"type": "at", "data": {"qq": f"{data[0][0]}"}},
            {"type": "text", "data": {"text": f"!!!\nTA一共戳了{data[0][1]}次，此时此刻我想询问获奖者一句话:就那么喜欢听我骂你吗?"}},
        ]))


poke_stat = on_command("本群戳一戳情况")


@poke_stat.handle()
async def _(bot: Bot, event: Event, state: T_State):
    group_id = event.group_id
    await send_poke_stat(group_id, bot)


poke_setting = on_command("戳一戳设置")


@poke_setting.handle()
async def _(bot: Bot, event: Event, state: T_State):
    db = get_driver().config.db
    try:
        group_members = await bot.get_group_member_list(group_id=event.group_id)
        for m in group_members:
            if m['user_id'] == event.user_id:
                break
        if m['role'] != 'owner' and m['role'] != 'admin' and str(m['user_id']) not in Config.superuser:
            await poke_setting.finish("这个...只有管理员可以设置戳一戳, 但是你不要去戳我....嗯..尽量别戳啦。")
            return
    except Exception as e:
        await poke_setting.finish(f"!>> 戳一戳设置 - 现在是私聊？\n私聊设置个锤子戳一戳，你别戳不就完事了。如果不是，看下下面的错误记录。\nTechnical Information:\n{e}")
    argv = str(event.get_message()).strip().split(' ')
    try:
        if argv[0] == "默认":
            c = await db.cursor()
            await c.execute(f'update group_poke_table set disabled=0, strategy="default" where group_id={event.group_id}')
        elif argv[0] == "限制":
            c = await db.cursor()
            await c.execute(
                f'update group_poke_table set disabled=0, strategy="limited{int(argv[1])}" where group_id={event.group_id}')
        elif argv[0] == "禁用":
            c = await db.cursor()
            await c.execute(
                f'update group_poke_table set disabled=1 where group_id={event.group_id}')
        else:
            raise ValueError
        await poke_setting.send(f"√>> 戳一戳设置 - 成功\n戳一戳已成功设置为: {argv[0]}")
        await db.commit()
    except (IndexError, ValueError):
        await poke_setting.finish("☆>> 戳一戳设置 - 帮助\n本命令的格式:\n戳一戳设置 <默认/限制 (秒)/禁用>\n\n - 默认:将启用默认的戳一戳设定，包括随机性抽中禁言 1 - 1 分 30 秒。\n - 限制 (秒):在戳完一次 Kiba 的指定时间内，调用戳一戳只会让 Kiba 反过来戳你。在指定时间外时，与默认相同。\n- 禁用:禁用戳一戳的相关功能。")
    pass

shuffle = on_command('shuffle')


@shuffle.handle()
async def _(bot: Bot, event: Event):
    argv = int(str(event.get_message()))
    if argv > 100:
        await shuffle.finish('×>> 随机排列 - 数字过大\n随机排列太多了会刷屏，请输入100以内的数字。')
        return
    d = [str(i + 1) for i in range(argv)]
    random.shuffle(d)
    await shuffle.finish(','.join(d))

roll = on_regex(r"^([1-9]\d*)r([1-9]\d*)")

@roll.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([1-9]\d*)r([1-9]\d*)"
    groups = re.match(regex, str(event.get_message())).groups()
    try:
        num = random.randint(int(groups[0]),int(groups[1]))
        await roll.send(f"☆>> 随机数\n您的随机数是{num}。")
    except Exception:
        await roll.send("×>> 随机数 - 错误\n语法有错哦，您是不是输入的浮点数还是落了一个？或者左面比右面的数字大？这都是不可以的。")

tz = on_regex(r"^投骰子([1-9]\d*)")

@tz.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "投骰子([1-9]\d*)"
    groups = re.match(regex, str(event.get_message())).groups()
    try:
        if int(groups[0]) > 10:
            await roll.send("×>> 骰子 - 过多\n骰子数量不能大于10个。你是要刷屏嘛？")
        else:
            s = "☆>> 骰子\n结果如下:"
            for i in range(int(groups[0])):
                num = random.randint(1,6)
                s += f'\n第 {i + 1} 个骰子 投掷结果是: {num}点'
            await roll.send(s)
    except Exception:
        await roll.send("×>> 骰子 - 错误\n语法上可能有错哦。再检查一下试试吧！")

tz_100 = on_regex(r"^投百面骰子([1-9]\d*)")

@tz_100.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "投百面骰子([1-9]\d*)"
    groups = re.match(regex, str(event.get_message())).groups()
    try:
        if int(groups[0]) > 10:
            await roll.send("×>> 百面骰子 - 过多\n骰子数量不能大于10个。你是要刷屏嘛？")
        else:
            s = "☆>> 百面骰子\n结果如下:"
            for i in range(int(groups[0])):
                num = random.randint(1,100)
                s += f'\n第 {i + 1} 个骰子 投掷结果是: {num}点'
            await roll.send(s)
    except Exception:
        await roll.send("×>> 百面骰子 - 错误\n语法上可能有错哦。再检查一下试试吧！")

random_person = on_regex("随个([男女]?)群友")

@random_person.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        gid = event.group_id
        glst = await bot.get_group_member_list(group_id=gid, self_id=int(bot.self_id))
        v = re.match("随个([男女]?)群友", str(event.get_message())).group(1)
        if v == '男':
            for member in glst[:]:
                if member['sex'] != 'male':
                    glst.remove(member)
        elif v == '女':
            for member in glst[:]:
                if member['sex'] != 'female':
                    glst.remove(member)
        m = random.choice(glst)
        await random_person.finish(Message([
        {
            "type": "text",
            "data": {
                "text": f"☆>> To "
            }
        },
        {
            "type": "at",
            "data": {
                "qq": event.user_id
            }
        }, 
        {
            "type": "text",
            "data": {
                "text": f" | 随人\n{m['card'] if m['card'] != '' else m['nickname']}({m['user_id']})"
            }
        }]))
    except AttributeError:
        await random_person.finish("你不在群聊使用.....所以你随啥呢这是，这个要去群里用。")

snmb = on_command("随个", priority=19)

@snmb.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        gid = event.group_id
        if random.random() < 0.5:
            await snmb.finish(Message([
                {"type": "text", "data": {"text": "随你"}},
                {"type": "image", "data": {"file": "https://www.diving-fish.com/images/emoji/horse.png"}}
            ]))
        else:
            glst = await bot.get_group_member_list(group_id=gid, self_id=int(bot.self_id))
            m = random.choice(glst)
            await random_person.finish(Message([
            {
                    "type": "text",
                    "data": {
                        "text": f"☆>> To "
                }
            },
            {
                "type": "at",
                "data": {
                    "qq": event.user_id
                }
            },
            {
                "type": "text",
                "data": {
                    "text": f" | 随人\n{m['card'] if m['card'] != '' else m['nickname']}({m['user_id']})"
                }
            }]))
    except AttributeError:
        await random_person.finish("你不在群聊使用.....所以你随啥呢这是，这个要去群里用。")


select = on_command("帮选", aliases={"帮我选"})
@select.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    argv = str(event.get_message()).strip().split(" ")
    if len(argv) == 1:
        await select.finish("×>> 帮选 - 参数不足\n选你🐎。")
        return
    elif len(argv) is not None:
        result = random.randint(0, len(argv) - 1)
        await select.finish(f"☆>> 帮选\n我选 {argv[result]}。")
        return
    else:
        await select.finish("×>> 帮选 - 无参数\n选你🐎。")
        return

plp_settings = on_command("漂流瓶设置")

@plp_settings.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    try:
        if len(argv) == 3:
            success = 400
            group_members = await bot.get_group_member_list(group_id=argv[2])
            for m in group_members:
                if m['user_id'] == event.user_id:
                    success = 0
                    break
            if success != 0:
                await plp_settings.finish("!>> 漂流社区设置\n请检查您输入的群号，您不在此群或输错了号码。")
                return
            elif m['role'] != 'owner' and m['role'] != 'admin' and str(m['user_id']) not in Config.superuser:
                await plp_settings.finish("!>> 漂流社区设置\n请检查您输入的群号，您不是此群管理员或您输错了号码。")
                return
        else:
            group_members = await bot.get_group_member_list(group_id=event.group_id)
            for m in group_members:
                if m['user_id'] == event.user_id:
                    break
            if m['role'] != 'owner' and m['role'] != 'admin' and str(m['user_id']) not in Config.superuser:
                await plp_settings.finish("!>> 漂流社区设置\n这个...只有管理员可以设置漂流社区。")
                return
    except Exception as e:
        await plp_settings.finish(f"!>> 漂流社区设置 - 现在是私聊？\n群的瓶子开关在私聊是无法设置的，或您输入了错误的群号(犽不在这个群)。\n如果需要在私聊处理成员的拉黑，您需要在命令后面添加犽所在群号以便查验您是否为管理员。\n请在如果不是私聊，看下下面的错误记录。\nTechnical Information:\n{e}")
        return
    try:
        if argv[0] == "完全启用":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
                else:
                    await c.execute(f"update group_plp_table set disableinsert=0,disabletake=0,disablereply=0 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await plp_insert.finish(f"!>> To {nickname} | 漂流社区设置 - 限制人员功能\n您输入的 ID 没有在限制名单内。")
                else:
                    await c.execute(f"delete from plp_blacklist_table where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "完全禁用":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},1,1,1)')
                else:
                    await c.execute(f"update group_plp_table set disableinsert=1,disabletake=1,disablereply=1 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into plp_blacklist_table values ({argv[1]},{event.user_id},1,1,1)')
                else:
                    await c.execute(f"update plp_blacklist_table set lastbanner={event.user_id},disableinsert=1,disabletake=1,disablereply=1 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "启用扔瓶子":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
                else:
                    await c.execute(f"update group_plp_table set disableinsert=0 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await plp_insert.finish(f"!>> To {nickname} | 漂流社区设置 - 限制人员功能\n您输入的 ID 没有在限制名单内。")
                else:
                    await c.execute(f"update plp_blacklist_table set disableinsert=0 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "禁用扔瓶子":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},1,0,0)')
                else:
                    await c.execute(f"update group_plp_table set disableinsert=1 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into plp_blacklist_table values ({argv[1]},{event.user_id},1,0,0)')
                else:
                    await c.execute(f"update plp_blacklist_table set lastbanner={event.user_id},disableinsert=1 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "启用捞瓶子":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
                else:
                    await c.execute(f"update group_plp_table set disabletake=0 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await plp_insert.finish(f"!>> To {nickname} | 漂流社区设置 - 限制人员功能\n您输入的 ID 没有在限制名单内。")
                else:
                    await c.execute(f"update plp_blacklist_table set disabletake=0 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "禁用捞瓶子":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,1,0)')
                else:
                    await c.execute(f"update group_plp_table set disabletake=1 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into plp_blacklist_table values ({argv[1]},{event.user_id},0,1,0)')
                else:
                    await c.execute(f"update plp_blacklist_table set lastbanner={event.user_id},disabletake=1 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "启用回复":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
                else:
                    await c.execute(f"update group_plp_table set disablereply=0 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await plp_insert.finish(f"!>> To {nickname} | 漂流社区设置 - 限制人员功能\n您输入的 ID 没有在限制名单内。")
                else:
                    await c.execute(f"update plp_blacklist_table set disablereply=0 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        elif argv[0] == "禁用回复":
            if len(argv) == 1:
                await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,1)')
                else:
                    await c.execute(f"update group_plp_table set disablereply=1 where group_id={event.group_id}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 完成\n已成功设置为: {argv[0]}")
            else:
                await c.execute(f'select * from plp_blacklist_table where id={argv[1]}')
                data = await c.fetchone()
                if data is None:
                    await c.execute(f'insert into plp_blacklist_table values ({argv[1]},{event.user_id},0,0,1)')
                else:
                    await c.execute(f"update plp_blacklist_table set lastbanner={event.user_id},disablereply=1 where id={argv[1]}")
                await db.commit()
                await plp_insert.finish(f"√>> To {nickname} | 漂流社区设置 - 限制人员功能\n对象 {argv[1]} 已成功设置为: {argv[0]}")
        else:
            await plp_settings.send(f"☆>> To {nickname} | 漂流社区设置 - 帮助\n格式为:漂流瓶设置 <完全启（禁）用/禁（启）用扔瓶子/禁（启）用捞瓶子/禁（启）用回复> <(需要进行操作的)QQ号> <所在的群号(私聊情况下需要填写)>\n在不填写QQ号的情况下，默认是对您所在群的功能开关；填写QQ号后，转换为对此QQ号的功能开关。\n只能在处理QQ号时使用私聊。")
            return
    except Exception as e:
        print(e)
    

plp_insert = on_command("扔瓶子")

@plp_insert.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    now = datetime.datetime.now() 
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    try:
        await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
        data = await c.fetchone()
        if data is None:
            await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
            await db.commit()
        else:
            if data[1] == 1:
                await plp_insert.send(f"×>> To {nickname} | 漂流社区 - 扔瓶子 - 错误\n管理员已禁用扔瓶子功能，请联系群管理员获得详情。")
                return
    except Exception:
        pass
    try:
        await c.execute(f'select * from plp_blacklist_table where id={event.user_id}')
        data = await c.fetchone()
        if data is None:
            pass
        else:
            if data[2] == 1:
                await plp_insert.send(f"⛔>> To {nickname} | 漂流社区 - 扔瓶子 - 错误\n您的扔瓶子功能已被限制使用。")
                return
    except Exception:
        pass
    plpid = now.year * random.randint(1,7200) + now.month * random.randint(1,4800) + now.day * random.randint(1,2400) + now.hour * random.randint(1,1200)+ now.minute * random.randint(1,600) + now.second * random.randint(1,300) + random.randint(1,9999999999)
    try:
        if len(argv) > 1:
            allmsg = ""
            for i in range(len(argv)):
                allmsg += f"{argv[i]}"
            argv[0] = allmsg
        elif len(argv) == 1 and argv[0] == "":
            await plp_insert.send(f"☆>> To {nickname} | 漂流社区: 扔瓶子 - 帮助\n格式为:扔瓶子 瓶子内容.\n禁止发送黄赌毒、个人收款码等不允许发送的内容。否则将禁止个人使用此功能。")
            return
        elif argv[0].find("|") != -1:
            await plp_insert.send(f"×>> To {nickname} | 漂流社区: 扔瓶子 - 错误\n请不要在发送内容中加'|'，会干扰漂流瓶功能。")
            return
        if argv[0].find("CQ:image") != -1:
            message = argv[0].split("[")
            msg = message[0]
            piclink = message[1][57:].split("]")
            await c.execute(f'insert into plp_table values ({plpid},{event.user_id},"{nickname}","{msg}|{piclink[0]}",1,0,0)')
            await db.commit()
            await plp_insert.finish(f"√>> To {nickname} | 漂流社区: 扔瓶子 - 完成\n您的 图片 漂流瓶(ID: {plpid})已经扔出去啦!\n请注意: 如果您的瓶子包含了 R-18 (包括擦边球）以及任何不应在漂流瓶内出现的内容，您可能会受到漂流社区的部分功能封禁或相应处置。如果需要撤回瓶子，请使用 “删瓶子” 指令。")
            return
        else:
            await c.execute(f'insert into plp_table values ({plpid},{event.user_id},"{nickname}","{argv[0]}",0,0,0)')
            await db.commit()
            await plp_insert.finish(f"√>> To {nickname} | 漂流社区: 扔瓶子 - 完成\n您的 文字 漂流瓶(ID: {plpid})已经扔出去啦!\n请注意: 如果您的瓶子包含了不应在漂流瓶内出现的内容，您可能会受到漂流社区的部分功能封禁或相应处置。如果需要撤回瓶子，请使用 “删瓶子” 指令。")
            return
    except Exception as e:
        print(e)

plp_find = on_command("捞瓶子")

@plp_find.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    try:
        await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
        data = await c.fetchone()
        if data is None:
            await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
            await db.commit()
        else:
            if data[2] == 1:
                await plp_find.send(f"×>> To {nickname} | 漂流社区: 捞瓶子 - 错误\n管理员已禁用捞瓶子功能，请联系群管理员获得详情。")
                return
    except Exception:
        pass
    try:
        await c.execute(f'select * from plp_blacklist_table where id={event.user_id}')
        data = await c.fetchone()
        if data is None:
            pass
        else:
            if data[3] == 1:
                await plp_insert.send(f"⛔>> To {nickname} | 漂流社区 - 扔瓶子 - 错误\n您的捞瓶子功能已被限制使用。")
                return
    except Exception:
        pass
    try:
        if len(argv) > 1:
            await plp_find.finish(f"×>> To {nickname} | 漂流社区: 捞瓶子 - 错误\n只能输入QQ号查找。您输入了好多条分段数据.....")
        elif argv[0] == "":
            await c.execute(f'select * from plp_table order by random() limit 1')
            data = await c.fetchone()
            if data is None:
                await plp_find.finish(f"×>> To {nickname} | 漂流社区: 捞瓶子 - 没有瓶子\n啊呀....小犽这目前一个瓶子都莫得。要不先扔一个看看？")
                return
            else:
                if data[4] == 0:
                    await plp_find.send(f"☆>> To {nickname} | 漂流社区: 瓶子\nID: {data[0]} | {data[2]}({data[1]})\n👓 {data[5] + 1} | 💬 {data[6]}\n{data[3]}")
                    await c.execute(f"update plp_table set view={data[5] + 1} where id={data[0]}")
                    await db.commit()
                    return
                else:
                    message = data[3].split("|")
                    await plp_find.send(Message([
                        MessageSegment.text(f"☆>> To {nickname} | 漂流社区: 瓶子\nID: {data[0]} | {data[2]}({data[1]})\n👓 {data[5] + 1} | 💬 {data[6]}\n{message[0]}"),
                        MessageSegment.image(f"{message[1]}")    
                    ]))
                    await c.execute(f"update plp_table set view={data[5] + 1} where id={data[0]}")
                    await db.commit()
                    return
        else:
            await c.execute(f'select * from plp_table where user_id={argv[0]}')
            data = await c.fetchall()
            if len(data) == 0:
                await c.execute(f'select * from plp_table where id={argv[0]}')
                data = await c.fetchone()
                if data is None:
                    await plp_find.finish(f"×>> To {nickname} | 漂流社区: 捞瓶子 - 错误\n您输入的 QQ 号码没有扔瓶子或您输入的漂流瓶 ID 不存在。")
                    return
                else:
                    if data[4] == 0:
                        msg1 = f"☆>> To {nickname} | 漂流社区: 瓶子 - 定向 ID 查找: {argv[0]}\n{data[2]}({data[1]})\n👓 {data[5] + 1} | 💬 {data[6]}\n{data[3]}"
                        await plp_find.send(msg1)
                        await c.execute(f"update plp_table set view={data[5] + 1} where id={data[0]}")
                        await db.commit()
                        return
                    else:
                        message = data[3].split("|")
                        await plp_find.send(Message([
                            MessageSegment.text(f"☆>> To {nickname} | 漂流社区: 瓶子 - 定向 ID 查找: {argv[0]}\n{data[2]}({data[1]})\n👓 {data[5] + 1} | 💬 {data[6]}\n{message[0]}"),
                            MessageSegment.image(f"{message[1]}")
                        ]))
                        await c.execute(f"update plp_table set view={data[5] + 1} where id={data[0]}")
                        await db.commit()
                        return
            else:
                msg = f"☆>> To {nickname} | 漂流社区: 瓶子 - 定向 QQ 查找: {data[0][2]}({argv[0]})"
                if len(data) > 5:
                    msg += "\nta 扔的瓶子太多了，只显示最新四条消息。"
                    for i in range(len(data) - 4, len(data)):
                        if data[i][4] == 0:
                            msg += f"\n--------第 {i + 1} 条--------\nID: {data[i][0]}\n👓 {data[i][5] + 1} | 💬 {data[i][6]}\n{data[i][3]}"
                            await c.execute(f"update plp_table set view={data[i][5] + 1} where id={data[i][0]}")
                        else:
                            message = data[i][3].split("|")
                            msg += f"\n--------第 {i + 1} 条--------\nID: {data[i][0]}\n👓 {data[i][5] + 1} | 💬 {data[i][6]}\n{message[0]}\n[定向 QQ 查找不支持显示图片，您需要点击链接查看]\n{message[1]}"
                            await c.execute(f"update plp_table set view={data[i][5] + 1} where id={data[i][0]}")
                else:
                    for i in range(len(data)):
                        if data[i][4] == 0:
                            msg += f"\n--------第 {i + 1} 条--------\nID: {data[i][0]}\n👓 {data[i][5] + 1} | 💬 {data[i][6]}\n{data[i][3]}"
                            await c.execute(f"update plp_table set view={data[i][5] + 1} where id={data[i][0]}")
                        else:
                            message = data[i][3].split("|")
                            msg += f"\n--------第 {i + 1} 条--------\nID: {data[i][0]}\n👓 {data[i][5] + 1} | 💬 {data[i][6]}\n{message[0]}\n[定向 QQ 查找不支持显示图片，您需要点击链接查看]\n{message[1]}"
                            await c.execute(f"update plp_table set view={data[i][5] + 1} where id={data[i][0]}")
                await plp_find.send(msg)
                await db.commit()
    except Exception as e:
        pass

plp_clean = on_command("洗瓶子", rule=to_me())

@plp_clean.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    if str(event.user_id) not in Config.superuser:
        await plp_clean.finish(f"×>> To {nickname} | 漂流社区: 洗瓶子 - 没有权限\n这个...只有小犽的管理员才可以清空瓶子。")
        return
    else:
        await c.execute(f'delete from plp_table')
        await c.execute(f'delete from plp_reply_table')
        await db.commit()
        await plp_clean.finish(f"√>> To {nickname} | 漂流社区: 洗瓶子\n已清空漂流瓶数据。")
        return

plp_reply = on_command("回复瓶子")

@plp_reply.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    argv = str(event.get_message()).strip().split(" ")
    try:
        await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
        data = await c.fetchone()
        if data is None:
            await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
            await db.commit()
        else:
            if data[3] == 1:
                await plp_reply.send(f"×>> To {nickname} | 漂流社区: 回复瓶子 - 错误\n管理员已禁用瓶子评论回复功能，请联系群管理员获得详情。")
                return
    except Exception:
        pass
    try:
        await c.execute(f'select * from plp_blacklist_table where id={event.user_id}')
        data = await c.fetchone()
        if data is None:
            pass
        else:
            if data[4] == 1:
                await plp_insert.send(f"⛔>> To {nickname} | 漂流社区 - 扔瓶子 - 错误\n您的瓶子评论回复功能已被限制使用。")
                return
    except Exception:
        pass
    try:
        if len(argv) > 2 or len(argv) == 1 and argv[0] != "帮助":
            await plp_reply.finish(f"×>> To {nickname} | 漂流社区: 回复瓶子 - 错误\n参数输入有误。请参阅 “回复瓶子 帮助”")
        elif argv[0] == "帮助":
            await plp_reply.finish(f"×>> To {nickname} | 漂流社区: 回复瓶子 - 帮助\n命令格式是:\n回复瓶子 瓶子ID 回复内容\n注意回复无法带图片。")
        else:
            await c.execute(f'select * from plp_table where id={argv[0]}')
            data = await c.fetchone()
            if data is None:
                await plp_reply.finish(f"×>> To {nickname} | 漂流社区: 回复瓶子 - 错误\n没有这个瓶子捏。")
                return
            else:
                if argv[1].find("CQ:image") != -1:
                    await plp_reply.finish(f"×>> To {nickname} | 漂流社区: 回复瓶子 - 错误\n漂流瓶回复中不可以夹带图片！")
                    return
                else:
                    replyid = int(data[0] / random.randint(1,random.randint(199,9999)) * random.randint(random.randint(1,97), random.randint(101,199)))
                    await c.execute(f'insert into plp_reply_table values ({replyid},{argv[0]},{event.user_id},"{nickname}","{argv[1]}")')
                    await c.execute(f'update plp_table set reply={data[6] + 1} where id={argv[0]}')
                    await db.commit()
                    await plp_reply.finish(f"√>> To {nickname} | 漂流社区: 回复瓶子\n已成功回复 ID 是 {argv[0]} 的漂流瓶。")
    except Exception as e:
        print(e)


plp_reply_view = on_command("看回复")

@plp_reply_view.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    argv = str(event.get_message()).strip().split(" ")
    try:
        await c.execute(f'select * from group_plp_table where group_id={event.group_id}')
        data = await c.fetchone()
        if data is None:
            await c.execute(f'insert into group_plp_table values ({event.group_id},0,0,0)')
            await db.commit()
        else:
            if data[3] == 1:
                await plp_reply.send(f"×>> To {nickname} | 漂流社区: 回复 - 错误\n管理员已禁用瓶子评论回复功能，请联系群管理员获得详情。")
                return
    except Exception:
        pass
    try:
        await c.execute(f'select * from plp_blacklist_table where id={event.user_id}')
        data = await c.fetchone()
        if data is None:
            pass
        else:
            if data[4] == 1:
                await plp_insert.send(f"⛔>> To {nickname} | 漂流社区 - 扔瓶子 - 错误\n您的瓶子评论回复功能已被限制使用。")
                return
    except Exception:
        pass
    try:
        if len(argv) > 1 or argv[0] == "":
            await plp_reply_view.finish(f"×>> To {nickname} | 漂流社区: 回复 - 错误\n请输入漂流瓶 ID 来查看瓶子回复。")
        else:
            await c.execute(f'select * from plp_reply_table where plpid={argv[0]}')
            data = await c.fetchall()
            if len(data) == 0:
                await plp_reply_view.finish(f"☆>> To {nickname} | 漂流社区: 回复 - {argv[0]}\n现在这个瓶子一个评论都没有!来坐沙发吧。")
            else:
                msg = f"☆>> To {nickname} | 漂流社区: 回复 - {argv[0]}"
                for i in range(len(data)):
                    msg += f'\n#{i + 1} | Reply ID: {data[i][0]}\n{data[i][3]}({data[i][2]}): {data[i][4]}'
                await plp_reply_view.finish(msg)
    except Exception as e:
        print(e)

plp_num = on_command("当前瓶子数量")

@plp_num.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    await c.execute(f'select * from plp_table')
    data = await c.fetchall()
    await plp_num.finish(f"☆>> To {nickname} | 漂流社区\n现在全社区共有 {len(data)} 个漂流瓶。")

delete_plp = on_command("删瓶子")

@delete_plp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    c = await db.cursor()
    argv = str(event.get_message()).strip().split(" ")
    try:
        try:
            ids = event.get_session_id()
        except:
            pass
        else:
            if ids.startswith("group"):
                group_members = await bot.get_group_member_list(group_id=event.group_id)
                for m in group_members:
                    if m['user_id'] == event.user_id:
                        break
                if m['role'] != 'owner' and m['role'] != 'admin' and str(m['user_id']) not in Config.superuser:
                    await c.execute(f'select * from plp_table where id={argv[0]}')
                    data = await c.fetchone()
                    if data is None:
                        await delete_plp.finish("×>> 漂流社区\n找不到这个瓶子捏，看看您的 漂流瓶 ID 是否输入正确？")
                        return
                    else:
                        if event.user_id == data[1]:
                            await c.execute(f'delete from plp_table where id={argv[0]}')
                            await c.execute(f'delete from plp_reply_table where plpid={argv[0]}')
                            await db.commit()
                            await delete_plp.finish(f"√>> 漂流社区 - 删除完成\n已删除 ID 是 {argv[0]} 的漂流瓶。")
                            return
                        else:
                            await delete_plp.finish("×>> 漂流社区\n您没有相应的权限来删除此漂流瓶，您需要是管理员或您是瓶子发送者才有权限删除此瓶子。")
                            return
            else:
                await c.execute(f'select * from plp_table where id={argv[0]}')
                data = await c.fetchone()
                if data is None:
                    await delete_plp.finish("×>> 漂流社区\n找不到这个瓶子捏，看看您的 漂流瓶 ID 是否输入正确？")
                    return
                else:
                    if event.user_id == data[1]:
                        await c.execute(f'delete from plp_table where id={argv[0]}')
                        await c.execute(f'delete from plp_reply_table where plpid={argv[0]}')
                        await db.commit()
                        await delete_plp.finish(f"√>> 漂流社区 - 删除完成\n已删除 ID 是 {argv[0]} 的漂流瓶。")
                        return
                    else:
                        await delete_plp.finish("×>> 漂流社区\n您没有相应的权限来删除此漂流瓶，您需要是瓶子发送者才有权限删除此瓶子。如您是群管理员，请在群聊内使用此指令。")
                        return
    except Exception as e:
        return
    await c.execute(f'select * from plp_table where id={argv[0]}')
    data = await c.fetchone()
    if data is None:
        await delete_plp.finish("×>> 漂流社区\n找不到这个瓶子捏，看看您的 漂流瓶 ID 是否输入正确？")
        return
    else:
        await c.execute(f'delete from plp_table where id={argv[0]}')
        await c.execute(f'delete from plp_reply_table where plpid={argv[0]}')
        await db.commit()
        await delete_plp.finish(f"√>> 漂流社区 - 删除完成\n已删除 ID 是 {argv[0]} 的漂流瓶。")

my_plp = on_command("我的漂流瓶")

@my_plp.handle()
async def _(bot: Bot, event: Event, state: T_State):
    nickname = event.sender.nickname
    db = get_driver().config.db
    is_admin = 1
    is_black = 1
    baninsert = 1
    banreply = 1
    bantake = 1
    msg = f"☆>> To {nickname} | 我的漂流社区主页\n"
    c = await db.cursor()
    try:
        ids = event.get_session_id()
    except:
        pass
    else:
        if ids.startswith("group"):
            group_members = await bot.get_group_member_list(group_id=event.group_id)
            for m in group_members:
                if m['user_id'] == event.user_id:
                    break
            if m['role'] != 'owner' and m['role'] != 'admin':
                is_admin = 0
            if str(m['user_id']) in Config.superuser:
                is_admin = 2
        else:
            if str(event.user_id) in Config.superuser:
                is_admin = 2
            else:
                is_admin = -1
    await c.execute(f'select * from plp_blacklist_table where id={event.user_id}')
    data = await c.fetchone()
    if data is None:
        is_black = 0
        baninsert = 0
        banreply = 0
        bantake = 0
    else:
        if data[2] == 0:
            baninsert = 0
        if data[3] == 0:
            bantake = 0
        if data[4] == 0:
            banreply = 0
    if is_admin == -1:
        if is_black == 1:
            if baninsert == 0 and bantake == 0 and banreply == 0:
                msg += "👤 普通成员(非群聊无法确定是否为管理员)"
            elif baninsert == 1 and bantake == 1 and banreply == 1:
                msg += "👤 禁止使用"
            else:
                msg += "👤 限制功能"
        else:
            msg += "👤 普通成员(非群聊无法确定是否为管理员)"
    elif is_admin == 0:
        if is_black == 1:
            if baninsert == 0 and bantake == 0 and banreply == 0:
                msg += "👤 普通成员"
            elif baninsert == 1 and bantake == 1 and banreply == 1:
                msg += "👤 禁止使用"
            else:
                msg += "👤 限制功能"
        else:
            msg += "👤 普通成员"
    elif is_admin == 1:
        if is_black == 1:
            if baninsert == 0 and bantake == 0 and banreply == 0:
                msg += "👤 群管理员"
            else:
                msg += "👤 被限制功能的群管理员(可自行解除限制)"
        else:
            msg += "👤 群管理员"
    elif is_admin == 2:
        if is_black == 1:
            if baninsert == 0 and bantake == 0 and banreply == 0:
                msg += "👤 超级管理员"
            else:
                msg += "👤 被限制功能的超级管理员(可自行解除限制)"
        else:
            msg += "👤 超级管理员"
    await c.execute(f'select * from plp_table where user_id={event.user_id}')
    data2 = await c.fetchall()
    msg += f" | 🍾 {len(data2)}\n----------------------\n当前状态可使用以下社区功能:\n"
    if baninsert == 0:
        msg += "[√] 扔瓶子\n"
    else:
        msg += "[×] 扔瓶子\n"
    if bantake == 0:
        msg += "[√] 捞瓶子\n"
    else:
        msg += "[×] 捞瓶子\n"
    if banreply == 0:
        msg += "[√] 回复功能\n"
    else:
        msg += "[×] 回复功能\n"
    if len(data2) != 0:
        msg += "----------------------\n您扔过的漂流瓶的 ID 如下:"
        for i in range(len(data2)):
            if i == 0:
                msg += f"\n{data2[i][0]}"
            else:
                msg += f" {data2[i][0]}"
    await my_plp.finish(msg)