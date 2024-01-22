from pathlib import Path
import json
import re
import os
import requests

from time import time
from .__meta__ import getMeta

localDir = getMeta("localDir")
gachaTypeDict = getMeta("gachaTypeDict")

# 获取本地缓存抽卡记录 [fileread]
# 返回值：dict
#   msg: "" / 错误信息
#   data: 抽卡记录数据 / {"time": int}
async def getCacheData(qq: str, readCache: bool = True) -> dict:
    cache = {"msg": "", "data": {}}
    cacheFile = localDir + "/cache-config.json"
    # 本地无缓存配置文件时，创建缓存配置文件
    if not os.path.isfile(cacheFile):
        with open(cacheFile, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        cache["msg"] = "暂无本地抽卡记录！"
        cache["data"]["time"] = int(time())
        return cache
    with open(cacheFile, "r", encoding="utf-8") as f:
        cacheConfig = json.load(f)
    # 本地有缓存配置文件时，检查是否有用户缓存
    if qq not in cacheConfig.keys():
        cache["msg"] = "暂无本地抽卡记录！"
        cache["data"]["time"] = int(time())
        return cache
    # 本地有用户缓存时读取缓存的抽卡记录
    if not readCache:
        cache["msg"] = cacheConfig[qq]
        return cache
    with open(cacheConfig[qq], "r", encoding="utf-8") as f:
        cachedRawData = json.load(f)
    cache["data"] = cachedRawData
    return cache

# 缓存数据
def cachaData(qq: str, rawData):
    uid = rawData["uid"]
    # 创建 UID 对应缓存文件
    cacheFile = localDir + f"/cache-{uid}.json"
    with open(cacheFile, "w", encoding="utf-8") as f:
        json.dump(rawData, f, ensure_ascii=False, indent=2)
    # 更新用于 getCacheData 的缓存配置文件
    cgfFile = localDir + "/cache-config.json"
    with open(cgfFile, "r", encoding="utf-8") as f:
        cacheConfig = json.load(f)
    if "delete" in rawData.keys():
        cacheConfig.pop(qq)
    else:
        cacheConfig[qq] = cacheFile
    with open(cgfFile, "w", encoding="utf-8") as f:
        json.dump(cacheConfig, f, ensure_ascii=False, indent=2)
    return "成功！"

# 获取本地抽卡记录
def getCachaData(qq: str, readCache: bool = True) -> dict:
    cache = {"msg": "", "data": {}}
    cacheFile = localDir + "/cache-config.json"
    # 本地无缓存配置文件时，创建缓存配置文件
    if not os.path.isfile(cacheFile):
        with open(cacheFile, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        cache["msg"] = "暂无本地抽卡记录！"
        cache["data"]["time"] = int(time())
        return cache
    with open(cacheFile, "r", encoding="utf-8") as f:
        cacheConfig = json.load(f)
    # 本地有缓存配置文件时，检查是否有用户缓存
    if qq not in cacheConfig.keys():
        cache["msg"] = "暂无本地抽卡记录！"
        cache["data"]["time"] = int(time())
        return cache
    # 本地有用户缓存时读取缓存的抽卡记录
    if not readCache:
        cache["msg"] = cacheConfig[qq]
        return cache
    with open(cacheConfig[qq], "r", encoding="utf-8") as f:
        cachedRawData = json.load(f)
    cache["data"] = cachedRawData
    return cache

def checkAuthkey(url):
    response = requests.get(url)
    body = response.text
    body = json.loads(body)
    message = body["message"]
    if message == "authkey timeout":
        return "抽卡链接 AuthKey 已经失效，尝试返回缓存内容..."
    elif message == "OK":
        return "成功"
    else:
        return "抽卡链接错误" + message

def getRawData(authkey, force: bool = False):
    raw = {"msg": "" if not force else "强制获取最新数据..", "data": {}}
    url = "https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog?" \
          "authkey_ver=1&sign_type=2&auth_appid=webview_gacha&win_mode=fullscreen&" \
          "gacha_id=4611e733d9bac2b4402701bd189a9aa226a7&timestamp=1681910087&region=prod_gf_cn" \
          "&default_gacha_type=11&lang=zh-cn&authkey={}&game_biz=hkrpg_cn" \
          "&os_system=Windows%2010%20%20%2810.0.19044%29%2064bit&device_model=CW65S%20%28HASEE%20Computer%29" \
          "&plat_type=pc&page=1&size=5&gacha_type=11&end_id=0".format(authkey)
    authkeyStatu = checkAuthkey(url)
    if authkeyStatu != "成功":
        raw["msg"] += authkeyStatu
        return raw
    heards = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    gachaData = {
        "uid": "",
        "time": "",
        "url": "",
        "gachaLogs": {}
    }
    for gachaType in gachaTypeDict:
        end_id = 0
        result = []
        page = 1
        while True:
            url = re.sub(r'gacha_type=(.*?)&', "gacha_type={}&".format(gachaType), url)
            url = re.sub(r'size=(.*?)&', "size=20&", url)
            url = re.sub(r'end_id=(.*?)\d+', "end_id={}".format(end_id), url)
            response = requests.get(url, headers=heards)
            body = response.text
            body = json.loads(body)
            data = body["data"]['list']
            print("正在获取第{}页记录".format(page))
            result.extend(data)
            page += 1
            uid = ""
            if len(data) == 20:
                end_id = data[19]["id"]
            if 1 <= len(data) < 20:
                res = []
                for i in result:
                    rex = {}
                    rex["gacha_id"] = i["gacha_id"]
                    rex["item_id"] = i["item_id"]
                    rex["count"] = i["count"]
                    rex["time"] = i["time"]
                    rex["name"] = i["name"]
                    rex["item_type"] = i["item_type"]
                    rex["rank_type"] = i["rank_type"]
                    rex["gacha_type"] = i["gacha_type"]
                    rex["id"] = i["id"]
                    uid = i["uid"]
                    res.append(rex)
                gachaData["uid"] = uid
                gachaData["time"] = int(time())
                gachaData["url"] = url
                gachaData["gachaLogs"][gachaType] = res
                break
            if len(data) == 0:
                break
    raw["data"] = gachaData
    return raw

def mergeData(cache: dict, raw: dict, qq: str, fw: bool = True):
    # 若无新增数据，则直接返回缓存数据
    if not raw["data"].get("gachaLogs", {}):
        cache["msg"] += raw["msg"]
        return cache
    # 若无缓存数据，则直接返回新增数据
    if not cache["data"].get("gachaLogs", {}):
        raw["msg"] = cache["msg"] + raw["msg"]
        if raw["data"].get("gachaLogs", {}):
            cachaData(qq, raw["data"])
        return raw
    # 既有缓存数据又有新增数据
    locData = cache["data"]
    newData = raw["data"]
    # 检查 UID 是否为同一账号
    if locData["uid"] != newData["uid"]:
        warnMsg = "缓存与新增数据 UID 不同，合并记录中断！"
        cache["msg"] += "\n".join(raw["msg"], warnMsg)
        return cache
    # 执行合并
    msgList = []
    merged = {"msg": "", "data": {}}
    for gachaType in gachaTypeDict:
        logsLoc = locData["gachaLogs"][gachaType]
        if gachaType in newData["gachaLogs"].keys():
            logsNew = newData["gachaLogs"][gachaType]
        else:
            logsNew = locData["gachaLogs"][gachaType]
        if logsLoc != logsNew:
            tempList = []
            itemsGot = [[got["time"], got["name"]] for got in logsLoc]
            for i in range(len(logsNew)):
                item = [logsNew[i]["time"], logsNew[i]["name"]]
                if item not in itemsGot:
                    tempList.insert(0, logsNew[i])
                else:
                    pass
            for item in tempList:
                locData["gachaLogs"][gachaType].insert(0, item)
            if tempList:
                s = f"新增 {len(tempList)} 条{gachaTypeDict[gachaType]}记录.."
                msgList.append(s)
        else:
            pass
    # 处理附加信息
    locData["uid"] = newData["uid"]
    locData["time"] = newData["time"]
    locData["url"] = newData["url"]
    # 缓存合并数据并生成结果
    if fw:
        cachaData(qq, locData)
    merged["data"] = locData
    merged["msg"] = "\n".join(msgList)
    if cache["msg"] or raw["msg"]:
        merged["msg"] = cache["msg"] + raw["msg"] + "\n" + merged["msg"]
    return merged

# 获取抽卡记录
def getGachaData(qq: str, logUrl: str = "", cache: dict = {}, force: bool = False) -> dict:
    # 读取缓存
    cache = getCachaData(qq) if not cache else cache
    # 无链接且要求强制刷新，返回缓存数据
    logUrl = logUrl if logUrl else cache["data"].get("url", "")
    logUrl = re.sub("amp;", "", logUrl)
    authkey = re.findall(r"authkey=(.*?)&game", logUrl)
    # 刷新数据
    raw = getRawData(authkey[0], force=force)
    # 合并数据
    fullData = mergeData(cache, raw, qq)
    return fullData

# 更新Authkey
def alterAuthkey(qq, logUrl, cache: dict = {}, force: bool = False):
    raw = {"msg": "", "data": {}}
    cache = getCachaData(qq) if not cache else cache
    url = re.sub("amp;", "", logUrl)
    authkey = re.findall(r"authkey=(.*?)&game", url)
    url = "https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog?" \
          "authkey_ver=1&sign_type=2&auth_appid=webview_gacha&win_mode=fullscreen&" \
          "gacha_id=4611e733d9bac2b4402701bd189a9aa226a7&timestamp=1681910087&region=prod_gf_cn" \
          "&default_gacha_type=11&lang=zh-cn&authkey={}&game_biz=hkrpg_cn" \
          "&os_system=Windows%2010%20%20%2810.0.19044%29%2064bit&device_model=CW65S%20%28HASEE%20Computer%29" \
          "&plat_type=pc&page=1&size=5&gacha_type=11&end_id=0".format(authkey[0])
    ms = checkAuthkey(url)
    if ms != "成功":
        raw["msg"] += ms
        return raw
    # 刷新数据
    raw = getRawData(authkey[0], force=force)
    # 合并数据
    fullData = mergeData(cache, raw, qq)
    return fullData
