"""Import reviewed expert evidence into the maintained operator research JSONs."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'research/ai-infra'


def read(name):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def main():
    corpus = read('operator-routes.json')
    evidence = read('operator-sources.json')
    sources = {row['id']: row for row in evidence['sources']}
    routes = {row['id']: row for branch in corpus['branches'] for row in branch['routes']}
    seen = set()
    for filename in ['operator-expert-compute.json','operator-expert-communication.json']:
        packet = read(filename)
        for source in packet['source_additions']:
            if source['id'] in sources:
                assert sources[source['id']]['url'] == source['url'], source['id']
                sources[source['id']].update(source)
            else:
                evidence['sources'].append(source)
                sources[source['id']] = source
        for patch in packet['routes']:
            key = patch['id']
            assert key in routes and key not in seen, key
            seen.add(key)
            route = routes[key]
            for field in ['brief','conclusion','bottleneck_signal']:
                assert isinstance(patch.get(field),str) and patch[field].strip(), (key,field)
            assert len(patch['branches']) >= 2 and len(patch['evidence_rows']) >= 2, key
            route['expert'] = dict(patch,title=route['title'])
            route['judgment'] = patch['brief']
            route['research_questions'] = patch['open_questions']
            for kind,field in [('industry','boundary'),('academic','evidence_scope')]:
                selected = [row for row in patch['evidence_rows'] if row['kind']==kind]
                assert selected, (key,kind)
                route[kind] = [dict(title=row['work'],mechanism=row['change'],date=row['date'],
                                    conditions=row['conditions'],result=row['result'],
                                    source_ids=row['source_ids'],**{field:row['limit']}) for row in selected]
    assert seen == set(routes), 'Incomplete expert evidence import'
    for route in routes.values():
        for row in route['expert']['branches']:
            assert set(row['evidence_ids']) <= set(sources), route['id']
        for row in route['expert']['evidence_rows']:
            assert set(row['source_ids']) <= set(sources), route['id']
    corpus['updated_at'] = evidence['reviewed_at'] = '2026-10-23'
    # Preserve stable source ordering so already displayed citation numbers do not move.
    for name,data in [('operator-routes.json',corpus),('operator-sources.json',evidence)]:
        (DATA/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Integrated {len(seen)} operator dossiers; {len(sources)} primary/official sources')


if __name__ == '__main__':
    main()
