"""Create an inspection copy of the training baseline; never enable hardware IO."""
from pathlib import Path
import argparse,json,shutil
from lxml import etree as ET

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    args=p.parse_args();dest=args.destination.resolve()
    if dest.exists():p.error('Destination exists; choose a new directory')
    source=ROOT/'reference/visionplus'
    if dest.is_relative_to(source.resolve()):p.error('Destination must not be inside the source reference')
    shutil.copytree(source,dest)
    disabled=[]
    suffixes={'.page','.groupflow','.xml','.device','.window'}
    for path in (dest/'Config').rglob('*'):
        if not path.is_file() or path.suffix not in suffixes:continue
        tree=ET.fromstring(path.read_bytes(),parser=ET.XMLParser(huge_tree=True,resolve_entities=False,no_network=True));changed=False
        for node in tree.iter():
            if node.get('Key') in ['CommonIO.WriteData','Algorithm2D_VPImage.SnapVP']:
                node.set('IsEnabled','false');changed=True
                disabled.append({'file':path.relative_to(dest).as_posix(),'id':node.get('Id'),'key':node.get('Key')})
            if node.tag=='Device':node.set('LastStatus','Closed');changed=True
            if node.tag=='HMIWindow':node.set('AutoStart','false');changed=True
        if changed:path.write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
    (dest/'inspection-copy.json').write_text(json.dumps({'mode':'inspection only','hardware_and_capture_nodes_disabled':disabled,'hmi_originally_empty':True,'missing_device_and_main_flow_links_not_repaired':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Inspection copy:',dest/'基线程序.vpsx')
    print('Disabled',len(disabled),'capture / device-write nodes. Original reference files unchanged.')

if __name__=='__main__':main()
