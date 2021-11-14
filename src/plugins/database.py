import aiosqlite
import sqlite3
import asyncio
import nonebot
from nonebot.log import logger

driver: nonebot.Driver = nonebot.get_driver()
config: nonebot.config.Config = driver.config


@driver.on_startup
async def init_db():
    config.db = await aiosqlite.connect("src/static/Kiba.db")
    logger.info("Kiba Kernel -> Load \"Kiba Database\" successfully")
    try:
        await config.db.executescript(
            "create table group_poke_table (group_id bigint primary key not null, last_trigger_time int, triggered int, disabled bit, strategy text);"
            "create table user_poke_table (user_id bigint, group_id bigint, triggered int);"
            "create table guess_table (group_id bigint, enabled bit);"
            "create table waiting_table (group_id bigint, shop text, waiting int);"
            "create table plp_table (id bigint, user_id bigint, message text);"
            )
        logger.info("Kiba Kernel -> Create \"Kiba Database\" successfully")
    except Exception:
        logger.info("Kiba Kernel --WARNING!-> Cannot Create Database! You may need to create database manually.")
        pass

@driver.on_shutdown
async def free_db():
    await config.db.close()