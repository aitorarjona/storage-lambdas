import logging
import time
import os
import io
import subprocess

import laspy
import numpy as np

from module_handler.handler import ModuleHandler

logger = logging.getLogger(__name__)


def tiled_partition(context, parts):
    context.do_get()
    buff = io.BytesIO()
    buff.write(context.input_stream.read(1024))
    buff.seek(0)

    parts = int(parts)

    las_input = laspy.lasreader.LasReader(source=buff)
    x_min, y_min = las_input.header.x_min, las_input.header.y_min
    x_max, y_max = las_input.header.x_max, las_input.header.y_max

    x_size = (x_max - x_min) / parts
    y_size = (y_max - y_min) / parts

    sub_bounds = []
    for i in range(parts):
        for j in range(parts):
            x_min_bound = (x_size * i) + x_min
            y_min_bound = (y_size * j) + y_min
            x_max_bound = x_min_bound + x_size
            y_max_bound = y_min_bound + y_size
            sub_bounds.append((x_min_bound, y_min_bound, x_max_bound, y_max_bound))

    procs = []
    for min_X, min_Y, max_X, max_Y in sub_bounds:
        p = subprocess.Popen(

            f"bin/las2las -verbose -stdin -stdout -olas -inside {min_X} {min_Y} {max_X} {max_Y}",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
        )
        p.stdin.write(buff.getvalue())
        procs.append(p)

    chunk = p.stdin.write(context.input_stream.read(65536))
    while chunk != b"":
        for p in procs:
            p.stdin.write(chunk)

        for out, p in zip(context.output_streams, procs):
            res = p.stdout.read(65536)
            out.write(res)


def _tiled_partition(context, parts):
    logger.debug(f'--- start tiled_partition ---')
    t0 = time.perf_counter()

    parts = int(parts)

    context.do_get()
    buff = io.BytesIO()
    buff.write(context.input_stream.read(1024))
    buff.seek(0)

    laspy.LasHeader.read_from()

    laspy.LasData.points.

    las_input = laspy.lasreader.LasReader(source=buff)
    x_min, y_min = las_input.header.x_min, las_input.header.y_min
    x_max, y_max = las_input.header.x_max, las_input.header.y_max

    x_size = (x_max - x_min) / parts
    y_size = (y_max - y_min) / parts

    sub_bounds = []
    for i in range(parts):
        for j in range(parts):
            x_min_bound = (x_size * i) + x_min
            y_min_bound = (y_size * j) + y_min
            x_max_bound = x_min_bound + x_size
            y_max_bound = y_min_bound + y_size
            sub_bounds.append((x_min_bound, y_min_bound, x_max_bound, y_max_bound))

    output_writers = [laspy.laswriter.LasWriter(dest=stream, header=las_input.header)
                      for stream in context.output_streams]
    print(sub_bounds)

    try:
        count = 0
        for points in las_input.chunk_iterator(1_000_000):
            x, y = points.x.copy(), points.y.copy()
            point_piped = 0

            for i, (x_min, y_min, x_max, y_max) in enumerate(sub_bounds):
                mask = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)

                if np.any(mask):
                    sub_points = points[mask]
                    print('writing points')
                    output_writers[i].write_points(sub_points)

                point_piped += np.sum(mask)
                if point_piped == len(points):
                    break
            count += len(points)
            print(f"{count / las_input.header.point_count * 100}%")
    finally:
        for writer in context.output_streams:
            writer.close()
        las_input.close()

    t1 = time.perf_counter()
    logger.debug(f'--- end tiled_partition --- (took {t1 - t0} s)')


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', logging.INFO))
    logging.getLogger('botocore').setLevel(logging.CRITICAL)

    target = os.environ.get('TARGET', '127.0.0.1:8000')
    logging.info('Listening on %s', target)
    host, port = target.split(':')

    lidar_handler = ModuleHandler(host=host, port=int(port))

    # lidar_handler.stateless_action('extract_meta', extract_meta)
    # lidar_handler.stateless_action('las2laz', las2laz)
    # lidar_handler.stateless_action('filter_inside_XY', filter_inside_XY)

    lidar_handler.stateful_action('tiled_partition', action_callable=tiled_partition,
                                  calc_parts_callable=lambda _, parts: int(parts))

    try:
        lidar_handler.serve()
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt')
        lidar_handler.stop()
