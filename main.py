import argparse
import os
import time
from datetime import datetime

import cv2 as cv
from pipeline import (
    ContourPipeline,
    CountourSavePipeline,
    FgMaskPipeline,
    FpsPipeline,
    GrayPipeline,
    PipelineExecutor,
    SobelPipeline
)

VERSION = '0.1.0'


def capture_video(capture, executor: PipelineExecutor) -> bool:
    try:
        ret, frame = capture.read()
        if not ret or frame is None:
            return False
        executor.execute(frame)
        keyboard = cv.waitKey(1) & 0xFF
        if keyboard == ord('q') or keyboard == 27:
            return False
    except KeyboardInterrupt:
        return False
    return True


def prepare_folder():
    if not os.path.exists('captures'):
        os.mkdir('captures')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help="Show frame from each pipelines includes main frame"
    )
    parser.add_argument(
        '-r', '--save-raw', action='store_true',
        help='Save captured frame as npy'
    )
    parser.add_argument(
        '-t', '--throttle', default=3,
        help='Throttle for save captured frames in seconds'
    )
    parser.add_argument(
        '-v', '--version', action='store_true',
        help='Show app version'
    )
    args = parser.parse_args()
    print(f'Version {VERSION}')
    # quit(0)
    return args


def main():
    prepare_folder()
    args = parse_args()

    capture = cv.VideoCapture(0)
    if not capture.isOpened:
        print('Unable to open camera')
        exit(0)
    executor = PipelineExecutor([
        GrayPipeline(out=True),
        FgMaskPipeline(out=True),
        SobelPipeline(out=True),
        ContourPipeline(out=True),
        CountourSavePipeline(
            throttle=int(args.throttle),
            save_raw=args.save_raw),
        FpsPipeline(capture)
    ], debug=bool(args.debug))
    ok = True
    while ok:
        ok = capture_video(capture, executor)
    capture.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
