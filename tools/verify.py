"""Check source preservation, provenance, example outputs and document links."""
from pathlib import Path
import base64,csv,hashlib,json,re
from urllib.parse import unquote
from PIL import Image
from lxml import etree as ET

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))

def main():
    checks=[]
    def check(condition,description):
        if not condition:raise AssertionError(description)
        checks.append(description)
    files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in {'.git','__pycache__','output'} or x.startswith('runtime') for x in p.relative_to(ROOT).parts)]
    for p in files:
        check(not {'AccountAuthority','MPA','Logs','LogDog','Temp'}.intersection(p.relative_to(ROOT).parts) and p.name!='DongleConfig.ini' and p.suffix!='.db','excluded sensitive/runtime content: '+p.relative_to(ROOT).as_posix())
        check(p.stat().st_size<100*1024**2,'repository file under 100 MiB: '+p.relative_to(ROOT).as_posix())
        if p.suffix in {'.md','.json','.py','.html','.yml','.txt'}:
            text=p.read_text(encoding='utf-8-sig')
            check(not re.search(r'[A-Za-z]:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{30,}',text),'no private path/token pattern: '+p.relative_to(ROOT).as_posix())
        if p.suffix in {'.md','.html'}:
            text=p.read_text(encoding='utf-8');links=re.findall(r'\]\(([^)]+)\)',text) if p.suffix=='.md' else re.findall(r'(?:src|href)="([^"]+)"',text)
            for link in links:
                if re.match(r'https?://|mailto:|#',link):continue
                local=unquote(link.split('#')[0]);check((p.parent/local).exists(),'local document link: '+local)
    baseline=load('manifests/baseline-files.json');check(len(baseline)==64,'64 preserved baseline files')
    for row in baseline:check(sha(ROOT/row['file'])==row['sha256'],'baseline original hash: '+row['file'])
    for row in load('manifests/external-images.json'):
        check(sha(ROOT/row['file'])==row['sha256'],'upstream hardware photo bytes: '+row['file'])
        check(bool(row['author_and_license']),'external photo attribution and license are recorded')
    parsed={};parser=ET.XMLParser(huge_tree=True,resolve_entities=False,no_network=True)
    for row in load('manifests/extracted-training-images.json'):
        check(sha(ROOT/row['file'])==row['sha256'],'extracted training image hash')
        with Image.open(ROOT/row['file']) as image:
            check(list(image.size)==row['dimensions'] and hashlib.sha256(image.tobytes()).hexdigest()==row['raw_pixel_sha256'],'full-frame pixels preserved from original training reference')
        if row['source'] not in parsed:parsed[row['source']]=ET.fromstring((ROOT/row['source']).read_bytes(),parser=parser)
        node=next(x for x in parsed[row['source']].iter('Image') if x.get('ID')==row['image_id'])
        check(hashlib.sha256(base64.b64decode(node.findtext('Data'),validate=True)).hexdigest()==row['raw_pixel_sha256'],'source XML embedded pixels match extraction')
    for p in (ROOT/'reference/visionplus/Config').rglob('*'):
        if not p.is_file() or p.suffix=='.csv':continue
        root=ET.fromstring(p.read_bytes(),parser=parser)
        private_found=False
        for node in root.iter():
            values=list(node.attrib.values())+([node.text] if node.text and len(node.text)<8192 else [])
            for value in values:
                if len(value)<8192 and re.search(r'[A-Za-z]:\\Users\\|gh[pousr]_[A-Za-z0-9]{20,}',value):private_found=True
        check(not private_found,'no private path/token in baseline XML: '+p.relative_to(ROOT).as_posix())
    summary=load('examples/demo/summary.synthetic.json')
    check(summary['is_synthetic'] is True and (summary['samples'],summary['passed_samples'],summary['ng_samples'])==(6,1,5),'six labelled synthetic demo results')
    check(summary['robot_plan']['sent'] is False,'demo did not send robot motion')
    for case in ['ok','missing_resistor','missing_capacitor','wrong_capacitor_colour','missing_chip','multiple_defects']:
        row=load('examples/demo/'+case+'.json');check(row['is_synthetic'] is True,'synthetic origin retained in '+case)
        check(row['passed']==(case=='ok'),'expected example result for '+case)
        for key in ['source_image','record_image']:
            path=ROOT/'examples/demo'/row[key]
            with Image.open(path) as im:check(im.size==(960,640),'full-size demo image '+path.name)
    with (ROOT/'examples/demo/results.synthetic.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f));check(len(rows)==6 and all(x['is_synthetic']=='true' for x in rows),'CSV rows label synthetic data')
    print('PASS:',len(checks),'file / provenance / document checks;',len(files),'files. No live hardware execution claimed.')
    return {'passed':len(checks),'files':len(files),'scope':'static source/provenance/example checks; no physical hardware execution'}

if __name__=='__main__':main()
