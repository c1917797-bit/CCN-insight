"""Scientific-data regressions: missing values, versions, shared experiments."""
from copy import deepcopy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import rows
from paper_experiments import validate, TABLE

data = rows(TABLE)
args = [rows(n) for n in ('cloud_core_sources', 'ic_compression_topic_cards', 'ic_compression_topics', 'ic_compression_topic_card_refs')]
assert validate(data, *args) == 8
assert len({r['source_id'] for r in data}) == 7
assert len({t for r in data for t in json.loads(r['topic_ids_json'])}) == 4
align = [r for r in data if r['method'] == 'AlignQuant']
assert len(align) == 2 and len({r['experiment_kind'] for r in align}) == 2
assert all(len(json.loads(r['topic_ids_json'])) == 2 for r in align)
system = next(r for r in align if r['experiment_kind'] == 'system')
metrics = {m['metric']: m for m in json.loads(system['performance_metrics_json'])}
assert metrics['TTFT']['result'] > metrics['TTFT']['baseline']
assert metrics['TPOT']['result'] < metrics['TPOT']['baseline']
assert len(json.loads(system['memory_metrics_json'])) == 2

checks = 8
def rejected(label, mutate):
    global checks
    values = deepcopy(data)
    mutate(values)
    try:
        validate(values, *args)
    except (ValueError, TypeError, KeyError):
        checks += 1
        return
    raise AssertionError('Accepted invalid evidence: ' + label)

rejected('foreign source', lambda v: v[0].update(source_id='unknown'))
rejected('unpinned paper', lambda v: v[0].update(source_url='https://arxiv.org/html/2306.00978'))
rejected('different paper', lambda v: v[0].update(source_url='https://arxiv.org/html/2402.02750v6'))
rejected('mismatched version', lambda v: v[0].update(observed_version='v1'))
rejected('duplicate experiment', lambda v: v.append(deepcopy(v[0])))
rejected('missing is not zero', lambda v: v[0].update(performance_status='reported'))
rejected('empty reported measurement', lambda v: v[0].update(quality_metrics_json='[]'))
rejected('foreign topic', lambda v: v[0].update(topic_ids_json='["unknown"]'))
rejected('PPL percentage confusion', lambda v: v[0].update(quality_metrics_json=v[0]['quality_metrics_json'].replace('"PPL"','"%"')))
rejected('kernel renamed TPOT', lambda v: v[-1].update(performance_metrics_json=v[-1]['performance_metrics_json'].replace('key_matvec', 'TPOT')))

# A real zero is a valid reported measurement and must survive unchanged.
zero = deepcopy(data)
metric = json.loads(zero[0]['quality_metrics_json']); metric[0]['result'] = 0
zero[0]['quality_metrics_json'] = json.dumps(metric)
validate(zero, *args)
checks += 1
print(f'PASS: {checks} paper-experiment data contracts; 8 records, 7 primary papers, 4 linked topics')
