"""绘图辅助模块：坐标变换、标签定位、颜色分配、核心绘图函数"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from typing import Dict, List, Tuple

# ============================================================
# 全局绘图参数
# ============================================================
COLOR_PALETTE = [
    "#FF0000", "#FF8800", "#FFDD00", "#00FF00", "#00FFCC", "#00BBFF",
    "#0066FF", "#8800FF", "#FF00AA", "#FF0044", "#AAFF00", "#00FF88",
    "#00DDFF", "#4400FF", "#DD00FF", "#4400FF", "#FF3333", "#FF9933",
    "#FFEE33", "#33FF33", "#33FFCC", "#33CCFF", "#3388FF", "#9933FF",
    "#FF33AA", "#FF3388", "#99FF33", "#33FF99", "#33EEFF", "#5533FF",
    "#EE33FF", "#FF5533", "#FF6666", "#FFAA66", "#FFFF66", "#66FF66",
    "#66FFCC", "#66DDFF", "#66AAFF", "#AA66FF", "#FF66CC", "#AAFF66",
    "#66FFAA", "#66EEFF", "#6644FF", "#FF66FF", "#FF6644", "#FFAAAA",
    "#FFCCAA", "#FFFFAA", "#AAFFAA", "#AAFFCC", "#AAEEFF", "#AACCFF",
    "#CCAAFF", "#FFAAEE", "#CCFFAA", "#CC0000", "#CC6600", "#CCCC00",
    "#00CC00", "#00CCCC", "#0099CC", "#0033CC", "#6600CC", "#CC0099",
    "#CC0033", "#99CC00", "#00CC66",
]

# ============================================================
# 三元相图坐标变换
# ============================================================

def coord_to_cartesian(comp_dict: Dict, elems: Tuple[str, str, str]) -> Tuple[float, float]:
    """将三元成分坐标转换为笛卡尔坐标（等边三角形底边朝下）"""
    total = sum(comp_dict.values())
    if total == 0:
        return 0.5, 0.5
    fracs = {e: comp_dict.get(e, 0) / total for e in elems}
    # elems[0] 在左下角, elems[1] 在右下角, elems[2] 在顶部
    x = fracs.get(elems[1], 0) + 0.5 * fracs.get(elems[2], 0)
    y = (np.sqrt(3) / 2) * fracs.get(elems[2], 0)
    return x, y


# ============================================================
# 标签自动避让算法
# ============================================================

def find_best_label_position(px: float, py: float, occupied: List[Tuple[float, float, str]],
                              margin: float = 0.12) -> Tuple[str, float, float]:
    """在三元相图中为标签找到最佳位置（避免与其他标签重叠）"""
    positions = [
        ('top left', -0.12, 0.10), ('top right', 0.12, 0.10),
        ('bottom left', -0.12, -0.08), ('bottom right', 0.12, -0.08),
        ('middle left', -0.15, 0), ('middle right', 0.15, 0),
        ('top center', 0, 0.12), ('bottom center', 0, -0.10),
    ]
    best_pos, best_x, best_y = 'top left', px - 0.12, py + 0.10
    best_dist = -1
    for pos_name, ox, oy in positions:
        test_x, test_y = px + ox, py + oy
        if test_y < -0.05 or test_y > 0.95:
            continue
        if test_x < -0.05 or test_x > 1.05:
            continue
        min_dist = min(((test_x - pox) ** 2 + (test_y - poy) ** 2) ** 0.5
                       for (pox, poy, _) in occupied) if occupied else 999
        if min_dist > best_dist:
            best_dist = min_dist
            best_pos, best_x, best_y = pos_name, test_x, test_y
    return best_pos, best_x, best_y


def calculate_label_positions(phases: List[Dict], margin: float = 0.12) -> List[Dict]:
    """为所有相计算最佳标签位置"""
    occupied = []
    sorted_phases = sorted(phases, key=lambda p: p['y'])
    for phase in sorted_phases:
        pos, lx, ly = find_best_label_position(phase['x'], phase['y'], occupied, margin)
        phase['label_pos'] = pos
        phase['label_x'] = lx
        phase['label_y'] = ly
        occupied.append((lx, ly, phase['formula']))
    return phases


# ============================================================
# 颜色分配
# ============================================================

def allocate_colors(phases: List[Dict]) -> List[Dict]:
    """为每个相分配颜色（循环使用调色板）"""
    for i, phase in enumerate(phases):
        phase['color'] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
    return phases