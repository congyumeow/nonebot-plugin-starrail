import sys

from nonebot.typing import T_State
from nonebot import on_command
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

try:
    from nonebot.adapters.onebot.v11 import (Bot, GroupMessageEvent, Message,
                                             MessageEvent, MessageSegment,
                                             PrivateMessageEvent)
except ImportError:
    from nonebot.adapters.cqhttp import Bot, Message, MessageSegment
    from nonebot.adapters.cqhttp.event import (GroupMessageEvent, MessageEvent,
                                               PrivateMessageEvent)

from .data_source import getGachaData, checkAuthkey, getCacheData, alterAuthkey
from .data_render import getInfoImages, mergeImage, drewPie, getStat

__starrail_version__ = "v1.0.0"
__tarot_usages__ = f'''
崩铁抽卡记录 {__starrail_version__}
[崩铁抽卡记录] 显示崩铁抽卡分析图
[更新抽卡地址] 抽卡记录authkey失效时更新抽卡地址,建议私聊使用'''.strip()
__plugin_meta__ = PluginMetadata(
    name="崩铁抽卡记录分析",
    description="崩铁抽卡记录分析",
    usage=__tarot_usages__,
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)
gMatcher = on_command("崩铁抽卡记录", aliases={"btckjl"}, priority=1)
aMatcher = on_command("更新抽卡地址", aliases={"更新authkey"}, priority=1)

@gMatcher.handle()
async def gachaHistory(bot: Bot,event: MessageEvent, state: T_State):
    q = event.get_user_id()
    s = event.get_plaintext()
    c = await getCacheData(q)
    # 群聊用户不在缓存中且没有输入链接，结束会话
    if c["msg"] == "暂无本地抽卡记录！":
        if isinstance(event, GroupMessageEvent) and s in ["", "-f", "--force"]:
            c["msg"] += "请在私聊中使用「抽卡记录」命令添加抽卡记录链接！"
            await gMatcher.finish(Message(c["msg"]))
    # 检测到缓存的用户将缓存数据传递至 got 方法进一步判断
    else:
        state["cache"] = c
        state["url"] = c["data"]["url"]
    # 只在触发时判定用户是否要求强制刷新
    state["force"] = True if s in ["-f", "--force"] else False
    # 传递附加在首次触发命令的消息中的链接
    if s not in ["", "-f", "--force"]:
        state["url"] = s

@gMatcher.got("url", prompt=("西琳将从接下来你回复的内容中找出有效链接用于统计：\n\n"
                             "* api-takumi.mihoyo.com/common/...end_id= * 在内即可"))
async def getHistoryRes(bot: Bot, event: MessageEvent, state: T_State):
    qq = event.get_user_id()
    state["url"] = str(state["url"])
    # 未缓存用户
    if "cache" not in state.keys():
        # 适应 Nonebot2 beta got 装饰器事件处理流程
        # https://github.com/nonebot/discussions/discussions/74#discussioncomment-1999189
        if "https" not in state["url"]:
            await gMatcher.reject(
                "西琳将从接下来你回复的内容中找出有效链接用于统计：\n\n"
                "* api-takumi.mihoyo.com/common/...end_id= * 在内即可"
            )
        # 常规流程获取数据
        rt = getGachaData(qq, state["url"], force=state["force"])
        # 已缓存用户
    else:
        # 不是缓存中的链接，则判定为需要强制刷新
        if state["url"] != state["cache"]["data"]["url"]:
            # 粗略判断输入是否合法，不合法继续使用缓存链接
            if "https" not in state["url"]:
                state["url"] = ""
            else:
                state["force"] = True
        # 检查缓存中的链接是否失效，发送提示信息
        else:
            expireCheck = await checkAuthkey(state["cache"]["data"]["url"])
            if expireCheck != "OK":
                warnMag = checkAuthkey()
                await gMatcher.reject(Message(warnMag))
        # 常规流程获取数据
        rt = getGachaData(qq, state["url"], state["cache"], state["force"])
    # 生成图片和消息
    if rt["msg"]:
        await gMatcher.send(Message(rt["msg"]))
    if not rt["data"].get("gachaLogs", ""):
        raise FinishedException
    try:
        stat = getStat(rt)
        pie_list = drewPie(stat)
        infoImages = getInfoImages(rt, pie_list)
        img = mergeImage(infoImages, rt)
        await gMatcher.finish(MessageSegment.image(img))
    except OSError:
        await gMatcher.finish("数据已经成功获取，但是未找到生成图片所需静态资源！")
    except FinishedException:
        pass
    except Exception as e:
        logger.error("抽卡记录图片生成出错：" + str(sys.exc_info()[0]) + "\n" + str(e))
        await bot.send_private_msg(
            message=(f"[error] [genshin_export]\n由用户 {event.get_user_id()} 触发"
                     f"\n{str(sys.exc_info()[0])}\n{str(e)}"),
            user_id=int(list(bot.config.superusers)[0]),
        )


@aMatcher.handle()
async def alterAuthkeySend(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    q = event.get_user_id()
    s = event.get_plaintext()
    c = await getCacheData(q)
    if c["msg"] == "暂无本地抽卡记录！":
        if isinstance(event, GroupMessageEvent) and s in ["", "-f", "--force"]:
            c["msg"] += "请在私聊中使用「抽卡记录」命令添加抽卡记录链接！"
            await aMatcher.finish(Message(c["msg"]))
    # 检测到缓存的用户将缓存数据传递至 got 方法进一步判断
    else:
        matcher.set_arg("ms", args)


@aMatcher.got("url", prompt=("西琳将从接下来你回复的内容中找出有效链接用于统计：\n\n"
                             "* api-takumi.mihoyo.com/common/...end_id= * 在内即可"))
async def updateAuthkey(bot: Bot, event: MessageEvent):
    q = event.get_user_id()
    url = event.get_plaintext()
    rt = alterAuthkey(q, url)
    # 生成图片和消息
    if rt["msg"]:
        await gMatcher.send(Message(rt["msg"]))
    if not rt["data"].get("gachaLogs", ""):
        raise FinishedException
    try:
        stat = getStat(rt)
        pie_list = drewPie(stat)
        infoImages = getInfoImages(rt, pie_list)
        img = mergeImage(infoImages, rt)
        await gMatcher.finish(MessageSegment.image(img))
    except OSError:
        await gMatcher.finish("数据已经成功获取，但是未找到生成图片所需静态资源！")
    except FinishedException:
        pass
    except Exception as e:
        logger.error("抽卡记录图片生成出错：" + str(sys.exc_info()[0]) + "\n" + str(e))
        await bot.send_private_msg(
            message=(f"[error] [genshin_export]\n由用户 {event.get_user_id()} 触发"
                     f"\n{str(sys.exc_info()[0])}\n{str(e)}"),
            user_id=int(list(bot.config.superusers)[0]),
        )