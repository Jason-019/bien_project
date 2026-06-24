"""
viz.py — 可视化工具函数

基于 plotly 的可视化封装。
"""

from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import numpy as np


def plot_theme_network(
    graph: nx.Graph,
    breakage: Dict[int, float],
    title: str = "Theme Network G_m",
) -> go.Figure:
    """绘制主题网络图（plotly 交互式）。"""
    pos = nx.spring_layout(graph, seed=42, k=0.15)

    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = [pos[n][0] for n in graph.nodes()]
    node_y = [pos[n][1] for n in graph.nodes()]
    node_sizes = [breakage.get(n, 0) * 15 + 5 for n in graph.nodes()]
    node_text = [f"T_{n}<br>B_direct={breakage.get(n,0):.3f}" for n in graph.nodes()]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            size=node_sizes,
            color=[breakage.get(n, 0) for n in graph.nodes()],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="B_direct"),
            line=dict(width=1, color="#333"),
        ),
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                         title=title,
                         showlegend=False,
                         hovermode="closest",
                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         width=800, height=700,
                     ))
    return fig


def plot_occurrence_timeline(
    occurrences: List[Dict[str, Any]],
    symmetric_families: Dict[int, List[int]],
    title: str = "Theme Occurrence Timeline",
) -> go.Figure:
    """绘制主题出现时间线（彩色条带按对称族着色）。"""
    fig = go.Figure()

    family_colors = {}
    color_palette = px.colors.qualitative.Plotly
    for i, fid in enumerate(symmetric_families.keys()):
        family_colors[fid] = color_palette[i % len(color_palette)]

    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])

    for occ in sorted_occs:
        fid = occ.get("family_id", 0)
        color = family_colors.get(fid, "#ccc")
        fig.add_trace(go.Scatter(
            x=[occ["sigma"][0], occ["sigma"][1]],
            y=[occ["occ_id"], occ["occ_id"]],
            mode="lines",
            line=dict(color=color, width=8),
            name=f"F_{fid}" if fid not in [t.name for t in fig.data] else None,
            showlegend=False,
            hovertext=f"Occ#{occ['occ_id']} T_{occ.get('strict_type_id','?')} F_{fid}",
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (quarterLength)",
        yaxis_title="Occurrence #",
        height=500,
    )
    return fig


def plot_similarity_heatmap(
    sim_matrix: np.ndarray,
    type_ids: list,
    title: str = "Theme Similarity Matrix S_m(T_i, T_j)",
    max_display: Optional[int] = None,
) -> go.Figure:
    """绘制主题相似度矩阵热力图。max_display=None 时显示全部类型。"""
    if max_display is None:
        n = len(type_ids)
    else:
        n = min(max_display, len(type_ids))
    sub = sim_matrix[:n, :n]
    labels = [f"T_{tid}" for tid in type_ids[:n]]

    # 自适应尺寸
    cell_size = max(8, min(22, 900 // n))
    fig_width = max(500, n * cell_size + 120)
    fig_height = max(450, n * cell_size + 80)

    fig = go.Figure(data=go.Heatmap(
        z=sub,
        x=labels,
        y=labels,
        colorscale="Viridis",
        zmin=0, zmax=1,
        colorbar=dict(title="S_m"),
    ))
    fig.update_layout(
        title=title,
        width=fig_width, height=fig_height,
        xaxis=dict(tickangle=45, tickfont=dict(size=max(7, cell_size - 2))),
        yaxis=dict(tickfont=dict(size=max(7, cell_size - 2))),
    )
    return fig


def plot_fracture_distribution(
    dynamic_metrics: List[Dict[str, Any]],
    title: str = "Dynamic Net Fracture D_dyn Distribution",
) -> go.Figure:
    """绘制 D_dyn 沿全曲时间轴的分布。"""
    t_values = [m["t_c"] for m in dynamic_metrics]
    d_values = [m["D_dyn"] for m in dynamic_metrics]
    # 也绘制 B_dyn
    b_values = [m["B_dyn"] for m in dynamic_metrics]
    c_values = [m["C_tilde"] for m in dynamic_metrics]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t_values, y=d_values,
        mode="lines+markers",
        name="D_dyn",
        line=dict(color="red", width=1.5),
        marker=dict(size=3),
    ))
    fig.add_trace(go.Scatter(
        x=t_values, y=b_values,
        mode="lines",
        name="B_dyn",
        line=dict(color="blue", width=1, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=t_values, y=c_values,
        mode="lines",
        name="C̃_res",
        line=dict(color="green", width=1, dash="dot"),
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (quarterLength)",
        yaxis_title="Value",
        height=400,
        hovermode="x",
        template="plotly_white",
    )
    fig.update_traces(line_shape='spline')
    return fig


# =============================================================================
# 新增: 丰富的可视化函数
# =============================================================================

def plot_motif_temporal_distribution(
    occurrences: List[Dict[str, Any]],
    motifs: List[Dict[str, Any]],
    top_n: int = 30,
    title: str = "Motif Temporal Distribution (Top Motifs)",
) -> go.Figure:
    """
    动机在时序上的分布 — 类似钢琴卷帘的色块图。

    横轴 = 时间, 纵轴 = 动机原型 (按出现频率排序取 Top-N),
    每个色块 = 一次主题出现, 颜色 = 所属对称族。
    """
    from collections import Counter

    motif_counts = Counter(o["motif_id"] for o in occurrences)
    top_motifs = [mid for mid, _ in motif_counts.most_common(top_n)]
    filtered = [o for o in occurrences if o["motif_id"] in top_motifs]
    sorted_occs = sorted(filtered, key=lambda o: o["sigma"][0])
    motif_to_y = {mid: i for i, mid in enumerate(top_motifs)}

    family_ids = sorted(set(o.get("family_id", 0) for o in sorted_occs))
    color_palette = px.colors.qualitative.Alphabet + px.colors.qualitative.Dark24
    family_colors = {fid: color_palette[i % len(color_palette)]
                     for i, fid in enumerate(family_ids)}

    fig = go.Figure()
    for occ in sorted_occs:
        y = motif_to_y.get(occ["motif_id"], 0)
        fid = occ.get("family_id", 0)
        color = family_colors.get(fid, "#ccc")
        fig.add_trace(go.Scatter(
            x=[occ["sigma"][0], occ["sigma"][1]],
            y=[y, y],
            mode="lines",
            line=dict(color=color, width=6),
            showlegend=False,
            hovertext=(f"μ#{occ['motif_id']} | T_{occ.get('strict_type_id','?')} | "
                       f"t=[{occ['sigma'][0]:.1f}, {occ['sigma'][1]:.1f}]"),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (quarterLength)",
        yaxis=dict(tickvals=list(range(top_n)),
                    ticktext=[f"μ#{mid}" for mid in top_motifs], dtick=1),
        height=max(500, top_n * 16),
        hovermode="closest",
    )
    return fig


def plot_theme_timeline_enhanced(
    occurrences: List[Dict[str, Any]],
    strict_types: Dict[int, List[Dict[str, Any]]],
    symmetric_families: Dict[int, List[int]],
    title: str = "Theme Occurrence Timeline (by Family)",
) -> go.Figure:
    """增强版主题时间线 — 按对称族分组，Y轴为族标签，色块=出现。"""
    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    family_first = {}
    for o in sorted_occs:
        fid = o.get("family_id")
        if fid and fid not in family_first:
            family_first[fid] = o["sigma"][0]
    sorted_families = sorted(family_first.keys(), key=lambda f: family_first[f])
    fid_to_y = {fid: i for i, fid in enumerate(sorted_families)}

    color_palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2
    fid_colors = {fid: color_palette[i % len(color_palette)]
                  for i, fid in enumerate(sorted_families)}

    fig = go.Figure()
    legend_shown = set()
    for occ in sorted_occs:
        fid = occ.get("family_id")
        if fid is None or fid not in fid_to_y:
            continue
        y = fid_to_y[fid]
        show_leg = fid not in legend_shown
        legend_shown.add(fid)
        fig.add_trace(go.Scatter(
            x=[occ["sigma"][0], occ["sigma"][1]],
            y=[y, y],
            mode="lines",
            line=dict(color=fid_colors[fid], width=14),
            name=f"F_{fid} (μ#{occ['motif_id']})",
            showlegend=show_leg,
            hovertext=(f"Occ#{occ['occ_id']} | T_{occ.get('strict_type_id','?')} | "
                       f"t=[{occ['sigma'][0]:.1f}, {occ['sigma'][1]:.1f}]"),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Time (quarterLength)",
        yaxis=dict(tickvals=list(range(len(sorted_families))),
                    ticktext=[f"F_{fid}" for fid in sorted_families], dtick=1,
                    tickfont=dict(size=9)),
        height=max(800, len(sorted_families) * 28 + 120),
        margin=dict(l=80, r=20, t=50, b=50),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01, font=dict(size=8)),
        hovermode="closest",
    )
    return fig


def plot_dynamic_metrics_timeline(
    dynamic_metrics: List[Dict[str, Any]],
    title: str = "Dynamic Fracture Metrics Timeline",
) -> go.Figure:
    """
    动态断裂指标沿时间轴的五面板图:
    D_dyn / B_dyn / C_res / T_m / E_cont+U_cad
    """
    from plotly.subplots import make_subplots

    sorted_m = sorted(dynamic_metrics, key=lambda m: m["t_c"])
    t = [m["t_c"] for m in sorted_m]
    D, B = [m["D_dyn"] for m in sorted_m], [m["B_dyn"] for m in sorted_m]
    C_raw, C_tilde = [m["C_res_raw"] for m in sorted_m], [m["C_tilde"] for m in sorted_m]
    T_m = [m["T_m"] for m in sorted_m]
    E, U = [m["E_cont"] for m in sorted_m], [m["U_cad"] for m in sorted_m]

    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        subplot_titles=(
            "D_dyn — Dynamic Net Fracture",
            "B_dyn — Dynamic Breakage Potential",
            "C_res — Residual Coherence",
            "T_m = B_dyn + C_res — Musical Toughness",
            "E_cont + U_cad — Expectation & Incompleteness",
        ),
    )
    fig.add_trace(go.Scatter(x=t, y=D, mode="lines+markers", name="D_dyn",
                              line=dict(color="red", width=1.5), marker=dict(size=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=B, mode="lines", name="B_dyn",
                              line=dict(color="blue", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=C_raw, mode="lines", name="C_res (raw)",
                              line=dict(color="green", width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=t, y=C_tilde, mode="lines", name="C̃_res (norm.)",
                              line=dict(color="limegreen", width=1, dash="dot")), row=3, col=1)
    fig.add_trace(go.Scatter(x=t, y=T_m, mode="lines", name="T_m",
                              line=dict(color="purple", width=1.5)), row=4, col=1)
    fig.add_trace(go.Scatter(x=t, y=E, mode="lines", name="E_cont",
                              line=dict(color="orange", width=1)), row=5, col=1)
    fig.add_trace(go.Scatter(x=t, y=U, mode="lines", name="U_cad",
                              line=dict(color="gray", width=1, dash="dash")), row=5, col=1)

    fig.update_layout(title=title, height=1100, hovermode="x unified",
                       showlegend=True, font=dict(size=11),
                       template="plotly_white")
    fig.update_xaxes(title_text="Time (quarterLength)", row=5, col=1)
    fig.update_traces(line_shape='spline')
    return fig


def plot_memory_activation_curves(
    occurrences: List[Dict[str, Any]],
    strict_types: Dict[int, List[Dict[str, Any]]],
    tau: float,
    top_n: int = 5,
    n_samples: int = 500,
    title: str = "Memory Activation A_i(t) — Top Theme Types",
) -> go.Figure:
    """Top-N 主题类型的记忆激活曲线 A_i(t)。"""
    from music_analysis.dynamics import memory_activation_type

    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    t_min, t_max = sorted_occs[0]["sigma"][0], sorted_occs[-1]["sigma"][1] + 2.0

    type_counts = {}
    for o in occurrences:
        tid = o.get("strict_type_id")
        if tid: type_counts[tid] = type_counts.get(tid, 0) + 1
    top_types = [tid for tid, _ in sorted(type_counts.items(), key=lambda x: -x[1])[:top_n]]

    t_vals = np.linspace(t_min, t_max, n_samples)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig = go.Figure()
    for i, tid in enumerate(top_types):
        occs_of_type = strict_types.get(tid, [])
        A_vals = [memory_activation_type(occs_of_type, t, tau) for t in t_vals]
        fig.add_trace(go.Scatter(x=t_vals, y=A_vals, mode="lines",
                                  name=f"T_{tid} ({len(occs_of_type)}×)",
                                  line=dict(color=colors[i % 5], width=2)))

        # 出现标记
        t_occ = [o["sigma"][0] for o in occs_of_type]
        fig.add_trace(go.Scatter(x=t_occ, y=[1.05 + i * 0.03] * len(t_occ),
                                  mode="markers", marker=dict(symbol="line-ns", size=8,
                                  color=colors[i % 5]), showlegend=False))

    fig.update_layout(title=title, xaxis_title="Time (quarterLength)",
                       yaxis_title="Activation A_i(t)", height=450, hovermode="x unified")
    fig.update_traces(line_shape='spline')
    return fig


def plot_theme_type_activation_matrix(
    occurrences: List[Dict[str, Any]],
    strict_types: Dict[int, List[Dict[str, Any]]],
    tau: float,
    top_n: int = 30,
    n_time_bins: int = 100,
    title: str = "Theme Type Activation Matrix",
) -> go.Figure:
    """主题类型 × 时间 激活矩阵热力图。"""
    from music_analysis.dynamics import memory_activation_type

    sorted_occs = sorted(occurrences, key=lambda o: o["sigma"][0])
    t_min, t_max = sorted_occs[0]["sigma"][0], sorted_occs[-1]["sigma"][1] + 2.0

    type_counts = {}
    for o in occurrences:
        tid = o.get("strict_type_id")
        if tid: type_counts[tid] = type_counts.get(tid, 0) + 1
    top_types = [tid for tid, _ in sorted(type_counts.items(), key=lambda x: -x[1])[:top_n]]

    time_bins = np.linspace(t_min, t_max, n_time_bins)
    Z = np.zeros((top_n, n_time_bins))
    for i, tid in enumerate(top_types):
        occs_of_type = strict_types.get(tid, [])
        for j in range(n_time_bins):
            tc = (time_bins[j] + time_bins[min(j+1, n_time_bins-1)]) / 2
            Z[i, j] = memory_activation_type(occs_of_type, tc, tau)

    fig = go.Figure(data=go.Heatmap(
        z=Z, x=time_bins, y=[f"T_{tid}" for tid in top_types],
        colorscale="Viridis", zmin=0, zmax=1, colorbar=dict(title="A_i(t)"),
    ))
    fig.update_layout(title=title, xaxis_title="Time (quarterLength)",
                       yaxis_title="Theme Type", height=max(400, top_n * 16),
                       yaxis=dict(dtick=1))
    return fig


def plot_lake_thomas_decomposition(
    breakage: Dict[int, float],
    strict_types: Dict[int, List[Dict[str, Any]]],
    graph: Any,
    top_n: int = 15,
    title: str = "Lake-Thomas Decomposition: B_sym vs B_temp",
) -> go.Figure:
    """Lake-Thomas 型分解 — B_sym (对称关系) vs B_temp (时间邻接关系) 堆叠柱状图。"""
    sorted_by_total = sorted(breakage.items(), key=lambda x: -x[1])[:top_n]
    type_ids = [tid for tid, _ in sorted_by_total]
    B_sym_vals, B_temp_vals = [], []

    for tid in type_ids:
        b_sym, b_temp = 0.0, 0.0
        for neighbor in graph.neighbors(tid):
            w = graph[tid][neighbor].get("weight", 0)
            if "sym" in str(graph[tid][neighbor].get("edge_type", "temp")):
                b_sym += w
            else:
                b_temp += w
        B_sym_vals.append(b_sym)
        B_temp_vals.append(b_temp)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="B_sym (对称关系)", x=[f"T_{tid}" for tid in type_ids],
                          y=B_sym_vals, marker_color="#636efa"))
    fig.add_trace(go.Bar(name="B_temp (时间邻接)", x=[f"T_{tid}" for tid in type_ids],
                          y=B_temp_vals, marker_color="#ef553b"))

    fig.update_layout(title=title, xaxis_title="Theme Type",
                       yaxis_title="Breakage Energy", barmode="stack",
                       height=450, hovermode="x unified")
    return fig


def plot_network_degree_distribution(
    graph: Any,
    title: str = "Theme Network — Degree Distribution",
) -> go.Figure:
    """主题网络度分布直方图。"""
    degrees = [d for _, d in graph.degree()]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=degrees, nbinsx=30, marker_color="#636efa", name="Degree"))
    if degrees:
        fig.add_vline(x=np.median(degrees), line_dash="dash", line_color="red",
                       annotation_text=f"median={np.median(degrees):.1f}")
    fig.update_layout(title=title, xaxis_title="Weighted Degree", yaxis_title="Count", height=350)
    return fig


def plot_midi_pianoroll_with_metrics(
    events: List[Dict[str, Any]],
    dynamic_metrics: List[Dict[str, Any]],
    voice_layers: Dict[Tuple[str, str], List[Dict[str, Any]]],
    title: str = "MIDI Piano Roll + Dynamic Fracture Metrics",
    metric_keys: Tuple[str, ...] = ("D_dyn", "B_dyn", "C_tilde"),
    metric_labels: Tuple[str, ...] = ("D_dyn", "B_dyn", "C̃_res"),
    metric_colors: Tuple[str, ...] = ("red", "blue", "green"),
    n_pitch_bins: int = 80,
) -> go.Figure:
    """
    MIDI 钢琴卷帘 + 动态指标叠加图。

    上方面板: 音符事件钢琴卷帘（横轴=时间, 纵轴=MIDI音高, 颜色=谱表）
    下方面板: 指定的动态指标沿时间轴的平滑曲线

    便于直观感受"哪些音符区域对应高断裂感"。
    """
    from plotly.subplots import make_subplots

    n_metrics = len(metric_keys)
    total_rows = 1 + n_metrics
    row_heights = [0.45] + [0.55 / n_metrics] * n_metrics

    fig = make_subplots(
        rows=total_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=("MIDI Piano Roll",) + metric_labels,
    )

    # --- 钢琴卷帘 ---
    # 只取音符事件（非休止）
    note_events = [e for e in events if e["p_n"] is not None]
    if not note_events:
        return fig

    t_min = min(e["t_n"] for e in note_events)
    t_max = max(e["t_n"] + e["d_n"] for e in note_events)

    # 按谱表分组, 每个谱表用 **一个** trace (而非每个音符一个trace)
    # 用 None 分隔不同音符, 避免 1352 个 traces 导致的 hover 混乱
    staff_groups: Dict[str, List[Dict]] = {}
    for e in note_events:
        staff_groups.setdefault(e["s_n"], []).append(e)

    staff_colors = {"P1-Staff1": "#1f77b4", "P1-Staff2": "#d62728"}
    for i, s in enumerate(sorted(staff_groups.keys())):
        if s not in staff_colors:
            staff_colors[s] = px.colors.qualitative.Plotly[i % 10]

    for s, evs in sorted(staff_groups.items()):
        # 按 t_n 排序
        evs.sort(key=lambda e: e["t_n"])
        x_all, y_all, hovers = [], [], []
        for e in evs:
            x_all.extend([e["t_n"], e["t_n"] + e["d_n"], None])
            y_all.extend([e["p_n"], e["p_n"], None])
            # hover 信息放起始点, 终点跳过
            hovers.extend([
                f"p={e['p_n']} d={e['d_n']:.2f} m={e['m_n']} v={e['v_n']} t={e['t_n']:.1f}",
                "", None,
            ])

        fig.add_trace(go.Scatter(
            x=x_all, y=y_all,
            mode="lines",
            line=dict(color=staff_colors.get(s, "#999"), width=2.5),
            name=s.replace("P1-", ""),
            legendgroup=s,
            hovertext=hovers,
            hoverinfo="text",
            connectgaps=False,
        ), row=1, col=1)

    fig.update_yaxes(title_text="MIDI Pitch", row=1, col=1,
                      range=[30, 100], dtick=12,
                      gridcolor="#eee")

    # --- 动态指标面板 ---
    sorted_m = sorted(dynamic_metrics, key=lambda m: m["t_c"])
    t_vals = [m["t_c"] for m in sorted_m]

    for i, (key, label, color) in enumerate(zip(metric_keys, metric_labels, metric_colors)):
        y_vals = [m[key] for m in sorted_m]
        fig.add_trace(go.Scatter(
            x=t_vals, y=y_vals,
            mode="lines",
            name=label,
            line=dict(color=color, width=1.8, shape="spline"),
            showlegend=False,
        ), row=2 + i, col=1)

        fig.update_yaxes(title_text=label, row=2 + i, col=1,
                          gridcolor="#eee")

    fig.update_xaxes(title_text="Time (quarterLength)", row=total_rows, col=1,
                      range=[t_min, t_max])

    fig.update_layout(
        title=title,
        height=280 + n_metrics * 150,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.01),
    )

    return fig


def plot_summary_dashboard(
    stats: Dict[str, Any],
    graph: nx.Graph,
    sim_matrix: np.ndarray,
    dynamic_metrics: List[Dict],
    output_path: Optional[str] = None,
) -> None:
    """生成汇总仪表盘（多子图组合）。"""
    pass  # 可后续扩展
