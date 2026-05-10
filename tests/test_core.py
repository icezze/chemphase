"""chemphase 基础导入测试"""

import pytest


def test_import():
    """测试包可以正常导入"""
    import chemphase
    assert chemphase.__version__ == "0.1.0"


def test_import_core():
    """测试核心模块可导入"""
    from chemphase.core import (
        PhaseDiagramConfig, validate_elements, print_banner,
        DEFAULT_ELEMENTS, EAH_THRESHOLD,
    )
    assert DEFAULT_ELEMENTS == ["Cu", "Ag", "O", "Se"]
    assert EAH_THRESHOLD == 0.05


def test_import_cli():
    """测试 CLI 模块可导入"""
    from chemphase.cli import main
    assert callable(main)


def test_import_diagrams():
    """测试相图模块可导入"""
    from chemphase.diagrams import (
        generate_binary_composition_diagram,
        generate_ternary_composition_diagram,
    )
    assert callable(generate_binary_composition_diagram)
    assert callable(generate_ternary_composition_diagram)


def test_import_plotting():
    """测试绘图模块可导入"""
    from chemphase.plotting import (
        coord_to_cartesian, allocate_colors,
        find_best_label_position, calculate_label_positions,
    )
    assert callable(coord_to_cartesian)
    assert callable(allocate_colors)


def test_validate_elements():
    """测试元素验证"""
    from chemphase.core import validate_elements
    ok, valid, errors = validate_elements(["Cu", "Ag", "O", "Se"])
    assert ok is True
    assert valid == ["Cu", "Ag", "O", "Se"]
    assert errors == []

    ok, valid, errors = validate_elements(["Xx", "Cu", "Yy"])
    assert ok is False
    assert "Cu" in valid
    assert len(errors) == 2


def test_coord_to_cartesian():
    """测试三元坐标变换"""
    from chemphase.plotting import coord_to_cartesian
    import numpy as np

    x, y = coord_to_cartesian({"A": 1, "B": 0, "C": 0}, ("A", "B", "C"))
    assert abs(x - 0.0) < 0.01
    assert abs(y - 0.0) < 0.01

    x, y = coord_to_cartesian({"A": 0, "B": 1, "C": 0}, ("A", "B", "C"))
    assert abs(x - 1.0) < 0.01
    assert abs(y - 0.0) < 0.01

    x, y = coord_to_cartesian({"A": 0, "B": 0, "C": 1}, ("A", "B", "C"))
    assert abs(x - 0.5) < 0.01
    assert abs(y - np.sqrt(3) / 2) < 0.01


def test_config():
    """测试配置类"""
    from chemphase.core import PhaseDiagramConfig

    config = PhaseDiagramConfig(eah_threshold=0.1, output_root="test_output")
    assert config.eah_threshold == 0.1
    assert config.output_root == "test_output"
    assert config.api_key == ""
    assert config.local_dir is None
    assert config.compare_structure is False