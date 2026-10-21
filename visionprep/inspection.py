"""Traditional ROI inspection for registered, fixed-position training images."""
from PIL import Image, ImageDraw
import numpy as np

def region(image, box):
    if len(box) != 4 or any(isinstance(x,bool) or not isinstance(x,int) for x in box):
        raise ValueError('ROI must contain four integers')
    x0,y0,x1,y1 = box
    if not 0 <= x0 < x1 <= image.width or not 0 <= y0 < y1 <= image.height:
        raise ValueError('ROI is empty or outside the image')
    return image.crop(tuple(box))

def colour_fraction(image, target):
    hsv = np.asarray(image.convert('HSV'))
    h,s,v = [hsv[:,:,i] for i in range(3)]
    saturated = (s >= 100) & (v >= 80)
    if target == 'orange':mask = (h >= 10) & (h <= 35)
    elif target == 'green':mask = (h >= 60) & (h <= 115)
    elif target == 'red':mask = (h <= 12) | (h >= 245)
    else:raise ValueError('Unsupported colour')
    return float(np.mean(mask & saturated))

def inspect(image, config):
    image = image.convert('RGB')
    if list(image.size) != config['image_size']:
        raise ValueError('Image resolution differs from the ROI configuration; register/reconfigure it first')
    results = []
    for item in config['components']:
        roi = region(image, item['box'])
        gray = np.asarray(roi.convert('L'), dtype=float)
        metrics = {'gray_mean':float(gray.mean()),'gray_variance':float(gray.var())}
        kind = item['kind']
        if kind == 'resistor':
            passed = item['variance_min'] <= metrics['gray_variance'] <= item['variance_max']
        elif kind == 'capacitor':
            metrics['orange_fraction'] = colour_fraction(roi,'orange')
            metrics['green_fraction'] = colour_fraction(roi,'green')
            passed = metrics['orange_fraction'] >= item['orange_min']
        elif kind == 'chip':
            metrics['dark_fraction'] = float(np.mean(gray < item['dark_threshold']))
            passed = metrics['dark_fraction'] >= item['dark_min']
        else:raise ValueError('Unknown component kind')
        results.append({'id':item['id'],'kind':kind,'box':item['box'],'passed':bool(passed),'metrics':metrics})
    if not results:
        raise ValueError('No component inspections configured')
    return {'passed':all(r['passed'] for r in results),'components':results,
            'method':'fixed registered ROIs: gray variance, HSV colour fraction and dark-pixel fraction',
            'scope':'training reference, thresholds require validation on independent real images'}

def draw_record(image, report):
    result = image.convert('RGB').copy()
    draw = ImageDraw.Draw(result)
    for row in report['components']:
        colour = '#21da8c' if row['passed'] else '#ff5364'
        draw.rectangle(tuple(row['box']),outline=colour,width=4)
        draw.text((row['box'][0],row['box'][1]-15),row['id']+(' OK' if row['passed'] else ' NG'),fill=colour)
    return result
