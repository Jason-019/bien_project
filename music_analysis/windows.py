"""
windows.py — 候选音型窗口提取

从声部分层事件中提取:
    单声部窗口 ω_{i,L}^{(λ)}   — 满足 L/D/B/tie 约束
    多声部块窗口 ω_i^{(Λ')}   — |Λ'|=2 的声部对组合

Window data structure:
    {
        'type': 'single' | 'multi',
        'lambda': (s, v) or None,
        'lambda_set': [(s1,v1), (s2,v2)] or None,
        'events': List[Dict],        # 窗口内的事件列表
        'L': int,                    # 事件数
        'D': float,                  # 时间跨度
        'B': int,                    # 小节跨度
        'i_start': int,              # 在 λ 层中的起始索引
        'time_interval': (t_start, t_end),
    }
"""

import pickle
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple, Set

from . import config


# =============================================================================
# 约束检查函数
# =============================================================================

def check_L_constraint(L: int) -> bool:
    """检查事件数量约束: L_min ≤ L ≤ L_max。"""
    return config.L_MIN <= L <= config.L_MAX


def check_D_constraint(window_events: List[Dict[str, Any]]) -> bool:
    """
    检查时间跨度约束: D_min ≤ D(ω) ≤ D_max。

    D(ω) = t_{end} + d_{end} - t_{start}
    """
    if not window_events:
        return False
    t_start = window_events[0]["t_n"]
    last = window_events[-1]
    t_end = last["t_n"] + last["d_n"]
    D = t_end - t_start
    return config.D_MIN <= D <= config.D_MAX


def check_B_constraint(window_events: List[Dict[str, Any]]) -> bool:
    """
    检查小节跨度约束: B(ω) ≤ B_max。

    B(ω) = m_{last} - m_{first} + 1
    """
    if not window_events:
        return False
    m_first = window_events[0]["m_n"]
    m_last = window_events[-1]["m_n"]
    B = m_last - m_first + 1
    return B <= config.B_MAX


def check_tie_constraint(window_events: List[Dict[str, Any]]) -> bool:
    """
    检查延音线约束 C_tie(ω)。

    窗口起点 tie ∉ {continue, stop}
    窗口终点 tie ∉ {start, continue}
    """
    if not window_events:
        return False

    start_tie = window_events[0]["beta_n"]["tie"]
    end_tie = window_events[-1]["beta_n"]["tie"]

    if start_tie in config.TIE_INVALID_START:
        return False
    if end_tie in config.TIE_INVALID_END:
        return False

    return True


def compute_window_D(window_events: List[Dict[str, Any]]) -> float:
    """计算窗口时间跨度 D(ω)。"""
    if not window_events:
        return 0.0
    t_start = window_events[0]["t_n"]
    last = window_events[-1]
    return last["t_n"] + last["d_n"] - t_start


def compute_window_B(window_events: List[Dict[str, Any]]) -> int:
    """计算窗口小节跨度 B(ω)。"""
    if not window_events:
        return 0
    m_first = window_events[0]["m_n"]
    m_last = window_events[-1]["m_n"]
    return m_last - m_first + 1


# =============================================================================
# 单声部窗口提取
# =============================================================================

def extract_single_voice_windows(
    voice_layer: List[Dict[str, Any]],
    lambda_key: Tuple[str, str],
) -> List[Dict[str, Any]]:
    """
    对单个声部层 λ 提取所有满足约束的候选窗口 ω_{i,L}^{(λ)}。

    使用滑动窗口:
        i 从 0 到 N_λ-L+1
        L 从 L_min 到 min(L_max, N_λ - i)

    Constraints applied:
        L_min ≤ L ≤ L_max
        D_min ≤ D(ω) ≤ D_max
        B(ω) ≤ B_max
        C_tie(ω) = 1

    Returns:
        List of window dicts, each containing events, metadata, and constraint flags
    """
    N_lambda = len(voice_layer)
    windows: List[Dict[str, Any]] = []

    for i in range(N_lambda):
        max_L = min(config.L_MAX, N_lambda - i)
        if max_L < config.L_MIN:
            continue

        for L in range(config.L_MIN, max_L + 1):
            window_events = voice_layer[i:i + L]

            # 三层约束
            if not check_D_constraint(window_events):
                continue
            if not check_B_constraint(window_events):
                continue
            if not check_tie_constraint(window_events):
                continue

            D_val = compute_window_D(window_events)
            B_val = compute_window_B(window_events)
            t_start = window_events[0]["t_n"]
            t_end = window_events[-1]["t_n"] + window_events[-1]["d_n"]

            window = {
                "type": "single",
                "lambda": lambda_key,
                "lambda_set": [lambda_key],
                "events": window_events,
                "L": L,
                "D": D_val,
                "B": B_val,
                "i_start": i,
                "time_interval": (t_start, t_end),
                # 特征占位 — 在 Step 03 中填充
                "features": None,
            }
            windows.append(window)

    return windows


# =============================================================================
# 多声部窗口提取
# =============================================================================

def extract_multi_voice_windows(
    voice_layers: Dict[Tuple[str, str], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    提取多声部块窗口 ω_i^{(Λ')}。

    首版仅处理 |Λ'|=2 的声部对组合。
    方法: 对每个声部对，取两层时间轴上的重叠区间作为候选窗口。

    Constraints:
        D_min ≤ D(ω) ≤ D_max
        B(ω) ≤ B_max
        C_tie(ω) = 1 for all λ∈Λ'
    """
    multi_windows: List[Dict[str, Any]] = []
    lambda_keys = sorted(voice_layers.keys())

    for (lam_a, lam_b) in combinations(lambda_keys, 2):
        lambda_set = [lam_a, lam_b]
        layer_a = voice_layers[lam_a]
        layer_b = voice_layers[lam_b]

        # 为这对声部生成重叠时间区间
        candidate_windows = _find_overlapping_windows(
            layer_a, lam_a,
            layer_b, lam_b,
            lambda_set,
        )
        multi_windows.extend(candidate_windows)

    return multi_windows


def _find_overlapping_windows(
    layer_a: List[Dict[str, Any]],
    lam_a: Tuple[str, str],
    layer_b: List[Dict[str, Any]],
    lam_b: Tuple[str, str],
    lambda_set: List[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    """
    对两个声部层，寻找所有满足约束的时间重叠区间。

    策略:
        1. 收集两层所有事件的 (t_start, t_end) 区间
        2. 对每个 layer_a 中的事件作为锚点，查找 layer_b 中与其时间重叠的事件
        3. 在重叠区间上筛选满足约束的子序列
    """
    windows: List[Dict[str, Any]] = []

    # 对 layer_a 的每个 L (L_min 到 L_max) 的滑动窗口
    N_a = len(layer_a)
    for i_a in range(N_a):
        max_L_a = min(config.L_MAX, N_a - i_a)
        if max_L_a < config.L_MIN:
            continue

        for L_a in range(config.L_MIN, max_L_a + 1):
            sub_a = layer_a[i_a:i_a + L_a]

            # 确定时间区间
            t_start_a = sub_a[0]["t_n"]
            t_end_a = sub_a[-1]["t_n"] + sub_a[-1]["d_n"]

            # 在 layer_b 中找到与 [t_start_a, t_end_a] 重叠的事件
            sub_b = _get_events_in_interval(layer_b, t_start_a, t_end_a)

            if len(sub_b) < config.L_MIN:
                continue

            # 对所有满足的 layer_b 子序列尝试
            for i_b in range(len(sub_b)):
                max_L_b = min(config.L_MAX, len(sub_b) - i_b)
                if max_L_b < config.L_MIN:
                    continue

                for L_b in range(config.L_MIN, max_L_b + 1):
                    sub_b_window = sub_b[i_b:i_b + L_b]

                    # 组合窗口事件 (所有参与声部的事件，按 t_n 排序)
                    combined = sorted(sub_a + sub_b_window, key=lambda e: e["t_n"])

                    # 计算多声部窗口参数
                    t_start = min(sub_a[0]["t_n"], sub_b_window[0]["t_n"])
                    t_end = max(
                        sub_a[-1]["t_n"] + sub_a[-1]["d_n"],
                        sub_b_window[-1]["t_n"] + sub_b_window[-1]["d_n"],
                    )
                    D_val = t_end - t_start

                    # 小节跨度
                    all_m = [e["m_n"] for e in combined]
                    B_val = max(all_m) - min(all_m) + 1

                    # 约束检查
                    if D_val < config.D_MIN or D_val > config.D_MAX:
                        continue
                    if B_val > config.B_MAX:
                        continue
                    # Tie 约束 — 每个单声部子窗口各自检查
                    if not check_tie_constraint(sub_a):
                        continue
                    if not check_tie_constraint(sub_b_window):
                        continue

                    window = {
                        "type": "multi",
                        "lambda": None,  # 多声部没有单一 λ
                        "lambda_set": lambda_set,
                        "events": combined,
                        "events_by_layer": {
                            lam_a: sub_a,
                            lam_b: sub_b_window,
                        },
                        "L": (L_a, L_b),  # 各层的长度
                        "D": D_val,
                        "B": B_val,
                        "i_start": (i_a, i_b),
                        "time_interval": (t_start, t_end),
                        "features": None,
                    }
                    windows.append(window)

    return windows


def _get_events_in_interval(
    layer: List[Dict[str, Any]],
    t_start: float,
    t_end: float,
) -> List[Dict[str, Any]]:
    """
    从声部层中提取在 [t_start, t_end] 时间区间内发声音的事件。

    考虑音符的完整持续区间 [t_n, t_n + d_n) 与 [t_start, t_end) 有交集。
    """
    result = []
    for ev in layer:
        ev_start = ev["t_n"]
        ev_end = ev["t_n"] + ev["d_n"]
        # 区间重叠检测
        if ev_start < t_end and ev_end > t_start:
            result.append(ev)
    return result


# =============================================================================
# 窗口过滤与去重 (避免过度相似的窗口)
# =============================================================================

def deduplicate_windows(
    windows: List[Dict[str, Any]],
    min_ratio: float = 0.95,
) -> List[Dict[str, Any]]:
    """
    移除过度相似的（高度重叠的）窗口，保留最具代表性的。

    对于同一 λ 中时间区间重叠超过 min_ratio 的两个窗口，保留 D 更接近中位数的那个。
    """
    if len(windows) <= 1:
        return windows

    # 按 λ 分组
    by_lambda: Dict[str, List[Dict]] = {}
    for w in windows:
        key = str(w.get("lambda") or w.get("lambda_set"))
        by_lambda.setdefault(key, []).append(w)

    result = []
    for key, ws in by_lambda.items():
        # 按时间排序
        ws.sort(key=lambda w: w["time_interval"][0])
        kept = []
        for w in ws:
            is_dup = False
            for k in kept:
                overlap = _interval_overlap_ratio(w["time_interval"], k["time_interval"])
                if overlap > min_ratio:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(w)
        result.extend(kept)

    return result


def _interval_overlap_ratio(
    interval_a: Tuple[float, float],
    interval_b: Tuple[float, float],
) -> float:
    """计算两个区间 [a,b] 的重叠比例（相对于较小者）。"""
    a1, a2 = interval_a
    b1, b2 = interval_b
    overlap_start = max(a1, b1)
    overlap_end = min(a2, b2)
    if overlap_start >= overlap_end:
        return 0.0
    overlap_len = overlap_end - overlap_start
    min_len = min(a2 - a1, b2 - b1)
    if min_len == 0:
        return 0.0
    return overlap_len / min_len


# =============================================================================
# 统计与持久化
# =============================================================================

def print_window_stats(
    single_windows: List[Dict],
    multi_windows: List[Dict],
    voice_layers: Dict,
) -> None:
    """打印窗口提取统计。"""
    N_single = len(single_windows)
    N_multi = len(multi_windows)
    N_total = N_single + N_multi

    print("=" * 60)
    print("📊 候选音型窗口统计")
    print("=" * 60)
    print(f"  单声部窗口 |Ω|        = {N_single}")
    print(f"  多声部窗口 |Ω_multi|  = {N_multi}")
    print(f"  总候选窗口 |Ω*|        = {N_total}")
    print("-" * 60)

    # 按声部层统计单声部窗口
    for (s, v), layer_events in sorted(voice_layers.items()):
        count = sum(1 for w in single_windows if w["lambda"] == (s, v))
        if count > 0:
            print(f"  λ=({s}, {v:>4s}): {count} 单声部窗口")

    if N_single > 0:
        Ls = [w["L"] for w in single_windows]
        Ds = [w["D"] for w in single_windows]
        Bs = [w["B"] for w in single_windows]
        print(f"\n  单声部窗口 - L 范围: [{min(Ls)}, {max(Ls)}], "
              f"D 范围: [{min(Ds):.1f}, {max(Ds):.1f}], "
              f"B 范围: [{min(Bs)}, {max(Bs)}]")

    if N_multi > 0:
        print(f"\n  多声部窗口声部对组合:")
        pair_counts: Dict[str, int] = {}
        for w in multi_windows:
            pair_key = " × ".join(f"({s},{v})" for s, v in w["lambda_set"])
            pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1
        for pair, cnt in sorted(pair_counts.items(), key=lambda x: -x[1]):
            print(f"    {pair}: {cnt} 窗口")

    print("=" * 60)


def save_windows(
    single_windows: List[Dict],
    multi_windows: List[Dict],
) -> None:
    """持久化窗口数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    data = {
        "single": single_windows,
        "multi": multi_windows,
        "config": {
            "L_MIN": config.L_MIN, "L_MAX": config.L_MAX,
            "D_MIN": config.D_MIN, "D_MAX": config.D_MAX,
            "B_MAX": config.B_MAX,
        },
    }
    with open(config.WINDOWS_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ 窗口数据已保存: {config.WINDOWS_PKL} ({len(single_windows)} single + {len(multi_windows)} multi)")


def load_windows() -> Tuple[List[Dict], List[Dict]]:
    """加载窗口数据。"""
    with open(config.WINDOWS_PKL, "rb") as f:
        data = pickle.load(f)
    return data["single"], data["multi"]
