"""Apply the approved route navigation copy, preserving existing research and IDs."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'original-reader/site/business_insight/cloud_core'


def update(table, changes):
    path = ROOT/'data/compression/tables'/table/'rows.jsonl'
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    changed = 0
    for item in records:
        values = changes.get(item['key'])
        if values and not item.get('deleted') and any(item['row'].get(key) != value for key, value in values.items()):
            item['row'].update(values)
            item['row_version'] += 1
            changed += 1
    path.write_text(''.join(json.dumps(item, ensure_ascii=False, separators=(',', ':'))+'\n' for item in records), encoding='utf-8')
    return changed


def main():
    count = update('ic_compression_topics', {
        'parameters-distillation': {'title_zh': '知识蒸馏与紧凑学生模型', 'title_en': 'Knowledge distillation and compact students', 'question_zh': '怎样通过教师监督训练紧凑学生，在减少部署开销时保留更多能力？'},
        'activations-distillation': {'title_zh': '特征监督与紧凑中间表示', 'title_en': 'Feature supervision and compact intermediate representations'},
        'kv_cache-distillation': {'title_zh': '紧凑注意力与 KV 结构蒸馏', 'title_en': 'Distillation for compact attention and KV structures'},
    })
    # This is an editorial reorganization, not a new primary-source review.
    cards = ROOT/'data/compression/tables/ic_compression_topic_cards/rows.jsonl'
    rows = [json.loads(line) for line in cards.read_text(encoding='utf-8').splitlines() if line.strip()]
    card = next(item['row'] for item in rows if item['key'] == 'parameters-distillation__dossier_5')
    count += update('ic_compression_topic_cards', {'parameters-distillation__dossier_5': {
        'body_zh': card['body_zh'].replace('技术定位：在技术地图中，蒸馏应作为跨对象的训练与恢复方法，与量化、剪枝和低秩路线关联。', '技术定位：知识蒸馏是独立研究主线，以教师、学生、监督信号和能力迁移为核心；也与量化、剪枝和低秩路线的质量恢复关联。'),
        'body_en': card['body_en'].replace('Map position: treat distillation as a training and recovery method spanning quantization, pruning and low-rank routes.', 'Map position: distillation is a core research route organized around teachers, students, supervision and capability transfer; it also supports quality recovery in quantization, pruning and low-rank routes.'),
    }})
    for language, copy in {
        'zh': {'topics_help': '沿四条研究路线阅读原理、挑战与进展，再按压缩对象查找具体专题。相关月度新增证据见“本期动态”。', 'map_help': '四条主线组织长期研究，压缩对象提供检索入口；本期动态记录新增证据，洞察报告形成综合判断。'},
        'en': {'topics_help': 'Explore four core research routes, then filter by compression target. New monthly evidence appears in Current updates.', 'map_help': 'Core routes organize enduring research, while target filters help retrieval. Current updates record new evidence, and Insight reports synthesize judgments.'},
    }.items():
        path = BASE/f'data/focus-ui.{language}.json'
        pack = json.loads(path.read_text(encoding='utf-8'))
        pack['strings'].update(copy)
        path.write_text(json.dumps(pack, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    bootstrap = (BASE/'reader-bootstrap.js').read_text(encoding='utf-8').strip()
    for name in ['index.html', 'topic.html', 'monthly.html']:
        path = BASE/name
        text = path.read_text(encoding='utf-8')
        text, replaced = re.subn(r'(<script data-lri-reader-bootstrap>\s*).*?(\s*</script>)', lambda match: match[1]+bootstrap+match[2], text, count=1, flags=re.S)
        assert replaced == 1, name
        text = text.replace('每个交叉格对应一个研究专题，介绍背景、原理、技术路线与代表文献。相关月度进展见“本期动态”。', '沿四条研究路线阅读原理、挑战与进展，再按压缩对象查找具体专题。相关月度新增证据见“本期动态”。')
        path.write_text(text, encoding='utf-8')
    print(f'Updated {count} editorial records; localized navigation and inline bootstrap synchronized')


if __name__ == '__main__':
    main()
