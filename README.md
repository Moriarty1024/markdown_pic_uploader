# Markdown_pic_uploader 使用说明
## 说在前面
- 开源软件许可：GPLv2.0
- 本软件暂时只能实现将本地图片上传到阿里云OSS，其他平台不支持，可下载源码自己二次开发
- 图片上传之后会对原文件中的图片链接进行替换，并将替换后的.md文件另存在当前目录下，命名格式为：\*.md_oss.md

## 使用说明
- ossconfig.txt中存放的是你的阿里云OSS相关设置项，具体项的含义请参照以下网址：
[配置项 (aliyun.com)](https://help.aliyun.com/document_detail/64097.html)
- 在windoes和Linux平台下均可以执行以下命令运行markdown_pic_uploader.py，前提是电脑上装有python3.x以及使用到的第三方库：`oss2`、`markdown`
```shell
python markdown_pic_uploader.py
```

- 如果不想安装第三方库或者不会安装，请下载可执行文件，缺点是体积大(使用pyinstaller打包了依赖项)。Windows平台下载MD_pic_uploader.exe，双击运行即可；Linux平台下载MD_pic_uploader，双击，选择“在终端中运行”，或者直接在可执行文件所在目录打开终端，输入软件名回车即可

- 运行.py脚本或者可执行文件之后，会提示：“请输入待扫描目录的绝对路径或md文档绝对路径:”，你要输入你的.md文件所在的文件夹（目录）的绝对路径，例如：C:\abc\hello\789（Windows）、/home/md_dir（Linux），或者单个md文件的绝对路径

## 软件特性说明

- 该软件会遍历你所给的目录下的所有文件，并找到所有的.md文件，并将所有.md中的图片上传到阿里云OSS（.md_oss.md结尾的md文件不会被遍历，这样可实现刷新.md_oss.md结尾的文件内容，即：当再次在md文件中插入了本地图片并运行软件之后，会刷新之前生成的.md_oss.md结尾的文件的内容）
- .md文件中的图片只能是本地图片或者已经存到阿里云OSS的图片，如果是本地图片的话可以用相对路径或者绝对路径。相对路径是以你的.md所在位置作为参照，比如你的图片和你的md文件在同一个目录下，那么md文件中图片链接为\!\[\](图片名.png)，如果图片放在md所在目录的image目录中，那么md文件中图片链接为\!\[\](image/图片名.png)
- 对于没有图片的md文件程序会跳过该文件，不进行处理，也不另存文件