"""Validate PBIP/PBIR definitions against Microsoft's public schemas.

Requires internet on first run; caches schemas under outputs/. Does not execute DAX or M.
"""
import json
import warnings
from pathlib import Path
from urllib.request import urlopen

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'outputs/schema-cache'


def fetch(uri):
    # Only retrieve Microsoft's schema repository, including relative schema references.
    prefix = 'https://developer.microsoft.com/json-schemas/'
    if not uri.startswith(prefix):
        raise ValueError(f'Unexpected schema host: {uri}')
    relative = uri[len(prefix):]
    path = CACHE / relative
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen('https://raw.githubusercontent.com/microsoft/json-schemas/main/' + relative, timeout=30) as response:
            path.write_bytes(response.read())
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    count = 0
    for path in sorted((ROOT / 'powerbi').rglob('*')):
        if path.suffix not in {'.json', '.pbip', '.pbir', '.pbism'} or '.pbi' in path.parts:
            continue
        value = json.loads(path.read_text(encoding='utf-8'))
        if '$schema' not in value:
            continue
        schema = fetch(value['$schema'])
        resolver = jsonschema.RefResolver(base_uri=value['$schema'], referrer=schema,
                                         handlers={'https': fetch})
        jsonschema.Draft7Validator(schema, resolver=resolver).validate(value)
        count += 1
    print(f'PASS: {count} PBIP/PBIR files conform to Microsoft JSON schemas.')
    model=json.loads((ROOT/'powerbi/Olist.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
    tables={t['name']:t for t in model['tables']}
    fields={name:{c['name'] for c in table['columns']} | {m['name'] for m in table.get('measures',[])}
            for name,table in tables.items()}
    for relation in model['relationships']:
        assert relation['fromColumn'] in fields[relation['fromTable']],relation
        assert relation['toColumn'] in fields[relation['toTable']],relation
    def references(value):
        if isinstance(value,dict):
            for kind in ['Column','Measure']:
                if kind in value:
                    ref=value[kind]
                    name=ref['Expression']['SourceRef']['Entity']
                    assert ref['Property'] in fields[name],ref
            for child in value.values():
                references(child)
        elif isinstance(value,list):
            for child in value:
                references(child)
    for path in (ROOT/'powerbi/Olist.Report').rglob('visual.json'):
        references(json.loads(path.read_text(encoding='utf-8')))
    print('PASS: all report field references and four relationships point to model columns/measures.')
    print('This checks structure only. DAX, Power Query refresh and visual interaction need Desktop.')


if __name__ == '__main__':
    main()
