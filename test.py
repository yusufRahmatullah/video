from itertools import product
import json
import math
import re

import numpy as np

from PIL import Image

colors = [
    (0, 0, 0),  # black
    (0, 0, 170),  # blue
    (0, 170, 0),  # green
    (0, 170, 170),  # cyan
    (170, 0, 0),  # red
    (170, 0, 170),  # magenta
    (170, 85, 0),  # brown
    (170, 170, 170),  # light grey
    (85, 85, 85),  # dark grey
    (85, 85, 255),  # light blue
    (85, 255, 85),  # light green
    (85, 255, 255),  # light cyan
    (255, 85, 85),  # light red
    (255, 85, 255),  # light magenta / pink
    (255, 255, 85),  # yellow
    (255, 255, 255),  # white
]

mt_colors = [
    (170,   0,   0), (  0,   0, 170), (  0, 170, 170),
    (170, 170, 170), (255,  85, 170), (  0,   0,   0),
    (170,  85,   0), (  0, 170,   0), (255, 255, 255),
    (255,  85,   0), ( 85,   0, 170), (255, 255,   0),
    (170,   0, 170), ( 85,  85,  85), (  0,  85,   0)
]

mt_names = [
    'red', 'blue', 'cyan',
    'grey', 'pink', 'black',
    'brown', 'green', 'white',
    'orange', 'white', 'yellow',
    'magenta', 'dark_grey', 'dark_green'
]

color_names = [
    'black', 'blue', 'green', 'cyan', 'red', 'magenta', 'brown', 'light grey',
    'dark grey', 'light blue', 'light green', 'light cyan', 'light red',
    'light magenta (pink)', 'yellow', 'white'
]

def calculate_distance(a, b):
    x1, y1, z1 = a
    x2, y2, z2 = b

    return math.sqrt(
        (x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2
    )


def calculate_distance_e2(a, b):
    x1, y1, z1 = a
    x2, y2, z2 = b

    return (x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2


def calculate_m_distance(a, b):
    x1, y1, z1 = a
    x2, y2, z2 = b

    return abs(x2 - x1) + abs(y2 - y1) + abs(z2 - z1)


def get_closest_color(color):
    m = 300
    mi = 0
    for i, c in enumerate(colors):
        d = calculate_distance(c, color)
        if d < m:
            m = d
            mi = i
    return colors[mi]


def get_closest_color_m(color):
    m = 300
    mi = 0
    for i, c in enumerate(colors):
        d = calculate_m_distance(c, color)
        if d < m:
            m = d
            mi = i
    return colors[mi]


def get_closest_color_e2(color):
    m = 300
    mi = 0
    for i, c in enumerate(colors):
        d = calculate_distance_e2(c, color)
        if d < m:
            m = d
            mi = i
    return colors[mi]


def convert_image(img):
    cimg = img.copy()
    pm = cimg.load()
    for i in range(cimg.size[0]):
        for j in range(cimg.size[1]):
            c = pm[i, j]
            nc = get_closest_color(c)
            pm[i, j] = nc
    return cimg

# ~2s
def convert_image_m(img):
    cimg = img.copy()
    pm = cimg.load()
    for i in range(cimg.size[0]):
        for j in range(cimg.size[1]):
            c = pm[i, j]
            nc = get_closest_color_m(c)
            pm[i, j] = nc
    return cimg

# ~7s
def convert_image_e2(img):
    cimg = img.copy()
    pm = cimg.load()
    for i in range(cimg.size[0]):
        for j in range(cimg.size[1]):
            c = pm[i, j]
            nc = get_closest_color_e2(c)
            pm[i, j] = nc
    return cimg


cnp = np.asarray(colors, dtype='uint8')
pos = [0, 85, 170, 255]
ucolor = np.asarray(list(product(pos, pos, pos)))
um = np.zeros((64, 16), dtype='uint8')
for i, color in enumerate(colors):
    um[:, i] = np.abs(ucolor - color).sum(axis=1)
uidx = um.argmin(axis=1)
mcolor = cnp[uidx]

# ~0.165 s
def convert_image_np(img):
    nimg = np.array(img)
    h, w, _ = nimg.shape
    cim = np.zeros((h, w, 16), dtype='uint16')
    for i, color in enumerate(colors):
        cim[:,:,i] = np.abs(nimg - color).sum(axis=2)
    idx = cim.argmin(axis=2)
    res = cnp[idx]
    return Image.fromarray(res)


# ~0.02 s, color not mapped correctly
def convert_image_np_s(img, ret=''):
    nimg = np.array(img)
    res = nimg.copy()
    b = nimg // 43
    res[b == 0] = 0
    res[(b == 1) | (b == 2)] = 85
    res[(b == 3) | (b == 4)] = 170
    res[b == 5] = 255
    if ret == 'numpy':
        return res        
    else:
        return Image.fromarray(res)


def scale_img(img, scale):
    w, h = img.size
    ws, hs = int(w / scale), int(h / scale)
    return img.resize((ws, hs))


def mt_get_closest_color(color):
    m = 300
    mi = 0
    for i, c in enumerate(mt_colors):
        d = calculate_m_distance(c, color)
        if d < m:
            m = d
            mi = i
    return mt_colors[mi]


# ~2.98 s (spectrum)
def mt_convert_image(img):
    cimg = img.copy()
    pm = cimg.load()
    for i in range(cimg.size[0]):
        for j in range(cimg.size[1]):
            c = pm[i, j]
            nc = mt_get_closest_color(c)
            pm[i, j] = nc    
    return cimg


def mt_convert_image_png(img):
    if img.mode != 'RGBA':
        raise Exception(f'Not in RGBA format. mode: {img.mode}')
    cimg = img.copy()
    pm = cimg.load()
    for i in range(cimg.size[0]):
        for j in range(cimg.size[1]):
            c = pm[i, j]
            a = c[-1]
            c = c[:3]
            nc = mt_get_closest_color(c)
            pm[i, j] = nc + (a,)
    return cimg


def mt_get_name(color):
    idx = mt_colors.index(color)
    cn = mt_names[idx]
    return f'["name"] = "wool:{cn}"'


mt_meta = '["meta"] = {["fields"] = {}, ["inventory"] = {}}'
mt_z = '["z"] = 0'


def mt_v(k, i):
    return f'["{k}"] = {i}'


def mt_to_we(img, ver=5):
    body = []
    pm = img.load()
    w, h = img.size
    for i in range(w):
        for j in range(h-1, 0, -1):
            c = pm[i, j]
            x = mt_v('x', i)
            y = mt_v('y', h - 1 - j)
            name = mt_get_name(c)
            body.append(f'{{{x}, {mt_meta}, {y}, {mt_z}, {name}}}')
    body = ', '.join(body)
    return f'{ver}:return {{{body}}}'


def mt_to_we_png(img, ver=5):
    if img.mode != 'RGBA':
        raise Exception(f'Not in RGBA format. mode: {img.mode}')
    body = []
    pm = img.load()
    w, h = img.size
    for i in range(w):
        for j in range(h-1, 0, -1):
            c = pm[i, j]
            a  = c[-1]
            if a <= 128:
                continue
            c = c[:3]
            x = mt_v('x', i)
            y = mt_v('y', h - 1 - j)
            name = mt_get_name(c)
            body.append(f'{{{x}, {mt_meta}, {y}, {mt_z}, {name}}}')
    body = ', '.join(body)
    return f'{ver}:return {{{body}}}'


pat_d = re.compile(r'\d+')
pat_name = re.compile(r'"[\w:_]+"')


def mt_process_chunk(chunk):
    x, y, z = 0, 0, 0
    name = ''
    for line in chunk:
        if '"x"' in line:
            cand = pat_d.findall(line)
            x = int(cand[0])
        elif '"y"' in line:
            cand = pat_d.findall(line)
            y = int(cand[0])
        elif '"z"' in line:
            cand = pat_d.findall(line)
            z = int(cand[0])
        elif '"name"' in line:
            cand = pat_name.findall(line)
            name = cand[1].strip('"')
    return {'x': x, 'y': y, 'z': z, 'name': name}



def mt_we_to_json(we):
    res = []
    sep_idx = we.index(':')
    ver = we[:sep_idx]
    body = we[sep_idx + 7:].strip()
    inside_body = body[1:-1]
    lines = inside_body.split(', ')
    for i in range(0, len(lines), 6):
        chunk = lines[i : i+6]
        data = mt_process_chunk(chunk)
        res.append(data)
    return res


def mt_prettify_we(we):
    res = []
    for i, c in enumerate(we):
        if c == '{':
            if we[i+1] == '}':
                res.append(c)
                continue
            else:
                res.append(c)
                res.append('\n')
        elif c == '}':
            if we[i-1] == '{':
                res.append(c)
                continue
            else:
                res.append('\n')
                res.append(c)
        elif c == ',':
            res.append(c)
            res.append('\n')
        else:
            res.append(c)
    print(''.join(res))


reg_lexs = {
    'int': re.compile(r'\d+'),
    'key': re.compile(r'\["([A-Za-z0-9_]+)"\]'),
    'value': re.compile(r'"([A-Za-z0-9_:]+)"'),
    'symbols': re.compile(r'[\{\}\"\:\=\,]')
}


def mt_tokenize_we(we):
    words = we.split()
    res = []
    while words:
        word = words.pop(0)
        for k, p in reg_lexs.items():
            m = p.match(word)
            if m:
                e = m.end()
                if e < len(word):
                    words.insert(0, word[e:])
                v = m.group(1) if k in ['key', 'value'] else m.group()
                if k == 'int':
                    v = int(v)
                res.append(v)
                break
    return res




















def gen_neighbor(x, y):
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            yield x+i, y+j


def mt_vote_neighbor(img):
    cimg = img.copy()
    pm = cimg.load()
    for i in range(1, cimg.size[0] - 1):
        for j in range(1, cimg.size[1] - 1):
            oc = pm[i, j]
            candidate = {}
            for x, y in gen_neighbor(i, j):
                c = pm[x, y]
                if c in candidate:
                    candidate[c] += 1
                else:
                    candidate[c] = 1
            k, v = max(candidate.items(), key=lambda x: x[1])
            if candidate[oc] == 1:  # alone
                pm[i, j] = k
    return cimg
