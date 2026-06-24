"""
features.py — 结构特征计算

从候选窗口 ω 中提取:
    单声部: P(ω), I(ω), R(ω), R̂(ω), T_start_ref(ω), T̂_start_ref(ω)
    多声部: {φ^λ}, V^{Λ'}(ω), C^{Λ'}(ω)

特征向量 φ(ω) = (P, I, R/R̂, T/T̂)
相对特征 φ_rel(ω) = (I, R̂, T̂_start_ref)  — 用于动机原型分析
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from . import config


# =============================================================================
# 单声部特征计算
# =============================================================================

def compute_single_voice_features(
    window: Dict[str, Any],
) -> Dict[str, Any]:
    """
    计算单声部窗口的结构特征。

    Returns dict with keys:
        'P'         — 绝对音高序列 (list of int)
        'I'         — 音程序列 (list of int)
        'R'         — 时值序列 (list of float)
        'R_hat'     — 归一化节奏 (list of float)
        'T_start_ref'   — 相对起始时间 (list of float)
        'T_hat_start_ref' — 归一化起始时间 (list of float)
        'L'         — 窗口长度
    """
    events = window["events"]
    L = len(events)

    # P(ω): 绝对音高
    P = [_pitch_or_zero(e["p_n"]) for e in events]

    # I(ω): 音程序列 Δp_k = p_{k+1} - p_k
    if L >= 2:
        I = [P[k+1] - P[k] for k in range(L-1)]
    else:
        I = []

    # R(ω): 时值序列
    R = [e["d_n"] for e in events]

    # R̂(ω): 归一化节奏 = d_j / Σ d_j
    total_dur = sum(R)
    if total_dur > 0:
        R_hat = [d / total_dur for d in R]
    else:
        R_hat = [0.0] * L

    # T_start_ref(ω): 相对起始时间 (以首音为 0)
    t0 = events[0]["t_n"]
    T_start_ref = [e["t_n"] - t0 for e in events]

    # T̂_start_ref(ω): 归一化起始时间 = T_start_ref / D(ω)
    D = window["D"]
    if D > 0:
        T_hat_start_ref = [t / D for t in T_start_ref]
    else:
        T_hat_start_ref = [0.0] * L

    features = {
        "P": P,
        "I": I,
        "R": R,
        "R_hat": R_hat,
        "T_start_ref": T_start_ref,
        "T_hat_start_ref": T_hat_start_ref,
        "L": L,
    }
    return features


def _pitch_or_zero(p: Optional[int]) -> int:
    """将 None 音高（休止符）转为 0 用于音程计算。"""
    return p if p is not None else 0


# =============================================================================
# 多声部特征计算
# =============================================================================

def compute_multi_voice_features(
    multi_window: Dict[str, Any],
) -> Dict[str, Any]:
    """
    计算多声部块窗口的扩展特征。

    Returns dict with:
        'features_by_layer' — Dict[λ, φ^λ]
        'V'                 — 纵向音程矩阵
        'C'                 — 声部进行关系矩阵
    """
    events_by_layer = multi_window.get("events_by_layer", {})
    lambda_set = multi_window["lambda_set"]

    # 各声部横向特征
    features_by_layer: Dict[Tuple, Dict] = {}
    for lam, layer_events in events_by_layer.items():
        temp_window = {
            "events": layer_events,
            "D": _compute_layer_D(layer_events),
            "time_interval": multi_window["time_interval"],
        }
        features_by_layer[lam] = compute_single_voice_features(temp_window)

    # 纵向音程 V^{Λ'}
    V = compute_vertical_intervals(multi_window)

    # 声部进行关系 C^{Λ'}
    C = compute_voice_leading(multi_window)

    features = {
        "features_by_layer": features_by_layer,
        "V": V,
        "C": C,
    }
    return features


def _compute_layer_D(layer_events: List[Dict[str, Any]]) -> float:
    """计算单声部事件序列的时间跨度。"""
    if not layer_events:
        return 0.0
    t_start = layer_events[0]["t_n"]
    last = layer_events[-1]
    return last["t_n"] + last["d_n"] - t_start


def compute_vertical_intervals(
    multi_window: Dict[str, Any],
) -> Dict[Tuple[str, str], List[Dict]]:
    """
    计算纵向音程 V_{λ_a,λ_b}(t)。

    对每个时间点和每对声部，计算有效发声音高的差值。

    Returns:
        Dict[(lam_a, lam_b), List[{'t': float, 'interval': float | None}]]
    """
    events_by_layer = multi_window.get("events_by_layer", {})
    lambda_set = list(events_by_layer.keys())
    V: Dict[Tuple, List] = {}

    # 收集所有时间点
    all_times: List[float] = []
    for events in events_by_layer.values():
        for e in events:
            all_times.append(e["t_n"])
    all_times = sorted(set(all_times))

    for i in range(len(lambda_set)):
        for j in range(i + 1, len(lambda_set)):
            lam_a = lambda_set[i]
            lam_b = lambda_set[j]
            key = (lam_a, lam_b)
            V[key] = []

            for t in all_times:
                p_a = _get_pitch_at_time(events_by_layer[lam_a], t)
                p_b = _get_pitch_at_time(events_by_layer[lam_b], t)
                if p_a is not None and p_b is not None:
                    interval = p_b - p_a
                else:
                    interval = None
                V[key].append({"t": t, "interval": interval})

    return V


def _get_pitch_at_time(
    events: List[Dict[str, Any]],
    t: float,
) -> Optional[int]:
    """
    获取声部在时刻 t 的有效发声音高。

    考虑音符持续区间 [t_n, t_n + d_n)，若 t 落在区间内则返回该音高。
    """
    best: Optional[int] = None
    for e in events:
        if e["p_n"] is None:
            continue
        if e["t_n"] <= t < e["t_n"] + e["d_n"]:
            best = e["p_n"]
    return best


def compute_voice_leading(
    multi_window: Dict[str, Any],
) -> Dict[Tuple[str, str], List[Dict]]:
    """
    计算声部进行关系 C_{λ_a,λ_b}(t)。

    对相邻时间点，计算 sgn(Δp_a) · sgn(Δp_b):
        +1 = 同向, -1 = 反向, 0 = 至少一个保持

    Returns:
        Dict[(lam_a, lam_b), List[{'t_from': float, 't_to': float, 'relation': int}]]
    """
    events_by_layer = multi_window.get("events_by_layer", {})
    lambda_set = list(events_by_layer.keys())
    C: Dict[Tuple, List] = {}

    # 时间点
    all_times: List[float] = []
    for events in events_by_layer.values():
        for e in events:
            all_times.append(e["t_n"])
    all_times = sorted(set(all_times))

    if len(all_times) < 2:
        return C

    for i in range(len(lambda_set)):
        for j in range(i + 1, len(lambda_set)):
            lam_a = lambda_set[i]
            lam_b = lambda_set[j]
            key = (lam_a, lam_b)
            C[key] = []

            for k in range(len(all_times) - 1):
                t_from = all_times[k]
                t_to = all_times[k + 1]

                p_a_from = _get_pitch_at_time(events_by_layer[lam_a], t_from)
                p_a_to = _get_pitch_at_time(events_by_layer[lam_a], t_to)
                p_b_from = _get_pitch_at_time(events_by_layer[lam_b], t_from)
                p_b_to = _get_pitch_at_time(events_by_layer[lam_b], t_to)

                if None in (p_a_from, p_a_to, p_b_from, p_b_to):
                    relation = 0
                else:
                    delta_a = p_a_to - p_a_from
                    delta_b = p_b_to - p_b_from
                    relation = int(np.sign(delta_a) * np.sign(delta_b))

                C[key].append({
                    "t_from": t_from,
                    "t_to": t_to,
                    "relation": relation,
                })

    return C


# =============================================================================
# 批量特征计算
# =============================================================================

def compute_all_features(
    single_windows: List[Dict[str, Any]],
    multi_windows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    为所有窗口计算特征并附加到窗口 dict 中。

    同时构建统一的特征列表供后续步骤使用。
    """
    all_features: List[Dict[str, Any]] = []

    print("正在计算单声部特征...")
    for w in single_windows:
        features = compute_single_voice_features(w)
        w["features"] = features
        all_features.append({
            "window": w,
            "features": features,
            "type": "single",
            "lambda": w["lambda"],
        })
    print(f"  ✅ {len(single_windows)} 个单声部窗口特征已计算")

    print("正在计算多声部特征...")
    for w in multi_windows:
        features = compute_multi_voice_features(w)
        w["features"] = features
        all_features.append({
            "window": w,
            "features": features,
            "type": "multi",
            "lambda_set": w["lambda_set"],
        })
    print(f"  ✅ {len(multi_windows)} 个多声部窗口特征已计算")

    return all_features


# =============================================================================
# 持久化
# =============================================================================

def save_features(
    features: List[Dict],
    single_windows: List[Dict],
    multi_windows: List[Dict],
) -> None:
    """持久化特征数据和更新后的窗口数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    with open(config.FEATURES_PKL, "wb") as f:
        pickle.dump(features, f)
    # 也更新窗口数据（包含特征）
    from .windows import save_windows
    save_windows(single_windows, multi_windows)
    print(f"✅ 特征数据已保存: {config.FEATURES_PKL} ({len(features)} entries)")


def load_features() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """加载特征和窗口数据。"""
    from .windows import load_windows
    single_windows, multi_windows = load_windows()
    with open(config.FEATURES_PKL, "rb") as f:
        features = pickle.load(f)
    return features, single_windows, multi_windows
