"""
themes.py — 主题出现、严格主题类型与对称族

构建主题出现 𝔬_q = (μ_q, g_q, P_q, D_q, σ_q, κ_q)。
定义严格等价 ∼_strict → T_i，对称等价 ∼_sym → F_ℓ。

首版仅处理单声部 (|Λ'|=1)。
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from . import config
from .motifs import extract_phi_rel, _phi_hash


# =============================================================================
# 主题出现构建
# =============================================================================

def build_theme_occurrences(
    features_list: List[Dict[str, Any]],
    motifs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    构建全部单声部主题出现 𝔬_q。

    每个 𝔬_q = {
        'occ_id':      int,      出现序号
        'motif_id':    int,      所属动机原型 μ 的 id
        'g_label':     str,      V4 变换标签 (e/I/R/RI)
        'P':           List[int], 绝对音高序列
        'D':           List[float], 绝对时值序列
        'sigma':       (float, float), 时间区间 [t⁻, t⁺]
        'kappa':       Dict,     严格键 = φ_rel(ω)
        'window_idx':  int,      来源窗口在 features_list 中的索引
    }
    """
    # 建立 window_idx → motif 的映射
    # 先构建 motif hash → motif_id 映射
    motif_hash_to_id: Dict[str, int] = {}
    for m in motifs:
        h = _phi_hash(m["phi_rel_canon"])
        motif_hash_to_id[h] = m["motif_id"]

    occurrences: List[Dict[str, Any]] = []

    for idx, entry in enumerate(features_list):
        if entry["type"] != "single":
            continue

        window = entry["window"]
        features = entry["features"]
        phi_rel = extract_phi_rel(features)

        if phi_rel["L"] < 2:
            continue

        # 确定该 φ_rel 属于哪个动机原型
        rel_hash = _phi_hash(phi_rel)
        motif_id = motif_hash_to_id.get(rel_hash)

        # 如果当前 φ_rel 的直接哈希不在 motif 表中（因为在轨道中去重了），
        # 尝试在动机的 orbit 中查找
        if motif_id is None:
            for m in motifs:
                orbit = m["orbit"]
                found = False
                for g, orb_phi in orbit.items():
                    if _phi_hash(orb_phi) == rel_hash:
                        motif_id = m["motif_id"]
                        found = True
                        break
                if found:
                    break

        if motif_id is None:
            continue  # 无法归类到已知动机原型

        occ = {
            "occ_id": len(occurrences) + 1,
            "motif_id": motif_id,
            "P": features.get("P", []),
            "D": features.get("R", []),
            "sigma": window["time_interval"],
            "kappa": phi_rel,
            "window_idx": idx,
            # g_label 待后续 step 确定(通过距离最近匹配)
            "g_label": config.V4_IDENTITY,  # placeholder
        }
        occurrences.append(occ)

    # 排序: 按时间顺序
    occurrences.sort(key=lambda o: o["sigma"][0])
    for i, occ in enumerate(occurrences):
        occ["occ_id"] = i + 1

    print(f"构建了 {len(occurrences)} 次主题出现 (单声部)")
    return occurrences


# =============================================================================
# 严格主题类型 ∼_strict
# =============================================================================

def build_strict_types(
    occurrences: List[Dict[str, Any]],
) -> Dict[int, List[Dict[str, Any]]]:
    """
    按严格等价关系 ∼_strict 划分主题出现。

    T_i = {𝔬_q : κ(𝔬_q) = κ_i}

    两个出现的 κ（归一化相对特征）完全相同的归入同一严格类型。

    Returns:
        Dict[int, List[Dict]]: {type_id: [occurrences]}
    """
    # 用 κ 的哈希作为分组键
    kappa_groups: Dict[str, List[Dict]] = {}

    for occ in occurrences:
        kh = _phi_hash(occ["kappa"])
        if kh not in kappa_groups:
            kappa_groups[kh] = []
        kappa_groups[kh].append(occ)

    # 分配 type_id，按出现次数降序
    strict_types: Dict[int, List[Dict]] = {}
    sorted_groups = sorted(kappa_groups.items(), key=lambda x: -len(x[1]))

    for tid, (kh, group) in enumerate(sorted_groups, start=1):
        strict_types[tid] = group
        # 在每次出现上标记 type_id
        for occ in group:
            occ["strict_type_id"] = tid

    print(f"严格主题类型数 K = {len(strict_types)}")
    # 统计
    sizes = [len(g) for g in strict_types.values()]
    print(f"  出现次数: min={min(sizes)}, max={max(sizes)}, mean={np.mean(sizes):.1f}")
    print(f"  Singleton 类型 (仅出现1次): {sum(1 for s in sizes if s == 1)}")

    return strict_types


# =============================================================================
# 对称族 ∼_sym
# =============================================================================

def build_symmetric_families(
    strict_types: Dict[int, List[Dict[str, Any]]],
) -> Dict[int, List[int]]:
    """
    按对称等价关系 ∼_sym 将严格类型归入对称族。

    F_ℓ = {T_j : μ(T_j) = μ_ℓ}

    两个严格类型属于同一对称族，当且仅当它们的 motif_id 相同。

    Returns:
        Dict[int, List[int]]: {family_id: [type_ids]}
    """
    # 按 motif_id 分组
    motif_to_types: Dict[int, List[int]] = {}

    for tid, group in strict_types.items():
        motif_id = group[0]["motif_id"]
        if motif_id not in motif_to_types:
            motif_to_types[motif_id] = []
        motif_to_types[motif_id].append(tid)

    symmetric_families: Dict[int, List[int]] = {}
    sorted_groups = sorted(motif_to_types.items(), key=lambda x: -len(x[1]))

    for fid, (motif_id, type_ids) in enumerate(sorted_groups, start=1):
        symmetric_families[fid] = type_ids
        # 标记
        for tid in type_ids:
            for occ in strict_types[tid]:
                occ["family_id"] = fid

    print(f"对称族数 L = {len(symmetric_families)}")
    sizes = [len(types) for types in symmetric_families.values()]
    print(f"  每族严格类型数: min={min(sizes)}, max={max(sizes)}, mean={np.mean(sizes):.1f}")
    large_families = sum(1 for s in sizes if s > 1)
    print(f"  含多个严格类型的族: {large_families}")

    return symmetric_families


# =============================================================================
# 压缩增益计算与过滤 (新增)
# =============================================================================

def compute_compression_gain(
    strict_types: Dict[int, List[Dict[str, Any]]],
) -> Dict[int, Dict[str, float]]:
    """
    为每个严格主题类型 T_i 计算压缩增益。

    L_raw(T_i)   = n_i × L̄_i        (所有出现的总描述长度)
    L_model(T_i) = L̄_i + n_i × c_ref (模板 + 位置引用)
    G_i          = L_raw - L_model
    Ĝ_i          = max(0, G_i / L_raw)

    其中 n_i = 出现次数, L̄_i = 平均窗口长度, c_ref = 参考编码成本。

    Returns:
        Dict[int, Dict]: {type_id: {
            'n_i': int, 'L_bar': float,
            'L_raw': float, 'L_model': float,
            'G': float, 'G_hat': float,
        }}
    """
    gains: Dict[int, Dict[str, float]] = {}

    for tid, occs in strict_types.items():
        n_i = len(occs)
        # 平均窗口长度 (事件数)
        L_vals = [o["kappa"].get("L", len(o.get("P", []))) for o in occs]
        L_bar = float(np.mean(L_vals)) if L_vals else 0.0

        L_raw = n_i * L_bar
        L_model = L_bar + n_i * config.C_REF
        G = L_raw - L_model
        G_hat = max(0.0, G / L_raw) if L_raw > 0 else 0.0

        gains[tid] = {
            "n_i": n_i,
            "L_bar": L_bar,
            "L_raw": L_raw,
            "L_model": L_model,
            "G": G,
            "G_hat": G_hat,
        }

    return gains


def filter_by_compression_gain(
    strict_types: Dict[int, List[Dict[str, Any]]],
    occurrences: List[Dict[str, Any]],
    symmetric_families: Dict[int, List[int]],
    theta_g: Optional[float] = None,
) -> Tuple[Dict[int, List[Dict]], List[Dict], Dict[int, List[int]], Dict[int, Dict]]:
    """
    按压缩增益阈值 θ_G 过滤主题类型。

    仅保留 Ĝ_i > θ_G 的严格主题类型 T_i，
    并从 occurrences 和 symmetric_families 中同步移除被丢弃类型的数据。

    Args:
        strict_types: 原始严格主题类型
        occurrences: 原始主题出现列表
        symmetric_families: 原始对称族
        theta_g: 压缩增益阈值 (默认使用 config.THETA_G)

    Returns:
        (filtered_strict_types, filtered_occurrences, filtered_families, gains_dict)
    """
    if theta_g is None:
        theta_g = config.THETA_G

    # 计算所有类型的压缩增益
    gains = compute_compression_gain(strict_types)

    # 筛选保留的类型 ID
    kept_type_ids: set = set()
    rejected_type_ids: set = set()
    for tid, g in gains.items():
        if g["G_hat"] > theta_g:
            kept_type_ids.add(tid)
        else:
            rejected_type_ids.add(tid)

    n_before = len(strict_types)
    n_rejected = len(rejected_type_ids)

    # 构建过滤后的 strict_types
    filtered_strict_types: Dict[int, List[Dict]] = {}
    new_id_map: Dict[int, int] = {}  # old_id → new_id
    for new_tid, old_tid in enumerate(sorted(kept_type_ids), start=1):
        filtered_strict_types[new_tid] = strict_types[old_tid]
        new_id_map[old_tid] = new_tid

    # 过滤 occurrences (移除被拒绝类型的出现)
    kept_occ_ids: set = set()
    for tid in kept_type_ids:
        for occ in strict_types[tid]:
            kept_occ_ids.add(occ["occ_id"])

    filtered_occurrences = [o for o in occurrences if o["occ_id"] in kept_occ_ids]

    # 更新 occurrence 上的 type_id
    for occ in filtered_occurrences:
        old_tid = occ.get("strict_type_id")
        if old_tid in new_id_map:
            occ["strict_type_id"] = new_id_map[old_tid]

    # 重建 symmetric_families (保持按 motif_id 分组)
    motif_to_types: Dict[int, List[int]] = {}
    for old_tid in sorted(kept_type_ids):
        new_tid = new_id_map[old_tid]
        motif_id = strict_types[old_tid][0]["motif_id"]
        motif_to_types.setdefault(motif_id, []).append(new_tid)

    filtered_families: Dict[int, List[int]] = {}
    sorted_motifs = sorted(motif_to_types.items(), key=lambda x: -len(x[1]))
    for fid, (motif_id, type_ids) in enumerate(sorted_motifs, start=1):
        filtered_families[fid] = type_ids
        for tid in type_ids:
            for occ in filtered_strict_types[tid]:
                occ["family_id"] = fid

    # 打印统计
    n_after = len(filtered_strict_types)
    n_occ_before = len(occurrences)
    n_occ_after = len(filtered_occurrences)

    print(f"\n{'='*60}")
    print(f"🔍 压缩增益过滤 (θ_G = {theta_g})")
    print(f"{'='*60}")
    print(f"  过滤前: K = {n_before} 严格类型, Q = {n_occ_before} 次出现")
    print(f"  被拒绝: {n_rejected} 个类型 (Ĝ ≤ {theta_g})")
    print(f"  过滤后: K = {n_after} 严格类型, Q = {n_occ_after} 次出现")
    print(f"  压缩比: K {n_after}/{n_before} = {n_after/n_before*100:.1f}%, "
          f"Q {n_occ_after}/{n_occ_before} = {n_occ_after/n_occ_before*100:.1f}%")

    # 被拒绝类型的统计
    rejected_gains = [gains[tid]["G_hat"] for tid in rejected_type_ids]
    kept_gains = [gains[tid]["G_hat"] for tid in kept_type_ids]
    print(f"  保留类型 Ĝ: min={min(kept_gains):.3f}, max={max(kept_gains):.3f}, "
          f"mean={np.mean(kept_gains):.3f}")
    if rejected_gains:
        print(f"  拒绝类型 Ĝ: min={min(rejected_gains):.3f}, max={max(rejected_gains):.3f}, "
              f"mean={np.mean(rejected_gains):.3f}")
    print(f"{'='*60}")

    return filtered_strict_types, filtered_occurrences, filtered_families, gains


def compute_theme_importance(
    strict_types: Dict[int, List[Dict[str, Any]]],
    gains: Dict[int, Dict[str, float]],
) -> Dict[int, float]:
    """
    计算每个主题类型的"基础重要性" A_i。

    A_i = n_i · Ĝ_i           (linear)
    或  = log(1+n_i) · Ĝ_i    (log, 默认)
    或  = √n_i · Ĝ_i          (sqrt)

    对应 formalization 中的"有效链段密度/活性链数"。

    Returns:
        Dict[int, float]: {type_id: importance}
    """
    importance: Dict[int, float] = {}
    for tid in strict_types:
        g = gains[tid]
        n_i = g["n_i"]
        G_hat = g["G_hat"]

        if config.IMPORTANCE_MODE == "linear":
            A_i = n_i * G_hat
        elif config.IMPORTANCE_MODE == "sqrt":
            A_i = np.sqrt(n_i) * G_hat
        else:  # log (default)
            A_i = np.log(1 + n_i) * G_hat

        importance[tid] = A_i

    return importance


# =============================================================================
# 持久化
# =============================================================================

def save_themes(
    occurrences: List[Dict],
    strict_types: Dict[int, List[Dict]],
    symmetric_families: Dict[int, List[int]],
) -> None:
    """持久化主题数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    data = {
        "occurrences": occurrences,
        "strict_types": strict_types,
        "symmetric_families": symmetric_families,
    }
    with open(config.THEMES_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ 主题数据已保存: {config.THEMES_PKL}")


def load_themes() -> Tuple[List[Dict], Dict[int, List[Dict]], Dict[int, List[int]]]:
    """加载主题数据。"""
    with open(config.THEMES_PKL, "rb") as f:
        data = pickle.load(f)
    return data["occurrences"], data["strict_types"], data["symmetric_families"]
