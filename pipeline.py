import os
import time
from datetime import datetime
from typing import List

import cv2 as cv
import numpy as np


class Pipeline:
    def __init__(self, out: bool = False, name: str = '',
                 requires: List[str] = [], provides: List[str] = []):
        self.out = out
        self.name = name
        self.frame = None
        if requires:
            self._requires = requires
        else:
            self._requires = []
        if provides:
            self._provides = provides
        else:
            self._provides = provides

    def process(self, key: str, frame) -> dict:
        return {'main': frame}

    @property
    def requires(self) -> List[str]:
        if self._requires:
            return self._requires
        return ['main']

    @property
    def provides(self) -> List[str]:
        if self._provides:
            return self._provides
        return ['main']


class PipelineExecutor:
    def __init__(self, pipelines: List[Pipeline], debug: bool = False):
        self.pipelines = pipelines
        self._validate()
        self._mapping = {}
        self.debug = debug

    def execute(self, main_frame):
        self._mapping['main'] = main_frame
        for pl in self.pipelines:
            for req in pl.requires:
                iframe = self._mapping[req]
                oframes = pl.process(req, iframe)
                for k, v in oframes.items():
                    self._mapping[k] = v
        self._draw()

    def _draw(self):
        for pl in self.pipelines:
            if self.debug and pl.out:
                for p in pl.provides:
                    cv.imshow(p, self._mapping[p])
        if self.debug:
            cv.imshow('main', self._mapping['main'])

    def _validate(self) -> bool:
        reqs = set(['main'])
        for p in self.pipelines:
            for r in p.requires:
                if r not in reqs:
                    return False
            for r in p.provides:
                reqs.add(r)
        return True


class ContourPipeline(Pipeline):
    def __init__(self, out: bool = False,
                 name: str = 'Contour'):
        super().__init__(
            out=out, name=name, requires=['fgmask', 'main'],
            provides=['contours']
        )
        self.contours = []

    def process(self, key: str, frame) -> dict:
        if key == 'fgmask':
            cnts, h = cv.findContours(
                frame.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
            )
            self.contours = []
            for c in cnts:
                if cv.contourArea(c) < 1000:
                    continue
                self.contours.append(c)
            return {}
        elif key == 'main':
            return {
                'contours': self._process_main_frame(frame)
            }

    def _process_main_frame(self, frame):
        myframe = frame.copy()
        for c in self.contours:
            x, y, w, h = cv.boundingRect(c)
            cv.rectangle(myframe, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return myframe


class CountourSavePipeline(Pipeline):
    def __init__(self, out: bool = False,
                 name: str = 'contour-save', throttle: int = 3,
                 save_raw: bool = False):
        super().__init__(
            out=out, name=name, requires=['contours', 'main'], provides=[]
        )
        self.throttle = throttle
        self.save_raw = save_raw
        self._flag = False

    def process(self, key: str, frame) -> dict:
        if key == 'contours':
            now = int(time.time())
            nc = now - self.throttle + 1
            for t in range(nc, now):
                dt = datetime.fromtimestamp(t)
                if self.save_raw:
                    fpath = os.path.join('captures', f'{str(dt)}.npy')
                else:
                    fpath = os.path.join('captures', f'{str(dt)}.jpg')
                if os.path.exists(fpath):
                    return {}
            self._dt = datetime.fromtimestamp(now)
            self._flag = True
        elif key == 'main' and self._flag:
            if self.save_raw:
                fpath = os.path.join('captures', f'{str(self._dt)}.npy')
                np.save(fpath, frame)
            else:
                fpath = os.path.join('captures', f'{str(self._dt)}.jpg')
                cv.imwrite(fpath, frame)
            self._flag = False
        return {}


class FgMaskPipeline(Pipeline):
    def __init__(self, out: bool = False, name: str = 'FgMask'):
        super().__init__(
            out=out, name=name, requires=['gray'], provides=['fgmask']
        )
        self.backSub = cv.createBackgroundSubtractorMOG2()

    def process(self, key: str, frame) -> dict:
        if key != 'gray':
            return {}
        mask = self.backSub.apply(frame)
        return {
            'fgmask': mask
        }


class FpsPipeline(Pipeline):
    def __init__(self, capture, out: bool = False, name: str = 'fps'):
        super().__init__(
            out=out, name=name, requires=['main'], provides=['main']
        )
        self.capture = capture

    def process(self, key: str, frame) -> dict:
        if key != 'main':
            return {}
        cv.rectangle(frame, (10, 2), (100, 20), (255, 255, 255), -1)
        cv.putText(
            frame, str(self.capture.get(cv.CAP_PROP_FPS)), (15, 15),
            cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0)
        )
        return {
            'main': frame
        }


class GrayPipeline(Pipeline):
    def __init__(self, out: bool = False, name: str = 'Gray'):
        super().__init__(
            out=out, name=name, requires=['main'], provides=['gray']
        )

    def process(self, key: str, frame):
        if key != 'main':
            return {}
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (21, 21), 0)
        return {
            'gray': gray
        }
