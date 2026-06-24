"""
music_analysis.config — 全局超参数与常量

严格对应 formalization_v1.md 中的符号定义和默认约束值。
"""

from typing import Dict, Optional

# =============================================================================
# 窗口约束参数 (Section: 局部音乐事件序列)
# =============================================================================

L_MIN: int = 3         # 窗口最少事件数
L_MAX: int = 8         # 窗口最多事件数
D_MIN: float = 1.0     # 窗口最短时长 (quarter length)
D_MAX: float = 8.0     # 窗口最长时长 (quarter length)
B_MAX: int = 2         # 窗口最多跨越小节数

# 声部层过滤: 事件数 < MIN_VOICE_EVENTS 的层被视为编码噪声, 合并到同谱表主声部
MIN_VOICE_EVENTS: int = 20

# =============================================================================
# 特征距离权重 (Section: 商空间距离与主题相似度)
# =============================================================================

W_I: float = 0.5       # 音程序列距离权重
W_R: float = 0.3       # 归一化节奏距离权重
W_T: float = 0.2       # 归一化起始时间距离权重

# =============================================================================
# 压缩增益过滤参数 (Section: 压缩增益初筛)
# =============================================================================

# 参考编码成本 (用于压缩增益计算)
#   表示存储一个"位置引用"的信息代价 (≈ log2(total_possible_positions))
C_REF: float = 2.0

# 压缩增益阈值 — Ĝ_i > θ_G 的主题类型被保留
THETA_G: float = 0.0

# 主题重要性计算方式: 'linear' | 'log' | 'sqrt'
IMPORTANCE_MODE: str = "log"

# =============================================================================
# 主题网络边权超参数 (Section: 主题网络)
# =============================================================================

LAMBDA_SYM: float = 1.0    # 对称边权重
LAMBDA_TEMP: float = 0.5   # 时间邻接边权重

# =============================================================================
# 动态指标参数 (Section: 记忆激活函数 / 残余相干)
# =============================================================================

# τ_𝔇 由数据自动计算（median duration + median gap），此处设默认回退值
TAU_DEFAULT: float = 2.0

# 残余观察窗口倍数（相对于 τ_𝔇）
DELTA_T_MULTIPLIER: float = 2.0

# =============================================================================
# 力度映射表 (α_n: dynamics → MIDI velocity)
# =============================================================================

DYNAMICS_MAP: Dict[str, int] = {
    "ppp": 16,
    "pp": 32,
    "p": 48,
    "mp": 64,
    "mf": 80,
    "f": 96,
    "ff": 112,
    "fff": 127,
}

DYNAMICS_ORDER: list = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]


def dynamics_to_midi(dyn_str: Optional[str]) -> Optional[int]:
    """将力度记号映射为 MIDI velocity 数值，无法识别则返回 None。"""
    if dyn_str is None:
        return None
    return DYNAMICS_MAP.get(dyn_str.lower(), None)


def midi_to_dynamics(vel: int) -> str:
    """将 MIDI velocity 反向映射为最接近的力度记号。"""
    closest = min(DYNAMICS_MAP.items(), key=lambda kv: abs(kv[1] - vel))
    return closest[0]


# =============================================================================
# V4 群元素标签 (Section: 克莱因四元群)
# =============================================================================

V4_IDENTITY = "e"
V4_INVERSION = "I"
V4_RETROGRADE = "R"
V4_RETROGRADE_INVERSION = "RI"

V4_ELEMENTS: list = [V4_IDENTITY, V4_INVERSION, V4_RETROGRADE, V4_RETROGRADE_INVERSION]

# =============================================================================
# Tie 状态常量 (Section: tie 约束)
# =============================================================================

TIE_START = "start"
TIE_STOP = "stop"
TIE_CONTINUE = "continue"

# 窗口起点不允许的 tie 状态
TIE_INVALID_START: set = {TIE_CONTINUE, TIE_STOP}
# 窗口终点不允许的 tie 状态
TIE_INVALID_END: set = {TIE_START, TIE_CONTINUE}


# =============================================================================
# 文件路径
# =============================================================================

MXL_PATH: str = "BWV861_Prelude_G_minor.mxl"
DATA_DIR: str = "data"
NOTEBOOK_DIR: str = "notebooks"

# 中间数据文件
EVENTS_PKL: str = "data/events.pkl"
VOICE_LAYERS_PKL: str = "data/voice_layers.pkl"
WINDOWS_PKL: str = "data/windows.pkl"
FEATURES_PKL: str = "data/features.pkl"
MOTIFS_PKL: str = "data/motifs.pkl"
THEMES_PKL: str = "data/themes.pkl"
SIMILARITY_PKL: str = "data/similarity_matrix.pkl"
NETWORK_PKL: str = "data/theme_network.pkl"
DYNAMIC_METRICS_PKL: str = "data/dynamic_metrics.pkl"
