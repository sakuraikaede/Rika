import aiosqlite
import sqlite3
import asyncio
import nonebot
from nonebot.log import logger

driver: nonebot.Driver = nonebot.get_driver()
config: nonebot.config.Config = driver.config


@driver.on_startup
async def init_db():
    config.db = await aiosqlite.connect("src/static/Rika.db")
    logger.info("Rika Kernel -> Starting to Create \"Rika Database\"")
    try:
        await config.db.executescript(
            "create table group_poke_table (group_id bigint primary key not null, last_trigger_time int, triggered int, disabled bit, strategy text);"
            "create table user_poke_table (user_id bigint, group_id bigint, triggered int);"
            "create table guess_table (group_id bigint, enabled bit);"
            "create table waiting_table (shop text, location text, wait int, updated text);"
            "create table plp_table (id bigint, user_id bigint, nickname text, message text, is_picture bit, view bigint, reply bigint);"
            "create table plp_reply_table (id bigint, plpid bigint, userid bigint, nickname text, message text);"
            "create table group_plp_table (group_id bigint, disableinsert int, disabletake int, disablereply int);"
            "create table plp_blacklist_table (id bigint, lastbanner bigint, disableinsert int, disabletake int, disablereply int)"
            )
        logger.info("Rika Kernel -> Create \"Rika Database\" successfully")
    except Exception:
        logger.info("Rika Kernel --Skip-> Database Created....Skipped Creating Databases.")
        pass

@driver.on_shutdown
async def free_db():
    await config.db.close()