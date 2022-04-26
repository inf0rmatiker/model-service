#!/bin/python3

import argparse
from datetime import datetime


def process_file(input_file, nmon_metrics):
    # print(f"nmon_metrics={nmon_metrics}")

    metric_indices = {}
    header = 'timestamp'
    out_line = ''
    for line in input_file:
        line = line.rstrip()  # remove trailing newline character
        line_array = line.split(",")

        if line.startswith('ZZZZ,'):
            # if 'out_line' is set -> processing metric reports
            if out_line:
                print(out_line)
            else:
                print(header)

            # parse timestamp and add to out_line
            utc_time = datetime.strptime(line_array[3] + "T" + line_array[2], "%d-%b-%YT%H:%M:%S")
            epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
            out_line = str(int(epoch_time))
        elif out_line == '':
            # before first metric report
            if line_array[0] in nmon_metrics:
                # if metric device is captured -> parse metric field indices
                indices = []
                metric_indices[line_array[0]] = indices

                for field_name in nmon_metrics[line_array[0]]:
                    for i, j in enumerate(line_array):
                        if field_name == j:
                            indices.append(i)

                            # append metric field to header
                            header += ',' + line_array[0] + ':' + field_name
        else:
            # process metric report
            if line_array[0] in metric_indices:
                for index in metric_indices[line_array[0]]:
                    out_line += "," + line_array[index]


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='FILE', help='input file.')
    parser.add_argument('-m', '--metrics', action='append',
                        help='nmon report device metric (ex. "DISKREAD:sdd", "MEM:active", "NET:eno1-write-KB/s").')
    args = parser.parse_args()

    # parse metrics -> from list (ex. [ 'CPU:User%', 'CPU:Wait' ])
    # to map (ex. { 'CPU' -> [ 'User%', 'Wait%' ] })
    metrics_map = {}
    for metric in args.metrics[0].split():
        # print(f"metric={metric}")
        metric_values = metric
        array = metric.split(':')

        if array[0] in metrics_map:
            metrics_map[array[0]].append(array[1])
        else:
            metrics_map[array[0]] = [array[1]]

    # open input and output files
    in_file = open(args.file, 'r')

    try:
        # process file
        process_file(in_file, metrics_map)
    finally:
        # close input and output files
        if in_file:
            in_file.close()