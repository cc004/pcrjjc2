# pcrjjc2

本插件是[pcrjjc](https://github.com/lulu666lulu/pcrjjc)重置版，不需要使用其他后端api，但是需要自行配置客户端  

**本项目基于AGPL v3协议开源**

## 不遵守协议的耻辱柱
- **[@watermellye](https://github.com/watermellye)**

## 配置方法

0. (可选)配置bot发送验证码链接时用到的插件自带的验证网页地址，config为机器人的配置文件__bot__.py所配置的属性，不配置则访问4.ipw.cn来获取IP地址

配置示例

```python
PORT = 8080  # 配置已有，默认即可
IP = '1.2.3.4'  # 设置你的服务器IP,推荐添加
PUBLIC_ADDRESS = 'example.com:8080'  # 设置能访问到bot的域名或者域名端口组合,如果有推荐添加
```

1. 克隆本仓库：

   ```
   git clone https://github.com/cc004/pcrjjc2.git
   ```

2. 更改account.json内的account和password为你的bilibili账号的用户名和密码, admin为管理员的qq，用来接受bilibili验证码进行登录

3. 机器人登录需要验证码时会将链接形式私聊发给admin，这时你需要点进链接正确验证，如果成功，将会出现如下的内容：  
   `
     validate=c721fe67f0196d7defad7245f6e58d62
     seccode=c721fe67f0196d7defad7245f6e58d62|jordan
     `  
     此时，你需要将验证结果发给机器人，通过指令`/pcrval c721fe67f0196d7defad7245f6e58d62`即可完成验证（~~测试的时候似乎私聊没反应？私聊没反应的话就在群里发也可以，反正不泄露密码，大概率是程序没写好~~已修复 感谢 @assassingyk ）

4. account.json里面的platform和channel分别代表android和b服，emmm最好别改，改了我也不知道可不可以用

5. 安装依赖：

   ```
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

6. 在`create_img.py`文件中更改你所在的服务器名称

   ```
   # 设置服务器名称
   server_name = 'bilibili官方服务器'
   ```

7. 台服请使用**pcrjjc3-tw**：

   **pcrjjc3-tw:** [由pcrjjc2修改而来的台服竞技场查询插件，额外支持了多服查询 (github.com)](https://github.com/azmiao/pcrjjc3-tw)

8. 如果想推送全部排名变化（而不仅仅是上升排名变化），请切换到分支`notice-all`：

   ```
   # 直接克隆仓库的notice-all分支
   git clone https://github.com/cc004/pcrjjc2.git -b notice-all
   
   # 或者在克隆本仓库后切换到notice-all分支
   git checkout notice-all
   ```

9. **注意事项：**

- 若运行过程中出现`TypeError: __init__() got an unexpected keyword argument 'strict_map_key'`报错，为依赖问题，请在终端中进行如下操作，一行一行依次复制执行，过程中提示是否卸载，选择Y：

   ```
   pip uninstall msgpack_python
   pip uninstall msgpack
   pip install msgpack~=1.0.2
   ```

- 本插件仅适配新版星乃（hoshinobot），如果出现头像框等功能报错，请更新星乃本体。

- 提示版本更新失败的时候请删除version.txt并将pcrclient.py中`version`的初始值改为当前app版本号
## 命令

| 关键词             | 说明                                                         |
| ------------------ | ------------------------------------------------------------ |
| 竞技场绑定 uid     | 绑定竞技场排名变动推送，默认双场均启用，仅排名降低时推送     |
| 竞技场查询 uid     | 查询竞技场简要信息（绑定后无需输入uid）                      |
| 停止竞技场订阅     | 停止战斗竞技场排名变动推送                                   |
| 停止公主竞技场订阅 | 停止公主竞技场排名变动推送                                   |
| 启用竞技场订阅     | 启用战斗竞技场排名变动推送                                   |
| 启用公主竞技场订阅 | 启用公主竞技场排名变动推送                                   |
| 竞技场历史         | 查询战斗竞技场变化记录（战斗竞技场订阅开启有效，可保留10条） |
| 公主竞技场历史     | 查询公主竞技场变化记录（公主竞技场订阅开启有效，可保留10条） |
| 删除竞技场订阅     | 删除竞技场排名变动推送绑定                                   |
| 竞技场订阅状态     | 查看排名变动推送绑定状态                                     |
| 详细查询 uid       | 查询账号详细状态（绑定后无需输入uid）                        |
| 查询群数           | 查询bot所在群的数目                                          |
| 查询竞技场订阅数   | 查询绑定账号的总数量                                         |
| 查询头像框         | 查看自己设置的详细查询里的角色头像框                         |
| 更换头像框         | 更换详细查询生成的头像框，默认彩色                           |
| 清空竞技场订阅     | 清空所有绑定的账号(仅限主人)                                 |

## 更新日志

2022-07-13：多端适配优化，可用多go-cqhttp端接入同一个hoshinobot后端

2022-03-27：新增自定义头像框功能

2022-03-26：竞技场历史记录查询 #74

2022-02-21：详细查询整合为两张精美图片，分别为个人资料卡图片以及支援界面图片

## 图片预览
![FQ~} OTM$L20L6DAEI~RN`K](https://user-images.githubusercontent.com/71607036/154993217-a123399a-f187-42d0-a1c9-1611591a33c6.PNG)

![4@{%Z%591B` YE1%}H0E7@1](https://user-images.githubusercontent.com/71607036/154993258-9ab18fae-aa27-480f-b380-68086ff92b84.jpg)
