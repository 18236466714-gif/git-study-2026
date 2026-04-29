import pygame
import random
import math
from enum import Enum
import os
import json
import subprocess
import sys
from typing import Optional
import datetime

# -----------------------------
# Constants (常量定义)
# -----------------------------
WIDTH, HEIGHT = 1000, 750
FPS = 60
GRAVITY = 0.8
INITIAL_SPEED = 7
GROUND_HEIGHT = 60
DINO_WIDTH, DINO_HEIGHT = 80, 80
OBSTACLE_WIDTH = 135
OBSTACLE_HEIGHTS = {
    "small_cactus": 120,
    "tall_cactus": 120,
    "rock": 120,
    # Cultural-mechanic obstacle (文化机关障碍)
    "wood_frame": 110,  # 木结构：可用“木构件”拆解通过
}

# Flying Obstacle Properties (飞行障碍物属性)
FLYING_OBSTACLE_PROPERTIES = {
    "balloon": {
        "width": 25, "height": 40,
        "colors": [(255, 100, 100), (255, 150, 150)],
        "min_speed": -3, "max_speed": -1.5,
        "x_range": [WIDTH // 4, WIDTH * 3 // 4]
    },
    "daodan": {
        "width": 60, "height": 30,
        "colors": [(255, 0, 0), (255, 100, 0)],
        "min_speed": 8, "max_speed": 12,
        "y_range": [50, HEIGHT - GROUND_HEIGHT - 50]
    }
}

# Colors (颜色定义)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 69, 0)  # Orange-Red (更鲜艳的橙红色)
YELLOW = (255, 215, 0)
GREEN = (34, 139, 34)  # Forest Green (森林绿)
BRIGHT_GREEN = (50, 205, 50)  # Lime Green (酸橙绿)
BLUE = (65, 105, 225)  # Royal Blue (皇家蓝)
BRIGHT_BLUE = (100, 149, 237)  # Cornflower Blue (矢车菊蓝)
PURPLE = (128, 0, 128)
ORANGE = (255, 140, 0)  # Dark Orange (深橙色)
GRAY = (169, 169, 169)
SKY_BLUE = (135, 206, 255)
LIGHT_CLOUD = (245, 245, 245)  # Light Gray (浅灰色云朵)
SHADOW = (0, 0, 0, 50)  # Transparent Shadow (透明阴影)

# 全界面统一 UI 主题（浅底、靛青线框、可读灰字）
UI_MODAL_RGBA = (14, 22, 38, 200)
UI_PANEL_BG = (242, 248, 252)        # 不用纯白：淡青宣纸感
UI_PANEL_BORDER = (70, 102, 138)     # 边框略带青蓝
UI_TEXT_PRIMARY = (22, 32, 48)       # 更沉稳
UI_TEXT_SECONDARY = (74, 88, 112)    # 次级文字更柔和
UI_TITLE_LIGHT = (242, 246, 252)
UI_ACCENT_WARM = (188, 152, 88)
UI_DIVIDER = (188, 204, 224)

# 分界面淡彩主题（渐变：加深对比，避免“看起来像白色”）
UI_TUTORIAL_BG_TOP = (150, 200, 185)
UI_TUTORIAL_BG_BOTTOM = (210, 236, 226)
UI_TUTORIAL_CARD_TOP = (150, 205, 235)
UI_TUTORIAL_CARD_BOTTOM = (214, 238, 252)
UI_TUTORIAL_TIPS_TOP = (162, 214, 190)
UI_TUTORIAL_TIPS_BOTTOM = (216, 242, 228)

# 设置界面：偏青蓝（去掉“发黄”）
UI_SETTINGS_BG_TOP = (110, 168, 188)
UI_SETTINGS_BG_BOTTOM = (206, 238, 246)

UI_LOADOUT_BG_TOP = (128, 168, 214)
UI_LOADOUT_BG_BOTTOM = (206, 232, 250)

# 图鉴列表：更彩的蓝绿卡片（避免看成白色）
UI_CODEX_CARD_UNLOCKED = (196, 232, 252)
UI_CODEX_CARD_LOCKED = (162, 176, 198)
UI_CODEX_STRIP_UNLOCKED = (170, 214, 242, 150)

UI_CARD_NEUTRAL_TOP = (170, 198, 226)
UI_CARD_NEUTRAL_BOTTOM = (222, 240, 252)

UI_WARM_CARD_TOP = (196, 172, 126)
UI_WARM_CARD_BOTTOM = (236, 222, 196)

# Unified feedback colors (统一成功/失败配色)
UI_SUCCESS = (34, 148, 94)
UI_SUCCESS_SOFT = (208, 244, 226)
UI_DANGER = (208, 70, 70)
UI_DANGER_SOFT = (252, 228, 228)

# Game States (游戏状态)
class GameState(Enum):
    MODE_SELECT = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4
    CODEX = 5  # 建筑图鉴
    SETTINGS = 6  # 主页设置面板
    DECRYPT = 7  # 解密模式：古建筑题目问答
    LOADOUT = 8  # 技能装备：解密解锁后局内选择是否携带
    SHOP = 9     # 技能商店：用碎片购买永久技能

# Item Types (道具类型)
class ItemType(Enum):
    HEALTH = 1  # Health Pack (血包)
    SHIELD = 2  # Shield (护盾)

# Cultural Collectible Types (文化收集物类型)
class CollectibleType(Enum):
    WADANG = 1      # 瓦当
    DOUGONG = 2     # 斗拱组件
    WOOD = 3        # 木构件

# Resources (资源路径)
MODE_SELECT_MUSIC = "01.flac"
# In-game music pool: all modes randomly pick from these 4 tracks.
GAME_MUSIC_POOL = ["00.flac", "01.flac", "02.flac", "3.flac"]
# Home/menu music candidates (主页音乐候选：文件名 + 古风曲名)
HOME_MUSIC_META = [
    ("00.flac", "檐雨听风"),
    ("01.flac", "月下归舟"),
    ("02.flac", "松烟入墨"),
    ("3.flac", "山河旧梦"),
    ("back.flac", "归云深处"),
    ("pan.flac", "玉盘风清"),
    ("swim.flac", "烟波行歌"),
]
# 主页首次进入 / menu_music_index = -1 时优先播放的曲目（须在 HOME_MUSIC_META 且文件存在）
DEFAULT_HOME_MUSIC_BASENAME = "back.flac"
# Always store config next to this script to avoid "different cwd => different save file"
# (e.g. launching from IDE vs double-clicking exe/py creates separate configs)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_config.json")
CONFIG_BAK_FILE = CONFIG_FILE + ".bak"
LEVEL_UP_SCORES = [100, 300, 600, 1000]
INITIAL_SKILL_SHARDS = 10

# -----------------------------
# Skill System (技能系统：永久解锁 + 局内可选装备)
# -----------------------------
# unlock_skills: {skill_id: level}
# loadout: {"enabled": bool, "slots": [skill_id, ...]}  # 允许空槽
SKILLS = {
    "slowmo": {
        "name": "慢动作",
        "desc": "短时降低游戏速度，躲避更从容。",
        "max_level": 3,
    },
    "dash": {
        "name": "冲刺",
        "desc": "短时提升速度并免疫一次碰撞（更偏进攻节奏）。",
        "max_level": 3,
    },
    "magnet": {
        "name": "磁吸",
        "desc": "自动吸附附近文化构件（瓦当/斗拱/木构件）。",
        "max_level": 3,
    },
    "double_jump_plus": {
        "name": "加跳",
        "desc": "永久提高可用跳跃段数上限（与设置跳跃段数叠加取较大）。",
        "max_level": 2,
    },
    "identify": {
        "name": "鉴别",
        "desc": "在四合院主题下更容易通过“榫卯(虚/实)”机关（提示更明显）。",
        "max_level": 2,
    },
}

# Cultural systems (文化系统数据)
CODEX_ENTRIES = [
    {
        "id": "wadang",
        "name": "瓦当",
        "dynasty": "汉—明清皆常见",
        "pages": [
            "【是什么】\n"
            "瓦当（又称瓦头）是中国古建筑檐口筒瓦前端的遮挡构件，多为半圆/圆形陶件，"
            "位于屋檐最外缘，是你抬头最容易看到的一圈“屋面边缘装饰”。\n\n"
            "【它和“滴水”有什么区别】\n"
            "瓦当属于筒瓦端部；“滴水”多指板瓦前端的下垂部件（让雨水离开墙身滴落），"
            "两者经常同时出现，但位置和构件属性不同。",
            "【结构与功能】\n"
            "1) 保护：遮挡椽头/檩端等木构端面，减缓雨水侵蚀。\n"
            "2) 排水：引导檐口雨水有序离开屋面边缘，减少回流。\n"
            "3) 识别：瓦当纹样常带有时代特征与地域风格，是“看屋识代”的线索之一。\n"
            "4) 美学：檐口线条因此更完整，形成屋面轮廓的节奏感。",
            "【材料与等级】\n"
            "常见材质以灰陶为主；唐以后出现并普及琉璃瓦当（多见于皇家/高等级建筑或重要寺观），"
            "宋元明清偶见金属瓦当或特殊工艺。\n\n"
            "【你在游戏里的意义】\n"
            "收集瓦当可解锁图鉴并积累“建筑部件成就”。后续也可用于解锁更高级的屋面主题外观/关卡机制。",
        ],
        "unlock": {"type": "collect", "collectible": CollectibleType.WADANG, "count": 1},
        "game_rule": "收集用于解锁图鉴条目。",
    },
    {
        "id": "dougong",
        "name": "斗拱",
        "dynasty": "唐宋至明清体系化发展",
        "pages": [
            "【是什么】\n"
            "斗拱是柱与屋顶之间的过渡承重构件，由斗、拱、昂、枋等核心部件"
            "通过榫卯咬合叠加而成，整体像一组层层出挑的“木骨架”。\n\n"
            "它位于柱头/额枋之上，把屋檐的重量与外挑力量稳稳传回到柱与基础。",
            "【结构逻辑（看懂斗拱）】\n"
            "斗：像“方块承台”，用于承接并分配压力；\n"
            "拱：像“弯臂托架”，逐级出挑形成檐口外伸；\n"
            "昂：向外上方挑出的构件，增强出挑与稳定；\n"
            "枋：横向连接构件，形成整体框架。\n\n"
            "层层叠加的出挑，让飞檐的“轻盈”建立在力学的“可靠”之上。",
            "【功能】\n"
            "1) 承重传力：把屋面荷载传递到柱；\n"
            "2) 出挑形成飞檐：檐口越外挑，斗拱越关键；\n"
            "3) 抗震缓冲：榫卯与多节点连接提供一定耗能与位移容许；\n"
            "4) 等级与美学：斗拱形制、尺度与密度常体现建筑等级与审美风格。",
            "【你在游戏里的意义】\n"
            "收集斗拱组件用于解锁图鉴条目。\n\n"
            "后续可拓展为玩法规则：例如“斗拱点位=可借力的跳跃支点/二次弹跳点”，"
            "让玩家在关卡里真正‘踩着斗拱走’。",
        ],
        "unlock": {"type": "collect", "collectible": CollectibleType.DOUGONG, "count": 1},
        "game_rule": "收集用于解锁图鉴条目。",
    },
    {
        "id": "wood",
        "name": "木构件",
        "dynasty": "传统木构建筑通用",
        "pages": [
            "【木构系统（极简版）】\n"
            "柱：竖木，支撑房子；\n"
            "枋/额：横木，连接柱子，形成框架；\n"
            "梁：大梁，架在柱上托屋顶；\n"
            "檩：梁上长木，承托椽子；\n"
            "椽：密排小木条，铺瓦；\n"
            "斗拱：柱与屋顶之间，挑檐、承重、缓冲。\n\n"
            "你可以把它理解成：从“柱—梁—檩—椽—瓦”，逐层把重量传下去。",
            "【为什么木构厉害】\n"
            "1) 榫卯：不用钉子也能牢固连接；\n"
            "2) 可拆装：构件化思维强，便于维修替换；\n"
            "3) 韧性与耗能：多节点连接在一定程度上能缓冲震动；\n"
            "4) 空间美学：结构即空间，空间即秩序。",
            "【你在游戏里的玩法功能】\n"
            "木构件不是单纯的“金币替代品”，它直接参与规则：\n"
            "- 消耗 1 个木构件可拆解“木架机关”，安全通过并获得加分。\n\n"
            "后续也可扩展：木构件用于“修复断桥/搭建平台/榫卯重组”等机制。",
        ],
        "unlock": {"type": "collect", "collectible": CollectibleType.WOOD, "count": 1},
        "game_rule": "玩法功能：消耗 1 个木构件可拆解“木架机关”，安全通过并获得加分。",
    },
]

# -----------------------------
# Decrypt Mode (解密模式题库)
# -----------------------------
# 题目支持主题：siheyuan / yamen / palace / bridge / general
DECRYPT_QUESTIONS = [
    {
        "id": "dq_dougong_core",
        "theme": "palace",
        "q": "斗拱最核心的结构作用是？",
        "options": [
            "把屋面荷载与出挑力传回到柱与基础，同时形成飞檐",
            "主要用于防火隔热，减少木构件受热",
            "只是一种装饰构件，不参与受力",
            "专门用来把雨水引离墙身",
        ],
        "answer": 0,
        "explain": "斗拱位于柱头与屋面之间，既承重传力，又通过层层出挑形成飞檐与檐口外伸。",
    },
    {
        "id": "dq_wadang_where",
        "theme": "general",
        "q": "瓦当通常位于古建筑屋面的哪个位置？",
        "options": [
            "屋脊正中（脊刹位置）",
            "门扇中央（门钉周围）",
            "檐口筒瓦前端（屋檐最外缘）",
            "台基四角（角柱脚下）",
        ],
        "answer": 2,
        "explain": "瓦当是筒瓦前端的遮挡构件，位于檐口最外缘，是抬头最容易看到的一圈檐口装饰与保护件。",
    },
    {
        "id": "dq_levels_chain",
        "theme": "general",
        "q": "下面哪一组最符合“柱—梁—檩—椽—瓦”的层级关系？",
        "options": [
            "从上到下逐层悬挂，把柱子挂在屋顶上",
            "从下到上逐层承托，把屋面重量传回柱与基础",
            "各构件相互独立，不需要连接",
            "只在石构建筑中使用，不适用于木构",
        ],
        "answer": 1,
        "explain": "传统木构的受力传递是自屋面向下：瓦→椽→檩→梁→柱→基础（题干写法为自下而上列举）。",
    },
    {
        "id": "dq_sunmao_feature",
        "theme": "siheyuan",
        "q": "“榫卯”的最大特点更接近下面哪一句？",
        "options": [
            "用凹凸咬合的构造实现连接，便于拆装与维修",
            "必须依赖金属钉与铆才能牢固",
            "只能用于屋面瓦件之间的连接",
            "连接越死越好，完全不允许位移",
        ],
        "answer": 0,
        "explain": "榫卯通过构件之间的几何咬合连接，传统上可减少金属连接件依赖，并利于维护替换。",
    },
    {
        "id": "dq_taiji_role",
        "theme": "yamen",
        "q": "“台基”在古建筑里更常见的作用是？",
        "options": [
            "专门用来储水，防火时供水",
            "抬高建筑、防潮排水，并体现等级与庄重感",
            "只为了让屋顶更轻，减少荷载",
            "用于把斗拱固定在地面上",
        ],
        "answer": 1,
        "explain": "台基可抬高建筑、减少地面潮气影响并利于排水，同时也常带有礼制与等级表达。",
    },
    {
        "id": "dq_clue_recognize",
        "theme": "general",
        "q": "下面哪一种最可能用于“看屋识代/识别等级”的线索？",
        "options": [
            "瓦当纹样、斗拱形制与尺度密度",
            "室内电灯数量",
            "玻璃幕墙反光强度",
            "空调外机位置",
        ],
        "answer": 0,
        "explain": "瓦当纹样与斗拱形制常随时代、地域与等级变化，是传统建筑辨识的重要线索。",
    },
    {
        "id": "dq_bridge_load",
        "theme": "bridge",
        "q": "传统桥梁结构里，“拱”或“梁”的关键关注点更接近？",
        "options": [
            "颜色是否越鲜艳越好",
            "只要栏杆漂亮就行",
            "承重与传力路径是否连续可靠",
            "主要决定于室内采光",
        ],
        "answer": 2,
        "explain": "桥梁首先是承重结构，核心在于受力与传力路径的连续性与可靠性，其次才是装饰与细部。",
    },
    {
        "id": "dq_palace_eave",
        "theme": "palace",
        "q": "“飞檐”看起来很轻盈，但它的实现更依赖于？",
        "options": [
            "出挑构件体系（如斗拱/挑梁）把力稳稳传回柱网",
            "把屋面瓦做得越薄越好",
            "把檐口完全做成悬空不连接",
            "只靠彩绘就能实现飞檐",
        ],
        "answer": 0,
        "explain": "飞檐的外挑离不开结构体系支撑，出挑构件把外挑产生的力传回柱网与基础。",
    },
    {
        "id": "dq_yamen_order",
        "theme": "yamen",
        "q": "官署建筑常强调的空间体验更接近？",
        "options": [
            "轴线与秩序感（门—院—堂）逐层递进",
            "越曲折越好，越迷路越高级",
            "完全没有主次空间，随意排列",
            "只需要堆叠高塔体现气势",
        ],
        "answer": 0,
        "explain": "官署类建筑常以轴线组织空间，强调秩序与等级，形成“由外到内、由低到高”的递进感。",
    },
    {
        "id": "dq_siheyuan_layout",
        "theme": "siheyuan",
        "q": "四合院最典型的平面格局特征是？",
        "options": [
            "以单体塔楼为核心向外辐射",
            "四面房屋围合成院落，形成内向型空间",
            "沿河线性展开，院落不重要",
            "只有屋顶没有院子",
        ],
        "answer": 1,
        "explain": "四合院以围合院落为核心，空间内向、礼序清晰，院子是日常活动与采光通风的重要场所。",
    },
    # --- 追加题库（扩充解密模式题目数量）---
    {
        "id": "dq_dougong_levels",
        "theme": "palace",
        "q": "斗拱“层层出挑”的直接结果更接近下面哪一项？",
        "options": [
            "檐口外伸更大，同时把外挑力更平稳地传回柱网",
            "让屋脊变短，使屋面更平",
            "让台基更高，从而防潮",
            "让门扇更厚，以增强防御",
        ],
        "answer": 0,
        "explain": "斗拱的出挑让檐口更外伸，并把外挑产生的力通过多级构件回传到柱与基础。",
    },
    {
        "id": "dq_dian_order",
        "theme": "palace",
        "q": "传统木构的受力传递，下面哪条更合理？",
        "options": [
            "柱→梁→檩→椽→瓦",
            "瓦→椽→檩→梁→柱→基础",
            "瓦→柱→梁→基础→椽",
            "檩→瓦→梁→柱→椽",
        ],
        "answer": 1,
        "explain": "屋面荷载先落到瓦与椽，再到檩、梁，最终由柱传到基础。",
    },
    {
        "id": "dq_roof_ridge",
        "theme": "general",
        "q": "“屋脊”更接近下面哪种说法？",
        "options": [
            "台基四周的排水沟",
            "斗拱下方的额枋",
            "屋顶两坡交汇形成的最高线（或转折线）",
            "门洞上方的门楣",
        ],
        "answer": 2,
        "explain": "屋脊通常指屋面坡面交汇处形成的线（正脊、垂脊等），是屋顶形态的重要特征。",
    },
    {
        "id": "dq_wadang_vs_dishui",
        "theme": "general",
        "q": "瓦当与“滴水”的常见区别是？",
        "options": [
            "瓦当多在筒瓦端部；滴水多在板瓦前端用于引水滴落",
            "瓦当只用于室内；滴水只用于室外",
            "瓦当用于地面铺装；滴水用于屋脊装饰",
            "瓦当是木构；滴水是石构",
        ],
        "answer": 0,
        "explain": "二者常同时出现但位置属性不同：瓦当是筒瓦端部遮挡/装饰件，滴水更多用于板瓦前端导水。",
    },
    {
        "id": "dq_siheyuan_axis",
        "theme": "siheyuan",
        "q": "四合院里“正房”常见的位置更可能是？",
        "options": [
            "中轴线北侧，坐北朝南（采光与尊位）",
            "最靠南的一排，面向北",
            "院落中央的圆亭",
            "院外街道一侧的角落",
        ],
        "answer": 0,
        "explain": "北方四合院常以坐北朝南的正房为尊，兼顾采光与礼序。",
    },
    {
        "id": "dq_siheyuan_yard",
        "theme": "siheyuan",
        "q": "四合院“院子”的功能更贴近下面哪项？",
        "options": [
            "采光通风、组织动线与家庭活动的共享空间",
            "专门用于防火的蓄水池",
            "只为装饰，不允许活动",
            "用于承托斗拱的结构层",
        ],
        "answer": 0,
        "explain": "院落是采光通风与活动空间，也是四合院组织居住与动线的重要核心。",
    },
    {
        "id": "dq_bridge_span",
        "theme": "bridge",
        "q": "“跨径”这个词在桥梁里更常指？",
        "options": [
            "桥面到水面的高度",
            "桥栏杆的高度",
            "相邻支点之间的水平距离（一个跨度）",
            "桥面铺装的厚度",
        ],
        "answer": 2,
        "explain": "跨径通常指桥梁一个跨度内相邻支点（桥墩/桥台）之间的距离。",
    },
    {
        "id": "dq_mortise_fix",
        "theme": "siheyuan",
        "q": "榫卯连接的一个常见优点是？",
        "options": [
            "构件化、可拆装，维修时可替换局部构件",
            "必须永久焊死，不能拆",
            "完全依赖胶水连接",
            "只能用在石构建筑",
        ],
        "answer": 0,
        "explain": "榫卯连接强调构件几何咬合，便于拆装与维护更换，体现传统木构的构件化思维。",
    },
    {
        "id": "dq_taiji_drain",
        "theme": "general",
        "q": "台基“防潮排水”的直观原因更可能是？",
        "options": [
            "降低建筑高度，让雨水更快进屋",
            "抬高室内地坪，减少地面潮气影响并利于雨水远离墙根",
            "把屋顶改成平顶，取消排水",
            "把所有木构换成金属就不用防潮",
        ],
        "answer": 1,
        "explain": "台基抬高建筑，雨水不易回溅墙根，潮气也更难影响室内地坪。",
    },
    # --- 题库扩充（二）---
    {
        "id": "dq_liang_zhu",
        "theme": "general",
        "q": "传统木构里，“梁”与“柱”最常见的结构关系是？",
        "options": [
            "梁主要横架在柱上，把上部荷载传到柱",
            "柱悬在梁下面，只靠装饰拉住",
            "梁与柱完全不接触",
            "梁只铺在地上，柱子装饰用",
        ],
        "answer": 0,
        "explain": "梁横向架于柱上，与柱、枋等共同形成竖向承重框架。",
    },
    {
        "id": "dq_litian",
        "theme": "palace",
        "q": "“琉璃瓦”在古建筑中多见于？",
        "options": [
            "皇家、高等级寺观或重要建筑屋面",
            "普通农舍茅顶",
            "只用于铺地",
            "只用于桥梁支座",
        ],
        "answer": 0,
        "explain": "琉璃瓦工艺复杂、成本高，历史上多见于高等级建筑的屋面。",
    },
    {
        "id": "dq_yingshan",
        "theme": "siheyuan",
        "q": "四合院中，“影壁”常见作用是？",
        "options": [
            "遮挡视线、挡风并强调入口礼序",
            "代替正房居住",
            "专门养鱼的池子",
            "屋顶排水的主渠道",
        ],
        "answer": 0,
        "explain": "影壁起遮挡视线、缓冲风势与组织入口空间的作用，兼有礼制寓意。",
    },
    {
        "id": "dq_angsang",
        "theme": "bridge",
        "q": "古代木拱廊桥一类结构，“剪刀撑/斜撑”往往用于？",
        "options": [
            "让桥身更轻，取消桥墩",
            "提高桁架或拱架面外稳定与整体刚度",
            "只做桥面装饰",
            "固定栏杆花纹",
        ],
        "answer": 1,
        "explain": "斜撑可提高木构桥架的整体稳定性，减少扭转与侧向变形。",
    },
    {
        "id": "dq_eave_drip",
        "theme": "general",
        "q": "檐口设置瓦件与滴水，主要功能之一是？",
        "options": [
            "让雨水离开墙身，减少墙面淋湿与侵蚀",
            "让雨水尽量打进室内",
            "增加建筑高度",
            "取消屋顶荷载",
        ],
        "answer": 0,
        "explain": "檐口构件组织排水路径，使滴落点离开墙身，保护墙体与木构。",
    },
    {
        "id": "dq_yamen_gate",
        "theme": "yamen",
        "q": "传统官署大门常强调“威仪”，下面哪项更贴切？",
        "options": [
            "门屋高大、仪门与照壁形成序列，轴线分明",
            "不设门，完全开放",
            "大门朝北且越矮越好",
            "取消院落，只留一条路",
        ],
        "answer": 0,
        "explain": "官署重视门第与轴线秩序，大门、仪门与院落序列体现权威与礼制。",
    },
    {
        "id": "dq_bracket_set",
        "theme": "palace",
        "q": "同一开间内斗拱“铺作”增多，往往意味着？",
        "options": [
            "屋面更轻，可以不要梁",
            "檐口或屋面荷载的分担节点更密，形制可能更繁、等级可能更高",
            "斗拱只变短不变多",
            "只影响油漆颜色",
        ],
        "answer": 1,
        "explain": "铺作增多通常对应更密的出挑与受力节点，常与形制、等级相关。",
    },
    {
        "id": "dq_siheyuan_chaofang",
        "theme": "siheyuan",
        "q": "四合院“厢房”一般位于？",
        "options": [
            "院落东西两侧，与正房、倒座围合院落",
            "院子正中央独立塔楼",
            "院外胡同里",
            "只做地下库房",
        ],
        "answer": 0,
        "explain": "厢房多位于院落东西两侧，与正房、倒座共同围合内向院落。",
    },
    {
        "id": "dq_stone_arch",
        "theme": "bridge",
        "q": "石拱桥桥拱的“推力”通常由谁承受？",
        "options": [
            "只靠桥面行人重量抵消",
            "桥墩、桥台与基础体系共同约束与传递",
            "完全由河水承担",
            "只由栏杆承担",
        ],
        "answer": 1,
        "explain": "拱的推力需由墩台与基础可靠承受并传到地基。",
    },
    {
        "id": "dq_caisson_ceiling",
        "theme": "palace",
        "q": "宫殿建筑室内“藻井”更常见的功能是？",
        "options": [
            "标示室内上方重要部位，兼有装饰与象征意义",
            "储存粮食",
            "通地下烟道",
            "代替柱子承重整座殿",
        ],
        "answer": 0,
        "explain": "藻井是传统天花的重要装饰与象征部位，常处理室内视觉焦点。",
    },
    {
        "id": "dq_dougong_material",
        "theme": "general",
        "q": "斗拱在传统建筑中主要为？",
        "options": [
            "木构架节点处的组合构件",
            "屋顶铺瓦的单一瓦片",
            "台基石雕的一种",
            "门钉排列方式",
        ],
        "answer": 0,
        "explain": "斗拱由斗、拱、昂等木构件组合，是柱头与屋面之间的关键过渡与承托节点。",
    },
    {
        "id": "dq_yard_microclimate",
        "theme": "siheyuan",
        "q": "合院“内向院落”对微气候的普遍帮助是？",
        "options": [
            "完全隔绝阳光",
            "利于采光通风，同时减少街巷噪声干扰",
            "让院子终年不见风",
            "只能冬季使用",
        ],
        "answer": 1,
        "explain": "围合院落可组织采光与通风，相对街道更安静、私密。",
    },
    {
        "id": "dq_palace_axis",
        "theme": "palace",
        "q": "宫殿建筑群常采用多重院落的意义更接近？",
        "options": [
            "层层递进、礼制与空间等级逐级升高",
            "让人快速走出宫城",
            "取消中轴线",
            "只保留一个院子",
        ],
        "answer": 0,
        "explain": "多重院落与中轴共同强化礼制序列，形成由外到内的等级体验。",
    },
    {
        "id": "dq_bridge_abutment",
        "theme": "bridge",
        "q": "桥台（岸边的“大头”）主要作用是？",
        "options": [
            "连接路基与桥跨，承受台后土压力与上部荷载",
            "只挂灯笼",
            "养鱼",
            "代替桥面通行",
        ],
        "answer": 0,
        "explain": "桥台衔接道路与桥梁，并承受后台填土与上部结构的力。",
    },
    {
        "id": "dq_fang_e_f",
        "theme": "yamen",
        "q": "“额枋/阑额”一类横向构件，更常被理解为？",
        "options": [
            "屋面最外层瓦片",
            "柱头间横向联系构件，承托上部并稳定柱架",
            "台基排水沟盖板",
            "栏杆望柱",
        ],
        "answer": 1,
        "explain": "额枋等构件位于柱头之间，起横向拉结与承托作用。",
    },
    {
        "id": "dq_rafter",
        "theme": "general",
        "q": "“椽子”在建筑中主要承担？",
        "options": [
            "把瓦面荷载传到檩条",
            "把柱荷载传到基础",
            "只做门扇铰链",
            "形成台基台阶",
        ],
        "answer": 0,
        "explain": "椽条承托瓦屋面，将荷载传递到檩（及梁架体系）。",
    },
    {
        "id": "dq_siheyuan_privacy",
        "theme": "siheyuan",
        "q": "四合院高墙与内向布局，常见社会功能是？",
        "options": [
            "增强私密性与家庭领域感",
            "强制道路从院内穿过",
            "取消邻里交往",
            "让雨水全部进入正房",
        ],
        "answer": 0,
        "explain": "围合与高界面的门墙强化了居住的私密与领域感。",
    },
    {
        "id": "dq_palace_color",
        "theme": "palace",
        "q": "高等级宫殿屋面的黄色琉璃瓦，更常与什么相关？",
        "options": [
            "皇家礼制与等级象征（配合形制尺度）",
            "渔民习俗",
            "随机染色",
            "防火涂料唯一选择",
        ],
        "answer": 0,
        "explain": "色彩与形制、尺度一样，常体现等级与秩序，黄色琉璃多见于高等级宫殿语境。",
    },
    {
        "id": "dq_wood_frame",
        "theme": "general",
        "q": "游戏里“木架构机关”用木构化解，更符合真实木构的哪种思维？",
        "options": [
            "构件化：用合适的木构“消耗/操作”来通过节点",
            "木构只能观赏不能用",
            "必须用铁钉穿透才算木构",
            "木构不参与任何玩法",
        ],
        "answer": 0,
        "explain": "木构传统强调可拆装与构件替换，游戏里用“木构件”化解障碍是对这一思路的玩法化表达。",
    },
    # --- 题库扩充（三）---
    {
        "id": "dq_v3_zongheng",
        "theme": "general",
        "q": "传统木构架中，“枋”一类构件更常起什么作用？",
        "options": [
            "柱间水平联系与拉结，稳定排架",
            "专门代替瓦当滴水",
            "只用于地面铺装",
            "只承担屋面采光",
        ],
        "answer": 0,
        "explain": "枋多横向置于柱间，用于联系柱列、分配荷载并增强整体稳定。",
    },
    {
        "id": "dq_v3_ruodian",
        "theme": "siheyuan",
        "q": "北京四合院“影壁”与“大门”相对布置，更常见的空间意图是？",
        "options": [
            "形成入口缓冲，弱化街巷直视与穿堂风",
            "让马车从影壁顶上通过",
            "取消院落围合",
            "把正房移到院外",
        ],
        "answer": 0,
        "explain": "影壁可遮挡视线与导风，使入口更有层次，也具礼俗寓意。",
    },
    {
        "id": "dq_v3_yamen_jietang",
        "theme": "yamen",
        "q": "官署中“大堂/公堂”一类空间，更接近哪种功能？",
        "options": [
            "举行公务、审断、礼仪性接见等正式场合",
            "仅供家眷日常起居",
            "用来储存粮草不分昼夜",
            "专作园林水榭",
        ],
        "answer": 0,
        "explain": "大堂多承载正式公务与礼仪性功能，体现权威与公开性。",
    },
    {
        "id": "dq_v3_gong_qin",
        "theme": "palace",
        "q": "宫殿建筑群体中，“前朝后寝”概括的是？",
        "options": [
            "南部礼仪朝政空间相对靠前，北部生活起居相对靠后",
            "寝宫必须建在最南端",
            "取消轴线，只保留花园",
            "把所有建筑连成一条直线隧道",
        ],
        "answer": 0,
        "explain": "传统宫城布局常以前朝（礼仪政务）与后寝（生活）分区组织空间序列。",
    },
    {
        "id": "dq_v3_bridge_pier",
        "theme": "bridge",
        "q": "梁桥中的“桥墩”主要承受？",
        "options": [
            "上部结构传来的竖向荷载，并把力继续传到基础",
            "只承受风向不改变受力",
            "代替栏杆装饰",
            "储存桥面雨水",
        ],
        "answer": 0,
        "explain": "桥墩是中间支点，把桥面系荷载传递到地基（常与基础连成体系）。",
    },
    {
        "id": "dq_v3_techao",
        "theme": "general",
        "q": "古建筑大木作与小木作，下面哪项更接近常见区分思路？",
        "options": [
            "大木作偏承重主体构架；小木作偏装修隔断门窗等细木",
            "大木作只做油漆，小木作才用木料",
            "大木作只用于石桥",
            "两者没有区别",
        ],
        "answer": 0,
        "explain": "大木作承担结构主体；小木作多指装修、门窗、隔断等细木制作。",
    },
    {
        "id": "dq_v3_wudian",
        "theme": "palace",
        "q": "庑殿顶（四坡顶）在最常见的等级语境里，往往？",
        "options": [
            "多见于高等级建筑屋面形式之一（具体时代与实例需结合判断）",
            "只用于牲畜棚",
            "比普通民宅瓦房更低级",
            "不能在木结构屋顶出现",
        ],
        "answer": 0,
        "explain": "庑殿顶属高等级屋面形式之一，实际等级还需结合时代、地域与建筑群的礼制语境。",
    },
    {
        "id": "dq_v3_xieshan",
        "theme": "general",
        "q": "歇山顶可以粗浅理解为？",
        "options": [
            "庑殿与硬山/悬山特征结合的屋面形式，常见于等级较高的殿宇等",
            "只有单坡屋面",
            "平顶无排水",
            "没有桁檩，只靠彩绘固定",
        ],
        "answer": 0,
        "explain": "歇山顶结合多种屋面特征，是传统高等级建筑常见屋面类型之一。",
    },
    {
        "id": "dq_v3_lang",
        "theme": "siheyuan",
        "q": "四合院里的“抄手游廊”主要改善了？",
        "options": [
            "雨雪天在庭院周边的通达与过渡体验",
            "让院落完全不透光",
            "代替大门门禁",
            "储冰",
        ],
        "answer": 0,
        "explain": "游廊提供檐下贯通路径，利于雨天行走与空间层次过渡。",
    },
    {
        "id": "dq_v3_yingshan_dumen",
        "theme": "siheyuan",
        "q": "四合院“垂花门”更常被理解为？",
        "options": [
            "内院与外院之间的重要门屋，装饰性与礼仪性都较强",
            "屋顶上的装饰件，与门无关",
            "桥头的望柱",
            "台基石雕的总称",
        ],
        "answer": 0,
        "explain": "垂花门是四合院分区与视觉焦点之一，常兼具通行与装饰礼仪意义。",
    },
    {
        "id": "dq_v3_pailou",
        "theme": "yamen",
        "q": "牌楼（牌坊类）在传统空间里更常见的角色是？",
        "options": [
            "标识入口、纪念旌表或界定段落的空间节点",
            "代替斗拱承重整座殿",
            "只用于室内天花",
            "一定是封闭房间",
        ],
        "answer": 0,
        "explain": "牌楼多起标识、纪念与空间段落提示作用，形式多样。",
    },
    {
        "id": "dq_v3_gongmen",
        "theme": "palace",
        "q": "宫城城门体量大、门道深，除了通行，还常兼顾？",
        "options": [
            "防御、礼仪序列与空间转换（内外之别）",
            "只减少造桥成本",
            "防止院内见到天空",
            "专门饲养家禽",
        ],
        "answer": 0,
        "explain": "城门是防御与礼制空间序列的关键节点，强调内外分区与安全。",
    },
    {
        "id": "dq_v3_opening",
        "theme": "general",
        "q": "大木构架开间“面阔三开间”通常指？",
        "options": [
            "沿建筑正面方向，柱子分割形成的三个开间",
            "屋顶只有三块瓦",
            "台基只有三层",
            "院落必须有三个门",
        ],
        "answer": 0,
        "explain": "开间指柱网划分的横向单元数量，三开间即三跨柱距的正面划分。",
    },
    {
        "id": "dq_v3_jinshen",
        "theme": "palace",
        "q": "宫殿空间序列里，“进深”更常被理解为？",
        "options": [
            "沿垂直于殿前主立面方向，室内或柱网的纵深尺度",
            "屋面瓦片总数",
            "院子里椅子数量",
            "台阶必须是三级",
        ],
        "answer": 0,
        "explain": "进深描述建筑向纵深方向的尺度，与面阔共同刻画柱网与空间体量。",
    },
    {
        "id": "dq_v3_bridge_deck",
        "theme": "bridge",
        "q": "桥面系（桥面板、横梁等）对拱桥拱圈的主要关系是？",
        "options": [
            "把车辆与人群等荷载传到拱圈或主受力体系",
            "与拱圈完全不相干",
            "只负责美观不参与传力",
            "只在夜间受力",
        ],
        "answer": 0,
        "explain": "桥面系将使用荷载传递到主拱（或主梁）等承重体系。",
    },
    {
        "id": "dq_v3_shiqiao",
        "theme": "bridge",
        "q": "敞肩拱桥（如赵州桥一类思路）用“小拱”减载，大意是？",
        "options": [
            "在拱肩上开孔泄洪、减重并改善受力，利于大河通过",
            "让小拱代替主拱承受全部洪水冲击而不计主拱",
            "只用于装饰无所谓结构",
            "主拱必须填实不留孔",
        ],
        "answer": 0,
        "explain": "敞肩孔可分流泄洪、减轻自重并优化拱上砌筑与受力路径。",
    },
    {
        "id": "dq_v3_wadian_kesi",
        "theme": "general",
        "q": "瓦作与木作交接处强调防水构造，下面哪项更合理？",
        "options": [
            "依靠屋面坡度、檐口构造与瓦件搭接组织排水，避免渗漏泡木",
            "完全依赖室内地毯吸水",
            "瓦愈后愈应水平铺设",
            "檐口越短越利于防水",
        ],
        "answer": 0,
        "explain": "传统屋面依靠坡度与瓦作搭接导流雨水，保护檐口木构免受长期浸渍。",
    },
    {
        "id": "dq_v3_yamen_wub",
        "theme": "yamen",
        "q": "衙署前常设照壁、仪门序列，主要不是为了？",
        "options": [
            "让办事百姓完全不识字也能办公",
            "秩序与礼仪层次的递进",
            "形成由外而内的管控与导引",
            "强调权威与规制",
        ],
        "answer": 0,
        "explain": "衙署空间序列重在秩序、礼仪与管控导引；与“识字与否”无直接对应。",
    },
    {
        "id": "dq_v3_shijing",
        "theme": "siheyuan",
        "q": "四合院“抄手游廊”与庭院的关系，更接近？",
        "options": [
            "沿内院边缘布置，串联各房入口与院落活动",
            "建在邻居屋顶上",
            "替代垂花门位置",
            "只能南北向不能拐弯",
        ],
        "answer": 0,
        "explain": "游廊常沿庭院周边布置，方便晴雨通行并串联各幢房屋入口。",
    },
    {
        "id": "dq_v3_pingzuo",
        "theme": "palace",
        "q": "殿堂前“月台/台明”抬高室内外高差，常见作用包括？",
        "options": [
            "礼仪展示、排水防潮与组织踏步登台的空间层次",
            "让室内低于庭院淹水",
            "取消踏跺全部用绳梯",
            "只用于堆放杂物",
        ],
        "answer": 0,
        "explain": "月台抬高可强化礼仪体量、利于排水组织并设置踏道进入殿内。",
    },
]

# 界面显示：题目序号从 1 开始，与 DECRYPT_QUESTIONS 列表顺序一致（内部存储仍可用字符串 id）
DECRYPT_QUESTION_NUM_BY_KEY: dict[str, int] = {}
for _dq_i, _dq in enumerate(DECRYPT_QUESTIONS):
    if not isinstance(_dq, dict):
        continue
    _dq_n = _dq_i + 1
    _dq_id = _dq.get("id")
    if isinstance(_dq_id, str) and _dq_id:
        DECRYPT_QUESTION_NUM_BY_KEY[_dq_id] = _dq_n
    _dq_q = _dq.get("q")
    if isinstance(_dq_q, str) and _dq_q:
        DECRYPT_QUESTION_NUM_BY_KEY[_dq_q] = _dq_n

# 图鉴列表布局（与 _codex_list_max_scroll / draw_codex_screen 保持一致）
CODEX_CARD_H = 220
CODEX_CARD_GAP = 16
CODEX_LIST_Y0 = 138
CODEX_LIST_TOP_CLIP = 126
CODEX_LIST_BOTTOM_CLIP = HEIGHT - 52


def _codex_list_max_scroll() -> int:
    viewport_h = CODEX_LIST_BOTTOM_CLIP - CODEX_LIST_Y0
    total_h = len(CODEX_ENTRIES) * (CODEX_CARD_H + CODEX_CARD_GAP) - CODEX_CARD_GAP
    return max(0, total_h - viewport_h)


# -----------------------------
# Global Variables (全局变量)
# -----------------------------
game_state = GameState.MODE_SELECT
current_mode = 1  # 1: Single, 2: Double, 3: Triple, 4: Survival
SURVIVAL_MODE_ID = 4
speed = INITIAL_SPEED
score = 0
score_float = 0.0
high_score = 0
current_level = 1
bg_scroll_x = 0

# Run skill state (局内技能状态)
run_equipped_skills: list[str] = []
run_skill_levels: dict[str, int] = {}
run_skill_runtime = {
    "dash_next_ready_ms": 0,
    "dash_charges": 0,
    "invul_until_ms": 0,
}

# Run event state (局内事件/波次)
run_event = {
    "type": "",           # wind | rain | collapse | chase
    "until_ms": 0,
    "next_ms": 0,
    "boss_next_ms": 0,
}

# Run goals (局内任务)
run_start_ms: int = 0
run_goals: list[dict] = []

# Daily challenge (每日挑战)
daily_run: bool = False
daily_seed_used: int = 0

# Cultural progression state (文化进度)
cultural_counts = {
    CollectibleType.WADANG: 0,
    CollectibleType.DOUGONG: 0,
    CollectibleType.WOOD: 0,
}
codex_unlocked = set()  # entry ids
hud_toast = {"text": "", "until_ms": 0}
# Shop reset confirm removed: user expects one-click reset
shop_reset_confirm_until_ms: int = 0
home_tutorial_dismissed: bool = False  # 每次启动默认显示新手引导；点“我知道了”后本次隐藏
home_tutorial_page: int = 0           # 新手引导页码（0/1）
home_tutorial_hotspots = {}           # 新手引导热点（用于点击提示）
home_tutorial_hint = {"text": "", "until_ms": 0}

# Settings cache (设置缓存，用于即时生效)
settings_cache = {
    "jump_level": 1,      # 1-4
    "max_hp": 3,          # 1-6
    "music_volume": 0.7,  # 0.0-1.0
}

# UI return-state helpers (用于在图鉴/设置中返回原界面)
codex_return_state = GameState.MODE_SELECT
codex_scroll_y = 0  # 图鉴滚动偏移
codex_view_mode = "list"  # list | detail
codex_selected_entry_id = None
codex_page_idx = 0
loadout_scroll_y = 0  # 技能装备页：可选技能列表滚动偏移
shop_scroll_y = 0  # 技能商店：未解锁技能列表滚动偏移（像素，仅滚轮/中轴，不与左键混淆）

# 解密模式进度
decrypt_stats = {"correct": 0, "total": 0}
decrypt_current = None  # {"q","options","answer","explain"}
decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
decrypt_view = "quiz"  # quiz | result | wrongbook
decrypt_theme = "general"
decrypt_time_limit_s = 60
decrypt_start_ms: Optional[int] = None
decrypt_streak = 0
decrypt_score = 0
decrypt_wrong_scroll_y = 0
# 解密模式答题锁定/自动下一题（提升手感）
decrypt_choice_idx: Optional[int] = None
decrypt_lock_until_ms: int = 0
decrypt_auto_next_ms: int = 0
# 题池模式：all=全部题库；wrong=只练错题本
decrypt_pool_mode: str = "all"


def _decrypt_question_key(q: dict) -> str:
    if not isinstance(q, dict):
        return ""
    if isinstance(q.get("id"), str) and q.get("id"):
        return q["id"]
    if isinstance(q.get("q"), str) and q.get("q"):
        return q["q"]
    return ""


def _decrypt_question_number(q) -> Optional[int]:
    if not isinstance(q, dict):
        return None
    k = _decrypt_question_key(q)
    if not k:
        return None
    return DECRYPT_QUESTION_NUM_BY_KEY.get(k)


def _decrypt_pool(theme_key: str):
    if not isinstance(theme_key, str) or not theme_key:
        theme_key = "general"
    # wrong-only mode: only questions in wrongbook
    if decrypt_pool_mode == "wrong":
        try:
            wb = load_config().get("decrypt_wrong")
            if not isinstance(wb, list):
                wb = []
        except Exception:
            wb = []
        wb_set = set([k for k in wb if isinstance(k, str) and k])
        pool0 = []
        for q in DECRYPT_QUESTIONS:
            if not isinstance(q, dict):
                continue
            qid = q.get("id")
            if isinstance(qid, str) and qid in wb_set:
                pool0.append(q)
        # allow legacy: some wrongbook keys might be raw question text
        if not pool0 and wb_set:
            for q in DECRYPT_QUESTIONS:
                if isinstance(q, dict) and isinstance(q.get("q"), str) and q.get("q") in wb_set:
                    pool0.append(q)
        if pool0:
            pool = [q for q in pool0 if q.get("theme") == theme_key]
            if pool:
                return pool
            return pool0

    pool = [q for q in DECRYPT_QUESTIONS if q.get("theme") == theme_key]
    if not pool:
        pool = [q for q in DECRYPT_QUESTIONS if q.get("theme") in ("general", None)]
    if not pool:
        pool = list(DECRYPT_QUESTIONS)
    return pool


def _decrypt_new_question():
    """Pick a new question for decrypt mode."""
    global decrypt_current, decrypt_choice_idx, decrypt_lock_until_ms, decrypt_auto_next_ms
    pool = _decrypt_pool(decrypt_theme)
    decrypt_current = random.choice(pool) if pool else {
        "q": "（题库为空）", "options": ["返回主页"], "answer": 0, "explain": ""
    }
    decrypt_choice_idx = None
    decrypt_lock_until_ms = 0
    decrypt_auto_next_ms = 0


def _decrypt_record_wrong(qobj: dict):
    key = _decrypt_question_key(qobj)
    if not key:
        return
    cfg = load_config()
    wb = cfg.get("decrypt_wrong")
    if not isinstance(wb, list):
        wb = []
    if key not in wb:
        wb.append(key)
        # avoid infinite growth
        if len(wb) > 80:
            wb = wb[-80:]
        cfg["decrypt_wrong"] = wb
        save_config(cfg)


def _decrypt_best_update(score_value: int):
    cfg = load_config()
    best = cfg.get("decrypt_best_score")
    try:
        best = int(best)
    except Exception:
        best = 0
    if score_value > best:
        cfg["decrypt_best_score"] = int(score_value)
        save_config(cfg)


def _decrypt_reward_toast(text: str, is_ok: bool = True):
    global decrypt_feedback
    decrypt_feedback = {
        "text": text,
        "until_ms": pygame.time.get_ticks() + 2600,
        "is_correct": is_ok,
    }


def _decrypt_apply_reward(now_ms: int):
    """Rewards: unlock codex entry or add cultural counts."""
    global hud_toast
    # priority 0: unlock/upgrade a skill permanently
    try:
        cfg = load_config()
    except Exception:
        cfg = {}
    us = cfg.get("unlock_skills") if isinstance(cfg, dict) else {}
    if not isinstance(us, dict):
        us = {}
    # choose a skill that isn't maxed
    candidates = []
    for sid, meta in SKILLS.items():
        mx = int(meta.get("max_level", 1) or 1)
        cur = 0
        try:
            cur = int(us.get(sid, 0))
        except Exception:
            cur = 0
        if cur < mx:
            candidates.append(sid)
    if candidates:
        sid = random.choice(candidates)
        mx = int(SKILLS[sid].get("max_level", 1) or 1)
        try:
            cur = int(us.get(sid, 0))
        except Exception:
            cur = 0
        new_lv = min(mx, max(0, cur) + 1)
        us[sid] = new_lv
        cfg["unlock_skills"] = us
        save_config(cfg)
        hud_toast["text"] = f"解密奖励：技能解锁「{SKILLS[sid]['name']}」Lv{new_lv}"
        hud_toast["until_ms"] = now_ms + 2600
        return

    # priority: unlock a locked codex entry
    locked = [e for e in CODEX_ENTRIES if e["id"] not in codex_unlocked]
    if locked:
        pick = random.choice(locked)
        codex_unlocked.add(pick["id"])
        _persist_cultural_to_config()
        hud_toast["text"] = f"解密奖励：图鉴解锁「{pick['name']}」(按 I 查看)"
        hud_toast["until_ms"] = now_ms + 2400
        return
    # otherwise: grant cultural counts randomly
    t = random.choice([CollectibleType.WADANG, CollectibleType.DOUGONG, CollectibleType.WOOD])
    cultural_counts[t] += 1
    _persist_cultural_to_config()
    hud_toast["text"] = "解密奖励：获得 1 个构件（用于解锁图鉴）"
    hud_toast["until_ms"] = now_ms + 2400


def draw_decrypt_screen(win, resources, mouse_pos):
    """Decrypt mode UI: ancient architecture quiz."""
    global decrypt_current, decrypt_stats, decrypt_feedback
    global decrypt_view, decrypt_theme, decrypt_time_limit_s, decrypt_start_ms
    global decrypt_streak, decrypt_score, decrypt_wrong_scroll_y
    global decrypt_choice_idx, decrypt_lock_until_ms, decrypt_auto_next_ms, decrypt_pool_mode
    now_ms = pygame.time.get_ticks()
    # 自动下一题：给玩家短暂时间看对错与解析
    if decrypt_choice_idx is not None and decrypt_auto_next_ms and now_ms >= decrypt_auto_next_ms and decrypt_view == "quiz":
        decrypt_current = None
        decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}

    if decrypt_current is None:
        _decrypt_new_question()

    _ui_modal_overlay(win, 195)

    hx = 56
    # 不显示「解密模式」大字标题；仅保留副标题与主题入口
    _ui_blit_label(win, resources["small_font"], "限时闯关 · 主题题库 · 错题本 · 解锁奖励", (206, 216, 234), hx, 38, outline_rgb=(24, 34, 52))
    pygame.draw.line(win, UI_DIVIDER, (hx, 76), (WIDTH - hx, 76), 1)

    # theme selection pills
    theme_keys = ["siheyuan", "yamen", "palace", "bridge"]
    theme_labels = {"siheyuan": "四合院", "yamen": "官府", "palace": "皇宫", "bridge": "桥梁"}
    pill_y = 90
    pill_h = 36
    pill_w = 92
    pill_gap = 10
    row_w = len(theme_keys) * pill_w + (len(theme_keys) - 1) * pill_gap
    pill_x0 = WIDTH // 2 - row_w // 2
    theme_rects = []
    for i, tk in enumerate(theme_keys):
        r = pygame.Rect(pill_x0 + i * (pill_w + pill_gap), pill_y, pill_w, pill_h)
        theme_rects.append((tk, r))
        draw_button(
            win,
            theme_labels.get(tk, tk),
            r,
            resources["small_font"],
            decrypt_theme == tk,
            r.collidepoint(mouse_pos),
            style={
                "radius": 999,
                "hover_lift": 10,
                "bg_color": (232, 255, 246) if decrypt_theme == tk else (236, 252, 255),
                "border_color": (48, 156, 118) if decrypt_theme == tk else (76, 152, 182),
                "text_color": (28, 60, 52) if decrypt_theme == tk else (34, 58, 78),
            },
        )

    # timer + score
    if decrypt_start_ms is None:
        decrypt_start_ms = pygame.time.get_ticks()
    elapsed_s = max(0.0, (pygame.time.get_ticks() - decrypt_start_ms) / 1000.0)
    remain_s = max(0, int(decrypt_time_limit_s - elapsed_s))
    timer_color = (255, 210, 120) if remain_s <= 10 else (200, 210, 228)
    # 右上角倒计时/得分：加暗描边，提升清晰度
    timer_txt = f"倒计时 {remain_s}s"
    timer_s = resources["small_font"].render(timer_txt, True, timer_color)
    _ui_blit_label(
        win, resources["small_font"], timer_txt, timer_color,
        WIDTH - hx - timer_s.get_width(), 36, outline_rgb=(16, 22, 34)
    )
    score_txt = f"得分 {decrypt_score}  连对 {decrypt_streak}"
    score_s = resources["small_font"].render(score_txt, True, (210, 220, 238))
    _ui_blit_label(
        win, resources["small_font"], score_txt, (210, 220, 238),
        WIDTH - hx - score_s.get_width(), 62, outline_rgb=(16, 22, 34)
    )

    if remain_s <= 0:
        decrypt_view = "result"

    # 内容面板整体下移，避免遮挡主题选择（pill_y~pill_y+pill_h）
    panel_top = pill_y + pill_h + 18
    panel = pygame.Rect(hx, panel_top, WIDTH - hx * 2, HEIGHT - panel_top - 92)
    _ui_panel_shadow(win, panel, 16)
    _ui_draw_vertical_gradient_panel(win, panel, UI_CARD_NEUTRAL_TOP, UI_CARD_NEUTRAL_BOTTOM, radius=16)
    pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=16)

    # wrap helper (Chinese-friendly by character) — 头部/题目/解析共用
    def _wrap_line(text: str, font, max_w: int):
        lines = []
        cur = ""
        for ch in list(text):
            trial = cur + ch
            if font.size(trial)[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        return lines

    # Panel header strip + progress bar (让解密面板更有层次)
    # 答题页头部信息较多：加高头部，避免题库名/提示/统计与进度条挤成一团
    header_h = 102 if decrypt_view == "quiz" else 54
    header = pygame.Rect(panel.x, panel.y, panel.w, header_h)
    # soft gradient strip
    grad = pygame.Surface((header.w, header.h), pygame.SRCALPHA)
    for yy in range(header.h):
        t = yy / max(1, header.h - 1)
        r = int(238 + (248 - 238) * t)
        g = int(248 + (252 - 248) * t)
        b = int(252 + (255 - 252) * t)
        pygame.draw.line(grad, (r, g, b, 255), (0, yy), (header.w, yy))
    win.blit(grad, header.topleft)
    pygame.draw.line(win, UI_DIVIDER, (panel.x + 16, panel.y + header_h), (panel.right - 16, panel.y + header_h), 1)

    # progress bar（先定宽度，供左侧文字换行留白）
    pb_w = 260
    pb_h = 10
    pb = pygame.Rect(panel.right - 22 - pb_w, panel.y + 18, pb_w, pb_h)

    # 顶部信息条的文字只在答题页显示，避免与错题本/结算页标题重叠
    if decrypt_view == "quiz":
        theme_labels2 = {"siheyuan": "四合院题库", "yamen": "官府题库", "palace": "皇宫题库", "bridge": "桥梁题库", "general": "综合题库"}
        th_txt = theme_labels2.get(decrypt_theme, "题库")
        hy = panel.y + 12
        _ui_blit_label(win, resources["small_font"], th_txt, UI_TEXT_SECONDARY, panel.x + 22, hy, outline_rgb=(252, 252, 255))
        hint_txt = "提示：可用 A/B/C/D 快捷选择 · 点击“下一题”继续"
        hint_max_w = max(120, panel.w - 48 - pb_w - 28)
        hy += 22
        for ln in _wrap_line(hint_txt, resources["small_font"], hint_max_w)[:3]:
            _ui_blit_label(win, resources["small_font"], ln, UI_TEXT_SECONDARY, panel.x + 22, hy, outline_rgb=(252, 252, 255))
            hy += 20
        stat_txt = f"正确 {decrypt_stats['correct']} / {max(1, decrypt_stats['total'])} 题  · 得分 {decrypt_score}  连对 {decrypt_streak}"
        _ui_blit_label(win, resources["small_font"], stat_txt, (72, 86, 112), panel.x + 22, hy + 2, outline_rgb=(252, 252, 255))

    pygame.draw.rect(win, (226, 234, 246), pb, border_radius=999)
    ratio = 0.0
    if decrypt_time_limit_s > 0:
        ratio = max(0.0, min(1.0, float(remain_s) / float(decrypt_time_limit_s)))
    fill = pb.copy()
    fill.w = max(6, int(pb.w * ratio))
    pygame.draw.rect(win, (76, 152, 182) if remain_s > 10 else (188, 152, 88), fill, border_radius=999)
    pygame.draw.rect(win, (158, 176, 206), pb, 1, border_radius=999)

    q_text = decrypt_current.get("q", "")
    q_no = _decrypt_question_number(decrypt_current)
    opts = list(decrypt_current.get("options", []))
    if not opts:
        opts = ["（无选项）"]

    max_w = panel.w - 48
    # view: result
    if decrypt_view == "result":
        best = int(load_config().get("decrypt_best_score", 0))
        t1 = resources["large_font"].render("时间到！", True, UI_TEXT_PRIMARY)
        win.blit(t1, t1.get_rect(center=(WIDTH // 2, panel.y + 96)))
        stat = resources["font"].render(
            f"本局：{decrypt_stats['correct']} / {max(1, decrypt_stats['total'])} 题  · 得分 {decrypt_score}", True, UI_TEXT_PRIMARY
        )
        win.blit(stat, stat.get_rect(center=(WIDTH // 2, panel.y + 160)))
        bst = resources["small_font"].render(f"最佳：{max(best, decrypt_score)} 分", True, UI_TEXT_SECONDARY)
        win.blit(bst, bst.get_rect(center=(WIDTH // 2, panel.y + 200)))
        hint = resources["small_font"].render("可查看错题本或再来一局", True, UI_TEXT_SECONDARY)
        win.blit(hint, hint.get_rect(center=(WIDTH // 2, panel.y + 236)))

        back_rect = pygame.Rect(panel.centerx - 330, panel.bottom - 76, 210, 54)
        retry_rect = pygame.Rect(panel.centerx - 105, panel.bottom - 76, 210, 54)
        wrong_rect = pygame.Rect(panel.centerx + 120, panel.bottom - 76, 210, 54)
        draw_button(
            win, "返回主页", back_rect, resources["font"], False, back_rect.collidepoint(mouse_pos),
            style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78)},
        )
        draw_button(
            win, "再来一局", retry_rect, resources["font_bold"], False, retry_rect.collidepoint(mouse_pos),
            style={"bg_color": (230, 250, 255), "border_color": (44, 148, 176), "text_color": (26, 60, 78)},
        )
        draw_button(
            win, "错题本", wrong_rect, resources["font"], False, wrong_rect.collidepoint(mouse_pos),
            style={"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52)},
        )
        return {"view": "result", "back": back_rect, "retry": retry_rect, "wrongbook": wrong_rect, "themes": theme_rects}

    # view: wrongbook
    if decrypt_view == "wrongbook":
        cfg = load_config()
        wb = cfg.get("decrypt_wrong")
        if not isinstance(wb, list):
            wb = []
        # 错题本标题区：从 header 条下方开始，避免与顶部信息条重叠
        title2 = resources["font"].render("错题本（自动记录）", True, UI_TEXT_PRIMARY)
        win.blit(title2, (panel.x + 24, panel.y + header_h + 14))
        hint = resources["small_font"].render("滚轮/↑↓ 滚动 · 点击题目回到答题", True, UI_TEXT_SECONDARY)
        win.blit(hint, (panel.x + 24, panel.y + header_h + 48))
        pygame.draw.line(
            win,
            UI_DIVIDER,
            (panel.x + 24, panel.y + header_h + 78),
            (panel.right - 24, panel.y + header_h + 78),
            1,
        )

        list_y0 = panel.y + header_h + 92
        list_h = panel.h - header_h - 188
        viewport = pygame.Rect(panel.x + 24, list_y0, panel.w - 48, list_h)
        # basic list with scroll
        item_h = 58
        gap = 10
        total_h = len(wb) * (item_h + gap) - gap if wb else 0
        max_scroll = max(0, total_h - viewport.h)
        decrypt_wrong_scroll_y = max(0, min(int(decrypt_wrong_scroll_y), int(max_scroll)))

        # build a display-friendly map (id -> question text)
        q_by_id = {}
        q_by_text = set()
        for qobj in DECRYPT_QUESTIONS:
            if not isinstance(qobj, dict):
                continue
            qid = qobj.get("id")
            qq = qobj.get("q")
            if isinstance(qid, str) and qid and isinstance(qq, str) and qq:
                q_by_id[qid] = qq
            if isinstance(qq, str) and qq:
                q_by_text.add(qq)

        item_rects = []
        for idx, key in enumerate(wb):
            y = viewport.y + idx * (item_h + gap) - int(decrypt_wrong_scroll_y)
            r = pygame.Rect(viewport.x, y, viewport.w, item_h)
            if r.bottom < viewport.top or r.top > viewport.bottom:
                continue
            item_rects.append((key, r))
            # key is stored as id (preferred) or raw question text (legacy)
            display_q = ""
            if isinstance(key, str):
                if key in q_by_id:
                    display_q = q_by_id[key]
                elif key in q_by_text:
                    display_q = key
                else:
                    display_q = key
            prefix = f"{idx + 1}."
            wnum = DECRYPT_QUESTION_NUM_BY_KEY.get(key) if isinstance(key, str) else None
            if wnum is not None:
                btn_txt = f"{prefix} 题号{wnum} · {display_q}"
            else:
                btn_txt = f"{prefix} {display_q}"
            draw_button(
                win,
                btn_txt,
                r,
                resources["small_font"],
                False,
                r.collidepoint(mouse_pos),
                style={"radius": 12, "wrap": True, "pad": (16, 10), "line_gap": 3},
            )

        back_rect = pygame.Rect(panel.x + 24, panel.bottom - 72, 210, 54)
        practice_rect = pygame.Rect(panel.centerx - 120, panel.bottom - 72, 240, 54)
        clear_rect = pygame.Rect(panel.right - 24 - 210, panel.bottom - 72, 210, 54)
        draw_button(
            win, "返回答题", back_rect, resources["font"], False, back_rect.collidepoint(mouse_pos),
            style={"bg_color": (230, 250, 255), "border_color": (44, 148, 176), "text_color": (26, 60, 78)},
        )
        draw_button(
            win, "重练错题", practice_rect, resources["font_bold"], False, practice_rect.collidepoint(mouse_pos),
            style={"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52)},
        )
        draw_button(
            win, "清空错题本", clear_rect, resources["font"], False, clear_rect.collidepoint(mouse_pos),
            style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78)},
        )
        return {
            "view": "wrongbook",
            "back": back_rect,
            "practice": practice_rect,
            "clear": clear_rect,
            "items": item_rects,
            "max_scroll": max_scroll,
            "themes": theme_rects,
        }

    # view: quiz
    y = panel.y + header_h + 14
    if q_no is not None:
        id_line = f"题目编号：{q_no}"
        _ui_blit_label(
            win, resources["small_font"], id_line, (90, 104, 132),
            panel.x + 24, y, outline_rgb=(252, 252, 255),
        )
        y += resources["small_font"].get_height() + 6
    q_prefix = "题目："
    q_font = resources["font"]
    q_lines = _wrap_line(q_prefix + q_text, q_font, max_w)
    if len(q_lines) > 5:
        q_font = resources["small_font"]
        q_lines = _wrap_line(q_prefix + q_text, q_font, max_w)
    q_line_cap = 8
    if len(q_lines) > q_line_cap:
        q_lines = q_lines[:q_line_cap]
        if q_lines:
            last = q_lines[-1]
            ell = "…"
            while q_font.size(last + ell)[0] > max_w and len(last) > 1:
                last = last[:-1]
            q_lines[-1] = last + ell
    for ln in q_lines:
        s = q_font.render(ln, True, UI_TEXT_PRIMARY)
        win.blit(s, (panel.x + 24, y))
        y += s.get_height() + 5
    y += 8

    opt_rects = []
    gap = 10
    fb_area_h = 188
    btn_w = panel.w - 48
    opt_area_top = y
    opt_area_bottom = panel.bottom - fb_area_h
    avail_opts = max(140, opt_area_bottom - opt_area_top)

    line_gap_btn = 4
    pad_y_btn = 10
    max_opt_lines = 4

    def _option_row_heights(fnt, mlines: int):
        hs = []
        inner_w = max(10, btn_w - 36)
        for i, opt in enumerate(opts[:4]):
            label = f"{chr(ord('A') + i)}. {opt}"
            olines = _wrap_line(label, fnt, inner_w)
            if len(olines) > mlines:
                olines = olines[:mlines]
                last = olines[-1]
                while fnt.size(last + "…")[0] > inner_w and len(last) > 1:
                    last = last[:-1]
                olines[-1] = last + "…"
            th = len(olines) * fnt.get_height() + max(0, len(olines) - 1) * line_gap_btn + 2 * pad_y_btn + 8
            hs.append(max(48, th))
        return hs

    opt_font = resources["font"] if btn_w >= 560 else resources["small_font"]
    heights = _option_row_heights(opt_font, max_opt_lines)
    need_total = sum(heights) + gap * max(0, len(heights) - 1)
    if need_total > avail_opts:
        opt_font = resources["small_font"]
        heights = _option_row_heights(opt_font, max_opt_lines)
        need_total = sum(heights) + gap * max(0, len(heights) - 1)
    while need_total > avail_opts and max_opt_lines > 2:
        max_opt_lines -= 1
        heights = _option_row_heights(opt_font, max_opt_lines)
        need_total = sum(heights) + gap * max(0, len(heights) - 1)

    ans_idx = int(decrypt_current.get("answer", 0)) if decrypt_current else 0
    locked = (decrypt_choice_idx is not None and decrypt_lock_until_ms and now_ms < decrypt_lock_until_ms)
    cy = opt_area_top
    for i, opt in enumerate(opts[:4]):
        h = heights[i]
        r = pygame.Rect(panel.x + 24, cy, btn_w, h)
        cy += h + gap
        opt_rects.append(r)
        st = {"radius": 12, "hover_lift": 14, "wrap": True, "pad": (18, 10), "line_gap": line_gap_btn, "max_wrap_lines": max_opt_lines}
        if locked:
            st["hover_lift"] = 0
            st["auto_press"] = False
            if i == ans_idx:
                st.update({"bg_color": UI_SUCCESS_SOFT, "border_color": UI_SUCCESS, "text_color": (28, 60, 52)})
            elif decrypt_choice_idx == i and i != ans_idx:
                st.update({"bg_color": UI_DANGER_SOFT, "border_color": UI_DANGER, "text_color": (88, 34, 34)})
        draw_button(
            win,
            f"{chr(ord('A') + i)}. {opt}",
            r,
            opt_font,
            False,
            r.collidepoint(mouse_pos),
            style=st,
        )

    # feedback / explain：仅在需要展示时再画信息框（避免平时干扰阅读/倒计时观感）
    show_reveal = (decrypt_choice_idx is not None and decrypt_lock_until_ms and now_ms < decrypt_lock_until_ms)
    if show_reveal or (decrypt_feedback["text"] and decrypt_feedback["until_ms"] > now_ms):
        fb_box = pygame.Rect(panel.x + 16, panel.bottom - fb_area_h + 8, panel.w - 32, fb_area_h - 16)
        # draw a distinct background so answer/explain never "sits on" options visually
        fb_bg = pygame.Surface((fb_box.w, fb_box.h), pygame.SRCALPHA)
        is_ok = bool(decrypt_feedback.get("is_correct"))
        # unified success/fail soft background
        _soft = UI_SUCCESS_SOFT if is_ok else UI_DANGER_SOFT
        fb_bg.fill((int(_soft[0]), int(_soft[1]), int(_soft[2]), 235))
        win.blit(fb_bg, fb_box.topleft)
        pygame.draw.rect(win, UI_SUCCESS if is_ok else UI_DANGER, fb_box, 1, border_radius=12)
        pygame.draw.line(win, UI_DIVIDER, (fb_box.x + 12, fb_box.y + 36), (fb_box.right - 12, fb_box.y + 36), 1)
        fb_y = fb_box.y + 10
        color = UI_SUCCESS if is_ok else UI_DANGER
        fb_txt = decrypt_feedback.get("text") or ("正确！" if is_ok else "不对哦")
        _ui_blit_label(win, resources["font"], fb_txt, color, fb_box.x + 14, fb_y, outline_rgb=(252, 252, 255))

        ans = int(decrypt_current.get("answer", 0)) if decrypt_current else 0
        opts2 = list(decrypt_current.get("options", [])) if decrypt_current else []
        ans_txt = ""
        if 0 <= ans < len(opts2):
            ans_txt = f"正确答案：{chr(ord('A') + ans)}. {opts2[ans]}"
        if ans_txt:
            fb_y2 = fb_y + 36
            for ln in _wrap_line(ans_txt, resources["small_font"], max_w)[:3]:
                _ui_blit_label(win, resources["small_font"], ln, (52, 66, 92), fb_box.x + 14, fb_y2, outline_rgb=(252, 252, 255))
                fb_y2 += 22
        else:
            fb_y2 = fb_y + 36

        exp = decrypt_current.get("explain", "")
        if exp:
            for ln in _wrap_line("解析：" + str(exp), resources["small_font"], max_w)[:4]:
                _ui_blit_label(win, resources["small_font"], ln, UI_TEXT_SECONDARY, fb_box.x + 14, fb_y2, outline_rgb=(252, 252, 255))
                fb_y2 += 22

    # （统计已移到面板头部条内）

    # bottom buttons
    back_rect = pygame.Rect(hx, panel.bottom + 16, 200, 54)
    next_rect = pygame.Rect(WIDTH - hx - 200, panel.bottom + 16, 200, 54)
    wrong_rect = pygame.Rect(WIDTH // 2 - 110, panel.bottom + 16, 220, 54)
    draw_button(
        win, "返回主页", back_rect, resources["font"], False, back_rect.collidepoint(mouse_pos),
        style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78)},
    )
    draw_button(
        win, "下一题", next_rect, resources["font_bold"], False, next_rect.collidepoint(mouse_pos),
        style={"bg_color": (230, 250, 255), "border_color": (44, 148, 176), "text_color": (26, 60, 78)},
    )
    draw_button(
        win, "错题本", wrong_rect, resources["font"], False, wrong_rect.collidepoint(mouse_pos),
        style={"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52)},
    )

    return {"view": "quiz", "options": opt_rects, "back": back_rect, "next": next_rect, "wrongbook": wrong_rect, "themes": theme_rects}


# 建筑主题关卡（四合院 / 官府 / 皇宫 / 桥梁）— 定时轮换，改变机关生成倾向
BUILDING_THEMES = ("siheyuan", "yamen", "palace", "bridge")
BUILDING_THEME_LABELS = {
    "siheyuan": "四合院·榫卯机关",
    "yamen": "官府·巡卫潜行",
    "palace": "皇宫·飞檐多层",
    "bridge": "桥梁·晃动承重",
}
# 主页按钮短名（与 BUILDING_THEMES 顺序一致）
BUILDING_SCENE_BUTTON_LABELS = {
    "siheyuan": "四合院",
    "yamen": "官府",
    "palace": "皇宫",
    "bridge": "桥梁",
}
ARCHITECTURE_SPAWN_INTERVAL_MS = 5200
# 桥梁平台尺寸（高度过小贴图会像一条线）
BRIDGE_PLATFORM_WIDTH = 300
BRIDGE_PLATFORM_HEIGHT = 90
# 飞檐（皇宫主题）：平台更长便于贴图展示
EAVE_PLATFORM_WIDTH = 280
EAVE_PLATFORM_WIDTH_ALT = 250
EAVE_PLATFORM_HEIGHT = 28
EAVE_SECOND_X_OFFSET = 330

building_theme = "siheyuan"
building_theme_ms = 0
architecture_spawn_timer = 0.0
architecture_platforms: list = []
patrol_guards: list = []

# Survival Mode Variables (生存模式专属变量)
survival_mode_duration = 0  # Survival time (seconds)
survival_next_boss_wave = 30  # BOSS wave interval (seconds)
survival_item_interval = 6000  # Item spawn interval (ms)

# UI Decorations (UI装饰元素)
clouds = []
stars = []  # For night effect (夜间效果星星)

# -----------------------------
# Resource Loading (资源加载)
# -----------------------------
def load_resources():
    resources = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load Dino Animation Frames (加载恐龙动画帧)
    resources['dino_frames'] = []
    resources['dino_frames_crouch'] = []
    try:
        for i in range(1, 13):
            if i == 8:  # 跳过8.png
                continue
            frame_num = f"0{i}" if i < 10 else str(i)
            img_path = os.path.join(script_dir, f"{frame_num}.png")
            if os.path.exists(img_path):
                frame = pygame.image.load(img_path).convert_alpha()
                resources['dino_frames'].append(pygame.transform.smoothscale(frame, (DINO_WIDTH, DINO_HEIGHT)))
                resources['dino_frames_crouch'].append(pygame.transform.smoothscale(frame, (DINO_WIDTH, DINO_HEIGHT // 2)))
        if resources['dino_frames']:
            print(f"Loaded {len(resources['dino_frames'])} dino animation frames")
        else:
            print("Warning: No dino animation frames found!")
    except Exception as e:
        print(f"Error loading dino frames: {e}")
        resources['dino_frames'] = None
        resources['dino_frames_crouch'] = None

    # Load Health Pack Image (加载血包图片 001.png)
    resources['health_item_img'] = None
    try:
        health_path = os.path.join(script_dir, "001.png")
        if os.path.exists(health_path):
            health_img = pygame.image.load(health_path).convert_alpha()
            resources['health_item_img'] = pygame.transform.scale(health_img, (40, 40))
            print("Loaded health pack image: 001.png")
        else:
            print("Warning: Health pack image (001.png) not found - using default green square")
    except Exception as e:
        print(f"Error loading health pack image: {e}")
        resources['health_item_img'] = None
        
    # Load Shield Image (加载护盾图片 002.png)
    resources['shield_item_img'] = None
    try:
        shield_path = os.path.join(script_dir, "002.png")
        if os.path.exists(shield_path):
            shield_img = pygame.image.load(shield_path).convert_alpha()
            resources['shield_item_img'] = pygame.transform.scale(shield_img, (40, 40))
            print("Loaded shield image: 002.png")
        else:
            print("Warning: Shield image (002.png) not found - using default blue square")
    except Exception as e:
        print(f"Error loading shield image: {e}")
        resources['shield_item_img'] = None

    # 移除备用恐龙图片加载（不再使用1.png）
    resources['dino'] = None

    # Load Background Image (加载背景图片)
    resources['background'] = None
    try:
        bg_paths = ["2.png", "2.jpg", "2.jpeg", "background.png", "background.jpg"]
        for path in bg_paths:
            bg_full_path = os.path.join(script_dir, path)
            if os.path.exists(bg_full_path):
                bg_img = pygame.image.load(bg_full_path).convert()
                resources['background'] = pygame.transform.scale(bg_img, (WIDTH, HEIGHT)) if bg_img.get_width() < WIDTH else bg_img
                break
        if not resources['background']:
            print("Error: No background image found! Using gradient background")
    except Exception as e:
        print(f"Error loading background: {e}")
        resources['background'] = None

    # Load Game Over Image (加载游戏结束图片)
    try:
        game_over_path = os.path.join(script_dir, "3.png")
        resources['game_over_img'] = pygame.image.load(game_over_path).convert_alpha()
    except FileNotFoundError:
        resources['game_over_img'] = None
    except Exception as e:
        resources['game_over_img'] = None

    # Load Obstacle Images (加载障碍物图片)
    try:
        resources['obstacle_imgs'] = {}
        img_map = {"small_cactus": "5.png", "tall_cactus": "6.png", "rock": "7.png"}
        for obs_type, height in OBSTACLE_HEIGHTS.items():
            img_name = img_map.get(obs_type)
            if img_name:
                img_path = os.path.join(script_dir, img_name)
                if os.path.exists(img_path):
                    img = pygame.image.load(img_path).convert_alpha()
                    resources['obstacle_imgs'][obs_type] = pygame.transform.scale(img, (OBSTACLE_WIDTH, height))
                else:
                    print(f"Warning: {obs_type} image ({img_name}) not found - using default color")
    except FileNotFoundError as e:
        resources['obstacle_imgs'] = None
        print(f"Warning: Could not load obstacle image: {e.filename}")
    except Exception as e:
        resources['obstacle_imgs'] = None
        print(f"Warning: Error loading obstacle images: {e}")

    # Load Flying Obstacle Images (加载飞行障碍物图片)
    try:
        resources['flying_obstacle_imgs'] = {}
        flying_img_map = {
            "balloon": "21.png",
            "daodan": "20.png"
        }
        for obs_type, img_name in flying_img_map.items():
            if obs_type in FLYING_OBSTACLE_PROPERTIES:
                props = FLYING_OBSTACLE_PROPERTIES[obs_type]
                img_path = os.path.join(script_dir, img_name)
                if os.path.exists(img_path):
                    img = pygame.image.load(img_path).convert_alpha()
                    resources['flying_obstacle_imgs'][obs_type] = pygame.transform.scale(img, (props["width"], props["height"]))
                else:
                    print(f"Warning: {obs_type} image ({img_name}) not found - using default color")
    except FileNotFoundError as e:
        resources['flying_obstacle_imgs'] = None
        print(f"Error: Flying obstacle image not found: {e.filename}")
    except Exception as e:
        resources['flying_obstacle_imgs'] = None
        print(f"Error loading flying obstacle images: {e}")

    # Load Home/Menu Music (加载主页音乐：可切换)
    resources["home_music_tracks"] = []
    try:
        for fn, nice_name in HOME_MUSIC_META:
            p = os.path.join(script_dir, str(fn))
            if os.path.exists(p):
                resources["home_music_tracks"].append({"path": p, "name": str(nice_name)})
    except Exception:
        resources["home_music_tracks"] = []

    def _pick_menu_music_path_by_index(idx: int) -> Optional[str]:
        tracks = resources.get("home_music_tracks") or []
        if not tracks:
            return None
        if not isinstance(idx, int):
            idx = 0
        idx = idx % len(tracks)
        return tracks[idx].get("path")

    tracks = resources.get("home_music_tracks") or []

    def _default_home_menu_index() -> int:
        if not tracks:
            return 0
        want = str(DEFAULT_HOME_MUSIC_BASENAME).lower()
        for i, t in enumerate(tracks):
            try:
                if os.path.basename(str(t.get("path", ""))).lower() == want:
                    return i
            except Exception:
                pass
        return 0

    cfg0 = load_config()
    try:
        menu_music_index = int(cfg0.get("menu_music_index", -1))
    except Exception:
        menu_music_index = -1

    if tracks:
        if menu_music_index < 0 or menu_music_index >= len(tracks):
            menu_music_index = _default_home_menu_index()

    menu_music_path = _pick_menu_music_path_by_index(menu_music_index)
    if not menu_music_path:
        # fallback to old behavior if the 4 tracks are missing
        candidates = [MODE_SELECT_MUSIC, "0.mp3", "1.mp3"]
        for fn in candidates:
            p = os.path.join(script_dir, str(fn))
            if os.path.exists(p):
                menu_music_path = p
                break

    resources["menu_music_index"] = menu_music_index
    resources["menu_music_name"] = ""
    try:
        if tracks:
            resources["menu_music_name"] = str(tracks[menu_music_index % len(tracks)].get("name", ""))
    except Exception:
        resources["menu_music_name"] = ""

    try:
        if menu_music_path:
            # Prefer Sound (low latency). If decoder rejects, fallback to music channel.
            try:
                resources['mode_select_music'] = pygame.mixer.Sound(menu_music_path)
                resources['mode_select_music_kind'] = "sound"
                resources['mode_select_music_path'] = menu_music_path
                resources['mode_select_music_loaded'] = True
            except Exception as e:
                resources['mode_select_music'] = None
                resources['mode_select_music_kind'] = "music"
                resources['mode_select_music_path'] = menu_music_path
                resources['mode_select_music_loaded'] = True
                print(f"Warning: Sound decode failed for menu music ({os.path.basename(menu_music_path)}): {e}")
        else:
            resources['mode_select_music_loaded'] = False
            resources['mode_select_music_path'] = None
            resources['mode_select_music_kind'] = "music"
    except Exception as e:
        resources['mode_select_music_loaded'] = False
        print(f"Error loading mode select music: {e}")

    # In-game music pool (局内音乐池：各模式随机播放同一组曲目)
    resources["game_music_pool"] = []
    try:
        for fn in GAME_MUSIC_POOL:
            p = os.path.join(script_dir, str(fn))
            if os.path.exists(p):
                resources["game_music_pool"].append(p)
    except Exception:
        resources["game_music_pool"] = []

    def _pick_windows_cjk_font_path() -> Optional[str]:
        # 强制选用 Windows 自带字体文件，避免 SysFont 选到无中文字形导致乱码/方块
        win_fonts_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        candidates = [
            "msyhui.ttc",   # 微软雅黑 UI（更适合屏幕显示，优先）
            "msyh.ttc",     # 微软雅黑
            "msyhbd.ttc",
            "msyhl.ttc",
            "simhei.ttf",   # 黑体
            "simsun.ttc",   # 宋体
            "simkai.ttf",
            "arialuni.ttf", # Arial Unicode (不一定存在)
        ]
        for fn in candidates:
            p = os.path.join(win_fonts_dir, fn)
            if os.path.exists(p):
                return p
        return None

    def _make_font(size: int, bold: bool = False):
        font_path = _pick_windows_cjk_font_path()
        try:
            if font_path:
                f = pygame.font.Font(font_path, size)
            else:
                # fallback: try common family list; still might fail on some PCs
                f = pygame.font.SysFont(["Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Arial"], size)
            f.set_bold(bold)
            return f
        except Exception:
            f = pygame.font.Font(None, size)
            try:
                f.set_bold(bold)
            except Exception:
                pass
            return f

    # 字体策略：
    # - 常规正文/按钮使用非粗体，避免“黑字太粗”
    # - 标题与强调使用粗体
    resources['font'] = _make_font(30, bold=False)
    resources['font_bold'] = _make_font(32, bold=True)
    resources['large_font'] = _make_font(72, bold=True)
    resources['small_font'] = _make_font(22, bold=False)
    resources['tiny_font'] = _make_font(18, bold=False)
    resources['title_font'] = _make_font(80, bold=True)

    # Load cultural collectible icons (文化收集物图标)
    # 你只要把对应 png 放到同目录就会自动显示：
    # wadang.png / dougong.png / wood.png
    resources["collectible_imgs"] = {}
    icon_map = {
        CollectibleType.WADANG: "wadang.png",
        CollectibleType.DOUGONG: "dougong.png",
        CollectibleType.WOOD: "wood.png",
    }
    icon_size_map = {
        CollectibleType.WADANG: (42, 42),
        CollectibleType.DOUGONG: (42, 42),
        CollectibleType.WOOD: (96, 96),  # wood.png 再放大一些更醒目
    }
    for ct, fn in icon_map.items():
        p = os.path.join(script_dir, fn)
        try:
            if os.path.exists(p):
                img = pygame.image.load(p).convert_alpha()
                resources["collectible_imgs"][ct] = pygame.transform.smoothscale(img, icon_size_map.get(ct, (42, 42)))
        except Exception as e:
            print(f"Warning: failed to load collectible icon {fn}: {e}")

    # Optional wood-frame obstacle image (木架机关图片，可选)
    # 放一个 wood_frame.png 在同目录即可替换默认绘制
    resources["wood_frame_img"] = None
    try:
        p = os.path.join(script_dir, "wood_frame.png")
        if os.path.exists(p):
            img = pygame.image.load(p).convert_alpha()
            resources["wood_frame_img"] = pygame.transform.smoothscale(img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHTS["wood_frame"]))
    except Exception as e:
        print(f"Warning: failed to load wood_frame.png: {e}")

    # 官府巡卫立绘（同目录放置 卫.png）
    resources["patrol_guard_img"] = None
    try:
        _wg = os.path.join(script_dir, "卫.png")
        if os.path.exists(_wg):
            _wi = pygame.image.load(_wg).convert_alpha()
            resources["patrol_guard_img"] = pygame.transform.smoothscale(_wi, (50, 72))
            print("Loaded patrol guard image: 卫.png")
    except Exception as e:
        print(f"Warning: failed to load 卫.png: {e}")

    # 桥梁机关贴图（同目录放置 桥.png，绘制时按平台矩形尺寸缩放）
    resources["bridge_platform_src"] = None
    try:
        _bp = os.path.join(script_dir, "桥.png")
        if os.path.exists(_bp):
            resources["bridge_platform_src"] = pygame.image.load(_bp).convert_alpha()
            print("Loaded bridge platform image: 桥.png")
    except Exception as e:
        print(f"Warning: failed to load 桥.png: {e}")

    # 飞檐贴图：飞.png / 飞 .png / 飞2.png 任一存在即可（按顺序优先加载）
    resources["eave_platform_src"] = None
    for _ef in ("飞.png", "飞 .png", "飞2.png"):
        _ep = os.path.join(script_dir, _ef)
        try:
            if os.path.exists(_ep):
                resources["eave_platform_src"] = pygame.image.load(_ep).convert_alpha()
                print(f"Loaded eave platform image: {_ef}")
                break
        except Exception as e:
            print(f"Warning: failed to load {_ef}: {e}")

    # 榫卯平台贴图：优先 榫卯.png，其次 榫卯.pmg（兼容文件名）
    resources["mortise_platform_src"] = None
    for _mf in ("榫卯.png", "榫卯.pmg"):
        _mp = os.path.join(script_dir, _mf)
        try:
            if os.path.exists(_mp):
                resources["mortise_platform_src"] = pygame.image.load(_mp).convert_alpha()
                print(f"Loaded mortise platform image: {_mf}")
                break
        except Exception as e:
            print(f"Warning: failed to load {_mf}: {e}")

    # Initialize Stars (初始化星星装饰)
    global stars
    stars = [{"x": random.randint(0, WIDTH), "y": random.randint(0, 200), "size": random.uniform(1, 3), "brightness": random.randint(150, 255)} for _ in range(80)]

    return resources

# -----------------------------
# Background Drawing (绘制背景)
# -----------------------------
def draw_background(win, resources):
    global bg_scroll_x, clouds, stars, cloud_surface_cache
    has_bg_img = bool(resources.get('background'))
    if has_bg_img:
        try:
            # Scrolling background image (滚动背景图)
            bg = resources['background']
            bw = bg.get_width()
            win.blit(bg, (bg_scroll_x, 0))
            win.blit(bg, (bg_scroll_x + bw, 0))

            scroll_speed = speed / 2.5 if game_state == GameState.PLAYING else 0.3
            bg_scroll_x -= scroll_speed
            if bg_scroll_x <= -bw:
                bg_scroll_x = 0
        except Exception:
            # fallback to gradient if blit fails
            has_bg_img = False

    # Gradient Background (渐变背景 - 白天/黑夜切换)
    if not has_bg_img:
        if game_state == GameState.MODE_SELECT:
            # Day gradient (白天渐变)
            for y in range(HEIGHT):
                r = int(135 + (255 - 135) * (y / HEIGHT))
                g = int(206 + (255 - 206) * (y / HEIGHT))
                b = int(235 + (255 - 235) * (y / HEIGHT))
                pygame.draw.line(win, (r, g, b), (0, y), (WIDTH, y))
        else:
            # Night gradient (夜间渐变)
            for y in range(HEIGHT):
                r = int(10 + (30 - 10) * (y / HEIGHT))
                g = int(20 + (50 - 20) * (y / HEIGHT))
                b = int(80 + (120 - 80) * (y / HEIGHT))
                pygame.draw.line(win, (r, g, b), (0, y), (WIDTH, y))

            # Draw stars (绘制星星)
            for star in stars:
                star['x'] -= 0.1
                if star['x'] < 0:
                    star['x'] = WIDTH
                pygame.draw.circle(win, (star['brightness'], star['brightness'], 255), (int(star['x']), int(star['y'])), int(star['size']))

    # Draw decorative ground (绘制装饰性地面)
    # - 背景图通常已经有地面元素；这里仍保留，确保无背景图时可见
    if not has_bg_img:
        pygame.draw.rect(win, (169, 169, 169), (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))
        pygame.draw.rect(win, (139, 69, 19), (0, HEIGHT - 5, WIDTH, 5))  # Ground border (地面边界)

    # Draw clouds (绘制云朵)
    if not clouds:
        for _ in range(5):
            clouds.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(50, 150),
                'size': random.randint(50, 100),
                'speed': random.uniform(0.2, 0.5),
                # style variant so clouds don't all look identical
                'variant': random.randint(0, 2),
            })

    for cloud in clouds:
        cloud['x'] -= cloud['speed']
        if cloud['x'] < -cloud['size']:
            cloud['x'] = WIDTH + random.randint(50, 100)
            cloud['y'] = random.randint(50, 150)
            cloud['variant'] = random.randint(0, 2)

        # Draw cloud with layers (绘制多层云朵)
        # 缓存云朵 surface：避免每帧创建新 Surface
        try:
            cache = cloud_surface_cache
        except Exception:
            cache = {}
            cloud_surface_cache = cache

        sz = int(cloud.get('size', 80))
        variant = int(cloud.get('variant', 0))
        key = (sz, variant)
        cloud_surface = cache.get(key)
        if cloud_surface is None:
            w = sz
            h = max(1, int(sz * 0.56))
            cloud_surface = pygame.Surface((w + 14, h + 14), pygame.SRCALPHA)

            # A slightly different shape per variant (more "cartoon cloud")
            if variant == 0:
                blobs = [(0.22, 0.58, 0.30), (0.44, 0.42, 0.36), (0.68, 0.55, 0.32), (0.50, 0.66, 0.44)]
            elif variant == 1:
                blobs = [(0.20, 0.60, 0.28), (0.40, 0.45, 0.34), (0.62, 0.42, 0.30), (0.78, 0.58, 0.26), (0.52, 0.68, 0.48)]
            else:
                blobs = [(0.18, 0.62, 0.30), (0.38, 0.46, 0.38), (0.58, 0.44, 0.34), (0.78, 0.56, 0.30), (0.52, 0.70, 0.52)]

            # Shadow (soft) - helps pop on detailed background
            shadow_col = (0, 0, 0, 50)
            ox, oy = 9, 9
            for (cx, cy, rr) in blobs:
                r = max(6, int(min(w, h) * rr * 0.55))
                pygame.draw.circle(cloud_surface, shadow_col, (ox + int(w * cx), oy + int(h * cy)), r)

            # Main body
            body_col = (248, 248, 252, 210)
            for (cx, cy, rr) in blobs:
                r = max(6, int(min(w, h) * rr * 0.55))
                pygame.draw.circle(cloud_surface, body_col, (7 + int(w * cx), 7 + int(h * cy)), r)

            # Base belly (slightly flatter)
            pygame.draw.ellipse(cloud_surface, (245, 245, 250, 200), (7, 7 + int(h * 0.40), w, int(h * 0.55)))

            # Highlight (top-left)
            hi_col = (255, 255, 255, 165)
            pygame.draw.ellipse(cloud_surface, hi_col, (7 + int(w * 0.10), 7 + int(h * 0.10), int(w * 0.55), int(h * 0.55)))

            cache[key] = cloud_surface

        win.blit(cloud_surface, (cloud['x'], cloud['y']))

# -----------------------------
# Game Objects (游戏对象)
# -----------------------------
class Dinosaur:
    FRAME_DURATION = 80
    def __init__(self, resources, x_pos, color, jump_button=None, jump_key=None, is_survival_mode=False):
        self.frames = resources.get('dino_frames')
        self.frames_crouch = resources.get('dino_frames_crouch')
        self.current_frame = 0
        self.frame_timer = 0
        self.image = resources['dino']
        self.x = x_pos
        self.y = HEIGHT - DINO_HEIGHT - GROUND_HEIGHT
        self.vel_y = 0
        self.is_jumping = False
        self.anim_offset = 0
        self.width = DINO_WIDTH
        self.height = DINO_HEIGHT
        self.jump_force = -20
        self.color = color
        self.jump_button = jump_button
        self.jump_key = jump_key
        # Jump settings (跳跃段数：1/2/3 段跳)
        self.max_jumps_total = 1
        self.jumps_used = 0  # number of jumps since last time on ground
        self.is_crouching = False
        self.normal_height = DINO_HEIGHT
        self.crouch_height = DINO_HEIGHT // 2
        
        # Only survival mode has health and shield (仅生存模式有血量和护盾)
        self.is_survival_mode = is_survival_mode
        if is_survival_mode:
            self.max_health = 3
            self.health = 3
            self.shields = 0
            
    def jump(self):
        if game_state != GameState.PLAYING: return
        # allow 1/2/3 total jumps before landing
        if self.jumps_used >= self.max_jumps_total:
            return

        # first jump starts airborne state
        if self.jumps_used == 0:
            self.is_jumping = True

        self.jumps_used += 1

        # slight diminishing returns for 2nd/3rd jump
        scale = 1.0
        if self.jumps_used == 2:
            scale = 0.82
        elif self.jumps_used == 3:
            scale = 0.70
        elif self.jumps_used == 4:
            scale = 0.60
        self.vel_y = self.jump_force * scale
            
    def crouch(self, is_crouching): 
        self.is_crouching = is_crouching
            
    def add_item(self, item_type):
        """Add item effect (only for survival mode)"""
        if not self.is_survival_mode: return
        
        if item_type == ItemType.HEALTH and self.health < self.max_health:
            self.health += 1
        elif item_type == ItemType.SHIELD:
            self.shields += 1
            
    def take_damage(self):
        """Take damage (only survival mode has damage mechanism)"""
        if not self.is_survival_mode:
            return True  # Instant death in other modes (非生存模式直接死亡)
            
        if self.shields > 0:
            self.shields -= 1
            return False
            
        self.health -= 1
        if self.health <= 0:
            return True  # Health exhausted (生命值耗尽)
        return False
        
    def _update_animation(self, dt):
        if not self.frames or game_state != GameState.PLAYING or self.is_jumping: return
        self.frame_timer += dt
        if self.frame_timer >= self.FRAME_DURATION:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
    def update(self, dt, platforms=None):
        if game_state != GameState.PLAYING: return
        platforms = platforms or []

        self._update_animation(dt)

        h = self.crouch_height if self.is_crouching else self.normal_height
        prev_y = self.y

        self.vel_y += GRAVITY
        self.y += self.vel_y

        feet_left = self.x + 12
        feet_right = self.x + self.width - 12
        prev_bottom = prev_y + h
        cur_bottom = self.y + h

        best_plat = None
        best_top = None
        if self.vel_y >= 0:
            for plat in platforms:
                if not plat.is_solid():
                    continue
                pr = plat.get_rect()
                if feet_right <= pr.x or feet_left >= pr.right:
                    continue
                if prev_bottom <= pr.y + 4 and cur_bottom >= pr.y - 1:
                    if best_plat is None or pr.y < best_top:
                        best_plat = plat
                        best_top = pr.y

        if best_plat is not None:
            pr = best_plat.get_rect()
            self.y = pr.y - h
            self.vel_y = 0
            self.is_jumping = False
            self.jumps_used = 0
            if getattr(best_plat, "kind", "") == "eave":
                self.vel_y = self.jump_force * 0.82
                self.is_jumping = True
                self.jumps_used = 0
            self.anim_offset = 0
            return

        ground_line = HEIGHT - GROUND_HEIGHT
        if self.y + h > ground_line:
            self.y = ground_line - h
            self.vel_y = 0
            self.is_jumping = False
            self.jumps_used = 0

        self.anim_offset = 0
        
    def draw(self, win, resources):
        draw_y = self.y
        current_image_to_draw = None
        
        if self.is_crouching:
            draw_y += (self.normal_height - self.crouch_height)
            if self.frames_crouch:
                try: 
                    current_image_to_draw = self.frames_crouch[self.current_frame]
                except: 
                    pass
        else:
            if self.frames:
                try: 
                    current_image_to_draw = self.frames[self.current_frame]
                except: 
                    pass
                    
        if not current_image_to_draw and self.image:
            current_image_to_draw = pygame.transform.smoothscale(
                self.image, 
                (self.width, self.crouch_height if self.is_crouching else self.normal_height)
            )
        
        # Draw dinosaur (绘制恐龙)
        if current_image_to_draw:
            win.blit(current_image_to_draw, (self.x, draw_y + self.anim_offset))
        else:
            rect_height = self.crouch_height if self.is_crouching else self.normal_height
            pygame.draw.rect(win, self.color, (self.x, draw_y, self.width, rect_height), border_radius=5)
            
        # Draw shield effect (only survival mode) (绘制护盾效果)
        if self.is_survival_mode and self.shields > 0:
            shield_surface = pygame.Surface((self.width + 20, self.normal_height + 20), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (100, 150, 255, 100), (self.width // 2 + 10, self.normal_height // 2 + 10), self.width // 2 + 15)
            pygame.draw.circle(shield_surface, (100, 150, 255, 150), (self.width // 2 + 10, self.normal_height // 2 + 10), self.width // 2 + 10, 2)
            win.blit(shield_surface, (self.x - 10, self.y - 10))
            
    def get_hitbox(self):
        hitbox_width = self.width - 20
        if self.is_crouching:
            hitbox_height = self.crouch_height - 10
            return pygame.Rect(
                self.x + 10, 
                self.y + (self.normal_height - self.crouch_height) + 5, 
                hitbox_width, 
                hitbox_height
            )
        return pygame.Rect(self.x + 10, self.y + 10, hitbox_width, self.normal_height - 20)

class Obstacle:
    def __init__(self, resources, obs_type=None):
        self.type = obs_type if obs_type else random.choice(list(OBSTACLE_HEIGHTS.keys()))
        self.height = OBSTACLE_HEIGHTS[self.type]
        self.image = resources['obstacle_imgs'].get(self.type) if resources['obstacle_imgs'] else None
        self.width = OBSTACLE_WIDTH
        self.x = WIDTH
        self.y = HEIGHT - self.height - GROUND_HEIGHT
        self.speed = speed
        
    def update(self):
        if game_state == GameState.PLAYING: 
            self.x -= self.speed
            
    def draw(self, win, resources):
        if self.image: 
            win.blit(self.image, (self.x, self.y))
        else:
            if self.type == "wood_frame" and resources.get("wood_frame_img") is not None:
                win.blit(resources["wood_frame_img"], (self.x, self.y))
                return

            color_map = {
                "small_cactus": (34, 139, 34), 
                "tall_cactus": (0, 100, 0), 
                "rock": (139, 69, 19),
                "wood_frame": (150, 96, 52),
            }
            if self.type == "wood_frame":
                # Draw a more "wooden frame" looking obstacle (替代难看的色块)
                base = pygame.Rect(self.x, self.y, self.width, self.height)
                wood = color_map["wood_frame"]
                dark = (max(0, wood[0] - 35), max(0, wood[1] - 25), max(0, wood[2] - 25))
                light = (min(255, wood[0] + 25), min(255, wood[1] + 18), min(255, wood[2] + 18))

                pygame.draw.rect(win, wood, base, border_radius=8)
                pygame.draw.rect(win, dark, base, 3, border_radius=8)

                # vertical posts
                post_w = 18
                left_post = pygame.Rect(base.x + 10, base.y + 10, post_w, base.height - 20)
                right_post = pygame.Rect(base.right - 10 - post_w, base.y + 10, post_w, base.height - 20)
                pygame.draw.rect(win, dark, left_post, border_radius=6)
                pygame.draw.rect(win, dark, right_post, border_radius=6)
                pygame.draw.rect(win, light, left_post.inflate(-8, -8), border_radius=5)
                pygame.draw.rect(win, light, right_post.inflate(-8, -8), border_radius=5)

                # cross beams
                beam_h = 16
                top_beam = pygame.Rect(base.x + 20, base.y + 18, base.width - 40, beam_h)
                mid_beam = pygame.Rect(base.x + 20, base.y + base.height//2 - beam_h//2, base.width - 40, beam_h)
                pygame.draw.rect(win, dark, top_beam, border_radius=6)
                pygame.draw.rect(win, dark, mid_beam, border_radius=6)
                pygame.draw.rect(win, light, top_beam.inflate(-10, -8), border_radius=5)
                pygame.draw.rect(win, light, mid_beam.inflate(-10, -8), border_radius=5)

                # simple "joinery" dots
                for px, py in [
                    (left_post.centerx, top_beam.centery),
                    (right_post.centerx, top_beam.centery),
                    (left_post.centerx, mid_beam.centery),
                    (right_post.centerx, mid_beam.centery),
                ]:
                    pygame.draw.circle(win, (80, 45, 20), (int(px), int(py)), 4)
                    pygame.draw.circle(win, (200, 170, 120), (int(px) - 1, int(py) - 1), 2)

                # label
                t = resources['small_font'].render("木架", True, (40, 20, 10))
                win.blit(t, (base.x + 12, base.y + 8))
                return

            # default obstacles
            pygame.draw.rect(win, color_map.get(self.type, GRAY), (self.x, self.y, self.width, self.height), border_radius=3)
                
    def get_hitbox(self):
        hitbox_width, hitbox_height = self.width * 0.8, self.height * 0.8
        return pygame.Rect(
            self.x + (self.width - hitbox_width) / 2, 
            self.y + (self.height - hitbox_height) / 2,
            hitbox_width, 
            hitbox_height
        )

class Item:
    def __init__(self, resources, item_type=None):
        self.x = WIDTH
        self.y = random.randint(50, HEIGHT - GROUND_HEIGHT - 50)
        self.speed = speed + 2
        self.collected = False
        
        # Random item type (only health and shield) (随机道具类型)
        if item_type is None:
            self.type = random.choice([ItemType.HEALTH, ItemType.SHIELD])
        else:
            self.type = item_type
            
        # Load item image (加载道具图片)
        self.image = None
        if self.type == ItemType.HEALTH:
            self.image = resources.get('health_item_img')
            self.width, self.height = (40, 40) if self.image else (30, 30)
        else:  # SHIELD
            self.image = resources.get('shield_item_img')
            self.width, self.height = (40, 40) if self.image else (30, 30)
            
    def update(self):
        if game_state == GameState.PLAYING and not self.collected: 
            self.x -= self.speed
            
    def draw(self, win, resources):
        if not self.collected:
            # Use image if available (优先使用图片)
            if self.image:
                win.blit(self.image, (self.x, self.y))
                
                # Add glow effect (添加发光效果)
                glow_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
                color = (0, 255, 0, 80) if self.type == ItemType.HEALTH else (0, 0, 255, 80)
                pygame.draw.rect(glow_surface, color, (0, 0, self.width + 10, self.height + 10), border_radius=5)
                win.blit(glow_surface, (self.x - 5, self.y - 5))
            else:
                # Draw default shape with text (绘制默认形状和文字)
                if self.type == ItemType.HEALTH:
                    pygame.draw.rect(win, GREEN, (self.x, self.y, self.width, self.height), border_radius=5)
                    heart_text = resources['small_font'].render("+", True, WHITE)
                else:  # SHIELD
                    pygame.draw.rect(win, BLUE, (self.x, self.y, self.width, self.height), border_radius=5)
                    heart_text = resources['small_font'].render("盾", True, WHITE)
                win.blit(heart_text, (self.x + self.width//2 - heart_text.get_width()//2, self.y + self.height//2 - heart_text.get_height()//2))
                    
    def get_hitbox(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Collectible:
    """Cultural collectibles:瓦当/斗拱/木构件 (文化收集物)"""
    def __init__(self, resources, collectible_type: CollectibleType):
        self.type = collectible_type
        self.x = WIDTH
        self.y = random.randint(80, HEIGHT - GROUND_HEIGHT - 80)
        self.speed = speed + 1.5
        self.collected = False
        icon = resources.get("collectible_imgs", {}).get(self.type) if resources else None
        if icon:
            self.width = int(icon.get_width())
            self.height = int(icon.get_height())
        else:
            self.width = 34
            self.height = 34

    def update(self):
        if game_state == GameState.PLAYING and not self.collected:
            self.x -= self.speed

    def draw(self, win, resources):
        if self.collected:
            return
        icon = resources.get("collectible_imgs", {}).get(self.type)
        if icon:
            # draw icon + subtle glow
            w, h = icon.get_width(), icon.get_height()
            glow = pygame.Surface((w + 18, h + 18), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 255, 255, 70), (0, 0, w + 18, h + 18))
            win.blit(glow, (self.x - 9, self.y - 9))
            # keep sprite aligned with its logical size
            win.blit(icon, (self.x, self.y))
            return

        color_map = {
            CollectibleType.WADANG: (220, 180, 80),
            CollectibleType.DOUGONG: (210, 120, 80),
            CollectibleType.WOOD: (150, 90, 50),
        }
        label_map = {
            CollectibleType.WADANG: "瓦",
            CollectibleType.DOUGONG: "斗",
            CollectibleType.WOOD: "木",
        }

        # glow
        glow = pygame.Surface((self.width + 16, self.height + 16), pygame.SRCALPHA)
        c = color_map[self.type]
        pygame.draw.circle(glow, (c[0], c[1], c[2], 80), (self.width // 2 + 8, self.height // 2 + 8), self.width // 2 + 8)
        win.blit(glow, (self.x - 8, self.y - 8))

        pygame.draw.circle(win, color_map[self.type], (int(self.x + self.width/2), int(self.y + self.height/2)), self.width // 2)
        pygame.draw.circle(win, (255, 255, 255), (int(self.x + self.width/2), int(self.y + self.height/2)), self.width // 2, 2)

        txt = resources['small_font'].render(label_map[self.type], True, (10, 10, 10))
        win.blit(txt, (self.x + self.width//2 - txt.get_width()//2, self.y + self.height//2 - txt.get_height()//2))

    def get_center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)

class FlyingObstacle:
    def __init__(self, resources, obstacle_type=None):
        self.type = obstacle_type if obstacle_type else random.choice(list(FLYING_OBSTACLE_PROPERTIES.keys()))
        props = FLYING_OBSTACLE_PROPERTIES[self.type]
        self.width, self.height = props["width"], props["height"]
        self.image = resources.get('flying_obstacle_imgs', {}).get(self.type)
        
        self.color = random.choice(props["colors"]) if "colors" in props else (255, 0, 0)
        # 修改速度方向：从右边来的飞行物应该向左移动
        self.speed_x = -random.uniform(props["min_speed"], props["max_speed"]) if "min_speed" in props else -10
        self.speed_y = 0
        
        # 所有飞行障碍物从右边开始（x = WIDTH）
        if self.type == "balloon":
            self.x = random.uniform(props["x_range"][0], props["x_range"][1])
            self.y = HEIGHT
            self.speed_y = random.uniform(props["min_speed"], props["max_speed"])
            self.speed_x = random.uniform(-1, 1)
        elif self.type == "daodan":
            self.x = WIDTH  # 从右边开始
            self.y = random.uniform(props["y_range"][0], props["y_range"][1])
        else:
            # 默认设置，确保所有障碍物都有x和y属性
            self.x = WIDTH
            self.y = HEIGHT // 2
            
    def update(self, player_y=0):
        if game_state == GameState.PLAYING:
            self.x += self.speed_x
            self.y += self.speed_y
            
            # 移除屏幕左侧的飞行物（从右边来，向左移动，超出左侧边界时移除）
            if self.x + self.width < 0:
                return True
            return False
                
    def draw(self, win):
        if self.image:
            win.blit(self.image, (self.x, self.y))
        else:
            if self.type == "balloon": 
                pygame.draw.ellipse(win, self.color, (self.x, self.y, self.width, self.height))
            elif self.type == "daodan": 
                pygame.draw.rect(win, self.color, (self.x, self.y + self.height//4, self.width, self.height//2))
                
    def get_hitbox(self):
        if self.type == "bird": 
            return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)
        elif self.type == "flying_saucer": 
            return pygame.Rect(self.x + 5, self.y, self.width - 10, self.height)
        elif self.type == "daodan": 
            return pygame.Rect(self.x, self.y, self.width + 10, self.height)
        elif self.type == "balloon": 
            return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)
        elif self.type == "daodan": 
            return pygame.Rect(self.x, self.y, self.width + 15, self.height)
            
    def is_off_screen(self):
        if self.speed_x > 0: 
            return self.x > WIDTH
        else: 
            return self.x + self.width < 0


class ArchitecturePlatform:
    """建筑机关平台：飞檐借力 / 桥梁晃动与承重 / 榫卯闪烁（时间解谜）"""

    def __init__(self, kind: str, x: float, base_y: float, width: int, height: int):
        self.kind = kind  # "eave" | "bridge" | "mortise"
        self.x = float(x)
        self.base_y = float(base_y)
        self.width = width
        self.height = height
        self.broken = False
        self.stand_ms = 0.0
        self.sway_amp = 34 if kind == "bridge" else 0
        self._bridge_scaled = None
        self._bridge_scale_key: Optional[tuple[int, int]] = None
        self._mortise_scaled = None
        self._mortise_scale_key: Optional[tuple[int, int]] = None
        self._eave_scaled = None
        self._eave_scale_key: Optional[tuple[int, int]] = None

    def _sway_y(self) -> float:
        if self.broken or self.kind != "bridge":
            return 0.0
        t = pygame.time.get_ticks()
        return math.sin(t * 0.0022) * self.sway_amp

    def current_y(self) -> float:
        if self.broken:
            return self.base_y + 800.0
        return self.base_y + self._sway_y()

    def is_solid(self) -> bool:
        if self.broken:
            return False
        if self.kind == "mortise":
            # 榫卯构件：间歇可踏——需在“实”相位起跳通过（每相位 2 秒）
            return (pygame.time.get_ticks() // 2000) % 2 == 0
        return True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.current_y()), self.width, self.height)

    def update(self):
        if game_state == GameState.PLAYING:
            self.x -= speed

    def register_standing(self, dt: float, standing: bool):
        if self.kind != "bridge" or self.broken:
            return
        if standing:
            self.stand_ms += dt
            if self.stand_ms > 2200:
                self.broken = True
                global hud_toast
                hud_toast["text"] = "桥梁承重超限！尽快起跳离开"
                hud_toast["until_ms"] = pygame.time.get_ticks() + 1800
        else:
            self.stand_ms = max(0.0, self.stand_ms - dt * 0.35)

    def draw(self, win, resources):
        r = self.get_rect()
        if self.kind == "eave":
            esrc = resources.get("eave_platform_src")
            if esrc is not None:
                key = (max(1, r.w), max(1, r.h))
                if self._eave_scale_key != key:
                    self._eave_scaled = pygame.transform.smoothscale(esrc, key)
                    self._eave_scale_key = key
                win.blit(self._eave_scaled, r.topleft)
            else:
                pygame.draw.rect(win, (210, 185, 155), r, border_radius=6)
                pygame.draw.rect(win, (120, 90, 70), r, 2, border_radius=6)
                tip = resources["small_font"].render("飞檐", True, (60, 40, 30))
                win.blit(tip, (r.x + 8, r.y + 2))
        elif self.kind == "bridge":
            src = resources.get("bridge_platform_src")
            if src is not None and not self.broken:
                key = (max(1, r.w), max(1, r.h))
                if self._bridge_scale_key != key:
                    self._bridge_scaled = pygame.transform.smoothscale(src, key)
                    self._bridge_scale_key = key
                win.blit(self._bridge_scaled, r.topleft)
            else:
                col = (160, 145, 130) if not self.broken else (90, 90, 90)
                pygame.draw.rect(win, col, r, border_radius=8)
                pygame.draw.rect(win, (70, 85, 100), r, 2, border_radius=8)
                tip = resources["small_font"].render("桥", True, (40, 50, 60))
                win.blit(tip, (r.centerx - tip.get_width() // 2, r.y + 3))
        else:
            ghost = not self.is_solid()
            msrc = resources.get("mortise_platform_src")
            if msrc is not None:
                key = (max(1, r.w), max(1, r.h))
                if self._mortise_scale_key != key:
                    self._mortise_scaled = pygame.transform.smoothscale(msrc, key)
                    self._mortise_scale_key = key
                win.blit(self._mortise_scaled, r.topleft)
                if ghost:
                    ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                    ov.fill((200, 220, 245, 115))
                    win.blit(ov, r.topleft)
                    pygame.draw.rect(win, (130, 150, 180), r, 2, border_radius=8)
                else:
                    pygame.draw.rect(win, (90, 120, 160), r, 2, border_radius=8)
                # identify skill: stronger hint + countdown
                has_identify = "identify" in run_equipped_skills
                col = (170, 52, 50) if ghost else (26, 120, 64)
                label_txt = "榫卯(虚)" if ghost else "榫卯(实)"
                if has_identify:
                    phase_ms = 2000
                    rem = phase_ms - (pygame.time.get_ticks() % phase_ms)
                    sec = max(0, int(math.ceil(rem / 1000.0)))
                    label_txt = f"{label_txt} · {sec}s"
                lab = resources["small_font"].render(label_txt, False, col)
                win.blit(lab, (r.x + 8, r.y + 2))
            else:
                if ghost:
                    s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                    s.fill((180, 200, 220, 90))
                    win.blit(s, r.topleft)
                    pygame.draw.rect(win, (130, 150, 180), r, 2, border_radius=8)
                else:
                    pygame.draw.rect(win, (200, 220, 245), r, border_radius=8)
                    pygame.draw.rect(win, (90, 120, 160), r, 2, border_radius=8)
                tip = resources["small_font"].render("榫卯" + ("(虚)" if ghost else "(实)"), True, (35, 45, 65))
                win.blit(tip, (r.x + 8, r.y + 2))


class PatrolGuard:
    """官府巡卫：左右巡逻的障碍（贴近地面，类似潜行遭遇）"""

    def __init__(self):
        self.width = 50
        self.height = 72
        self.x = float(WIDTH)
        self.base_y = float(HEIGHT - self.height - GROUND_HEIGHT)
        self.phase = random.random() * math.tau
        self.patrol_radius = 105.0

    def patrol_offset(self) -> float:
        return math.sin(self.phase) * self.patrol_radius

    def update(self, dt: float):
        if game_state != GameState.PLAYING:
            return
        self.x -= speed
        self.phase += dt * 0.0028

    def draw(self, win, resources):
        px = int(self.x + self.patrol_offset())
        rect = pygame.Rect(px, int(self.base_y), self.width, self.height)
        img = resources.get("patrol_guard_img")
        if img is not None:
            win.blit(img, (rect.x, rect.y))
        else:
            pygame.draw.rect(win, (85, 95, 120), rect, border_radius=10)
            pygame.draw.rect(win, (50, 55, 70), rect, 2, border_radius=10)
            t = resources["small_font"].render("卫", True, (230, 230, 235))
            win.blit(t, (rect.centerx - t.get_width() // 2, rect.y + 10))

    def get_hitbox(self) -> pygame.Rect:
        px = int(self.x + self.patrol_offset())
        return pygame.Rect(px + 8, int(self.base_y) + 12, self.width - 16, self.height - 20)


def _spawn_architecture_for_theme(theme: str, resources):
    """按当前建筑主题生成机关（与跑酷同向卷轴）"""
    if theme == "bridge":
        architecture_platforms.append(
            ArchitecturePlatform(
                "bridge",
                float(WIDTH),
                float(HEIGHT - 230),
                BRIDGE_PLATFORM_WIDTH,
                BRIDGE_PLATFORM_HEIGHT,
            )
        )
    elif theme == "palace":
        y = random.choice([HEIGHT - 300, HEIGHT - 340, HEIGHT - 380])
        architecture_platforms.append(
            ArchitecturePlatform(
                "eave", float(WIDTH), float(y), EAVE_PLATFORM_WIDTH, EAVE_PLATFORM_HEIGHT
            )
        )
        # palace: more multi-layer choices
        if random.random() < 0.62:
            y2 = random.choice([HEIGHT - 270, HEIGHT - 410])
            architecture_platforms.append(
                ArchitecturePlatform(
                    "eave",
                    float(WIDTH + EAVE_SECOND_X_OFFSET),
                    float(y2),
                    EAVE_PLATFORM_WIDTH_ALT,
                    EAVE_PLATFORM_HEIGHT,
                )
            )
    elif theme == "siheyuan":
        architecture_platforms.append(
            ArchitecturePlatform("mortise", float(WIDTH), float(HEIGHT - 255), 210, 22)
        )
        # siheyuan: more mortise sequences
        if random.random() < 0.55:
            architecture_platforms.append(
                ArchitecturePlatform("mortise", float(WIDTH + 280), float(HEIGHT - 300), 180, 22)
            )
    elif theme == "yamen":
        # yamen: guards appear more often; sometimes double patrol
        patrol_guards.append(PatrolGuard())
        if random.random() < 0.35:
            patrol_guards.append(PatrolGuard())


# -----------------------------
# Config File Functions (配置文件函数)
# -----------------------------
def load_config():
    if not os.path.exists(CONFIG_FILE): 
        return {
            "high_score": 0,
            "score": 0,
            "purchased_items": [],
            "cultural_counts": {"wadang": 0, "dougong": 0, "wood": 0},
            "codex_unlocked": [],
            "jump_level": 1,  # 1/2/3/4 段跳
            "max_hp": 3,      # 生存模式生命上限
            "music_volume": 0.7,  # 音乐音量 0.0-1.0
            "menu_music_index": -1,  # -1 = 默认播 DEFAULT_HOME_MUSIC_BASENAME；≥0 为列表下标
            "home_tutorial_enabled": True,  # 每次打开默认显示新手引导（可在设置里关）
            "home_tutorial_seen": False,  # legacy: 旧字段（保留兼容，不再作为显示条件）
            "fullscreen": False,  # 全屏
            "building_scene": "siheyuan",  # 主页可选：四合院/官府/皇宫/桥梁
            "decrypt_wrong": [],
            "decrypt_best_score": 0,
            # skills meta progression (技能成长)
            "unlock_skills": {},  # {skill_id: level}
            "loadout": {"enabled": True, "slots": []},  # 允许不携带
            "skill_shards": INITIAL_SKILL_SHARDS,
            # daily / long-term
            "daily": {"seed": 0, "best": 0, "last_date": ""},
        }
    def _load_json(path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    try:
        data = _load_json(CONFIG_FILE)
        # migrate old configs safely (兼容旧存档)
        data.setdefault("purchased_items", [])
        data.setdefault("high_score", 0)
        data.setdefault("score", 0)
        cc = data.get("cultural_counts")
        if not isinstance(cc, dict):
            cc = {}
        cc.setdefault("wadang", 0)
        cc.setdefault("dougong", 0)
        cc.setdefault("wood", 0)
        data["cultural_counts"] = cc
        if not isinstance(data.get("codex_unlocked"), list):
            data["codex_unlocked"] = []
        if not isinstance(data.get("decrypt_wrong"), list):
            data["decrypt_wrong"] = []
        bs = data.get("decrypt_best_score")
        try:
            bs = int(bs)
        except Exception:
            bs = 0
        if bs < 0:
            bs = 0
        data["decrypt_best_score"] = bs

        # Jump level migration:
        # - prefer explicit jump_level
        # - fallback to purchased_items "double_jump" if present
        jl = data.get("jump_level")
        if not isinstance(jl, int) or jl not in (1, 2, 3, 4):
            jl = 2 if "double_jump" in data.get("purchased_items", []) else 1
        data["jump_level"] = jl

        mh = data.get("max_hp")
        if not isinstance(mh, int) or mh < 1 or mh > 6:
            mh = 3
        data["max_hp"] = mh

        mv = data.get("music_volume")
        try:
            mv = float(mv)
        except Exception:
            mv = 0.7
        if mv < 0.0:
            mv = 0.0
        if mv > 1.0:
            mv = 1.0
        data["music_volume"] = mv

        if "menu_music_index" not in data:
            mmi = -1
        else:
            mmi = data.get("menu_music_index")
        try:
            mmi = int(mmi)
        except Exception:
            mmi = -1
        # -1：开局按 DEFAULT_HOME_MUSIC_BASENAME 解析；其余为 home_music_tracks 下标（越界在 load_resources 收紧）
        if mmi < -1:
            mmi = -1
        data["menu_music_index"] = mmi

        hts = data.get("home_tutorial_seen", False)
        data["home_tutorial_seen"] = bool(hts) if isinstance(hts, (bool, int)) else False

        hte = data.get("home_tutorial_enabled", True)
        data["home_tutorial_enabled"] = bool(hte) if isinstance(hte, (bool, int)) else True

        fs = data.get("fullscreen")
        data["fullscreen"] = bool(fs) if isinstance(fs, (bool, int)) else False

        data.setdefault("building_scene", "siheyuan")
        _bs = data.get("building_scene")
        if not isinstance(_bs, str) or _bs not in BUILDING_THEMES:
            data["building_scene"] = "siheyuan"

        # ---- skills migration ----
        us = data.get("unlock_skills")
        if not isinstance(us, dict):
            us = {}
        # sanitize keys/levels; keep only known skill ids
        clean_us = {}
        for k, v in us.items():
            if not isinstance(k, str) or k not in SKILLS:
                continue
            try:
                lv = int(v)
            except Exception:
                lv = 0
            if lv < 0:
                lv = 0
            mx = int(SKILLS.get(k, {}).get("max_level", 1) or 1)
            if lv > mx:
                lv = mx
            if lv > 0:
                clean_us[k] = lv
        data["unlock_skills"] = clean_us

        ld = data.get("loadout")
        if not isinstance(ld, dict):
            ld = {}
        enabled = ld.get("enabled")
        enabled = bool(enabled) if isinstance(enabled, (bool, int)) else True
        slots = ld.get("slots")
        if not isinstance(slots, list):
            slots = []
        clean_slots = []
        for s in slots:
            if isinstance(s, str) and s in SKILLS:
                clean_slots.append(s)
        # cap slot count (避免面板撑爆/存档膨胀)
        clean_slots = clean_slots[:6]
        data["loadout"] = {"enabled": enabled, "slots": clean_slots}

        shards = data.get("skill_shards")
        try:
            shards = int(shards)
        except Exception:
            shards = 0
        if shards < 0:
            shards = 0
        data["skill_shards"] = shards

        daily = data.get("daily")
        if not isinstance(daily, dict):
            daily = {}
        daily.setdefault("seed", 0)
        daily.setdefault("best", 0)
        daily.setdefault("last_date", "")
        try:
            daily["seed"] = int(daily.get("seed", 0))
        except Exception:
            daily["seed"] = 0
        try:
            daily["best"] = int(daily.get("best", 0))
        except Exception:
            daily["best"] = 0
        if daily["best"] < 0:
            daily["best"] = 0
        if not isinstance(daily.get("last_date"), str):
            daily["last_date"] = ""
        data["daily"] = daily
        return data
    except Exception as e:
        print(f"Error loading config file: {e}")
        # Try backup if main config is corrupted (e.g. interrupted write)
        try:
            if os.path.exists(CONFIG_BAK_FILE):
                data = _load_json(CONFIG_BAK_FILE)
                # best-effort: restore by re-saving through safe writer
                try:
                    save_config(data)
                except Exception:
                    pass
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {
            "high_score": 0,
            "score": 0,
            "purchased_items": [],
            "cultural_counts": {"wadang": 0, "dougong": 0, "wood": 0},
            "codex_unlocked": [],
            "jump_level": 1,
            "max_hp": 3,
            "music_volume": 0.7,
            "menu_music_index": -1,
            "home_tutorial_enabled": True,
            "home_tutorial_seen": False,
            "fullscreen": False,
            "building_scene": "siheyuan",
            "decrypt_wrong": [],
            "decrypt_best_score": 0,
            "unlock_skills": {},
            "loadout": {"enabled": True, "slots": []},
            "skill_shards": INITIAL_SKILL_SHARDS,
            "daily": {"seed": 0, "best": 0, "last_date": ""},
        }

def save_config(config):
    try:
        # Atomic-ish save: write temp then replace; also keep a .bak
        tmp_path = CONFIG_FILE + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        try:
            if os.path.exists(CONFIG_FILE):
                # keep last good version
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as rf:
                        prev = rf.read()
                    with open(CONFIG_BAK_FILE, 'w', encoding='utf-8') as bf:
                        bf.write(prev)
                except Exception:
                    pass
        except Exception:
            pass
        os.replace(tmp_path, CONFIG_FILE)
    except Exception as e:
        print(f"Error saving config file: {e}")

# -----------------------------
# Game Control Functions (游戏控制函数)
# -----------------------------
def reset_game(players, obstacles, items, flying_obstacles, resources):
    global speed, score, score_float, game_state, current_level, level_up_timer, flying_spawn_timer, bg_scroll_x
    global survival_mode_duration, survival_next_boss_wave
    global building_theme, building_theme_ms, architecture_spawn_timer
    global architecture_platforms, patrol_guards
    global run_equipped_skills, run_skill_levels, run_skill_runtime, run_event
    global run_start_ms, run_goals

    config = load_config()
    # daily challenge: deterministic RNG for this run
    if daily_run and daily_seed_used:
        try:
            random.seed(int(daily_seed_used))
        except Exception:
            pass
    
    if current_mode == SURVIVAL_MODE_ID: # Survival mode (生存模式)
        initial_speed = INITIAL_SPEED * 1.2
        score = 0
        score_float = 0.0
        survival_mode_duration = 0
        survival_next_boss_wave = 30
        current_level = 1
    else: # Traditional modes (传统模式)
        initial_speed = INITIAL_SPEED
        if "speed_boost" in config.get("purchased_items", []): 
            initial_speed *= 1.2
        score, current_level = 0, 1
        score_float = 0.0

    speed = initial_speed
    level_up_timer, flying_spawn_timer = 0, 0
    bg_scroll_x = 0
    _scene = config.get("building_scene", "siheyuan")
    if not isinstance(_scene, str) or _scene not in BUILDING_THEMES:
        _scene = BUILDING_THEMES[0]
    building_theme = _scene
    building_theme_ms = 0
    architecture_spawn_timer = 0.0
    architecture_platforms.clear()
    patrol_guards.clear()
    game_state = GameState.PLAYING
    obstacles.clear()
    items.clear()
    flying_obstacles.clear()
    players.clear()
    
    start_x = 50
    is_survival = current_mode == SURVIVAL_MODE_ID
    
    if not is_survival: # Traditional modes (传统模式)
        colors = [BLACK, BLUE, PURPLE]
        jump_buttons = [1, 3, None]
        jump_keys = [None, None, pygame.K_SPACE]
        for i in range(current_mode):
            player = Dinosaur(resources, start_x, colors[i], jump_button=jump_buttons[i], jump_key=jump_keys[i], is_survival_mode=False)
            player.max_jumps_total = int(config.get("jump_level", 1))
            players.append(player)
            start_x += 120
    else: # Survival mode (生存模式)
        max_hp = int(config.get("max_hp", 3))
        player = Dinosaur(resources, start_x, RED, jump_button=1, jump_key=pygame.K_SPACE, is_survival_mode=True)
        player.max_jumps_total = int(config.get("jump_level", 2))
        player.max_health = max_hp
        player.health = max_hp
        players.append(player)

    # ---- loadout -> run skill state ----
    ld = config.get("loadout")
    if not isinstance(ld, dict):
        ld = {"enabled": True, "slots": []}
    enabled = bool(ld.get("enabled", True))
    slots = ld.get("slots")
    if not isinstance(slots, list):
        slots = []
    us = config.get("unlock_skills")
    if not isinstance(us, dict):
        us = {}
    run_equipped_skills = [s for s in slots if isinstance(s, str) and s in SKILLS] if enabled else []
    run_skill_levels = {}
    for sid in run_equipped_skills:
        try:
            lv = int(us.get(sid, 1))
        except Exception:
            lv = 1
        mx = int(SKILLS.get(sid, {}).get("max_level", 1) or 1)
        run_skill_levels[sid] = max(1, min(mx, lv))

    now_ms = pygame.time.get_ticks()
    run_skill_runtime = {
        "dash_next_ready_ms": now_ms + 2000,
        "dash_charges": 0,
        "invul_until_ms": 0,
    }
    run_event = {"type": "", "until_ms": 0, "next_ms": now_ms + 18000, "boss_next_ms": now_ms + 32000}

    # ---- run goals ----
    run_start_ms = now_ms
    goals = []
    # time goal
    t_goal = random.choice([25, 35, 45])
    goals.append({"id": "survive", "name": f"无伤坚持 {t_goal}s", "target": t_goal, "progress": 0, "done": False, "reward_shards": 2, "reward_score": 120})
    # theme goal
    if building_theme == "bridge":
        goals.append({"id": "bridge_safe", "name": "桥梁上不触发坍塌通过 1 次", "target": 1, "progress": 0, "done": False, "reward_shards": 2, "reward_score": 160})
    elif building_theme == "siheyuan":
        goals.append({"id": "mortise_pass", "name": "通过榫卯(实)机关 2 次", "target": 2, "progress": 0, "done": False, "reward_shards": 2, "reward_score": 160})
    elif building_theme == "yamen":
        goals.append({"id": "evade_guard", "name": "躲避巡卫遭遇 2 次（不被碰到）", "target": 2, "progress": 0, "done": False, "reward_shards": 2, "reward_score": 160})
    else:
        goals.append({"id": "collect_parts", "name": "收集任意构件 3 个", "target": 3, "progress": 0, "done": False, "reward_shards": 2, "reward_score": 160})
    run_goals = goals[:2]

    # passive: double jump plus
    dj_lv = int(run_skill_levels.get("double_jump_plus", 0))
    if dj_lv > 0:
        extra = 1 if dj_lv >= 1 else 0
        if dj_lv >= 2:
            extra = 2
        for p in players:
            try:
                p.max_jumps_total = max(int(p.max_jumps_total), int(config.get("jump_level", 1)) + extra)
            except Exception:
                pass

    # Play game music (播放游戏音乐)
    pygame.mixer.music.stop()
    pool = resources.get("game_music_pool", [])
    if isinstance(pool, list) and pool:
        try:
            pick = random.choice(pool)
            pygame.mixer.music.load(pick)
            pygame.mixer.music.set_volume(float(load_config().get("music_volume", 0.7)))
            pygame.mixer.music.play(loops=-1)
        except Exception as e:
            print(f"Error playing game music: {e}")
            
    return players, obstacles, items, flying_obstacles

def _sync_cultural_from_config():
    """Load persistent cultural progression into runtime state."""
    global cultural_counts, codex_unlocked
    config = load_config()
    cc = config.get("cultural_counts", {})
    cultural_counts[CollectibleType.WADANG] = int(cc.get("wadang", 0))
    cultural_counts[CollectibleType.DOUGONG] = int(cc.get("dougong", 0))
    cultural_counts[CollectibleType.WOOD] = int(cc.get("wood", 0))
    codex_unlocked = set(config.get("codex_unlocked", []))

def _persist_cultural_to_config():
    config = load_config()
    config["cultural_counts"] = {
        "wadang": int(cultural_counts[CollectibleType.WADANG]),
        "dougong": int(cultural_counts[CollectibleType.DOUGONG]),
        "wood": int(cultural_counts[CollectibleType.WOOD]),
    }
    config["codex_unlocked"] = sorted(list(codex_unlocked))
    save_config(config)

def _maybe_unlock_codex(toast_now_ms: int):
    """Unlock codex entries based on rules; show toast if newly unlocked."""
    global hud_toast
    newly = []
    for entry in CODEX_ENTRIES:
        if entry["id"] in codex_unlocked:
            continue
        rule = entry["unlock"]
        if rule["type"] == "collect":
            t = rule["collectible"]
            if cultural_counts[t] >= rule["count"]:
                codex_unlocked.add(entry["id"])
                newly.append(entry["name"])
    if newly:
        hud_toast["text"] = f"图鉴解锁：{ '、'.join(newly) }  (按 I 查看)"
        hud_toast["until_ms"] = toast_now_ms + 2200
        _persist_cultural_to_config()

# 游戏内 HUD：得分/主题/文化行纵向错开，避免与「建筑主题」「图鉴」提示挤在一起
HUD_THEME_Y_TRAD = 52
HUD_CULTURAL_Y_TRAD = 90
HUD_THEME_Y_SURVIVAL = 118
HUD_CULTURAL_Y_SURVIVAL = 156
HUD_TEXT_DARK = (12, 16, 28)


def draw_cultural_hud(win, resources):
    # compact cultural counters (文化收集显示)
    wad = cultural_counts[CollectibleType.WADANG]
    dou = cultural_counts[CollectibleType.DOUGONG]
    wood = cultural_counts[CollectibleType.WOOD]
    text_surface = resources['small_font'].render(
        f"瓦当:{wad}  斗拱:{dou}  木构件:{wood}   (I 图鉴)", True, HUD_TEXT_DARK
    )

    if current_mode == SURVIVAL_MODE_ID:
        x, y = 10, HUD_CULTURAL_Y_SURVIVAL
    else:
        x, y = 10, HUD_CULTURAL_Y_TRAD

    pad_x, pad_y = 10, 6
    bg = pygame.Surface((text_surface.get_width() + pad_x * 2, text_surface.get_height() + pad_y * 2), pygame.SRCALPHA)
    bg.fill((255, 255, 255, 210))
    win.blit(bg, (x, y))
    pygame.draw.rect(win, (70, 85, 115), (x, y, bg.get_width(), bg.get_height()), 1, border_radius=6)
    win.blit(text_surface, (x + pad_x, y + pad_y))


def draw_building_theme_hud(win, resources):
    line = f"建筑主题：{BUILDING_THEME_LABELS.get(building_theme, building_theme)}"
    theme_hud = resources["small_font"].render(line, True, HUD_TEXT_DARK)
    ty = HUD_THEME_Y_SURVIVAL if current_mode == SURVIVAL_MODE_ID else HUD_THEME_Y_TRAD
    win.blit(theme_hud, (12, ty))


def draw_skill_hud(win, resources):
    """Small HUD for equipped skills and key runtime states."""
    if game_state != GameState.PLAYING:
        return
    if not run_equipped_skills:
        return
    # Place skill line at top-right to avoid overlapping score at top-left.
    # Survival mode draws time at top-right (y=10) using `font`, so move skills below it.
    if current_mode == SURVIVAL_MODE_ID:
        try:
            y = 10 + int(resources["font"].get_height()) + 6
        except Exception:
            y = 40
    else:
        y = 12
    pad_r = 12

    head = resources["small_font"].render("技能：", True, HUD_TEXT_DARK)
    parts = []
    shown = 0
    for sid in run_equipped_skills[:4]:
        nm = SKILLS.get(sid, {}).get("name", sid)
        lv = int(run_skill_levels.get(sid, 1))
        t = f"{nm}Lv{lv}"
        parts.append(resources["small_font"].render(t, True, (24, 34, 52)))
        shown += 1
    more = None
    if len(run_equipped_skills) > shown:
        more = resources["small_font"].render(f"+{len(run_equipped_skills) - shown}", True, (60, 72, 96))

    gap = 10
    total_w = head.get_width() + 6
    for s in parts:
        total_w += s.get_width() + gap
    if more is not None:
        total_w += more.get_width() + gap
    total_w = max(total_w - gap, head.get_width() + 6)

    x = max(12, WIDTH - pad_r - total_w)
    win.blit(head, (x, y))
    x2 = x + head.get_width() + 6
    for s in parts:
        win.blit(s, (x2, y))
        x2 += s.get_width() + gap
    if more is not None:
        win.blit(more, (x2, y))

    # dash / invul indicator
    inv = int(run_skill_runtime.get("invul_until_ms", 0))
    if inv and pygame.time.get_ticks() < inv:
        tag = resources["small_font"].render("护身中", True, (26, 120, 64))
        win.blit(tag, (x, y + 22))

    # run goals
    if run_goals:
        gy = max(58, y + 46)
        gtitle = resources["small_font"].render("目标：", True, HUD_TEXT_DARK)
        win.blit(gtitle, (12, gy))
        gy += 22
        for g in run_goals[:2]:
            done = bool(g.get("done"))
            prog = int(g.get("progress", 0))
            tgt = int(g.get("target", 1)) if int(g.get("target", 1)) > 0 else 1
            name = str(g.get("name", ""))
            col = (26, 120, 64) if done else (60, 72, 96)
            line = f"- {name}  {min(prog, tgt)}/{tgt}"
            s = resources["small_font"].render(line, False, col)
            win.blit(s, (12, gy))
            gy += 20

def draw_toast(win, resources, now_ms: int):
    if hud_toast["until_ms"] <= now_ms or not hud_toast["text"]:
        return
    t = resources['small_font'].render(hud_toast["text"], True, UI_TITLE_LIGHT)
    pad_x, pad_y = 14, 10
    br = 12
    box_w, box_h = t.get_width() + pad_x * 2, t.get_height() + pad_y * 2
    bx = WIDTH // 2 - box_w // 2
    # Avoid overlapping survival HUD lines (theme/cultural start at 118/156)
    by = 118 if current_mode != SURVIVAL_MODE_ID else 196
    _ui_panel_shadow(win, pygame.Rect(bx, by, box_w, box_h), radius=br)
    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(box, (28, 38, 58, 228), box.get_rect(), border_radius=br)
    pygame.draw.rect(box, (120, 145, 185, 200), box.get_rect(), 1, border_radius=br)
    win.blit(box, (bx, by))
    win.blit(t, (bx + pad_x, by + pad_y))

def draw_codex_detail(win, resources, entry, page_idx: int, mouse_pos=None):
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()
    _ui_modal_overlay(win, 195)

    hx = 56
    title = resources['large_font'].render(entry["name"], True, UI_TITLE_LIGHT)
    win.blit(title, (hx, 28))
    pygame.draw.line(win, UI_DIVIDER, (hx, 92), (WIDTH - hx, 92), 1)
    dynasty = resources["small_font"].render(entry.get("dynasty", ""), True, (200, 210, 228))
    win.blit(dynasty, (hx, 100))

    pages = entry.get("pages", [])
    total = max(1, len(pages))
    page_idx = max(0, min(page_idx, total - 1))

    panel = pygame.Rect(hx, 138, WIDTH - hx * 2, HEIGHT - 262)
    _ui_panel_shadow(win, panel, 16)
    _ui_draw_vertical_gradient_panel(win, panel, UI_CARD_NEUTRAL_TOP, UI_CARD_NEUTRAL_BOTTOM, radius=16)
    pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=16)

    def _wrap(text: str, font, max_w: int):
        lines = []
        for raw in text.split("\n"):
            if raw == "":
                lines.append("")
                continue
            cur = ""
            for ch in list(raw):
                trial = cur + ch
                if font.size(trial)[0] <= max_w:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = ch
            if cur:
                lines.append(cur)
        return lines

    content = pages[page_idx] if pages else ""
    lines = _wrap(content, resources["small_font"], panel.w - 48)
    y = panel.y + 22
    text_max_y = panel.bottom - 8
    for ln in lines:
        if y > text_max_y:
            break
        if ln == "":
            y += 12
            continue
        s = resources["small_font"].render(ln, True, UI_TEXT_PRIMARY)
        win.blit(s, (panel.x + 24, y))
        y += s.get_height() + 6

    pager = resources["small_font"].render(
        f"第 {page_idx + 1} / {total} 页　← → 翻页", True, UI_TITLE_LIGHT)
    win.blit(pager, (WIDTH - pager.get_width() - hx, panel.bottom + 14))

    btn_y = panel.bottom + 8
    prev_rect = pygame.Rect(hx, btn_y, 168, 52)
    next_rect = pygame.Rect(hx + 182, btn_y, 168, 52)
    back_rect = pygame.Rect(WIDTH - hx - 188, btn_y, 188, 52)
    draw_button(win, "上一页", prev_rect, resources["font"], False, prev_rect.collidepoint(mouse_pos))
    draw_button(win, "下一页", next_rect, resources["font"], False, next_rect.collidepoint(mouse_pos))
    draw_button(win, "返回列表", back_rect, resources["font"], False, back_rect.collidepoint(mouse_pos))

    return {"prev": prev_rect, "next": next_rect, "back": back_rect, "total": total}


def draw_codex_screen(win, resources, mouse_pos, scroll_y: int = 0):
    _ui_modal_overlay(win, 195)

    title = resources['large_font'].render("建筑图鉴", True, UI_TITLE_LIGHT)
    win.blit(title, (WIDTH // 2 - title.get_width() // 2, 32))
    sub = resources["small_font"].render(
        "收集构件解锁条目 · 鼠标滚轮 / ↑↓ 滑动 · 左键打开", True, (188, 198, 218))
    win.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 94))
    pygame.draw.line(win, UI_DIVIDER, (72, 124), (WIDTH - 72, 124), 1)

    def _wrap_text(text: str, font, max_width: int):
        words = list(text)  # Chinese-friendly: wrap by character
        lines = []
        cur = ""
        for ch in words:
            trial = cur + ch
            if font.size(trial)[0] <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        return lines

    card_w = WIDTH - 80
    card_h = CODEX_CARD_H
    x = (WIDTH - card_w) // 2
    y0 = CODEX_LIST_Y0
    gap = CODEX_CARD_GAP
    list_top_clip = CODEX_LIST_TOP_CLIP
    list_bottom_clip = CODEX_LIST_BOTTOM_CLIP
    cards = []  # (entry_id, rect, unlocked)
    content_bottom = y0
    for idx, entry in enumerate(CODEX_ENTRIES):
        y = y0 + idx * (card_h + gap) - int(scroll_y)
        rect = pygame.Rect(x, y, card_w, card_h)
        unlocked = entry["id"] in codex_unlocked
        cards.append((entry["id"], rect, unlocked))

        # update content bottom using non-scrolled coordinate
        content_bottom = max(content_bottom, y0 + (idx + 1) * (card_h + gap))

        if rect.bottom < list_top_clip or rect.top > list_bottom_clip:
            continue

        hovered = rect.collidepoint(mouse_pos)
        pressed = bool(hovered and pygame.mouse.get_pressed(num_buttons=3)[0])
        if unlocked:
            # animated card (hover lift + press)
            draw_rect = _ui_draw_card(
                win,
                rect,
                UI_CODEX_CARD_UNLOCKED,
                UI_CARD_NEUTRAL_BOTTOM,
                UI_PANEL_BORDER,
                hovered=hovered,
                pressed=pressed,
                radius=16,
                shadow_radius=16,
            )
        else:
            # locked: no shadow/motion, keep flat but still colored
            draw_rect = rect
            pygame.draw.rect(win, UI_CODEX_CARD_LOCKED, draw_rect, border_radius=16)
            pygame.draw.rect(win, (100, 108, 122), draw_rect, 2, border_radius=16)

        name = entry["name"] if unlocked else "？？？"
        dynasty = entry["dynasty"] if unlocked else "未解锁：收集对应构件"
        feature = entry.get("feature", "") if unlocked else "去跑酷收集瓦当/斗拱/木构件来解锁。"
        game_rule = entry.get("game_rule", "") if unlocked else ""

        pad = 24
        name_s = resources['font'].render(
            name, True, UI_TEXT_PRIMARY if unlocked else (52, 56, 68))
        win.blit(name_s, (draw_rect.x + pad, draw_rect.y + 16))
        d_s = resources['small_font'].render(dynasty, True, UI_TEXT_SECONDARY if unlocked else (70, 74, 86))
        win.blit(d_s, (draw_rect.x + pad, draw_rect.y + 56))

        desc_x = draw_rect.x + pad
        desc_y = draw_rect.y + 96
        desc_w = draw_rect.w - pad * 2
        desc_h = draw_rect.h - 112
        strip = pygame.Surface((desc_w, desc_h), pygame.SRCALPHA)
        strip.fill(UI_CODEX_STRIP_UNLOCKED if unlocked else (0, 0, 0, 50))
        win.blit(strip, (desc_x, desc_y))

        max_line_w = desc_w - 20
        lines = _wrap_text(feature, resources["small_font"], max_line_w)
        if game_rule:
            lines += ["", "【玩法】" + game_rule]
        yy = desc_y + 12
        for ln in lines[:8]:
            if ln == "":
                yy += 8
                continue
            s = resources["small_font"].render(
                ln, True, UI_TEXT_PRIMARY if unlocked else (60, 64, 76))
            win.blit(s, (desc_x + 12, yy))
            yy += s.get_height() + 5

    # scroll hint + clamp info
    hint = resources['small_font'].render(
        "滚轮 / ↑↓ 滑动 · I / Esc 返回", True, (210, 218, 232))
    win.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 46))
    # compute max scroll (content height minus viewport height)
    max_scroll = _codex_list_max_scroll()
    return cards, max_scroll

def check_level_up():
    global current_level, speed
    if current_level == 1 and score >= LEVEL_UP_SCORES[0]: 
        current_level = 2
        speed += 1.5
        return True
    elif current_level == 2 and score >= LEVEL_UP_SCORES[1]: 
        current_level = 3
        speed += 2
        return True
    elif current_level == 3 and score >= LEVEL_UP_SCORES[2]: 
        current_level = 4
        speed += 2.5
        return True
    elif current_level == 4 and score >= LEVEL_UP_SCORES[3]: 
        current_level = 5
        speed += 3
        return True
    return False

# -----------------------------
# UI Drawing Functions (界面绘制函数)
# -----------------------------
def _ui_modal_overlay(win, alpha: int = 200):
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    s.fill((UI_MODAL_RGBA[0], UI_MODAL_RGBA[1], UI_MODAL_RGBA[2], alpha))
    win.blit(s, (0, 0))


def _ui_panel_shadow(win, rect: pygame.Rect, radius: int = 18):
    sh = rect.copy()
    sh.x += 4
    sh.y += 5
    surf = pygame.Surface((sh.w, sh.h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0, 0, 0, 44), surf.get_rect(), border_radius=radius)
    win.blit(surf, sh.topleft)

def _ui_card_motion_offset(rect: pygame.Rect, hovered: bool, pressed: bool, hover_lift: int = 10, press_depth: int = 3):
    """Return moved rect for hover/press motion."""
    try:
        hover_lift = int(hover_lift)
    except Exception:
        hover_lift = 10
    try:
        press_depth = int(press_depth)
    except Exception:
        press_depth = 3
    if hovered:
        rect = rect.move(0, -max(0, hover_lift))
    if pressed:
        rect = rect.move(0, max(0, press_depth))
    return rect

def _ui_draw_card(win, rect: pygame.Rect, top_rgb: tuple, bottom_rgb: tuple, border_rgb: tuple, hovered: bool, pressed: bool, radius: int = 16, shadow_radius: int = 16):
    """Draw a motion card (shadow + gradient + border). Returns draw rect used."""
    draw_rect = _ui_card_motion_offset(rect, hovered, pressed, hover_lift=10, press_depth=3)
    _ui_panel_shadow(win, draw_rect, shadow_radius)
    _ui_draw_vertical_gradient_panel(win, draw_rect, top_rgb, bottom_rgb, radius=radius)
    pygame.draw.rect(win, border_rgb, draw_rect, 2, border_radius=radius)
    return draw_rect

def _ui_scroll_card_list_layout(viewport: pygame.Rect, item_count: int, item_h: int, gap: int, scroll_y: int):
    """Compute max_scroll + start_y for a vertical card list."""
    item_h = int(item_h)
    gap = int(gap)
    total_h = max(0, int(item_count) * (item_h + gap) - gap)
    max_scroll = max(0, int(total_h - viewport.h))
    try:
        scroll_y = int(scroll_y)
    except Exception:
        scroll_y = 0
    if scroll_y < 0:
        scroll_y = 0
    if scroll_y > max_scroll:
        scroll_y = max_scroll
    start_y = int(viewport.y - scroll_y)
    return max_scroll, scroll_y, start_y

def _ui_draw_scroll_card_list(
    win,
    viewport: pygame.Rect,
    items: list,
    scroll_y: int,
    item_h: int,
    gap: int,
    mouse_pos,
    draw_item_fn,
):
    """
    Draw a scrollable list of cards within viewport (with clipping).
    - draw_item_fn(win, item, rect, hovered, pressed) -> None
    Returns (visible_rects, max_scroll, scroll_y_clamped)
    """
    max_scroll, scroll_y, start_y = _ui_scroll_card_list_layout(viewport, len(items), item_h, gap, scroll_y)
    old_clip = win.get_clip()
    win.set_clip(viewport)
    visible = []
    for idx, it in enumerate(items):
        y = start_y + idx * (int(item_h) + int(gap))
        r = pygame.Rect(viewport.x, y, viewport.w, int(item_h))
        if r.bottom < viewport.y - 2:
            continue
        if r.top > viewport.bottom + 2:
            break
        hovered = r.collidepoint(mouse_pos)
        pressed = bool(hovered and pygame.mouse.get_pressed(num_buttons=3)[0])
        draw_item_fn(win, it, r, hovered, pressed)
        visible.append((it, r))
    win.set_clip(old_clip)
    return visible, max_scroll, scroll_y


def _ui_draw_vertical_gradient_panel(win, rect: pygame.Rect, top_rgb: tuple, bottom_rgb: tuple, radius: int = 18):
    """Draw a rounded-rect vertical gradient fill (用于界面底板渐变)."""
    r = rect.copy()
    if r.w <= 2 or r.h <= 2:
        return
    w, h = int(r.w), int(r.h)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    tr, tg, tb = int(top_rgb[0]), int(top_rgb[1]), int(top_rgb[2])
    br, bg, bb = int(bottom_rgb[0]), int(bottom_rgb[1]), int(bottom_rgb[2])
    # vertical gradient
    for y in range(h):
        t = 0.0 if h <= 1 else (y / float(h - 1))
        rr = int(tr + (br - tr) * t)
        gg = int(tg + (bg - tg) * t)
        bb2 = int(tb + (bb - tb) * t)
        pygame.draw.line(surf, (rr, gg, bb2, 255), (0, y), (w, y))

    # rounded mask
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    win.blit(surf, r.topleft)


def _ui_blit_centered_label(win, font, text: str, fg: tuple, y: int, outline_rgb=(236, 242, 252)):
    """浅色描边 + 主色字，在渐变天空上可读且不挡背景（四向描边，开销小）。"""
    main = font.render(text, True, fg)
    x = WIDTH // 2 - main.get_width() // 2
    ol = font.render(text, True, outline_rgb)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        win.blit(ol, (x + dx, y + dy))
    win.blit(main, (x, y))


def _ui_blit_label(win, font, text: str, fg: tuple, x: int, y: int, outline_rgb=(246, 248, 252)):
    """左上角定位的轻描边文字：更清晰、不发虚。"""
    # 小字号在半透明/渐变背景上开抗锯齿容易“发虚”，这里对小字关闭 AA 更清晰
    try:
        aa = bool(font.get_height() >= 34)
    except Exception:
        aa = True
    main = font.render(text, aa, fg)
    ol = font.render(text, aa, outline_rgb)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        win.blit(ol, (x + dx, y + dy))
    win.blit(main, (x, y))


def draw_button(win, text, rect, font, is_selected, is_hovered, style=None):
    """Draw a stylized button (绘制现代化按钮)"""
    style = style or {}
    # Button colors (按钮颜色)
    # Default theme: clean modern palette (清爽现代配色)
    # normal: light grey-blue, selected: soft blue
    default_bg = (245, 247, 252) if not is_selected else (205, 228, 255)
    bg_color = style.get("bg_color", default_bg)
    border_color = style.get("border_color", (92, 118, 150))
    # 默认文字用偏蓝灰，避免“纯黑很硬”
    text_color = style.get("text_color", (40, 52, 72))
    hover_lift = style.get("hover_lift", 20)
    shadow_alpha = style.get("shadow_alpha", 22)
    radius = style.get("radius", 12)
    bevel = style.get("bevel", 5)  # 凹凸厚度
    press_depth = style.get("press_depth", 2)  # 按下位移
    auto_press = style.get("auto_press", True)

    is_pressed = False
    if auto_press and is_hovered:
        try:
            is_pressed = bool(pygame.mouse.get_pressed(num_buttons=3)[0])
        except Exception:
            try:
                is_pressed = bool(pygame.mouse.get_pressed()[0])
            except Exception:
                is_pressed = False
    
    if is_hovered:
        bg_color = (min(bg_color[0] + hover_lift, 255), min(bg_color[1] + hover_lift, 255), min(bg_color[2] + hover_lift, 255))
        border_color = style.get("border_color_hover", (60, 90, 130))
    
    draw_rect = rect
    if is_pressed:
        draw_rect = rect.move(0, press_depth)
        shadow_alpha = max(0, shadow_alpha - 15)

    # Draw button shadow (绘制按钮阴影)
    shadow_rect = draw_rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    pygame.draw.rect(win, (0, 0, 0, shadow_alpha), shadow_rect, border_radius=radius)
    
    # Draw button background (绘制按钮背景)
    pygame.draw.rect(win, bg_color, draw_rect, border_radius=radius)

    # Emboss / bevel effect (凹凸感：高光边 + 阴影边 + 内阴影)
    # Light comes from top-left (默认光源)
    hi = (min(bg_color[0] + 25, 255), min(bg_color[1] + 25, 255), min(bg_color[2] + 25, 255))
    lo = (max(bg_color[0] - 35, 0), max(bg_color[1] - 35, 0), max(bg_color[2] - 35, 0))
    if is_selected:
        # selected slightly stronger contrast
        hi = (min(hi[0] + 10, 255), min(hi[1] + 10, 255), min(hi[2] + 10, 255))
        lo = (max(lo[0] - 10, 0), max(lo[1] - 10, 0), max(lo[2] - 10, 0))
    if is_pressed:
        # when pressed, invert highlight/shadow a bit for "pressed-in" feel
        hi, lo = lo, hi

    # highlight stroke (top-left)
    pygame.draw.rect(win, hi, draw_rect, 2, border_radius=radius)
    # inner highlight（极小按钮时跳过，避免 inflate 后出现非法尺寸）
    _inner = draw_rect.inflate(-bevel * 2, -bevel * 2)
    if _inner.width >= 6 and _inner.height >= 6:
        pygame.draw.rect(win, hi, _inner, 1, border_radius=max(2, radius - bevel))

    _inset = draw_rect.inflate(-2, -2)
    if _inset.width >= 8 and _inset.height >= 8:
        pygame.draw.rect(win, lo, _inset, 2, border_radius=max(2, radius - 1))

    # Outer border (统一边框色，压住光影边缘)
    pygame.draw.rect(win, border_color, draw_rect, 2, border_radius=radius)
    
    # Draw button text (绘制按钮文字)
    pad = style.get("pad", (14, 10))
    try:
        pad_x, pad_y = int(pad[0]), int(pad[1])
    except Exception:
        pad_x, pad_y = 14, 10
    allow_wrap = bool(style.get("wrap", False))
    line_gap = int(style.get("line_gap", 4))

    # 小字在复杂背景上 AA 会显糊：按钮文字也同策略
    try:
        aa_btn = bool(font.get_height() >= 30)
    except Exception:
        aa_btn = True

    if not allow_wrap:
        text_surface = font.render(text, aa_btn, text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        win.blit(text_surface, text_rect)
    else:
        # Chinese-friendly wrap by character（行数可由 style.max_wrap_lines 控制，默认 2）
        max_wrap_lines = int(style.get("max_wrap_lines", 2))
        if max_wrap_lines < 1:
            max_wrap_lines = 1
        if max_wrap_lines > 6:
            max_wrap_lines = 6
        max_w = max(10, draw_rect.w - pad_x * 2)
        chars = list(str(text))
        lines = []
        cur = ""
        for ch in chars:
            trial = cur + ch
            if font.size(trial)[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
                if len(lines) >= max_wrap_lines:
                    break
        if len(lines) < max_wrap_lines and cur:
            lines.append(cur)

        if lines:
            last = lines[-1]
            while font.size(last)[0] > max_w and len(last) > 1:
                last = last[:-1]
            consumed = sum(len(x) for x in lines)
            if len(lines) == max_wrap_lines and len(chars) > consumed:
                while font.size(last + "…")[0] > max_w and len(last) > 1:
                    last = last[:-1]
                last = last + "…"
            lines[-1] = last

        rendered = [font.render(ln, aa_btn, text_color) for ln in lines[:max_wrap_lines] if ln]
        total_h = sum(s.get_height() for s in rendered) + max(0, (len(rendered) - 1) * line_gap)
        y0 = draw_rect.centery - total_h // 2
        for s in rendered:
            x = draw_rect.x + pad_x
            win.blit(s, (x, y0))
            y0 += s.get_height() + line_gap

def draw_mode_select(win, resources, mouse_pos):
    global current_mode
    global home_tutorial_dismissed
    global home_tutorial_page
    global home_tutorial_hotspots, home_tutorial_hint
    draw_background(win, resources)
    config = load_config()
    jump_level = int(config.get("jump_level", 1))
    max_hp = int(config.get("max_hp", 3))
    music_volume = float(config.get("music_volume", 0.7))
    home_tutorial_enabled = bool(config.get("home_tutorial_enabled", True))

    # 主页不铺整块底板，保留背景云层/渐变可见；仅按钮自带绘制样式
    time = pygame.time.get_ticks() / 1000.0
    title_y_offset = math.sin(time * 1.6) * 6
    pulse = 0.9 + 0.1 * math.sin(time * 2.1)
    title_color = (
        int(min(255, 228 * pulse)),
        int(min(230, 168 * pulse)),
        int(min(200, 92 * pulse)),
    )

    title_text = resources['title_font'].render("古建行歌", True, title_color)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 82 + title_y_offset))

    glow_surface = pygame.Surface((title_text.get_width() + 20, title_text.get_height() + 20), pygame.SRCALPHA)
    for i in range(10):
        alpha = int(38 - i * 4)
        if alpha > 0:
            pygame.draw.rect(glow_surface, (*title_color[:3], alpha),
                           (10 - i//2, 10 - i//2, title_text.get_width() + i, title_text.get_height() + i),
                           border_radius=5)
    win.blit(glow_surface, (title_rect.x - 10, title_rect.y - 10))
    win.blit(title_text, title_rect)

    mode_names = {
        1: "单人（触碰即失败）",
        2: "双人（触碰即失败）",
        3: "三人（触碰即失败）",
        4: "生存（生命值/护盾）"
    }
    _ui_blit_centered_label(
        win, resources["small_font"],
        f"当前：{mode_names.get(current_mode, '未知模式')}",
        (34, 44, 58), 172,
    )
    _ui_blit_centered_label(
        win, resources["small_font"],
        f"跳跃 {jump_level} 段 · 生命 {max_hp} · 音量 {int(music_volume * 100)}%",
        (68, 78, 94), 198,
    )

    # Home UI palette（主页按钮配色：不再黑白灰）
    # 清爽蓝绿：统一蓝绿体系（低饱和、更耐看）
    STYLE_MODE = {
        1: {"bg_color": (234, 250, 255), "border_color": (64, 140, 176), "text_color": (34, 58, 78)},   # 清蓝
        2: {"bg_color": (232, 250, 244), "border_color": (56, 150, 118), "text_color": (30, 62, 50)},   # 清绿
        3: {"bg_color": (234, 248, 255), "border_color": (86, 156, 186), "text_color": (34, 58, 78)},   # 蓝青
        4: {"bg_color": (232, 255, 248), "border_color": (44, 156, 128), "text_color": (28, 60, 52)},   # 薄荷绿
    }
    STYLE_SCENE = {
        "siheyuan": {"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52)},
        "yamen": {"bg_color": (234, 250, 255), "border_color": (64, 140, 176), "text_color": (34, 58, 78)},
        "palace": {"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78)},
        "bridge": {"bg_color": (232, 255, 252), "border_color": (54, 156, 140), "text_color": (28, 60, 52)},
    }

    btn_width, btn_height = 200, 60
    h_spacing = 40
    v_spacing_mode = 40
    top_margin = 224
    
    # Calculate grid positions (计算网格位置)
    grid_width = btn_width * 2 + h_spacing
    grid_start_x = (WIDTH - grid_width) // 2
    
    ui_rects = []

    # 1 Player Button
    one_player_rect = pygame.Rect(grid_start_x, top_margin, btn_width, btn_height)
    draw_button(
        win, "单人", one_player_rect, resources["font"], current_mode == 1,
        one_player_rect.collidepoint(mouse_pos), style=STYLE_MODE[1],
    )
    ui_rects.append(one_player_rect)

    # 2 Player Button
    two_player_rect = pygame.Rect(grid_start_x + btn_width + h_spacing, top_margin, btn_width, btn_height)
    draw_button(
        win, "双人", two_player_rect, resources["font"], current_mode == 2,
        two_player_rect.collidepoint(mouse_pos), style=STYLE_MODE[2],
    )
    ui_rects.append(two_player_rect)

    # 3 Player Button
    three_player_rect = pygame.Rect(grid_start_x, top_margin + btn_height + v_spacing_mode, btn_width, btn_height)
    draw_button(
        win, "三人", three_player_rect, resources["font"], current_mode == 3,
        three_player_rect.collidepoint(mouse_pos), style=STYLE_MODE[3],
    )
    ui_rects.append(three_player_rect)

    # Survival Mode Button
    survival_rect = pygame.Rect(grid_start_x + btn_width + h_spacing, top_margin + btn_height + v_spacing_mode, btn_width, btn_height)
    draw_button(
        win, "生存", survival_rect, resources["font"], current_mode == SURVIVAL_MODE_ID,
        survival_rect.collidepoint(mouse_pos), style=STYLE_MODE[4],
    )
    ui_rects.append(survival_rect)

    # 建筑场景（关卡机关倾向）：与存档同步，开局使用该场景、游戏中不再自动轮换
    scene_key = config.get("building_scene", "siheyuan")
    if not isinstance(scene_key, str) or scene_key not in BUILDING_THEMES:
        scene_key = BUILDING_THEMES[0]
    scene_row_top = survival_rect.bottom + 18
    _ui_blit_centered_label(
        win, resources["small_font"], "建筑场景（机关与关卡倾向）", (52, 62, 80), scene_row_top,
    )
    scene_btn_y = scene_row_top + 26
    scene_btn_h = 48
    scene_btn_w = 112
    scene_gap = 10
    scene_row_w = len(BUILDING_THEMES) * scene_btn_w + (len(BUILDING_THEMES) - 1) * scene_gap
    scene_x0 = (WIDTH - scene_row_w) // 2
    theme_scene_rects = []
    for i, key in enumerate(BUILDING_THEMES):
        r = pygame.Rect(scene_x0 + i * (scene_btn_w + scene_gap), scene_btn_y, scene_btn_w, scene_btn_h)
        theme_scene_rects.append(r)
        lbl = BUILDING_SCENE_BUTTON_LABELS.get(key, key)
        draw_button(
            win, lbl, r, resources["small_font"], scene_key == key, r.collidepoint(mouse_pos),
            style={**{"radius": 10, "hover_lift": 14}, **STYLE_SCENE.get(key, {})},
        )
    ui_rects.extend(theme_scene_rects)

    # Start Game + Daily buttons
    row_y = scene_btn_y + scene_btn_h + 22
    start_rect = pygame.Rect((WIDTH - 250) // 2 - 140, row_y, 250, 70)
    daily_rect = pygame.Rect(start_rect.right + 24, row_y, 250, 70)
    draw_button(
        win, "开始游戏", start_rect, resources["font_bold"], False, start_rect.collidepoint(mouse_pos),
        style={"bg_color": (230, 250, 255), "border_color": (44, 148, 176), "text_color": (26, 60, 78), "radius": 14},
    )
    ui_rects.append(start_rect)
    draw_button(
        win, "每日挑战", daily_rect, resources["font_bold"], False, daily_rect.collidepoint(mouse_pos),
        style={"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52), "radius": 14},
    )
    ui_rects.append(daily_rect)

    # Home quick actions (主页快捷入口)：设置 / 图鉴 / 解密 / 技能 / 商店
    quick_y = start_rect.bottom + 16
    quick_h = 54
    quick_w = 150
    quick_gap = 16
    quick_row_w = quick_w * 5 + quick_gap * 4
    quick_x0 = (WIDTH - quick_row_w) // 2
    settings_btn_rect = pygame.Rect(quick_x0, quick_y, quick_w, quick_h)
    codex_home_rect = pygame.Rect(quick_x0 + quick_w + quick_gap, quick_y, quick_w, quick_h)
    decrypt_home_rect = pygame.Rect(quick_x0 + (quick_w + quick_gap) * 2, quick_y, quick_w, quick_h)
    loadout_home_rect = pygame.Rect(quick_x0 + (quick_w + quick_gap) * 3, quick_y, quick_w, quick_h)
    shop_home_rect = pygame.Rect(quick_x0 + (quick_w + quick_gap) * 4, quick_y, quick_w, quick_h)
    draw_button(
        win, "设置", settings_btn_rect, resources["font"], False, settings_btn_rect.collidepoint(mouse_pos),
        style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78), "radius": 12},
    )
    draw_button(
        win, "图鉴", codex_home_rect, resources["font"], False, codex_home_rect.collidepoint(mouse_pos),
        style={"bg_color": (232, 255, 246), "border_color": (48, 156, 118), "text_color": (28, 60, 52), "radius": 12},
    )
    draw_button(
        win, "解密模式", decrypt_home_rect, resources["small_font"], False, decrypt_home_rect.collidepoint(mouse_pos),
        style={"bg_color": (232, 255, 252), "border_color": (54, 156, 140), "text_color": (28, 60, 52), "radius": 12},
    )
    draw_button(
        win, "技能", loadout_home_rect, resources["font"], False, loadout_home_rect.collidepoint(mouse_pos),
        style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78), "radius": 12},
    )
    draw_button(
        win, "商店", shop_home_rect, resources["font"], False, shop_home_rect.collidepoint(mouse_pos),
        style={"bg_color": (255, 248, 232), "border_color": (188, 152, 88), "text_color": (60, 44, 20), "radius": 12},
    )
    ui_rects.extend([settings_btn_rect, codex_home_rect, decrypt_home_rect, loadout_home_rect, shop_home_rect])

    # Top-right: current menu music + click to switch (右上角：正在播放/点击切换)
    music_label = resources.get("menu_music_name") or "未加载"
    music_btn_w, music_btn_h = 260, 46
    music_btn_rect = pygame.Rect(WIDTH - music_btn_w - 16, 14, music_btn_w, music_btn_h)
    draw_button(
        win, f"正在：{music_label}  (切换)",
        music_btn_rect, resources["small_font"], False, music_btn_rect.collidepoint(mouse_pos),
        style={
            "bg_color": (236, 252, 255),
            "border_color": (76, 152, 182),
            "text_color": (34, 58, 78),
            "radius": 12,
            "max_wrap_lines": 1,
        },
    )
    ui_rects.append(music_btn_rect)

    # Home tutorial (新手引导：全屏覆盖，屏蔽背后按钮)
    tutorial_ok_rect = pygame.Rect(0, 0, 1, 1)
    tutorial_prev_rect = pygame.Rect(0, 0, 1, 1)
    tutorial_next_rect = pygame.Rect(0, 0, 1, 1)
    if home_tutorial_enabled and (not home_tutorial_dismissed):
        home_tutorial_hotspots = {}
        _ui_modal_overlay(win, 210)
        panel = pygame.Rect(24, 24, WIDTH - 48, HEIGHT - 48)
        _ui_panel_shadow(win, panel, 22)
        _ui_draw_vertical_gradient_panel(win, panel, UI_TUTORIAL_BG_TOP, UI_TUTORIAL_BG_BOTTOM, radius=22)
        pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=22)

        def _wrap_lines(font, text: str, max_w: int):
            chars = list(str(text))
            lines = []
            cur = ""
            for ch in chars:
                trial = cur + ch
                if font.size(trial)[0] <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = ch
            if cur:
                lines.append(cur)
            return lines

        def _blit_wrapped(font, text: str, x: int, y: int, max_w: int, color, line_gap: int = 8):
            yy = int(y)
            for ln in _wrap_lines(font, text, max_w):
                s = font.render(ln, False, color)
                win.blit(s, (int(x), yy))
                yy += s.get_height() + int(line_gap)
            return yy

        pad = 44
        content_x = panel.x + pad
        content_w = panel.w - pad * 2
        top_y = panel.y + 28

        # Top-right close
        tutorial_ok_rect = pygame.Rect(panel.right - 164, panel.y + 20, 144, 44)
        draw_button(
            win, "我知道了", tutorial_ok_rect, resources["small_font"],
            False, tutorial_ok_rect.collidepoint(mouse_pos),
            style={
                "bg_color": (232, 255, 246),
                "border_color": (48, 156, 118),
                "text_color": (28, 60, 52),
                "radius": 12,
                "hover_lift": 14,
            },
        )

        title = resources["large_font"].render("新手引导", True, UI_TEXT_PRIMARY)
        win.blit(title, (content_x, top_y))
        sub = resources["small_font"].render("不同模式操作不同，先看这里再开跑。", True, UI_TEXT_SECONDARY)
        win.blit(sub, (content_x, top_y + title.get_height() + 6))
        header_bottom = top_y + title.get_height() + sub.get_height() + 22
        pygame.draw.line(win, UI_DIVIDER, (panel.x + 32, header_bottom), (panel.right - 32, header_bottom), 1)

        # pager controls
        tutorial_prev_rect = pygame.Rect(panel.right - 320, panel.bottom - 62, 140, 44)
        tutorial_next_rect = pygame.Rect(panel.right - 168, panel.bottom - 62, 140, 44)
        draw_button(
            win, "上一页", tutorial_prev_rect, resources["small_font"],
            False, tutorial_prev_rect.collidepoint(mouse_pos),
            style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78), "radius": 12, "hover_lift": 12},
        )
        draw_button(
            win, "下一页", tutorial_next_rect, resources["small_font"],
            False, tutorial_next_rect.collidepoint(mouse_pos),
            style={"bg_color": (236, 252, 255), "border_color": (76, 152, 182), "text_color": (34, 58, 78), "radius": 12, "hover_lift": 12},
        )
        dots = resources["small_font"].render(f"{home_tutorial_page + 1}/2", True, UI_TEXT_SECONDARY)
        win.blit(dots, (panel.centerx - dots.get_width() // 2, panel.bottom - 54))

        body_top = header_bottom + 22
        body_bottom = tutorial_prev_rect.y - 14

        def _draw_keycap(x, y, w, h, label: str, active: bool = True):
            r = pygame.Rect(int(x), int(y), int(w), int(h))
            top = (170, 210, 236) if active else (188, 198, 210)
            bottom = (230, 244, 252) if active else (218, 224, 232)
            _ui_panel_shadow(win, r, 10)
            _ui_draw_vertical_gradient_panel(win, r, top, bottom, radius=10)
            pygame.draw.rect(win, UI_PANEL_BORDER, r, 2, border_radius=10)
            s = resources["small_font"].render(str(label), True, UI_TEXT_PRIMARY)
            win.blit(s, (r.centerx - s.get_width() // 2, r.centery - s.get_height() // 2))
            return r

        def _draw_mouse_icon(x, y, w, h, left_on=False, right_on=False):
            r = pygame.Rect(int(x), int(y), int(w), int(h))
            _ui_panel_shadow(win, r, 12)
            _ui_draw_vertical_gradient_panel(win, r, (170, 210, 236), (230, 244, 252), radius=12)
            pygame.draw.rect(win, UI_PANEL_BORDER, r, 2, border_radius=12)
            inner = r.inflate(-18, -14)
            pygame.draw.rect(win, (36, 48, 66), inner, 2, border_radius=18)
            midx = inner.centerx
            pygame.draw.line(win, (36, 48, 66), (midx, inner.y + 6), (midx, inner.y + inner.h // 2), 2)
            if left_on:
                pygame.draw.rect(win, UI_SUCCESS, pygame.Rect(inner.x + 4, inner.y + 4, inner.w // 2 - 6, inner.h // 2 - 8), 0, border_radius=10)
            if right_on:
                pygame.draw.rect(win, UI_SUCCESS, pygame.Rect(midx + 2, inner.y + 4, inner.w // 2 - 6, inner.h // 2 - 8), 0, border_radius=10)
            return r

        if int(home_tutorial_page) <= 0:
            # Page 1: mode cards + general tips
            cards_y = body_top
            card_gap = 18
            card_w = int((content_w - card_gap) / 2)
            card_h = 140
            x0 = content_x
            x1 = x0 + card_w + card_gap
            y0 = cards_y
            y1 = y0 + card_h + card_gap
            mode_cards = [
                ("单人模式", "操作：鼠标左键"),
                ("双人模式", "操作：鼠标左键 / 鼠标右键"),
                ("三人模式", "操作：鼠标左键 / 鼠标右键 / 空格"),
                ("生存模式", "操作：空格 或 鼠标左键（任选其一即可）"),
            ]
            for i, (hdr, body) in enumerate(mode_cards):
                cx = x0 if (i % 2 == 0) else x1
                cy = y0 if (i < 2) else y1
                r = pygame.Rect(cx, cy, card_w, card_h)
                _ui_panel_shadow(win, r, 14)
                _ui_draw_vertical_gradient_panel(win, r, UI_TUTORIAL_CARD_TOP, UI_TUTORIAL_CARD_BOTTOM, radius=14)
                pygame.draw.rect(win, (76, 152, 182), r, 2, border_radius=14)
                h = resources["font_bold"].render(hdr, True, UI_TEXT_PRIMARY)
                win.blit(h, (r.x + 18, r.y + 16))
                _blit_wrapped(resources["font"], body, r.x + 18, r.y + 54, r.w - 36, UI_TEXT_SECONDARY, line_gap=6)

            tips_top = y1 + card_h + 24
            tips_h = max(120, int(body_bottom - tips_top))
            tips_rect = pygame.Rect(content_x, tips_top, content_w, tips_h)
            _ui_panel_shadow(win, tips_rect, 14)
            _ui_draw_vertical_gradient_panel(win, tips_rect, UI_TUTORIAL_TIPS_TOP, UI_TUTORIAL_TIPS_BOTTOM, radius=14)
            pygame.draw.rect(win, UI_PANEL_BORDER, tips_rect, 2, border_radius=14)
            tip_title = resources["font_bold"].render("通用说明", True, UI_TEXT_PRIMARY)
            win.blit(tip_title, (tips_rect.x + 18, tips_rect.y + 14))
            tips_font = resources.get("tiny_font") or resources.get("small_font")
            old_clip = win.get_clip()
            inner_clip = tips_rect.inflate(-24, -24)
            if inner_clip.w > 2 and inner_clip.h > 2:
                win.set_clip(inner_clip)
            yy = tips_rect.y + 52
            gap = 2
            yy = _blit_wrapped(tips_font, "暂停：按 P 暂停/继续。", tips_rect.x + 18, yy, tips_rect.w - 36, UI_TEXT_SECONDARY, line_gap=gap)
            yy = _blit_wrapped(tips_font, "商店：用“碎片”购买并永久解锁技能（只认左键购买，滚轮只滚动列表）。", tips_rect.x + 18, yy + 4, tips_rect.w - 36, UI_TEXT_SECONDARY, line_gap=gap)
            yy = _blit_wrapped(tips_font, "技能：在“技能”里选择本局携带的技能（最多 6 个，鼠标滚轮可上下滚动列表）。", tips_rect.x + 18, yy + 4, tips_rect.w - 36, UI_TEXT_SECONDARY, line_gap=gap)
            _blit_wrapped(tips_font, "解密：进入“解密模式”答题，冲连对与分数。右上角可切换主页音乐。", tips_rect.x + 18, yy + 4, tips_rect.w - 36, UI_TEXT_SECONDARY, line_gap=gap)
            win.set_clip(old_clip)
        else:
            # Page 2: shortcut icons + per-mode mini diagram
            sec_title = resources["font_bold"].render("快捷键图标与示意", True, UI_TEXT_PRIMARY)
            win.blit(sec_title, (content_x, body_top))
            y = body_top + sec_title.get_height() + 14

            home_tutorial_hotspots["jump_space"] = _draw_keycap(content_x, y, 86, 52, "空格", active=True)
            home_tutorial_hotspots["jump_up"] = _draw_keycap(content_x + 96, y, 70, 52, "↑", active=True)
            lab = resources["small_font"].render("跳跃", True, UI_TEXT_SECONDARY)
            win.blit(lab, (content_x + 178, y + 14))
            home_tutorial_hotspots["pause_p"] = _draw_keycap(content_x + 260, y, 62, 52, "P", active=True)
            lab2 = resources["small_font"].render("暂停/继续", True, UI_TEXT_SECONDARY)
            win.blit(lab2, (content_x + 334, y + 14))

            y += 76
            hint2 = resources["tiny_font"].render("模式操作示意（绿色代表需要按的键/按键组合）", True, UI_TEXT_SECONDARY)
            win.blit(hint2, (content_x, y))
            y += 22

            demo_gap = 14
            demo_h = 110
            demo_w = int((content_w - demo_gap) / 2)
            demos = [
                ("单人", dict(l=True, r=False, sp=False)),
                ("双人", dict(l=True, r=True, sp=False)),
                ("三人", dict(l=True, r=True, sp=True)),
                ("生存", dict(l=True, r=False, sp=True, either=True)),
            ]
            for i, (nm, cfg2) in enumerate(demos):
                dx = content_x if (i % 2 == 0) else (content_x + demo_w + demo_gap)
                dy = y if (i < 2) else (y + demo_h + demo_gap)
                r = pygame.Rect(dx, dy, demo_w, demo_h)
                _ui_panel_shadow(win, r, 14)
                _ui_draw_vertical_gradient_panel(win, r, UI_TUTORIAL_CARD_TOP, UI_TUTORIAL_CARD_BOTTOM, radius=14)
                pygame.draw.rect(win, UI_PANEL_BORDER, r, 2, border_radius=14)
                h = resources["font_bold"].render(f"{nm}模式", True, UI_TEXT_PRIMARY)
                win.blit(h, (r.x + 16, r.y + 12))
                mx = r.x + 16
                my = r.y + 44
                home_tutorial_hotspots[f"mouse_{nm}"] = _draw_mouse_icon(mx, my, 88, 52, left_on=cfg2.get("l", False), right_on=cfg2.get("r", False))
                if cfg2.get("sp", False):
                    home_tutorial_hotspots[f"space_{nm}"] = _draw_keycap(mx + 98, my, 110, 52, "空格", active=True)
                if cfg2.get("either"):
                    e = resources["tiny_font"].render("任一即可", True, UI_TEXT_SECONDARY)
                    win.blit(e, (r.right - e.get_width() - 16, my + 14))

            # contextual hint toast inside tutorial (click hotspots to show)
            now_ms = pygame.time.get_ticks()
            if home_tutorial_hint.get("text") and int(home_tutorial_hint.get("until_ms", 0)) > now_ms:
                txt = str(home_tutorial_hint.get("text"))
                box = pygame.Rect(panel.x + 28, panel.bottom - 118, panel.w - 56, 54)
                _ui_panel_shadow(win, box, 14)
                _ui_draw_vertical_gradient_panel(win, box, UI_CARD_NEUTRAL_TOP, UI_CARD_NEUTRAL_BOTTOM, radius=14)
                pygame.draw.rect(win, UI_PANEL_BORDER, box, 2, border_radius=14)
                s = resources["small_font"].render(txt, True, UI_TEXT_PRIMARY)
                win.blit(s, (box.centerx - s.get_width() // 2, box.centery - s.get_height() // 2))

    ui_rects.extend([tutorial_ok_rect, tutorial_prev_rect, tutorial_next_rect])

    ver = resources["small_font"].render("v1.0.0", True, UI_TEXT_SECONDARY)
    vx, vy = WIDTH - ver.get_width() - 14, HEIGHT - 26
    vo = resources["small_font"].render("v1.0.0", True, (250, 252, 255))
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        win.blit(vo, (vx + dx, vy + dy))
    win.blit(ver, (vx, vy))

    return ui_rects

def draw_game_over(win, resources, mouse_pos=None):
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()
    if resources['game_over_img']:
        scaled_img = pygame.transform.scale(resources['game_over_img'], (WIDTH, HEIGHT))
        win.blit(scaled_img, (0, 0))
    else:
        win.fill(BLACK)

    _ui_modal_overlay(win, 150)

    card = pygame.Rect(WIDTH // 2 - 240, HEIGHT // 2 - 158, 480, 316)
    _ui_panel_shadow(win, card, 18)
    _ui_draw_vertical_gradient_panel(win, card, UI_WARM_CARD_TOP, UI_WARM_CARD_BOTTOM, radius=18)
    pygame.draw.rect(win, UI_PANEL_BORDER, card, 2, border_radius=18)

    game_over_text = resources['large_font'].render("游戏结束", True, UI_TEXT_PRIMARY)
    win.blit(game_over_text, game_over_text.get_rect(center=(WIDTH // 2, card.y + 52)))

    score_text = resources['font'].render(f"本局得分：{score}", True, UI_TEXT_PRIMARY)
    win.blit(score_text, score_text.get_rect(center=(WIDTH // 2, card.y + 118)))

    high_score_text = resources['font'].render(f"最高分：{high_score}", True, UI_ACCENT_WARM)
    win.blit(high_score_text, high_score_text.get_rect(center=(WIDTH // 2, card.y + 158)))

    restart_rect = pygame.Rect(WIDTH // 2 - 190, card.bottom - 72, 380, 54)
    draw_button(win, "返回主页", restart_rect, resources['font'], False, restart_rect.collidepoint(mouse_pos))

    return restart_rect


def draw_pause_screen(win, resources, mouse_pos=None):
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()
    _ui_modal_overlay(win, 120)

    card = pygame.Rect(WIDTH // 2 - 230, HEIGHT // 2 - 168, 460, 336)
    _ui_panel_shadow(win, card, 18)
    _ui_draw_vertical_gradient_panel(win, card, UI_CARD_NEUTRAL_TOP, UI_CARD_NEUTRAL_BOTTOM, radius=18)
    pygame.draw.rect(win, UI_PANEL_BORDER, card, 2, border_radius=18)

    pause_text = resources['large_font'].render("已暂停", True, UI_TEXT_PRIMARY)
    win.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, card.y + 56)))

    hint_text = resources['font'].render("按 P 继续游戏", True, UI_TEXT_SECONDARY)
    win.blit(hint_text, hint_text.get_rect(center=(WIDTH // 2, card.y + 118)))

    pygame.draw.line(win, UI_DIVIDER, (card.x + 40, card.y + 150), (card.right - 40, card.y + 150), 1)

    codex_rect = pygame.Rect(WIDTH // 2 - 180, card.y + 172, 360, 50)
    draw_button(win, "建筑图鉴（I）", codex_rect, resources['font'], False, codex_rect.collidepoint(mouse_pos))

    menu_rect = pygame.Rect(WIDTH // 2 - 180, card.y + 236, 360, 50)
    draw_button(win, "返回主页", menu_rect, resources['font'], False, menu_rect.collidepoint(mouse_pos))

    return menu_rect, codex_rect

def _apply_music_volume(vol: float, resources):
    vol = float(vol)
    if vol < 0.0: vol = 0.0
    if vol > 1.0: vol = 1.0
    try:
        pygame.mixer.music.set_volume(vol)
    except Exception:
        pass
    # if mode select music is a Sound, set its volume too
    try:
        if resources.get("mode_select_music_loaded", False) and resources.get("mode_select_music"):
            resources["mode_select_music"].set_volume(vol)
    except Exception:
        pass


def _play_mode_select_music(resources):
    """Play home/menu music (Sound or music channel fallback)."""
    if not resources.get('mode_select_music_loaded', False):
        return
    kind = resources.get("mode_select_music_kind", "sound")
    if kind == "sound" and resources.get("mode_select_music"):
        resources["mode_select_music"].play(loops=-1)
        return
    path = resources.get("mode_select_music_path")
    if isinstance(path, str) and path:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(loops=-1)


def _stop_mode_select_music(resources):
    """Stop home/menu music safely."""
    if not resources.get('mode_select_music_loaded', False):
        return
    try:
        kind = resources.get("mode_select_music_kind", "sound")
        if kind == "sound" and resources.get("mode_select_music"):
            resources["mode_select_music"].stop()
        elif kind == "music":
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
    except Exception:
        pass

def _switch_menu_music(resources, next_index: int):
    """Switch home/menu music track and restart playback."""
    tracks = resources.get("home_music_tracks") or []
    if not tracks:
        return
    next_index = int(next_index) % len(tracks)
    next_path = tracks[next_index].get("path")
    next_name = str(tracks[next_index].get("name", ""))
    if not isinstance(next_path, str) or not next_path:
        return

    try:
        _stop_mode_select_music(resources)
    except Exception:
        pass

    resources["menu_music_index"] = next_index
    resources["menu_music_name"] = next_name
    resources["mode_select_music_path"] = next_path
    resources["mode_select_music_loaded"] = True

    # Recreate Sound if possible; otherwise use music channel.
    try:
        resources["mode_select_music"] = pygame.mixer.Sound(next_path)
        resources["mode_select_music_kind"] = "sound"
    except Exception:
        resources["mode_select_music"] = None
        resources["mode_select_music_kind"] = "music"

    try:
        _apply_music_volume(load_config().get("music_volume", 0.7), resources)
    except Exception:
        pass
    try:
        _play_mode_select_music(resources)
    except Exception:
        pass

def _apply_fullscreen(screen, fullscreen: bool):
    try:
        flags = pygame.FULLSCREEN if fullscreen else 0
        return pygame.display.set_mode((WIDTH, HEIGHT), flags)
    except Exception:
        return screen

def draw_settings_screen(win, resources, mouse_pos):
    cfg = load_config()
    jump_level = int(cfg.get("jump_level", 1))
    max_hp = int(cfg.get("max_hp", 3))
    music_volume = float(cfg.get("music_volume", 0.7))
    fullscreen = bool(cfg.get("fullscreen", False))
    home_tutorial_enabled = bool(cfg.get("home_tutorial_enabled", True))

    _ui_modal_overlay(win, 165)

    # 设置面板加大：避免按钮/文字在大字体下重叠
    panel = pygame.Rect(WIDTH // 2 - 420, 50, 840, 680)
    _ui_panel_shadow(win, panel, 18)
    _ui_draw_vertical_gradient_panel(win, panel, UI_SETTINGS_BG_TOP, UI_SETTINGS_BG_BOTTOM, radius=18)
    pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=18)

    # 自适应排版：不同字体/渲染下高度变化，固定 y 容易重叠
    title = resources["large_font"].render("设置", True, UI_TEXT_PRIMARY)
    title_y = panel.y + 18
    win.blit(title, (panel.centerx - title.get_width() // 2, title_y))
    divider_y = title_y + title.get_height() + 10
    pygame.draw.line(win, UI_DIVIDER, (panel.x + 48, divider_y), (panel.right - 48, divider_y), 1)
    cap = resources["small_font"].render("生存模式与音效选项 · 即时保存", True, UI_TEXT_SECONDARY)
    cap_y = divider_y + 10
    win.blit(cap, (panel.centerx - cap.get_width() // 2, cap_y))

    y = cap_y + cap.get_height() + 28
    row_h = max(90, resources["font"].get_height() + 42)
    label_x = panel.x + 70
    ctrl_x = panel.x + 360
    value_x = ctrl_x + 170

    # --- Max HP ---
    win.blit(resources["font"].render("生命上限", True, UI_TEXT_PRIMARY), (label_x, y))
    hp_val = resources["font"].render(str(max_hp), True, UI_TEXT_PRIMARY)
    win.blit(hp_val, (value_x - hp_val.get_width()//2, y))
    hp_minus = pygame.Rect(ctrl_x, y - 4, 70, 50)
    hp_plus = pygame.Rect(ctrl_x + 320, y - 4, 70, 50)
    draw_button(win, "－", hp_minus, resources["font"], False, hp_minus.collidepoint(mouse_pos))
    draw_button(win, "＋", hp_plus, resources["font"], False, hp_plus.collidepoint(mouse_pos))

    # --- Jump level ---
    y2 = y + row_h
    win.blit(resources["font"].render("跳跃段数", True, UI_TEXT_PRIMARY), (label_x, y2))
    jl_val = resources["font"].render(f"{jump_level} 段", True, UI_TEXT_PRIMARY)
    win.blit(jl_val, (value_x - jl_val.get_width()//2, y2))
    jl_minus = pygame.Rect(ctrl_x, y2 - 4, 70, 50)
    jl_plus = pygame.Rect(ctrl_x + 320, y2 - 4, 70, 50)
    draw_button(win, "－", jl_minus, resources["font"], False, jl_minus.collidepoint(mouse_pos))
    draw_button(win, "＋", jl_plus, resources["font"], False, jl_plus.collidepoint(mouse_pos))

    # --- Music volume ---
    y3 = y2 + row_h
    win.blit(resources["font"].render("音乐音量", True, UI_TEXT_PRIMARY), (label_x, y3))
    mv_percent = int(music_volume * 100)
    mv_val = resources["font"].render(f"{mv_percent}%", True, UI_TEXT_PRIMARY)
    win.blit(mv_val, (value_x - mv_val.get_width()//2, y3))
    mv_minus = pygame.Rect(ctrl_x, y3 - 4, 70, 50)
    mv_plus = pygame.Rect(ctrl_x + 320, y3 - 4, 70, 50)
    draw_button(win, "－", mv_minus, resources["font"], False, mv_minus.collidepoint(mouse_pos))
    draw_button(win, "＋", mv_plus, resources["font"], False, mv_plus.collidepoint(mouse_pos))

    # --- Fullscreen ---
    y4 = y3 + row_h
    win.blit(resources["font"].render("全屏", True, UI_TEXT_PRIMARY), (label_x, y4))
    fs_text = "开" if fullscreen else "关"
    fs_val = resources["font"].render(fs_text, True, UI_TEXT_PRIMARY)
    win.blit(fs_val, (value_x - fs_val.get_width()//2, y4))
    fs_toggle = pygame.Rect(ctrl_x, y4 - 4, 430, 50)
    draw_button(win, "切换全屏", fs_toggle, resources["font"], False, fs_toggle.collidepoint(mouse_pos))

    # --- Home tutorial ---
    y5 = y4 + row_h
    win.blit(resources["font"].render("新手引导", True, UI_TEXT_PRIMARY), (label_x, y5))
    ht_text = "开" if home_tutorial_enabled else "关"
    ht_val = resources["font"].render(ht_text, True, UI_TEXT_PRIMARY)
    win.blit(ht_val, (value_x - ht_val.get_width()//2, y5))
    tutorial_toggle = pygame.Rect(ctrl_x, y5 - 4, 430, 50)
    draw_button(win, f"引导（{ht_text}）", tutorial_toggle, resources["font"], False, tutorial_toggle.collidepoint(mouse_pos))

    hint = resources["small_font"].render("点击按钮调节 · Esc 返回主页", True, UI_TEXT_SECONDARY)
    win.blit(hint, (panel.centerx - hint.get_width()//2, panel.bottom - 62))

    return {
        "panel": panel,
        "hp_minus": hp_minus, "hp_plus": hp_plus,
        "jl_minus": jl_minus, "jl_plus": jl_plus,
        "mv_minus": mv_minus, "mv_plus": mv_plus,
        "fs_toggle": fs_toggle,
        "tutorial_toggle": tutorial_toggle,
    }


def draw_loadout_screen(win, resources, mouse_pos, scroll_y: int = 0):
    """Skill loadout screen: enable/disable and choose equipped skills."""
    cfg = load_config()
    _ui_modal_overlay(win, 165)

    # slightly taller panel to fit lists on 750p
    panel = pygame.Rect(WIDTH // 2 - 420, 50, 840, 660)
    _ui_panel_shadow(win, panel, 18)
    _ui_draw_vertical_gradient_panel(win, panel, UI_LOADOUT_BG_TOP, UI_LOADOUT_BG_BOTTOM, radius=18)
    pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=18)

    title = resources["large_font"].render("技能装备", True, UI_TEXT_PRIMARY)
    title_y = panel.y + 18
    win.blit(title, (panel.centerx - title.get_width() // 2, title_y))
    divider_y = title_y + title.get_height() + 10
    pygame.draw.line(win, UI_DIVIDER, (panel.x + 48, divider_y), (panel.right - 48, divider_y), 1)

    unlock = cfg.get("unlock_skills") if isinstance(cfg, dict) else {}
    if not isinstance(unlock, dict):
        unlock = {}
    loadout = cfg.get("loadout") if isinstance(cfg, dict) else {}
    if not isinstance(loadout, dict):
        loadout = {}
    enabled = bool(loadout.get("enabled", True))
    slots = loadout.get("slots")
    if not isinstance(slots, list):
        slots = []
    shards = int(cfg.get("skill_shards", 0)) if isinstance(cfg, dict) else 0

    cap = resources["small_font"].render("解密答对可永久解锁技能；每局可选择不携带", True, UI_TEXT_SECONDARY)
    win.blit(cap, (panel.centerx - cap.get_width() // 2, divider_y + 10))
    cap2 = resources["small_font"].render("说明：技能效果只在跑酷中生效（解密/主页不会变化）", True, UI_TEXT_SECONDARY)
    win.blit(cap2, (panel.centerx - cap2.get_width() // 2, divider_y + 34))

    # top toggles
    toggle_rect = pygame.Rect(panel.x + 60, divider_y + 50, 260, 54)
    toggle_text = "携带：开" if enabled else "携带：关"
    draw_button(
        win, toggle_text, toggle_rect, resources["font_bold"], enabled, toggle_rect.collidepoint(mouse_pos),
        style={"bg_color": (232, 255, 246) if enabled else (236, 252, 255), "border_color": (48, 156, 118) if enabled else (76, 152, 182)},
    )

    shard_s = resources["small_font"].render(f"技能碎片：{max(0, shards)}", True, UI_TEXT_SECONDARY)
    win.blit(shard_s, (panel.right - 60 - shard_s.get_width(), divider_y + 64))

    # Equipped slots (compact: 2 rows x 3)
    slot_y = divider_y + 110
    win.blit(resources["font"].render("已装备（最多 6 个）", True, UI_TEXT_PRIMARY), (panel.x + 60, slot_y))
    slot_y += 44
    slot_rects = []
    slot_gap_x = 12
    slot_gap_y = 10
    slot_w = int((panel.w - 120 - slot_gap_x * 2) / 3)
    slot_h = 46
    for i in range(6):
        r = pygame.Rect(
            panel.x + 60 + (i % 3) * (slot_w + slot_gap_x),
            slot_y + (i // 3) * (slot_h + slot_gap_y),
            slot_w,
            slot_h,
        )
        sid = slots[i] if i < len(slots) else ""
        label = "（空槽）"
        st = {"radius": 12, "hover_lift": 12, "wrap": True, "pad": (16, 10), "line_gap": 8}
        if isinstance(sid, str) and sid in SKILLS:
            label = f"{SKILLS[sid]['name']} Lv{int(unlock.get(sid, 1))}"
            st.update({"bg_color": (230, 250, 255), "border_color": (44, 148, 176), "text_color": (26, 60, 78)})
        else:
            st.update({"bg_color": (245, 247, 252), "border_color": (92, 118, 150), "text_color": (40, 52, 72)})
        draw_button(win, label, r, resources["small_font"], False, r.collidepoint(mouse_pos), style=st)
        slot_rects.append((i, r))

    # Current equipped detail (quick preview)
    pv_y = slot_y + 2 * (slot_h + slot_gap_y) + 10
    # show description for hovered slot
    hover_sid = None
    for i, r in slot_rects:
        if r.collidepoint(mouse_pos) and i < len(slots):
            hover_sid = slots[i]
            break
    if hover_sid in SKILLS:
        nm = SKILLS[hover_sid]["name"]
        desc = SKILLS[hover_sid]["desc"]
        t = resources["font"].render(f"预览：{nm}", True, UI_TEXT_PRIMARY)
        win.blit(t, (panel.x + 60, pv_y))
        d = resources["small_font"].render(desc, False, UI_TEXT_SECONDARY)
        win.blit(d, (panel.x + 60, pv_y + 34))

    # Available skills list
    # 原右侧栏在窄屏下会导致文字溢出；改为“下方全宽列表”
    list_x = panel.x + 60
    list_w = panel.w - 120
    list_top = pv_y + 78
    win.blit(resources["font"].render("可选技能（点击添加/移除）", True, UI_TEXT_PRIMARY), (list_x, list_top))
    list_top += 44

    unlocked_ids = [sid for sid, lv in unlock.items() if isinstance(sid, str) and sid in SKILLS and int(lv) > 0]
    unlocked_ids.sort(key=lambda s: SKILLS.get(s, {}).get("name", s))
    if not unlocked_ids:
        empty = resources["small_font"].render("（尚未解锁技能，去解密模式答题吧）", True, UI_TEXT_SECONDARY)
        win.blit(empty, (list_x, list_top + 10))

    skill_rects = []
    item_h = 78
    # 根据可用高度 + 滚动，避免“移除后找不到”的问题
    avail_h = (panel.bottom - 120) - list_top
    total_h = max(0, len(unlocked_ids) * (item_h + 10) - 10)
    max_scroll = max(0, int(total_h - avail_h))
    try:
        scroll_y = int(scroll_y)
    except Exception:
        scroll_y = 0
    if scroll_y < 0:
        scroll_y = 0
    if scroll_y > max_scroll:
        scroll_y = max_scroll

    viewport = pygame.Rect(list_x, list_top, list_w, max(0, (panel.bottom - 120) - list_top))
    card_font = resources.get("small_font")
    desc_font = resources.get("tiny_font") or resources.get("small_font")

    def _draw_skill_item(_win, sid: str, r: pygame.Rect, hovered: bool, pressed: bool):
        equipped = sid in slots
        top = (160, 224, 196) if equipped else (156, 206, 236)
        bot = (220, 246, 232) if equipped else (224, 244, 252)
        border = (48, 156, 118) if equipped else UI_PANEL_BORDER
        draw_r = _ui_draw_card(_win, r, top, bot, border, hovered=hovered, pressed=pressed, radius=14, shadow_radius=14)

        nm = str(SKILLS.get(sid, {}).get("name", sid))
        lv = int(unlock.get(sid, 1))
        title = card_font.render(f"{nm}  Lv{lv}", True, UI_TEXT_PRIMARY)
        _win.blit(title, (draw_r.x + 16, draw_r.y + 12))

        desc = str(SKILLS.get(sid, {}).get("desc", ""))
        if desc:
            max_w = max(10, draw_r.w - 32)
            cur = ""
            line = ""
            for ch in list(desc):
                trial = cur + ch
                if desc_font.size(trial)[0] <= max_w:
                    cur = trial
                else:
                    line = cur
                    break
            if not line:
                line = cur
            d = desc_font.render(line, False, UI_TEXT_SECONDARY)
            _win.blit(d, (draw_r.x + 16, draw_r.y + 46))

    visible, max_scroll, scroll_y = _ui_draw_scroll_card_list(
        win, viewport, unlocked_ids, scroll_y, item_h=item_h, gap=10, mouse_pos=mouse_pos, draw_item_fn=_draw_skill_item
    )
    skill_rects = [(sid, r) for (sid, r) in visible]

    # locked purchase moved to shop screen
    if max_scroll > 0:
        tip = resources["small_font"].render("鼠标滚轮：滚动技能列表", True, UI_TEXT_SECONDARY)
        win.blit(tip, (panel.right - 60 - tip.get_width(), panel.bottom - 126))

    hint = resources["small_font"].render("提示：关闭“携带”即可本局不带技能", True, UI_TEXT_SECONDARY)
    win.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 104))

    back = pygame.Rect(panel.centerx - 120, panel.bottom - 60, 240, 48)
    draw_button(win, "返回主页", back, resources["font_bold"], False, back.collidepoint(mouse_pos))

    return {
        "toggle": toggle_rect,
        "slots": slot_rects,
        "skills": skill_rects,
        "back": back,
        "max_scroll": max_scroll,
    }


def draw_skill_shop(win, resources, mouse_pos, scroll_y: int = 0):
    """Skill shop: 1 shard buys 1 locked skill (permanent unlock)."""
    cfg = load_config()
    _ui_modal_overlay(win, 165)

    panel = pygame.Rect(WIDTH // 2 - 420, 72, 840, 610)
    _ui_panel_shadow(win, panel, 18)
    _ui_draw_vertical_gradient_panel(win, panel, UI_WARM_CARD_TOP, UI_WARM_CARD_BOTTOM, radius=18)
    pygame.draw.rect(win, UI_PANEL_BORDER, panel, 2, border_radius=18)

    title = resources["large_font"].render("技能商店", True, UI_TEXT_PRIMARY)
    title_y = panel.y + 18
    win.blit(title, (panel.centerx - title.get_width() // 2, title_y))
    divider_y = title_y + title.get_height() + 10
    pygame.draw.line(win, UI_DIVIDER, (panel.x + 48, divider_y), (panel.right - 48, divider_y), 1)

    unlock = cfg.get("unlock_skills") if isinstance(cfg, dict) else {}
    if not isinstance(unlock, dict):
        unlock = {}
    shards = int(cfg.get("skill_shards", 0)) if isinstance(cfg, dict) else 0

    s = resources["font_bold"].render(f"碎片：{max(0, shards)}", True, UI_TEXT_PRIMARY)
    win.blit(s, (panel.x + 60, divider_y + 18))
    hint = (resources.get("tiny_font") or resources["small_font"]).render("规则：1 碎片 = 解锁 1 个技能（永久）", True, UI_TEXT_SECONDARY)
    win.blit(hint, (panel.x + 60, divider_y + 56))

    unlocked_ids = [sid for sid, lv in unlock.items() if isinstance(sid, str) and sid in SKILLS and int(lv) > 0]
    locked_ids = [sid for sid in SKILLS.keys() if sid not in unlocked_ids]
    locked_ids.sort(key=lambda s: SKILLS.get(s, {}).get("name", s))

    list_x = panel.x + 60
    list_w = panel.w - 120
    list_top = divider_y + 100
    item_h = 88
    list_bottom = panel.bottom - 140
    viewport = pygame.Rect(list_x, list_top, list_w, max(0, list_bottom - list_top))

    shop_font = resources.get("tiny_font") or resources["small_font"]

    def _draw_shop_item(_win, sid: str, r: pygame.Rect, hovered: bool, pressed: bool):
        can_buy = shards >= 1
        top = UI_WARM_CARD_TOP if can_buy else (170, 170, 170)
        bot = UI_WARM_CARD_BOTTOM if can_buy else (210, 210, 210)
        border = UI_PANEL_BORDER if can_buy else (110, 120, 132)
        draw_r = _ui_draw_card(_win, r, top, bot, border, hovered=hovered, pressed=pressed, radius=14, shadow_radius=14)

        name = str(SKILLS.get(sid, {}).get("name", sid))
        title = shop_font.render(f"购买：{name}（-1 碎片）", True, UI_TEXT_PRIMARY if can_buy else (86, 92, 104))
        _win.blit(title, (draw_r.x + 16, draw_r.y + 14))

        desc = str(SKILLS.get(sid, {}).get("desc", ""))
        if desc:
            max_w = max(10, draw_r.w - 32)
            lines = []
            cur = ""
            for ch in list(desc):
                tr = cur + ch
                if shop_font.size(tr)[0] <= max_w:
                    cur = tr
                else:
                    if cur:
                        lines.append(cur)
                    cur = ch
                if len(lines) >= 2:
                    break
            if len(lines) < 2 and cur:
                lines.append(cur)
            yy = draw_r.y + 46
            for ln in lines[:2]:
                d = shop_font.render(ln, False, UI_TEXT_SECONDARY if can_buy else (96, 102, 112))
                _win.blit(d, (draw_r.x + 16, yy))
                yy += d.get_height() + 6

    visible, max_scroll, scroll_y = _ui_draw_scroll_card_list(
        win, viewport, locked_ids, scroll_y, item_h=item_h, gap=10, mouse_pos=mouse_pos, draw_item_fn=_draw_shop_item
    )
    buy_rects = [(sid, r) for (sid, r) in visible]

    if max_scroll > 0:
        tip = (resources.get("tiny_font") or resources["small_font"]).render("鼠标滚轮：上下滚动商品列表", True, UI_TEXT_SECONDARY)
        win.blit(tip, (panel.right - 60 - tip.get_width(), panel.bottom - 126))

    if not locked_ids:
        done = resources["font"].render("（全部技能已解锁）", True, UI_TEXT_SECONDARY)
        win.blit(done, (panel.centerx - done.get_width() // 2, list_top + 20))

    # bottom actions
    reset_btn = pygame.Rect(panel.centerx - 260, panel.bottom - 60, 220, 48)
    back = pygame.Rect(panel.centerx + 40, panel.bottom - 60, 220, 48)
    draw_button(
        win,
        "重置已购买",
        reset_btn,
        resources["font_bold"],
        False,
        reset_btn.collidepoint(mouse_pos),
        style={"bg_color": (245, 247, 252), "border_color": (92, 118, 150), "text_color": (60, 72, 92), "radius": 12},
    )
    draw_button(win, "返回主页", back, resources["font_bold"], False, back.collidepoint(mouse_pos))

    return {"buy": buy_rects, "reset": reset_btn, "back": back, "max_scroll": max_scroll}

# -----------------------------
# Main Function (主函数)
# -----------------------------
def main():
    global game_state, speed, score, score_float, high_score, current_level, current_mode, survival_mode_duration, survival_next_boss_wave
    global codex_return_state, codex_scroll_y, codex_view_mode, codex_selected_entry_id, codex_page_idx
    global building_theme, building_theme_ms, architecture_spawn_timer, hud_toast
    global decrypt_stats, decrypt_current, decrypt_feedback
    global decrypt_view, decrypt_theme, decrypt_start_ms, decrypt_streak, decrypt_score, decrypt_wrong_scroll_y
    global decrypt_choice_idx, decrypt_lock_until_ms, decrypt_auto_next_ms, decrypt_pool_mode
    global run_equipped_skills, run_skill_levels, run_skill_runtime, run_event
    global run_start_ms, run_goals
    global daily_run, daily_seed_used
    global loadout_scroll_y, shop_scroll_y, home_tutorial_dismissed, home_tutorial_page
    
    pygame.init()
    pygame.mixer.init()
    home_tutorial_dismissed = False
    home_tutorial_page = 0
    # 默认窗口化启动；是否全屏由配置项 fullscreen 决定（默认 False）
    cfg0 = load_config()
    # 用户需求：每次打开游戏都重置“已购买/已解锁技能”
    if isinstance(cfg0, dict):
        cfg0["unlock_skills"] = {}
        ld0 = cfg0.get("loadout")
        if not isinstance(ld0, dict):
            ld0 = {"enabled": True, "slots": []}
        ld0["slots"] = []
        cfg0["loadout"] = ld0
        cfg0["skill_shards"] = INITIAL_SKILL_SHARDS
        save_config(cfg0)
    start_fullscreen = bool(cfg0.get("fullscreen", False))
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if start_fullscreen else 0)
    pygame.display.set_caption("古建行歌")
    clock = pygame.time.Clock()
    resources = load_resources()
    high_score = load_config().get("high_score", 0)
    _sync_cultural_from_config()
    _apply_music_volume(load_config().get("music_volume", 0.7), resources)

    players = []
    obstacles = []
    items = []
    collectibles = []
    flying_obstacles = []

    spawn_timer = 0
    item_spawn_timer = 0
    collectible_spawn_timer = 0

    theme_scene_rects = [pygame.Rect(0, 0, 1, 1) for _ in range(len(BUILDING_THEMES))]

    mouse_pos = pygame.mouse.get_pos()
    ui_rects = draw_mode_select(screen, resources, mouse_pos)
    
    # 确保获取所有按钮（... + 主页音乐切换 + 新手引导按钮(关闭/上一页/下一页) = 19）
    while len(ui_rects) < 19:
        ui_rects = draw_mode_select(screen, resources, mouse_pos)

    # 顺序：4 个模式 + 4 个建筑场景 + 开始 + 每日 + 设置 + 图鉴 + 解密 + 技能 + 商店 + 主页音乐切换 + 新手引导（关闭/上一页/下一页）（共 19 个）
    one_player_rect, two_player_rect, three_player_rect, survival_rect = ui_rects[:4]
    theme_scene_rects = ui_rects[4:8]
    start_rect, daily_rect, settings_btn_rect, codex_home_rect, decrypt_home_rect, loadout_home_rect, shop_home_rect, menu_music_rect, tutorial_ok_rect, tutorial_prev_rect, tutorial_next_rect = ui_rects[8:19]

    # Play mode select music (播放模式选择音乐)
    if resources.get('mode_select_music_loaded', False):
        try:
            _apply_music_volume(load_config().get("music_volume", 0.7), resources)
            _play_mode_select_music(resources)
        except Exception as e:
            print(f"Failed to play mode select music: {e}")

    running = True
    # pause toggle: use key state edge, IME-safe
    prev_p_pressed = False
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        now_ms = pygame.time.get_ticks()
        base_speed = float(speed)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEWHEEL:
                if game_state == GameState.CODEX:
                    if codex_view_mode == "list":
                        codex_scroll_y = max(
                            0,
                            min(_codex_list_max_scroll(), codex_scroll_y - int(event.y * 64)),
                        )
                elif game_state == GameState.DECRYPT and decrypt_view == "wrongbook":
                    decrypt_wrong_scroll_y = max(0, int(decrypt_wrong_scroll_y) - int(event.y * 72))
                elif game_state == GameState.LOADOUT:
                    # scroll available skills list
                    loadout_scroll_y = max(0, int(loadout_scroll_y) - int(event.y * 72))
                elif game_state == GameState.SHOP:
                    shop_scroll_y = max(0, int(shop_scroll_y) - int(event.y * 72))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == GameState.MODE_SELECT:
                    # Home tutorial overlay: if enabled, only accept "OK" click, block others
                    if bool(load_config().get("home_tutorial_enabled", True)) and (not home_tutorial_dismissed):
                        if tutorial_ok_rect.collidepoint(event.pos):
                            home_tutorial_dismissed = True
                            home_tutorial_page = 0
                        elif tutorial_prev_rect.collidepoint(event.pos):
                            home_tutorial_page = max(0, int(home_tutorial_page) - 1)
                        elif tutorial_next_rect.collidepoint(event.pos):
                            home_tutorial_page = min(1, int(home_tutorial_page) + 1)
                        else:
                            # tutorial hotspots (page2): click to show tips
                            try:
                                if int(home_tutorial_page) == 1 and isinstance(home_tutorial_hotspots, dict):
                                    p = event.pos
                                    if home_tutorial_hotspots.get("jump_space") and home_tutorial_hotspots["jump_space"].collidepoint(p):
                                        home_tutorial_hint["text"] = "空格：跳跃（部分模式需要）"
                                        home_tutorial_hint["until_ms"] = pygame.time.get_ticks() + 1800
                                    elif home_tutorial_hotspots.get("jump_up") and home_tutorial_hotspots["jump_up"].collidepoint(p):
                                        home_tutorial_hint["text"] = "↑：也可以跳跃（与空格同作用）"
                                        home_tutorial_hint["until_ms"] = pygame.time.get_ticks() + 1800
                                    elif home_tutorial_hotspots.get("pause_p") and home_tutorial_hotspots["pause_p"].collidepoint(p):
                                        home_tutorial_hint["text"] = "P：暂停/继续（任何时候都能用）"
                                        home_tutorial_hint["until_ms"] = pygame.time.get_ticks() + 1800
                                    else:
                                        for k, r in list(home_tutorial_hotspots.items()):
                                            if isinstance(r, pygame.Rect) and r.collidepoint(p) and k.startswith("mouse_"):
                                                home_tutorial_hint["text"] = "鼠标左右键：按模式使用（绿色=需要按）"
                                                home_tutorial_hint["until_ms"] = pygame.time.get_ticks() + 1800
                                                break
                            except Exception:
                                pass
                        continue
                    if one_player_rect.collidepoint(event.pos): 
                        current_mode = 1
                    elif two_player_rect.collidepoint(event.pos): 
                        current_mode = 2
                    elif three_player_rect.collidepoint(event.pos): 
                        current_mode = 3
                    elif survival_rect.collidepoint(event.pos): 
                        current_mode = SURVIVAL_MODE_ID
                    elif any(_tr.collidepoint(event.pos) for _tr in theme_scene_rects):
                        for _ti, _tr in enumerate(theme_scene_rects):
                            if _tr.collidepoint(event.pos):
                                _cfg = load_config()
                                _cfg["building_scene"] = BUILDING_THEMES[_ti]
                                save_config(_cfg)
                                break
                    elif settings_btn_rect.collidepoint(event.pos):
                        game_state = GameState.SETTINGS
                    elif codex_home_rect.collidepoint(event.pos):
                        codex_return_state = GameState.MODE_SELECT
                        game_state = GameState.CODEX
                    elif decrypt_home_rect.collidepoint(event.pos):
                        decrypt_stats = {"correct": 0, "total": 0}
                        decrypt_current = None
                        decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                        decrypt_view = "quiz"
                        decrypt_streak = 0
                        decrypt_score = 0
                        decrypt_wrong_scroll_y = 0
                        cfg = load_config()
                        decrypt_theme = cfg.get("building_scene", "siheyuan")
                        if not isinstance(decrypt_theme, str) or decrypt_theme not in BUILDING_THEMES:
                            decrypt_theme = "siheyuan"
                        decrypt_start_ms = None
                        game_state = GameState.DECRYPT
                    elif loadout_home_rect.collidepoint(event.pos):
                        game_state = GameState.LOADOUT
                    elif shop_home_rect.collidepoint(event.pos):
                        shop_scroll_y = 0
                        game_state = GameState.SHOP
                    elif menu_music_rect.collidepoint(event.pos):
                        tracks = resources.get("home_music_tracks") or []
                        if tracks:
                            cur = int(resources.get("menu_music_index", 0))
                            nxt = (cur + 1) % len(tracks)
                            cfg = load_config()
                            cfg["menu_music_index"] = nxt
                            save_config(cfg)
                            _switch_menu_music(resources, nxt)
                    elif start_rect.collidepoint(event.pos):
                        if resources.get('mode_select_music_loaded', False):
                            _stop_mode_select_music(resources)
                        daily_run = False
                        daily_seed_used = 0
                        players, obstacles, items, flying_obstacles = reset_game(players, obstacles, items, flying_obstacles, resources)
                    elif daily_rect.collidepoint(event.pos):
                        if resources.get('mode_select_music_loaded', False):
                            _stop_mode_select_music(resources)
                        # daily seed by date + selected mode + scene
                        cfg = load_config()
                        today = datetime.date.today().isoformat()
                        seed = abs(hash((today, int(current_mode), str(cfg.get("building_scene", "siheyuan"))))) % (10**9)
                        daily_run = True
                        daily_seed_used = int(seed)
                        # persist last date
                        d = cfg.get("daily")
                        if not isinstance(d, dict):
                            d = {}
                        d["seed"] = int(seed)
                        d["last_date"] = today
                        cfg["daily"] = d
                        save_config(cfg)
                        players, obstacles, items, flying_obstacles = reset_game(players, obstacles, items, flying_obstacles, resources)

                elif game_state == GameState.GAME_OVER:
                    restart_rect = draw_game_over(screen, resources, mouse_pos)
                    if restart_rect.collidepoint(event.pos):
                        pygame.mixer.music.stop()
                        if resources.get('mode_select_music_loaded', False):
                            _play_mode_select_music(resources)
                        game_state = GameState.MODE_SELECT
                        daily_run = False
                        daily_seed_used = 0
                        # Save high score (保存最高分)
                        if score > high_score:
                            high_score = score
                            config = load_config()
                            config["high_score"] = high_score
                            save_config(config)
                elif game_state == GameState.PAUSED:
                    menu_rect, codex_rect = draw_pause_screen(screen, resources, mouse_pos)
                    if codex_rect.collidepoint(event.pos):
                        game_state = GameState.CODEX
                    elif menu_rect.collidepoint(event.pos):
                        pygame.mixer.music.stop()
                        if resources.get('mode_select_music_loaded', False):
                            _play_mode_select_music(resources)
                        game_state = GameState.MODE_SELECT
                elif game_state == GameState.CODEX:
                    # 滚轮在部分环境下会产生 button 4/5 的 MOUSEBUTTONDOWN，不得当作左键点卡片
                    if event.button in (4, 5) and codex_view_mode == "list":
                        step = 72
                        if event.button == 4:
                            codex_scroll_y = max(0, codex_scroll_y - step)
                        else:
                            codex_scroll_y = min(_codex_list_max_scroll(), codex_scroll_y + step)
                    elif event.button == 1:
                        if codex_view_mode == "list":
                            cards, max_scroll = draw_codex_screen(
                                screen, resources, mouse_pos, scroll_y=codex_scroll_y
                            )
                            codex_scroll_y = max(0, min(int(codex_scroll_y), int(max_scroll)))
                            for entry_id, rect, unlocked in cards:
                                if unlocked and rect.collidepoint(event.pos):
                                    codex_selected_entry_id = entry_id
                                    codex_view_mode = "detail"
                                    codex_page_idx = 0
                                    break
                        else:
                            entry = next((e for e in CODEX_ENTRIES if e["id"] == codex_selected_entry_id), None)
                            if entry:
                                controls = draw_codex_detail(screen, resources, entry, codex_page_idx, mouse_pos)
                                if controls["back"].collidepoint(event.pos):
                                    codex_view_mode = "list"
                                elif controls["prev"].collidepoint(event.pos):
                                    codex_page_idx = max(0, codex_page_idx - 1)
                                elif controls["next"].collidepoint(event.pos):
                                    codex_page_idx = min(controls["total"] - 1, codex_page_idx + 1)
                elif game_state == GameState.SETTINGS:
                    controls = draw_settings_screen(screen, resources, mouse_pos)
                    cfg = load_config()
                    changed = False
                    if controls["hp_minus"].collidepoint(event.pos):
                        cfg["max_hp"] = max(1, int(cfg.get("max_hp", 3)) - 1)
                        changed = True
                    elif controls["hp_plus"].collidepoint(event.pos):
                        cfg["max_hp"] = min(6, int(cfg.get("max_hp", 3)) + 1)
                        changed = True
                    elif controls["jl_minus"].collidepoint(event.pos):
                        cfg["jump_level"] = max(1, int(cfg.get("jump_level", 1)) - 1)
                        changed = True
                    elif controls["jl_plus"].collidepoint(event.pos):
                        cfg["jump_level"] = min(4, int(cfg.get("jump_level", 1)) + 1)
                        changed = True
                    elif controls["mv_minus"].collidepoint(event.pos):
                        cfg["music_volume"] = max(0.0, round(float(cfg.get("music_volume", 0.7)) - 0.1, 2))
                        changed = True
                    elif controls["mv_plus"].collidepoint(event.pos):
                        cfg["music_volume"] = min(1.0, round(float(cfg.get("music_volume", 0.7)) + 0.1, 2))
                        changed = True
                    elif controls["fs_toggle"].collidepoint(event.pos):
                        cfg["fullscreen"] = not bool(cfg.get("fullscreen", False))
                        changed = True
                    elif controls.get("tutorial_toggle") and controls["tutorial_toggle"].collidepoint(event.pos):
                        cfg["home_tutorial_enabled"] = not bool(cfg.get("home_tutorial_enabled", True))
                        changed = True
                    if changed:
                        save_config(cfg)
                        _apply_music_volume(cfg.get("music_volume", 0.7), resources)
                        screen = _apply_fullscreen(screen, bool(cfg.get("fullscreen", False)))
                elif game_state == GameState.LOADOUT:
                    controls = draw_loadout_screen(screen, resources, mouse_pos, scroll_y=loadout_scroll_y)
                    # clamp scroll (in case unlocked count changed)
                    try:
                        loadout_scroll_y = max(0, min(int(loadout_scroll_y), int(controls.get("max_scroll", 0))))
                    except Exception:
                        loadout_scroll_y = 0
                    cfg = load_config()
                    changed = False
                    if controls["back"].collidepoint(event.pos):
                        game_state = GameState.MODE_SELECT
                    elif controls["toggle"].collidepoint(event.pos):
                        ld = cfg.get("loadout")
                        if not isinstance(ld, dict):
                            ld = {"enabled": True, "slots": []}
                        ld["enabled"] = not bool(ld.get("enabled", True))
                        cfg["loadout"] = ld
                        changed = True
                    else:
                        # remove equipped by clicking slot
                        if not changed:
                            for idx, r in controls.get("slots", []):
                                if r.collidepoint(event.pos):
                                    ld = cfg.get("loadout")
                                    if not isinstance(ld, dict):
                                        ld = {"enabled": True, "slots": []}
                                    slots = ld.get("slots")
                                    if not isinstance(slots, list):
                                        slots = []
                                    if 0 <= int(idx) < len(slots):
                                        slots.pop(int(idx))
                                        ld["slots"] = slots
                                        cfg["loadout"] = ld
                                        changed = True
                                    break
                        # add/remove by clicking skill
                        if not changed:
                            for sid, r in controls.get("skills", []):
                                if r.collidepoint(event.pos):
                                    ld = cfg.get("loadout")
                                    if not isinstance(ld, dict):
                                        ld = {"enabled": True, "slots": []}
                                    slots = ld.get("slots")
                                    if not isinstance(slots, list):
                                        slots = []
                                    if sid in slots:
                                        slots = [s for s in slots if s != sid]
                                    else:
                                        if len(slots) < 6:
                                            slots.append(sid)
                                    ld["slots"] = slots
                                    cfg["loadout"] = ld
                                    changed = True
                                    break
                    if changed:
                        save_config(cfg)
                elif game_state == GameState.SHOP:
                    controls = draw_skill_shop(screen, resources, mouse_pos, scroll_y=shop_scroll_y)
                    try:
                        max_sc = int(controls.get("max_scroll", 0))
                    except Exception:
                        max_sc = 0
                    shop_scroll_y = max(0, min(int(shop_scroll_y), max_sc))
                    # 滚轮在部分环境下会产生 button 4/5 的 MOUSEBUTTONDOWN，只作列表滚动，不得当作左键购买
                    if event.button in (4, 5):
                        step = 72
                        if event.button == 4:
                            shop_scroll_y = max(0, shop_scroll_y - step)
                        else:
                            shop_scroll_y = min(max_sc, shop_scroll_y + step)
                    elif event.button == 1:
                        cfg = load_config()
                        changed = False
                        if controls["back"].collidepoint(event.pos):
                            game_state = GameState.MODE_SELECT
                        elif controls.get("reset") and controls["reset"].collidepoint(event.pos):
                            # One-click reset purchased/unlocked skills (and equipped list)
                            cfg["unlock_skills"] = {}
                            ld = cfg.get("loadout")
                            if not isinstance(ld, dict):
                                ld = {"enabled": True, "slots": []}
                            ld["slots"] = []
                            cfg["loadout"] = ld
                            cfg["skill_shards"] = INITIAL_SKILL_SHARDS
                            hud_toast["text"] = "已重置：清空已购买技能/已装备/碎片"
                            hud_toast["until_ms"] = pygame.time.get_ticks() + 1600
                            changed = True
                        else:
                            for sid, r in controls.get("buy", []):
                                if r.collidepoint(event.pos):
                                    shards = int(cfg.get("skill_shards", 0))
                                    if shards >= 1:
                                        us = cfg.get("unlock_skills")
                                        if not isinstance(us, dict):
                                            us = {}
                                        if sid not in us:
                                            us[sid] = 1
                                        cfg["unlock_skills"] = us
                                        cfg["skill_shards"] = shards - 1
                                        # Auto-equip to loadout if there is space (购买后自动加入装备栏，避免“买了但装备里没有”的困惑)
                                        ld = cfg.get("loadout")
                                        if not isinstance(ld, dict):
                                            ld = {"enabled": True, "slots": []}
                                        slots = ld.get("slots")
                                        if not isinstance(slots, list):
                                            slots = []
                                        if isinstance(sid, str) and sid in SKILLS and sid not in slots and len(slots) < 6:
                                            slots.append(sid)
                                            ld["slots"] = slots
                                            cfg["loadout"] = ld
                                            hud_toast["text"] = f"购买成功并已装备：{SKILLS.get(sid, {}).get('name', sid)}"
                                        else:
                                            hud_toast["text"] = f"购买成功：{SKILLS.get(sid, {}).get('name', sid)}"
                                        hud_toast["until_ms"] = pygame.time.get_ticks() + 1600
                                        changed = True
                                    else:
                                        hud_toast["text"] = "碎片不足（需要 1）"
                                        hud_toast["until_ms"] = pygame.time.get_ticks() + 1200
                                    break
                        if changed:
                            save_config(cfg)
                elif game_state == GameState.DECRYPT:
                    # left click only
                    if getattr(event, "button", 1) != 1:
                        pass
                    else:
                        controls = draw_decrypt_screen(screen, resources, mouse_pos)
                        # theme pills
                        for tk, tr in controls.get("themes", []):
                            if tr.collidepoint(event.pos):
                                decrypt_theme = tk
                                decrypt_current = None
                                decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                                break

                        if controls.get("view") == "result":
                            _decrypt_best_update(decrypt_score)
                            if controls["back"].collidepoint(event.pos):
                                game_state = GameState.MODE_SELECT
                            elif controls["retry"].collidepoint(event.pos):
                                decrypt_stats = {"correct": 0, "total": 0}
                                decrypt_current = None
                                decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                                decrypt_view = "quiz"
                                decrypt_streak = 0
                                decrypt_score = 0
                                decrypt_wrong_scroll_y = 0
                                decrypt_start_ms = None
                            elif controls["wrongbook"].collidepoint(event.pos):
                                decrypt_view = "wrongbook"
                        elif controls.get("view") == "wrongbook":
                            if controls["back"].collidepoint(event.pos):
                                decrypt_view = "quiz"
                                decrypt_current = None
                                decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                                decrypt_pool_mode = "all"
                            elif controls["clear"].collidepoint(event.pos):
                                cfg = load_config()
                                cfg["decrypt_wrong"] = []
                                save_config(cfg)
                                decrypt_wrong_scroll_y = 0
                            elif controls.get("practice") and controls["practice"].collidepoint(event.pos):
                                # practice wrongbook only
                                decrypt_pool_mode = "wrong"
                                decrypt_stats = {"correct": 0, "total": 0}
                                decrypt_current = None
                                decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                                decrypt_view = "quiz"
                                decrypt_streak = 0
                                decrypt_score = 0
                                decrypt_wrong_scroll_y = 0
                                decrypt_start_ms = None
                            else:
                                for key, r in controls.get("items", []):
                                    if r.collidepoint(event.pos):
                                        decrypt_view = "quiz"
                                        qobj = next((q for q in DECRYPT_QUESTIONS if _decrypt_question_key(q) == key), None)
                                        decrypt_current = qobj if qobj else None
                                        decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                                        decrypt_pool_mode = "all"
                                        break
                        else:
                            if controls["back"].collidepoint(event.pos):
                                game_state = GameState.MODE_SELECT
                            elif controls["wrongbook"].collidepoint(event.pos):
                                decrypt_view = "wrongbook"
                            elif controls["next"].collidepoint(event.pos):
                                # if locked (revealing), ignore manual next
                                if not (decrypt_choice_idx is not None and decrypt_lock_until_ms and pygame.time.get_ticks() < decrypt_lock_until_ms):
                                    decrypt_current = None
                                    decrypt_feedback = {"text": "", "until_ms": 0, "is_correct": None}
                            else:
                                for i, r in enumerate(controls.get("options", [])):
                                    if r.collidepoint(event.pos):
                                        # lock while revealing answer
                                        if decrypt_choice_idx is not None and decrypt_lock_until_ms and pygame.time.get_ticks() < decrypt_lock_until_ms:
                                            break
                                        ans = int(decrypt_current.get("answer", 0)) if decrypt_current else 0
                                        decrypt_choice_idx = i
                                        decrypt_stats["total"] += 1
                                        ok = (i == ans)
                                        now_ms = pygame.time.get_ticks()
                                        if ok:
                                            decrypt_stats["correct"] += 1
                                            decrypt_streak += 1
                                            decrypt_score += 100 + min(80, decrypt_streak * 10)
                                            # always grant shards so progress is visible
                                            try:
                                                cfg = load_config()
                                                cfg["skill_shards"] = int(cfg.get("skill_shards", 0)) + 1
                                                save_config(cfg)
                                            except Exception:
                                                pass
                                            _decrypt_reward_toast("正确！+技能碎片 1", True)
                                            # more frequent unlock/upgrade
                                            if decrypt_streak > 0 and decrypt_streak % 2 == 0:
                                                _decrypt_apply_reward(now_ms)
                                        else:
                                            decrypt_streak = 0
                                            _decrypt_record_wrong(decrypt_current or {})
                                            _decrypt_reward_toast("不对哦：已加入错题本", False)
                                        # reveal for a moment, then auto next
                                        decrypt_lock_until_ms = now_ms + 1400
                                        decrypt_auto_next_ms = now_ms + 1400
                                        break
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == GameState.PLAYING:
                        pygame.mixer.music.stop()
                        if resources.get('mode_select_music_loaded', False):
                            _play_mode_select_music(resources)
                        game_state = GameState.MODE_SELECT
                        # Save high score (保存最高分)
                        if score > high_score:
                            high_score = score
                            config = load_config()
                            config["high_score"] = high_score
                            save_config(config)
                    else:
                        if game_state in (GameState.CODEX, GameState.SETTINGS, GameState.PAUSED):
                            if game_state == GameState.CODEX and codex_view_mode == "detail":
                                codex_view_mode = "list"
                            else:
                                game_state = GameState.MODE_SELECT
                        elif game_state == GameState.DECRYPT:
                            if decrypt_view != "quiz":
                                decrypt_view = "quiz"
                            else:
                                game_state = GameState.MODE_SELECT
                        else:
                            running = False
                elif event.key == pygame.K_i:
                    if game_state in (GameState.PLAYING, GameState.PAUSED, GameState.MODE_SELECT):
                        codex_return_state = game_state
                        codex_scroll_y = 0
                        codex_view_mode = "list"
                        codex_selected_entry_id = None
                        codex_page_idx = 0
                        game_state = GameState.CODEX
                    elif game_state == GameState.CODEX:
                        game_state = codex_return_state
                elif event.key in (pygame.K_UP, pygame.K_w):
                    if game_state == GameState.CODEX:
                        if codex_view_mode == "list":
                            codex_scroll_y = max(0, codex_scroll_y - 64)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if game_state == GameState.CODEX:
                        if codex_view_mode == "list":
                            codex_scroll_y = min(_codex_list_max_scroll(), codex_scroll_y + 64)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if game_state == GameState.CODEX and codex_view_mode == "detail":
                        codex_page_idx = max(0, codex_page_idx - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if game_state == GameState.CODEX and codex_view_mode == "detail":
                        entry = next((e for e in CODEX_ENTRIES if e["id"] == codex_selected_entry_id), None)
                        if entry:
                            codex_page_idx = min(max(0, len(entry.get("pages", [])) - 1), codex_page_idx + 1)
                elif game_state == GameState.DECRYPT and decrypt_view == "quiz":
                    # A/B/C/D quick answer
                    key_map = {
                        pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3,
                        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
                    }
                    if event.key in key_map:
                        now_ms = pygame.time.get_ticks()
                        if not (decrypt_choice_idx is not None and decrypt_lock_until_ms and now_ms < decrypt_lock_until_ms):
                            i = int(key_map[event.key])
                            ans = int(decrypt_current.get("answer", 0)) if decrypt_current else 0
                            decrypt_choice_idx = i
                            decrypt_stats["total"] += 1
                            ok = (i == ans)
                            if ok:
                                decrypt_stats["correct"] += 1
                                decrypt_streak += 1
                                decrypt_score += 100 + min(80, decrypt_streak * 10)
                                try:
                                    cfg = load_config()
                                    cfg["skill_shards"] = int(cfg.get("skill_shards", 0)) + 1
                                    save_config(cfg)
                                except Exception:
                                    pass
                                _decrypt_reward_toast("正确！+技能碎片 1", True)
                                if decrypt_streak > 0 and decrypt_streak % 2 == 0:
                                    _decrypt_apply_reward(now_ms)
                            else:
                                decrypt_streak = 0
                                _decrypt_record_wrong(decrypt_current or {})
                                _decrypt_reward_toast("不对哦：已加入错题本", False)
                            decrypt_lock_until_ms = now_ms + 1400
                            decrypt_auto_next_ms = now_ms + 1400
                # 暂停键不再依赖 KEYDOWN（输入法可能吞键）；见下方每帧按键状态检测
                for p in players:
                    if event.key == p.jump_key:
                        p.jump()
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        p.crouch(True)
            if event.type == pygame.KEYUP:
                for p in players:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        p.crouch(False)
            if event.type == pygame.MOUSEBUTTONUP and game_state == GameState.PLAYING:
                for p in players:
                    if event.button == p.jump_button:
                        p.jump()

        # ---- IME-safe pause toggle (按键状态边沿触发) ----
        try:
            keys = pygame.key.get_pressed()
            p_pressed = bool(keys[pygame.K_p])
        except Exception:
            p_pressed = False
        if p_pressed and not prev_p_pressed:
            if game_state == GameState.PLAYING:
                game_state = GameState.PAUSED
                try:
                    pygame.mixer.music.pause()
                except Exception:
                    pass
            elif game_state == GameState.PAUSED:
                game_state = GameState.PLAYING
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    pass
        prev_p_pressed = p_pressed

        if game_state == GameState.PLAYING:
            # passive: slowmo reduces overall speed slightly
            if "slowmo" in run_equipped_skills:
                slv = int(run_skill_levels.get("slowmo", 1))
                mul = 1.0 - min(0.22, 0.06 + (slv - 1) * 0.04)
                speed = max(3.0, float(speed) * mul)

            # ---- events & boss waves (节奏变化) ----
            if now_ms >= int(run_event.get("next_ms", 0)):
                # choose event with bias by theme
                theme = building_theme
                pool = ["wind", "rain", "collapse", "chase"]
                if theme == "bridge":
                    pool += ["wind"]
                if theme == "yamen":
                    pool += ["chase", "chase"]
                if theme == "palace":
                    pool += ["rain"]
                et = random.choice(pool)
                dur = 9000
                if et in ("wind", "rain"):
                    dur = 11000
                run_event["type"] = et
                run_event["until_ms"] = now_ms + dur
                run_event["next_ms"] = now_ms + 26000
                hud_toast["text"] = {"wind": "事件：穿堂风（速度降低）", "rain": "事件：风雨骤至（障碍更密）", "collapse": "事件：坍塌波（连发障碍）", "chase": "事件：巡卫追击（卫兵增援）"}.get(et, "事件到来")
                hud_toast["until_ms"] = now_ms + 1800

            # boss wave: periodic spike challenge
            if now_ms >= int(run_event.get("boss_next_ms", 0)):
                run_event["boss_next_ms"] = now_ms + 42000
                hud_toast["text"] = "波次：机关爆发！"
                hud_toast["until_ms"] = now_ms + 1600
                # spawn a burst of hazards (non-lethal if dash is ready)
                try:
                    obstacles.append(Obstacle(resources, "tall_cactus"))
                    obstacles.append(Obstacle(resources, "rock"))
                    if random.random() < 0.45:
                        obstacles.append(Obstacle(resources, "wood_frame"))
                    flying_obstacles.append(FlyingObstacle(resources, "daodan"))
                except Exception:
                    pass

            # apply event modifiers
            et = run_event.get("type", "")
            if et and now_ms >= int(run_event.get("until_ms", 0)):
                run_event["type"] = ""
            et = run_event.get("type", "")
            event_speed_mul = 1.0
            event_spawn_mul = 1.0
            if et == "wind":
                event_speed_mul = 0.86
            elif et == "rain":
                event_spawn_mul = 0.78
            elif et == "collapse":
                event_spawn_mul = 0.64
            elif et == "chase":
                # occasionally add a guard
                if building_theme == "yamen" and random.random() < 0.02:
                    patrol_guards.append(PatrolGuard())
                event_spawn_mul = 0.84

            speed = max(3.0, float(speed) * event_speed_mul)
            screen.fill(SKY_BLUE)
            draw_background(screen, resources)

            # ---- run goal progress: survive time (no damage) ----
            survive_s = int(max(0, (now_ms - int(run_start_ms or now_ms)) / 1000))
            for g in run_goals:
                if g.get("id") == "survive" and not g.get("done"):
                    g["progress"] = survive_s

            # --- Game Logic Updates ---
            spawn_timer += dt
            item_spawn_timer += dt
            collectible_spawn_timer += dt

            architecture_spawn_timer += dt
            if architecture_spawn_timer >= ARCHITECTURE_SPAWN_INTERVAL_MS:
                architecture_spawn_timer = 0
                _spawn_architecture_for_theme(building_theme, resources)
            
            # --- Adjust Game Logic by Mode ---
            if current_mode == SURVIVAL_MODE_ID: # Survival mode (生存模式)
                survival_mode_duration += dt / 1000.0
                
                # Base score (基础得分)
                score_float += float(dt) / 100.0
                score = int(score_float)
                
                # Survival bonus (生存奖励)
                if int(survival_mode_duration) % 10 == 0 and survival_mode_duration - int(survival_mode_duration) < 0.1:
                    score_float += 100.0
                    score = int(score_float)
                    
                # Obstacle spawn rate increases with time (障碍物生成频率随时间加快)
                base_interval = 1200
                speed_factor = max(0.3, 1.0 - (survival_mode_duration / 15.0) * 0.1)
                obstacle_spawn_interval = base_interval * speed_factor
                item_spawn_interval = 6000
                
                # BOSS wave challenge (BOSS波挑战)
                if survival_mode_duration >= survival_next_boss_wave:
                    survival_next_boss_wave += 30
                    
                    # Spawn multiple high-difficulty obstacles (生成多个高难度障碍物)
                    obstacles.append(Obstacle(resources, "tall_cactus"))
                    obstacles.append(Obstacle(resources, "rock"))
                    flying_obstacles.append(FlyingObstacle(resources, "daodan"))
                    flying_obstacles.append(FlyingObstacle(resources, "daodan"))
                    
                    # Show BOSS wave prompt (显示BOSS波提示)
                    boss_text = resources['font'].render("首领来袭！", True, RED)
                    screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 50))
                    pygame.display.flip()
                    pygame.time.wait(1000)
                    
            else: # Traditional modes (传统模式)
                obstacle_spawn_interval = max(1000, 3000 - (current_level * 200))
                item_spawn_interval = float('inf')  # No items in traditional modes (传统模式不生成道具)

                # Score and level up (得分和等级提升)
                score_float += float(dt) / 50.0
                score = int(score_float)
                check_level_up()

            # event spawn density modifier (全模式生效)
            try:
                et = run_event.get("type", "")
            except Exception:
                et = ""
            if et == "rain":
                obstacle_spawn_interval *= 0.78
            elif et == "collapse":
                obstacle_spawn_interval *= 0.64
            elif et == "chase":
                obstacle_spawn_interval *= 0.84

            # Spawn obstacles (生成障碍物)
            if spawn_timer > obstacle_spawn_interval:
                spawn_timer = 0
                if current_mode != SURVIVAL_MODE_ID:
                    # add a small chance to spawn cultural-mechanic wood frame
                    if random.random() < 0.18:
                        obstacles.append(Obstacle(resources, "wood_frame"))
                    else:
                        obstacles.append(Obstacle(resources))
                    if random.random() < 0.3 + (current_level * 0.05):
                        flying_obstacles.append(FlyingObstacle(resources))
                else: # Survival mode (生存模式)
                    if random.random() < 0.4:
                        if random.random() < 0.16:
                            obstacles.append(Obstacle(resources, "wood_frame"))
                        else:
                            obstacles.append(Obstacle(resources))
                    else:
                        if random.random() < 0.25:
                            flying_obstacles.append(FlyingObstacle(resources, "daodan"))
                        else:
                            flying_obstacles.append(FlyingObstacle(resources))

            # Spawn items (only survival mode) (生成道具)
            if current_mode == SURVIVAL_MODE_ID and item_spawn_timer > item_spawn_interval:
                item_spawn_timer = 0
                items.append(Item(resources))

            # Spawn cultural collectibles (所有模式都生成文化收集物)
            # 让文化“进到循环里”，而不是背景贴图
            cultural_interval = 4200 if current_mode != SURVIVAL_MODE_ID else 3800
            if collectible_spawn_timer > cultural_interval:
                collectible_spawn_timer = 0
                # 调整权重：木构件更常见，保证“木架拆解”机制能经常触发
                r = random.random()
                if r < 0.38:
                    ct = CollectibleType.WADANG
                elif r < 0.68:
                    ct = CollectibleType.DOUGONG
                else:
                    ct = CollectibleType.WOOD
                collectibles.append(Collectible(resources, ct))

            # Update all objects (更新所有对象)
            for obs in obstacles: 
                obs.update()
            for item in items: 
                item.update()
            for c in collectibles:
                c.update()
            # passive: magnet skill pulls collectibles closer
            if "magnet" in run_equipped_skills and players:
                mag_lv = int(run_skill_levels.get("magnet", 1))
                radius = 160 + mag_lv * 70
                pull = 0.06 + mag_lv * 0.03
                px = float(players[0].x + players[0].width / 2)
                py = float(players[0].y + players[0].height / 2)
                for c in collectibles:
                    if getattr(c, "collected", False):
                        continue
                    cx, cy = c.get_center()
                    dx = px - float(cx)
                    dy = py - float(cy)
                    dist2 = dx * dx + dy * dy
                    if dist2 <= float(radius * radius):
                        c.x += dx * pull
                        c.y += dy * pull
            for obs in flying_obstacles: 
                obs.update(players[0].y if players else 0)

            for plat in architecture_platforms:
                plat.update()
            for g in patrol_guards:
                g.update(dt)

            for p in players:
                p.update(dt, architecture_platforms)

            def _feet_on_rect(player, rect_top: float, pr: pygame.Rect) -> bool:
                h0 = player.crouch_height if player.is_crouching else player.normal_height
                bottom = player.y + h0
                feet_l = player.x + 12
                feet_r = player.x + player.width - 12
                return (
                    feet_r > pr.x and feet_l < pr.right and abs(bottom - rect_top) <= 8
                )

            for plat in architecture_platforms:
                if plat.kind != "bridge" or plat.broken:
                    continue
                pr = plat.get_rect()
                any_on = any(_feet_on_rect(p, float(pr.y), pr) for p in players)
                plat.register_standing(dt, any_on)

            # Collision detection (碰撞检测)
            game_over_triggered = False
            # passive runtime refresh
            if "dash" in run_equipped_skills:
                dash_lv = int(run_skill_levels.get("dash", 1))
                # cooldown decreases with level
                cd = 20000 - min(8000, (dash_lv - 1) * 4000)
                if now_ms >= int(run_skill_runtime.get("dash_next_ready_ms", 0)) and int(run_skill_runtime.get("dash_charges", 0)) <= 0:
                    run_skill_runtime["dash_charges"] = 1
                    run_skill_runtime["dash_next_ready_ms"] = now_ms + cd

            for i, p in enumerate(players):
                p_hitbox = p.get_hitbox()
                
                # Collision with ground obstacles (与地面障碍物碰撞)
                for obs in obstacles[:]:
                    if p_hitbox.colliderect(obs.get_hitbox()):
                        # Cultural rule: 木结构可被“木构件”拆解通过
                        if obs.type == "wood_frame" and cultural_counts[CollectibleType.WOOD] > 0:
                            cultural_counts[CollectibleType.WOOD] -= 1
                            obstacles.remove(obs)
                            score_float += 60.0
                            score = int(score_float)
                            hud_toast["text"] = "使用木构件拆解木架机关 +60"
                            hud_toast["until_ms"] = now_ms + 1500
                            _persist_cultural_to_config()
                        else:
                            # dash: consume one charge to ignore a hit
                            if int(run_skill_runtime.get("dash_charges", 0)) > 0:
                                run_skill_runtime["dash_charges"] = 0
                                run_skill_runtime["invul_until_ms"] = now_ms + 900
                                try:
                                    obstacles.remove(obs)
                                except Exception:
                                    pass
                                hud_toast["text"] = "技能「冲刺」护身触发！"
                                hud_toast["until_ms"] = now_ms + 1100
                                continue
                            if p.take_damage():
                                game_over_triggered = True
                                break
                            else:
                                obstacles.remove(obs)
                if game_over_triggered: 
                    break

                for g in patrol_guards[:]:
                    if p_hitbox.colliderect(g.get_hitbox()):
                        if p.take_damage():
                            game_over_triggered = True
                            break
                        patrol_guards.remove(g)
                if game_over_triggered:
                    break
                
                # Collision with flying obstacles (与飞行障碍物碰撞)
                for obs in flying_obstacles[:]:
                    if p_hitbox.colliderect(obs.get_hitbox()):
                        if int(run_skill_runtime.get("dash_charges", 0)) > 0:
                            run_skill_runtime["dash_charges"] = 0
                            run_skill_runtime["invul_until_ms"] = now_ms + 900
                            try:
                                flying_obstacles.remove(obs)
                            except Exception:
                                pass
                            hud_toast["text"] = "技能「冲刺」护身触发！"
                            hud_toast["until_ms"] = now_ms + 1100
                            continue
                        if p.take_damage():
                            game_over_triggered = True
                            break
                        else:
                            flying_obstacles.remove(obs)
                if game_over_triggered: 
                    break
                
                # Collect items (only survival mode) (收集道具)
                if current_mode == SURVIVAL_MODE_ID:
                    for item in items[:]:
                        if p_hitbox.collidepoint(item.x + item.width//2, item.y + item.height//2):
                            item.collected = True
                            items.remove(item)
                            p.add_item(item.type)

                # Collect cultural collectibles (文化收集物)
                for c in collectibles[:]:
                    cx, cy = c.get_center()
                    if p_hitbox.collidepoint(cx, cy):
                        c.collected = True
                        collectibles.remove(c)
                        cultural_counts[c.type] += 1
                        _persist_cultural_to_config()
                        _maybe_unlock_codex(now_ms)
                        for g in run_goals:
                            if g.get("id") == "collect_parts" and not g.get("done"):
                                g["progress"] = int(g.get("progress", 0)) + 1

            # Game over handling (游戏结束处理)
            if game_over_triggered:
                pygame.mixer.music.stop()
                if resources.get('mode_select_music_loaded', False):
                    _stop_mode_select_music(resources)
                if score > high_score:
                    high_score = score
                    config = load_config()
                    config["high_score"] = high_score
                    save_config(config)
                # daily best record
                if daily_run and daily_seed_used:
                    try:
                        cfg = load_config()
                        d = cfg.get("daily")
                        if not isinstance(d, dict):
                            d = {}
                        best = int(d.get("best", 0)) if str(d.get("best", "0")).lstrip("-").isdigit() else 0
                        if score > best:
                            d["best"] = int(score)
                            cfg["daily"] = d
                            save_config(cfg)
                    except Exception:
                        pass
                game_state = GameState.GAME_OVER
            else:
                # goals completion & rewards
                for g in run_goals:
                    if g.get("done"):
                        continue
                    try:
                        prog = int(g.get("progress", 0))
                        tgt = int(g.get("target", 1))
                    except Exception:
                        prog, tgt = 0, 1
                    if tgt <= 0:
                        tgt = 1
                    if prog >= tgt:
                        g["done"] = True
                        # reward: shards + score
                        try:
                            score_float += float(g.get("reward_score", 0))
                            score = int(score_float)
                        except Exception:
                            pass
                        try:
                            cfg = load_config()
                            cfg["skill_shards"] = int(cfg.get("skill_shards", 0)) + int(g.get("reward_shards", 0))
                            save_config(cfg)
                        except Exception:
                            pass
                        hud_toast["text"] = f"目标完成：{g.get('name','')} +碎片{int(g.get('reward_shards',0))}"
                        hud_toast["until_ms"] = now_ms + 1800
            # restore base speed (avoid permanent drift)
            speed = base_speed
            
            # Remove off-screen objects (移除屏幕外的对象)
            obstacles = [obs for obs in obstacles if obs.x + obs.width > 0]
            items = [item for item in items if item.x + item.width > 0 and not item.collected]
            collectibles = [c for c in collectibles if c.x + c.width > 0 and not c.collected]
            flying_obstacles = [obs for obs in flying_obstacles if not obs.is_off_screen()]
            architecture_platforms[:] = [
                pl for pl in architecture_platforms if pl.x + pl.width > -80
            ]
            patrol_guards[:] = [g for g in patrol_guards if g.x + g.width > -80]

            # Draw all objects (绘制所有对象)
            for obs in obstacles: 
                obs.draw(screen, resources)
            for pl in architecture_platforms:
                pl.draw(screen, resources)
            for g in patrol_guards:
                g.draw(screen, resources)
            for item in items: 
                item.draw(screen, resources)
            for c in collectibles:
                c.draw(screen, resources)
            for obs in flying_obstacles: 
                obs.draw(screen)
            for p in players: 
                p.draw(screen, resources)

            # Draw HUD (绘制HUD)
            score_text = resources['font'].render(f"得分：{score}", True, BLACK)
            screen.blit(score_text, (10, 10))
            draw_building_theme_hud(screen, resources)
            draw_cultural_hud(screen, resources)
            draw_skill_hud(screen, resources)
            draw_toast(screen, resources, now_ms)
            
            if current_mode == SURVIVAL_MODE_ID:
                # Survival mode HUD (生存模式HUD)
                time_text = resources['font'].render(f"时间：{survival_mode_duration:.1f}s", True, RED)
                screen.blit(time_text, (WIDTH - time_text.get_width() - 10, 10))
                
                # Health bar (生命值条)
                health_bar_width = 150
                health_bar_height = 20
                health_ratio = players[0].health / max(1, getattr(players[0], "max_health", 3))
                pygame.draw.rect(screen, (200, 200, 200), (10, 50, health_bar_width, health_bar_height), border_radius=5)
                pygame.draw.rect(screen, (255 - int(health_ratio * 255), int(health_ratio * 255), 0), 
                               (10, 50, health_bar_width * health_ratio, health_bar_height), border_radius=5)
                mh = getattr(players[0], "max_health", 3)
                health_text = resources['small_font'].render(f"生命：{players[0].health}/{mh}", True, BLACK)
                screen.blit(health_text, (10 + health_bar_width + 10, 50))
                
                # Shield display (护盾显示)
                if players[0].shields > 0:
                    shield_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(shield_icon, (100, 150, 255, 200), (15, 15), 15)
                    pygame.draw.circle(shield_icon, (255, 255, 255, 255), (15, 15), 15, 2)
                    screen.blit(shield_icon, (10, 90))
                    shield_text = resources['small_font'].render(f"x{players[0].shields}", True, BLACK)
                    screen.blit(shield_text, (45, 95))
                    
                # Next BOSS wave timer (下一波BOSS倒计时)
                boss_timer = max(0, survival_next_boss_wave - survival_mode_duration)
                if boss_timer <= 10:
                    boss_text = resources['font'].render(f"下一波首领：{boss_timer:.0f}s", True, ORANGE)
                    screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 10))
            else:
                # Traditional mode HUD (传统模式HUD)
                level_text = resources['font'].render(f"Level: {current_level}", True, BLACK)
                screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))

        elif game_state == GameState.MODE_SELECT:
            ui_rects = draw_mode_select(screen, resources, mouse_pos)
            while len(ui_rects) < 19:
                ui_rects = draw_mode_select(screen, resources, mouse_pos)
            one_player_rect, two_player_rect, three_player_rect, survival_rect = ui_rects[:4]
            theme_scene_rects = ui_rects[4:8]
            start_rect, daily_rect, settings_btn_rect, codex_home_rect, decrypt_home_rect, loadout_home_rect, shop_home_rect, menu_music_rect, tutorial_ok_rect, tutorial_prev_rect, tutorial_next_rect = ui_rects[8:19]

        elif game_state == GameState.GAME_OVER:
            restart_rect = draw_game_over(screen, resources, mouse_pos)
        elif game_state == GameState.PAUSED:
            # 暂停时先绘制游戏画面，再绘制暂停界面
            draw_background(screen, resources)
            for obs in obstacles:
                obs.draw(screen, resources)
            for pl in architecture_platforms:
                pl.draw(screen, resources)
            for g in patrol_guards:
                g.draw(screen, resources)
            for obs in flying_obstacles:
                obs.draw(screen)
            for item in items:
                item.draw(screen, resources)
            for c in collectibles:
                c.draw(screen, resources)
            for p in players:
                p.draw(screen, resources)
            
            # 绘制UI元素
            score_text = resources['font'].render(f"得分：{score}", True, BLACK)
            screen.blit(score_text, (10, 10))
            draw_building_theme_hud(screen, resources)
            draw_cultural_hud(screen, resources)
            draw_skill_hud(screen, resources)
            draw_toast(screen, resources, now_ms)
            
            if current_mode == SURVIVAL_MODE_ID:
                # Survival mode HUD (生存模式HUD)
                time_text = resources['font'].render(f"时间：{survival_mode_duration:.1f}s", True, RED)
                screen.blit(time_text, (WIDTH - time_text.get_width() - 10, 10))
                
                # Health bar (生命值条)
                health_bar_width = 150
                health_bar_height = 20
                health_ratio = players[0].health / max(1, getattr(players[0], "max_health", 3))
                pygame.draw.rect(screen, (200, 200, 200), (10, 50, health_bar_width, health_bar_height), border_radius=5)
                pygame.draw.rect(screen, (255 - int(health_ratio * 255), int(health_ratio * 255), 0), 
                               (10, 50, health_bar_width * health_ratio, health_bar_height), border_radius=5)
                mh = getattr(players[0], "max_health", 3)
                health_text = resources['small_font'].render(f"生命：{players[0].health}/{mh}", True, BLACK)
                screen.blit(health_text, (10 + health_bar_width + 10, 50))
                
                # Shield display (护盾显示)
                if players[0].shields > 0:
                    shield_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(shield_icon, (100, 150, 255, 200), (15, 15), 15)
                    pygame.draw.circle(shield_icon, (255, 255, 255, 255), (15, 15), 15, 2)
                    screen.blit(shield_icon, (10, 90))
                    shield_text = resources['small_font'].render(f"x{players[0].shields}", True, BLACK)
                    screen.blit(shield_text, (45, 95))
                    
                # Next BOSS wave timer (下一波BOSS倒计时)
                boss_timer = max(0, survival_next_boss_wave - survival_mode_duration)
                if boss_timer <= 10:
                    boss_text = resources['font'].render(f"下一波首领：{boss_timer:.0f}s", True, ORANGE)
                    screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 10))
            else:
                # Traditional mode HUD (传统模式HUD)
                level_text = resources['font'].render(f"Level: {current_level}", True, BLACK)
                screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))
            
            # 最后绘制暂停界面
            menu_rect, codex_rect = draw_pause_screen(screen, resources, mouse_pos)

        elif game_state == GameState.CODEX:
            # show codex on top of last frame; keep simple by drawing background
            draw_background(screen, resources)
            for obs in obstacles:
                obs.draw(screen, resources)
            for pl in architecture_platforms:
                pl.draw(screen, resources)
            for g in patrol_guards:
                g.draw(screen, resources)
            for obs in flying_obstacles:
                obs.draw(screen)
            for item in items:
                item.draw(screen, resources)
            for c in collectibles:
                c.draw(screen, resources)
            for p in players:
                p.draw(screen, resources)
            draw_cultural_hud(screen, resources)
            draw_skill_hud(screen, resources)
            if codex_view_mode == "list":
                _, max_scroll = draw_codex_screen(screen, resources, mouse_pos, scroll_y=codex_scroll_y)
                codex_scroll_y = max(0, min(int(codex_scroll_y), int(max_scroll)))
            else:
                entry = next((e for e in CODEX_ENTRIES if e["id"] == codex_selected_entry_id), None)
                if entry:
                    draw_codex_detail(screen, resources, entry, codex_page_idx, mouse_pos)
        elif game_state == GameState.SETTINGS:
            # settings overlay on top of mode select background
            draw_mode_select(screen, resources, mouse_pos)
            draw_settings_screen(screen, resources, mouse_pos)
        elif game_state == GameState.LOADOUT:
            # loadout overlay on top of mode select background
            draw_mode_select(screen, resources, mouse_pos)
            controls = draw_loadout_screen(screen, resources, mouse_pos, scroll_y=loadout_scroll_y)
            try:
                loadout_scroll_y = max(0, min(int(loadout_scroll_y), int(controls.get("max_scroll", 0))))
            except Exception:
                loadout_scroll_y = 0
        elif game_state == GameState.SHOP:
            # shop overlay on top of mode select background
            draw_mode_select(screen, resources, mouse_pos)
            controls = draw_skill_shop(screen, resources, mouse_pos, scroll_y=shop_scroll_y)
            try:
                shop_scroll_y = max(0, min(int(shop_scroll_y), int(controls.get("max_scroll", 0))))
            except Exception:
                shop_scroll_y = 0
        elif game_state == GameState.DECRYPT:
            # decrypt overlay on top of mode select background
            draw_mode_select(screen, resources, mouse_pos)
            draw_decrypt_screen(screen, resources, mouse_pos)

        pygame.display.flip()

    # Exit game (退出游戏)
    pygame.mixer.music.stop()
    if resources.get('mode_select_music_loaded', False):
        _stop_mode_select_music(resources)
    
    config = load_config()
    if score > high_score:
        config["high_score"] = score
        save_config(config)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
