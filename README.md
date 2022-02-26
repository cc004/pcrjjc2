# pcrjjc2

本插件是[pcrjjc](https://github.com/lulu666lulu/pcrjjc)重置版，不需要使用其他后端api，但是需要自行配置客户端  

**本项目基于AGPL v3协议开源**

## 配置方法

1. 更改account.json内的account和password为你的bilibili账号的用户名和密码, admin为管理员的qq，用来接受bilibili验证码进行登录

2. 机器人登录需要验证码时会将链接形式私聊发给admin，这时你需要点进链接正确验证，如果成功，将会出现如下的内容：  
  `
  validate=c721fe67f0196d7defad7245f6e58d62
  seccode=c721fe67f0196d7defad7245f6e58d62|jordan
  `  
  此时，你需要将验证结果发给机器人，通过指令`/pcrval c721fe67f0196d7defad7245f6e58d62`即可完成验证（~~测试的时候似乎私聊没反应？私聊没反应的话就在群里发也可以，反正不泄露密码，大概率是程序没写好~~已修复 感谢 @assassingyk ）

3. account.json里面的platform和channel分别代表android和b服，emmm最好别改，改了我也不知道可不可以用

4. 安装依赖：

   ```
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
5. 在create_img.py中更改你所在的服务器名称
6. 台服请切换到`tw`分支

## 命令

| 关键词             | 说明                                                     |
| ------------------ | -------------------------------------------------------- |
| 竞技场绑定 uid     | 绑定竞技场排名变动推送，默认双场均启用，仅排名降低时推送 |
| 竞技场查询 uid     | 查询竞技场简要信息（绑定后无需输入uid）                  |
| 停止竞技场订阅     | 停止战斗竞技场排名变动推送                               |
| 停止公主竞技场订阅 | 停止公主竞技场排名变动推送                               |
| 启用竞技场订阅     | 启用战斗竞技场排名变动推送                               |
| 启用公主竞技场订阅 | 启用公主竞技场排名变动推送                               |
| 删除竞技场订阅     | 删除竞技场排名变动推送绑定                               |
| 竞技场订阅状态     | 查看排名变动推送绑定状态                                 |
| 详细查询 uid       | 查询账号详细状态（绑定后无需输入uid）                    |
| 查询群数           | 查询bot所在群的数目                                      |
| 查询竞技场订阅数   | 查询绑定账号的总数量                                     |
| 清空竞技场订阅     | 清空所有绑定的账号(仅限主人)                             |

## 更新日志

2022-2-21：详细查询整合为两张精美图片，分别为个人资料卡图片以及支援界面图片

## 图片预览
![FQ~} OTM$L20L6DAEI~RN`K](https://user-images.githubusercontent.com/71607036/154993217-a123399a-f187-42d0-a1c9-1611591a33c6.PNG)

![4@{%Z%591B` YE1%}H0E7@1](https://user-images.githubusercontent.com/71607036/154993258-9ab18fae-aa27-480f-b380-68086ff92b84.jpg)
