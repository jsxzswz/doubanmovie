#!/usr/bin/env python 
# -*- coding:utf-8 -*-
# @Author  : swz
# @Time    : 2019/6/18 16:19
# @File    : run.py

from scrapy import cmdline

cmdline.execute("scrapy crawl doubanMovie".split())