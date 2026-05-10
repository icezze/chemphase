"""核心模块：配置管理、VASP 数据解析、Materials Project API、结构对比"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from itertools import combinations

# ============================================================
# 元素验证
# ============================================================
VALID_ELEMENTS = {
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
    'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
    'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
    'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
    'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
    'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm',
    'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
    'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'
}

EAH_THRESHOLD = 0.05         # 能量 above hull 阈值 (eV/atom)
OUTPUT_ROOT = "phase_diagrams_output"
UNIFIED_PHASES_DIR = "unified_phases"
DEFAULT_ELEMENTS = ["Cu", "Ag", "O", "Se"]
STRUCTURE_TOLERANCE = 0.2    # 结构匹配容忍度


def validate_elements(elements: List[str]) -> Tuple[bool, List[str], List[str]]:
    """验证元素符号是否有效"""
    errors = []
    valid = []
    for elem in elements:
        elem = elem.strip().capitalize()
        if elem in VALID_ELEMENTS:
            valid.append(elem)
        else:
            errors.append(f"'{elem}' 不是有效元素符号")
    return len(errors) == 0, valid, errors


# ============================================================
# 配置类
# ============================================================
class PhaseDiagramConfig:
    """相图生成配置"""

    def __init__(self, api_key: str = "", eah_threshold: float = EAH_THRESHOLD,
                 output_root: str = OUTPUT_ROOT, unified_phases_dir: str = UNIFIED_PHASES_DIR,
                 debug: bool = False, local_dir: Optional[Path] = None,
                 compare_structure: bool = False):
        self.api_key = api_key or os.environ.get("MATERIALS_PROJECT_API_KEY", "")
        self.eah_threshold = eah_threshold
        self.output_root = output_root
        self.unified_phases_dir = unified_phases_dir
        self.debug = debug
        self.local_dir = local_dir
        self.compare_structure = compare_structure

    @property
    def database_file(self) -> Path:
        return Path(self.unified_phases_dir) / "phases_database.json"


def ensure_api_key(config: PhaseDiagramConfig) -> str:
    """确保 API 密钥可用，优先从环境变量读取"""
    if not config.api_key:
        print("\n" + "=" * 60)
        print("  请设置 Materials Project API 密钥")
        print("=" * 60)
        print("  获取方式: https://materialsproject.org/api")
        print("  环境变量: export MATERIALS_PROJECT_API_KEY=你的密钥")
        print()
        key = input("  请输入API密钥: ").strip()
        if not key:
            print("  未输入密钥，退出")
            sys.exit(0)
        config.api_key = key
        print("  ⚠ 密钥仅本次有效，建议设置环境变量 MATERIALS_PROJECT_API_KEY")
    return config.api_key


# ============================================================
# 本地 VASP 数据解析
# ============================================================

def parse_energy_from_vasprun(vasprun_path: str, debug: bool = False) -> Optional[float]:
    """从 vasprun.xml 解析最终能量"""
    try:
        from pymatgen.io.vasp.outputs import Vasprun
        vr = Vasprun(vasprun_path)
        return vr.final_energy
    except Exception as e:
        if debug:
            print(f"    vasprun.xml解析失败: {e}")
        return None


def parse_energy_from_outcar(outcar_path: str, debug: bool = False) -> Optional[float]:
    """从 OUTCAR 解析最终能量"""
    try:
        with open(outcar_path, 'r') as f:
            content = f.read()
        matches = re.findall(r'energy\(sigma->0\)\s*=\s*([-\d.]+)', content)
        if matches:
            return float(matches[-1])
    except Exception as e:
        if debug:
            print(f"    OUTCAR解析失败: {e}")
    return None


def parse_structure_info(poscar_path: str, debug: bool = False) -> Tuple[Optional[str], Optional[int]]:
    """从 POSCAR 解析化学式和原子数"""
    try:
        from pymatgen.core import Structure
        structure = Structure.from_file(poscar_path)
        return structure.composition.reduced_formula, structure.num_atoms
    except Exception as e:
        if debug:
            print(f"    POSCAR解析失败: {e}")
        return None, None


def parse_phase_directory(phase_dir: Path, eah_threshold: float = EAH_THRESHOLD) -> Optional[Dict]:
    """解析单个 VASP 计算目录"""
    dir_name = phase_dir.name
    name_match = re.match(r'(.+?)_EaH_([\d.]+)(_stable)?', dir_name)
    if not name_match:
        return None

    formula_from_name = name_match.group(1)
    eah = float(name_match.group(2))
    is_stable = name_match.group(3) == '_stable' or eah < eah_threshold

    poscar = phase_dir / "POSCAR"
    vasprun = phase_dir / "vasprun.xml"
    outcar = phase_dir / "OUTCAR"

    if not poscar.exists():
        return None

    formula, num_atoms = parse_structure_info(str(poscar))
    if not formula:
        formula = formula_from_name

    energy = None
    if vasprun.exists():
        energy = parse_energy_from_vasprun(str(vasprun))
    elif outcar.exists():
        energy = parse_energy_from_outcar(str(outcar))

    if energy is None:
        return None

    energy_per_atom = energy / num_atoms if num_atoms else None
    from pymatgen.core import Composition
    elements = list(set(Composition(formula).as_dict().keys()))

    return {
        'name': dir_name,
        'formula': formula,
        'energy': energy,
        'energy_per_atom': energy_per_atom,
        'num_atoms': num_atoms,
        'eah': eah,
        'is_stable': is_stable,
        'elements': elements,
        'path': str(phase_dir)
    }


def scan_local_phases(local_dir: Path, target_elements: Optional[List[str]] = None,
                      eah_threshold: float = EAH_THRESHOLD) -> List[Dict]:
    """扫描本地目录中的所有 VASP 计算"""
    if not local_dir.exists():
        print(f"目录不存在: {local_dir}")
        return []

    phases = []
    target_set = set(target_elements) if target_elements else None

    for phase_dir in local_dir.iterdir():
        if not phase_dir.is_dir():
            continue
        phase_data = parse_phase_directory(phase_dir, eah_threshold)
        if phase_data is None:
            continue
        if target_set:
            phase_elements = set(phase_data['elements'])
            if not phase_elements <= target_set:
                continue
        phases.append(phase_data)

    return phases


def build_local_entries(phases: List[Dict]) -> List:
    """从本地相数据构建 pymatgen PDEntry 列表"""
    from pymatgen.core import Structure
    from pymatgen.analysis.phase_diagram import PDEntry

    entries = []
    for phase in phases:
        try:
            structure = Structure.from_file(phase['path'] + "/POSCAR")
            entry = PDEntry(
                composition=structure.composition,
                energy=phase['energy'],
                name=phase['name']
            )
            entries.append(entry)
        except Exception as e:
            print(f"    构建Entry失败 {phase['name']}: {e}")
    return entries


# ============================================================
# 结构对比功能
# ============================================================

def compare_structures(local_structure, mp_structure,
                       tolerance: float = STRUCTURE_TOLERANCE) -> Dict:
    """比较两个晶体结构的相似度"""
    from pymatgen.analysis.structure_matcher import StructureMatcher
    matcher = StructureMatcher(ltol=tolerance, stol=tolerance, angle_tol=10)
    try:
        is_same = matcher.fit(local_structure, mp_structure)
        return {
            'is_same': is_same,
            'local_formula': local_structure.composition.reduced_formula,
            'mp_formula': mp_structure.composition.reduced_formula,
            'local_sites': len(local_structure.sites),
            'mp_sites': len(mp_structure.sites),
            'local_volume': local_structure.volume,
            'mp_volume': mp_structure.volume,
            'volume_diff_percent': abs(local_structure.volume - mp_structure.volume) / mp_structure.volume * 100
        }
    except Exception as e:
        return {
            'is_same': False,
            'error': str(e),
            'local_formula': local_structure.composition.reduced_formula,
            'mp_formula': mp_structure.composition.reduced_formula
        }


def structure_comparison_report(local_phases: List[Dict], config: PhaseDiagramConfig) -> Dict:
    """生成结构对比报告"""
    from pymatgen.ext.matproj import MPRester
    from pymatgen.core import Structure

    report = {
        'total_compared': 0,
        'matching': 0,
        'different': 0,
        'not_found_in_mp': 0,
        'details': []
    }

    if not config.api_key:
        print("  ! 无API密钥，跳过结构对比")
        return report

    try:
        mpr = MPRester(api_key=config.api_key)
    except Exception as e:
        print(f"  ! 无法连接Materials Project: {e}")
        return report

    for phase in local_phases:
        formula = phase['formula']
        report['total_compared'] += 1

        try:
            mp_entries = mpr.get_entries(formula, inc_structure=True)
            if not mp_entries:
                report['not_found_in_mp'] += 1
                report['details'].append({
                    'formula': formula,
                    'status': 'not_found_in_mp',
                    'message': f'在MP数据库中未找到 {formula}'
                })
                continue

            local_structure = Structure.from_file(phase['path'] + "/POSCAR")
            mp_entry = mp_entries[0]
            mp_structure = mp_entry.structure

            comparison = compare_structures(local_structure, mp_structure)
            comparison['formula'] = formula
            comparison['local_path'] = phase['path']

            if comparison['is_same']:
                report['matching'] += 1
                comparison['status'] = 'matching'
            else:
                report['different'] += 1
                comparison['status'] = 'different'

            report['details'].append(comparison)

        except Exception as e:
            report['not_found_in_mp'] += 1
            report['details'].append({
                'formula': formula,
                'status': 'error',
                'message': str(e)
            })

    return report


# ============================================================
# 工具函数
# ============================================================

def get_all_element_combinations(elements: List[str], min_size: int = 2) -> List:
    """获取元素的所有组合（从 min_size 到全部）"""
    result = []
    for r in range(min_size, len(elements) + 1):
        for combo in combinations(elements, r):
            result.append(combo)
    return result


def load_database(config: PhaseDiagramConfig) -> Dict:
    """加载本地相数据库"""
    Path(config.unified_phases_dir).mkdir(parents=True, exist_ok=True)
    if config.database_file.exists():
        with open(config.database_file, 'r') as f:
            return json.load(f)
    return {"phases": {}, "download_history": [], "element_systems": {}}


def save_database(config: PhaseDiagramConfig, db: Dict):
    """保存本地相数据库"""
    Path(config.unified_phases_dir).mkdir(parents=True, exist_ok=True)
    with open(config.database_file, 'w') as f:
        json.dump(db, f, indent=2, sort_keys=True)


def get_entries_from_mp(config: PhaseDiagramConfig, elements: List[str]):
    """从 Materials Project 下载条目"""
    from pymatgen.ext.matproj import MPRester
    mpr = MPRester(api_key=config.api_key)
    return mpr.get_entries_in_chemsys(elements)


def get_system_name(elements: List[str]) -> str:
    """获取体系名称（排序后的元素用下划线连接）"""
    return "_".join(sorted(elements))


def print_banner():
    """打印启动横幅"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║       相图与化学势热图统一生成器 v5.0 (chemphase)                       ║
║    Phase Diagram & Chemical Potential Heatmap Generator                 ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")