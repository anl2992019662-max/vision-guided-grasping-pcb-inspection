import argparse
from datetime import datetime,timezone
from pathlib import Path
import json
from PIL import Image
from .demo import run_demo,write_json
from .geometry import focal_limit,teaching_fov,fit_planar_affine
from .inspection import inspect,draw_record

def main():
    parser=argparse.ArgumentParser(description='Machine vision training reference; offline by default')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('demo',help='Generate labelled synthetic cases and run the complete offline workflow')
    p.add_argument('--output',type=Path,default=Path('output')/datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    p=commands.add_parser('optics',help='Solve the two taskbook optics exercises')
    p=commands.add_parser('calibrate',help='Fit a planar affine mapping from explicitly identified point data')
    p.add_argument('--points',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('inspect',help='Inspect a registered image with an explicit ROI configuration')
    p.add_argument('--image',type=Path,required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='demo':
        result=run_demo(args.output);print(json.dumps(result,ensure_ascii=False,indent=2));print('Open:',args.output/'index.html')
    elif args.command=='optics':
        print(json.dumps({'example_focal_mm':6.4*400/160,'exercise':focal_limit(6.4,4.6,150,[16,12]),'fov_at_50mm':teaching_fov(6.4,4.6,150,50),'scope':'taskbook approximation; verify actual lens minimum object distance and FOV'},ensure_ascii=False,indent=2))
    elif args.command=='calibrate':
        if args.output.exists():raise FileExistsError('Output already exists')
        source=json.loads(args.points.read_text(encoding='utf-8'));result=fit_planar_affine(source['pixels'],source['robot_xy_mm'])
        result.update(data_origin='synthetic' if source.get('is_synthetic') is True else 'caller supplied, unverified',is_synthetic=source.get('is_synthetic'))
        args.output.parent.mkdir(parents=True,exist_ok=True);write_json(args.output,result);print(args.output)
    elif args.command=='inspect':
        if args.output.exists():raise FileExistsError('Output folder already exists')
        config=json.loads(args.config.read_text(encoding='utf-8'))
        with Image.open(args.image) as im:image=im.convert('RGB')
        result=inspect(image,config);result.update(data_origin='caller supplied, unverified',source_image=args.image.name)
        args.output.mkdir(parents=True);write_json(args.output/'result.json',result);draw_record(image,result).save(args.output/'record.png');print(args.output)

if __name__=='__main__':main()
