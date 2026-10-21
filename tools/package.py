"""Create a complete source archive; generated runs and credentials stay excluded."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]

def files():
    ignored={'.git','__pycache__','.venv','output','AccountAuthority','MPA','Logs','LogDog','Temp'}
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(s in ignored or s.startswith('runtime') for s in p.relative_to(ROOT).parts) and p.name!='DongleConfig.ini' and p.suffix not in {'.zip','.db','.pyc'}]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():p.error('Output archive already exists')
    selected=files()
    rows=[{'file':f.relative_to(ROOT).as_posix(),'bytes':f.stat().st_size,'sha256':digest(f)} for f in selected if f.name!='repository-files.json']
    manifest=ROOT/'manifests/repository-files.json';manifest.write_text(json.dumps({'scope':'repository files except this inventory itself','files':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    selected=files();args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for f in selected:z.write(f,'machine-vision-national-prep/'+f.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(args.output) as z:assert z.testzip() is None
    sums=args.output.with_name('SHA256SUMS.txt');sums.write_text(digest(args.output)+'  '+args.output.name+'\n',encoding='utf-8',newline='\n')
    print('Packaged',len(selected),'files;',round(args.output.stat().st_size/1e6,2),'MB;',digest(args.output))

if __name__=='__main__':main()
