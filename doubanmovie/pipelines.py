# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from logging import log

import pymysql
import pymongo
from scrapy import Request
import re
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from doubanmovie import settings
from doubanmovie.items import MovieItem
from openpyxl import Workbook


class JsonPipeline(object):
    def __init__(self):
        self.file = open('movie.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        # 读取item中的数据
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.file.close()


class ImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # yield Request(item['img_url'])
        # 循环每一张图片地址下载，若传过来的不是集合则无需循环直接yield
        # for image_url in item['img_url']:
        # meta里面的数据是从spider获取，然后通过meta传递给下面方法：file_path
        yield Request(item['img_url'], meta={'name': item['name']})

    # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
    def file_path(self, request, response=None, info=None):
        # 提取url前面名称作为图片名。
        image_guid = request.url.split('/')[-1]
        # 接收上面meta传递过来的图片名称
        name = request.meta['name']
        # 过滤windows字符串，不经过这么一个步骤，你会发现有乱码或无法下载
        name = re.sub(r'[？\\*|“<>:/]', '', name)
        # 分文件夹存储的关键：{0}对应着name；{1}对应着image_guid
        filename = u'{0}/{1}'.format(name, image_guid)
        return filename

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        item['img_url'] = image_paths
        return item


class MysqlPipeline(object):
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=3306,
            db=settings.MYSQL_DBNAME,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PWD,
            charset='utf8',
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor();

    def process_item(self, item, spider):
        try:
            self.cursor.execute(
                """insert into doubanmovie(name, info, rating, num ,quote, img_url,id_num)
                value (%s, %s, %s, %s, %s, %s, %s)""",
                (item['name'],
                 item['info'],
                 item['rating'],
                 item['num'],
                 item['quote'],
                 item['img_url'],
                 item['id_num']
                 ))
            # 提交sql语句
            self.connect.commit()
        except Exception as error:
            # 出现错误时打印错误日志
            log(error)
        return item


class MongoDBPipeline(object):
    def __init__(self):
        client = pymongo.MongoClient("localhost", 27017)
        doubanMovie = client["doubanMovie"]
        self.movieInfo = doubanMovie["movieInfo"]

    def process_item(self, item, spider):
        """ 判断item的类型，并作相应的处理，再入数据库 """
        if isinstance(item, MovieItem):
            try:
                self.movieInfo.insert(dict(item))
            except Exception:
                pass
        return item


class ExcelPipeline(object):
    def __init__(self):
        self.file = "豆瓣电影250.xlsx"
        item = [u'序号', u'电影名字', '电影信息', u'评分', u'评论人数', u'经典语句', u'电影图片']
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(['%s' % i for i in item])

    def process_item(self, item, spider):
        try:
            if isinstance(item, MovieItem):
                item = dict(item)
                data = [item["id_num"], item["name"], item["info"], item["rating"], item["num"], item["quote"],
                        item["img_url"]]
                self.ws.append(data)
                # self.wb.save(self.file)
                return item
        except:
            self.ws.save(self.file)
            return item

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        print("##############export data to excel end#############")
        self.wb.save(self.file)
