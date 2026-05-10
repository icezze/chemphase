"""相图生成模块：二元/三元成分相图 + Hull 连线"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from pathlib import Path
from typing import List, Tuple

import plotly.graph_objects as go
from pymatgen.analysis.phase_diagram import PhaseDiagram

from chemphase.plotting import (
    coord_to_cartesian, allocate_colors, calculate_label_positions,
)

# ============================================================
# 绘图参数
# ============================================================
MARKER_SIZE = 25
MARKER_LINE_WIDTH = 2
TITLE_FONT_SIZE = 20
LABEL_BACKGROUND = 'rgba(255,255,255,0.9)'

BINARY_FIG_WIDTH = 12
BINARY_FIG_HEIGHT = 10
BINARY_LABEL_FONT_SIZE = 14
BINARY_XLABEL_FONT_SIZE = 14
BINARY_YLABEL_FONT_SIZE = 14
BINARY_HULL_LINE_COLOR = "gray"
BINARY_HULL_LINE_WIDTH = 1.5
BINARY_DPI = 150

TERNARY_FIG_WIDTH = 1000
TERNARY_FIG_HEIGHT = 900
TERNARY_LABEL_FONT_SIZE = 14
TERNARY_TITLE_FONT_SIZE = 20
TERNARY_HULL_LINE_COLOR = "gray"
TERNARY_HULL_LINE_WIDTH = 1.5
TERNARY_SHOW_HULL = True
TERNARY_LABEL_MARGIN = 0.12


# ============================================================
# 二元成分相图
# ============================================================

def generate_binary_composition_diagram(entries, elements: Tuple[str, str],
                                       output_dir: Path, title_suffix: str = "") -> bool:
    """生成二元成分相图（ΔE vs 成分，含 Hull 连线）

    Parameters
    ----------
    entries : list of pymatgen PDEntry
        热力学条目列表
    elements : tuple of (str, str)
        两种元素符号
    output_dir : Path
        输出目录
    title_suffix : str
        标题后缀（如 "MP数据" 或 "本地数据"）

    Returns
    -------
    bool : 是否成功生成
    """
    try:
        pd = PhaseDiagram(entries)
        phases = []
        base_energy = None

        for entry in pd.stable_entries:
            comp_dict = entry.composition.as_dict()
            formula = entry.composition.reduced_formula
            total = sum(comp_dict.values())
            x = comp_dict.get(elements[0], 0) / total if total > 0 else 0.5
            e_per_atom = pd.get_hull_energy(entry.composition) / entry.composition.num_atoms

            if base_energy is None or e_per_atom < base_energy:
                base_energy = e_per_atom

            phases.append({
                'formula': formula, 'x': x, 'e_per_atom': e_per_atom,
                'comp_dict': comp_dict
            })

        for phase in phases:
            phase['delta_e'] = phase['e_per_atom'] - base_energy

        phases = allocate_colors(phases)
        fig, ax = plt.subplots(figsize=(BINARY_FIG_WIDTH, BINARY_FIG_HEIGHT))

        ax.set_xlim(-0.05, 1.05)
        y_max = max(p['delta_e'] for p in phases) if phases else 0.5
        y_min = min(min(p['delta_e'] for p in phases), -0.05) if phases else -0.1
        ax.set_ylim(y_min - 0.15, y_max + 0.5)
        ax.set_xlabel(f'Composition (x in {elements[0]}$_{{1-x}}${elements[1]}$_x$)',
                     fontsize=BINARY_XLABEL_FONT_SIZE)
        ax.set_ylabel('ΔE (eV/atom)', fontsize=BINARY_YLABEL_FONT_SIZE)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Hull 连线（Delaunay 三角剖分）
        if len(phases) >= 3:
            points = np.array([[p['x'], p['delta_e']] for p in phases])
            try:
                tri = Delaunay(points)
                for simplex in tri.simplices:
                    for i in range(3):
                        ax.plot([points[simplex[i], 0], points[simplex[(i + 1) % 3], 0]],
                               [points[simplex[i], 1], points[simplex[(i + 1) % 3], 1]],
                               '-', color=BINARY_HULL_LINE_COLOR, linewidth=BINARY_HULL_LINE_WIDTH)
            except Exception:
                pass

        # 标签避让
        occupied = []
        sorted_phases = sorted(phases, key=lambda p: p['delta_e'])
        for phase in sorted_phases:
            best_y_offset = 0.05
            for y_offset_test in np.arange(0.02, 0.25, 0.02):
                overlaps = any(abs(ey - (phase['delta_e'] + y_offset_test)) < 0.05
                              for (ex, ey, ef) in occupied)
                if not overlaps:
                    best_y_offset = y_offset_test
                    break
            phase['label_y_offset'] = best_y_offset
            occupied.append((phase['x'], phase['delta_e'] + best_y_offset, phase['formula']))

        for phase in phases:
            ax.plot(phase['x'], phase['delta_e'], 'o', markersize=MARKER_SIZE / 3,
                   color=phase['color'])
            ax.annotate(phase['formula'],
                        (phase['x'], phase['delta_e'] + phase['label_y_offset']),
                        xytext=(0, 5), textcoords='offset points',
                        fontsize=BINARY_LABEL_FONT_SIZE,
                        color=phase['color'], fontweight='bold', ha='center',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                 alpha=0.8, edgecolor=phase['color']))

        system_str = f"{elements[0]}-{elements[1]}"
        suffix = f" ({title_suffix})" if title_suffix else ""
        ax.set_title(f'{system_str}{suffix}', fontsize=TITLE_FONT_SIZE, fontweight='bold')
        plt.tight_layout()

        filename = f"binary_{elements[0]}-{elements[1]}_phase.png"
        filepath = output_dir / filename
        plt.savefig(str(filepath), dpi=BINARY_DPI, bbox_inches='tight')
        plt.close('all')
        print(f"    + {filename}")
        return True
    except Exception as e:
        print(f"    - {elements[0]}-{elements[1]}: {e}")
        return False


# ============================================================
# 三元成分相图
# ============================================================

def draw_triangle_boundary(fig, elems: Tuple[str, str, str]):
    """绘制三元相图的三角形边界"""
    triangle_x = [0, 1, 0.5, 0]
    triangle_y = [0, 0, np.sqrt(3) / 2, 0]
    fig.add_trace(go.Scatter(
        x=triangle_x, y=triangle_y, mode='lines',
        line=dict(color='black', width=4), name='边界', hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1, 0.5], y=[-0.12, -0.12, np.sqrt(3) / 2 + 0.14],
        mode='text', text=[f"<b>{elems[0]}</b>", f"<b>{elems[1]}</b>", f"<b>{elems[2]}</b>"],
        textfont=dict(size=24, color='black'), name='元素标签', hoverinfo='skip'
    ))


def draw_hull_lines(fig, phases: List[dict]):
    """绘制三元相图的 Hull 连线（Delaunay 三角剖分）"""
    if not TERNARY_SHOW_HULL:
        return
    points = np.array([[p['x'], p['y']] for p in phases])
    if len(points) < 3:
        return
    tri = Delaunay(points)
    hull_x, hull_y = [], []
    for simplex in tri.simplices:
        for i in range(3):
            hull_x.extend([points[simplex[i], 0], points[simplex[(i + 1) % 3], 0], np.nan])
            hull_y.extend([points[simplex[i], 1], points[simplex[(i + 1) % 3], 1], np.nan])
    fig.add_trace(go.Scatter(
        x=hull_x, y=hull_y, mode='lines',
        line=dict(color=TERNARY_HULL_LINE_COLOR, width=TERNARY_HULL_LINE_WIDTH),
        name='Hull连线', hoverinfo='skip'
    ))


def draw_phases(fig, phases: List[dict]):
    """在三元相图上绘制相点和标签"""
    for phase in phases:
        fig.add_trace(go.Scatter(
            x=[phase['x']], y=[phase['y']], mode='markers',
            marker=dict(size=MARKER_SIZE, color=phase['color'],
                       line=dict(color='white', width=MARKER_LINE_WIDTH)),
            name=phase['formula'],
            hovertemplate=f"<b>{phase['formula']}</b><br>E = {phase['e_per_atom']:.4f} eV/atom",
            showlegend=False
        ))
        fig.add_annotation(
            x=phase['label_x'], y=phase['label_y'],
            text=f"<b>{phase['formula']}</b>", showarrow=False,
            font=dict(size=TERNARY_LABEL_FONT_SIZE, color=phase['color']),
            bgcolor=LABEL_BACKGROUND, bordercolor=phase['color'],
            borderwidth=1, borderpad=3, xref='x', yref='y'
        )


def generate_ternary_composition_diagram(entries, elements: Tuple[str, str, str],
                                        output_dir: Path, title_suffix: str = "") -> bool:
    """生成三元成分相图（Gibbs 三角图，含 Hull 连线和自动避让标签）

    Parameters
    ----------
    entries : list of pymatgen PDEntry
        热力学条目列表
    elements : tuple of (str, str, str)
        三种元素符号
    output_dir : Path
        输出目录
    title_suffix : str
        标题后缀

    Returns
    -------
    bool : 是否成功生成
    """
    try:
        pd = PhaseDiagram(entries)
        phases = []

        for entry in pd.stable_entries:
            comp_dict = entry.composition.as_dict()
            formula = entry.composition.reduced_formula
            x, y = coord_to_cartesian(comp_dict, elements)
            e_per_atom = pd.get_hull_energy(entry.composition) / entry.composition.num_atoms
            phases.append({
                'formula': formula, 'x': x, 'y': y, 'e_per_atom': e_per_atom,
                'comp_dict': comp_dict
            })

        phases = allocate_colors(phases)
        phases = calculate_label_positions(phases, TERNARY_LABEL_MARGIN)

        fig = go.Figure()
        draw_triangle_boundary(fig, elements)
        draw_hull_lines(fig, phases)
        draw_phases(fig, phases)

        system_str = "-".join(elements)
        suffix = f" ({title_suffix})" if title_suffix else ""
        fig.update_layout(
            title=dict(text=f"<b>{system_str}{suffix}</b><br><sup>{len(phases)} phases</sup>",
                      font=dict(size=TERNARY_TITLE_FONT_SIZE), x=0.5, xanchor='center'),
            xaxis=dict(range=[-0.2, 1.2], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-0.25, 1.1], showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor='x', scaleratio=1),
            plot_bgcolor='white', width=TERNARY_FIG_WIDTH, height=TERNARY_FIG_HEIGHT
        )

        filename = f"ternary_{elements[0]}-{elements[1]}-{elements[2]}_phase.png"
        filepath = output_dir / filename
        try:
            fig.write_image(str(filepath), scale=2)
        except Exception:
            fig.write_html(str(filepath).replace('.png', '.html'))
        plt.close('all')
        print(f"    + {filename}")
        return True
    except Exception as e:
        print(f"    - {elements[0]}-{elements[1]}-{elements[2]}: {e}")
        return False