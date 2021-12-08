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


selfban = on_command("烟我", aliases={'抽奖'}, rule=to_me())

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
                await selfban.send(f'☆>> 自助禁言\n好的！您被我烟了{t}秒（1-600秒随机），不能反悔嗷。')
            except Exception as e:
                print(e)
                await selfban.finish(f"!>> 自助禁言 - 出现问题\n我不是管理员，或者你是管理员/群主，所以....我烟个锤子。\n[Exception Occurred]\n{e}")
        else:
            await selfban.finish("私聊我烟个锤子。")

ban = on_command("禁言", rule=to_me(),  priority=17)

@ban.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    if argv[0] == "":
        await ban.finish("×>> 随机时长禁言 - 无账号\n没有账号我禁个锤子。")
    else:
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
                        await poke_setting.finish("你不是管理烟个锤子哦。")
                        return
                _, group_id, user_id = event.get_session_id().split("_")
                t = random.randint(1,900)
                try:
                    await bot.set_group_ban(group_id=group_id, user_id=argv[0], duration=t)
                    await selfban.send(f'☆>> 随机时长禁言\n好的！ta已经被烟了{t}秒（1-900秒随机）。')
                except Exception as e:
                    print(e)
                    await selfban.finish(f"!>> 自助禁言 - 出现问题\n我不是管理员，或者ta是管理员/群主，或者这个QQ号不在这个群，所以....我烟个锤子。\n[Exception Occurred]\n{e}")
            else:
                await selfban.finish("私聊我烟个锤子。")