"""Compare existing extracted files with manifests in existing local ZIPs; no extraction."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('reports/audit/archive-provenance.json'))
    args=parser.parse_args()
    records=[]
    for archive in sorted(args.root.glob('*.zip')):
        item={'archive':str(archive),'metadata':{},'checks':[]}
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                if Path(entry.filename).name in {'bag-info.txt','FurtherInformation.txt','manifest-sha1.txt'}:
                    if entry.file_size>100000:
                        raise ValueError('Unexpected oversized metadata')
                    item['metadata'][Path(entry.filename).name]=z.read(entry).decode('utf-8-sig')
            for line in item['metadata'].get('manifest-sha1.txt','').splitlines():
                if not line.strip():
                    continue
                expected,member=line.split(maxsplit=1)
                matches=list(args.root.rglob(Path(member).name))
                for candidate in matches:
                    if not candidate.is_file():
                        continue
                    with candidate.open('rb') as handle:
                        actual=hashlib.file_digest(handle,'sha1').hexdigest()
                    item['checks'].append({'member':member,'local_path':str(candidate),'expected_sha1':expected,'actual_sha1':actual,'matches':expected.lower()==actual})
        records.append(item)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'archives':records,'limitation':'SHA-1 matches establish consistency with these local manifests, not independent authenticity or label correctness.'},indent=2),encoding='utf-8')
    print(json.dumps({'archives':len(records),'comparisons':sum(len(i['checks']) for i in records),'all_matched':all(c['matches'] for i in records for c in i['checks'])}))


if __name__=='__main__':
    main()
