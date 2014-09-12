#!/usr/bin/env python
# encoding: utf-8

import os
import csv
import json
import shutil


DIST_DIR = './dist'
DATA_PATH = './data/GeoLite2-City-Locations.csv'
TEST_DATA_PATH = 'test.csv'


def readcsv(parse, save=None):
    '''
    :param parse: a function to parse a list data of row
        eg. ['col0', 'col1', ...]
    '''
    try:
        shutil.rmtree(DIST_DIR)
    except:
        pass
    os.mkdir(DIST_DIR)

    with open(DATA_PATH) as f:
        r = csv.reader(f)
        for row in r:
            parse(row)
    save()


def print_row(row):
    print row


# 用于全局保存当前已经存在的国家和大洲
countries = {}
continents = []


def parse_country_city(row):
    '''
    生成3份数据, 分别写入country.josn, continent.json
    因为要导入Mongo 的原因，下面格式将会每行一条写入json文件中

    Continent:
    {
        'name_en': 'Asia',
        'code': 'AS',
    }

    Country：
    {
        'name_en': 'China',
        'code': 'CN',
        'continent_code': 'AS',
        'subdivisions': {
            '12': {
                'name_en': 'zhejiang',
                'code': '12',
                'citys': ['Ningbo', 'Hangzhou']
            }
        },
    }
    城市没有code只能通过名字匹配，所以不嵌套country下，
    如果需要新增城市相关的详细信息，城市单独形成一张表
    '''

    if row[0] == 'geoname_id':
        # header:
        # ['geoname_id', 'continent_code', 'continent_name',
        #  'country_iso_code', 'country_name', 'subdivision_iso_code',
        #  'subdivision_name', 'city_name', 'metro_code', 'time_zone']
        return
    _write_continent(row)
    _cache_country(row)


def _write_continent(row):
    global continents
    fpath = os.path.join(DIST_DIR, 'continents.json')
    # cont -> continent
    cont_code = row[1]
    cont_name = row[2]
    print continents
    if cont_code and cont_code not in continents:
        with open(fpath, 'a+') as f:
            c = json.dumps({'name_en': cont_name, 'code': cont_code})
            f_writeline(f, c)
        continents.append(cont_code)


def _cache_country(row):
    global countries
    # coun -> country, subd -> subdivision
    cont_code = row[1]
    coun_code = row[3]
    coun_name = row[4]
    subd_code = row[5]
    subd_name = row[6]
    city_name = row[7]
    # time_zone = row[9]
    if not (coun_code and coun_name and
            subd_code and subd_name and city_name):
        return

    data = {
        'name_en': coun_name,
        'code': coun_code,
        'continent_code': cont_code,
        'subdivisions': {
            subd_code: {
                'name_en': subd_name,
                'code': subd_code,
                'citys': [city_name]
            }
        }
    }
    if coun_code in countries.keys():
        old_subds = countries[coun_code]['subdivisions']
        subds = _update_subds(subd_code, old_subds,
                              data['subdivisions'][subd_code])
        countries[coun_code]['subdivisions'] = subds
    else:
        countries[coun_code] = data


def _update_subds(subd_code, old_subds, data):
    if subd_code in old_subds.keys():
        city = data['citys'][0]
        try:
            old_citys = old_subds[subd_code]['citys']
        except:
            import pdb
            pdb.set_trace()
        if city not in old_citys:
            old_citys.append(city)
    else:
        old_subds[subd_code] = data
    return old_subds


def save_countries():
    global countries
    fpath = os.path.join(DIST_DIR, 'countries.json')
    for country in countries.itervalues():
        with open(fpath, 'a+') as f:
            f_writeline(f, json.dumps(country))


def f_writeline(f, text):
    f.write(text + '\n')


if __name__ == '__main__':
    readcsv(parse_country_city, save_countries)
