"""Teaching examples, deliberately separate from factual publication records."""
from html import escape as e
from decision_map import read

def worked_example(area):
    r=next(r for r in read('reader-examples.csv') if r['area_id']==area)
    stages=[('observe','观察输入'),('constraint','检查约束'),('decision','作出选择'),('feedback','根据结果调整')]
    steps=''.join(f'<li><span>{i:02d}</span><h4>{label}</h4><p>{e(r[key])}</p></li>' for i,(key,label) in enumerate(stages,1))
    return f'''<article class="worked-example" id="worked-example"><p class="eyebrow">先看一个例子 / 教学设计</p><h3>{e(r['title'])}</h3><ol class="decision-walkthrough">{steps}</ol><p class="example-boundary"><strong>示例边界：</strong>{e(r['boundary'])}</p><p class="example-terms"><strong>本节词汇：</strong>{e(r['terms'])}</p></article>'''
