# chemphase

**相图与化学势热图统一生成器 v5.0**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

一键从 Materials Project API 或本地 VASP 计算结果生成高质量相图。

## 功能

- **API 模式**：从 Materials Project 数据库下载热力学数据
- **本地模式**：读取本地 VASP 计算目录 (POSCAR + vasprun.xml/OUTCAR)
- **混合模式**：本地数据 + API 补充
- **二元成分相图**：ΔE vs 成分，含 Hull 连线、自动标签避让
- **三元成分相图**：Gibbs 三角图 (Plotly 交互式)，含 Hull 三角剖分
- **结构对比**：检测本地计算与 MP 数据库的晶体结构差异

## 安装

```bash
pip install chemphase
```

## 快速开始

### API 模式（默认）

```bash
# 使用默认元素 Cu-Ag-O-Se
chemphase

# 指定元素
chemphase --elements Li O Co
```

### 本地 VASP 数据模式

```bash
chemphase --local /path/to/vasp/calculations --elements Cu Ag O Se
```

### 结构对比

```bash
chemphase --local /path/to/vasp/calculations --elements Cu Ag O Se --compare-structure
```

## 依赖

- [pymatgen](https://pymatgen.org) — 材料分析库
- [doped](https://github.com/SMTG-Bham/doped) — 缺陷计算工具
- [matplotlib](https://matplotlib.org) — 二维绘图
- [plotly](https://plotly.com) — 交互式三元图

## API 密钥

API 模式需要 Materials Project API 密钥。设置环境变量：

```bash
export MATERIALS_PROJECT_API_KEY=你的密钥
```

获取密钥：https://materialsproject.org/api

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--elements` | 元素列表 | `Cu Ag O Se` |
| `--local` | 本地VASP目录 | — |
| `--output` | 输出目录 | `phase_diagrams_output` |
| `--eah` | E above hull 阈值 | `0.05` eV/atom |
| `--compare-structure` | 启用结构对比 | `False` |
| `--debug` | 调试模式 | `False` |

## 许可证

MIT License — 详见 [LICENSE](LICENSE)