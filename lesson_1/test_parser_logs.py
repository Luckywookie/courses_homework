import os
import unittest
from datetime import datetime
from mock import MagicMock
from pprint import pprint
from log_analyzer import read_config, open_logs, group_by_url, log_statistic, find_last_log

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_OF_PARSED_DATA = [
    ('/api/v2/banner/25019354', 0.390),
    ('/api/1/photogenic_banners/list/?server_name=WIN7RB4', 0.133),
    ('/api/v2/banner/16852664', 0.199),
    ('/api/v2/slot/4705/groups', 0.704),
    ('/api/v2/internal/banner/24294027/info', 0.146),
    ('/api/v2/banner/25019354', 0.590)
]


DICT_OF_GROUPED_DATA = {
    '/api/v2/banner/25019354': [0.390, 0.590],
    '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133],
    '/api/v2/banner/16852664': [0.199],
    '/api/v2/slot/4705/groups': [0.704],
    '/api/v2/internal/banner/24294027/info': [0.146]
}

SAMPLE_STAT = [
    dict(count=1, count_perc=0, time_avg=0.199, time_max=0.199, time_med=0.199, time_perc=0.09204440333024978,
         time_sum=0.199, url='/api/v2/banner/16852664'),
    dict(count=1, count_perc=0, time_avg=0.704, time_max=0.704, time_med=0.704, time_perc=0.32562442183163737,
         time_sum=0.704, url='/api/v2/slot/4705/groups'),
    dict(count=1, count_perc=0, time_avg=0.146, time_max=0.146, time_med=0.146, time_perc=0.06753006475485661,
         time_sum=0.146, url='/api/v2/internal/banner/24294027/info'),
    dict(count=2, count_perc=0, time_avg=0.49, time_max=0.59, time_med=0.49, time_perc=0.4532839962997225,
         time_sum=0.98, url='/api/v2/banner/25019354'),
    dict(count=1, count_perc=0, time_avg=0.133, time_max=0.133, time_med=0.133, time_perc=0.06151711378353377,
         time_sum=0.133, url='/api/1/photogenic_banners/list/?server_name=WIN7RB4')
]

CONFIG = {
    "REPORT_SIZE": 1000000,
    "REPORT_DIR": "reports/",
    "LOG_DIR": "nginx_logs/",
    "TS_PATH": "log_nalyzer.ts"
}

NEW_CONFIG = {
    'REPORT_DIR': 'reports/',
    'REPORT_SIZE': 1000000,
    'LOG_DIR': 'nginx_logs/',
    'TS_PATH': 'log_nalyzer_custom.ts',
    'LOGGER_PATH': 'log/parse_nginx_logs.log'
}


# class OpenTest(unittest.TestCase):
#     test_file_path = 'nginx_logs/nginx-access-ui.log-test2'
#
#     def test_open_write_file(self):
#         self.assertRaises(IOError, open_logs(self.test_file_path, 0.0))


class ParserTest(unittest.TestCase):
    test_file_path = 'nginx_logs/nginx-access-ui.log-test'
    test_custom_config = 'custome_log.conf'

    def test_open_conf(self):
        self.result_config = read_config(CONFIG, self.test_custom_config)
        self.assertDictEqual(self.result_config, NEW_CONFIG)

    def test_find_last_file(self):
        os.listdir = MagicMock(return_value=['nginx-access-ui.log-20170102',
                                             'nginx-access-ui.log-20170602.gz',
                                             'nginx-access-ui.log-20170107'])
        self.last_log = find_last_log('')
        self.assertEqual(self.last_log, (datetime(2017, 6, 2, 0, 0), 'nginx-access-ui.log-20170602.gz'))

    def test_parse_log(self):
        self.parsed_data = open_logs(self.test_file_path)
        self.assertListEqual(self.parsed_data, LIST_OF_PARSED_DATA)

    def test_group_data(self):
        self.grouped_data = group_by_url(LIST_OF_PARSED_DATA)
        self.assertDictEqual(self.grouped_data, DICT_OF_GROUPED_DATA)

    def test_stat_count(self):
        self.stat = log_statistic(DICT_OF_GROUPED_DATA)
        self.assertEqual(self.stat, SAMPLE_STAT)


if __name__ == '__main__':
    unittest.main()
