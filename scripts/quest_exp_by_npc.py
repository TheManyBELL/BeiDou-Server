# -*- coding: utf-8 -*-
"""
根据 NPC ID 修改其相关任务的经验值。
从 Check.img.xml 中按 NPC 收集 QuestID，再在两个 Act.img.xml 中替换对应任务的 exp 字段。
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# 项目根目录（脚本在 scripts/ 下时，上级为根）
ROOT = Path(__file__).resolve().parent.parent

# 本次配置: (NPC ID, 经验值)
NPC_EXP_CONFIG = [
    (2140000, 6000000),
    (9270062, 7000000),
]

CHECK_PATH = ROOT / "gms-server" / "wz-zh-CN" / "Quest.wz" / "Check.img.xml"
ACT_PATHS = [
    ROOT / "gms-server" / "wz-zh-CN" / "Quest.wz" / "Act.img.xml",
    ROOT / "gms-server" / "wz" / "Quest.wz" / "Act.img.xml",
]


def _has_npc_in_tree(element, npc_id: str) -> bool:
    """递归检查子树中是否存在 <int name="npc" value="npc_id"/>"""
    if element.tag == "int" and element.get("name") == "npc":
        if element.get("value") == npc_id:
            return True
    for child in element:
        if _has_npc_in_tree(child, npc_id):
            return True
    return False


def collect_quest_ids_by_npc(check_path: Path, npc_exp_config: list) -> dict:
    """
    从 Check.img.xml 收集每个 NPC 对应的 QuestID 列表。
    npc_exp_config: [(npc_id, exp), ...]，npc_id 为 int 或 str。
    返回: { "npc_id_str": [quest_id_str, ...], ... }
    """
    tree = ET.parse(check_path, parser=ET.XMLParser(encoding="utf-8"))
    root = tree.getroot()

    result = {}
    for npc_id, _ in npc_exp_config:
        npc_id_str = str(npc_id)
        result[npc_id_str] = []

    for quest_imgdir in root:
        if quest_imgdir.tag != "imgdir":
            continue
        quest_id = quest_imgdir.get("name")
        if not quest_id:
            continue
        for npc_id, _ in npc_exp_config:
            npc_id_str = str(npc_id)
            if _has_npc_in_tree(quest_imgdir, npc_id_str):
                result[npc_id_str].append(quest_id)
                break

    return result


def build_quest_to_exp(npc_quest_lists: dict, npc_exp_config: list) -> dict:
    """
    构建 QuestID -> 经验值 映射。同一 QuestID 被多个 NPC 命中时，按配置顺序后者覆盖。
    返回: { "quest_id_str": exp_int, ... }
    """
    quest_to_exp = {}
    for npc_id, exp in npc_exp_config:
        npc_id_str = str(npc_id)
        for qid in npc_quest_lists.get(npc_id_str, []):
            quest_to_exp[qid] = exp
    return quest_to_exp


def _find_quest_block_bounds(content: str, quest_id: str) -> tuple:
    """
    在 Act 文件内容中定位 <imgdir name="quest_id"> 对应的整块（含嵌套）的 (start, end) 字符位置。
    若未找到或匹配失败返回 (None, None)。
    """
    pattern = re.compile(
        r'<imgdir\s+name="' + re.escape(quest_id) + r'"\s*>',
        re.IGNORECASE
    )
    match = pattern.search(content)
    if not match:
        return None, None
    start = match.start()
    # 找到开标签的 > 位置，从其后开始扫描
    end_bracket = content.index(">", match.start())
    i = end_bracket + 1
    depth = 1
    while i < len(content) and depth > 0:
        if content[i] != "<":
            i += 1
            continue
        # 先检查结束标签 </imgdir>（共 9 个字符）
        if i + 9 <= len(content) and content[i : i + 9] == "</imgdir>":
            depth -= 1
            if depth == 0:
                return start, i + 9
            i += 9
            continue
        # 开始标签 <imgdir ...> 或自闭合 <imgdir .../>；仅非自闭合的计入 depth
        if i + 7 <= len(content) and content[i : i + 7] == "<imgdir":
            tag_end = content.find(">", i + 7)
            if tag_end == -1:
                i += 1
                continue
            # 自闭合为 .../>，非自闭合为 ...>
            if tag_end > 0 and content[tag_end - 1] == "/":
                i = tag_end + 1
                continue
            depth += 1
            i = tag_end + 1
            continue
        i += 1
    return None, None


def replace_exp_in_act_file(act_path: Path, quest_to_exp: dict, encoding: str = "utf-8") -> int:
    """
    在单个 Act 文件中，对 quest_to_exp 中的每个任务块内替换 exp 的 value。
    仅当该任务块内存在 <int name="exp" value="..."/> 时才替换。
    返回修改过的任务数量。
    """
    act_path = Path(act_path)
    content = act_path.read_text(encoding=encoding)
    original_content = content
    modified_count = 0
    # 从后往前替换，避免偏移变化
    for quest_id in sorted(quest_to_exp.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True):
        exp_value = quest_to_exp[quest_id]
        start, end = _find_quest_block_bounds(content, quest_id)
        if start is None:
            continue
        block = content[start:end]
        # 只替换该块内的 exp 节点（兼容可能的空格/换行差异）
        new_block = re.sub(
            r'(<int\s+name="exp"\s+value=")\d+(")\s*/>',
            r'\g<1>' + str(exp_value) + r'\g<2>/>',
            block,
            count=1,
        )
        if new_block != block:
            content = content[:start] + new_block + content[end:]
            modified_count += 1
    if content != original_content:
        act_path.write_text(content, encoding=encoding)
    return modified_count


def main():
    print("Quest exp by NPC: 从 Check 收集任务 ID，并修改 Act 中的经验值")
    print("配置:", NPC_EXP_CONFIG)
    print("Check:", CHECK_PATH)

    if not CHECK_PATH.exists():
        print("错误: Check 文件不存在:", CHECK_PATH)
        return

    npc_quest_lists = collect_quest_ids_by_npc(CHECK_PATH, NPC_EXP_CONFIG)
    for npc_id, exp in NPC_EXP_CONFIG:
        lst = npc_quest_lists.get(str(npc_id), [])
        print(f"  NPC {npc_id} -> 经验 {exp}: QuestID 数量 {len(lst)}")

    quest_to_exp = build_quest_to_exp(npc_quest_lists, NPC_EXP_CONFIG)
    print("待修改任务数:", len(quest_to_exp))

    for act_path in ACT_PATHS:
        if not act_path.exists():
            print("跳过不存在的 Act 文件:", act_path)
            continue
        n = replace_exp_in_act_file(act_path, quest_to_exp)
        print("已修改", act_path.name, "中", n, "个任务的 exp")


if __name__ == "__main__":
    main()
