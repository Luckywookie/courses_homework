#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import sys
import gzip
import json
import logging
import argparse
from time import time
from pprint import pprint
from collections import defaultdict
from string import Template
from datetime import datetime


logger = logging.getLogger('Log Analyzer')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s')


def write_log(log_level=30, msg=''):
    logger.log(level=log_level, msg=msg)


def median(numbers):
    return (sorted(numbers)[int(round((len(numbers) - 1) / 2.0))] + sorted(numbers)[int(round((len(numbers) - 1) // 2.0))]) / 2.0


def read_config(path_to_config=None):
    with open(path_to_config, 'r') as f:
        data = json.load(f)
    size_report = data.get('REPORT_SIZE', None)
    report_dir = data.get('REPORT_DIR', None)
    log_dir = data.get('LOG_DIR', None)
    ts_path = data.get('TS_PATH', None)
    logger_path_conf = data.get('LOGGER_PATH', None)
    return size_report, report_dir, log_dir, ts_path, logger_path_conf


def find_last_log(path_logs):
    pattern_log_name = re.compile(r"nginx-access-ui\.log-(?P<log_date>\d{8})(?P<type_file>.*)")
    date_list = []
    for file_item in os.listdir(path_logs):
        find_files = pattern_log_name.search(file_item)
        if find_files:
            datadict = find_files.groupdict()
            log_date = datadict["log_date"]
            type_file = datadict["type_file"]
            this_date = datetime.strptime(log_date, '%Y%m%d')
            filename_log = 'nginx-access-ui.log-{}{}'.format(log_date, type_file)
            date_list.append(this_date)
            write_log(log_level=20,
                      msg='Max date config {}, nginx log filename: {}'.format(max(date_list), filename_log))
            return max(date_list), filename_log


def find_report_by_day(path_reports, log_day):
    return os.path.exists(path_reports + '/report_{day}.html'.format(day=log_day.strftime("%Y-%m-%d")))


def parse_logs(log_file, req_time_more):
    pattern_log = re.compile(
        '(?:.+) \[(?:.+)\] "(?:.+) (?P<url>.+) HTTP/\d.\d".+(?P<time_req>\d+\.\d+)')
    lines = []
    for line in log_file:
        findes = pattern_log.search(line)
        if findes:
            datadict = findes.groupdict()
            url = datadict["url"]
            time_req = datadict["time_req"]
            if float(time_req) > req_time_more:
                lines.append((url, float(time_req)))
    write_log(log_level=20, msg='Len of list parsed urls: {}'.format(len(lines)))
    return lines


def open_logs(filename='', req_time_more=0.0):
    if filename.endswith(".gz"):
        with gzip.open(filename, 'r') as log_file:
            parsed_list = parse_logs(log_file, req_time_more)
    else:
        with open(filename, 'r') as log_file:
            parsed_list = parse_logs(log_file, req_time_more)
    return parsed_list


def group_by_url(list_to_sort):
    new_count_urls = defaultdict(list)
    for this_url, url_time in list_to_sort:
        new_count_urls[this_url].append(url_time)
    write_log(log_level=20, msg='dicts len: {}'.format(len(new_count_urls.keys())))
    return new_count_urls


def log_statistic(list_of_lines, count_size_report=1000):
    all_count = sum(len(i) for i in list_of_lines.values())
    write_log(log_level=20, msg='all count urls: {}'.format(all_count))
    all_time_req = sum(sum(i) for i in list_of_lines.values())
    write_log(log_level=20, msg='all_time_req: {}'.format(all_time_req))
    table_list = []
    for url, times_of_url in list_of_lines.items():
        count = len(times_of_url)
        max_time = max(times_of_url)
        time_sum = sum(times_of_url)
        time_avg = time_sum / count
        med = median(times_of_url)
        dict_stat = {"count": count,
                     "time_avg": time_avg,
                     "time_max": max_time,
                     "time_sum": time_sum,
                     "url": url,
                     "time_med": med,
                     "time_perc": time_sum / all_time_req,
                     "count_perc": count / all_count}
        table_list.append(dict_stat)
    return table_list[:count_size_report]


def main(size_report, report_dir, log_dir, ts_path):
    day_last_log, filename = find_last_log(log_dir)
    if not find_report_by_day(report_dir, day_last_log):
        now_time = time()

        my_list = open_logs(filename=log_dir + filename, req_time_more=0.0)
        sorted_dict_urls = group_by_url(my_list)
        table_json = log_statistic(sorted_dict_urls, count_size_report=size_report)

        write_log(log_level=20, msg='statistic time: {}'.format((time() - now_time) / 60, 'mins'))

        new_file = Template(open('templates/report.html').read()).safe_substitute(table_json=table_json)
        with open('reports/' + 'report_' + day_last_log.strftime("%Y-%m-%d") + '.html', 'w') as new_file_report:
            new_file_report.write(new_file)

        ts = time()
        with open(ts_path, 'w') as ts_file:
            ts_file.write(str(ts))

        write_log(log_level=20, msg='mtime of ts-file: {}'.format(os.path.getmtime(ts_path)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For custom config')
    parser.add_argument('--config', type=str, help='path to custom config file')
    args = parser.parse_args()

    if args.config:
        size_report, report_dir, log_dir, ts_path, logger_path_conf = read_config(args.config)
    else:
        size_report, report_dir, log_dir, ts_path, logger_path_conf = read_config('config/log_analyzer.conf')

    if logger_path_conf and logger_path_conf:
        handler = logging.FileHandler(logger_path_conf)
    else:
        handler = logging.StreamHandler(sys.stdout)

    logger.addHandler(handler)
    handler.setFormatter(formatter)

    main(size_report, report_dir, log_dir, ts_path)
