"""
network.py — 主题网络

构造加权无向图 G_m = (V_m, E_m, W_m):
    V_m = {T_1, ..., T_K}  严格主题类型
    E_m = E_sym ∪ E_temp   对称边 + 时间邻接边
    w_ij = λ_sym·1[T_i∼T_j] + λ_temp·c_ij^{temp}/max c
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

from . import config


def build_theme_network(
    strict_types: Dict[int, List[Dict[str, Any]]],
    symmetric_families: Dict[int, List[int]],
    occurrences: List[Dict[str, Any]],
) -> nx.Graph:
    """
    构建主题网络 G_m。

    节点: 严格主题类型 T_i
    边:
        对称边: 同一对称族内的所有 T 对
        时间邻接边: 按出现时间顺序相邻的 T 对

    边权:
        w_ij = λ_sym · 1[T_i ∼_sym T_j]
             + λ_temp · c_ij^{temp} / max c^{temp}
    """
    K = len(strict_types)
    type_ids = sorted(strict_types.keys())
    G = nx.Graph()
    G.add_nodes_from(type_ids)

    # ---- 对称边 ----
    # 建立 type_id → family_id 映射
    type_to_family = {}
    for fid, tids in symmetric_families.items():
        for tid in tids:
            type_to_family[tid] = fid

    for fid, tids in symmetric_families.items():
        if len(tids) >= 2:
            for i in range(len(tids)):
                for j in range(i + 1, len(tids)):
                    G.add_edge(tids[i], tids[j],
                               weight=config.LAMBDA_SYM,
                               edge_type="sym")

    # ---- 时间邻接边 ----
    # 统计 c_ij^{temp}
    temp_counts: Dict[Tuple[int, int], int] = {}
    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])

    for q in range(len(sorted_occs) - 1):
        o_q = sorted_occs[q]
        o_next = sorted_occs[q + 1]
        tid_i = o_q.get("strict_type_id")
        tid_j = o_next.get("strict_type_id")
        if tid_i is not None and tid_j is not None and tid_i != tid_j:
            key = (tid_i, tid_j)
            temp_counts[key] = temp_counts.get(key, 0) + 1

    max_c = max(temp_counts.values()) if temp_counts else 1

    for (tid_i, tid_j), count in temp_counts.items():
        weight = config.LAMBDA_TEMP * count / max_c
        if G.has_edge(tid_i, tid_j):
            G[tid_i][tid_j]["weight"] += weight
            G[tid_i][tid_j]["edge_type"] += "+temp"
        else:
            G.add_edge(tid_i, tid_j,
                       weight=weight,
                       edge_type="temp")

    print(f"主题网络: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
    print(f"  密度: {nx.density(G):.4f}")
    if G.number_of_edges() > 0:
        weights = [d["weight"] for _, _, d in G.edges(data=True)]
        print(f"  边权: min={min(weights):.3f}, max={max(weights):.3f}, mean={np.mean(weights):.3f}")

    return G


def compute_direct_breakage(graph: nx.Graph) -> Dict[int, float]:
    """
    静态直接破坏量:
        B_direct(T_i) = Σ_j w_ij = weighted degree
    """
    breakage = {}
    for node in graph.nodes():
        total_w = sum(d["weight"] for _, _, d in graph.edges(node, data=True))
        breakage[node] = total_w
    return breakage


def get_network_stats(graph: nx.Graph) -> Dict[str, Any]:
    """主题网络基本统计。"""
    if graph.number_of_nodes() == 0:
        return {}

    degrees = [d for _, d in graph.degree()]
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "avg_degree": np.mean(degrees),
        "max_degree": max(degrees),
        "components": nx.number_connected_components(graph),
    }


def save_network(graph: nx.Graph, breakage: Dict[int, float]) -> None:
    """持久化网络数据。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    data = {
        "graph": graph,
        "breakage": breakage,
    }
    with open(config.NETWORK_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ 网络数据已保存: {config.NETWORK_PKL}")


def load_network() -> Tuple[nx.Graph, Dict[int, float]]:
    """加载网络数据。"""
    with open(config.NETWORK_PKL, "rb") as f:
        data = pickle.load(f)
    return data["graph"], data["breakage"]
