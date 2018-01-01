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
    u"REPORT_SIZE": 1000000,
    u"REPORT_DIR": u"reports/",
    u"LOG_DIR": u"nginx_logs/",
    u"SUCCESS_LEVEL_PARSE": 0.66,
    u"TS_PATH": u"log_nalyzer.ts"
}


def median(numbers):
    return (sorted(numbers)[int(round((len(numbers) - 1) / 2.0))] + sorted(numbers)[int(round((len(numbers) - 1) // 2.0))]) / 2.0


def read_config(config, path_to_config=None):
    if path_to_config:
        with open(path_to_config, 'r') as f:
            custom_dict = json.load(f)
        config.update(custom_dict)
    return config


def find_last_log(path_logs):
    pattern_log_name = re.compile(r"nginx-access-ui\.log-(?P<log_date>\d{8})(?P<type_file>$|.gz)")
    date_list = []
    try:
        for file_item in os.listdir(path_logs):
            find_files = pattern_log_name.search(file_item)
            if find_files:
                datadict = find_files.groupdict()
                log_date = datadict["log_date"]
                type_file = datadict["type_file"]
                this_date = datetime.strptime(log_date, '%Y%m%d')
                filename_log = 'nginx-access-ui.log-{}{}'.format(log_date, type_file)
                date_list.append((this_date, filename_log))
        if date_list:
            max_log = max(date_list, key=lambda x: x[0])
            logging.info(msg='Max date config {}, nginx log filename: {}'.format(max_log[0], max_log[1]))
            return max_log[0], max_log[1]
    except OSError as ex:
        logging.exception(str(ex))


def find_report_by_day(path_reports, log_day):
    return os.path.exists(path_reports + '/report_{day}.html'.format(day=log_day.strftime("%Y-%m-%d")))


def parse_logs(log_file, parse_level):
    pattern_log = re.compile(
        '(?:.+) \[(?:.+)\] "(?:.+) (?P<url>.+) HTTP/\d.\d".+(?P<time_req>\d+\.\d+)')
    lines = []
    count_success = 0
    all_count = 0
    for line in log_file:
        all_count += 1
        findes = pattern_log.search(line)
        if findes:
            try:
                datadict = findes.groupdict()
                url = datadict["url"]
                time_req = datadict["time_req"]
                lines.append((url, float(time_req)))
                count_success += 1
            except Exception as ex:
                logging.exception('Cannot parse this line {} with error: {}'.format(line, ex))
    # print float(count_success) / all_count, parse_level
    if float(count_success) / all_count < parse_level:
        logging.exception('Less 66% success parsed lines')
        raise Exception('Less 66% success parsed lines')
    logging.info(msg='Len of list parsed urls: {}'.format(len(lines)))
    return lines


def open_logs(filename, parse_level):
    if filename.endswith(".gz"):
        opener = gzip.open
    else:
        opener = open
    # TODO think about encoding
    with opener(filename, 'r') as log_file:
        parsed_list = parse_logs(log_file, parse_level)
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
def main(dict_of_config):
    last_log = find_last_log(dict_of_config['LOG_DIR'])
    if last_log:
        day_last_log, filename = last_log
        if not find_report_by_day(dict_of_config['REPORT_DIR'], day_last_log):
            now_time = time()

            my_list = open_logs(filename=os.path.join(dict_of_config['LOG_DIR'], filename),
                                parse_level=dict_of_config['SUCCESS_LEVEL_PARSE'])
            sorted_dict_urls = group_by_url(my_list)
            table_json = log_statistic(sorted_dict_urls, count_size_report=dict_of_config['REPORT_SIZE'])

            logging.info(msg='statistic time: {}'.format((time() - now_time) / 60, 'mins'))

            new_file = Template(open('templates/report.html').read()).safe_substitute(table_json=table_json)

            if not os.path.exists(dict_of_config['REPORT_DIR']):
                logging.info(msg='Create folder: {} for reports'.format(dict_of_config['REPORT_DIR']))
                os.mkdir(dict_of_config['REPORT_DIR'])

            try:
                with open(dict_of_config['REPORT_DIR'] + 'report_' + day_last_log.strftime("%Y-%m-%d") + '.html', 'w') as new_file_report:
                    new_file_report.write(new_file)
            except OSError as ex:
                logging.exception(str(ex))
                return str(ex)

            ts = time()
            with open(dict_of_config['TS_PATH'], 'w') as ts_file:
                ts_file.write(str(ts))

            logging.info(msg='mtime of ts-file: {}'.format(os.path.getmtime(dict_of_config['TS_PATH'])))
        else:
            logging.info(msg='Report for log {} already exist'.format(last_log))

            ts = time()
            with open(dict_of_config['TS_PATH'], 'w') as ts_file:
                ts_file.write(str(ts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For custom config')
    parser.add_argument('--config', type=str, help='path to custom config file')
    args = parser.parse_args()
    dict_of_config = read_config(config, args.config)

    logging.basicConfig(
        filename=dict_of_config.get('LOGGER_PATH', None),
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%H:%M:%S %d-%b-%Y',
        level=logging.DEBUG
    )

    try:
        main(dict_of_config)
    except Exception as ex:
        logging.exception(str(ex))
