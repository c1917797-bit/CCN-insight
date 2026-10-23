from html import escape as e
from decision_map import read


def gate_fields(area_id):
    row=next(r for r in read('research-gates.csv') if r['area_id']==area_id)
    return ''.join(f'<dt>{label}</dt><dd>{e(row[field])}</dd>' for field,label in [('stage','推进顺序'),('advance','继续条件'),('stop','调整条件'),('unknown','仍缺信息')])


def gate_card(area_id):
    return '<article class="structured-advice research-gate"><h3>什么证据会改变当前建议</h3><dl>'+gate_fields(area_id)+'</dl><p class="note">以上是研究决策条件。业务阈值在实验前约定，尚无本地达标结果。</p></article>'
