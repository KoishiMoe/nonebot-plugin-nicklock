import asyncio

from nonebot import require, logger, on_message, get_driver
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from .config import config

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

my_bot: Bot = None

driver = get_driver()


@scheduler.scheduled_job("cron", minute='*/5', id="ResetNickName")
async def auto_reset():
    if not my_bot: 
        return
    assert isinstance(my_bot, Bot)
    for group in config.groups:
        if await is_group_admin(my_bot, int(group), int(my_bot.self_id)):
            for member, nick in config.get(group).items():
                try:
                    info = await my_bot.get_group_member_info(group_id=int(group), user_id=int(member))
                    if info.get('card', '') != nick:
                        await my_bot.set_group_card(group_id=int(group), user_id=int(member), card=nick)
                        logger.debug(f"已在群 {group} 中将成员 {member} 的名片重置为 {nick}")
                        await my_bot.get_group_member_info(group_id=int(group), user_id=int(member), no_cache=True)  # 刷新缓存
                        await asyncio.sleep(0.5)
                except Exception as e:
                    logger.info(f"在群 {group} 中恢复成员 {member} 的群名片失败: {e}")


listener = on_message(block=False)


@listener.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if str(event.group_id) in config.groups:  # 框架获取成员信息有缓存，按理说应该不会造成很大负载……大概……
        cfg = config.get(str(event.group_id))
        locked_nick = cfg.get(str(event.sender.user_id))
        if await is_group_admin(bot, event.group_id, event.self_id) and locked_nick and locked_nick != (event.sender.card or event.sender.nickname):
            try:
                await bot.set_group_card(group_id=event.group_id, user_id=event.sender.user_id, card=locked_nick)
                logger.debug(f"已在群 {event.group_id} 中将成员 {event.sender.user_id} 的名片重置为 {locked_nick}")
            except Exception as e:
                logger.info(f"在群 {event.group_id} 中恢复成员 {event.sender.user_id} 的群名片失败: {e}")


async def is_group_admin(bot: Bot, gid: int, uid: int) -> bool:
    try:
        member_info = await bot.get_group_member_info(group_id=gid, user_id=uid, no_cache=True)
        return member_info.get("role") in ("owner", "admin")
    except Exception as e:
        logger.warning(f"获取群{gid}成员{uid}的信息时发生了错误：{e}")
        return False


@driver.on_bot_connect
async def _get_bot(bot: Bot):
    global my_bot
    my_bot = bot


@driver.on_bot_disconnect
async def _del_bot(bot: Bot):
    global my_bot
    my_bot = None
