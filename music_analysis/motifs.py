"""
motifs.py — 动机原型与 V4 克莱因四元群

实现 V4 = {e, I, R, RI} 群变换、轨道计算、稳定子检测、
商空间映射，以及动机原型 μ 的提取。

关键定义:
    φ_rel = (I, R̂, T̂_start_ref)
    μ = Orb(φ) = {g·φ | g∈V4}  (动机原型 = V4 轨道)
"""

import pickle
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from . import config


# =============================================================================
# 从特征中提取相对特征 φ_rel
# =============================================================================

def extract_phi_rel(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    从完整特征中提取相对特征 φ_rel = (I, R̂, T̂_start_ref)。

    Returns:
        Dict with keys 'I', 'R_hat', 'T_hat_start_ref', 'L'
    """
    return {
        "I": features.get("I", []),
        "R_hat": features.get("R_hat", []),
        "T_hat_start_ref": features.get("T_hat_start_ref", []),
        "L": features.get("L", 0),
    }


# =============================================================================
# V4 群变换算子
# =============================================================================

def v4_identity(phi_rel: Dict[str, Any]) -> Dict[str, Any]:
    """恒等变换 e·φ = (I, R̂, T̂)。"""
    return {
        "I": phi_rel["I"][:],
        "R_hat": phi_rel["R_hat"][:],
        "T_hat_start_ref": phi_rel["T_hat_start_ref"][:],
        "L": phi_rel["L"],
    }


def v4_inversion(phi_rel: Dict[str, Any]) -> Dict[str, Any]:
    """
    倒影 I·φ = (-I, R̂, T̂)。

    音程取反，节奏和起始时间不变。
    """
    return {
        "I": [-i for i in phi_rel["I"]],
        "R_hat": phi_rel["R_hat"][:],
        "T_hat_start_ref": phi_rel["T_hat_start_ref"][:],
        "L": phi_rel["L"],
    }


def v4_retrograde(phi_rel: Dict[str, Any]) -> Dict[str, Any]:
    """
    逆行 R·φ = (-I^rev, R̂^rev, T̂^rev)。

    音程取反并逆序，节奏和起始时间逆序。
    """
    I = phi_rel["I"]
    R = phi_rel["R_hat"]
    T = phi_rel["T_hat_start_ref"]

    # I^rev = 逆序音程
    I_rev = I[::-1] if I else []
    # -I^rev
    I_result = [-i for i in I_rev]

    # R̂^rev: 逆序节奏
    R_result = R[::-1]

    # T̂^rev: 逆序起始时间 (只取相对分布，非严格逆序)
    # 逆序后需从 0 重新归一化
    T_rev = T[::-1]
    if T_rev:
        t0 = T_rev[0]
        T_result = [t - t0 for t in T_rev]
        total_T = T_result[-1] if T_result[-1] > 0 else 1.0
        T_result = [t / total_T for t in T_result]
    else:
        T_result = []

    return {
        "I": I_result,
        "R_hat": R_result,
        "T_hat_start_ref": T_result,
        "L": phi_rel["L"],
    }


def v4_retrograde_inversion(phi_rel: Dict[str, Any]) -> Dict[str, Any]:
    """
    逆行倒影 RI·φ = (I^rev, R̂^rev, T̂^rev)。

    音程仅逆序（不取反），节奏和起始时间逆序。
    """
    I = phi_rel["I"]
    R = phi_rel["R_hat"]
    T = phi_rel["T_hat_start_ref"]

    # I^rev
    I_result = I[::-1] if I else []

    R_result = R[::-1]

    T_rev = T[::-1]
    if T_rev:
        t0 = T_rev[0]
        T_result = [t - t0 for t in T_rev]
        total_T = T_result[-1] if T_result[-1] > 0 else 1.0
        T_result = [t / total_T for t in T_result]
    else:
        T_result = []

    return {
        "I": I_result,
        "R_hat": R_result,
        "T_hat_start_ref": T_result,
        "L": phi_rel["L"],
    }


V4_TRANSFORM = {
    config.V4_IDENTITY: v4_identity,
    config.V4_INVERSION: v4_inversion,
    config.V4_RETROGRADE: v4_retrograde,
    config.V4_RETROGRADE_INVERSION: v4_retrograde_inversion,
}


def apply_v4(phi_rel: Dict[str, Any], g: str) -> Dict[str, Any]:
    """对相对特征 φ_rel 应用 V4 群变换 g。"""
    if g not in V4_TRANSFORM:
        raise ValueError(f"Unknown V4 element: {g}")
    return V4_TRANSFORM[g](phi_rel)


# =============================================================================
# 轨道与稳定子
# =============================================================================

def compute_orbit(phi_rel: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    计算 φ_rel 的 V4 轨道: Orb(φ) = {g·φ | g∈V4}。

    Returns:
        Dict[str, Dict]: {g_label: g·φ} — 四种（或退化）变体
    """
    orbit = {}
    seen = set()

    for g in config.V4_ELEMENTS:
        transformed = apply_v4(phi_rel, g)
        # 生成哈希用于去重
        key = _phi_hash(transformed)
        if key not in seen:
            seen.add(key)
            orbit[g] = transformed

    return orbit


def compute_stabilizer(phi_rel: Dict[str, Any]) -> Set[str]:
    """
    计算稳定子 Stab(φ) = {g∈V4 | g·φ = φ}。

    使用浮点容差比较。
    """
    stab = set()
    base_hash = _phi_hash(phi_rel)

    for g in config.V4_ELEMENTS:
        transformed = apply_v4(phi_rel, g)
        if _phi_hash(transformed) == base_hash:
            stab.add(g)

    return stab


def _phi_hash(phi_rel: Dict[str, Any], decimals: int = 6) -> str:
    """生成 φ_rel 的哈希字符串（用于比较等价性）。"""
    I_rounded = tuple(round(i, decimals) for i in phi_rel["I"])
    R_rounded = tuple(round(r, decimals) for r in phi_rel["R_hat"])
    T_rounded = tuple(round(t, decimals) for t in phi_rel["T_hat_start_ref"])
    return f"{I_rounded}|{R_rounded}|{T_rounded}|{phi_rel['L']}"


def detect_symmetry_type(phi_rel: Dict[str, Any]) -> str:
    """
    检测动机的对称类型。

    Returns:
        'asymmetric'  — |Stab|=1, |Orb|=4
        'palindromic' — 具有节奏回文或音程回文
        'full_sym'    — 完全对称
    """
    stab = compute_stabilizer(phi_rel)
    orbit = compute_orbit(phi_rel)

    if len(stab) == 1:
        return "asymmetric"
    elif len(orbit) == 2:
        return "full_sym"  # 轨道退化到 2
    else:
        return "palindromic"


# =============================================================================
# 动机原型提取
# =============================================================================

def build_motif_prototypes(
    features_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    从特征列表中构建所有动机原型 μ。

    将每个单声部窗口的 φ_rel 映射到 V4 轨道，
    相同轨道归于同一动机原型。

    每个动机原型 = 轨道的代表 φ_rel + 该原型的所有出现窗口索引列表。

    Returns:
        List of dicts, each containing:
            'motif_id'       — int, 动机原型编号
            'phi_rel_canon'  — 规范代表 φ_rel (e 变换后的形式)
            'orbit'          — Dict[g, phi_rel]
            'stabilizer'     — Set[str]
            'symmetry_type'  — str
            'orbit_size'     — int (1, 2, or 4)
            'window_indices' — List[int], 属于该原型的窗口索引
    """
    # 轨道收集: hash → (canonical phi_rel, orbit, stab, window_indices)
    orbit_map: Dict[str, Dict] = {}

    for idx, entry in enumerate(features_list):
        # 仅处理单声部（单声部窗口才有 V4 动机分析）
        if entry["type"] != "single":
            continue

        phi_rel = extract_phi_rel(entry["features"])

        # 跳过空特征
        if phi_rel["L"] < 2:
            continue

        orbit = compute_orbit(phi_rel)
        stab = compute_stabilizer(phi_rel)

        # 用规范代表 (e 变换) 的哈希作为轨道标识
        canon = V4_TRANSFORM[config.V4_IDENTITY](phi_rel)
        orbit_hash = _phi_hash(canon)

        if orbit_hash not in orbit_map:
            orbit_map[orbit_hash] = {
                "phi_rel_canon": canon,
                "orbit": orbit,
                "stabilizer": stab,
                "symmetry_type": detect_symmetry_type(phi_rel),
                "orbit_size": len(orbit),
                "window_indices": [],
            }
        orbit_map[orbit_hash]["window_indices"].append(idx)

    # 转为列表并分配 ID
    motifs = []
    for mid, (orbit_hash, data) in enumerate(sorted(orbit_map.items()), start=1):
        data["motif_id"] = mid
        motifs.append(data)

    print(f"构建了 {len(motifs)} 个动机原型")
    asym = sum(1 for m in motifs if m["symmetry_type"] == "asymmetric")
    pal = sum(1 for m in motifs if m["symmetry_type"] == "palindromic")
    full = sum(1 for m in motifs if m["symmetry_type"] == "full_sym")
    print(f"  非对称 (|Orb|=4): {asym}")
    print(f"  回文/部分对称:      {pal}")
    print(f"  完全对称 (|Orb|=2): {full}")

    # 轨道大小分布
    sizes = {}
    for m in motifs:
        s = m["orbit_size"]
        sizes[s] = sizes.get(s, 0) + 1
    print(f"  轨道大小分布: {dict(sorted(sizes.items()))}")

    return motifs


# =============================================================================
# 持久化
# =============================================================================

def save_motifs(motifs: List[Dict]) -> None:
    """持久化动机数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.MOTIFS_PKL, "wb") as f:
        pickle.dump(motifs, f)
    print(f"✅ 动机数据已保存: {config.MOTIFS_PKL} ({len(motifs)} motifs)")


def load_motifs() -> List[Dict]:
    """加载动机数据。"""
    with open(config.MOTIFS_PKL, "rb") as f:
        motifs = pickle.load(f)
    return motifs
