"""Deterministic synthetic images. These are not photographs or field evidence."""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np

CASES = ['ok','missing_resistor','missing_capacitor','wrong_capacitor_colour','missing_chip','multiple_defects']

def default_rois():
    return {'image_size':[960,640],'coordinate_system':'fixed synthetic fixture, pixels',
            'components':[
                *[{'id':'R'+str(i+1),'kind':'resistor','box':[160,180+i*100,240,220+i*100], 'variance_min':1000,'variance_max':16000} for i in range(3)],
                {'id':'C1','kind':'capacitor','box':[330,180,390,240],'orange_min':0.35},
                {'id':'C2','kind':'capacitor','box':[330,360,390,420],'orange_min':0.35},
                {'id':'U1','kind':'chip','box':[500,220,660,360],'dark_threshold':60,'dark_min':0.6}]}

def make_sample(case='ok', seed=2026):
    if case not in CASES:raise ValueError('Unknown synthetic case')
    image = Image.new('RGB',(960,640),'#152437');draw=ImageDraw.Draw(image)
    font=ImageFont.load_default(size=20)
    draw.text((26,18),'SYNTHETIC TRAINING SAMPLE - NOT HARDWARE EVIDENCE',font=font,fill='#f7bd52')
    draw.rounded_rectangle((80,90,880,550),radius=22,fill=(28,115,67),outline='#d1b64e',width=3)
    for x,y in [(105,115),(855,115),(105,525),(855,525)]:draw.ellipse((x-9,y-9,x+9,y+9),fill='#d0c890')
    for y in [200,300,400]:draw.line((110,y,800,y),fill='#a2b74d',width=3)
    for i in range(3):
        if i==1 and case in ['missing_resistor','multiple_defects']:continue
        y=180+i*100;draw.rectangle((160,y,239,y+39),fill='#333943')
        for x in [168,183,216,230]:draw.rectangle((x,y,x+5,y+39),fill='#d9cfb2')
    for i,(x,y) in enumerate([(330,180),(330,360)]):
        if i==0 and case in ['missing_capacitor','multiple_defects']:continue
        colour='#176bdf' if i==1 and case=='wrong_capacitor_colour' else '#ef892b'
        draw.ellipse((x+2,y+2,x+57,y+57),fill=colour,outline='#ffd4a4',width=2)
    if case not in ['missing_chip','multiple_defects']:
        draw.rectangle((500,220,659,359),fill='#202127',outline='#a4a8ab',width=3)
        draw.text((542,275),'U1',fill='#c8cdd2')
        for y in range(230,350,12):
            draw.line((480,y,500,y),fill='#c6bd9c',width=4);draw.line((660,y,680,y),fill='#c6bd9c',width=4)
    draw.text((120,475),'PCB TRAINING FIXTURE / '+case,font=font,fill='#cce8d4')
    arr=np.asarray(image,dtype=np.int16)
    noise=np.random.default_rng(seed).integers(-2,3,arr.shape,dtype=np.int16)
    return Image.fromarray(np.clip(arr+noise,0,255).astype('uint8'))

def calibration_example():
    pixels=[[x,y] for y in [160,320,480] for x in [200,480,760]]
    robot=[[0.05*x+180,-0.05*y+150] for x,y in pixels]
    return {'is_synthetic':True,'purpose':'planar nine-point fit exercise; not measured robot calibration',
            'pixels':pixels,'robot_xy_mm':robot,'example_workspace_limits':[[0,400],[0,300],[0,200],[-180,180]]}
