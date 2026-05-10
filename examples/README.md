# chemphase 示例输出

本目录包含 chemphase 在两个代表体系上的完整运行示例：

## Cu-Ag-O-Se 四元体系

- **数据来源**: Materials Project API
- **运行命令**: `chemphase --elements Cu Ag O Se`
- **输出内容**:
  - 6 张二元相图 (Cu-Ag, Cu-O, Cu-Se, Ag-O, Ag-Se, O-Se)
  - 4 张三元相图 (Cu-Ag-O, Cu-Ag-Se, Cu-O-Se, Ag-O-Se)
  - 1 张四元综合分析图
  - 3 张化学势热图

## V-Nb-S 三元体系

- **数据来源**: 本地 VASP 计算结果
- **运行命令**: `chemphase --local ./VNb3S6_calculations --elements V Nb S`
- **输出内容**:
  - 3 张二元相图
  - 1 张三元相图

## 统一相数据库 (unified_phases/)

包含自动去重合并后的相态数据库：
- `phases_database.json` — 主索引文件
- `phases/Ag_Cu_O_Se/` — Cu-Ag-O-Se 四元体系各相
- `phases/Ag_Cu_Se/` — Cu-Ag-Se 三元体系各相
- `phases/Cu_O_Se/` — Cu-O-Se 三元体系各相
- ... (共 12 个子系统)