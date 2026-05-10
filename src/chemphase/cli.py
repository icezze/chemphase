"""命令行接口 (CLI)

安装后通过终端命令 `chemphase` 或 `python -m chemphase` 调用
"""

import sys
import argparse
from pathlib import Path
from itertools import combinations

from chemphase.core import (
    PhaseDiagramConfig, validate_elements, ensure_api_key,
    scan_local_phases, build_local_entries, structure_comparison_report,
    get_entries_from_mp, get_system_name, get_all_element_combinations,
    print_banner, DEFAULT_ELEMENTS,
)
from chemphase.diagrams import (
    generate_binary_composition_diagram,
    generate_ternary_composition_diagram,
)


def run_local_mode(config: PhaseDiagramConfig, elements, output_root: str):
    """本地数据模式：读取 VASP 计算结果生成相图"""
    print(f"\n扫描本地目录: {config.local_dir}")
    local_phases = scan_local_phases(config.local_dir, elements, config.eah_threshold)
    print(f"找到 {len(local_phases)} 个相关相")

    if not local_phases:
        print("没有找到有效的相数据")
        return

    # 结构对比
    if config.compare_structure:
        print("\n" + "=" * 60)
        print("  结构对比分析")
        print("=" * 60)
        report = structure_comparison_report(local_phases, config)
        print(f"  总共对比: {report['total_compared']}")
        print(f"  结构匹配: {report['matching']}")
        print(f"  结构不同: {report['different']}")
        print(f"  MP未收录: {report['not_found_in_mp']}")

        import json
        report_file = Path(output_root) / "structure_comparison_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"  报告已保存: {report_file}")

    entries = build_local_entries(local_phases)
    print(f"\n构建了 {len(entries)} 个PhaseDiagramEntry")

    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    binary_combos = list(combinations(elements, 2))
    ternary_combos = list(combinations(elements, 3))

    # 二元相图
    print("\n" + "=" * 60)
    print("  生成二元相图")
    print("=" * 60)
    binary_dir = output_dir / "binary"
    binary_dir.mkdir(parents=True, exist_ok=True)
    for e1, e2 in binary_combos:
        sub_entries = [e for e in entries if set(e.composition.as_dict().keys()) <= {e1, e2}]
        if len(sub_entries) >= 2:
            generate_binary_composition_diagram(sub_entries, (e1, e2), binary_dir, "本地数据")

    # 三元相图
    print("\n" + "=" * 60)
    print("  生成三元相图")
    print("=" * 60)
    ternary_dir = output_dir / "ternary"
    ternary_dir.mkdir(parents=True, exist_ok=True)
    for e1, e2, e3 in ternary_combos:
        sub_entries = [e for e in entries if set(e.composition.as_dict().keys()) <= {e1, e2, e3}]
        if len(sub_entries) >= 3:
            generate_ternary_composition_diagram(sub_entries, (e1, e2, e3), ternary_dir, "本地数据")

    print("\n" + "=" * 60)
    print("  本地数据模式完成")
    print("=" * 60)
    print(f"输出目录: {output_dir}")


def run_api_mode(config: PhaseDiagramConfig, elements, output_root: str):
    """API 下载模式：从 Materials Project 下载数据生成相图"""
    print(f"\n从Materials Project下载 {get_system_name(elements)} 体系数据")

    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    binary_combos = list(combinations(elements, 2))
    ternary_combos = list(combinations(elements, 3))

    # 二元相图
    print("\n" + "=" * 60)
    print("  生成二元相图")
    print("=" * 60)
    binary_dir = output_dir / "binary"
    binary_dir.mkdir(parents=True, exist_ok=True)
    for e1, e2 in binary_combos:
        try:
            entries = get_entries_from_mp(config, [e1, e2])
            if len(entries) >= 2:
                from pymatgen.analysis.phase_diagram import PDEntry
                pd_entries = [PDEntry(composition=e.composition, energy=e.energy, name=e.name)
                             for e in entries]
                generate_binary_composition_diagram(pd_entries, (e1, e2), binary_dir, "MP数据")
        except Exception as e:
            print(f"    - {e1}-{e2}: {e}")

    # 三元相图
    print("\n" + "=" * 60)
    print("  生成三元相图")
    print("=" * 60)
    ternary_dir = output_dir / "ternary"
    ternary_dir.mkdir(parents=True, exist_ok=True)
    for e1, e2, e3 in ternary_combos:
        try:
            entries = get_entries_from_mp(config, [e1, e2, e3])
            if len(entries) >= 3:
                from pymatgen.analysis.phase_diagram import PDEntry
                pd_entries = [PDEntry(composition=e.composition, energy=e.energy, name=e.name)
                             for e in entries]
                generate_ternary_composition_diagram(pd_entries, (e1, e2, e3), ternary_dir, "MP数据")
        except Exception as e:
            print(f"    - {e1}-{e2}-{e3}: {e}")

    print("\n" + "=" * 60)
    print("  API模式完成")
    print("=" * 60)
    print(f"输出目录: {output_dir}")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        prog="chemphase",
        description="相图与化学势热图统一生成器 v5.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # API模式 - 下载CuAgOSe数据（默认）
  chemphase

  # 指定API模式的元素
  chemphase --elements Li O Co

  # 本地模式 - 读取VASP计算结果
  chemphase --local /path/to/calculations --elements Cu Ag O Se

  # 混合模式 - 本地数据为主
  chemphase --local /path/to/data --elements Cu Ag O Se

  # 启用结构对比
  chemphase --local /path/to/data --elements Cu Ag O Se --compare-structure
        """
    )
    parser.add_argument('--local', type=str, help='本地VASP计算结果目录')
    parser.add_argument('--elements', nargs='+', help='目标元素列表（如 Cu Ag O Se）')
    parser.add_argument('--output', default='phase_diagrams_output', help='输出目录 (默认: phase_diagrams_output)')
    parser.add_argument('--eah', type=float, default=0.05, help='Energy above hull 阈值 (默认: 0.05 eV/atom)')
    parser.add_argument('--compare-structure', action='store_true', help='启用本地结构 vs MP数据库对比')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    print_banner()

    config = PhaseDiagramConfig(
        eah_threshold=args.eah,
        output_root=args.output,
        local_dir=Path(args.local) if args.local else None,
        compare_structure=args.compare_structure,
        debug=args.debug
    )

    if args.local:
        if not args.elements:
            print("错误: 本地模式需要指定 --elements")
            sys.exit(1)
        ok, valid, errors = validate_elements(args.elements)
        if not ok:
            print("错误: " + ", ".join(errors))
            sys.exit(1)
        run_local_mode(config, valid, args.output)
    else:
        ensure_api_key(config)
        elements = args.elements if args.elements else DEFAULT_ELEMENTS
        ok, valid, errors = validate_elements(elements)
        if not ok:
            print("错误: " + ", ".join(errors))
            sys.exit(1)
        run_api_mode(config, valid, args.output)

    print("\n" + "=" * 60)
    print("  执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()