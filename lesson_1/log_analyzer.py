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

config = {
    "REPORT_SIZE": 1000000,
    "REPORT_DIR": "reports/",
    "LOG_DIR": "nginx_logs/",
    "TS_PATH": "log_nalyzer.ts"
}

# logger = logging.getLogger('Log Analyzer')
# logger.setLevel(logging.INFO)

# formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s')


def median(numbers):
    return (sorted(numbers)[int(round((len(numbers) - 1) / 2.0))] + sorted(numbers)[int(round((len(numbers) - 1) // 2.0))]) / 2.0


def read_config(path_to_config=None):
    if path_to_config:
        with open(path_to_config, 'r') as f:
            data = json.load(f)
        size_report = data.get('REPORT_SIZE', None)
        report_dir = data.get('REPORT_DIR', None)
        log_dir = data.get('LOG_DIR', None)
        ts_path = data.get('TS_PATH', None)
        logger_path_conf = data.get('LOGGER_PATH', None)
        # return size_report, report_dir, log_dir, ts_path, logger_path_conf
        result_config = {
            "REPORT_SIZE": size_report if size_report else config['REPORT_SIZE'],
            "REPORT_DIR": report_dir if report_dir else config['REPORT_DIR'],
            "LOG_DIR": log_dir if log_dir else config['LOG_DIR'],
            "TS_PATH": ts_path if ts_path else config['TS_PATH'],
            "LOGGER_PATH": logger_path_conf
        }
    else:
        result_config = config
    return result_config


def find_last_log(path_logs):
    pattern_log_name = re.compile(r"nginx-access-ui\.log-(?P<log_date>\d{8})(?P<type_file>.*)")
    date_list = []
    filename_log = ''
    try:
        for file_item in os.listdir(path_logs):
            find_files = pattern_log_name.search(file_item)
            if find_files:
                datadict = find_files.groupdict()
                log_date = datadict["log_date"]
                type_file = datadict["type_file"]
                this_date = datetime.strptime(log_date, '%Y%m%d')
                filename_log = 'nginx-access-ui.log-{}{}'.format(log_date, type_file)
                date_list.append(this_date)
                logging.info(msg='Max date config {}, nginx log filename: {}'.format(max(date_list), filename_log))
        return max(date_list), filename_log
    except OSError as ex:
        logging.exception(str(ex))


def find_report_by_day(path_reports, log_day):
    return os.path.exists(path_reports + '/report_{day}.html'.format(day=log_day.strftime("%Y-%m-%d")))


def parse_logs(log_file):
    pattern_log = re.compile(
        '(?:.+) \[(?:.+)\] "(?:.+) (?P<url>.+) HTTP/\d.\d".+(?P<time_req>\d+\.\d+)')
    lines = []
    for line in log_file:
        findes = pattern_log.search(line)
        if findes:
            datadict = findes.groupdict()
            url = datadict["url"]
            time_req = datadict["time_req"]
            lines.append((url, float(time_req)))
    logging.info(msg='Len of list parsed urls: {}'.format(len(lines)))
    return lines


def open_logs(filename=''):
    if filename.endswith(".gz"):
        opener = gzip.open
    else:
        opener = open
    with opener(filename, 'r') as log_file:
        parsed_list = parse_logs(log_file)
    return parsed_list


def group_by_url(list_to_sort):
    new_count_urls = defaultdict(list)
    for this_url, url_time in list_to_sort:
        new_count_urls[this_url].append(url_time)
    logging.info(msg='dicts len: {}'.format(len(new_count_urls.keys())))
    return new_count_urls


def log_statistic(list_of_lines, count_size_report=1000):
    all_count = sum(len(i) for i in list_of_lines.values())
    logging.info(msg='all count urls: {}'.format(all_count))
    all_time_req = sum(sum(i) for i in list_of_lines.values())
    logging.info(msg='all_time_req: {}'.format(all_time_req))
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


# def main(size_report, report_dir, log_dir, ts_path):
def main(dict_of_conf):
    day_last_log, filename = find_last_log(dict_of_conf['LOG_DIR'])
    if not find_report_by_day(dict_of_conf['REPORT_DIR'], day_last_log):
        now_time = time()

        my_list = open_logs(filename=dict_of_conf['LOG_DIR'] + filename)
        sorted_dict_urls = group_by_url(my_list)
        table_json = log_statistic(sorted_dict_urls, count_size_report=dict_of_conf['REPORT_SIZE'])

        logging.info(msg='statistic time: {}'.format((time() - now_time) / 60, 'mins'))

        new_file = Template(open('templates/report.html').read()).safe_substitute(table_json=table_json)
        try:
            with open(dict_of_conf['REPORT_DIR'] + 'report_' + day_last_log.strftime("%Y-%m-%d") + '.html', 'w') as new_file_report:
                new_file_report.write(new_file)
        except OSError as ex:
            logging.exception(str(ex))
            return str(ex)

        ts = time()
        with open(dict_of_conf['TS_PATH'], 'w') as ts_file:
            ts_file.write(str(ts))

        logging.info(msg='mtime of ts-file: {}'.format(os.path.getmtime(dict_of_conf['TS_PATH'])))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For custom config')
    parser.add_argument('--config', type=str, help='path to custom config file')
    args = parser.parse_args()
    # print(args.config)
    dict_of_conf = read_config(args.config)

    logging.basicConfig(
        # filename=local_path_error,
        filename=dict_of_conf.get('LOGGER_PATH', None),
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%H:%M:%S %d-%b-%Y',
        level=logging.DEBUG,
        # handlers=[queue_handler]
    )

    main(dict_of_conf)
