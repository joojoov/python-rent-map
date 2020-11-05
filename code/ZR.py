# -*- coding: utf-8 -*-
import tesserocr
import requests
import urllib
import csv
import time
import os 
import re
import sys

from bs4 import BeautifulSoup
from tesserocr import PyTessBaseAPI
from PIL import Image

ua = ["Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1",
      "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
      "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
      'Mozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0',
      'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
      'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
      'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/533.3',
      'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.8 (KHTML, like Gecko) Chrome/7.0.521.0 Safari/534.8',
      'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.1 Safari/534.3',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
      'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
      'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8',
      'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.77 Safari/535.7ad-imcjapan-syosyaman-xkgi3lqg03!wgz'
      ]

url = 'http://gz.ziroom.com/z/r0-p{page}/?qwd=天河&cp=1500TO3000'
page = 0
n = 0

csv_file = open('rent.csv', 'w', -1, "UTF-8")
csv_write = csv.writer(csv_file, delimiter=',')

def get_price_img(n, image_url):
    image_path = './img_dir/'  # 图片保存路径
    image_name = '{}{}'.format(image_path, str(n))
    urllib.request.urlretrieve(url=image_url, filename=image_name)
    return image_name

def pic_turn_white_ocr(image_name):
    im = Image.open(image_name)
    x, y = im.size

    # 使用白色来填充背景
    p = Image.new('RGBA', im.size, (255, 255, 255))
    p.paste(im, (0, 0, x, y), im)
    white_picture_name = image_name + 'white.png' 
    p.save(white_picture_name)

    # 放大
    img = Image.open(white_picture_name)
    x, y = img.size
    pic_big = Image.new('RGBA', (x + 20, y + 20), (255, 255, 255))
    pic_big.paste(img, (10, 10, x + 10, y + 10), img)

    # 灰度
    pic_gray = pic_big.convert('L')
    gray_picture_name = image_name + 'gray.png'
    pic_gray.save(gray_picture_name)

    # 二值化
    threshold = 220

    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    two_pic = pic_gray.point(table, '1')
    two_picture_name = image_name + 'two.png'
    two_pic.save(two_picture_name)

    image = Image.open(two_picture_name)
    price_pic = tesserocr.image_to_text(image)
    price_list = list(price_pic)  
    del(price_list[-1])
    num_list = list(map(int, price_list))  
    return num_list

def ocr_pic(num_list, offset): 
    os = float(offset)
    n = int(os / 21.4)
    num = num_list[n]
    return num

if __name__ == '__main__':
    while True:
        page += 1
        print('正在下载网页:', url.format(page=page))
        response = requests.get(url.format(page=page))
        html = BeautifulSoup(response.content, "html.parser")
        house_list = html.find('div', class_='Z_list-box').find_all('div', {'class':'info-box'})

        if html.find('div', class_='Z_list').find('div', {'class':'Z_list-stat Z_list-empty'}):
            print('所有信息爬取完成')
            break

        for house in house_list:
            n += 1
            house_title = house.find('h5', {'class', ('title sign', 'title turn', 'title pre_sign', 'title release')}).get_text()  #注意后面有待释放状态的房子，一定要添加title release
            house_url = 'http:'+ house.a['href']
            response = requests.get(house_url)
            html = BeautifulSoup(response.content, "html.parser")
            house_location_root1 = html.find('h1', {'class': 'Z_name'}).get_text()
            house_location_root2 = re.search(r'(?<=\·).+?(?=$)', house_location_root1, re.M).group(0)
            house_location = re.sub(r'\·.*$', "", house_location_root2)

            price_root = house.find('div', {'class':'price'}).find('span', {'class':'num'})
            offset_string = house.find('div', {'class':'price'}).find_all('span', {'class':'num'})

            url_root1 = re.sub(r'\<span class=\"num\" style=\"background-image\: url\(', "", str(price_root))
            url_root2 = re.sub(r'png.*$', "", url_root1)
            image_url = 'http:'+ url_root2 +'png'
            print(image_url)

            i_n = get_price_img(n, image_url)
            w_p_n = pic_turn_white_ocr(i_n)

            num_list = [] 
            offset_n = 0
            for i in offset_string:
                offset_n += 1
                offset_root = re.sub(r'px\"\>\<\/span\>.*$', "", str(i))  
                offset = re.search(r'(?<=background-position: -).+?(?=$)', offset_root, re.M).group(0)
                num = str(ocr_pic(w_p_n, offset))
                num_list.append(num)

            house_price = ''.join(num_list) 
            csv_write.writerow([house_title, house_location, house_price, house_url])
            

    csv_file.close()


















    

    