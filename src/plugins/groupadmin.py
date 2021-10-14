import random
import re

from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from random import randint

from collections import defaultdict

from nonebot.rule import to_me
from src.libraries.config import Config

driver = get_driver()

scheduler = require("nonebot_plugin_apscheduler").scheduler


selfban = on_command("烟我", rule=to_me())

@selfban.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        ids = event.get_session_id()
    except:
        pass
    else:
        if ids.startswith("group"):
            _, group_id, user_id = event.get_session_id().split("_")
            t = random.randint(1,600)
            try:
                await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=t)
                await selfban.send(f'好的！您被我烟了{t}秒（1-600秒随机），不能反悔嗷。')
            except Exception as e:
                print(e)
                await selfban.finish("我不是管理员，或者你是管理员/群主，所以....我烟个锤子。")
        else:
            await selfban.finish("私聊我烟个锤子。")