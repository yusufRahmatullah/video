# from https://stackoverflow.com/a/15278868/13889280
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb
import numpy as np
from PIL import Image
import pickle as pk


col2nk = pk.load(open('col2nk_m.pk', 'rb'))
cmap = pk.load(open('cmap.pk', 'rb'))
x2xs = pk.load(open('x2xs.pk', 'rb'))

def img_to_hsv(img):
    # default h range is 0 - 1
    # default s range is 0 - 1
    # edfault v range is 0 - 255
    nimg = rgb_to_hsv(img)
    nimg[:,:,0] = np.round(nimg[:,:,0] * 24)  # force h to round 0-23
    nimg[:,:,1] = np.round(nimg[:,:,1] * 4)  # force s to round 0-4
    nimg[:,:,2] = np.round(nimg[:,:,2] * 15/255) # force v to round 0-15
    return nimg


def get_closest_hsv(color):
    h, s, v = color
    if h == 0 and s == 0:  # white - black
        return 255 - v
    elif v == 15:
        return h + s * 24  # first 5 period
    elif s <= 3:  # range v is shallower than s
        if v >= 11:
            return h + 5 * 24  # 6th period
        elif v > 4:
            return h + 7 * 24  # 8th period
        else:
            return h + 9 * 24  # 10th period
    elif s > 3:
        if v >= 8:  # half top
            return h + 6 * 24  # 7th period
        else:
            return h + 8 * 24  # 9th period
    else:  # default value, return full color (5th period)
        return h + 4 * 24


p_to_s = {
    1: 0.25, 2: 0.40, 3: 0.49, 4: 0.80, 5: 1.00,
    6: 0.66, 7: 1.00, 8: 0.66, 9: 1.00, 10: 0.67
}
p_to_v = {
    1: 255, 2: 255, 3: 255, 4: 255, 5: 255,
    6: 191, 7: 166, 8: 125, 9: 84.2, 10: 63.8
}
cid_to_v = {
    255: 0, 254: 17, 253: 34, 252: 51, 251: 68, 250: 85,
    249: 102, 248: 119, 247: 136, 246: 153, 245: 170,
    244: 187, 243: 204, 242: 221, 241: 238, 240: 255
}


def get_hsv_from_color_id(color_id):
    # imediate return if color_id in white-black
    if color_id >= 240:
        return 0, 0, cid_to_v[color_id]
    # default h range is 0 - 1
    # default s range is 0 - 1
    # edfault v range is 0 - 255
    h = color_id % 24
    h = h * 15 / 360

    period = int(color_id // 24) + 1
    s = p_to_s[period]
    v = p_to_v[period]

    return h, s, v


def hsv_to_img(himg):
    hsv = np.zeros(himg.shape, dtype=himg.dtype)
    for i, x in enumerate(himg):
        for j, y in enumerate(x):
            cid = get_closest_hsv(y)
            cc = get_hsv_from_color_id(cid)
            hsv[i,j] = cc
    nimg = hsv_to_rgb(hsv)
    return Image.fromarray(nimg.astype('uint8'))


def img_to_nk(img):
    dimg = img.copy()
    im = img.load()
    dm = dimg.load()
    w, h = img.size
    for i in range(w):
        for j in range(h):
            r, g, b = im[i, j]
            dr = x2xs[r]
            dg = x2xs[g]
            db = x2xs[b]
            dm[i, j] = col2nk[(dr, dg, db)]
    return dimg


meta = '["meta"] = {["fields"] = {}, ["inventory"] = {}}'
name = '["name"] = "unifiedbricks:clayblock"'
z = '["z"] = 0'


def x2v(k, i):
    return f'["{k}"] = {i}'


def xp2(i):
    return f'["param2"] = {i}'


def img_to_we(img, ver=5):
    body = []
    dimg = img_to_nk(img)
    im = dimg.load()
    w, h = dimg.size
    for i in range(w):
        for j in range(h-1, -1, -1):
            r, g, b = im[i, j]
            cid = cmap[(r, g, b)]
            x = x2v('x', i)
            y = x2v('y', h - 1 - j)
            p2 = xp2(cid)
            body.append(f'{{{x}, {meta}, {p2}, {y}, {z}, {name}}}')
    body = ', '.join(body)
    return f'{ver}:return {{{body}}}'


def img_to_we_struct(img, ver=5):
    body = []
    dimg = img_to_nk(img)
    im = dimg.load()
    w, h = dimg.size
    for i in range(w):
        for j in range(h-1, -1, -1):
            r, g, b = im[i, j]
            cid = cmap[(r, g, b)]
            body.append({
                'x': i, 'y': h - 1 - j, 'z': 0, 'param2': cid,
                'name': 'unifiedbricks:clayblock',
                'meta': {'field': {}, 'inventory': {}}
            })
    return body
