# BWV861 音乐形式化分析系统 — 安装指南

本指南适用于 **零基础** 用户 — 无需预先安装 Python 或 Jupyter。

---

## 方式一：Conda 一键安装（推荐，全平台通用）

### 1. 安装 Miniconda

| 平台 | 下载地址 |
|------|----------|
| Windows | [Miniconda3 Windows 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe) |
| macOS Intel | [Miniconda3 macOS x86_64](https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.pkg) |
| macOS Apple Silicon | [Miniconda3 macOS ARM64](https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.pkg) |
| Linux | [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) |

**Windows**: 双击 `.exe` → 一路 Next（勾选 "Add to PATH"）。  
**macOS**: 双击 `.pkg` → 按提示安装。  
**Linux**: `bash Miniconda3-latest-Linux-x86_64.sh` → 回车确认。

安装完成后，**重新打开终端**（Windows 打开 "Anaconda Prompt"）。

### 2. 创建项目环境

```bash
# 进入项目目录
cd "你的路径/bien_project"

# 用 environment.yml 一键创建含 Python 3.11 的环境
conda env create -f environment.yml
```

> `environment.yml` 已包含 Python 3.11 + 所有依赖的精确版本。

### 3. 激活环境 & 启动 Jupyter

```bash
conda activate bien_music_env
jupyter notebook notebooks/
```

浏览器会自动打开，从 `00_environment_setup.ipynb` 开始按顺序运行。

---

## 方式二：Python 自带 venv（无需 Anaconda，全平台通用）

> 适用场景：不想安装 Miniconda/Anaconda，直接使用系统自带的 Python 或从 python.org 安装的 Python。

### 1. 安装 Python 3.11+

| 平台 | 下载地址 |
|------|----------|
| Windows | [python.org — Python 3.11.x](https://www.python.org/downloads/) |
| macOS | `brew install python@3.11` 或 [python.org](https://www.python.org/downloads/) |
| Linux | `sudo apt install python3.11 python3.11-venv` (Ubuntu/Debian) |

**Windows 安装时务必勾选 ✅ "Add Python to PATH"**。

验证安装：
```bash
python --version    # 应显示 Python 3.11.x
```

### 2. 创建 .venv 虚拟环境

```bash
# 进入项目目录
cd "你的路径/bien_project"

# 创建虚拟环境（在项目根目录生成 .venv 文件夹）
python -m venv .venv
```

### 3. 激活虚拟环境

| 平台 | 命令 |
|------|------|
| **Windows** (cmd) | `.venv\Scripts\activate` |
| **Windows** (PowerShell) | `.venv\Scripts\Activate.ps1` |
| **macOS / Linux** | `source .venv/bin/activate` |

激活成功后，终端提示符前会出现 `(.venv)` 标识。

### 4. 安装依赖 & 启动 Jupyter

```bash
# 升级 pip（可选但推荐）
python -m pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt

# 启动 Jupyter Notebook
jupyter notebook notebooks/
```

浏览器会自动打开，从 `00_environment_setup.ipynb` 开始按顺序运行。

> **注意**：如果 PowerShell 提示"无法加载文件 Activate.ps1"，执行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> 然后重新激活。

### 5. 后续使用

每次打开新终端时需要重新激活：
```bash
cd "你的路径/bien_project"
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
jupyter notebook notebooks/
```

---

## 验证安装

打开 `notebooks/00_environment_setup.ipynb` → 点击 `Run All`。

如果看到 `✅ 所有依赖库导入成功` 且 music21 能正常解析 `.mxl` 文件，则环境就绪。

---

## 运行流水线

按顺序打开并 `Run All` 每个 Notebook：

| 顺序 | Notebook | 预计耗时 |
|------|----------|----------|
| 1 | `00_environment_setup.ipynb` | 10 秒 |
| 2 | `01_event_extraction.ipynb` | 5 秒 |
| 3 | `02_window_extraction.ipynb` | 10 秒 |
| 4 | `03_feature_extraction.ipynb` | 5 秒 |
| 5 | `04_motif_prototypes.ipynb` | 5 秒 |
| 6 | `05_theme_analysis.ipynb` | 5 秒 |
| 7 | `06_similarity_network.ipynb` | ~1 秒 (52×52 矩阵) |
| 8 | `07_dynamic_metrics.ipynb` | 5 秒 |
| 9 | `08_final_report.ipynb` | 15 秒（含 11 张图表） |

> 每个 Notebook 会将结果持久化到 `data/` 目录，支持断点续跑。

---

## 常见问题

**Q: `conda` 命令找不到？**  
A: Windows 请使用 "Anaconda Prompt"（开始菜单搜索），macOS/Linux 请重新打开终端。

**Q: music21 无法解析 `.mxl` 文件？**  
A: 部分系统需要额外安装 MuseScore。运行 `music21.configure.run()` 查看配置状态。

**Q: Notebook 运行时 kernel 报错？**  
A: 确保已激活 `bien_music_env` 环境：`conda activate bien_music_env`，然后在 Notebook 中选择对应的 kernel。

**Q: 图表不显示？**  
A: plotly 图表需要在 Notebook 中运行才能渲染。确保使用 `jupyter notebook`（非 `jupyter lab`）以获得最佳兼容性。

**Q: 如何区分我该用 Conda 还是 .venv？**  
A: 如果已经装了 Anaconda/Miniconda → 用方式一。如果只想用系统 Python，不想装额外工具 → 用方式二。两者效果完全相同。

**Q: `.venv` 文件夹可以删除吗？**  
A: 可以，`.venv` 只是本地虚拟环境，删除后重新 `python -m venv .venv && pip install -r requirements.txt` 即可重建。建议将其加入 `.gitignore`。
