# 音乐事件、动机及主题的形式化定义

一部音乐作品看成一个**带时间顺序的离散事件系统**。

在这个系统中，最底层是 **音符/和弦音/休止等事件**，中间层是 **局部音型窗口**，更高层是 **可重复识别的动机**，再上层是 **跨多个位置出现的主题**。

用一个简单的单向流程图表示，即为：
$$
\text{event → window → motif → theme}
$$
其中每一层都比上一层更抽象。

## 离散音列事件

设一部音乐作品为一系列总数为 $N$ 个的离散音乐事件 $x_n$ 的集合 $\mathcal{M}$，即
$$
\mathcal{M} = \{x_n\}_{n=1}^N
$$
其中 $N$ 为总事件数，$x_n$ 为第 $n$ 个离散事件。

每个事件 $x_n$ 可以被完整定义为
$$
x_n = (p_n, d_n, t_n, s_n, m_n, r_n, v_n, \alpha_n, \beta_n;\rho_n)
$$
其中，

|    符号    | 含义（英文 / 中文）                                          |
| :--------: | :----------------------------------------------------------- |
|  $ p_n $   | pitch    音高                                                |
|  $ d_n $   | duration   时值                                              |
|   $t_n$    | global onset time   全局起始时间                             |
|   $s_n$    | staff / part / voice layer   谱表 / 声层                     |
|   $v_n$    | voice index  声部索引（若存在多声部）                        |
|  $ m_n $   | measure number   表示第 $n$ 个事件所在的小节号               |
|   $r_n$    | measure offset   表示第 $n$ 个事件相对于所在小节起点的时间偏移 |
| $\alpha_n$ | dynamic / loudness / intensity   力度 / 响度 / 强度          |
| $\beta_n$  | articulation / accent / note relation   演奏法 / 重音 / 音符关系 |
|  $\rho_n$  | 这个事件的元标签数据，例如事件来源、调号与谱号信息、拍号上下文、乐器与谱表信息等 |

> 注：
>
> - 在实际计算中，$p_n$ 可以有两种常见形式：
>
>   MIDI 音高数字：例如 C4 = 60，A4 = 69；
>
>   音名集合中的元素：例如 C4、F#5、B♭3。实质上是MIDI 音高数字mod 12 后的音级类别。
>
>   对于和弦事件$C_j = \left\{ p_{1},\, p_{2},\, \dotsc,\, p_{j} \right\}$，将其展开为 $j$ 个独立的音高事件 $x_1, x_2, \ldots, x_j$，每个事件拥有不同的 $p$，但共享相同的 $t$ 和 $d$。
>
>   对于休止符，没有音高，其$p_n = \emptyset$。
>
> - 时值 $d_n$ 单位通常是 quarter length，即以四分音符为基本单位。
>
> | 记谱时值               | $d_n$/quarter length |
> | :--------------------- | :------------------: |
> | 十六分音符(Semiquaver) |         0.25         |
> | 八分音符(Quaver)       |         0.5          |
> | 四分音符(Crotchet)     |         1.0          |
> | 二分音符(Minim)        |         2.0          |
> | 全音符(Semibreve)      |         4.0          |
>
> - $t_n$ 是以整部 score 的起点为零点计算的时间位置。例如，$t_n=4$ 表示距离作品开头 4 个 quarter length 的位置。在时间约束上，事件序列必须满足时间顺序 $t_1 \le t_2 \le \cdots \le t_N$ 。若存在同一时间点的多个事件，使用辅助排序规则：$(t_n,s_n,v_n,p_n)$，即先按全局时间，再按谱表、声部、音高排序。
> - $s_n$ 与 $v_n$：前者为较粗层级，可用于区分材料出现在哪个声部区域，例如右手、左手、上声部、低声部等；后者为较细层级，表示同一 part/staff 内的 voice 编号。
> - $r_n$：形式上 $r_n = t_n - t_{\text{start},m_n}$。$t_{\text{start},m_n}$是第 $m_n$ 小节的起始时间。例如，在 4/4小节中：
>
> | 小节内位置 | $r_n$ |
> | :--------- | :---: |
> | 第 1 拍    |   0   |
> | 第 2 拍    |   1   |
> | 第 3 拍    |   2   |
> | 第 4 拍    |   3   |
>
> - $\alpha_n$：表示第 $n$ 个事件所处的力度或强度状态，属于扩展字段。最简单地，可以取乐谱中的力度记号$\alpha_n \in \{ \text{ppp},\, \text{pp},\, \text{p},\, \text{mp},\, \text{mf},\, \text{f},\, \text{ff},\, \text{fff} \}$，或映射为 MIDI 常用数值：*ppp* (16), *pp* (32), *p* (48), *mp* (64), *mf* (80), *f* (96), *ff* (112), *fff* (127)。如果某个事件之前没有明确力度标记，则 $a_n = \emptyset $。
> - $\beta_n$ ：可以包含多个子属性，例如
>
> $$
> \beta_n = \bigl( \beta_n^{\text{art}},\, \beta_n^{\text{acc}},\, \beta_n^{\text{rel}} \bigr)
> $$
>
> 其中 $\beta_n^{\text{art}}$：发音法，包括Staccato（断奏）、Tenuto（保持音）、Marcato（重断奏）等；$\beta_n^{\text{acc}}$：重音，如accent（普通重音）、strong accent（强重音）等；$\beta_n^{\text{rel}}$：音符关系，如 Slur（连音线 / 圆滑线）、Tie（延音线）、Phrase Relation（乐句关系）等，同样属于扩展字段。

在实际的音乐文件中，例如 MIDI 或 MusicXML 文件，往往只记录了基本字段和某些特定字段中的一部分，例如
$$
x_n = \bigl( p_n,\, d_n,\, t_n,\, s_n,\, v_n,\ m_n,\, r_n,\,\beta_n^{\mathrm{tie}}; \rho_n\bigr)
$$

## 局部音乐事件序列

### 局部音乐事件序列

为了方便描述，我们先对 $x_n$ 按照进行谱表 $s_n$ 和声部索引 $v_n$ 进行分层，定义某一谱表和声部索引的组合为$\lambda = (s_n, v_n)$，该声部层中的 $N_\lambda$ 个局部音乐事件总序列重写为
$$
\mathcal{M}^{(\lambda)} = \{x_1^{(\lambda)},x_2^{(\lambda)},\ldots, x_n^{(\lambda)}\}
$$
此时的$x_n^{(\lambda)}$内不显含 $s_n, v_n$（已被 $\lambda$ 决定）。

所有声部层的集合记为
$$
\Lambda=\{(s,v)\mid \exists n,\ s_n=s,\ v_n=v\}.
$$

在完成声部层划分后，全曲的多声部事件结构可以表示为按声部层排列的事件族：
$$
\mathcal{M}^{\Lambda}
=
\bigl(
\mathcal{M}^{(\lambda)}
\bigr)_{\lambda\in\Lambda}
=
\bigl(
x_k^{(\lambda)}
\bigr)_{\lambda\in\Lambda,\;1\leq k\leq N_\lambda}.
$$

其中
$$
x_k^{(\lambda)}
=
(p_k^{(\lambda)},d_k^{(\lambda)},t_k^{(\lambda)},m_k^{(\lambda)},r_k^{(\lambda)},
\alpha_k^{(\lambda)},\beta_k^{(\lambda)};\rho_k^{(\lambda)}).
$$

由于谱表 \(s\) 与声部索引 \(v\) 已经由 \(\lambda=(s,v)\) 决定，故 \(x_k^{(\lambda)}\) 内不再显含 \(s_k,v_k\)。因此，\(\mathcal{M}^{\Lambda}\) 不是只保留音高的矩阵或张量，而是一个以声部层 \(\lambda\) 与局部事件序号 \(k\) 为索引的完整事件结构。其元素仍然是完整音乐事件 \(x_k^{(\lambda)}\)，因而保留音高 \(p\)、时值 \(d\)、全局起始时间 \(t\)、小节号 \(m\)、小节内偏移 \(r\)、力度 \(\alpha\)、演奏法与音符关系 \(\beta\)、以及元标签 \(\rho\) 等信息。

该表示既避免把不同声部中同时出现的音符错误地拼接为同一旋律片段，也为后续定义多声部窗口、纵向音程关系和声部进行关系提供基础。

给定声部层 $\lambda$ 后，从该层事件序列中取一个长度为 $L$ 的连续窗口：
$$
\omega_{i,L}^{(\lambda)} = \bigl( x_i^{(\lambda)}, x_{i+1}^{(\lambda)}, \dots, x_{i+L-1}^{(\lambda)} \bigr)
$$
其中 $1 \le i \le N_\lambda - L + 1$。

这里 $i$ 为窗口起点，$L$ 为窗口包含的事件数量。

因此，单层候选音型片段集合可以定义为
$$
\Omega
=
\left\{
\omega^{(\lambda)}_{i,L}
\mid
\lambda\in\Lambda,\ 
1\leq i\leq N_\lambda-L+1
\right\}
$$
其中
$$
\Lambda=\{(s,v)\mid \exists n,\ s_n=s,\ v_n=v\}
$$
单声部窗口 \(\omega_{i,L}^{(\lambda)}\) 只描述某一声部层内部的横向事件序列。为了描述多个声部在同一时间区域内共同构成的复合音型，引入声部层子集
\[
\Lambda'\subseteq \Lambda.
\]

给定一个时间区间
\[
\sigma_i=[t_i^-,t_i^+],
\]
定义该区间内、由声部层集合 \(\Lambda'\) 共同构成的多声部块窗口为
\[
\omega_{i,L}^{(\Lambda')}
=
\left\{
x_k^{(\lambda)}\in \mathcal{M}^{(\lambda)}
\ \middle|\ 
\lambda\in\Lambda',
\ t_i^- \leq t_k^{(\lambda)} < t_i^+
\right\},
\]
在多声部里，每个声部的事件数可能不一样。因此这里面的 \(L\) 表示该块窗口内的参考横向长度，通常可由主导声部或起始声部中的事件数量确定。

当 \(\Lambda'=\{\lambda\}\) 时，多声部块窗口退化为原来的单声部候选窗口：
\[
\omega_{i,L}^{(\{\lambda\})}
=
\omega_{i,L}^{(\lambda)}.
\]

由此，单声部窗口刻画的是一个声部内部的横向动机材料，而多声部块窗口刻画的是若干声部在同一时间区域中形成的纵横复合结构。

对于该局部音乐事件序列，存在两个选取约束。

### 时间跨度约束

(1) 事件数量长度 $L(\omega^{(\lambda)}_{i,L})$ 
$$
L_{\min}\leq L\leq L_{\max}
$$
(2) 由于每个事件的时值 $d_n$ 也不尽相同，还需要时间跨度约束
$$
D(\omega^{(\lambda)}_{i,L})
=
t^{(\lambda)}_{i+L-1}
-
t^{(\lambda)}_i +
d^{(\lambda)}_{i+L-1}
$$
要求 $D_{\min}
\leq
D(\omega^{(\lambda)}_{i,L})
\leq
D_{\max}$。这里 $d^{(\lambda)}_{i+L-1}$ 是指加上这个窗口中最后一个音的持续时值。

例如可以设
$$
L_{\min}=3,\quad L_{\max}=8，D_{\min}=1,\quad D_{\max}=8
$$
表示候选片段窗口至少选 3 个音，最多 8 个音，总和时长在 1 到 8 个四分音符之间。

(3) 小节跨度约束。定义窗口跨越的小节数为
$$
B(\omega^{(\lambda)}_{i,L})=m^{(\lambda)}_{i+L-1}-m^{(\lambda)}_i+1
$$
要求$B(\omega^{(\lambda)}_{i,L})
\leq B_{\max}$，例如 $B_{\max} = 2$。例：如果窗口从第 5 小节开始，到第 5 小节结束，覆盖一个小节；如果窗口从第 5 小节到第 7 小节，覆盖了5,6,7小节，共 3 个小节。

### tie（延音线）约束

候选窗口不能从一个延音线中间开始，否则会把一个被延音连接的音错误地切开。

可以定义窗口起点合法性
\[
\tau^{(\lambda)}_i \notin \{\text{continue},\text{stop}\}
\]
可以定义窗口终点合法性
$$
\tau^{(\lambda)}_{i+L-1} \notin \{\text{start},\text{continue}\}
$$
即窗口不能从 tie 的中间或结尾开始，也不能在一个 tie 尚未结束的位置截断。

我们可以定义一个布尔型的指示函数
$$
C_{\mathrm{tie}}(\omega) 
$$
 \[ C_{\mathrm{tie}}(\omega) = 1 \] 表示窗口满足 tie 约束， \[ C_{\mathrm{tie}}(\omega) = 0 \] 表示窗口不满足 tie 约束。

综合时间跨度约束和 tie 约束，可以定义单声部候选音型片段集合为：
\[
\Omega=\left\{\omega^{(\lambda)}_{i,L}\ \middle|\ \begin{aligned}&\lambda\in\Lambda,\\&L_{\min}\leq L\leq L_{\max},\\&1\leq i\leq N_\lambda-L+1,\\&D_{\min}\leq D(\omega^{(\lambda)}_{i,L})\leq D_{\max},\\&B(\omega^{(\lambda)}_{i,L})\leq B_{\max},\\&C_{\mathrm{tie}}(\omega^{(\lambda)}_{i,L})=1\end{aligned}\right\}
\]

其余扩展字段 $\alpha_n，\beta_n$ (例如力度、发音法)等若有记录，可视作加入新的约束条件或下面的结构特征特点中。

在单声部候选音型片段集合 \(\Omega\) 的基础上，可以定义多声部候选音型片段集合
$$
\Omega^{\mathrm{multi}}
=
\left\{
\omega_i^{(\Lambda')}
\ \middle|\ 
\begin{aligned}
&\Lambda'\subseteq\Lambda,\quad |\Lambda'|\geq 2,\\
&D_{\min}\leq D(\omega_i^{(\Lambda')})\leq D_{\max},\\
&B(\omega_i^{(\Lambda')})\leq B_{\max},\\
&C_{\mathrm{tie}}(\omega_i^{(\Lambda')})=1
\end{aligned}
\right\}.
$$
其中多声部窗口的时间跨度定义为
\[
D(\omega_i^{(\Lambda')})
=
t_i^+ - t_i^-.
\]

窗口跨越的小节数可以定义为
\[
B(\omega_i^{(\Lambda')})
=
\max_{x_k^{(\lambda)}\in\omega_i^{(\Lambda')}} m_k^{(\lambda)}
-
\min_{x_k^{(\lambda)}\in\omega_i^{(\Lambda')}} m_k^{(\lambda)}
+1.
\]

多声部 tie 约束要求窗口内每个参与声部层的切入点与切出点均不截断延音线：
\[
C_{\mathrm{tie}}(\omega_i^{(\Lambda')})=1
\quad\Longleftrightarrow\quad
C_{\mathrm{tie}}(\omega_i^{(\lambda)})=1
\quad \text{for all } \lambda\in\Lambda'.
\]

最终，统一的候选音型片段集合可以写为
\[
\Omega^{*}
=
\Omega
\cup
\Omega^{\mathrm{multi}}.
\]

其中 \(\Omega\) 对应单声部横向候选片段，\(\Omega^{\mathrm{multi}}\) 对应多声部纵横复合候选片段。

## 从候选音型片段到结构特征

### 单声部横向结构特征

得到候选片段 \(\omega\) 后，我们不通常直接比较原始的局部事件，而是提取它的音高轮廓和节奏结构，得到抽象动机和主题的原型。设
$$
\omega_{i,L}^{(\lambda)} = \bigl( x_i^{(\lambda)}, x_{i+1}^{(\lambda)}, \dots, x_{i+L-1}^{(\lambda)} \bigr)
$$
其音高序列为
$$
P^{\lambda}(\omega)=(p_i,p_{i+1},\ldots,p_{i+L-1})
$$
其时值序列为
$$
R^{\lambda}(\omega)=(d_i,d_{i+1},\ldots,d_{i+L-1})
$$
其音程序列为
$$
I^{\lambda}(\omega)
=
(p_{i+1}-p_i,\ p_{i+2}-p_{i+1},\ldots,p_{i+L-1}-p_{i+L-2})
$$
其相对起始时间序列为
$$
T_{\text{start ref}}^{\lambda}(\omega)
&=
(t_i-t_i,\ t_{i+1}-t_i,\ldots,t_{i+L-1}-t_i) \\ &= (0,\ t_{i+1}-t_i,\ldots,t_{i+L-1}-t_i) \\ &= (0,\Delta t_1,\ldots, \Delta t_i)
$$
因此，一个候选音型可以进一步表示为
$$
\phi(\omega)
=
(P(\omega),R(\omega),T_{\text{start ref}}(\omega))
$$
若只关心关心音高轮廓和节奏，则候选音型可以简化为
$$
\phi(\omega)
=
(I(\omega),R(\omega),T_{\text{start ref}}(\omega))
$$

### 绝对音高型

对窗口 $\omega = (x_1, \dots, x_L)$，将音高序列视为一组向量
$$
P^{\lambda}(\omega)=(p_i,p_{i+1},\ldots,p_{i+L-1})
$$
它受移调影响，但适合具体标注和代表性展示。

### 音程型

对窗口 $\omega = (x_1, \dots, x_L)$，同理，音程向量为
$$
I^{\lambda}(\omega) = (\Delta p_1, \Delta p_2, \dots, \Delta p_{L-1})
$$
其中： \[ \Delta p_k = \tilde{p}_{k+1} - \tilde{p}_k \] 音程型是最核心的结构特征，因为它通常对移调不变。 

如果整体移调 $c$： \[ \tilde{p}'_k = \tilde{p}_k + c \] ，则 \[ I(\omega') = I(\omega) \]

### 节奏型

对窗口 $\omega = (x_1, \dots, x_L)$，定义归一化节奏向量
$$
\widehat{R}^{\lambda}(\omega) = \left( \frac{d_1}{\sum_j d_j},\, \dots,\, \frac{d_L}{\sum_j d_j} \right)
$$
如果两个候选片段 $\omega^\lambda_1,\ \omega^\lambda_2$ 的 $\widehat{R}^{\lambda}(\omega)$ 相同，则它们具有严格的“节奏同一性”，互为 Augmentation（增值）或 Diminution（减值）变体。当然此特征不适用于和弦音。此处可非归一化保留$R^{\lambda}(\omega)$，在后续的动机变换中会被纳入时值变换。

### 相对起始时间归一化

对窗口 $\omega = (x_1, \dots, x_L)$，定义归一化起始时间刻向量
$$
\widehat{T}_{\text{start ref}}^{\lambda}(\omega) = \dfrac{T_{\text{start ref}}^{\lambda}(\omega)}{D^{\lambda}(\omega)}
$$
这一归一化强调事件起点之间的比例关系。在该变换下，若窗口内部事件起点的相对分布结构相同，被视为具有同一种时间比例结构。同理，此处亦可非归一化保留$T_{\text{start ref}}^{\lambda}(\omega)$，在后续的动机变换中会被纳入时值变换。

### 多声部纵向音程特征

对于多声部块窗口 \(\omega_i^{(\Lambda')}\)，除了各声部内部的横向音程结构，还需要刻画不同声部在同一时间位置上的纵向音程关系。

设 \(t\) 为窗口内的一个有效比较时刻。记声部层 \(\lambda\) 在时刻 \(t\) 上的有效发声音高为
\[
p^{(\lambda)}(t).
\]

若该声部在 \(t\) 时刻没有发声，则记
\[
p^{(\lambda)}(t)=\emptyset.
\]

对于任意两个参与声部层 \(\lambda_a,\lambda_b\in\Lambda'\)，定义纵向音程为
\[
V_{\lambda_a,\lambda_b}(t)
=
p^{(\lambda_b)}(t)-p^{(\lambda_a)}(t),
\]
其中要求 \(p^{(\lambda_a)}(t)\neq\emptyset\) 且 \(p^{(\lambda_b)}(t)\neq\emptyset\)。

由此得到多声部块窗口的纵向音程特征
\[
V^{\Lambda'}(\omega_i)
=
\left(
V_{\lambda_a,\lambda_b}(t)
\right)_{
t\in\mathcal{T}(\omega_i),\;
\lambda_a,\lambda_b\in\Lambda'
}.
\]

其中 \(\mathcal{T}(\omega_i)\) 表示该窗口内用于比较纵向关系的时间点集合。该集合可以取窗口内所有事件起点：
\[
\mathcal{T}(\omega_i)
=
\left\{
t_k^{(\lambda)}
:
x_k^{(\lambda)}\in\omega_i^{(\Lambda')}
\right\}.
\]

如果需要考虑延音、挂留与保持音，则 \(p^{(\lambda)}(t)\) 应根据事件的实际发声区间
\[
[t_k^{(\lambda)},\ t_k^{(\lambda)}+d_k^{(\lambda)})
\]
来判定，而不仅仅根据起音时刻判定。

### 声部进行关系特征

纵向音程描述的是某一时刻不同声部之间的垂直关系，而声部进行关系描述的是相邻时间位置之间，各声部如何运动。

设 \(t,t^+\in\mathcal{T}(\omega_i)\) 是窗口内相邻的两个比较时刻。定义声部层 \(\lambda\) 的局部音高运动为
\[
\Delta p_{\lambda}(t)
=
p^{(\lambda)}(t^+)-p^{(\lambda)}(t),
\]
其中要求 \(p^{(\lambda)}(t)\) 与 \(p^{(\lambda)}(t^+)\) 均不为空。

对于两个声部层 \(\lambda_a,\lambda_b\in\Lambda'\)，定义它们在 \(t\to t^+\) 上的运动关系为
\[
C_{\lambda_a,\lambda_b}(t)
=
\operatorname{sgn}\bigl(\Delta p_{\lambda_a}(t)\bigr)
\operatorname{sgn}\bigl(\Delta p_{\lambda_b}(t)\bigr).
\]

其中：
\[
C_{\lambda_a,\lambda_b}(t)=1
\]
表示两声部同向进行；

\[
C_{\lambda_a,\lambda_b}(t)=-1
\]
表示两声部反向进行；

\[
C_{\lambda_a,\lambda_b}(t)=0
\]
表示至少一个声部保持不动。

因此，多声部块窗口的声部进行特征可以写为
\[
C^{\Lambda'}(\omega_i)
=
\left(
C_{\lambda_a,\lambda_b}(t)
\right)_{
t\in\mathcal{T}(\omega_i),\;
\lambda_a,\lambda_b\in\Lambda'
}.
\]

该特征能够刻画平行、反向、斜向、保持等对位关系，为区分单纯旋律相似与多声部结构相似提供依据。

### 多声部扩展特征映射

对于单声部窗口，定义特征映射 $\Omega\rightarrow \mathcal{\Phi}$ ，则该映射将 $\Omega$ 集合空间中的窗口长度为 $L$ 的候选音型片段
$$
\omega^{(\lambda)}_{i,L}
$$
映射为 $\Phi$ 结构特征空间中同样建构在窗口长度 $L$ 上的元素
$$
\phi_{i,L}^{\lambda}(\omega)
=
(P^{\lambda}(\omega),I^{\lambda}(\omega),R^{\lambda}/\widehat{R}^{\lambda}(\omega),T_{\text{start ref}}^{\lambda}/\widehat{T}_{\text{start ref}}^{\lambda}(\omega))
$$

对于多声部块窗口 \(\omega_i^{(\Lambda')}\)，其特征应同时包含每个声部内部的横向特征，以及声部之间的纵向关系和进行关系。定义多声部扩展特征映射为
\[
\phi^{\mathrm{multi}}(\omega_i^{(\Lambda')})
=
\left(
\{\phi^{\lambda}(\omega_i)\}_{\lambda\in\Lambda'},
V^{\Lambda'}(\omega_i),
C^{\Lambda'}(\omega_i)
\right).
\]

相应地，多声部相对特征可以定义为
\[
\varphi^{\mathrm{multi}}(\omega_i^{(\Lambda')})
=
\left(
\{\varphi^{\lambda}(\omega_i)\}_{\lambda\in\Lambda'},
V^{\Lambda'}(\omega_i),
C^{\Lambda'}(\omega_i)
\right),
\]
其中
\[
\varphi^{\lambda}(\omega_i)
=
\left(
I^{\lambda}(\omega_i),
\widehat{R}^{\lambda}(\omega_i),
\widehat{T}_{\text{start ref}}^{\lambda}(\omega_i)
\right).
\]

## 动机：局部可识别模式

先以单声部情况进行讨论，结构特征空间 $\Phi$ 中的元素为 $\phi_{i,L}^{\lambda}(\omega)
=
(P^{\lambda}(\omega),I^{\lambda}(\omega),R^{\lambda}/\widehat{R}^{\lambda}(\omega),T_{\text{start ref}}^{\lambda}/\widehat{T}_{\text{start ref}}^{\lambda}(\omega))$。

为了进一步为动机的抽象铺垫，我们暂时将绝对音高型特征单独移出，即将原来的单一特征空间 $\Phi$ 分解为两个正交的子空间：音高空间与相对特征空间。

设窗口长度为 $L$，定义

1. 绝对音高空间 $\mathcal{P} \subset \mathbb{Z}^L$  
   存放绝对音高序列 $P = (p_1, p_2, \dots, p_L)$。

2. 相对特征空间 $\Phi_{\mathrm{rel}}$  
   存放内部结构关系，空间中的一个元素为 $\varphi = (I, \hat{R}, \hat{T}_{\text{start ref}})$，其中 $I$ 为音程序列，$\hat{R}, \hat{T}_{\text{start ref}}$ 为归一化节奏与发音特征。

总特征空间为两者的笛卡尔积 
$$
\Phi = \mathcal{P} \times \Phi_{\mathrm{rel}}
$$

特征映射 $\phi$ 相应分解为两部分  
$$
\phi(\omega) = \big( \underbrace{P(\omega)}_{\in \mathcal{P}},\; \underbrace{\varphi(\omega)}_{\in \Phi_{\mathrm{rel}}} \big)
$$

### 绝对音高空间 $\mathcal{P}$：一维仿射子空间

绝对音高序列是一个向量$P^{\lambda}(\omega)=(p_i,p_{i+1},\ldots,p_{i+L-1})^T$。音程序列 $I^{\lambda}(\omega)$ 可以通过差分矩阵 $\mathbf{D}_{\text{diff}}$ 提取
\[
\mathbf{I} = \mathbf{D}_{\text{diff}} \, \mathbf{P}.
\]

对于给定的相对音程特征 $\mathbf{I}$，所有满足该音程关系的绝对音高集合 $\mathcal{P}(\mathbf{I})$ 构成了 $\mathbb{R}^L$ 中的一个一维仿射子空间
\[
\mathcal{P}(\mathbf{I}) = \left\{ \mathbf{P} \in \mathbb{R}^L \mid \mathbf{P} = c \, \mathbf{1} + \mathbf{C}(\mathbf{I}), \; c \in \mathbb{R} \right\},
\]
$\mathbf{1} = (1, 1, \dots, 1)^\top$ 是全 1 向量（代表整体移调方向）；$c$ 是移调参数（即首音音高 $p_{\text{start}}$）；$\mathbf{C}(\mathbf{I}) = \bigl(0,\, i_1,\, i_1+i_2,\, \dots,\, \sum_{k=1}^{L-1} i_k \bigr)^\top$ 是由音程 $\mathbf{I}$ 决定的相对累积位移向量。

### 相对特征空间 $\Phi_\text{rel}/\Phi_\text{rel}^{\text{multi}}$: 商空间 $\mathbb{Q}$

#### 动机变换群 $G$

(1) 移调算子 $T_c$ （Transposition）
$$
T_c : \Phi_{\text{rel}} \to \Phi_{\text{rel}}
$$
音程序列 $I$ 在移调下天然不变，为恒等变换，即
$$
T_c \cdot (I, \hat{R}, \hat{T}_{\text{start ref}}) = (I,\; \hat{R},\; \hat{T}_{\text{start ref}})
$$
(2) 逆行 $R$ （Retrograde）

$$
R : \Phi_{\text{rel}} \to \Phi_{\text{rel}}
$$

$$
R \cdot (I, \hat{R}, \hat{T}) = (I^{\mathrm{rev}},\; \hat{R}^{\mathrm{rev}},\; \hat{T}_{\text{start ref}}^{\mathrm{rev}})
$$

其中上标 rev 表示序列逆序。具体地，
$$
I^{\mathrm{rev}} = (-\Delta p_{L-1},\; -\Delta p_{L-2},\; \dots,\; -\Delta p_1)
$$
(3) 倒影 $\mathcal{I}$ （Inversion）

\[
\mathcal{I} : \Phi_{\text{rel}} \to \Phi_{\text{rel}}
\]

\[
\mathcal{I} \cdot (I, \hat{R}, \hat{T}) = (-I,\; \hat{R},\; \hat{T}_{\text{start ref}})
\]

(4) 时值缩放变换 $S_k$ （Augmentation / Diminution）

\[
S_k : \Phi_{\text{rel}} \to \Phi_{\text{rel}}
\]

\[
S_k \cdot (I, \hat{R}, \hat{T}) = (I,\; \hat{R},\; \hat{T}_{\text{start ref}})
\]

归一化 $\hat{R},\; \hat{T}$ 时为恒等变换。但当 $R$ 和 $T$ 未归一化时，时值缩放 $S_k$ 的作用为：  
$S_k : \Phi_{\mathrm{rel}}^{\mathrm{un}} \to \Phi_{\mathrm{rel}}^{\mathrm{un}}$，且 $S_k \cdot (I, R, T_{\text{start ref}}) = (I,\; k \cdot R,\; k \cdot T_{\text{start ref}})$。

#### 克莱因四元群 $ V_4 $

在归一化相对特征空间 $\Phi_{\text{rel}}$ 中（移调和时值缩放已退化为恒等映射），有效的动机变换群同构于克莱因四元群
$$
G \cong V_4 \cong \mathbb{Z}_2 \times \mathbb{Z}_2
$$
群 $V_4$ 包含四个元素 $V_4 = \{e, \mathcal{I}, \mathcal{R}, \mathcal{RI}\}$：
*   **$e$ (Identity / 原形)**：恒等变换。
*   **$\mathcal{I}$ (Inversion / 倒影)**：生成元之一，二阶元素（$\mathcal{I}^2 = e$）。
*   **$\mathcal{R}$ (Retrograde / 逆行)**：生成元之一，二阶元素（$\mathcal{R}^2 = e$）。
*   **$\mathcal{RI}$ (Retrograde-Inversion / 逆行倒影)**：复合元素，$\mathcal{RI} = \mathcal{R} \circ \mathcal{I} = \mathcal{I} \circ \mathcal{R}$。

##### 群乘法表 (Cayley Table)
$V_4$ 是一个阿贝尔群，且**每个非单位元都是对合的（自逆的）**。其乘法表如下：

| $\circ$            |      $e$       | $\mathcal{I}$  | $\mathcal{R}$  | $\mathcal{RI}$ |
| :----------------- | :------------: | :------------: | :------------: | :------------: |
| **$e$**            |      $e$       | $\mathcal{I}$  | $\mathcal{R}$  | $\mathcal{RI}$ |
| **$\mathcal{I}$**  | $\mathcal{I}$  |      $e$       | $\mathcal{RI}$ | $\mathcal{R}$  |
| **$\mathcal{R}$**  | $\mathcal{R}$  | $\mathcal{RI}$ |      $e$       | $\mathcal{I}$  |
| **$\mathcal{RI}$** | $\mathcal{RI}$ | $\mathcal{R}$  | $\mathcal{I}$  |      $e$       |

*音乐意义：任何两种不同的非平凡变换叠加，必然等价于第三种非平凡变换。例如，对倒影进行逆行，必然得到逆行倒影。*

1.  **$e \cdot \varphi = (I, \hat{R}, \hat{T}_{\text{start ref}})$**
2.  **$\mathcal{I} \cdot \varphi = (-I, \hat{R}, \hat{T}_{\text{start ref}})$** （仅音程空间取反）
3.  **$\mathcal{R} \cdot \varphi = (-I^{\text{rev}}, \hat{R}^{\text{rev}}, \hat{T}_{\text{start ref}}^{\text{rev}})$** （音程取反且逆序，节奏/发音逆序）
4.  **$\mathcal{RI} \cdot \varphi = (I^{\text{rev}}, \hat{R}^{\text{rev}}, \hat{T}_{\text{start ref}}^{\text{rev}})$** （仅序列纯逆序，音程不取反）

在 $V_4$ 框架下，“动机”可视作一个**代数几何对象**。

##### 动机原型作为轨道 (Orbit)和商空间点
动机原型 $\mu$ 被定义为相对特征空间 $\Phi_{\text{rel}}$ 在 $ V_4 $ 作用下的一条**轨道**， 
$$
\mu = \text{Orb}(\varphi) = \{ g \cdot \varphi \mid g \in V_4 \} \subset \Phi_{\text{rel}}
$$
或是通过商映射，轨道在商空间 $\Phi_{\text{rel}} / V_4$ 中被坍缩为一个正则点/奇异点。正则点代表了不具备内部对称性的常规动机；而对于具有内部对称性的动机，其稳定子群非平凡，轨道大小退化为 2，商空间在这些点处发生了“折叠”或“锥化”，形成奇点。

##### 稳定子 (Stabilizer) 与对称动机
稳定子群定义为保持特征不变的群元素集合：
$$ \text{Stab}(\varphi) = \{ g \in V_4 \mid g \cdot \varphi = \varphi \} $$

*   **一般动机（非对称）**：$\text{Stab}(\varphi) = \{e\}$。轨道大小为 $4/1 = 4$。（包含原形、倒影、逆行、逆行倒影 4 种不同形态）。
*   **节奏回文动机**：如果 $\hat{R} = \hat{R}^{\text{rev}}$ 且 $\hat{T}_{\text{start ref}} = \hat{T}_{\text{start ref}}^{\text{rev}}$，但音程不对称。此时 $\mathcal{RI}$ 不能使音程不变（除非音程也是回文），但如果音程满足 $I = -I^{\text{rev}}$，则 $\mathcal{R} \cdot \varphi = \varphi$。
*   **完全对称动机**：如果 $\varphi$ 满足 $I = I^{\text{rev}}$（音程回文）且 $\hat{R} = \hat{R}^{\text{rev}}$，则 $\mathcal{RI} \cdot \varphi = \varphi$。此时 $\text{Stab}(\varphi) = \{e, \mathcal{RI}\} \cong \mathbb{Z}_2$。轨道大小退化为 $4/2 = 2$。

#### 商集与动机间的距离度量

如果我们将所有可能的归一化所有相对特征向量构成的裸集合记为 $\Phi_{\text{rel}}$，那么**所有可能的动机原型**构成了 $\Phi_{\text{rel}}$ 在 $ V_4 $ 作用下的**商集 (Quotient Set)**
$$
\mathcal{Q}= \Phi_{\text{rel}} / V_4
$$
它将动机出现严格分类为离散的形态轨道。

商集 $\mathcal{Q}$ 中的每一个点（等价类）就是一个动机原型 $\mu$。

若该商集提升为度量商空间 $\mathbb{Q}$，在商空间中，两个动机 $\mu_A$ 和 $\mu_B$ 之间的距离可以定义为它们轨道之间的**豪斯多夫距离 (Hausdorff Distance)** 或**最小匹配距离**

$$
d_{\mathbb{Q}}(\mu_A, \mu_B) = \min_{g_1, g_2 \in V_4} d_{\Phi}(g_1 \cdot \varphi_A, g_2 \cdot \varphi_B)
$$
由于 $ V_4 $ 是群，上式等价于
$$
d_{\mathbb{Q}}(\mu_A, \mu_B) = \min_{g \in V_4} d_{\Phi}(\varphi_A, g \cdot \varphi_B)
$$
要比较两个动机，不需要比较所有 $4 \times 4 = 16$ 种组合，只需要固定 A 的原形，将 B 的 4 种形态（$e, \mathcal{I}, \mathcal{R}, \mathcal{RI}$）分别与 A 计算距离，取最小值即可。这对我们后面主题相似度的计算存在启发。

动机原型空间即为商空间 $\mathbb{Q}$。至此，我们建立了一个纯粹的代数分类系统，以代表抽象的“动机的灵魂——动机原型”。

### 多声部情况拓展

由原来的相对特征空间
$$
\Phi_{\mathrm{rel}}
=
\mathcal{I}\times\widehat{\mathcal{R}}\times\widehat{\mathcal{T}}_{\text{start ref}}
$$
可以扩展为
$$
\Phi_{\mathrm{rel}}^{\mathrm{multi}}
=
\Phi_{\mathrm{hor}}
\times
\Phi_{\mathrm{vert}}
\times
\Phi_{\mathrm{cp}},
$$
其中：
$$
\Phi_{\mathrm{hor}}
$$
表示各声部内部的横向相对特征空间；

$$
\Phi_{\mathrm{vert}}
$$
表示纵向音程关系空间；

$$
\Phi_{\mathrm{cp}}
$$
表示声部进行关系空间。

当 \(|\Lambda'|=1\) 时，纵向音程关系和声部进行关系退化为空结构，\(\Phi_{\mathrm{rel}}^{\mathrm{multi}}\) 退化为原来的 \(\Phi_{\mathrm{rel}}\)。

#### 多声部容许置换群 \(\Pi_{\Lambda'}^{\mathrm{adm}}\)

在单声部动机中，主要考虑的是音程倒影、逆行与逆行倒影等横向变换。但在多声部结构中，还可能出现声部之间的对应关系变化。例如，两个内声部之间可能交换材料，而高声部与低声部通常不应被视为可任意互换，因为它们承担不同的结构功能。

因此，对于参与多声部块窗口的声部层集合 \(\Lambda'\)，定义容许声部置换群
\[
\Pi_{\Lambda'}^{\mathrm{adm}}
\subseteq
S_{\Lambda'},
\]
其中 \(S_{\Lambda'}\) 是声部层集合 \(\Lambda'\) 上的全置换群。

所谓“容许”，是指只允许功能角色相同或相近的声部层之间进行置换。例如，同属内声部的两个声部可以互换，而旋律高声部与低音支撑声部通常不互换。具体的容许关系可由乐器、谱表、音域、声部功能或人工标注共同决定。

置换 \(\pi\in\Pi_{\Lambda'}^{\mathrm{adm}}\) 对多声部相对特征的作用为
\[
\pi\cdot
\varphi^{\mathrm{multi}}(\omega_i^{(\Lambda')})
=
\left(
\{\varphi^{\pi(\lambda)}(\omega_i)\}_{\lambda\in\Lambda'},
\pi\cdot V^{\Lambda'}(\omega_i),
\pi\cdot C^{\Lambda'}(\omega_i)
\right).
\]

其中 \(\pi\cdot V^{\Lambda'}\) 表示对纵向音程矩阵中的声部标签进行同步置换，\(\pi\cdot C^{\Lambda'}\) 表示对声部进行关系矩阵中的声部标签进行同步置换。

#### 多声部扩展变换群 \(G_{\Lambda'}\)

对于单声部相对特征，原文中的有效动机变换群为
\[
V_4=\{e,\mathcal{I},\mathcal{R},\mathcal{RI}\}.
\]

对于多声部相对特征，需要同时考虑横向动机变换与声部层置换。因此定义多声部扩展变换群为
\[
G_{\Lambda'}
=
V_4
\times
\Pi_{\Lambda'}^{\mathrm{adm}}.
\]

其中，\(V_4\) 作用于各声部内部的横向相对特征：
\[
\{\varphi^{\lambda}\}_{\lambda\in\Lambda'},
\]
而 \(\Pi_{\Lambda'}^{\mathrm{adm}}\) 作用于声部标签，并同步作用于纵向音程特征 \(V^{\Lambda'}\) 与声部进行特征 \(C^{\Lambda'}\)。

于是，多声部动机原型可以定义为 \(\Phi_{\mathrm{rel}}^{\mathrm{multi}}\) 在 \(G_{\Lambda'}\) 作用下的轨道：
\[
\mu^{\mathrm{multi}}
=
\operatorname{Orb}_{G_{\Lambda'}}
\bigl(
\varphi^{\mathrm{multi}}
\bigr)
=
\left\{
g\cdot\varphi^{\mathrm{multi}}
:
g\in G_{\Lambda'}
\right\}.
\]

相应的多声部动机原型空间为商空间
\[
\mathbb{Q}^{\mathrm{multi}}
=
\Phi_{\mathrm{rel}}^{\mathrm{multi}}
/
G_{\Lambda'}.
\]

当 \(|\Lambda'|=1\) 时，
\[
\Pi_{\Lambda'}^{\mathrm{adm}}=\{e\},
\]
因此
\[
G_{\Lambda'}=V_4,
\qquad
\mathbb{Q}^{\mathrm{multi}}=\mathbb{Q}.
\]

也就是说，原来的单声部动机空间是多声部动机空间的特例。

### 动机原型与动机具体出现

乐谱中每一次具体的动机出现，在一个新空间中被严格定义为实例化的一个点
$$
o(q) = (\mu,g_q,\mathbf{P_q},\mathbf{D_q},\sigma_q)
$$
其中

| 符号             | 数学空间                                                     | 角色与含义                                                   |
| :--------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| $\mu$            | $ \in \mathcal{M}_{\mathrm{motif}} = \Phi_{\mathrm{rel}}/V_4 $ | 动机身份（分类）：所属的  $ V_4 $  轨道（原型）。            |
| $ g_q $          | $ \in V_4 $                                                  | 形态同构（分类）：指明当前是原型的哪一种变体（ $ \{e, \mathcal{I}, \mathcal{R}, \mathcal{RI}\} $ ）。 |
| $ \mathbf{P}_q $ | $ \in \mathbb{R}^L $                                         | 绝对音高状态（物理）：完整的绝对音高序列向量。               |
| $ \mathbf{D}_q $ | $ \in \mathbb{R}^L $                                         | 绝对时值状态（物理）：完整的绝对时值序列向量。               |
| $ \sigma_q $     | $ \subset \mathbb{R} $                                       | 时空坐标（物理）：在乐谱/音频时间轴上的绝对起止区间  $ [t_q^-, t_q^+] $ 。 |

> [!IMPORTANT]
>
> 下标 q 代表的是“实例索引（Instance Index / Occurrence Index）”，或者更准确地说，是离散发声事件的序号（Discrete Sounding Event Index）。在乐谱或音频中，同一个动机原型 $\mu$ 会在不同的时间、以不同的变体**多次出现**，$q$ 标记了该动机原型在时间轴上的第 $q$ 次具体发声事件。

对于动机原型 $\mu$ 和动机实例 $o$，可定义一个**识别映射** $\pi$，模拟从动机实例 $o$ 提取动机原型 $\mu$ 的过程
$$
\pi : \mathcal{O} \to \mathcal{Q}, \quad o(t) \mapsto \mu
$$
对于一个具体的实例 $o(t) = (\mu, g_q, \mathbf{P}_q, \mathbf{D}_q, \sigma_q)$ ，映射 $\pi$ 首先“忽略”其绝对音高 $ \mathbf{P}_q $（移调不变性）和绝对时值 $ \mathbf{D}_q $（缩放不变性）。接着，$\pi$ 剥离其具体的形态变体 $g_q \in V_4$（例如，大脑/算法能听出“逆行倒影”依然是同一个动机）。最终，$\pi(o(t))$ 输出唯一的等价类 $\mu \in \mathcal{Q}$。  

这个投影映射 $\pi$ 形式化了音乐认知中的“格式塔恒常性（Gestalt Constancy）”。例如，贝多芬《命运交响曲》的“三短一长”动机，无论是在 C 小调由弦乐猛烈奏出，还是在降 E 调由木管轻柔吹出，甚至是被逆行演奏，都能通过 $\pi$ 将其识别为同一个动机 $\mu$。

当多个动机实例在时间轴上按照特定的句法逻辑（Syntax）进行排列，并通过和声与节奏的缝隙相互缝合，最终形成一个具有宏观轮廓和闭合感的有机体时，动机便发生了相变，跃升为了**主题（Theme）**。

## 主题出现及主题类型

### 主题出现

在动机实例 $o(q)$ 的基础上，**主题出现**是一个扩展元组

$$
\mathfrak{o}_q = \bigl(\mu_q,\; g_q,\; \mathbf{P}_q,\; \mathbf{D}_q,\; \sigma_q,\; \kappa_q \bigr)
$$

其中各分量的含义为：

| 符号           | 空间                                                   | 含义                                                         |
| :------------- | :----------------------------------------------------- | :----------------------------------------------------------- |
| $\mu_q$        | $\in \mathcal{Q} = \Phi_{\mathrm{rel}}/V_4$            | 动机原型：所属的 $V_4$ 轨道                                  |
| $g_q$          | $\in V_4 = \{e,\mathcal{I},\mathcal{R},\mathcal{RI}\}$ | 形态变体：当前出现是原型的哪一种变换                         |
| $\mathbf{P}_q$ | $\in \mathbb{Z}^L$                                     | 绝对音高序列                                                 |
| $\mathbf{D}_q$ | $\in \mathbb{R}_{>0}^L$                                | 绝对时值序列                                                 |
| $\sigma_q$     | $= [t_q^-,\, t_q^+] \subset \mathbb{R}$                | 时空坐标，即全局时间区间                                     |
| $\kappa_q$     | $\in \Phi_{\mathrm{rel}}$                              | **严格键**（strict key）：归一化后的完整相对特征向量 $\varphi(\omega_q)$ |

严格键 $\kappa_q$ 与动机原型 $\mu_q$ 的关系：

$$
\kappa_q \equiv \varphi(\omega_q) \in \Phi_{\mathrm{rel}}, \qquad \mu_q = \pi(\mathfrak{o}_q) =[\varphi(\omega_q)]_{V_4} \in \mathcal{Q}
$$

即 $\mu_q$ 是 $\kappa_q$ 在 $ V_4 $ 作用下的等价类。$\kappa_q$ 比 $\mu_q$ 更细：它不仅知道"是哪个动机原型"，还知道"当前是哪种变换形态"。

### 多声部主题出现

对于由多声部块窗口 \(\omega_i^{(\Lambda')}\) 生成的主题出现，需要记录其参与声部集合与多声部严格键。因此，多声部主题出现可以定义为
$$
\mathfrak{o}_q^{\mathrm{multi}}
=
\bigl(
\mu_q^{\mathrm{multi}},
g_q,
\Lambda'_q,
\mathbf{P}_q^{\Lambda'},
\mathbf{D}_q^{\Lambda'},
\sigma_q,
\kappa_q^{\mathrm{multi}}
\bigr).
$$

| 符号                                                         | 含义                                   |
| ------------------------------------------------------------ | -------------------------------------- |
| $ \mu_q^{\mathrm{multi}} \in \mathbb{Q}^{\mathrm{multi}} $   | 多声部动机原型                         |
| $ g_q \in G_{\Lambda'_q} $                                   | 当前多声部主题出现相对于原型的具体变换 |
| $ \Lambda'_q \subseteq \Lambda $                             | 该主题出现所涉及的声部层集合           |
| $ \mathbf{P}_q^{\Lambda'} $                                  | 所有参与声部的绝对音高状态             |
| $ \mathbf{D}_q^{\Lambda'} $                                  | 所有参与声部的绝对时值状态             |
| $ \sigma_q = [t_q^-, t_q^+] $                                | 该多声部主题出现的全局时间区间         |
| $ \kappa_q^{\mathrm{multi}} = \varphi^{\mathrm{multi}}(\omega_q^{(\Lambda'*q)}) \in \Phi*{\mathrm{rel}}^{\mathrm{multi}} $ | 该主题出现的多声部严格键               |

此时，单声部主题出现
$$
\mathfrak{o}_q
=
(\mu_q,g_q,\mathbf{P}_q,\mathbf{D}_q,\sigma_q,\kappa_q)
$$
可以看作 \(|\Lambda'_q|=1\) 时的特例。

设全部主题出现的集合为

$$
\mathfrak{O} = \bigl\{\mathfrak{o}_q/ \mathfrak{o}_q^{\text{multi}} \bigr\}_{q=1}^{Q}
$$

在 $\mathfrak{O}$ 上定义两种主题出现之间存在的关系：**严格等价关系**和**对称等价关系**。

### **严格等价关系** $\sim_{\mathrm{strict}}$

$$
\mathfrak{o}_a \sim_{\mathrm{strict}} \mathfrak{o}_b
\quad \Longleftrightarrow \quad
\kappa(\mathfrak{o}_a) = \kappa(\mathfrak{o}_b)
$$

即两个主题出现的归一化相对特征向量 $\varphi(\omega_q)$ 完全相同。这意味着它们不仅属于同一动机原型，还使用了同一种 $ V_4 $ 形态变体。

每一个等价类称为一个**严格主题类型**

$$
T_i = [\mathfrak{o}]_{\sim_{\mathrm{strict}}} = \bigl\{ \mathfrak{o}_q \in \mathfrak{O} : \kappa(\mathfrak{o}_q) = \kappa_i \bigr\}
$$

全部严格主题类型的集合为商集 $\mathcal{T}$

$$
\mathcal{T} = \mathfrak{O} \,/\, {\sim_{\mathrm{strict}}} = \{T_1, T_2, \dots, T_K\}
$$

每个 $T_i$ 携带一个典范代表特征 $\kappa_i \in \Phi_{\mathrm{rel}}$，以及一个 $ V_4 $ 形态标签 $g_i \in V_4$（满足 $\kappa_i = g_i \cdot \varphi_{\text{canon}}$，其中 $\varphi_{\text{canon}}$ 为该族的原形特征向量）。

### 对称等价关系 $\sim_{\mathrm{sym}}$

**对称等价关系** $\sim_{\mathrm{sym}}$：
$$
T_i \sim_{\mathrm{sym}} T_j
\quad \Longleftrightarrow \quad
\mu(T_i) = \mu(T_j)
\quad \Longleftrightarrow \quad
\exists\, g \in V_4 : \kappa_j = g \cdot \kappa_i
$$

#### 对称族

每一个对称等价类称为一个**对称族**

$$
F_\ell = [T_i]_{\sim_{\mathrm{sym}}} = \bigl\{ T_j \in \mathcal{T} : \mu(T_j) = \mu_\ell \bigr\}
$$

全部对称族构成二级商集

$$
\mathcal{F} = \mathcal{T} \,/\, {\sim_{\mathrm{sym}}} \;\cong\; \mathfrak{O} \,/\, {\sim_{\mathrm{sym}}}
$$

### 等价关系的精化链条

由于 $\sim_{\mathrm{strict}}$ 比 $\sim_{\mathrm{sym}}$ 更细，存在自然的满射投影

$$
\mathfrak{O}
\;\xrightarrow{\;\pi_{\mathrm{strict}}\;}
\mathcal{T}
\;\xrightarrow{\;\pi_{\mathrm{sym}}\;}
\mathcal{F}
\;\xrightarrow{\;\pi_{\mathcal{Q}}\;}
\mathcal{Q}
$$

由轨道-稳定子定理，每个对称族所含的严格主题类型数满足

$$
|F_\ell| = \frac{|V_4|}{|\mathrm{Stab}(\varphi_i)|} \leq 4
$$

若 $\mathrm{Stab}(\varphi_i) = \{e\}$（一般非对称动机），则 $F_\ell$ 恰好包含四个严格类型，对应 $\{e, \mathcal{I}, \mathcal{R}, \mathcal{RI}\}$ 四种变体。若动机具有内部对称性（如节奏回文），稳定子非平凡，族内类型数相应退化。

对于多声部主题出现，严格等价关系改写为
\[
\mathfrak{o}_a^{\mathrm{multi}}
\sim_{\mathrm{strict}}
\mathfrak{o}_b^{\mathrm{multi}}
\quad\Longleftrightarrow\quad
\kappa_a^{\mathrm{multi}}
=
\kappa_b^{\mathrm{multi}}.
\]

对称等价关系改写为
\[
T_i^{\mathrm{multi}}
\sim_{\mathrm{sym}}
T_j^{\mathrm{multi}}
\quad\Longleftrightarrow\quad
\exists g\in G_{\Lambda'}:
\kappa_j^{\mathrm{multi}}
=
g\cdot \kappa_i^{\mathrm{multi}}.
\]

### $^*$可选调性上下文层

本模型的核心主题识别与断裂计算不依赖调性假设。严格主题类型 \(T_i\)、对称族 \(F_\ell\) 与商空间距离 \(d_{\mathbb Q}\) 均由归一化相对特征与动机变换群决定，因此同样适用于调性、泛调性、中心音音乐与无调性音乐。

若作品具有明确或局部可估计的调性结构，可为每次主题出现附加一个可选调性上下文标签
\[
\theta_q\in \Theta\cup\{\bot\}.
\]
其中 \(\Theta\) 表示调性或音高中心上下文空间，\(\bot\) 表示无明确调性、不可判定调性或不启用调性层。

于是主题出现可扩展为
\[
\mathfrak{o}_q
=
(\mu_q,g_q,\mathbf{P}_q,\mathbf{D}_q,\sigma_q,\kappa_q;\theta_q).
\]

分号后的 \(\theta_q\) 不参与严格等价关系：
\[
\mathfrak{o}_a\sim_{\mathrm{strict}}\mathfrak{o}_b
\Longleftrightarrow
\kappa_a=\kappa_b.
\]
因此，调性上下文不改变主题身份，只作为后续相似度计算中的可选修正项，详见主题相似度部分。

## 商空间距离与主题相似度

### 单声部商空间距离

回顾：前面已经定义了归一化相对特征空间
\[
\Phi_{\text{rel}} = \mathcal{I} \times \widehat{\mathcal{R}} \times \widehat{\mathcal{T}}_{\text{start ref}}
\]

其中一个候选音型的相对特征可写为
\[
\varphi(\omega) = \bigl( I(\omega),\, \widehat{R}(\omega),\, \widehat{T}_{\text{start ref}}(\omega) \bigr) \in \Phi_{\text{rel}}.
\]

动机变换群为
\[
V_4 = \{ e,\, \mathcal{I},\, \mathcal{R},\, \mathcal{R}\mathcal{I} \},
\]
其中
$$
\begin{align*}
e \cdot \varphi &= \bigl( I,\, \widehat{R},\, \widehat{T}_{\text{start ref}} \bigr), \\
\mathcal{I} \cdot \varphi &= \bigl( -I,\, \widehat{R},\, \widehat{T}_{\text{start ref}} \bigr), \\
\mathcal{R} \cdot \varphi &= \bigl( -I^{\mathrm{rev}},\, \widehat{R}^{\mathrm{rev}},\, \widehat{T}_{\text{start ref}}^{\mathrm{rev}} \bigr), \\
\mathcal{R}\mathcal{I} \cdot \varphi &= \bigl( I^{\mathrm{rev}},\, \widehat{R}^{\mathrm{rev}},\, \widehat{T}_{\text{start ref}}^{\mathrm{rev}} \bigr).
\end{align*}
$$
因此，每个动机原型不是一个单独的向量，而是一个 $V_4$ 轨道：
\[
\mu = Orb(\varphi) = \{ g \cdot \varphi : g \in V_4 \}.
\]
因此，要考虑任意主题类型 $T_i, T_j$ 之间的距离或相似度，我们需要同时考虑群轨道距离以及相对特征空间中距离的耦合关系。

我们前面定义过在 $ V_4 $ 群操作下，两个动机原型 $\mu_A$ 和 $\mu_B$ 之间的最小匹配距离：

$$
d_{\mathbb{Q}}(\mu_A, \mu_B) = \min_{g \in V_4} d_{\Phi}(\varphi_A, g \cdot \varphi_B)
$$
这里面，我们是通过穷举不同的 $ g \in [\mathcal{e},\mathcal{R},\mathcal{I},\mathcal{RI}]$，计算在不同的操作变换下商空间 $\mathbb{Q}$ 中$\mu_A, \mu_B$ 的距离最小值。具体的展开为：
\[
d_\mathbb{Q}(T_i, T_j) = \min \left\{
\begin{aligned}
& d_\Phi(\varphi_A, e \cdot \varphi_B), \\
& d_\Phi(\varphi_A, \mathcal{I} \cdot \varphi_B), \\
& d_\Phi(\varphi_A, \mathcal{R} \cdot \varphi_B), \\
& d_\Phi(\varphi_A, \mathcal{R}\mathcal{I} \cdot \varphi_B)
\end{aligned}
\right\}.
\]
关于 $d_\Phi$ 距离的具体计算，$d_\Phi(\varphi_A, g \cdot \varphi_B)$ 即在某种 $g$ 变换下，在归一化相对特征空间 $\Phi_\text{ref}$ 中相对特征向量 $\varphi_A$ 和 $g \cdot \varphi_B$ 之间的特征距离。
\[
\varphi_i = \bigl( I_i,\, \widehat{R}_i,\, \widehat{T}_{i,\text{start ref}} \bigr), \qquad
\varphi_j = \bigl( I_j,\, \widehat{R}_j,\, \widehat{T}_{j,\text{start ref}} \bigr).
\]

特征距离自然分为三部分：音程序列距离 $d_I$ ,归一化节奏比例序列距离 $d_R$，和相对起始时间序列距离 $d_T$。
\[
d_\Phi(\varphi_i, \varphi_j) 
= w_I \, d_I(I_i, I_j) 
+ w_R \, d_R(\widehat{R}_i, \widehat{R}_j) 
+ w_T \, d_T(\widehat{T}_{i,sr}, \widehat{T}_{j,sr}),
\]
 $d_I,d_R,d_T$ 取序列上的归一化编辑距离或 DTW (动态时间序列规整距离) 实现。

**关键性质**：$T_i \sim_{\mathrm{strict}} T_j$ 时 $d_{\mathbb Q}(T_i, T_j) $ 自然为0。若不满足 $T_i \sim_{\mathrm{strict}} T_j$ ，但满足 $T_i \sim_{\mathrm{sym}} T_j$（同属一个对称族），则 $d_{\mathbb Q}(T_i, T_j) $ 也等于0。

### 多声部扩展商空间距离

对于多声部主题类型 \(T_i^{\mathrm{multi}},T_j^{\mathrm{multi}}\)，其严格键分别为
\[
\kappa_i^{\mathrm{multi}},
\qquad
\kappa_j^{\mathrm{multi}}
\in
\Phi_{\mathrm{rel}}^{\mathrm{multi}}.
\]

多声部商空间距离定义为
\[
d_{\mathbb{Q}}^{\mathrm{multi}}
(T_i,T_j)
=
\min_{g\in G_{\Lambda'}}
d_{\Phi}^{\mathrm{multi}}
\left(
\kappa_i^{\mathrm{multi}},
g\cdot \kappa_j^{\mathrm{multi}}
\right).
\]

其中多声部特征距离由三部分组成：
\[
d_{\Phi}^{\mathrm{multi}}
=
w_{\mathrm{hor}}d_{\mathrm{hor}}
+
w_{\mathrm{vert}}d_{\mathrm{vert}}
+
w_{\mathrm{cp}}d_{\mathrm{cp}}.
\]

这里：
\[
d_{\mathrm{hor}}
\]
表示各声部内部横向相对特征之间的距离；

\[
d_{\mathrm{vert}}
\]
表示纵向音程特征 \(V^{\Lambda'}\) 之间的距离；

\[
d_{\mathrm{cp}}
\]
表示声部进行关系特征 \(C^{\Lambda'}\) 之间的距离。

例如，可以定义
\[
d_{\mathrm{hor}}
=
\sum_{\lambda\in\Lambda'}
d_{\Phi}
\left(
\varphi_i^{\lambda},
\varphi_j^{\lambda}
\right),
\]
其中 \(d_{\Phi}\) 沿用原文中的音程序列距离、归一化节奏距离和相对起始时间距离。

纵向音程距离可定义为
\[
d_{\mathrm{vert}}
=
d_V
\left(
V_i^{\Lambda'},
V_j^{\Lambda'}
\right),
\]
声部进行距离可定义为
\[
d_{\mathrm{cp}}
=
d_C
\left(
C_i^{\Lambda'},
C_j^{\Lambda'}
\right).
\]

其中 \(d_V,d_C\) 可取编辑距离、DTW 距离或逐时刻矩阵差异的归一化距离。

当 \(|\Lambda'|=1\) 时，纵向音程特征和声部进行特征为空，故有
\[
d_{\mathbb{Q}}^{\mathrm{multi}}
=
d_{\mathbb{Q}}.
\]

### 主题相似度

采用指数核将商空间距离 \(d_{\mathbb Q}\) 映射为主题相似度：
\[
S_m(T_i,T_j)
=
\exp\!\left(
-\frac{d_{\mathbb Q}(T_i,T_j)}{\ell}
\right).
\]

其中尺度参数 \(\ell\) 由数据自适应确定：
\[
\ell
=
\operatorname{median}
\bigl\{
d_{\mathbb Q}(T_i,T_j)
:
i<j,\;
d_{\mathbb Q}(T_i,T_j)>0
\bigr\}.
\]

若所有非零距离集合为空，即全部主题同族，则令
\[
S_m(T_i,T_j)\equiv 1.
\]

该定义保证：若 \(T_i\) 与 \(T_j\) 属于同一对称族，则
\[
d_{\mathbb Q}(T_i,T_j)=0,
\qquad
S_m(T_i,T_j)=1.
\]
若二者属于不同族，则相似度随商空间距离连续衰减。

对于多声部主题类型，只需将商空间距离替换为多声部扩展商空间距离：
\[
S_m^{\mathrm{multi}}(T_i,T_j)
=
\exp\!\left(
-\frac{
d_{\mathbb Q}^{\mathrm{multi}}(T_i,T_j)
}{\ell}
\right).
\]

若上下文中已经统一使用多声部特征，则仍可简记为
\[
S_m(T_i,T_j)
=
\exp\!\left(
-\frac{
d_{\mathbb Q}^{\mathrm{multi}}(T_i,T_j)
}{\ell}
\right).
\]

### $^*$可选调性上下文修正

上述 \(S_m(T_i,T_j)\) 是基于动机结构的基础相似度，不依赖调性假设。为了使模型同时适用于调性音乐和无调性音乐，调性不参与严格主题类型 \(T_i\) 的定义，也不参与对称族 \(F_\ell\) 的划分。调性只作为可选上下文，对主题相似度进行弱修正。

设每次主题出现 \(\mathfrak{o}_q\) 可附带一个调性上下文标签：
\[
\theta_q=(k_q,\mathbf{h}_q,\gamma_q),
\]
其中：

- \(k_q\) 表示局部调中心或音高中心；
- \(\mathbf{h}_q\) 表示局部 pitch-class profile；
- \(\gamma_q\in[0,1]\) 表示局部调性置信度。

若该处无明确调性、调性不可判定，或不启用调性层，则记为
\[
\theta_q=\perp.
\]

对于主题类型 \(T_i\)，可将其所有出现的调性上下文汇总为类型层面的调性上下文 \(\theta_i\)。例如，可取其出现集合 \(\mathfrak{O}_i\) 中局部调性置信度的中位数：
\[
\gamma_i
=
\operatorname{median}_{\mathfrak{o}_q\in\mathfrak{O}_i}
\gamma_q.
\]

若需要考虑调性上下文，可先定义调性相似度
\[
S_{\mathrm{ton}}(T_i,T_j)
=
\exp\!\left(
-\frac{
d_{\mathrm{ton}}(\theta_i,\theta_j)
}{
\ell_{\mathrm{ton}}
}
\right).
\]

其中
\[
d_{\mathrm{ton}}(\theta_i,\theta_j)
=
d_{\Theta}(\theta_i,\theta_j)
\]
表示调性上下文空间中的距离。根据具体任务，\(d_{\Theta}\) 可取：

1. 调中心距离；
2. 五度圈距离；
3. pitch-class profile 距离；
4. Krumhansl key profile 距离；
5. 两个局部音级分布向量之间的余弦距离、KL 距离或 Jensen-Shannon 距离。

若任意一方无明确调性，即
\[
\theta_i=\perp
\quad\text{或}\quad
\theta_j=\perp,
\]
则定义
\[
S_{\mathrm{ton}}(T_i,T_j)=1.
\]
这表示调性层在该对主题之间不施加额外惩罚。

为了避免手动设置调性权重，引入自动调性门控系数
\[
\eta_{ij}\in[0,1].
\]

该系数由全曲调性显著性和局部主题调性置信度共同决定。首先定义全曲调性置信度：
\[
\Gamma_{\mathrm{ton}}(\mathcal{M})
=
\operatorname{median}_q \gamma_q.
\]

再定义调中心稳定度。设全曲局部调中心分布为
\[
\mathbf{p}_{\mathrm{key}}
=
(p_1,\dots,p_K),
\]
其中 \(K\) 可以取 \(12\) 个音高中心，或 \(24\) 个大小调中心。其归一化熵为
\[
H_{\mathrm{ton}}
=
-\frac{1}{\log K}
\sum_{k=1}^{K}
p_k\log p_k.
\]

于是调中心稳定度定义为
\[
\Sigma_{\mathrm{ton}}(\mathcal{M})
=
1-H_{\mathrm{ton}}.
\]

当局部调中心高度集中时，\(\Sigma_{\mathrm{ton}}\) 接近 \(1\)；当调中心分布接近均匀或高度不稳定时，\(\Sigma_{\mathrm{ton}}\) 接近 \(0\)。

最终，主题 \(T_i,T_j\) 之间的调性上下文门控系数定义为
\[
\eta_{ij}
=
\Gamma_{\mathrm{ton}}(\mathcal{M})
\cdot
\Sigma_{\mathrm{ton}}(\mathcal{M})
\cdot
\gamma_i
\cdot
\gamma_j.
\]

因此，只有当作品整体具有明确调性倾向、调中心分布相对稳定，并且两个主题所在局部区域都有较高调性置信度时，调性上下文才会显著参与相似度修正。

#### $^*$带调性上下文修正的相似度

于是，带调性上下文修正的主题相似度修正为
\[
S_m^{\mathrm{ctx}}(T_i,T_j)
=
S_m(T_i,T_j)
\cdot
S_{\mathrm{ton}}(T_i,T_j)^{\eta_{ij}}.
\]

其中：

- \(S_m(T_i,T_j)\) 是基础结构相似度；
- \(S_{\mathrm{ton}}(T_i,T_j)\) 是调性上下文相似度；
- \(\eta_{ij}\) 是自动调性门控系数。

当作品无明确调性、调中心不稳定，或某个主题局部调性不可判定时，有
\[
\eta_{ij}\approx 0.
\]

此时
\[
S_m^{\mathrm{ctx}}(T_i,T_j)
\approx
S_m(T_i,T_j),
\]
模型自动退化为纯结构相似度。

因此，调性上下文不会改变主题身份，也不会影响严格等价关系或对称等价关系。它只在调性显著时作为相似度的可选修正项。

### 主题网络

以严格主题类型集合 $\mathcal{T}$ 为顶点集，构造加权无向图

$$
G_m = (V_m,\, E_m,\, W_m)
$$

其中节点集 $V_m = \mathcal{T} = \{T_1, \dots, T_K\}$，边集与权函数由以下两类关系叠加定义。

**对称边**：若 $T_i \sim_{\mathrm{sym}} T_j$（即 $\mu_i = \mu_j$，同属一个 $ V_4 $ 轨道），则
$$
e_{ij}^{\mathrm{sym}} \in E_{\mathrm{sym}},
\qquad
w_{ij}^{\mathrm{sym}} = \lambda_{\mathrm{sym}} \cdot S_F(T_i, T_j)
$$

这类边在图中精确对应 $ V_4 $ 轨道内的四个节点之间的连接，其结构由稳定子 $\mathrm{Stab}(\varphi)$ 决定族内的实际连接数。

**时间邻接边**：设所有主题出现按时间排序为 $\mathfrak{O}^{\uparrow} =(\mathfrak{o}_{(1)}, \mathfrak{o}_{(2)}, \dots, \mathfrak{o}_{(Q)})$，定义邻接频次
$$
c_{ij}^{\mathrm{temp}}
= \sum_{q=1}^{Q-1}
\mathbf{1}\bigl[\mathfrak{o}_{(q)} \in T_i,\; \mathfrak{o}_{(q+1)} \in T_j,\; i \neq j\bigr]
$$

归一化后的时间边权为

$$
w_{ij}^{\mathrm{temp}}
= \lambda_{\mathrm{temp}} \cdot \frac{c_{ij}^{\mathrm{temp}}}{\max_{a,b}\, c_{ab}^{\mathrm{temp}}}
$$

**总边权**
$$
w_{ij}
= \lambda_{\mathrm{sym}} \cdot \mathbf{1}[T_i \sim_{\mathrm{sym}} T_j]
+ \lambda_{\mathrm{temp}} \cdot \frac{c_{ij}^{\mathrm{temp}}}{\max c^{\mathrm{temp}}}
$$

其中 $\lambda_{\mathrm{sym}} = 1.0,\; \lambda_{\mathrm{temp}} = 0.5$ 为当前设定边权超参数。

## 从 Lake–Thomas 到音乐结构韧性

### 代数结构到物理类比的对应

交联聚合物 Lake–Thomas 模型的核心形式为

$$
\Gamma_{\mathrm{LT}} \sim \nu N U
$$

其物理意义是：宏观裂纹推进消耗的不只是裂纹面上单个键能$U$，而是整条链被拉伸到断裂所积累的总能量，链密度 $\nu$ 与链长 $N$ 共同放大这一效应。

在主题网络 $G_m$ 中，可以构造如下的结构同态关系：

- **交联点** $v \in V_p$ $\leftrightarrow$ **严格主题类型** $T_i \in V_m$
- **链段** $e \in E_p$ $\leftrightarrow$ **主题关系** $e_{ij} \in E_m$
- **单键能量** $U_e$ $\leftrightarrow$ **关系权重** $w_{ij}$
- **交联密度** $\nu$ $\leftrightarrow$ **主题关系密度** $\rho_i = \deg(T_i)$
- **每链有效链段数** $N$ $\leftrightarrow$ **平均关系强度** $\bar{w}_i = \frac{1}{\deg(T_i)}\sum_j w_{ij}$

### 静态直接破坏量 $B_{\text{direct}}$

直接破坏量具有 Lake–Thomas 型分解
$$
B_{\mathrm{direct}}(T_i)
= \sum_j w_{ij}
= \underbrace{\deg(T_i)}_{\sim\,\nu}
\cdot
\underbrace{\bar{w}_i}_{\sim\,NU}
$$

这一指标实质上描述了某一主题类型 \(T_i\) 在全局主题网络中的总连接强度。这与 $\Gamma_{\mathrm{LT}} \sim \nu N U$ 完全同构：网络中连接越密集（$\deg$ 大）、关系越强（$\bar{w}$ 大），该主题节点的"断裂代价"越高。

进一步，由于 $w_{ij}$ 由对称边和时间邻接边叠加而成，可以将直接破坏量分解为两个物理来源

$$
B_{\mathrm{direct}}(T_i)
= \underbrace{\lambda_{\mathrm{sym}} \sum_{j:\, T_j \sim_{\mathrm{sym}} T_i} 1}_{B_{\mathrm{sym}}(T_i)}
+ \underbrace{\lambda_{\mathrm{temp}} \sum_j \frac{c_{ij}^{\mathrm{temp}}}{\max c^{\mathrm{temp}}}}_{B_{\mathrm{temp}}(T_i)}
$$

其中 $B_{\mathrm{sym}}$ 对应同一 $ V_4 $ 轨道内的代数关系强度，$B_{\mathrm{temp}}$ 对应时间句法层面的共现关系强度。

### *时间常量

先从主题出现中提取三个基本量，方便之后时域上指标的定义。

**主题持续时长**：  
$$
d_q = t_q^+ - t_q^-.
$$
**相邻主题起点间隔**：  
$$
\delta_q = t_{q+1}^- - t_q^-.
$$
**相邻主题空隙**：  
$$
g_q = |(t_{q+1}^- - t_q^+)|.
$$
**乐曲内部的主题时间尺度** 
$$
\tau_{\mathfrak{D}} = \operatorname{median}\{d_q\} + \operatorname{median}\{g_q : g_q > 0\}
$$
如果没有正主题空隙，则取：  
$$
\tau_{\mathfrak{D}} = \operatorname{median}\{d_q\}
$$

### 记忆激活函数 $A_i(t)$

对一次主题出现 $\mathfrak{o}_q \in T_i$，其时间区间为
$$
\sigma_q=[t_q^-,t_q^+].
$$
在其结束时刻 $t_c = t_q^+$ 之后，可定义该次主题出现合理的时间激活衰减统一设为
$$
a_{\mathfrak{o}_q}(t)
=
\begin{cases}
1, & t_q^- \leq t \leq t_q^+ \\[4pt]
2^{\!-\dfrac{t - t_q^+}{\tau_\mathfrak{D}}} = 2^{\!-\dfrac{\delta t}{\tau_\mathfrak{D}}} , & t > t_q^+ \\[4pt]
0, & t < t_q^-
\end{cases}
$$

这样，经过一个乐曲内部主题时间尺度后，该次主题出现记忆强度减半。

关于某一主题类型 $T_i$ 的**激活**为 \(A_i(t)\)，表示主题类型 \(T_i\) 在时刻 \(t\) 的动态记忆强度 
$$
A_i(t) = 1 - \prod_{\mathfrak{o}_q \in T_i}\bigl(1 - a_{\mathfrak{o}_q}(t)\bigr)
$$

该定义允许多个同类主题出现共同增强当前激活，同时保证
\[
0\leq A_i(t)\leq 1.
\]

若同一时刻存在多个主题、多个声部或多个变形材料同时进行，它们各自的局部激活都会参与乘积项，从而体现复调叠置或密集回响带来的激活增强。

从上面的记忆激活衰减函数中我们抽取出记忆衰减核（Memory Decay Kernel）
$$
K_m(\Delta t) =2^{\!-\dfrac{\delta t}{\tau_\mathfrak{D}}}, \qquad \delta t \geq 0
$$

### 动态断裂势能 $B_{\text{dyn}}$

静态直接破坏量 $B_{\text{direct}}$ 只描述 \(T_i\) 在全局主题网络中的总连接强度。但在具体终止时刻 \(t_c\)，只有仍处于听觉记忆激活状态的主题关系才真正参与断裂。

因此定义动态断裂势能
\[
B_{\mathrm{dyn}}(T_i,t_c)
=
A_i(t_c)
\sum_j w_{ij}A_j(t_c)
\]

其中：

- \(A_i(t_c)\) 表示当前终止主题 \(T_i\) 自身的激活强度；
- \(A_j(t_c)\) 表示与 \(T_i\) 相连的主题类型 \(T_j\) 在当前时刻的激活强度；
- \(w_{ij}\) 表示主题网络中的关系权重。

该定义表示：若 \(T_i\) 本身已经不活跃，或者与其相连的主题关系在当前听觉记忆中已经衰减，则即使 \(T_i\) 在静态网络中很重要，其即时断裂势能也会降低。

将 \(w_{ij}\) 分解为对称边和时间邻接边，可得
\[
B_{\mathrm{dyn}}(T_i,t_c)
=
A_i(t_c)
\left(
\lambda_{\mathrm{sym}}
\sum_{j:T_j\sim_{\mathrm{sym}}T_i}
A_j(t_c)
+
\lambda_{\mathrm{temp}}
\sum_j
\frac{c_{ij}^{\mathrm{temp}}}{\max c^{\mathrm{temp}}}
A_j(t_c)
\right).
\]

其中第一项表示同一对称族内部的动态断裂势能，第二项表示时间句法关系上的动态断裂势能。

### 延续预期 $E_{\mathrm{cont}}$

断裂感不仅取决于结构关系是否被切断，还取决于听者是否预期该结构继续。一个主题如果已经自然闭合，则其停止未必造成强断裂；反之，如果主题正处于高激活、高重复惯性或高回归预期状态，则其突然终止会产生更强断裂感。

延续预期可以用一个最直观的方式进行定义：过去同类主题结束之后，是否经常在一个自然时间尺度内被相似材料接续。

对当前终止事件 $(T_i, t_c)$，考虑历史中所有同类终止：  
$$
\mathcal{H}_i(t_c) = \{ o_q \in T_i : t_q^+ < t_c \}.
$$

对每个历史终止 $o_q$，找它之后的所有主题出现：  
$$
\Delta_q^+ = \{ o_r : t_q^+ < t_r \}.
$$

定义该历史终止后的实际接续强度：  
$$
e_q = \max_{o_r \in \Delta_q^+} \left[ 2^{-\frac{t_r - t_q^+}{\tau_{\mathfrak{D}}}}  \, S_m(T_i, T_r) \right].
$$

即：后面越快出现、越相似，接续强度越高。取最大值是因为听觉上一个强接续就足以形成“这个主题通常会被接上”的经验。

当前延续预期定义为历史平均：  
$$
E_{\mathrm{cont}}(T_i, t_c) = \frac{1}{|\mathcal{H}_i(t_c)|} \sum_{o_q \in \mathcal{H}_i(t_c)} e_q
$$

如果没有历史同类终止，即：  
$$
|\mathcal{H}_i(t_c)| = 0,
$$
则退回到当前激活：  
$$
E_{\mathrm{cont}}(T_i, t_c) = A_i(t_c)
$$

### 句法未闭合度 $U_{\mathrm{cad}}$

如果一个主题出现长度接近该主题类型的典型长度，则更像完整陈述；如果明显短于典型长度，则更像中断。

对主题类型 $T_i$，定义**典型时长**：  
$$
D_i^{\mathrm{typ}} = \operatorname{median}\left\{ t_q^+ - t_q^- : o_q \in T_i \right\}.
$$

当前出现 $o_q \in T_i$ 的**完整度**：  
$$
K_{\mathrm{form}}(o_q) = \min\left\{ 1,\; \frac{t_q^+ - t_q^-}{D_i^{\mathrm{typ}}} \right\}.
$$

**句法未闭合度**定义为：  
$$
U_{\mathrm{cad}}(o_q) = 1 - K_{\mathrm{form}}(o_q)
$$

即：  
$$
U_{\mathrm{cad}}(o_q) = 1 - \min\left\{ 1,\; \frac{t_q^+ - t_q^-}{D_i^{\mathrm{typ}}} \right\}
$$

该式子只表达“是否疑似未完整陈述”。如果某个主题类型只出现一次，则无法估计典型时长。此时令：  

$$
U_{\mathrm{cad}}(o_q) = 0.
$$

### 残余相干 $C_{\mathrm{res}}^{\mathrm{dyn}}$

在某次主题出现 $\mathfrak{o}_q \in T_i$ 的终止时刻 $t_c = t_q^+$ 之后，取残余观察窗口 $[t_c,\, t_c + \Delta t]$，设该窗口内的后续主题出现集合为

$$
\mathfrak{O}^+(t_c, \Delta t)
= \bigl\{ \mathfrak{o}_j \in \mathfrak{O} : t_c < t_j^- \leq t_c + \Delta t \bigr\}
$$

对每个后续主题出现 $\mathfrak{o}_j \in T_k$，其对 $T_i$ 的残余贡献为

$$
r_{i \to k}(t_c, t_j^-)
= K_m(t_j^- - t_c) \cdot S_m(T_i, T_k)
= 2^{\!-\dfrac{\delta t}{\tau_\mathfrak{D}}} S_m(T_i, T_k)
$$

对$\mathfrak{O}^+(t_c, \Delta t)$ 内所有后续主题出现求和，得总残余相干

$$
C_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c;\, \Delta t, \tau_m)
= \sum_{\mathfrak{o}_j \in \mathfrak{O}^+(t_c,\,\Delta t)}
2^{\!-\dfrac{\delta t}{\tau_\mathfrak{D}}}
S_m\!\left(T_i,\, T(\mathfrak{o}_j)\right)
$$

其中 $T(\mathfrak{o}_j)$ 为 $\mathfrak{o}_j$ 所属的严格主题类型。

这一形式在材料模型中对应的是**裂纹尖端过程区耗散积分**

$$
\Gamma_{\mathrm{diss}}
= \int_{\Omega_p} \psi_{\mathrm{diss}}(\mathbf{x})\, d\mathbf{x}
\quad \longleftrightarrow \quad
C_{\mathrm{res}}^{\mathrm{dyn}}
= \sum_{\mathfrak{o}_j \in \Omega_m} K_m(t_j^- - t_c)\, S_m(T_i, T(\mathfrak{o}_j))
$$

过程区空间积分变为时间窗口上的离散求和，空间耗散核$K_p(r)$ 对应记忆衰减核 $K_m(\Delta t)$，局部耗散密度 $\psi_{\mathrm{diss}}$ 对应主题碎片相似度 $S_m$。

用所有终止事件上的最大值归一化：

$$
\boxed{
\widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c) = 
\frac{C_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c)}{
\displaystyle \max_q C_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_q^+)
}
}
$$

如果分母为 0，则令 
$$
\widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c) = 0.
$$

这样  
$$
0 \leq \widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}} \leq 1.
$$

### 音乐结构韧性 $\mathcal{T}^{\mathrm{dyn}}_m$

一次主题终止事件 $(T_i, \mathfrak{o}_q, t_c)$ 的**音乐结构韧性**定义为

$$
\mathcal{T}^{\mathrm{dyn}}_m(T_i, t_c)
= \underbrace{B_{\mathrm{dyn}}(T_i, t_c)}_{\text{直接网络断裂}}
+ \underbrace{C_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c;\,\Delta t, \tau_m)}_{\text{残余主题耗散}}
$$

$B_{\mathrm{dyn}}$：终止时刻切断的当前结构势能；$C_{\mathrm{res}}^{\mathrm{dyn}}$：后续仍然回响的残余结构能量。

展开为
$$
\mathcal{T}_m(T_i, t_c)
=
A_i(t_c)
\sum_j w_{ij}A_j(t_c)
+
\sum_{\mathfrak{o}_j \in \mathfrak{O}^+(t_c,\,\Delta t)}
K_m(\Delta t)\cdot
S_m\!\left(T_i,\, T(\mathfrak{o}_j)\right)
$$

它表示这个主题终止事件牵涉多少结构能量。

### 动态净断裂感 $D_{\mathrm{dyn}}$

以下所有因子都在 $[0,1]$ 内：  
$$
E_{\mathrm{cont}} \in [0,1], \quad 
U_{\mathrm{cad}} \in [0,1], \quad 
\widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}} \in [0,1].
$$

定义**动态净断裂感**：  
$$
D_{\mathrm{dyn}}(T_i, t_c) = 
B_{\mathrm{dyn}}(T_i, t_c) \cdot 
E_{\mathrm{cont}}(T_i, t_c) \cdot 
U_{\mathrm{cad}}(o_q) \cdot 
\bigl(1 - \widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_c)\bigr)
$$
其中 $t_c = t_q^+$。

它表达：
- 当前结构关系越活跃，断裂感越强；  
- 过去越形成“它会被接续”的经验，断裂感越强；  
- 当前出现越不完整，断裂感越强；  
- 后面越快出现相似材料，断裂感越弱。

### 主题层面统计量

由于严格主题类型 $T_i$ 可能在全曲中出现 $n_i = |T_i|$ 次，在每次出现结束时均产生一个终止事件，

对主题类型 $T_i$，定义其主题出现集合为：  
$$
\mathfrak{O}_i = \{ \mathfrak{o}_q : T_q = T_i \}.
$$

则平均动态净断裂感为 
$$
\overline{D}_{\mathrm{dyn}}(T_i) = \frac{1}{|\mathfrak{O}_i|} \sum_{\mathfrak{o}_q \in \mathfrak{O}_i} D_{\mathrm{dyn}}(T_i, t_q^+)
$$

表征“这个主题通常有多容易断”。

最大动态净断裂感为 
$$
D_{\mathrm{dyn}}^{\max}(T_i) = \max_{\mathfrak{o}_q \in \mathfrak{O}_i} D_{\mathrm{dyn}}(T_i, t_q^+)
$$

表征“这个主题最强的一次断裂对应的断裂感强度有多大”。

平均动态结构韧性为 
$$
\overline{\mathcal{T}}_m^{\mathrm{dyn}}(T_i) = \frac{1}{|\mathfrak{O}_i|} \sum_{\mathfrak{o}_q \in \mathfrak{O}_i} \mathcal{T}_m^{\mathrm{dyn}}(T_i, t_q^+)
$$

表征“这个主题终止时通常牵涉多少结构能量”。

最大动态结构韧性为 
$$
\mathcal{T}_{m,\max}^{\mathrm{dyn}}(T_i) = \max_{\mathfrak{o}_q \in \mathfrak{O}_i} \mathcal{T}_m^{\mathrm{dyn}}(T_i, t_q^+)
$$
表征“这个主题终止时最大牵涉多少结构能量”。

平均残差相干补偿为
$$
\overline{C}_{\mathrm{res}}^{\mathrm{dyn}}(T_i) = 
\frac{1}{|\mathfrak{O}_i|} \sum_{\mathfrak{o}_q \in \mathfrak{O}_i} C_{\mathrm{res}}^{\mathrm{dyn}}(T_i, t_q^+)
$$
表征“这个主题终止后通常有没有被补回来”；亦可同理定义“最大残差相干补偿量”。

## 完整对应表及形式化链条总结

| 交联聚合物 | 关键物理量 | 音乐模型 | 关键音乐量 |
| :--- | :---: | :--- | :---: |
| 单体/链段事件 | \(x \in \mathcal{M}_p\) | 音乐事件 | \(x_n \in \mathcal{M}\) |
| 局部链构型 | \(\omega_p\) | 候选音型窗口 | \(\omega_{i,L}^{(\lambda)}\in\Omega\) |
| 链内结构特征 | \(\varphi_p(\omega_p)\) | 归一化相对特征 | \(\varphi(\omega)\in\Phi_{\mathrm{rel}}\) |
| 构型对称变换群 | \(G_p\) | 动机变换群 | \(V_4\) |
| 链型 / 构型等价类 | \([e]_{\sim}\) | 严格主题类型 | \(T_i\) |
| 拓扑等价族 | 同构链族 | 对称族 | \(F_\ell\) |
| 聚合物网络 | \(G_p\) | 主题网络 | \(G_m\) |
| 交联点 | \(v\) | 主题类型节点 | \(T_i\) |
| 链段 / 网络边 | \(e_{ij}\) | 主题关系边 | \(e_{ij}^{m}\) |
| 单链断裂能 | \(U_e\) | 主题关系权重 | \(w_{ij}\) |
| 交联密度 | \(\nu\) | 主题关系度 | \(\deg(T_i)\) |
| 每链有效单元数 | \(N\) | 平均关系强度 | \(\bar{w}_i\) |
| Lake-Thomas 断裂能 | \(\Gamma_{\mathrm{LT}}\) | 静态直接破坏量 | \(B_{\mathrm{direct}}\) |
| 当前链段受力状态 | stress activation | 主题记忆激活 | \(A_i(t)\) |
| 动态可断裂链段 | active cut bonds | 动态相关主题关系 | \(w_{ij}A_j(t_c)\) |
| 动态断裂能量 | activated rupture energy | 动态断裂势能 | \(B_{\mathrm{dyn}}\) |
| 裂纹切断链段集 | \(E_{\mathrm{cut}}^p\) | 终止时刻切断关系集 | \(E_{\mathrm{cut}}(T_i,t_c)\) |
| 裂纹尖端过程区 | \(\Omega_p\) | 后续残余相干域 | \(\Omega_m(t_c,\Delta t)\) |
| 过程区松弛核 | \(K_p\) | 记忆衰减核 | \(K_m\) |
| 局部耗散密度 | \(\psi_{\mathrm{diss}}\) | 主题相似度 / 碎片相干 | \(S_m\) |
| 过程区耗散积分 | \(\Gamma_{\mathrm{diss}}\) | 残余相干 | \(C_{\mathrm{res}}^{\mathrm{dyn}}\) |
| 归一化耗散补偿 | \(\widehat{\Gamma}_{\mathrm{diss}}\) | 归一化残余补偿 | \(\widetilde{C}_{\mathrm{res}}^{\mathrm{dyn}}\) |
| 总断裂能 / 韧性 | \(\Gamma\) | 音乐结构韧性 | \(\mathcal{T}_m^{\mathrm{dyn}}\) |
| 裂纹推进驱动力 | driving force | 延续预期 | \(E_{\mathrm{cont}}\) |
| 局部未断裂闭合 | incomplete failure closure | 句法未闭合度 | \(U_{\mathrm{cad}}\) |
| 净裂纹驱动力 | driving force - resistance | 动态净断裂感 | \(D_{\mathrm{dyn}}\) |
| 断裂事件统计 | event-level distribution | 主题终止画像 | \(\Phi_{\mathrm{dyn}}(T_i)\) |
### 形式化链条总结

在单声部情形下，形式化链条为
\[
\mathcal{M}
\;\xrightarrow{\text{声部层划分}}\;
\mathcal{M}^{(\lambda)}
\;\xrightarrow{\text{滑动窗口+约束}}\;
\Omega
\;\xrightarrow{\;\phi\;}\;
\Phi_{\mathrm{rel}}
\;\xrightarrow{\;/V_4\;}\; \\
\mathbb{Q}
\;\xrightarrow{\text{strict key}}\;
\mathcal{T}
\;\xrightarrow{\;/{\sim_{\mathrm{sym}}}\;}
\mathcal{F}
\;\xrightarrow{\text{权重叠加}}\;
G_m
\;\xrightarrow{B+C}\;
\mathcal{T}_m.
\]

在多声部情形下，链条扩展为
\[
\mathcal{M}
\;\xrightarrow{\text{声部层划分}}\;
\mathcal{M}^{\Lambda}
\;\xrightarrow{\text{多声部块窗口+约束}}\;
\Omega^{*}
\;\xrightarrow{\;\phi^{\mathrm{multi}}\;}\;
\Phi_{\mathrm{rel}}^{\mathrm{multi}}
\;\xrightarrow{\;/G_{\Lambda'}\;}\; \\
\mathbb{Q}^{\mathrm{multi}}
\;\xrightarrow{\text{multi strict key}}\;
\mathcal{T}^{\mathrm{multi}}
\;\xrightarrow{\;/{\sim_{\mathrm{sym}}}\;}
\mathcal{F}^{\mathrm{multi}}
\;\xrightarrow{\text{权重叠加}}\;
G_m
\;\xrightarrow{B+C}\;
\mathcal{T}_m.
\]

其中单声部模型是多声部模型在 \(|\Lambda'|=1\) 时的特例。



