import random
import re

from PIL import Image
from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from src.libraries.image import *
from random import randint
import asyncio

from src.libraries.image import image_to_base64, path, draw_text, get_jlpx, text_to_image
from src.libraries.tool import hash

import time
from collections import defaultdict

driver = get_driver()

scheduler = require("nonebot_plugin_apscheduler").scheduler

help = on_command('help')


@help.handle()
async def _(bot: Bot, event: Event, state: T_State):
    help_str = '''Kiba
Build 2.11_release_patch_211005 |  Powered by BlitzR 2021.
本bot基于千雪Chiyuki开源项目并遵守MIT/反996协议。
==============================================
|   Mai-Bot Github: https://github.com/Diving-Fish/mai-bot                    | 
|   Chiyuki Github: https://github.com/Diving-Fish/Chiyuki-bot               |
|   GitHub: https://github.com/Blitz-Raynor/Kiba                                       |
==============================================
||                                              可用命令帮助                                                   ||
==============================================
今日舞萌/今日运势                             查看今天的舞萌运势
XXXmaimaiXXX什么                         随机一首歌
随个[dx/标准][绿黄红紫白]<难度>    随机一首指定条件的乐曲
查歌<乐曲标题的一部分>                  查询符合条件的乐曲
[绿黄红紫白]id<歌曲编号>                查询乐曲信息或谱面信息
<歌曲别名>是什么歌                         查询乐曲别名对应的乐曲
定数查歌 <定数下限> <定数上限>    查询定数对应的乐曲
分数线 <难度+歌曲id> <分数线>     详情请输入“分数线 帮助”查看
今日性癖/jrxp                                     看看你今天性什么东西捏？
戳一戳                                                来戳戳我？
本群戳一戳情况                                  查看一下群里有几位杰出的无聊人
今日雀魂                                             查看今天的雀魂运势
mjxp                                                   看看你今天要做什么牌捏？
=============================================='''
    await help.send(Message([{
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
        await poke.send(Message('妈你戳'))
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
    elif r <= 7:
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/images/poke/{r - 5}.gif",
            }
        }]))
    elif r <= 12:
        await poke.send(Message([{
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/images/poke/{r - 7}.jpg",
            }
        }]))
    elif r == 1:
        await poke.send(Message('戳你妈'))
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
        await bot.send_msg(group_id=group_id, message="欢迎来到“金中指奖”的颁奖现场！\n接下来公布一下上次重启以来，本群最JB闲着没事 -- 干玩戳一戳的获奖者。")
        await asyncio.sleep(1)
        if len(data) == 3:
            await bot.send_msg(group_id=group_id, message=Message([
                {"type": "text", "data": {"text": "铜中指奖的获得者是......"}},
                {"type": "at", "data": {"qq": f"{data[2][0]}"}},
                {"type": "text", "data": {"text": f"!!\n累计戳了 {data[2][1]} 次！\n让我们恭喜这位闲的没事干的家伙！"}},
            ]))
            await asyncio.sleep(1)
        if len(data) >= 2:
            await bot.send_msg(group_id=group_id, message=Message([
                {"type": "text", "data": {"text": "银中指奖的获得者是......"}},
                {"type": "at", "data": {"qq": f"{data[1][0]}"}},
                {"type": "text", "data": {"text": f"!!\n累计戳了 {data[1][1]} 次！\n这太几把闲得慌了，请用中指戳戳自己肚皮解闷!"}},
            ]))
            await asyncio.sleep(1)
        await bot.send_msg(group_id=group_id, message=Message([
            {"type": "text", "data": {"text": "最JB离谱的!!金中指奖的获得者是......"}},
            {"type": "at", "data": {"qq": f"{data[0][0]}"}},
            {"type": "text", "data": {"text": f"!!!\n......\nTA一共戳了{data[0][1]}次，此时此刻我想询问获奖者一句话:就那么喜欢听我骂你吗?"}},
        ]))


poke_stat = on_command("本群戳一戳情况")


@poke_stat.handle()
async def _(bot: Bot, event: Event, state: T_State):
    group_id = event.group_id
    await send_poke_stat(group_id, bot)

shuffle = on_command('shuffle')


@shuffle.handle()
async def _(bot: Bot, event: Event):
    argv = int(str(event.get_message()))
    if argv > 100:
        await shuffle.finish('请输入100以内的数字')
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
        await roll.send(f"随机数是{num}.")
    except Exception:
        await roll.send("...语法有错哦，您是不是输入的浮点数还是落了一个？这都是不可以的。")
