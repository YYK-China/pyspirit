import win32con
import win32gui
import win32api
import win32clipboard
import pyautogui
import time
import os
import traceback
import json
import logging

pyautogui.FAILSAFE = False

# 配置
# 扫描文件路径
blk_file_path = './a.txt'

frame_title = '******'  # 根据实际情况设置窗口名称，后续根据窗口名称找窗口句柄并操作
frame_class = '******'  # 根据实际情况设置窗口类名，后续根据窗口类名找窗口句柄并操作

# 下面配置一般不需要改
max_file_len = 4096  # 文件最大大小
cache_file_path = './'  # 缓存文件路径，缓存文件会记录每日已扫合约，防止重启后重新扫描下单。如需重复下单，可以删除里面内容
scan_gap = 0.1  # 扫描时间间隔

last_press_vol_time = time.time()
last_press_vol_key = 1  # 1up,-1down
is_defend_screen_lock = False


# 根据类名和title查找窗口
def win_active2(base_class, title):
    hwnd = win32gui.FindWindow(base_class, title)
    if hwnd:
        if win32gui.GetActiveWindow() != hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)  # SW_SHOWDEFAULT 默认大小，SW_SHOWMAXIMIZED 最大化显示
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
            pyautogui.press('f9', _pause=False)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
        else:
            logging.info('窗口已激活')
        return hwnd
    else:
        return None


# 用于解析BLK文件
class BLKFileDecoder:
    def __init__(self):
        self.content = bytes()
        pass

    def read(self, file: str):
        try:
            with open(file, 'rb') as fp:
                self.content = fp.read(max_file_len)
                # print(len(self.content))
                return True
        except IOError:
            exception_info = traceback.format_exc()
            print('Exception {}'.format(exception_info))
            print("无法打开BLK文件:", file)
            return False

    def decode(self):
        if not self.content.endswith(b'\x00\x00\x00\x00'):
            print('文件未正常结尾')
            return {}
        bs = self.content[4:].split(b'\x00\x00\x00\x00')
        return [s.decode('utf=8') for s in bs if s]


# 用于解析CSV文件
class CsvFileDecoder:
    def __init__(self):
        self.content = ''
        pass

    def read(self, file: str):
        try:
            with open(file, 'r') as fp:
                self.content = fp.read(max_file_len)
                # print(len(self.content))
                return True
        except IOError:
            return False

    def decode(self):
        if not self.content.endswith(',') and self.content:
            print('文件未正常结尾')
            return {}
        bs = self.content.split(',')
        return [s for s in bs if s]


# 用于过滤重复合约
class SymbolSet:
    def __init__(self):
        self.symbols = {}
        self.fp = None
        self.t_date = time.strftime('%Y%m%d')
        pass

    def init(self):
        try:
            self.fp = open(cache_file_path + self.t_date + '.txt', 'a+')
            self.fp.seek(0)
            buff = self.fp.read(max_file_len)
            symbols = buff.split(',')
            self.symbols = {s for s in symbols if s}
            return True
        except IOError:
            exception_info = traceback.format_exc()
            print('Exception {}'.format(exception_info))
            print("打开缓存文件失败")
            return False

    def diff_symbols(self, ns):
        return [x for x in ns if x not in self.symbols]

    def add_symbols(self, ns):
        self.symbols.update(ns)
        for x in ns:
            self.fp.write(x + ',')
            self.fp.flush()


# 模拟按键
def type_action(ns):
    try:
        ss = ','.join(ns)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(ss)
        win32clipboard.CloseClipboard()
        hwd = win_active2(frame_class, frame_title)
        if not hwd:
            print('未找到窗口，无法操作...')
            logging.error('未找到窗口，无法操作...')
            return False
        # win32gui.SendMessage(g_hwd, win32con.WM_ACTIVATE, 0, 0)
        pyautogui.press('f7', _pause=False)
        # pyautogui.press('f7')
        logging.info('press F7...')
        # pyautogui.typewrite(ss,_pause=False)
        logging.info('press paste...')
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.press('f8', _pause=False)
        # pyautogui.press('f8')
        logging.info('press F8...')
        return True
    except Exception as e:
        exception_info = traceback.format_exc()
        print('Exception {}'.format(exception_info))
        logging.error('exception occured: {}'.format(exception_info))
        return False


# 防止锁屏，原理是模拟调整音量
def defend_screen_lock():
    global last_press_vol_key
    t_now = time.time()
    key = 'volumedown' if last_press_vol_key == 1 else 'volumeup'
    last_press_vol_key *= -1
    # print(key)
    pyautogui.press(key)


def check_window():
    hwd = win32gui.FindWindow(frame_class, frame_title)
    if hwd:
        print('找到客户端窗口，句柄为：{}'.format(hwd))
        logging.info('找到客户端窗口，句柄为：{}'.format(hwd))
        win_active2(frame_class, frame_title)
    else:
        print('[WARN]无法找到客户端')
        logging.warning('无法找到客户端')

if __name__ == '__main__':

    # 初始化日志
    log_name = 'spirit' + time.strftime('%Y%m%d') + '.txt'
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=log_name, format=LOG_FORMAT, level=logging.NOTSET)

    # 读取配置文件
    master_para = json.load(open(os.path.abspath("./config.json")))
    blk_file_path = master_para['file_path']

    # 下面配置一般不需要改
    max_file_len = master_para['max_file_len']  # 文件最大大小
    cache_file_path = './'  # 缓存文件路径，缓存文件会记录每日已扫合约，防止重启后重新扫描下单。如需重复下单，可以删除里面内容
    scan_gap = master_para['scan_gap']  # 扫描时间间隔
    is_defend_screen_lock = master_para['defend_screen_lock'] == 'True'
    logging.info('config para is {}'.format(master_para))

    symbols = SymbolSet()
    if not symbols.init():
        print('初始化缓存失败！')
        logging.error('初始化缓存失败！')
        os._exit(-1)
    decoder = CsvFileDecoder()

    exception_count = 0
    logging.info('started...')
    check_window()

    # 循环扫描，盘后会自动退出
    while True:
        t_now = int(time.strftime('%H%M%S'))
        if t_now > 153000:
            print('盘后时间，进程将退出')
            logging.error('盘后时间，进程将退出')
            os._exit(0)

        if decoder.read(blk_file_path):
            ns = decoder.decode()
            codes = symbols.diff_symbols(ns)
            if codes:  # 如果有新合约
                last_press_vol_time = time.time()
                print('新合约列表有：{}，时间：{}'.format(codes, t_now))
                logging.info('新合约列表有：{}，时间：{}'.format(codes, t_now))
                t_begin = time.time()
                if not type_action(codes):  # 如果有异常，且超过10次，程序退出
                    exception_count += 1
                    if exception_count > 10:
                        print('异常次数达到10次，将要退出！')
                        logging.info('异常次数达到10次，将要退出！')
                        break
                    else:
                        continue
                exception_count = 0
                t_cost = time.time() - t_begin
                print('总条数:{}，总耗时:{}, 平均耗时:{}'.format(len(codes), t_cost, t_cost / len(codes)))
                logging.info('总条数:{}，总耗时:{}, 平均耗时:{}'.format(len(codes), t_cost, t_cost / len(codes)))
                symbols.add_symbols(codes)

                time.sleep(scan_gap)  # 防止两次操作太快
                continue
                pass
            pass

        # 解析文件失败，或没有新合约时，打印运行信息，检查窗口
        t_now = time.time()
        if t_now - last_press_vol_time > 60:
            last_press_vol_time = t_now
            print("[{}]运行中....".format(time.strftime('%H:%M:%S')))
            check_window()
            if is_defend_screen_lock:
                defend_screen_lock()  # 防止锁屏

        time.sleep(scan_gap)
