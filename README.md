这个是一个AI智能伴侣网页的小练习
时间：2026.09

请按照以下步骤进行第一次项目启动

1、API的创建与充值
此项目AI模型为Deepseek-v4-pro
如果想要进行对话，请前往DeepSeek官网进行API充值，链接如下
https://platform.deepseek.com/usage
充值后点击API keys按钮，创建API key，API名称随意
创建后请及时复制API Key

2、环境的配置
首先先去设置中找到高级系统属性，再找到环境变量
点击新建，无论是用户变量还是系统变量都是可以的
变量名为 DEEPSEEK_API_KEY
变量值则为第一步复制的API Key

设置完成后，请关闭并重新打开终端（或重启 IDE），确保环境变量生效。

3、环境的搭建
（若您没有python环境，请先去
https://www.python.org/downloads/
进行python的下载与配置，本文档将不会进行描述
安装 Python 时请务必勾选 Add Python to PATH，否则命令行可能找不到 python。）

下载好zip安装包后进行解压操作
在解压后的文件夹地址栏输入 `cmd` 并回车，打开命令行窗口。
然后输入以下命令回车（假设 `star.py` 就在当前文件夹）：
python star.py
如果不在当前文件夹，请使用完整路径并用双引号包裹，例如：
python "D:\下载\AI伴侣\star.py"

（star.py 会自动检查并安装所需依赖（streamlit、openai），然后启动应用。）


（如若有编程软件，例如vscode, pycharm等
也可在此类编程软件中打开本文件夹进行相同操作）

<img width="3072" height="1824" alt="image" src="https://github.com/user-attachments/assets/dcddb0f7-435c-4f5e-b1de-1344dedb7848" />
