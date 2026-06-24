# BWV861 音乐形式化分析系统 · 项目文档

> 严格按照 `formalization_v1.md` 的数学框架，对巴赫《BWV861 G小调前奏曲》(WTC I) 进行从离散事件到动态断裂韧性指标的完整计算流水线。

---

## 项目结构

```
bien_project/
├── formalization_v1.md              # 数学形式化定义文档（理论规范）
├── BWV861_Prelude_G_minor.mxl       # 输入：巴赫 BWV861 的 MusicXML 乐谱
├── music_analysis/                  # Python 共享包 (10 个模块)
│   ├── __init__.py                  # 包入口
│   ├── config.py                    # 全局超参数与常量
│   ├── events.py                    # 离散音乐事件提取
│   ├── windows.py                   # 候选音型窗口提取
│   ├── features.py                  # 结构特征计算
│   ├── motifs.py                    # V4 群变换 / 动机原型
│   ├── themes.py                    # 主题出现 / 类型 / 压缩增益过滤
│   ├── distance.py                  # 商空间距离 / 主题相似度
│   ├── network.py                   # 主题网络 G_m
│   ├── dynamics.py                  # 记忆激活 / 断裂韧性 / 动态指标
│   └── viz.py                       # 可视化封装 (plotly)
├── notebooks/                       # 9 个 Jupyter Notebook（流水线）
│   ├── 00_environment_setup.ipynb   # 环境验证
│   ├── 01_event_extraction.ipynb    # 离散事件提取
│   ├── 02_window_extraction.ipynb   # 候选窗口
│   ├── 03_feature_extraction.ipynb  # 结构特征
│   ├── 04_motif_prototypes.ipynb    # 动机原型
│   ├── 05_theme_analysis.ipynb      # 主题分析 + 压缩增益过滤
│   ├── 06_similarity_network.ipynb  # 距离 / 相似度 / 网络
│   ├── 07_dynamic_metrics.ipynb     # 动态断裂韧性指标
│   └── 08_final_report.ipynb        # 最终报告（图表+表格）
└── data/                            # 中间数据 (pickle)
```

---

## Notebook 流水线

```
00_setup → 01_events → 02_windows → 03_features → 04_motifs → 05_themes → 06_similarity → 07_dynamics → 08_report
```

| #  | Notebook               | 输入                 | 输出                                             | 作用                                                                                            |
| -- | ---------------------- | -------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| 00 | `environment_setup`  | —                   | 验证通过的环境                                   | 安装依赖、创建包骨架、测试 music21 解析                                                         |
| 01 | `event_extraction`   | `.mxl`             | `events.pkl`, `voice_layers.pkl`             | 提取离散事件$x_n$，按 $\lambda=(s,v)$ 分层                                                  |
| 02 | `window_extraction`  | 声部分层             | `windows.pkl`                                  | 生成候选窗口$\omega$，应用 L/D/B/tie 约束                                                     |
| 03 | `feature_extraction` | 候选窗口             | `features.pkl`                                 | 计算$\phi(\omega)$: P, I, R, R̂, T, T̂                                                      |
| 04 | `motif_prototypes`   | 特征                 | `motifs.pkl`                                   | V4 群变换 → 轨道 → 动机原型$\mu$                                                            |
| 05 | `theme_analysis`     | 特征 + 动机          | `themes_filtered.pkl`                          | 主题出现$\mathfrak{o}_q$ → $T_i$ → $F_\ell$ → 压缩增益过滤                             |
| 06 | `similarity_network` | 过滤后主题           | `similarity_matrix.pkl`, `theme_network.pkl` | $d_\mathbb{Q}$ → $S_m$ → $G_m$                                                          |
| 07 | `dynamic_metrics`    | 主题 + 网络 + 相似度 | `dynamic_metrics.pkl`                          | $A_i(t)$, $B_{dyn}$, $E_{cont}$, $U_{cad}$, $C_{res}$, $D_{dyn}$, $\mathcal{T}_m$ |
| 08 | `final_report`       | 全部数据             | 交互式图表                                       | 10 张图 + 3 张统计表                                                                            |

---

## Python 模块说明

### `config.py` — 全局超参数

| 参数                            | 默认值        | 对应公式                                                                                               |
| ------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------ |
| `L_MIN`, `L_MAX`            | 3, 8          | $L_{\min} \le L \le L_{\max}$                                                                        |
| `D_MIN`, `D_MAX`            | 1.0, 8.0      | $D_{\min} \le D(\omega) \le D_{\max}$                                                                |
| `B_MAX`                       | 2             | $B(\omega) \le B_{\max}$                                                                             |
| `W_I`, `W_R`, `W_T`       | 0.5, 0.3, 0.2 | $d_\Phi = w_I d_I + w_R d_R + w_T d_T$                                                               |
| `LAMBDA_SYM`, `LAMBDA_TEMP` | 1.0, 0.5      | $w_{ij} = \lambda_{sym} \cdot \mathbf{1}[T_i\sim T_j] + \lambda_{temp} \cdot c_{ij}^{temp} / \max c$ |
| `C_REF`                       | 2.0           | $L_{model}(T_i) = \bar{L}_i + n_i \cdot c_{ref}$                                                     |
| `THETA_G`                     | 0.0           | $G_i > \theta_G$ 保留                                                                                |
| `TAU_DEFAULT`                 | 2.0           | $\tau_{\mathfrak{D}}$ 回退值                                                                         |
| `DELTA_T_MULTIPLIER`          | 2.0           | $\Delta t = 2 \cdot \tau_{\mathfrak{D}}$                                                             |

### `events.py` — 离散事件提取

**对应 Section: 离散音列事件**

| 函数                                 | 形式化公式                                                                                                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `extract_events(score)`            | $\mathcal{M} = \{x_n\}_{n=1}^N$，$x_n = (p_n, d_n, t_n, s_n, v_n, m_n, r_n, \alpha_n, \beta_n; \rho_n)$ |
| `build_voice_layers(events)`       | $\mathcal{M}^{(\lambda)} = \{x_k^{(\lambda)}\}$，$\Lambda = \{(s,v)\}$                                  |
| `_resolve_tie(el)`                 | $\beta_n^{tie} \in \{\text{start}, \text{stop}, \text{continue}\}$                                        |
| `_resolve_dynamic_for_element(el)` | $\alpha_n$ 映射 (ppp→16 … fff→127)                                                                     |
| `_collect_slur_info(score)`        | $\beta_n^{slur}$ 连音线信息                                                                               |

### `windows.py` — 候选窗口提取

**对应 Section: 局部音乐事件序列**

| 函数                                        | 形式化公式                                                                                                                     |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `extract_single_voice_windows(layer, λ)` | $\omega_{i,L}^{(\lambda)} = (x_i^{(\lambda)}, \dots, x_{i+L-1}^{(\lambda)})$                                                 |
| `check_L_constraint(L)`                   | $L_{\min} \le L \le L_{\max}$                                                                                                |
| `check_D_constraint(events)`              | $D(\omega) = t_{i+L-1}^{(\lambda)} - t_i^{(\lambda)} + d_{i+L-1}^{(\lambda)}$                                                |
| `check_B_constraint(events)`              | $B(\omega) = m_{i+L-1}^{(\lambda)} - m_i^{(\lambda)} + 1$                                                                    |
| `check_tie_constraint(events)`            | $C_{tie}(\omega)$: 起点 $\tau_i \notin \{\text{continue, stop}\}$，终点 $\tau_{i+L-1} \notin \{\text{start, continue}\}$ |
| `extract_multi_voice_windows(layers)`     | $\omega_i^{(\Lambda')}$ (首版仅 $\vert\Lambda'\vert=2$)                                                                    |
| `deduplicate_windows(windows)`            | 去重：移除时间重叠超过 80% 的相似窗口                                                                                          |

### `features.py` — 结构特征计算

**对应 Section: 从候选音型片段到结构特征**

| 函数                                      | 形式化公式                                                                                               |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `compute_single_voice_features(window)` | $\phi(\omega) = (P, I, R, \widehat{R}, T_{start\_ref}, \widehat{T}_{start\_ref})$                      |
| — 其中 P                                 | $P^\lambda(\omega) = (p_i, p_{i+1}, \dots, p_{i+L-1})$                                                 |
| — 其中 I                                 | $I^\lambda(\omega) = (p_{i+1}-p_i, \dots, p_{i+L-1}-p_{i+L-2})$                                        |
| — 其中 R̂                               | $\widehat{R}^\lambda(\omega) = (d_1/\Sigma d_j, \dots, d_L/\Sigma d_j)$                                |
| — 其中 T̂                               | $\widehat{T}_{start\_ref}^\lambda(\omega) = T_{start\_ref}^\lambda(\omega) / D^\lambda(\omega)$        |
| `compute_vertical_intervals(window)`    | $V_{\lambda_a,\lambda_b}(t) = p^{(\lambda_b)}(t) - p^{(\lambda_a)}(t)$                                 |
| `compute_voice_leading(window)`         | $C_{\lambda_a,\lambda_b}(t) = \mathrm{sgn}(\Delta p_a) \cdot \mathrm{sgn}(\Delta p_b) \in \{+1,-1,0\}$ |
| `compute_multi_voice_features(window)`  | $\phi^{multi} = (\{\phi^\lambda\}, V^{\Lambda'}, C^{\Lambda'})$                                        |

### `motifs.py` — V4 群与动机原型

**对应 Section: 动机：局部可识别模式 / 克莱因四元群**

| 函数                                 | 形式化公式                                                                       |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| `extract_phi_rel(features)`        | $\varphi = (I, \widehat{R}, \widehat{T}_{start\_ref}) \in \Phi_{rel}$          |
| `v4_identity(φ)`                  | $e \cdot \varphi = (I, \widehat{R}, \widehat{T})$                              |
| `v4_inversion(φ)`                 | $\mathcal{I} \cdot \varphi = (-I, \widehat{R}, \widehat{T})$                   |
| `v4_retrograde(φ)`                | $\mathcal{R} \cdot \varphi = (-I^{rev}, \widehat{R}^{rev}, \widehat{T}^{rev})$ |
| `v4_retrograde_inversion(φ)`      | $\mathcal{RI} \cdot \varphi = (I^{rev}, \widehat{R}^{rev}, \widehat{T}^{rev})$ |
| `compute_orbit(φ)`                | $\mu = Orb(\varphi) = \{g \cdot \varphi \mid g \in V_4\}$                      |
| `compute_stabilizer(φ)`           | $Stab(\varphi) = \{g \in V_4 \mid g \cdot \varphi = \varphi\}$                 |
| `detect_symmetry_type(φ)`         | 对称分类：asymmetric / palindromic / full_sym                                    |
| `build_motif_prototypes(features)` | $\mathcal{Q} = \Phi_{rel} / V_4$ 商空间，提取 $\mu$ 原型                     |

### `themes.py` — 主题出现 / 类型 / 压缩增益

**对应 Section: 主题出现及主题类型 + 压缩增益**

| 函数                                              | 形式化公式                                                                          |
| ------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `build_theme_occurrences(features, motifs)`     | $\mathfrak{o}_q = (\mu_q, g_q, \mathbf{P}_q, \mathbf{D}_q, \sigma_q, \kappa_q)$   |
| `build_strict_types(occurrences)`               | $T_i = [\mathfrak{o}]_{\sim_{strict}}$，$\kappa_a = \kappa_b$                   |
| `build_symmetric_families(strict_types)`        | $F_\ell = [T_i]_{\sim_{sym}}$，$\exists g \in V_4: \kappa_j = g \cdot \kappa_i$ |
| `compute_compression_gain(strict_types)`        | $G_i = L_{raw}(T_i) - L_{model}(T_i)$，$\widehat{G}_i = G_i / L_{raw}(T_i)$     |
| `filter_by_compression_gain(...)`               | 保留$\widehat{G}_i > \theta_G$ 的主题类型                                         |
| `compute_theme_importance(strict_types, gains)` | $A_i = \log(1+n_i) \cdot \widehat{G}_i$                                           |

### `distance.py` — 商空间距离与主题相似度

**对应 Section: 商空间距离与主题相似度**

| 函数                                     | 形式化公式                                                                       |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| `interval_edit_distance(I_a, I_b)`     | $d_I(I_i, I_j)$ — 归一化编辑距离                                              |
| `rhythm_dtw_distance(R̂_a, R̂_b)`    | $d_R(\widehat{R}_i, \widehat{R}_j)$ — DTW symmetric2                          |
| `onset_dtw_distance(T̂_a, T̂_b)`     | $d_T(\widehat{T}_i, \widehat{T}_j)$ — DTW symmetric2                          |
| `feature_distance(φ_a, φ_b)`         | $d_\Phi(\varphi_i, \varphi_j) = w_I d_I + w_R d_R + w_T d_T$                   |
| `quotient_distance(κ_i, κ_j)`        | $d_\mathbb{Q}(T_i, T_j) = \min_{g \in V_4} d_\Phi(\kappa_i, g \cdot \kappa_j)$ |
| `compute_scale_parameter(dist_matrix)` | $\ell = \text{median}\{d_\mathbb{Q}(T_i, T_j) > 0\}$                   |
| `theme_similarity(dist_matrix, ℓ)`    | $S_m(T_i, T_j) = \exp(-d_\mathbb{Q}(T_i, T_j) / \ell)$                         |
| `build_distance_matrix(strict_types)`  | 批量计算 K×K 距离矩阵                                                           |

### `network.py` — 主题网络

**对应 Section: 主题网络**

| 函数                                                         | 形式化公式                                                                                                |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `build_theme_network(strict_types, families, occurrences)` | $G_m = (V_m, E_m, W_m)$                                                                                 |
| — 对称边                                                    | $w_{ij}^{sym} = \lambda_{sym} \cdot \mathbf{1}[T_i \sim_{sym} T_j]$                                     |
| — 时间邻接边                                                | $c_{ij}^{temp} = \sum_{q=1}^{Q-1} \mathbf{1}[\mathfrak{o}_{(q)} \in T_i, \mathfrak{o}_{(q+1)} \in T_j]$ |
| — 总边权                                                    | $w_{ij} = \lambda_{sym} \cdot \mathbf{1}[T_i\sim T_j] + \lambda_{temp} \cdot c_{ij}^{temp} / \max c$    |
| `compute_direct_breakage(graph)`                           | $B_{direct}(T_i) = \sum_j w_{ij} = \deg(T_i) \cdot \bar{w}_i$                                           |
| `get_network_stats(graph)`                                 | 网络统计：节点数 K、边数\|E\|、密度、平均度                                                               |

### `dynamics.py` — 记忆激活与断裂韧性

**对应 Section: 从 Lake–Thomas 到音乐结构韧性**

| 函数                                                      | 形式化公式                                                                                                                  |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `compute_temporal_constants(occurrences)`               | $d_q, \delta_q, g_q, \tau_{\mathfrak{D}}, D_i^{typ}, D_{global}$                                                          |
| `memory_activation_single(σ, t, τ)`                   | $a_{\mathfrak{o}_q}(t) = 1 \; (t \in \sigma_q), \; 2^{-\Delta t/\tau_{\mathfrak{D}}} \; (t > t_q^+), \; 0 \; (t < t_q^-)$ |
| `memory_activation_type(occs, t, τ)`                   | $A_i(t) = 1 - \prod_{\mathfrak{o}_q \in T_i}(1 - a_{\mathfrak{o}_q}(t))$                                                  |
| `dynamic_breakage(tid, t_c, ...)`                       | $B_{dyn}(T_i, t_c) = A_i(t_c) \sum_j w_{ij} A_j(t_c)$                                                                     |
| `continuation_expectation(tid, t_c, ...)`               | $E_{cont}(T_i, t_c) = \frac{1}{\vert\mathcal{H}_i\vert} \sum e_q$                                                         |
| `syntactic_incompleteness(occ, typical_durs, D_global)` | $U_{cad}(\mathfrak{o}_q) = 1 - \min(1, dur / D_{ref})$ (两级回退)                                                         |
| `residual_coherence(tid, t_c, ...)`                     | $C_{res}^{dyn}(T_i, t_c) = \sum K_m(\Delta t) \cdot S_m(T_i, T(\mathfrak{o}_j))$                                          |
| `compute_all_dynamic_metrics(...)`                      | $D_{dyn} = B_{dyn} \cdot E_{cont} \cdot U_{cad} \cdot (1-\widetilde{C}_{res})$                                            |
| —                                                        | $\mathcal{T}_m = B_{dyn} + C_{res}^{dyn}$                                                                                 |

### `viz.py` — 可视化

**10 个 plotly 图表函数，对应 formalization_v1.md 后半部分的所有核心概念：**

| 函数                                  | 可视化内容                       | 对应概念                                                       |
| ------------------------------------- | -------------------------------- | -------------------------------------------------------------- |
| `plot_theme_network`                | 主题网络图                       | $G_m$ 加权无向图                                             |
| `plot_similarity_heatmap`           | 相似度矩阵热力图                 | $S_m(T_i, T_j)$                                              |
| `plot_fracture_distribution`        | D_dyn / B_dyn / C̃_res 时序曲线 | $D_{dyn}$ 分布                                               |
| `plot_motif_temporal_distribution`  | 动机时序分布                     | $\mu$ 原型沿时间的出现                                       |
| `plot_theme_timeline_enhanced`      | 增强主题时间线                   | $\mathfrak{o}_q$ / $F_\ell$ 时序结构                       |
| `plot_memory_activation_curves`     | 记忆激活曲线                     | $A_i(t)$                                                     |
| `plot_theme_type_activation_matrix` | 主题×时间激活热力图             | $A_i(t)$ 二维矩阵                                            |
| `plot_dynamic_metrics_timeline`     | 五面板动态指标图                 | $D_{dyn}, B_{dyn}, C_{res}, \mathcal{T}_m, E_{cont}+U_{cad}$ |
| `plot_lake_thomas_decomposition`    | Lake-Thomas 分解                 | $B_{sym}$ vs $B_{temp}$                                    |
| `plot_network_degree_distribution`  | 网络度分布                       | $\rho_i = \deg(T_i)$                                         |

---

## 形式化公式 → 代码精确对照表

### Phase 1: 离散音列事件

| 公式       | LaTeX                                                                    | 代码位置                                                                  |
| ---------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| 作品事件集 | $\mathcal{M} = \{x_n\}_{n=1}^N$                                        | `events.py:extract_events()` → `List[Dict]`                          |
| 事件元组   | $x_n = (p_n, d_n, t_n, s_n, v_n, m_n, r_n, \alpha_n, \beta_n; \rho_n)$ | `events.py` 中每个 `ev` dict 的键                                     |
| 力度映射   | $\alpha_n \in \{ppp,\dots,fff\} \mapsto$ MIDI                          | `config.py: DYNAMICS_MAP`, `events.py:_resolve_dynamic_for_element()` |
| Tie 信息   | $\beta_n^{tie} \in \{start, stop, continue\}$                          | `events.py:_resolve_tie()`                                              |
| 声部分层   | $\mathcal{M}^{(\lambda)} = \{x_k^{(\lambda)}\}$, $\lambda=(s,v)$     | `events.py:build_voice_layers()`                                        |

### Phase 2: 局部窗口

| 公式       | LaTeX                                                                          | 代码位置                                      |
| ---------- | ------------------------------------------------------------------------------ | --------------------------------------------- |
| 单声部窗口 | $\omega_{i,L}^{(\lambda)} = (x_i^{(\lambda)}, \dots, x_{i+L-1}^{(\lambda)})$ | `windows.py:extract_single_voice_windows()` |
| 时长约束   | $D(\omega) = t_{i+L-1} - t_i + d_{i+L-1}$                                    | `windows.py:check_D_constraint()`           |
| 小节跨度   | $B(\omega) = m_{i+L-1} - m_i + 1$                                            | `windows.py:check_B_constraint()`           |
| Tie 约束   | $C_{tie}(\omega)=1$                                                          | `windows.py:check_tie_constraint()`         |
| 多声部窗口 | $\omega_i^{(\Lambda')}$                                                      | `windows.py:extract_multi_voice_windows()`  |

### Phase 3: 结构特征

| 公式           | LaTeX                                                                                    | 代码位置                                                   |
| -------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 音高序列       | $P^\lambda(\omega) = (p_i, \dots, p_{i+L-1})$                                          | `features.py:compute_single_voice_features()` → `'P'` |
| 音程序列       | $I^\lambda(\omega) = (\Delta p_1, \dots, \Delta p_{L-1})$                              | `features.py` → `'I'`                                 |
| 归一化节奏     | $\widehat{R}^\lambda(\omega) = (d_j / \Sigma d_j)$                                     | `features.py` → `'R_hat'`                             |
| 归一化起始时间 | $\widehat{T}_{start\_ref}^\lambda(\omega)$                                             | `features.py` → `'T_hat_start_ref'`                   |
| 相对特征       | $\varphi(\omega) = (I, \widehat{R}, \widehat{T})$                                      | `features.py` → `'I' + 'R_hat' + 'T_hat_start_ref'`   |
| 纵向音程       | $V_{\lambda_a,\lambda_b}(t)$                                                           | `features.py:compute_vertical_intervals()`               |
| 声部进行       | $C_{\lambda_a,\lambda_b}(t) = \mathrm{sgn}(\Delta p_a) \cdot \mathrm{sgn}(\Delta p_b)$ | `features.py:compute_voice_leading()`                    |

### Phase 4: 动机原型 (V4 群)

| 公式     | LaTeX                                                                            | 代码位置                                |
| -------- | -------------------------------------------------------------------------------- | --------------------------------------- |
| V4 群    | $V_4 = \{e, \mathcal{I}, \mathcal{R}, \mathcal{RI}\}$                          | `config.py:V4_ELEMENTS`               |
| 恒等     | $e \cdot \varphi = (I, \widehat{R}, \widehat{T})$                              | `motifs.py:v4_identity()`             |
| 倒影     | $\mathcal{I} \cdot \varphi = (-I, \widehat{R}, \widehat{T})$                   | `motifs.py:v4_inversion()`            |
| 逆行     | $\mathcal{R} \cdot \varphi = (-I^{rev}, \widehat{R}^{rev}, \widehat{T}^{rev})$ | `motifs.py:v4_retrograde()`           |
| 逆行倒影 | $\mathcal{RI} \cdot \varphi = (I^{rev}, \widehat{R}^{rev}, \widehat{T}^{rev})$ | `motifs.py:v4_retrograde_inversion()` |
| 轨道     | $\mu = Orb(\varphi) = \{g \cdot \varphi \mid g \in V_4\}$                      | `motifs.py:compute_orbit()`           |
| 稳定子   | $Stab(\varphi) = \{g \in V_4 \mid g \cdot \varphi = \varphi\}$                 | `motifs.py:compute_stabilizer()`      |
| 商空间   | $\mathcal{Q} = \Phi_{rel} / V_4$                                               | `motifs.py:build_motif_prototypes()`  |

### Phase 5: 主题出现

| 公式     | LaTeX                                                                             | 代码位置                                 |
| -------- | --------------------------------------------------------------------------------- | ---------------------------------------- |
| 主题出现 | $\mathfrak{o}_q = (\mu_q, g_q, \mathbf{P}_q, \mathbf{D}_q, \sigma_q, \kappa_q)$ | `themes.py:build_theme_occurrences()`  |
| 严格等价 | $\mathfrak{o}_a \sim_{strict} \mathfrak{o}_b \iff \kappa_a = \kappa_b$          | `themes.py:build_strict_types()`       |
| 对称等价 | $T_i \sim_{sym} T_j \iff \exists g \in V_4: \kappa_j = g \cdot \kappa_i$        | `themes.py:build_symmetric_families()` |
| 精化链条 | $\mathfrak{O} \to \mathcal{T} \to \mathcal{F} \to \mathcal{Q}$                  | 05 notebook 输出日志                     |

### Phase 6: 距离与相似度

| 公式       | LaTeX                                                                            | 代码位置                                  |
| ---------- | -------------------------------------------------------------------------------- | ----------------------------------------- |
| 特征距离   | $d_\Phi(\varphi_i, \varphi_j) = w_I d_I + w_R d_R + w_T d_T$                   | `distance.py:feature_distance()`        |
| 商空间距离 | $d_\mathbb{Q}(T_i, T_j) = \min_{g \in V_4} d_\Phi(\kappa_i, g \cdot \kappa_j)$ | `distance.py:quotient_distance()`       |
| 尺度参数   | $\ell = \text{median}\{d_\mathbb{Q}(T_i, T_j) > 0\}$                   | `distance.py:compute_scale_parameter()` |
| 主题相似度 | $S_m(T_i, T_j) = \exp(-d_\mathbb{Q}(T_i, T_j) / \ell)$                         | `distance.py:theme_similarity()`        |

### Phase 7: 主题网络

| 公式       | LaTeX                                                                                                     | 代码位置                                           |
| ---------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 对称边权   | $w_{ij}^{sym} = \lambda_{sym} \cdot \mathbf{1}[T_i \sim_{sym} T_j]$                                     | `network.py:build_theme_network()` sym edges     |
| 邻接计数   | $c_{ij}^{temp} = \sum_{q=1}^{Q-1} \mathbf{1}[\mathfrak{o}_{(q)} \in T_i, \mathfrak{o}_{(q+1)} \in T_j]$ | `network.py:build_theme_network()` temp_counts   |
| 总边权     | $w_{ij} = \lambda_{sym} \cdot \mathbf{1}[T_i\sim T_j] + \lambda_{temp} \cdot c_{ij}^{temp} / \max c$    | `network.py:build_theme_network()` final weights |
| 直接破坏量 | $B_{direct}(T_i) = \sum_j w_{ij}$                                                                       | `network.py:compute_direct_breakage()`           |

### Phase 8: 断裂韧性

| 公式         | LaTeX                                                                                     | 代码位置                                      |
| ------------ | ----------------------------------------------------------------------------------------- | --------------------------------------------- |
| 时间尺度     | $\tau_{\mathfrak{D}} = \text{median}\{d_q\} + \text{median}\{g_q > 0\}$ | `dynamics.py:compute_temporal_constants()`  |
| 记忆衰减核   | $K_m(\Delta t) = 2^{-\Delta t / \tau_{\mathfrak{D}}}$                                   | `dynamics.py:memory_activation_single()`    |
| 主题激活     | $A_i(t) = 1 - \prod_{\mathfrak{o}_q \in T_i}(1 - a_q(t))$                               | `dynamics.py:memory_activation_type()`      |
| 动态断裂势能 | $B_{dyn}(T_i, t_c) = A_i(t_c) \sum_j w_{ij} A_j(t_c)$                                   | `dynamics.py:dynamic_breakage()`            |
| 延续预期     | $E_{cont}(T_i, t_c)$                                                                    | `dynamics.py:continuation_expectation()`    |
| 句法未闭合度 | $U_{cad}(\mathfrak{o}_q) = 1 - \min(1, dur / D_{ref})$                                  | `dynamics.py:syntactic_incompleteness()`    |
| 残余相干     | $C_{res}^{dyn}(T_i, t_c) = \sum K_m(\Delta t) S_m(T_i, T(\mathfrak{o}_j))$              | `dynamics.py:residual_coherence()`          |
| 音乐结构韧性 | $\mathcal{T}_m(T_i, t_c) = B_{dyn} + C_{res}^{dyn}$                                     | `dynamics.py:compute_all_dynamic_metrics()` |
| 动态净断裂感 | $D_{dyn} = B_{dyn} \cdot E_{cont} \cdot U_{cad} \cdot (1-\widetilde{C}_{res})$          | `dynamics.py:compute_all_dynamic_metrics()` |

### Phase 9: 压缩增益

| 公式         | LaTeX                                               | 代码位置                                   |
| ------------ | --------------------------------------------------- | ------------------------------------------ |
| 原始描述长度 | $L_{raw}(T_i) = n_i \cdot \bar{L}_i$              | `themes.py:compute_compression_gain()`   |
| 模型描述长度 | $L_{model}(T_i) = \bar{L}_i + n_i \cdot C_{REF}$  | `themes.py:compute_compression_gain()`   |
| 压缩增益     | $\widehat{G}_i = (L_{raw} - L_{model}) / L_{raw}$ | `themes.py:compute_compression_gain()`   |
| 过滤条件     | $\widehat{G}_i > \theta_G$                        | `themes.py:filter_by_compression_gain()` |
| 主题重要性   | $A_i = \log(1+n_i) \cdot \widehat{G}_i$           | `themes.py:compute_theme_importance()`   |

---

## 运行方式

> 📖 详细安装步骤见 **[INSTALL.md](INSTALL.md)**（含零基础 Python/Jupyter 安装指南）。

**快速启动（已有 conda 环境）:**

```bash
conda activate bien_music_env
jupyter notebook notebooks/
```

按顺序运行 00 → 01 → … → 08，每个 Notebook 将中间结果持久化到 `data/` 目录，可断点续跑。

**首次安装:**

```bash
# 方式 A: conda 一键安装（推荐）
conda env create -f environment.yml

# 方式 B: pip 安装
pip install -r requirements.txt
```

---

## 中间数据文件

| 文件                           | 内容                                             | 生成于 |
| ------------------------------ | ------------------------------------------------ | ------ |
| `data/events.pkl`            | 1,456 个离散事件                                 | 01     |
| `data/voice_layers.pkl`      | 6 个声部层$\mathcal{M}^{(\lambda)}$            | 01     |
| `data/windows.pkl`           | 1,048 单声部 + 698 多声部候选窗口                | 02     |
| `data/features.pkl`          | 1,746 条特征向量$\phi(\omega)$                 | 03     |
| `data/motifs.pkl`            | 718 个动机原型$\mu$                            | 04     |
| `data/themes.pkl`            | 未过滤的 718 类型 / 1,048 出现                   | 05     |
| `data/themes_filtered.pkl`   | 过滤后的 61 类型 / 323 出现 + gains + importance | 05     |
| `data/similarity_matrix.pkl` | 61×61 距离矩阵 + 相似度矩阵 + ℓ                | 06     |
| `data/theme_network.pkl`     | 主题网络$G_m$ (61 节点 189 边)                 | 06     |
| `data/dynamic_metrics.pkl`   | 323 次终止事件的完整动态指标                     | 07     |

---

## 关键设计决策

1. **音高表示**: MIDI 音高数字，休止符 $p=\emptyset$ 用 `None`
2. **和弦拆分**: 和弦拆为独立事件，共享 $t, d, s, v, m, r$
3. **U_cad 两级回退**: 类型级参考 → 全局中位时长回退（解决了 $\sim_{strict}$ 导致 $U_{cad}\equiv 0$ 的问题）
4. **压缩增益过滤**: 仅保留 $\widehat{G}_i > 0$ 的类型，K 从 718 降至 61（8.5%），Q 从 1048 降至 323（30.8%）
5. **距离计算**: $d_I$ 用归一化编辑距离 (`editdistance`)，$d_R/d_T$ 用 DTW symmetric2 (`dtw-python`)
6. **调性上下文**: 标注为可选扩展，首版未实现
7. **多声部**: 首版仅 $\vert\Lambda'\vert=2$，不扩展更高阶组合

## 当前分析结果摘要 (BWV861)

| 指标               | 值                              |
| ------------------ | ------------------------------- |
| 总事件数 N         | 1,456 (音符 1,352 + 休止符 104) |
| 声部层数\|Λ\|     | 6                               |
| 候选窗口\|Ω*\|    | 1,733                           |
| 动机原型           | 736 (非对称 729, 完全对称 7)    |
| 过滤后严格类型 K   | 52                              |
| 过滤后主题出现 Q   | 268                             |
| 主题网络           | 52 节点, 161 边, 密度 0.121     |
| 相似度尺度 ℓ      | 0.326                           |
| 最强断裂事件 D_dyn | 0.093 (事件 #380, T_14)         |

## 文献引用

dtw module的使用：

T. Giorgino. Computing and Visualizing Dynamic Time Warping Alignments in R: The dtw Package.  J. Stat. Soft., doi:10.18637/jss.v031.i07.
