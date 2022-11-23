from json import loads

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER

from .config import config

nicklock = on_command('nicklock', aliases={'昵称锁定', '昵称锁', '名片锁'})


@nicklock.handle()
async def _(bot: Bot, event: GroupMessageEvent, raw_command: str = RawCommand()):
    msg = event.message.extract_plain_text()[len(raw_command):].strip()
    if not msg:
        await _help(bot, event)
        await nicklock.finish()
    at = check_at(event.json())
    params = msg.split()
    cfg = config.get(str(event.group_id))
    if params[0] == 'lock':
        if at:
            if not (await SUPERUSER(bot, event) or event.sender.role in ['owner', 'admin']):
                await nicklock.finish('你没有权限锁定他人的名片')
            if 'all' in at:
                members = await bot.get_group_member_list(group_id=event.group_id)
                for member in members:
                    cfg[str(member['user_id'])] = member.get('card', member.get('nickname', ''))
            for qq in at:
                info = await bot.get_group_member_info(group_id=event.group_id, user_id=qq, no_cache=True)
                cfg[str(qq)] = info.get('card', info.get('nickname', ''))
        if len(params) == 1:
            cfg[str(event.sender.user_id)] = event.sender.card or event.sender.nickname
        else:
            if not (await SUPERUSER(bot, event) or event.sender.role in ['owner', 'admin']):
                await nicklock.finish('你没有权限锁定他人的名片')
            for qq in params[1:]:
                if qq.isdigit():
                    info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(qq), no_cache=True)
                    cfg[str(qq)] = info.get('card', info.get('nickname', ''))
        config.save()
        await nicklock.finish('锁定成功')
    elif params[0] == 'unlock':
        if at:
            if not (await SUPERUSER(bot, event) or event.sender.role in ['owner', 'admin']):
                await nicklock.finish('你没有权限解锁他人的名片')
            if 'all' in at:
                cfg.clear()
            else:
                for qq in at:
                    cfg.pop(str(qq), None)
        if len(params) == 1 and not at:
            cfg.pop(str(event.sender.user_id), None)
        else:
            if not (await SUPERUSER(bot, event) or event.sender.role in ['owner', 'admin']):
                await nicklock.finish('你没有权限解锁他人的名片')
            for qq in params[1:]:
                if qq.isdigit():
                    cfg.pop(qq, None)
        config.save()
        await nicklock.finish('解锁成功')
    elif params[0] == 'status':
        enabled = []
        if at:
            if not (await SUPERUSER(bot, event) or event.sender.role in ['owner', 'admin']):
                await nicklock.finish('你没有权限查看他人的名片锁状态')
            if 'all' in at:
                enabled = list(cfg.keys())
            else:
                enabled = [qq for qq in at if qq in cfg]
        if len(params) == 1 and not at:
            await nicklock.finish(f"你{'已' if str(event.sender.user_id) in cfg else '未'}开启名片锁")
        else:
            enabled += [qq for qq in params[1:] if qq in cfg]
            await nicklock.finish(f"{' '.join(enabled)}已开启名片锁" if enabled else "这些用户均未开启名片锁")


async def _help(bot: Bot, event: MessageEvent):
    await bot.send(event, '使用/nicklock lock 为名片加锁， /nicklock unlock 为名片解锁， /nicklock status 查看名片锁状态\n'
                          '管理员可以在群内使用/nicklock lock [QQ号或@] 为指定成员加锁， /nicklock unlock [QQ号或@] 为指定成员解锁\n')


def check_at(data: str) -> list:
    """
    检测at了谁，返回[qq, qq, qq,...]
    包含全体成员直接返回['all']
    如果没有at任何人，返回[]
    来自 https://github.dev/yzyyz1387/nonebot_plugin_admin
    :param data: event.json
    :return: list
    """
    try:
        qq_list = []
        data = loads(data)
        for msg in data["message"]:
            if msg["type"] == "at":
                if 'all' not in str(msg):
                    qq_list.append(int(msg["data"]["qq"]))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []
