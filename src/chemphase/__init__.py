"""chemphase — 相图与化学势热图生成器

一键从 Materials Project API 或本地 VASP 计算结果生成：
- 二元/三元成分相图（含 Hull 连线、标签自动避让）
- 化学势热图
- 结构对比报告
"""

__version__ = "0.1.0"


def __getattr__(name):
    """惰性导入：仅在实际使用子模块时才导入"""
    if name == "PhaseDiagramConfig":
        from chemphase.core import PhaseDiagramConfig
        return PhaseDiagramConfig
    if name == "generate_binary_composition_diagram":
        from chemphase.diagrams import generate_binary_composition_diagram
        return generate_binary_composition_diagram
    if name == "generate_ternary_composition_diagram":
        from chemphase.diagrams import generate_ternary_composition_diagram
        return generate_ternary_composition_diagram
    if name == "main":
        from chemphase.cli import main
        return main
    raise AttributeError(f"module 'chemphase' has no attribute '{name}'")


__all__ = [
    "__version__",
    "PhaseDiagramConfig",
    "generate_binary_composition_diagram",
    "generate_ternary_composition_diagram",
    "main",
]