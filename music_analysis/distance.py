"""
distance.py — 商空间距离与主题相似度

实现:
    d_I (归一化编辑距离)
    d_R, d_T (DTW 距离)
    d_Φ = w_I·d_I + w_R·d_R + w_T·d_T
    d_ℚ = min_{g∈V4} d_Φ(κ_i, g·κ_j)
    ℓ   = median{ d_ℚ(T_i, T_j) > 0 }
    S_m = exp(-d_ℚ / ℓ)
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import editdistance
from dtw import dtw

from . import config
from .motifs import V4_TRANSFORM, apply_v4


# =============================================================================
# 序列距离
# =============================================================================

def interval_edit_distance(I_a: List[float], I_b: List[float]) -> float:
    """
    归一化音程编辑距离:
        d_I = editdistance(I_a, I_b) / max(L_a, L_b)
    """
    if not I_a and not I_b:
        return 0.0
    if not I_a or not I_b:
        return 1.0
    # 将浮点音程取整为半音
    a_ints = [int(round(i)) for i in I_a]
    b_ints = [int(round(i)) for i in I_b]
    raw = editdistance.eval(a_ints, b_ints)
    return raw / max(len(I_a), len(I_b))


def rhythm_dtw_distance(R_hat_a: List[float], R_hat_b: List[float]) -> float:
    """
    归一化节奏 DTW 距离 (symmetric2 step pattern)。
    """
    if not R_hat_a and not R_hat_b:
        return 0.0
    if not R_hat_a or not R_hat_b:
        return 1.0

    alignment = dtw(
        np.array(R_hat_a), np.array(R_hat_b),
        step_pattern="symmetric2",
        keep_internals=False,
    )
    return alignment.normalizedDistance


def onset_dtw_distance(T_hat_a: List[float], T_hat_b: List[float]) -> float:
    """
    归一化起始时间 DTW 距离 (symmetric2 step pattern)。
    """
    if not T_hat_a and not T_hat_b:
        return 0.0
    if not T_hat_a or not T_hat_b:
        return 1.0

    alignment = dtw(
        np.array(T_hat_a), np.array(T_hat_b),
        step_pattern="symmetric2",
        keep_internals=False,
    )
    return alignment.normalizedDistance


# =============================================================================
# 特征空间距离
# =============================================================================

def feature_distance(phi_a: Dict[str, Any], phi_b: Dict[str, Any]) -> float:
    """
    特征空间距离:
        d_Φ(φ_a, φ_b) = w_I·d_I(I_a, I_b)
                       + w_R·d_R(R̂_a, R̂_b)
                       + w_T·d_T(T̂_a, T̂_b)
    """
    d_I_val = interval_edit_distance(
        phi_a.get("I", []), phi_b.get("I", [])
    )
    d_R_val = rhythm_dtw_distance(
        phi_a.get("R_hat", []), phi_b.get("R_hat", [])
    )
    d_T_val = onset_dtw_distance(
        phi_a.get("T_hat_start_ref", []), phi_b.get("T_hat_start_ref", [])
    )

    return config.W_I * d_I_val + config.W_R * d_R_val + config.W_T * d_T_val


# =============================================================================
# 商空间距离
# =============================================================================

def quotient_distance(
    kappa_i: Dict[str, Any],
    kappa_j: Dict[str, Any],
) -> float:
    """
    商空间距离:
        d_ℚ(T_i, T_j) = min_{g∈V4} d_Φ(κ_i, g·κ_j)
    """
    min_dist = float("inf")
    for g in config.V4_ELEMENTS:
        transformed = V4_TRANSFORM[g](kappa_j)
        d = feature_distance(kappa_i, transformed)
        if d < min_dist:
            min_dist = d
    return min_dist


# =============================================================================
# 尺度参数与相似度
# =============================================================================

def compute_scale_parameter(
    dist_matrix: np.ndarray,
) -> float:
    """
    自适应尺度参数:
        ℓ = median{ d_ℚ(T_i, T_j) > 0 }
    """
    non_zero = dist_matrix[dist_matrix > 0]
    if len(non_zero) == 0:
        return 1.0
    return float(np.median(non_zero))


def theme_similarity(
    dist_matrix: np.ndarray,
    ell: float,
) -> np.ndarray:
    """
    主题相似度矩阵:
        S_m(T_i, T_j) = exp(-d_ℚ(T_i, T_j) / ℓ)
    """
    if ell <= 0:
        ell = 1.0
    return np.exp(-dist_matrix / ell)


# =============================================================================
# 批量距离矩阵计算
# =============================================================================

def build_distance_matrix(
    strict_types: Dict[int, List[Dict[str, Any]]],
) -> Tuple[np.ndarray, List[int]]:
    """
    为所有严格主题类型 {T_i} 计算两两商空间距离矩阵。

    每个 T_i 使用其第一个出现的 κ 作为代表。

    Returns:
        (K×K 距离矩阵, type_ids 列表)
    """
    type_ids = sorted(strict_types.keys())
    K = len(type_ids)

    # 收集每个类型的代表 κ
    kappas = []
    for tid in type_ids:
        first_occ = strict_types[tid][0]
        if "kappa" in first_occ:
            kappa = first_occ["kappa"]
        elif "kappa_rel" in first_occ:
            kappa = first_occ["kappa_rel"]
        else:
            kappa = {}
        kappas.append(kappa)

    dist_matrix = np.zeros((K, K))
    print(f"正在计算 {K}×{K} 商空间距离矩阵...")

    for i in range(K):
        for j in range(i + 1, K):
            d = quotient_distance(kappas[i], kappas[j])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    print(f"✅ 距离矩阵计算完成")
    return dist_matrix, type_ids


# =============================================================================
# 持久化
# =============================================================================

def save_similarity(
    dist_matrix: np.ndarray,
    sim_matrix: np.ndarray,
    type_ids: List[int],
    ell: float,
) -> None:
    """持久化距离和相似度数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    data = {
        "dist_matrix": dist_matrix,
        "sim_matrix": sim_matrix,
        "type_ids": type_ids,
        "ell": ell,
    }
    with open(config.SIMILARITY_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ 相似度数据已保存: {config.SIMILARITY_PKL} (ℓ={ell:.4f})")


def load_similarity() -> Tuple[np.ndarray, np.ndarray, List[int], float]:
    """加载距离和相似度数据。"""
    with open(config.SIMILARITY_PKL, "rb") as f:
        data = pickle.load(f)
    return data["dist_matrix"], data["sim_matrix"], data["type_ids"], data["ell"]
