"""
dynamics.py — 动态断裂韧性指标

实现:
    A_i(t)      — 记忆激活函数
    B_direct    — 静态直接破坏量
    B_dyn       — 动态断裂势能
    E_cont      — 延续预期
    U_cad       — 句法未闭合度
    C_res       — 残余相干
    D_dyn       — 动态净断裂感
    T_m         — 音乐结构韧性
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import networkx as nx

from . import config


# =============================================================================
# 时间常量
# =============================================================================

def compute_temporal_constants(
    occurrences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    从主题出现中提取时间常量。

    Returns:
        Dict with:
            'durations'     — List[float], 每次出现的时长
            'gaps'          — List[float], 相邻主题空隙
            'tau'           — float, τ_𝔇 = median(d) + median(g>0)
            'typical_durs'  — Dict[int, float], 每个 T_i 的典型时长
    """
    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    durations = []
    gaps = []

    for o in sorted_occs:
        d = o["sigma"][1] - o["sigma"][0]
        durations.append(d)

    for q in range(len(sorted_occs) - 1):
        g = sorted_occs[q + 1]["sigma"][0] - sorted_occs[q]["sigma"][1]
        if g > 0:
            gaps.append(g)

    # τ_𝔇 = median duration + median positive gap
    med_d = float(np.median(durations)) if durations else config.TAU_DEFAULT
    med_g = float(np.median(gaps)) if gaps else 0.0
    tau = med_d + med_g
    if tau <= 0:
        tau = config.TAU_DEFAULT

    # 每个 T_i 的典型时长
    typical_durs: Dict[int, float] = {}
    durations_by_type: Dict[int, List[float]] = {}
    for o in occurrences:
        tid = o.get("strict_type_id")
        if tid is None:
            continue
        d = o["sigma"][1] - o["sigma"][0]
        durations_by_type.setdefault(tid, []).append(d)

    for tid, ds in durations_by_type.items():
        typical_durs[tid] = float(np.median(ds))

    print(f"τ_𝔇 = {tau:.2f} QL  (median dur={med_d:.2f} + median gap={med_g:.2f})")

    D_global = float(np.median(durations)) if durations else 1.0

    return {
        "durations": durations,
        "gaps": gaps,
        "tau": tau,
        "typical_durs": typical_durs,
        "D_global": D_global,
    }


# =============================================================================
# 记忆激活函数
# =============================================================================

def memory_activation_single(
    sigma: Tuple[float, float],
    t: float,
    tau: float,
) -> float:
    """
    单次主题出现的记忆激活:
        a(t) = 1       (t ∈ σ)
             = 2^{-Δt/τ} (t > t⁺)
             = 0       (t < t⁻)
    """
    t_start, t_end = sigma
    if t_start <= t <= t_end:
        return 1.0
    if t < t_start:
        return 0.0
    delta = t - t_end
    return 2.0 ** (-delta / tau)


def memory_activation_type(
    occurrences_of_type: List[Dict[str, Any]],
    t: float,
    tau: float,
) -> float:
    """
    某一主题类型 T_i 在时刻 t 的激活:
        A_i(t) = 1 - Π (1 - a_{𝔬_q}(t))
    """
    product = 1.0
    for occ in occurrences_of_type:
        a = memory_activation_single(occ["sigma"], t, tau)
        product *= (1.0 - a)
    return 1.0 - product


# =============================================================================
# 动态断裂势能
# =============================================================================

def dynamic_breakage(
    type_id: int,
    t_c: float,
    strict_types: Dict[int, List[Dict[str, Any]]],
    graph: nx.Graph,
    tau: float,
) -> float:
    """
    动态断裂势能:
        B_dyn(T_i, t_c) = A_i(t_c) · Σ_j w_ij · A_j(t_c)
    """
    if type_id not in strict_types or type_id not in graph.nodes():
        return 0.0

    # A_i(t_c)
    A_i = memory_activation_type(strict_types[type_id], t_c, tau)

    # Σ_j w_ij · A_j(t_c)
    weighted_sum = 0.0
    for neighbor in graph.neighbors(type_id):
        if neighbor not in strict_types:
            continue
        w = graph[type_id][neighbor].get("weight", 0)
        A_j = memory_activation_type(strict_types[neighbor], t_c, tau)
        weighted_sum += w * A_j

    return A_i * weighted_sum


# =============================================================================
# 延续预期
# =============================================================================

def continuation_expectation(
    type_id: int,
    t_c: float,
    occurrences: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    type_id_to_idx: Dict[int, int],
    tau: float,
) -> float:
    """
    延续预期 E_cont(T_i, t_c)。

    若有历史同类终止，取平均接续强度；否则退化为 A_i(t_c)。
    """
    # 找到所有 T_i 的历史结束事件
    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    history: List[Dict] = []
    for o in sorted_occs:
        if o.get("strict_type_id") == type_id:
            t_end = o["sigma"][1]
            if t_end < t_c - 1e-9:
                history.append(o)
            elif abs(t_end - t_c) < 1e-9:
                break

    if not history:
        # 退化到当前激活
        strict_types_map: Dict[int, List] = {}
        for o in occurrences:
            tid = o.get("strict_type_id")
            if tid:
                strict_types_map.setdefault(tid, []).append(o)
        return memory_activation_type(strict_types_map.get(type_id, []), t_c, tau)

    # 计算每个历史终止后的接续强度
    strengths = []
    i_idx = type_id_to_idx.get(type_id)
    if i_idx is None:
        return 0.5

    for hist in history:
        t_hist_end = hist["sigma"][1]
        # 找 t_hist_end 之后的所有主题出现
        later_occs = [o for o in sorted_occs if o["sigma"][0] > t_hist_end + 1e-9]
        if not later_occs:
            continue

        best = 0.0
        for later in later_occs:
            j_tid = later.get("strict_type_id")
            if j_tid is None:
                continue
            j_idx = type_id_to_idx.get(j_tid)
            if j_idx is None:
                continue
            delta_t = later["sigma"][0] - t_hist_end
            S = similarity_matrix[i_idx, j_idx]
            strength = 2.0 ** (-delta_t / tau) * S
            if strength > best:
                best = strength
        strengths.append(best)

    if strengths:
        return float(np.mean(strengths))
    return 0.5


# =============================================================================
# 句法未闭合度
# =============================================================================

def syntactic_incompleteness(
    occurrence: Dict[str, Any],
    typical_durations: Dict[int, float],
    D_global: Optional[float] = None,
) -> float:
    """
    U_cad(𝔬_q) = 1 - min(1, dur / D_ref)

    优先使用类型级参考 D_i^{typ}。
    若同类型所有出现时长相等（dur == D_i^{typ} → U_cad=0），
    则退化为使用全局中位时长 D_global 作为参考。
    这样"短于全曲典型主题时长"的出现被视为未完整陈述。
    """
    tid = occurrence.get("strict_type_id")
    dur = occurrence["sigma"][1] - occurrence["sigma"][0]

    # 类型级参考
    D_typ = typical_durations.get(tid) if tid is not None else None

    if D_typ is not None and D_typ > 0:
        # 若类型级参考与当前时长不同 → 用类型级
        if abs(dur - D_typ) > 1e-6:
            return 1.0 - min(1.0, dur / D_typ)
        # 若相同 → 退化为全局参考
        elif D_global is not None and D_global > 0:
            return 1.0 - min(1.0, dur / D_global)

    # 最终回退
    if D_global is not None and D_global > 0:
        return 1.0 - min(1.0, dur / D_global)

    return 0.0


# =============================================================================
# 残余相干
# =============================================================================

def residual_coherence(
    type_id: int,
    t_c: float,
    delta_t: float,
    tau: float,
    occurrences: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    type_id_to_idx: Dict[int, int],
    all_t_c_values: Optional[List[float]] = None,
) -> Tuple[float, float]:
    """
    残余相干 C_res^{dyn} 和归一化版本 C̃_res。

    C_res(T_i, t_c) = Σ_{后续 𝔬_j} 2^{-Δt/τ} · S_m(T_i, T(𝔬_j))
    """
    if delta_t <= 0:
        delta_t = tau * config.DELTA_T_MULTIPLIER

    i_idx = type_id_to_idx.get(type_id)
    if i_idx is None:
        return 0.0, 0.0

    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    C_res = 0.0

    for o in sorted_occs:
        t_j_start = o["sigma"][0]
        if t_c < t_j_start <= t_c + delta_t:
            j_tid = o.get("strict_type_id")
            if j_tid is None:
                continue
            j_idx = type_id_to_idx.get(j_tid)
            if j_idx is None:
                continue
            delta = t_j_start - t_c
            # 记忆衰减核 K_m(Δt) = 2^{-Δt/τ}
            K = 2.0 ** (-delta / tau)
            C_res += K * similarity_matrix[i_idx, j_idx]

    # 归一化: 用所有终止事件上的最大值
    if all_t_c_values:
        all_C = []
        for tc in all_t_c_values:
            c = 0.0
            for o in sorted_occs:
                t_js = o["sigma"][0]
                if tc < t_js <= tc + delta_t:
                    j_tid = o.get("strict_type_id")
                    if j_tid is None:
                        continue
                    j_idx = type_id_to_idx.get(j_tid)
                    if j_idx is None:
                        continue
                    c += 2.0 ** (-(t_js - tc) / tau) * similarity_matrix[i_idx, j_idx]
            all_C.append(c)
        max_C = max(all_C) if all_C else 1.0
    else:
        max_C = C_res if C_res > 0 else 1.0

    C_tilde = C_res / max_C if max_C > 0 else 0.0
    return C_res, C_tilde


# =============================================================================
# 综合计算
# =============================================================================

def compute_all_dynamic_metrics(
    occurrences: List[Dict[str, Any]],
    strict_types: Dict[int, List[Dict[str, Any]]],
    graph: nx.Graph,
    similarity_matrix: np.ndarray,
    type_ids: List[int],
    temporal_constants: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    对所有终止事件计算完整动态指标。
    """
    tau = temporal_constants["tau"]
    delta_t = tau * config.DELTA_T_MULTIPLIER
    typical_durs = temporal_constants["typical_durs"]
    D_global = temporal_constants.get("D_global", None)

    # type_id → matrix index
    type_id_to_idx = {tid: i for i, tid in enumerate(type_ids)}

    # 收集所有终止事件的 t_c
    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    all_t_c = [o["sigma"][1] for o in sorted_occs]

    results = []
    print(f"正在计算 {len(sorted_occs)} 次终止事件的动态指标...")

    for o in sorted_occs:
        tid = o.get("strict_type_id")
        if tid is None:
            continue

        t_c = o["sigma"][1]

        B_dyn = dynamic_breakage(tid, t_c, strict_types, graph, tau)
        E_cont = continuation_expectation(
            tid, t_c, occurrences, similarity_matrix, type_id_to_idx, tau
        )
        U_cad = syntactic_incompleteness(o, typical_durs, D_global)
        C_res_raw, C_tilde = residual_coherence(
            tid, t_c, delta_t, tau, occurrences,
            similarity_matrix, type_id_to_idx, all_t_c,
        )

        # D_dyn = B_dyn · E_cont · U_cad · (1 - C̃_res)
        D_dyn = B_dyn * E_cont * U_cad * max(0.0, 1.0 - C_tilde)

        # T_m = B_dyn + C_res (music structural toughness)
        T_m = B_dyn + C_res_raw

        results.append({
            "occ_id": o["occ_id"],
            "strict_type_id": tid,
            "t_c": t_c,
            "B_dyn": B_dyn,
            "E_cont": E_cont,
            "U_cad": U_cad,
            "C_res_raw": C_res_raw,
            "C_tilde": C_tilde,
            "D_dyn": D_dyn,
            "T_m": T_m,
        })

    print(f"✅ {len(results)} 次终止事件的动态指标已计算")

    # 打印一些聚合统计
    if results:
        D_values = [r["D_dyn"] for r in results]
        print(f"  D_dyn: min={min(D_values):.4f}, max={max(D_values):.4f}, "
              f"mean={np.mean(D_values):.4f}, median={np.median(D_values):.4f}")

    return results


def save_dynamic_metrics(metrics: List[Dict]) -> None:
    """持久化动态指标数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.DYNAMIC_METRICS_PKL, "wb") as f:
        pickle.dump(metrics, f)
    print(f"✅ 动态指标已保存: {config.DYNAMIC_METRICS_PKL}")


def load_dynamic_metrics() -> List[Dict]:
    """加载动态指标数据。"""
    with open(config.DYNAMIC_METRICS_PKL, "rb") as f:
        return pickle.load(f)
