import os

localDir = os.path.join(os.path.dirname(__file__), "gachalogs")

def getMeta(need: str):
    gachaTypeDict = {
        "11": "角色活动跃迁",
        "12": "光锥活动跃迁",
        "1": "常驻跃迁",
        "2": "新手跃迁",
    }
    gachaMeta = {
        "gachaTypeDict": gachaTypeDict,
        "localDir": localDir.replace('\\', '/'),
    }
    return gachaMeta[need]