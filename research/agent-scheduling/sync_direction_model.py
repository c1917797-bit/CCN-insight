"""Align existing point links with the seven scheduling research directions."""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def sync():
    with (ROOT/'research-directions.csv').open(encoding='utf-8',newline='') as f:
        definitions = {r['point_id']:r for r in csv.DictReader(f)}
    target = ROOT/'scheduling-points.csv'
    with target.open(encoding='utf-8',newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        points = list(reader)
    assert len(points)==len(definitions)==7
    assert {p['id'] for p in points}==set(definitions)
    for point in points:
        definition = definitions[point['id']]
        assert '调度' in definition['title']
        point['title'],point['topic'] = definition['title'],definition['key']
    with target.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(points)
if __name__=='__main__':
    sync()
    print('Aligned seven scheduling points with canonical topic pages.')
