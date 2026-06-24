"""
events.py — 离散音乐事件提取

从 music21 Score 对象中提取所有离散事件 x_n，完成声部分层。

事件结构:
    x_n = (p_n, d_n, t_n, s_n, v_n, m_n, r_n, α_n, β_n; ρ_n)

其中:
    p_n  — MIDI 音高 (int, 或 None 表示休止符)
    d_n  — 时值 / quarterLength (float)
    t_n  — 全局起始时间 (float)
    s_n  — 谱表/Part ID (str)
    v_n  — 声部索引 (str, 默认 '0')
    m_n  — 小节号 (int)
    r_n  — 小节内偏移 (float)
    α_n  — 力度 MIDI velocity (int 或 None)
    β_n  — 演奏法/延音线 字典
    ρ_n  — 元标签字典
"""

import pickle
from typing import Any, Dict, List, Optional, Tuple

import music21
from music21 import (
    converter, note, chord, dynamics, articulations,
    spanner, stream, meter, tie, key, tempo,
)
import numpy as np

from . import config


# =============================================================================
# 主提取函数
# =============================================================================

def extract_events(
    score: music21.stream.Score,
    resolve_dynamics: bool = True,
    resolve_ties: bool = True,
    resolve_articulations: bool = True,
    resolve_slurs: bool = True,
) -> List[Dict[str, Any]]:
    """
    从 music21 Score 中提取所有离散音乐事件。

    遍历 Score → Part → Measure → (Voice) → Note/Chord/Rest。
    和弦事件拆分为多个独立音高事件（共享 t,d,s,v,m,r）。

    Args:
        score: music21 解析后的 Score 对象
        resolve_dynamics: 是否解析力度标注（默认 True）
        resolve_ties: 是否解析延音线（默认 True）
        resolve_articulations: 是否解析运音法（默认 True）
        resolve_slurs: 是否解析连音线（默认 True）

    Returns:
        List[Dict]: 事件列表，每个事件包含完整字段
    """
    events: List[Dict[str, Any]] = []

    # 预收集全曲的动态标注（按 part_id + offset 索引）用于 resolve_dynamics
    dynamics_map: Dict[Tuple[str, float], int] = {}
    if resolve_dynamics:
        dynamics_map = _collect_dynamics(score)

    # 预收集 slur 信息
    slur_map: Dict[int, str] = {}  # note id → slur_role
    if resolve_slurs:
        slur_map = _collect_slur_info(score)

    for part in score.parts:
        part_id: str = part.id if part.id else f"Part_{part.getOffsetInHierarchy(score)}"

        # 用于计算全局 time 的累加器
        # Measure.offset 在 Part 层级上有效，但我们需要的全局 t_n 要以 score 起点为零
        # 简便方法：将 part flat 遍历，用 getOffsetInHierarchy(score)
        for m in part.getElementsByClass(stream.Measure):
            measure_num: int = m.number

            # 尝试获取 Voice 子结构
            voices = list(m.getElementsByClass(stream.Voice))
            if voices:
                # 有声部层嵌套
                for v in voices:
                    voice_id = v.id if v.id else "0"
                    _extract_from_container(
                        v, part_id, voice_id, measure_num,
                        events, dynamics_map, slur_map,
                        score, resolve_dynamics, resolve_ties,
                        resolve_articulations,
                    )
            else:
                # 无声部层嵌套，默认为单一 voice
                _extract_from_container(
                    m, part_id, "0", measure_num,
                    events, dynamics_map, slur_map,
                    score, resolve_dynamics, resolve_ties,
                    resolve_articulations,
                )

    # 最终排序: (t_n, s_n, v_n, p_n)
    events.sort(key=lambda e: (
        e["t_n"],
        e["s_n"],
        e["v_n"],
        e["p_n"] if e["p_n"] is not None else -1,
    ))

    # 分配全局索引
    for idx, ev in enumerate(events, start=1):
        ev["global_index"] = idx

    return events


def _extract_from_container(
    container,
    part_id: str,
    voice_id: str,
    measure_num: int,
    events: List[Dict],
    dynamics_map: Dict[Tuple[str, float], int],
    slur_map: Dict[int, str],
    score,
    resolve_dynamics: bool,
    resolve_ties: bool,
    resolve_articulations: bool,
) -> None:
    """从容器（Measure 或 Voice）中提取事件。"""

    for el in container:
        # --- 跳过非音乐元素 ---
        if isinstance(el, (stream.Measure, stream.Voice)):
            continue
        if isinstance(el, (music21.layout.LayoutBase, music21.clef.Clef,
                           music21.key.KeySignature, music21.meter.TimeSignature,
                           music21.bar.Barline)):
            continue

        # --- 休止符 ---
        if isinstance(el, note.Rest):
            t_global = _compute_global_offset(el, score, container)
            r_n = t_global - _measure_start_time(score, part_id, measure_num)

            ev = {
                "p_n": None,  # 休止符无音高
                "d_n": el.duration.quarterLength,
                "t_n": t_global,
                "s_n": part_id,
                "v_n": voice_id,
                "m_n": measure_num,
                "r_n": r_n,
                "alpha_n": None,
                "beta_n": {"tie": None, "articulations": [], "slur": None},
                "rho_n": {"source": "rest", "note_id": id(el)},
            }
            events.append(ev)
            continue

        # --- 和弦 ---
        if isinstance(el, chord.Chord):
            t_global = _compute_global_offset(el, score, container)
            r_n = t_global - _measure_start_time(score, part_id, measure_num)

            base_ev = {
                "d_n": el.duration.quarterLength,
                "t_n": t_global,
                "s_n": part_id,
                "v_n": voice_id,
                "m_n": measure_num,
                "r_n": r_n,
                "alpha_n": _resolve_dynamic_for_element(
                    el, part_id, dynamics_map, resolve_dynamics
                ),
                "beta_n": {
                    "tie": _resolve_tie(el, resolve_ties),
                    "articulations": _resolve_articulations_list(el, resolve_articulations),
                    "slur": slur_map.get(id(el), None),
                },
                "rho_n": {"source": "chord", "note_id": id(el)},
            }

            for p in el.pitches:
                ev = base_ev.copy()
                ev["p_n"] = p.midi
                ev["beta_n"] = base_ev["beta_n"].copy()
                ev["rho_n"] = base_ev["rho_n"].copy()
                events.append(ev)
            continue

        # --- 普通音符 ---
        if isinstance(el, note.Note):
            t_global = _compute_global_offset(el, score, container)
            r_n = t_global - _measure_start_time(score, part_id, measure_num)

            ev = {
                "p_n": el.pitch.midi,
                "d_n": el.duration.quarterLength,
                "t_n": t_global,
                "s_n": part_id,
                "v_n": voice_id,
                "m_n": measure_num,
                "r_n": r_n,
                "alpha_n": _resolve_dynamic_for_element(
                    el, part_id, dynamics_map, resolve_dynamics
                ),
                "beta_n": {
                    "tie": _resolve_tie(el, resolve_ties),
                    "articulations": _resolve_articulations_list(el, resolve_articulations),
                    "slur": slur_map.get(id(el), None),
                },
                "rho_n": {"source": "note", "note_id": id(el)},
            }
            events.append(ev)


# =============================================================================
# 辅助函数
# =============================================================================

def _compute_global_offset(
    el,
    score: music21.stream.Score,
    container,
) -> float:
    """
    计算元素在 Score 层级的全局起始时间 t_n。

    使用 music21 的 getOffsetInHierarchy(score) 方法。
    若该方法返回异常或 None，则退化为手动累加。
    """
    try:
        offset = el.getOffsetInHierarchy(score)
        if offset is not None:
            return float(offset)
    except Exception:
        pass

    # 退化方案：用 container 在 score 中的 offset + el 在 container 中的 offset
    try:
        container_offset = container.getOffsetInHierarchy(score)
        return float(container_offset + el.offset)
    except Exception:
        return float(el.offset)


def _measure_start_time(
    score: music21.stream.Score,
    part_id: str,
    measure_num: int,
) -> float:
    """计算指定小节在 Score 层级的起始时间。"""
    for part in score.parts:
        if part.id == part_id:
            for m in part.getElementsByClass(stream.Measure):
                if m.number == measure_num:
                    try:
                        return float(m.getOffsetInHierarchy(score))
                    except Exception:
                        return 0.0
    return 0.0


# ---------- 力度解析 ----------

def _collect_dynamics(score: music21.stream.Score) -> Dict[Tuple[str, float], int]:
    """
    收集全曲的动态标注，按 (part_id, offset) 索引，值为 MIDI velocity。

    Returns:
        Dict[(part_id, offset), velocity]
    """
    dyn_map: Dict[Tuple[str, float], int] = {}

    for part in score.parts:
        part_id = part.id
        for el in part.flatten().getElementsByClass(dynamics.Dynamic):
            offset = el.getOffsetInHierarchy(score)
            if offset is None:
                continue
            vel = config.dynamics_to_midi(el.value)
            if vel is not None:
                dyn_map[(part_id, float(offset))] = vel

    return dyn_map


def _resolve_dynamic_for_element(
    el,
    part_id: str,
    dynamics_map: Dict[Tuple[str, float], int],
    resolve: bool,
) -> Optional[int]:
    """为指定元素查找最近的力度标注。"""
    if not resolve:
        return None

    # 在元素所属 part 中查找 offset 不超过当前元素的最近 Dynamic
    best_vel: Optional[int] = None
    best_offset: float = -1.0

    for (p_id, offset), vel in dynamics_map.items():
        if p_id != part_id:
            continue
        if offset <= el.getOffsetInHierarchy(el.activeSite) + el.offset + 1e-9:
            if offset > best_offset:
                best_offset = offset
                best_vel = vel

    return best_vel


# ---------- 延音线解析 ----------

def _resolve_tie(el, resolve: bool) -> Optional[str]:
    """解析音符的延音线类型: 'start', 'stop', 'continue', 或 None。"""
    if not resolve:
        return None
    if el.tie is None:
        return None
    return el.tie.type  # 'start', 'stop', 'continue'


# ---------- 运音法解析 ----------

def _resolve_articulations_list(el, resolve: bool) -> List[str]:
    """解析音符的运音法标记列表。"""
    if not resolve:
        return []
    arts = []
    for a in el.articulations:
        arts.append(type(a).__name__)
    return arts


# ---------- 连音线解析 ----------

def _collect_slur_info(score: music21.stream.Score) -> Dict[int, str]:
    """
    收集全曲的连音线 (Slur) 信息。

    Returns:
        Dict[note_id → slur_role]: 'start', 'middle', 'end'
    """
    slur_map: Dict[int, str] = {}

    all_slurs = score.flatten().getElementsByClass(spanner.Slur)
    for sl in all_slurs:
        spanned = list(sl.getSpannedElements())
        for i, element in enumerate(spanned):
            eid = id(element)
            if len(spanned) == 1:
                slur_map[eid] = "single"
            elif i == 0:
                slur_map[eid] = "start"
            elif i == len(spanned) - 1:
                slur_map[eid] = "end"
            else:
                slur_map[eid] = "middle"

    return slur_map


# =============================================================================
# 声部分层
# =============================================================================

def build_voice_layers(
    events: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    将事件按声部层 λ = (s_n, v_n) 进行分层。

    返回 M^(λ) 结构，即每个 (part_id, voice_id) 对应的事件子列表。
    每个 λ 内的事件按 t_n 排序。

    Returns:
        Dict[Tuple[str, str], List[Dict]]:
            key = (staff_id, voice_id)
            value = 该层事件列表 M^(λ)
    """
    layers: Dict[Tuple[str, str], List[Dict]] = {}

    for ev in events:
        key = (ev["s_n"], ev["v_n"])
        if key not in layers:
            layers[key] = []
        layers[key].append(ev)

    # 每个 λ 内按 t_n 排序
    for key in layers:
        layers[key].sort(key=lambda e: e["t_n"])

    return layers


def merge_sparse_voices(
    events: List[Dict[str, Any]],
    voice_layers: Dict[Tuple[str, str], List[Dict[str, Any]]],
    min_events: Optional[int] = None,
) -> Tuple[List[Dict], Dict[Tuple[str, str], List[Dict]]]:
    """
    将事件数 < min_events 的稀疏声部层合并到同谱表的主声部。

    BWV861 这类键盘作品通常只有 3-6 个有效声部，
    但 MusicXML 编码器可能为少数音符创建额外的 voice ID。
    此函数过滤掉这些编码噪声。

    Args:
        events: 原始事件列表
        voice_layers: 原始声部分层
        min_events: 最少事件数阈值 (默认 config.MIN_VOICE_EVENTS)

    Returns:
        (updated_events, updated_voice_layers)
    """
    if min_events is None:
        min_events = config.MIN_VOICE_EVENTS

    # 按 staff 分组
    staffs: Dict[str, List[Tuple[str, str]]] = {}
    for (s, v) in voice_layers:
        staffs.setdefault(s, []).append((s, v))

    # 识别每个 staff 内的 major / minor 层
    major_by_staff: Dict[str, List[Tuple[str, str]]] = {}
    minor_keys: List[Tuple[str, str]] = []

    for s, layer_keys in staffs.items():
        for key in layer_keys:
            if len(voice_layers[key]) >= min_events:
                major_by_staff.setdefault(s, []).append(key)
            else:
                minor_keys.append(key)

    if not minor_keys:
        print(f"  所有声部层事件数均 ≥ {min_events}，无需合并")
        return events, voice_layers

    # 对每个 minor layer，找同 staff 中事件数最多的 major layer
    reassign_map: Dict[Tuple[str, str], str] = {}  # minor_key → new_voice_id
    for minor_key in minor_keys:
        s, v = minor_key
        majors = major_by_staff.get(s, [])
        if not majors:
            continue  # 该 staff 没有 major layer，保留原样
        # 取事件数最多的 major layer
        best = max(majors, key=lambda k: len(voice_layers[k]))
        reassign_map[minor_key] = best[1]  # new voice_id

    # 更新事件中的 v_n
    updated_count = 0
    for ev in events:
        key = (ev["s_n"], ev["v_n"])
        if key in reassign_map:
            ev["v_n"] = reassign_map[key]
            updated_count += 1

    # 重建 voice_layers
    updated_layers = build_voice_layers(events)

    n_before = len(voice_layers)
    n_after = len(updated_layers)
    print(f"  🔀 稀疏声部合并: {n_before} → {n_after} 层 "
          f"({len(minor_keys)} 个稀疏层共 {updated_count} 个事件已重分配, "
          f"阈值={min_events})")

    return events, updated_layers


# =============================================================================
# 持久化
# =============================================================================

def save_events(events: List[Dict], voice_layers: Dict) -> None:
    """将事件和声部分层持久化到 data/ 目录。"""
    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)

    with open(config.EVENTS_PKL, "wb") as f:
        pickle.dump(events, f)
    with open(config.VOICE_LAYERS_PKL, "wb") as f:
        pickle.dump(voice_layers, f)
    print(f"✅ 事件数据已保存: {config.EVENTS_PKL} ({len(events)} events)")
    print(f"✅ 声部分层已保存: {config.VOICE_LAYERS_PKL} ({len(voice_layers)} layers)")


def load_events() -> Tuple[List[Dict], Dict]:
    """从 data/ 目录加载事件和声部分层。"""
    with open(config.EVENTS_PKL, "rb") as f:
        events = pickle.load(f)
    with open(config.VOICE_LAYERS_PKL, "rb") as f:
        voice_layers = pickle.load(f)
    return events, voice_layers


# =============================================================================
# 便捷统计
# =============================================================================

def print_event_stats(events: List[Dict], voice_layers: Dict) -> None:
    """打印事件提取的统计摘要。"""
    N = len(events)
    notes = [e for e in events if e["p_n"] is not None]
    rests = [e for e in events if e["p_n"] is None]
    tied = [e for e in events if e["beta_n"]["tie"] is not None]
    with_dynamics = [e for e in events if e["alpha_n"] is not None]
    with_art = [e for e in events if e["beta_n"]["articulations"]]

    print("=" * 60)
    print("📊 事件提取统计")
    print("=" * 60)
    print(f"  总事件数 N       = {N}")
    print(f"  音符事件         = {len(notes)}")
    print(f"  休止符事件       = {len(rests)}")
    print(f"  含延音线的事件   = {len(tied)}")
    print(f"  含力度标记的事件 = {len(with_dynamics)}")
    print(f"  含运音法的事件   = {len(with_art)}")
    print(f"  声部层数 |Λ|     = {len(voice_layers)}")
    print("-" * 60)
    for (s, v), layer_events in sorted(voice_layers.items()):
        n_notes = sum(1 for e in layer_events if e["p_n"] is not None)
        print(f"  λ=({s}, {v:>4s}): {len(layer_events)} events ({n_notes} notes)")
    print("=" * 60)
