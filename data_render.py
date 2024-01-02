import re
from datetime import datetime
import math
from io import BytesIO
from base64 import b64encode

from PIL import Image, ImageDraw, ImageFont
from math import floor
from .data_source import getCachaData
from .__meta__ import getMeta

localDir = getMeta("localDir")
gachaTypeDict = getMeta("gachaTypeDict")
titleFontPath = localDir + "/lhy_font.ttf"
pieFontPath = localDir + "/LXGW-Regular.ttf"

# 转换 Image 对象图片为 Base64 编码字符串
def img2Base64(pic: Image.Image) -> str:
    buf = BytesIO()
    pic.save(buf, format="PNG", quality=100)
    base64_str = b64encode(buf.getbuffer()).decode()
    return "base64://" + base64_str

# 返回百分数字符串 / 根据百分数返回颜色
def percent(a: int, b: int, rt: str = "") -> str:
    if not rt:
        return str(round(a / b * 100, 2)) + "%"
    # 由概率生成颜色
    # https://github.com/voderl/genshin-gacha-analyzer/blob/main/src/pages/ShowPage/AnalysisChart/utils.ts
    percentColors = [
        {"pct": 0.0, "color": {"r": 46, "g": 200, "b": 5}},
        {"pct": 0.77, "color": {"r": 67, "g": 93, "b": 250}},
        {"pct": 1.0, "color": {"r": 255, "g": 0, "b": 0}},
    ]
    pct = a / b
    for level in percentColors:
        if pct < level["pct"]:
            prevKey = percentColors.index(level) - 1
            prevCl = percentColors[prevKey]["color"]
            prevPct = percentColors[prevKey]["pct"]
            upPct = (pct - prevPct) / (level["pct"] - prevPct)
            lowPct = 1 - upPct
            nowCl = level["color"]
            clR = floor(lowPct * prevCl["r"] + upPct * nowCl["r"])
            clG = floor(lowPct * prevCl["g"] + upPct * nowCl["g"])
            clB = floor(lowPct * prevCl["b"] + upPct * nowCl["b"])
            return "#{:02X}{:02X}{:02X}".format(clR, clG, clB)
    return "#FF5652"

# 设置 title 绘制字体
def tfs(size: int):
    return ImageFont.truetype(titleFontPath, size=size)

def pfs(size: int):
    return ImageFont.truetype(pieFontPath, size=size)

def getStat(result):
    data = result["data"]["gachaLogs"]
    stat = {}
    for cachaType in data:
        opticalCone3 = 0
        opticalCone4 = 0
        opticalCone5 = 0
        character4 = 0
        character5 = 0
        rex = {
            "五星角色": 0,
            "五星光锥": 0,
            "四星角色": 0,
            "四星光锥": 0,
            "三星光锥": 0
        }
        for dat in data[cachaType]:
            rank_type = dat["rank_type"]
            item_type = dat["item_type"]
            if rank_type == "3":
                opticalCone3 += 1
                rex["三星光锥"] = opticalCone3
            elif rank_type == "4" and item_type == "角色":
                character4 += 1
                rex["四星角色"] = character4
            elif rank_type == "4" and item_type == "光锥":
                opticalCone4 += 1
                rex["四星光锥"] = opticalCone4
            elif rank_type == "5" and item_type == "角色":
                character5 += 1
                rex["五星角色"] = character5
            elif rank_type == "5" and item_type == "光锥":
                opticalCone5 += 1
                rex["五星光锥"] = opticalCone5
        stat[cachaType] = rex
    return stat

def drewPie(stat):
    color = {
        "五星角色": "#fac858",
        "五星光锥": "#ee6666",
        "四星角色": "#5470c6",
        "四星光锥": "#91cc75",
        "三星光锥": "#73c0de"
    }
    pie_list = {}
    for cachaType in stat:
        img = Image.new("RGBA", (400, 420), "#ffffff")
        draw = ImageDraw.Draw(img)
        st = stat[cachaType]
        start_width = 5
        start_height = 5
        starpoint = {"x": 0, "y": 0}
        endpoint = {"x": 0, "y": 0}
        for type in color:
            width, height = tfs(15).getsize(type)
            if start_width < 400:
                draw = ImageDraw.Draw(img)
                draw.rectangle(((start_width, start_height), (start_width + 25, start_height + 15)), fill=color[type])
                draw.text(((start_width + 30), start_height), type, font=pfs(15), fill=color[type])
                start_width += width + 40
            else:
                start_width = 5
                start_height += height + 10
                draw = ImageDraw.Draw(img)
                draw.rectangle(((start_width, start_height), (start_width + 25, start_height + 15)), fill=color[type])
                draw.text(((start_width + 30), start_height), type, font=pfs(15), fill=color[type])
                start_width += width + 40
        count = 0
        start_angel = -90
        end_angel = -90
        for i in st:
            s = st[i]
            count += s
        for i in st:
            if count == 0:
                pass
            else:
                end_angel += 360 * (st[i] / count)
                draw.pieslice((40, 60, 360, 380), start=start_angel, end=end_angel, fill=color[i])
                start_angel = end_angel
        drewTypesText(img, st, starpoint, endpoint)
        pie_list[cachaType] = img
    return pie_list

def addTypeText(stat, end, count, type, image, startloc, endloc):
    angel = end + 360 * (stat[type] / count)
    x = int(120 * math.sin(math.pi * (angel / 2 + end / 2) / 180))
    y = int(120 * math.cos(math.pi * (angel / 2 + end / 2) / 180))
    pct = percent(stat[type], count)
    pctW, pctH = pfs(15).getsize(pct)
    if end <= 90:
        x = 200 + x - (pctW / 2)
        y = 200 - y - (pctH / 2)
    elif 90 < end <= 180:
        x = 200 + x - (pctW / 2)
        y = 200 + y - (pctH / 2)
    elif 180 < end <= 270:
        x = 200 - x - (pctW / 2)
        y = 200 + y - (pctH / 2)
    else:
        x = 200 - x - (pctW / 2)
        y = 200 - y - (pctH / 2)
    draw = ImageDraw.Draw(image)
    if startloc["x"] <= x:
        if  x <= endloc["x"]:
            if startloc["y"] <= y:
                if  y <= endloc["y"]:
                    y = endloc["y"] + 5
    draw.text((x, y), pct, font=pfs(15), fill="black")
    starpoint = {"x":x, "y":y}
    endpoint = {"x":x + pfs(15).getsize(pct)[0], "y":y + pfs(15).getsize(pct)[1]}
    return angel, starpoint, endpoint

# 添加各类型概率文字
def drewTypesText(image, stat, startloc, endloc):
    count = 0
    end = 0
    for i in stat:
        s = stat[i]
        count += s
    if stat["五星角色"] > 0:
        angel = addTypeText(stat, end, count, "五星角色", image, startloc, endloc)
        end = angel[0]
        startloc = angel[1]
        endloc = angel[2]
    if stat["五星光锥"] > 0:
        angel = addTypeText(stat, end, count, "五星光锥", image, startloc, endloc)
        end = angel[0]
        startloc = angel[1]
        endloc = angel[2]
    if stat["四星角色"] > 0:
        angel = addTypeText(stat, end, count, "四星角色", image, startloc, endloc)
        end = angel[0]
        startloc = angel[1]
        endloc = angel[2]
    if stat["四星光锥"] > 0:
        angel = addTypeText(stat, end, count, "四星光锥", image, startloc, endloc)
        end = angel[0]
        startloc = angel[1]
        endloc = angel[2]
    if stat["三星光锥"] > 0:
        addTypeText(stat, end, count, "三星光锥", image, startloc, endloc)
    return image, startloc, endloc

# 根据抽卡次数返回不同颜色五星记录
def colorfulFive(name: str, gachaType, type5weight, type5height, img):
    name_list = name.split(" ")
    draw = ImageDraw.Draw(img)
    couns = []
    for item in name_list:
        if item != "":
            coun = re.findall(r"\d+", item)
            coun = int(coun[0])
            couns.append(coun)
        char = list(item)
        color = percent(int(coun), 80 if gachaType == "12" else 90, "color")
        for cha in char:
            if type5weight + pfs(25).getsize(cha)[0] <= 425:
                draw.text((type5weight, type5height), cha, font=pfs(25), fill=color)
                type5weight += pfs(25).getsize(cha)[0]
            else:
                type5weight = 25
                type5height += pfs(25).getsize(cha)[1] + 5
                draw.text((type5weight, type5height), cha, font=pfs(25), fill=color)
                type5weight += pfs(25).getsize(cha)[0]
        draw.text((type5weight, type5height), " ", font=pfs(25), fill=color)
        type5weight += pfs(25).getsize(" ")[0]
    type5height += pfs(25).getsize(" ")[1] + 20
    return type5height

# 绘制单个卡池图片
def drawTypeInfo(pie_image, oneTypeData):
    img = Image.new("RGB", (450, 1500), "#f9f9f9")
    draw = ImageDraw.Draw(img)
    if len(oneTypeData) == 0:
        msg = "~ 这里什么都没有呢 ~"
        wmsg, hmsg = tfs(30).getsize(msg)
        draw.text((225 - wmsg / 2, 300), msg, font=tfs(30), fill="#66CCFF")
        height = 300 + hmsg
        return img, height
    gachaType = oneTypeData[0]["gacha_type"]
    typeName = gachaTypeDict[gachaType]
    titleW, titleH = tfs(25).getsize(typeName)
    draw.rectangle((0, 0, 450, 60), fill="#F0F0F0")
    draw.rectangle((0, 60, 450, 510), fill="#ffffff")
    draw.text((225 - (titleW / 2), 30 - (titleH / 2)), typeName, font=tfs(25), fill="black")
    img.paste(pie_image, (25, 80))  # 将饼图粘贴到当前图片
    pieW, pieH = pie_image.size
    height = 80 + pieH - 15
    firstTime = oneTypeData[len(oneTypeData) - 1]["time"]
    firstTime = datetime.strptime(firstTime, "%Y-%m-%d %H:%M:%S").date()
    lastTime = oneTypeData[0]["time"]
    lastTime = datetime.strptime(lastTime, "%Y-%m-%d %H:%M:%S").date()
    time = str(firstTime) + " ~ " + str(lastTime)
    timeW, timeH = pfs(15).getsize(time)
    draw.text((225 - (timeW / 2), height), time, font=pfs(15), fill="#666666")
    height += 40
    rank_type5 = 0
    rank_type4 = 0
    rank_type3 = 0
    count = 1
    nostar5 = 1
    type5log = "五星历史记录: "
    type5 = ""
    draw.text((25, 650), type5log, font=pfs(25), fill="black")
    type5weight = 25 + pfs(25).getsize(type5log)[0]
    for i in range(len(oneTypeData) - 1, -1, -1):
        rank_type = oneTypeData[i]["rank_type"]
        if rank_type == "5":
            rank_type5 += 1
            name = oneTypeData[i]["name"]
            coun = count
            type5 += name + "[" + str(coun) + "] "
            count = 0
            nostar5 = 0
        if rank_type == "4":
            rank_type4 += 1
            nostar5 += 1
        if rank_type == "3":
            rank_type3 += 1
            nostar5 += 1
        count += 1
    statstr1 = "共计 "
    statstr2 = str(len(oneTypeData))
    statstr3 = " 抽"
    statstr4 = ", 已累计 "
    statstr5 = str(nostar5)
    statstr6 = " 抽未出5星"
    draw.text((25, height), statstr1, font=pfs(25), fill="black")
    startW = 25 + pfs(25).getsize(statstr1)[0]
    draw.text((startW, height), statstr2, font=pfs(25), fill="rgb(24,144,255)")
    startW += pfs(25).getsize(statstr2)[0]
    draw.text((startW, height), statstr3, font=pfs(25), fill="black")
    startW += pfs(25).getsize(statstr3)[0]
    draw.text((startW, height), statstr4, font=pfs(25), fill="black")
    startW += pfs(25).getsize(statstr4)[0]
    nostart5color = percent(4, 80 if gachaType == "12" else 90, "color")
    draw.text((startW, height), statstr5, font=pfs(25), fill=nostart5color)
    startW += pfs(25).getsize(statstr5)[0]
    draw.text((startW, height), statstr6, font=pfs(25), fill="black")
    height += pfs(25).getsize(statstr6)[1] + 15
    stat5 = "五星: {}次".format(rank_type5)
    pct5 = "[" + percent(rank_type5, len(oneTypeData)) + "]"
    stat4 = "四星: {}次".format(rank_type4)
    pct4 = "[" + percent(rank_type4, len(oneTypeData)) + "]"
    stat3 = "三星: {}次".format(rank_type3)
    pct3 = "[" + percent(rank_type3, len(oneTypeData)) + "]"
    draw.text((25, height), stat5, font=pfs(20), fill="#C0713D")
    draw.text((400 - pfs(20).getsize(pct5)[0], height), pct5, font=pfs(20), fill="#C0713D")
    height += pfs(25).getsize(statstr6)[1] + 5
    draw.text((25, height), stat4, font=pfs(20), fill="#A65FE2")
    draw.text((400 - pfs(20).getsize(pct4)[0], height), pct4, font=pfs(20), fill="#A65FE2")
    height += pfs(25).getsize(statstr6)[1] + 5
    draw.text((25, height), stat3, font=pfs(20), fill="#4D8DF7")
    draw.text((400 - pfs(20).getsize(pct3)[0], height), pct3, font=pfs(20), fill="#4D8DF7")
    height += pfs(25).getsize(statstr6)[1] + 5
    info = colorfulFive(type5, gachaType, type5weight, 650, img)
    star5Avg = round((len(oneTypeData) - nostar5) / rank_type5, 2)
    lastStr = "平均5星抽数： "
    draw.text((25, info), lastStr, font=pfs(25), fill="black")
    weight = 25 + pfs(25).getsize(lastStr)[0] + 5
    draw.text((weight, info), f"{star5Avg:.2f}", font=pfs(25), fill=percent(round(star5Avg), 80 if gachaType == "12" else 90, "color"))
    height = info + pfs(25).getsize(lastStr)[1] + 5
    return img, height

# 图片合并
def mergeImage(images: dict, data):
    uid = data["data"]["uid"]
    height = 0
    for i in images:
        h = images[i][1]
        if h > height:
            height = h
    fW, fH = pfs(15).getsize(uid)
    height += fH + 20
    img = Image.new("RGB", (450 * len(images), height), "#f9f9f9")
    dit = 0
    for i in images:
        weight = dit * 450
        img.paste(images[i][0], (weight, 0))
        dit += 1
    uid = uid.replace(uid[3:6], "***", 1)
    ImageDraw.Draw(img).text(((dit * 450) - fW - 25, height - fH - 20), uid, font=pfs(15), fill="#666666")
    # img.show()
    resImgB64 = img2Base64(img)
    return resImgB64

# 获取所有卡池的图片，以集合方式返回
def getInfoImages(res, pie_list):
    infoimg = {}
    for gachaTYpe in gachaTypeDict:
        data = res["data"]["gachaLogs"][gachaTYpe]
        image = pie_list[gachaTYpe]
        info = drawTypeInfo(image, data)
        infoimg[gachaTYpe] = info
    return infoimg
