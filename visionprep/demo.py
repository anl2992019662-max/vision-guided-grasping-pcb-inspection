"""Run real inspection code against clearly labelled synthetic fixtures."""
from datetime import datetime, timezone
from pathlib import Path
import csv
import html
import json
import logging
import re
from .samples import CASES, make_sample, default_rois, calibration_example
from .inspection import inspect, draw_record
from .geometry import fit_planar_affine, transform_xy, focal_limit, teaching_fov
from .protocols import robot_move, read_request, write_request

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',encoding='utf-8',newline='\n')

def run_demo(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Output folder is not empty; choose a new folder to preserve prior records')
    output.mkdir(parents=True,exist_ok=True)
    (output/'images').mkdir(exist_ok=True)
    config=default_rois();points=calibration_example();fit=fit_planar_affine(points['pixels'],points['robot_xy_mm'])
    pick=transform_xy(fit['matrix'],[480,320])
    command=robot_move(*pick,50,0,points['example_workspace_limits'])
    write_json(output/'roi.synthetic.json',config)
    write_json(output/'calibration.synthetic.json',points)
    write_json(output/'calibration-fit.synthetic.json',dict(fit,is_synthetic=True))
    rows=[];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    log=logging.getLogger('visionprep.demo.'+stamp);log.setLevel(logging.INFO);log.propagate=False
    handler=logging.FileHandler(output/'user-log.jsonl',encoding='utf-8');handler.setFormatter(logging.Formatter('%(message)s'));log.addHandler(handler)
    try:
        for i,case in enumerate(CASES):
            image=make_sample(case,2026+i)
            report=inspect(image,config)
            source='images/SourceImage_'+stamp+'_'+case+'.png'
            record='images/RecordImage_'+stamp+'_'+case+'.png'
            image.save(output/source);draw_record(image,report).save(output/record)
            report.update(sample_id=case,is_synthetic=True,data_origin='generated training fixture',
                          timestamp_utc=stamp,source_image=source,record_image=record,
                          robot_plan={'mode':'offline string only','target_xy_mm':pick,'command':command},
                          plc_result_demo_code=1 if report['passed'] else 2)
            write_json(output/(case+'.json'),report);rows.append(report)
            log.info(json.dumps({'event':'inspection_finished','is_synthetic':True,'sample':case,'passed':report['passed'],'timestamp_utc':stamp},ensure_ascii=False))
    finally:
        handler.close();log.removeHandler(handler)
    with (output/'results.synthetic.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['timestamp_utc','sample_id','is_synthetic','passed','failed_components','plc_result_demo_code','source_image','record_image'])
        for r in rows:writer.writerow([stamp,r['sample_id'],'true',r['passed'],','.join(c['id'] for c in r['components'] if not c['passed']),r['plc_result_demo_code'],r['source_image'],r['record_image']])
    summary={'is_synthetic':True,'purpose':'functional software exercise; not field performance data','samples':len(rows),
             'passed_samples':sum(r['passed'] for r in rows),'ng_samples':sum(not r['passed'] for r in rows),
             'plc_protocol_examples':{'read_address_0_hex':read_request(1,1,0).hex(' '),'write_result_1_hex':write_request(2,1,1,1).hex(' '),'result_codes':'new demo convention: 0 WAIT, 1 OK, 2 NG; confirm PLC program mapping before use'},
             'planar_fit':dict(fit,is_synthetic=True),'robot_plan':{'command':command,'sent':False,'target_xy_mm':pick},
             'optics':{'example_focal_mm':16.0,'exercise_limits':focal_limit(6.4,4.6,150,[16,12]),'fov_at_50mm':teaching_fov(6.4,4.6,150,50)},
             'real_hardware_verification':'not performed'}
    write_json(output/'summary.synthetic.json',summary)
    (output/'index.html').write_text(render_html(rows,summary),encoding='utf-8',newline='\n')
    return summary

def render_html(rows, summary):
    labels={'ok':'合格样例','missing_resistor':'电阻缺失','missing_capacitor':'电容缺失','wrong_capacitor_colour':'电容颜色不符','missing_chip':'芯片缺失','multiple_defects':'多项缺陷'}
    cards=[]
    for row in rows:
        parts=''.join('<tr><td>'+html.escape(c['id'])+'</td><td>'+html.escape(c['kind'])+'</td><td>'+('OK' if c['passed'] else 'NG')+'</td><td>'+f"{c['metrics']['gray_variance']:.2f}"+'</td></tr>' for c in row['components'])
        cards.append(f'''<section class="sample"><div class="sample-head"><h2>{labels[row['sample_id']]}</h2><span class="{'pass' if row['passed'] else 'fail'}">{'OK' if row['passed'] else 'NG'}</span></div><div class="sample-grid"><img src="{row['record_image']}" alt="已标明合成来源的离线检测结果"><div><h3>真实执行的检测计算</h3><table><tr><th>器件</th><th>方法类别</th><th>结果</th><th>灰度方差</th></tr>{parts}</table><p>完整灰度、颜色比例和阈值见 <a href="{row['sample_id']}.json">该样例 JSON</a>。</p></div></div></section>''')
    style='''body{margin:0;background:#102131;color:#e7edf2;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1440px;margin:auto;padding:32px}header{padding:26px 34px;border-bottom:2px solid #36c3b8;background:#172e44;border-radius:14px}h1{font-size:34px;margin:0}h2{font-size:24px}h3{font-size:18px}.notice{color:#ffcf75}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:24px 0}.stats div,.sample,.details{background:#193247;border:1px solid #2d4d62;border-radius:12px;padding:20px}.stats b{font-size:30px;display:block;color:#62e7d3}.sample{margin:22px 0}.sample-head{display:flex;align-items:center;justify-content:space-between}.sample-grid{display:grid;grid-template-columns:1.5fr 1fr;gap:24px}.sample img{width:100%;border-radius:8px}.pass,.fail{border-radius:8px;padding:6px 25px;font-weight:bold}.pass{background:#126b4e;color:#b8ffdf}.fail{background:#8a3341;color:#ffccd3}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #36566b;text-align:left}a{color:#76e0d6}code{color:#ffcf75}footer{margin:30px 0;color:#b8c8d3}@media(max-width:900px){main{padding:16px}.sample-grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}}'''
    target=summary['robot_plan']['target_xy_mm']
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>机器视觉备赛 离线演示</title><style>{style}</style><main><header><p>VISIONPREP / OFFLINE TRAINING</p><h1>视觉引导与 PCB 检测</h1><p class="notice">离线合成样例 · 软件实际计算结果 · 未连接实物设备</p><p>图像检测、二维标定、通信报文与结果保存的可复现训练程序</p></header><div class="stats"><div><b>{summary['samples']}</b>合成样例</div><div><b>{summary['passed_samples']}</b>合格样例结果</div><div><b>{summary['ng_samples']}</b>缺陷样例结果</div><div><b>9</b>合成标定点</div></div><div class="details"><h2>示教与数据记录</h2><p>二维映射后的演示坐标：X={target[0]:.3f} mm，Y={target[1]:.3f} mm。运动字符串：<code>{summary['robot_plan']['command']}</code>；仅生成字符串，未发送。</p><p>结果写入 <a href="results.synthetic.csv">CSV</a>、各样例 JSON、原图/结果图与 <a href="user-log.jsonl">用户日志</a>。<a href="summary.synthetic.json">查看完整计算摘要</a>。</p><p>界面数据全部来自本次程序执行；样本及九点坐标为明确标注的合成训练输入，不表示真实硬件测试或量测精度。</p></div>{''.join(cards)}<footer>传统 ROI 方法：灰度方差、电容 HSV 颜色比例、芯片暗像素比例。当前阈值服务于固定位置的合成训练样例；实际样本需重新定位与独立验证。</footer></main></html>'''
