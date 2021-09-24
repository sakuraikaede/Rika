# Kiba 配置手册
欢迎使用Kiba！ 本手册为您提供对Kiba最基础的配置、教程与支持。
本项目基于 Mai-Bot 与 Chiyuki 。部分内容您可以参阅 https://github.com/Diving-Fish/mai-bot

## Step 1. 安装 Python

请自行前往 https://www.python.org/ 下载 Python 3 版本（> 3.7）并将其添加到环境变量（在安装过程中勾选 Add Python to system PATH）。对大多数用户来说，您应该下载 Windows installer (64-bit)。

在 Linux 系统上，可能需要其他方法安装 Python 3，请自行查找。

## Step 2. 运行项目

建议使用 git 对此项目进行版本管理。您也可以直接在本界面下载代码的压缩包进行运行。

在运行代码之前，您需要[点击下载](https://www.diving-fish.com/maibot/static.zip)此资源文件并解压到`src`文件夹中。在此之后，**您需要打开控制台，并切换到该项目所在的目录。**
在 Windows 10 / Windows Server 2016 以上的系统上，您可以直接在项目的根目录（即 bot.py）文件所在的位置按下 Shift + 右键，点击【在此处打开 PowerShell 窗口】。
如果您使用的是更旧的操作系统（比如 Windows 7），请自行查找关于`命令提示符(Command Prompt)`，`Windows Powershell`以及`cd`命令的教程。

打开控制台后，您可以输入
```
python --version
```
控制台应该会打印出 Python 的版本。如果提示找不到 `python` 命令，请检查环境变量，**建议您安装 Python 时勾选 Add Python to system PATH**。

之后，输入以下命令自动安装依赖。
```
pip install -r requirements.txt
```
在依赖安装完成后，输入此命令运行：
```
python bot.py
```
如果输出类似如下所示的内容，代表运行成功：
```
......
08-02 11:26:49 [INFO] uvicorn | Application startup complete.
08-02 11:26:49 [INFO] uvicorn | Uvicorn running on http://127.0.0.1:10219 (Press CTRL+C to quit)
```
如果输出了【ERROR】的红色输出，请您再次检查依赖项是否安装齐。

## Step 3. 连接 CQ-HTTP

前往 https://github.com/Mrs4s/go-cqhttp > Releases，下载适合自己操作系统的可执行文件。
go-cqhttp 在初次启动时会询问代理方式，选择反向 websocket 代理即可。

之后用任何文本编辑器打开`config.yml`文件，设置反向 ws 地址、上报方式：
```yml
message:
  post-format: array
  
servers:
  - ws-reverse:
      universal: ws://127.0.0.1:10219/cqhttp/ws
```
然后设置您的 QQ 号和密码。您也可以不设置密码，选择扫码登陆的方式。

登陆成功后，后台应该会发送一条类似的信息：
```
08-02 11:50:51 [INFO] nonebot | WebSocket Connection from CQHTTP Bot 114514 Accepted!
```
至此，您可以和对应的 QQ 号聊天并使用 mai bot 的所有功能了。

## FAQ

我不是 Windows 系统？
> 请您自行查阅其他系统上的 Python 安装方式。cqhttp提供了其他系统的可执行文件，您也可以自行配置 golang module 环境进行编译。

配置 nonebot 或 cq-http 过程中出错？
> 请查阅 https://github.com/nonebot/nonebot2 以及 https://github.com/Mrs4s/go-cqhttp 中的文档。

部分消息发不出来？
> 您的账号被风控了。解决方式：换号或者让这个号保持登陆状态和一定的聊天频率，持续一段时间。

## 说明

本 bot 提供了如下功能：

命令 | 功能
--- | ---
help | 查看帮助文档
今日舞萌 | 查看今天的舞萌运势
XXXmaimaiXXX什么 | 随机一首歌
随个[dx/标准][绿黄红紫白]<难度> | 随机一首指定条件的乐曲
查歌<乐曲标题的一部分> | 查询符合条件的乐曲
[绿黄红紫白]id<歌曲编号> | 查询乐曲信息或谱面信息
<歌曲别名>是什么歌 | 查询乐曲别名对应的乐曲
定数查歌 <定数> <br> 定数查歌 <定数下限> <定数上限> |  查询定数对应的乐曲
分数线 <难度+歌曲id> <分数线> | 展示歌曲的分数线
XrY | 在限定的上、下限随机数，要求X、Y均为正整数。

## License

MIT

您可以自由使用本项目的代码用于商业或非商业的用途，但必须附带 MIT 授权协议。
