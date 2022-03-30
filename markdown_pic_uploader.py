# -*- coding: utf-8 -*-
"""
Created on Sat Mar 26 16:22:18 2022
@author: Moriarty(微信公众号：ManjaroLinux)
@LICENSE：GPL
Markdown_image_upload script
"""
from os.path import expanduser
import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
import oss2
import oss2.exceptions as ep
import json
import urllib
import os

# 解析配置文件OSSconfig.txt


def parse_config(conf_path):
    with open(conf_path, 'r') as fo:
        config_date = fo.read()
    return json.loads(config_date)

# 如果图片名中有的汉字转码后产生的%开头的字符串则将其转码成汉字
# 如果图片名不包含转码后产生的%开头的字符串则不处理


def parse_chinese(ori_str):
    chinese_str = urllib.parse.unquote(ori_str)
    return chinese_str

# 从md图片链接中过滤出图片名


def parse_path(ori_image_link):
    image_dir = os.path.split(ori_image_link)[0]
    image_name = os.path.split(ori_image_link)[1]
    return image_dir, image_name

# 阿里云OSS相关操作


class AliyunOSS():
    def __init__(self, conf):
        self.auth = oss2.Auth(conf['AccessKeyId'], conf['AccessKeySecret'])
        self.bucket = oss2.Bucket(self.auth, conf['EndPoint'], conf['Bucket'])

    def upload_image(self, OSS_file_name, localPath):
        result = self.bucket.put_object_from_file(OSS_file_name, localPath)
        return result


class image_preprocessor(Treeprocessor):
    def run(self, root):
        self.md.images = []
        for image in root.findall('.//img'):
            self.md.images.append(image.get('src'))

# 提取图片链接


class image_extract_extension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.treeprocessors.register(image_preprocessor(md), 'tree', 15)

# 扫描给定目录下的全部 .md，但不扫描以new.md结尾的md文件


def scan_md():
    md_path_list = []
    scan_dir_path = input("请输入待扫描目录的绝对路径或md文档绝对路径:")

    # 判断扫描目录处理多个文件还是仅处理单个文件
    if scan_dir_path[-3:] == ".md":
        md_path_list = [scan_dir_path]

    else:
        for root, dirs, files in os.walk(scan_dir_path):
            for item in files:

                # 已经存在的*.md_oss.md文件不会再次生成新文件，而是被重新覆盖
                if os.path.splitext(item)[1] == ".md" and item[-6:] != "oss.md":
                    md_abspath = os.path.join(root, item)
                    md_path_list.append(md_abspath)

    return md_path_list

# 本地图片上传到OSS


def toOSS(md_local_path):
    # 加载配置文件
    conf = parse_config(expanduser("ossconfig.txt"))

    # 获取md文件名称
    md_name = os.path.split((md_local_path))[1]

    # 上传成功与失败次数计算
    success_time = 0
    failure_time = 0
    failure_pic_name = []
    error_message = []
    OSS_pic = 0

    # 是否另存.md_oss.md的标志位，默认另存，当出现配置文件异常时不另存
    write_md_flag = 1

    # 定义AliyunOSS实例
    OSS_manager = AliyunOSS(conf)
    md = markdown.Markdown(extensions=[image_extract_extension()])

    # 读取md文件内容
    with open(md_local_path, mode='r', encoding='utf-8') as md_file:
        md_data = md_file.read()

    md.convert(md_data)

    # 将md中的图片链接放到一个列表
    images = md.images
    images_len = len(images)

    # 遍历图片
    for index in range(images_len):

        # 获取md所在目录、图片目录及名字
        img_name = parse_path(images[index])[1]
        img_dir = parse_path(images[index])[0]
        md_dir = parse_path(md_local_path)[0]

        # 判断该图片是否已经在OSS图床
        if images[index][:8] == "https://":
            OSS_pic = OSS_pic + 1
            img = img_name
            print("\r", "正在处理第 {num} 张图片({name})...".format(
                num=index+1, name=img).ljust(100), end='')
            continue
        else:
            img = parse_chinese(img_name)
            print("\r", "正在处理第 {num} 张图片({name})...".format(
                num=index+1, name=img).ljust(100), end='')

        # 先判断md中图片路径是相对路径还是绝对路径，进而得到本地图片路径
        if os.path.isabs(images[index]):
            img_local_path = os.path.join(parse_path(images[index])[0], img)
        else:
            img_local_path = os.path.join(md_dir, img_dir, img)

        # 上传图片

        try:
            result = OSS_manager.upload_image(img, img_local_path)
        except ep.RequestError:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("网络请求失败，请检查网络连接���ossconfig.txt中EndPoint参数")
            write_md_flag = 0
            break
        except ep.NoSuchBucket:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("ossconfig.txt中Bucket参数配置错误，没有该Bucket")
            write_md_flag = 0
            break
        except ConnectionError:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("网络连接失败，请检查网络连接")
            write_md_flag = 0
            break
        except ep.ServerError:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("ossconfig.txt中AccessKeyId参数配置出错")
            write_md_flag = 0
            break
        except ep.SignatureDoesNotMatch:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("ossconfig.txt中AccessKeySecret参数配置出错")
            write_md_flag = 0
            break
        except FileNotFoundError:
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            error_message.append("本地找不到该图片")
            continue

        # 判断是否上传成功
        if result.status == 200:
            url = os.path.join(conf['UrlPrefix'], img)
            md_data = md_data.replace(images[index], url, 1)
            success_time = success_time + 1
        else:
            error_message.append("未知错误")
            failure_time = failure_time + 1
            failure_pic_name.append(img)
            continue

    # 当没有发生中断，同时md文件中存在图片时，写入新文件
    if write_md_flag and images_len != 0:
        with open(md_local_path + '_oss.md', mode='w', encoding='utf-8') as new_md:
            new_md.write(md_data)

    # 打印输出结果
        print("\r", "{md}处理完毕！".format(md=md_name).ljust(100))
        print("共 {pic_num} 张图片，{success} 张图片上传成功，{failure} 张图片上传失败，{oss} 张已在OSS图床！".format(
            pic_num=images_len, success=success_time, failure=failure_time, oss=OSS_pic))
        print('')

        # 如果有上传失败的图片，打印出图片名
        if len(failure_pic_name):
            for item in range(len(failure_pic_name)):
                print("上传失败的第 {order} 张图片：{picture}".format(
                    order=item+1, picture=failure_pic_name[item]))
                print("失败原因：", error_message[item])
                print('')

        # 分割线
        print("------------------------------------------")
    
        
    # 如果md文档中没有图片的话不处理该文档
    elif write_md_flag and images_len == 0:
        print("{md}文件中没有图片，不做处理！".format(md = md_name).ljust(100))
        print('')
        print("------------------------------------------")

    else:
        # 打印中断之前图片上传失败的原因及中断原因
        print("\r", "{md}处理到第 {interrupt_img} 张图片时发生中断！！！".format(
            md=md_name, interrupt_img = success_time+failure_time+OSS_pic).ljust(100))
        print("共 {pic_num} 张图片，{success} 张图片上传成功，{failure} 张图片上传失败，{oss} 张已在OSS图床！".format(
            pic_num=images_len, success=success_time, failure=failure_time, oss=OSS_pic))
            
        # 列表error_message中内容：如果没有中断，存储的是所有图片上传原因；
        # 如果存在中断，则最后一个元素是中断原因，其余元素为上传失败原因
        for item in range(len(failure_pic_name)-1):
            print("上传失败的第 {order} 张图片{picture}：".format(
                order=item+1, picture=failure_pic_name[item]))
            print("失败原因：", error_message[item])
            print('')
        print("中断原因为:", error_message[-1])

    return write_md_flag


if __name__ == '__main__':
    
    print("Open Source License:GPL")
    print("作者：ManjaroLinux公众号")
    print("使用规则请看 README.md")
    md_list = scan_md()
    for item in md_list:
        
        # 判断是否发生了意外中断
        interrupt_flag = toOSS(item)
        if interrupt_flag ==0:
            break
