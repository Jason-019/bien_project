# BWV861 音乐形式化分析 — 项目思维导图

```mermaid
graph TD
    %% ===== 输入层 =====
    SCORE["🎼 BWV861_Prelude_G_minor.mxl"] --> NB01
    PAPER["📐 formalization_v1.md<br/>数学框架定义"] --> CONFIG

    %% ===== 配置 =====
    CONFIG["⚙️ config.py<br/>L_MIN/MAX, D_MIN/MAX, B_MAX<br/>W_I/R/T, LAMBDA_SYM/TEMP<br/>THETA_G, MIN_VOICE_EVENTS=20"]

    %% ===== Notebook 流水线 (左侧) =====
    subgraph PIPELINE["📓 Notebook 执行流水线 (9步)"]
        NB00["00_environment_setup<br/>✅ 验证依赖库 & music21"]
        NB01["01_event_extraction<br/>MusicXML → 离散事件 + 声部层"]
        NB02["02_window_extraction<br/>事件 → 候选窗口 Ω*"]
        NB03["03_feature_extraction<br/>窗口 → 结构特征向量 φ"]
        NB04["04_motif_prototypes<br/>φ → V4轨道压缩 → 动机原型"]
        NB05["05_theme_analysis<br/>压缩增益过滤 → 严格类型 K"]
        NB06["06_similarity_network<br/>商距离 → 相似度 → 主题网络 G_m"]
        NB07["07_dynamic_metrics<br/>记忆激活 → D_dyn/B_dyn/Ĉ_res"]
        NB08["08_final_report<br/>📊 11图 + 3表 + 诊断报告"]
    end

    NB00 --> NB01 --> NB02 --> NB03 --> NB04 --> NB05 --> NB06 --> NB07 --> NB08

    %% ===== Python 模块层 (右侧) =====
    subgraph MODULES["🐍 music_analysis/ 模块 (10个)"]
        EV["events.py<br/>extract_events()<br/>build_voice_layers()<br/>merge_sparse_voices()"]
        WIN["windows.py<br/>extract_single_voice_windows()<br/>extract_multi_voice_windows()"]
        FEAT["features.py<br/>compute_single_voice_features()<br/>compute_multi_voice_features()<br/>→ P/I/R/R̂/T/T̂"]
        MOT["motifs.py<br/>v4_identity/inversion/retrograde/RI()<br/>compute_orbit() / compute_stabilizer()"]
        TH["themes.py<br/>build_theme_occurrences()<br/>build_strict_types()<br/>compute_compression_gain()<br/>filter_by_compression_gain()"]
        DIST["distance.py<br/>interval_edit_distance()<br/>rhythm/onset_dtw_distance()<br/>quotient_distance()<br/>theme_similarity()"]
        NET["network.py<br/>build_theme_network()<br/>compute_direct_breakage()"]
        DYN["dynamics.py<br/>compute_temporal_constants()<br/>memory_activation_type()<br/>dynamic_breakage()<br/>syntactic_incompleteness()<br/>residual_coherence()<br/>compute_all_dynamic_metrics()"]
        VIZ["viz.py (11个图表函数)<br/>plot_theme_network()<br/>plot_similarity_heatmap()<br/>plot_fracture_distribution()<br/>plot_motif_temporal_distribution()<br/>plot_theme_timeline_enhanced()<br/>plot_dynamic_metrics_timeline()<br/>plot_memory_activation_curves()<br/>plot_theme_type_activation_matrix()<br/>plot_lake_thomas_decomposition()<br/>plot_network_degree_distribution()<br/>plot_midi_pianoroll_with_metrics()"]
    end

    %% Notebook → Module 调用关系
    NB01 -.-> EV
    NB02 -.-> WIN
    NB03 -.-> FEAT
    NB04 -.-> MOT
    NB05 -.-> TH
    NB06 -.-> DIST
    NB06 -.-> NET
    NB07 -.-> DYN
    NB08 -.-> VIZ

    %% 模块间依赖
    EV --> WIN
    WIN --> FEAT
    FEAT --> MOT
    MOT --> TH
    TH --> DIST
    DIST --> NET
    NET --> DYN
    CONFIG -.-> EV
    CONFIG -.-> WIN
    CONFIG -.-> FEAT
    CONFIG -.-> MOT
    CONFIG -.-> TH
    CONFIG -.-> DIST
    CONFIG -.-> NET
    CONFIG -.-> DYN

    %% ===== 数据持久化层 =====
    subgraph DATA["💾 data/ 中间结果 (pickle)"]
        D0["events.pkl<br/>voice_layers.pkl"]
        D1["windows.pkl"]
        D2["features.pkl"]
        D3["motifs.pkl"]
        D4["themes.pkl<br/>themes_filtered.pkl"]
        D5["similarity_matrix.pkl<br/>theme_network.pkl"]
        D6["dynamic_metrics.pkl"]
    end

    NB01 --> D0
    NB02 --> D1
    NB03 --> D2
    NB04 --> D3
    NB05 --> D4
    NB06 --> D5
    NB07 --> D6
    D0 --> NB02
    D1 --> NB03
    D2 --> NB04
    D3 --> NB05
    D4 --> NB06
    D5 --> NB07
    D6 --> NB08

    %% ===== 输出 =====
    NB08 --> OUTPUT["📊 最终输出<br/>11张交互式Plotly图表<br/>3张统计表格<br/>声部诊断报告"]
```

---

## 模块速查表

### Python 模块 (`music_analysis/`)

| 模块 | 行数 | 核心职责 | 被谁调用 |
|------|------|----------|----------|
| `config.py` | ~30 | 全局超参数（窗口约束、权重、阈值） | 所有模块 |
| `events.py` | ~100 | MusicXML → 离散事件 `(p_n, o_n, d_n, s_n, v_n)`；声部层构建与合并 | NB01 |
| `windows.py` | ~100 | 候选窗口提取，含 L/D/B 约束 + 同音高打结检测 | NB02 |
| `features.py` | ~60 | 窗口 → 结构特征 φ = (P,I,R,R̂,T,T̂) | NB03 |
| `motifs.py` | ~80 | V4 群作用（Identity/Inversion/Retrograde/RI）+ 轨道压缩 | NB04 |
| `themes.py` | ~120 | 主题出现构建、严格类型归类、压缩增益过滤 | NB05 |
| `distance.py` | ~100 | 商距离（interval edit + rhythm DTW + onset DTW）→ 相似度矩阵 | NB06 |
| `network.py` | ~60 | 主题网络 G_m（sym + temporal edges）+ B_direct 断裂度 | NB06 |
| `dynamics.py` | ~120 | τ_𝔇 时间常量、记忆激活 A_i(t)、D_dyn/B_dyn/Ĉ_res/U_cad | NB07 |
| `viz.py` | ~500 | 11 个 Plotly 交互图表函数 | NB08 |

### Notebook 流水线

| # | Notebook | 输入 | 输出 | 预计耗时 |
|---|----------|------|------|----------|
| 00 | `environment_setup` | — | 验证环境 | 10s |
| 01 | `event_extraction` | `.mxl` | `events.pkl`, `voice_layers.pkl` | 5s |
| 02 | `window_extraction` | `events.pkl` | `windows.pkl` | 10s |
| 03 | `feature_extraction` | `windows.pkl` | `features.pkl` | 5s |
| 04 | `motif_prototypes` | `features.pkl` | `motifs.pkl` | 5s |
| 05 | `theme_analysis` | `motifs.pkl` | `themes.pkl`, `themes_filtered.pkl` | 5s |
| 06 | `similarity_network` | `themes_filtered.pkl` | `similarity_matrix.pkl`, `theme_network.pkl` | 1s |
| 07 | `dynamic_metrics` | `theme_network.pkl` | `dynamic_metrics.pkl` | 5s |
| 08 | `final_report` | 全部 `.pkl` | 11 图表 + 3 表格 + 诊断 | 15s |

---

## 数据流简图

```
BWV861.mxl
    │
    ▼
[01] events.py ──→ events.pkl, voice_layers.pkl
    │
    ▼
[02] windows.py ──→ windows.pkl
    │
    ▼
[03] features.py ──→ features.pkl
    │
    ▼
[04] motifs.py ──→ motifs.pkl
    │
    ▼
[05] themes.py ──→ themes.pkl ──→ themes_filtered.pkl (压缩增益)
    │
    ▼
[06] distance.py ──→ similarity_matrix.pkl
     network.py  ──→ theme_network.pkl
    │
    ▼
[07] dynamics.py ──→ dynamic_metrics.pkl
    │
    ▼
[08] viz.py ──→ 11张图表 + 报告
```

---

## 关键公式 → 代码映射

| 公式 (formalization_v1.md) | 实现位置 |
|---------------------------|---------|
| ω = (p, o, d, s, v) 事件定义 | `events.py:extract_events()` |
| Ω* 候选窗口 (L/D/B 约束) | `windows.py` |
| φ = (P, I, R, R̂, T, T̂) 特征向量 | `features.py` |
| V4 群作用 (I, R, RI) | `motifs.py:v4_*()` |
| 压缩增益 ΔL | `themes.py:compute_compression_gain()` |
| d_Q([ω], [ω′]) 商距离 | `distance.py:quotient_distance()` |
| G_m = (V_m, E_sym ∪ E_temp) | `network.py:build_theme_network()` |
| B_direct 直接断裂度 | `network.py:compute_direct_breakage()` |
| A_i(t) 记忆激活 | `dynamics.py:memory_activation_type()` |
| D_dyn = B_dyn · E_cont · U_cad / Ĉ_res | `dynamics.py:compute_all_dynamic_metrics()` |
| ℓ = mean(1-s_ij) 相似度尺度 | `distance.py:theme_similarity()` |
