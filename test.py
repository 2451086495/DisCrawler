#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser


config = ConfigParser.ConfigParser()
config.read('./spider.ini')

print config.sections()
print config.get("redis", "redis")
print config.get("spider", "DataSrc1", vars = {"DataSrc1":'ahah'})
print config.get("caffe", "PreTrainedModel", vars = {"DataSrc1":'ahah'})