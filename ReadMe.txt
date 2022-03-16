工具有四个文件：
1. requirements.txt: python 依赖包列表文件
2. spirit.py: 主要键盘精灵的运行文件
3. config.json: 配置文件
4. start.bat: 启动精灵，客户如果使用anaconda等虚拟环境，可直接修改该文件

首次使用流程：
1. 需要设置防止windows系统及客户端锁屏
2. 安装好python之后，使用pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/  命令通过阿里云镜像安装相关依赖；
3. 打开config.json配置文件，按需修改配置。其中每项配置含义为：
   file_path：需要扫描的文件名及路径，客户需保证每日第一次启动精灵程序时清空上一天文件
   max_file_len： 需扫描文件可能的最大大小，默认4096字节，大约可以有400条合约
   scan_gap：扫描间隔，单位是秒，默认设置0.1s(100ms)
   defend_screen_lock：是否需要防止锁屏，如果系统设置了电脑不锁屏，则该项可改成False(防锁屏原理是每隔一分钟会模拟按下音量调整键)
4. 启动客户端，打开相应页面
5. 执行命令python spirit.py，或双击start.bat启动精灵，按键精灵会在盘后15：30自动退出

注意事项：
1. 用户需保证每日首次启动前，清空上一交易日合约，防止重复下单
2. 精灵运行过程中，会每日产生一个临时缓存文件（如20211119.txt），用于存储当日通过按键精灵操作过的合约，防止重启之后重复操作。如果需要重新录入之前的合约，可删除或修改该文件后重启程序