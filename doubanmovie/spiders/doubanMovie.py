import scrapy

from doubanmovie.items import MovieItem


class DoubanMovie(scrapy.Spider):
    # 爬虫唯一标识符
    name = 'doubanMovie'
    # 爬取域名
    allowed_domain = ['movie.douban.com']
    # 爬取页面地址
    start_urls = ['https://movie.douban.com/top250']

    def parse(self, response):
        selector = scrapy.Selector(response)
        # 解析出各个电影
        movies = selector.xpath('//div[@class="item"]')
        # 存放电影信息
        item = MovieItem()
        for movie in movies:
            # 电影中文名字
            item['name'] = movie.xpath('.//span[@class="title"]/text()').extract_first().strip()
            # 电影信息列表
            infos = movie.xpath('.//div[@class="bd"]/p/text()').extract()
            # 电影信息合成一个字符串
            fullInfo = ''
            for info in infos:
                fullInfo += info.strip()
            item['info'] = fullInfo
            # 提取评分信息
            item['rating'] = movie.xpath('.//span[@class="rating_num"]/text()').extract_first().strip()
            # 提取评价人数
            item['num'] = movie.xpath('.//div[@class="star"]/span[last()]/text()').extract_first().strip()[:-3]
            # 提取经典语句，quote可能为空
            quote = movie.xpath('.//span[@class="inq"]/text()').extract()
            if quote:
                quote = quote[0].strip()
            else:
                quote = 'null'
            item['quote'] = quote
            # 提取电影图片
            item['img_url'] = movie.xpath('.//img/@src').extract_first()
            item['id_num'] = movie.xpath('.//em/text()').extract_first()
            yield item

        # next_page = selector.xpath('//span[@class="next"]/a/@href').extract()
        # if next_page:
        #     url = 'https://movie.douban.com/top250' + next_page[0]
        #     yield scrapy.Request(url, callback=self.parse)