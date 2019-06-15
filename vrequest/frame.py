
import requests

import os
import re
import sys
import json
import time
import shutil
import tempfile
import traceback
import tkinter
import inspect
import urllib.parse as ps
import tkinter.messagebox
from tkinter import ttk
from tkinter import scrolledtext
from tkinter.font import Font
from tkinter.simpledialog import askstring

try:
    from .root import DEFAULTS_HEADERS
except:
    from root import DEFAULTS_HEADERS

Text = scrolledtext.ScrolledText
#Text = tkinter.Text
Label = ttk.Label
Button = ttk.Button
Combobox = ttk.Combobox
Entry = ttk.Entry
Checkbutton = tkinter.Checkbutton

# 测试两种 Frame 效果
# Frame = ttk.Frame # ttk.Frame 没有 highlightthickness 这个参数
Frame = tkinter.Frame

frame_setting = {}

pdx = 0
pdy = 0
lin = 0

def request_window(setting=None):
    fr = Frame()
    ft = Font(family='Consolas',size=10)

    def change_method(*a):
        method = cbx.get()
        if method == 'POST':
            temp_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.BOTTOM)
        elif method == 'GET':
            temp_fr2.pack_forget()

    def test_code(*a):
        from .tab import create_test_code
        create_test_code()

    def scrapy_code(*a):
        from .tab import create_scrapy_code
        create_scrapy_code()


    def send_req(*a):
        from .tab import send_request
        send_request()

    temp_fr0 = Frame(fr)
    methods = ('GET','POST')
    cbx = Combobox(temp_fr0,width=10,state='readonly')
    cbx['values'] = methods     # 设置下拉列表的值
    cbx.current(0)
    cbx.pack(side=tkinter.RIGHT)
    cbx.bind('<<ComboboxSelected>>', change_method)
    temp_fr0.pack(fill=tkinter.X)
    btn1 = Button(temp_fr0, text='发送请求[Ctrl+r]', command=send_req)
    btn1.pack(side=tkinter.RIGHT)
    lab1 = Label(temp_fr0, text='请尽量发送请求后生成代码，那样会有更多功能：')
    lab1.pack(side=tkinter.LEFT)
    btn6 = Button(temp_fr0, text='生成[requests]代码[Alt+c]', command=test_code)
    btn6.pack(side=tkinter.LEFT)
    btn7 = Button(temp_fr0, text='生成[scrapy]代码[Alt+s]', command=scrapy_code)
    btn7.pack(side=tkinter.LEFT)

    temp_fr1 = Frame(fr,highlightthickness=lin)
    temp_fold_fr1 = Frame(temp_fr1)
    temp_fold_fr2 = Frame(temp_fr1)
    lb1 = Label (temp_fold_fr1,text='url')
    tx1 = Text  (temp_fold_fr1,height=1,width=1,font=ft)
    lb1.pack(side=tkinter.TOP)
    tx1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP,padx=pdx,pady=pdy)

    lb2 = Label (temp_fold_fr2,text='headers')
    tx2 = Text  (temp_fold_fr2,height=1,width=1,font=ft)
    lb2.pack(side=tkinter.TOP)
    tx2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP,padx=pdx,pady=pdy)
    temp_fold_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)
    temp_fold_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)
    temp_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)


    temp_fr2 = Frame(fr,highlightthickness=lin)
    lb3 = Label (temp_fr2,text='body')
    tx3 = Text  (temp_fr2,height=1,width=1,font=ft)
    lb3.pack(side=tkinter.TOP)
    tx3.pack(fill=tkinter.BOTH,expand=True,padx=pdx,pady=pdy)
    if setting and setting.get('method') == 'POST':
        cbx.current(methods.index('POST'))
        temp_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.BOTTOM)

    if setting:
        tx1.insert(0.,setting['url'].strip())
        tx2.insert(0.,setting['headers'].strip())
        tx3.insert(0.,setting['body'].strip())
    else:
        tx2.insert(0.,DEFAULTS_HEADERS.strip())

    frame_setting[fr] = {}
    frame_setting[fr]['type'] = 'request'
    frame_setting[fr]['fr_method'] = cbx
    frame_setting[fr]['fr_url'] = tx1
    frame_setting[fr]['fr_headers'] = tx2
    frame_setting[fr]['fr_body'] = tx3
    return fr


def response_window(setting=None):

    '''
    这里的 setting 结构应该就是一个请求信息的数据结构
    并且应该是整理好数据类型的字典，在这里请求任务结束之后返回的数据
    就按照展示结构放在 response 的结构框架里面。
    url     :str
    method  :str
    headers :dict
    body    :str
    '''

    def insert_txt(fr_txt, txt):
        fr_txt.delete(0.,tkinter.END)
        fr_txt.insert(0.,re.sub('[\uD800-\uDBFF][\uDC00-\uDFFF]|[\U00010000-\U0010ffff]','',txt))

    doc0 = '''列表解析路径方式
冒号后面配置的的内容为 xpath
<xpath:>
*组合功能！
如果先使用了 “分析xpath” 功能后解析到路径
那么使用该功能时会自动弹出选择窗口
选择窗中的内容为自动解析xpath中解析出的 xpath
'''

    doc1 = '''纯文字内容解析
解析某个 xpath 路径下面的所有文字字符串，默认是 //html 路径下的所有文字
<normal_content://html>
'''

    doc2 = '''根据字符串自动分析 xpath 路径
一般用于列表形式的路径
通常来说这个功能针对简单的网页结构还勉强有用，并非一定能够解析
所以一些比较复杂的网页或许还是需要考虑自省分析xpath。

冒号后面配置需要处理的字符串
多个字符串可以通过空格分隔
eg.:
    <auto_list_xpath:白天 黑夜>
不写则为查找所有 "string(.)" (xpath语法)
能解析出含有非空字符串的内容路径
'''

    doc3 = '''简单分析json数据内容
找出最长的list进行初步的迭代分析，并给出分析结果在输出框
<auto_list_json:>
'''

    doc4 = '''生成scrapy代码
如果存在 “解析xpath”、“自动json” 或 “获取纯文字” 状态
则会在生成代码中包含相应的代码
'''

    doc5 = '''生成requests代码
如果存在 “解析xpath”、“自动json” 或 “获取纯文字” 状态
则会在生成代码中包含相应的代码
'''

    def document(*a):
        method = cbx.get()
        if methods.index(method) == 0:
            insert_txt(tx3,doc0)
        if methods.index(method) == 1:
            insert_txt(tx3,doc1)
        if methods.index(method) == 2:
            insert_txt(tx3,doc2)
        if methods.index(method) == 3:
            insert_txt(tx3,doc3)
        if methods.index(method) == 4:
            insert_txt(tx3,doc4)
        if methods.index(method) == 5:
            insert_txt(tx3,doc5)
        switch_show(onlyshow=True)

    fr = Frame()
    ft = Font(family='Consolas',size=10)
    def switch_show(*a, onlyshow=False):
        try:
            temp_fold_fr2.pack_info()
            packed = True
        except:
            packed = False
        if packed:
            if not onlyshow:
                temp_fold_fr2.pack_forget()
        else:
            temp_fold_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)

    def html_pure_text(*a):
        from .tab import get_html_pure_text
        get_html_pure_text()

    def xpath_elements(*a):
        from .tab import get_xpath_elements
        get_xpath_elements()

    def auto_xpath(*a):
        from .tab import get_auto_xpath
        get_auto_xpath()

    def auto_json(*a):
        from .tab import get_auto_json
        get_auto_json()

    def test_code(*a):
        from .tab import create_test_code
        create_test_code()

    def scrapy_code(*a):
        from .tab import create_scrapy_code
        create_scrapy_code()

    temp_fr0 = Frame(fr)
    lab1 = Label(temp_fr0, text='功能说明：')
    lab1.pack(side=tkinter.LEFT)
    methods = ('(Alt+x) 解析xpath','(Alt+d) 获取纯文字','(Alt+f) 分析xpath','(Alt+z) 自动json', '(Alt+s) 生成 scrapy代码', '(Alt+c) 生成 requests代码')
    cbx = Combobox(temp_fr0,width=18,state='readonly')
    cbx['values'] = methods     # 设置下拉列表的值
    cbx.current(0)
    cbx.pack(side=tkinter.LEFT)
    cbx.bind('<<ComboboxSelected>>', document)
    temp_fr0.pack(fill=tkinter.X)
    btn3 = Button(temp_fr0, text='分析xpath', command=auto_xpath)
    btn3.pack(side=tkinter.LEFT)
    btn4 = Button(temp_fr0, text='解析xpath', command=xpath_elements)
    btn4.pack(side=tkinter.LEFT)
    btn2 = Button(temp_fr0, text='获取纯文字', command=html_pure_text)
    btn2.pack(side=tkinter.LEFT)
    btn5 = Button(temp_fr0, text='自动json', command=auto_json)
    btn5.pack(side=tkinter.LEFT)
    btn1 = Button(temp_fr0, text='显示/隐藏配置', command=switch_show)
    btn1.pack(side=tkinter.RIGHT)
    btn6 = Button(temp_fr0, text='生成[requests]代码', command=test_code)
    btn6.pack(side=tkinter.RIGHT)
    btn7 = Button(temp_fr0, text='生成[scrapy]代码', command=scrapy_code)
    btn7.pack(side=tkinter.RIGHT)

    temp_fr1 = Frame(fr,highlightthickness=lin)
    temp_fold_fr1 = Frame(temp_fr1)
    lb1 = Label (temp_fold_fr1,text='HTML文本展示')
    tx1 = Text  (temp_fold_fr1,height=1,width=1,font=ft,wrap='none')
    lb1.pack(side=tkinter.TOP)
    tx1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP,padx=pdx,pady=pdy)

    temp_fold_fr2 = Frame(temp_fr1)
    temp_fold_fold_fr1 = Frame(temp_fold_fr2)
    temp_fold_fold_fr2 = Frame(temp_fold_fr2)
    lb2 = Label (temp_fold_fold_fr1,text='配置数据')
    tx2 = Text  (temp_fold_fold_fr1,height=1,width=1,font=ft)
    lb2.pack(side=tkinter.TOP)
    tx2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP,padx=pdx,pady=pdy)
    lb3 = Label (temp_fold_fold_fr2,text='执行说明')
    tx3 = Text  (temp_fold_fold_fr2,height=1,width=1,font=ft)
    lb3.pack(side=tkinter.TOP)
    tx3.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP,padx=pdx,pady=pdy)
    temp_fold_fold_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)
    temp_fold_fold_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)
    temp_fold_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)
    # temp_fold_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)
    temp_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)

    temp_fr2 = Frame(fr,highlightthickness=lin)
    lb4 = Label (temp_fr2,text='解析内容[Esc 开启/关闭解析显示]')
    tx4 = Text  (temp_fr2,height=1,width=1,font=ft)
    lb4.pack(side=tkinter.TOP)
    tx4.pack(fill=tkinter.BOTH,expand=True,padx=pdx,pady=pdy)
    #temp_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.BOTTOM)

    frame_setting[fr] = {}
    frame_setting[fr]['type'] = 'response'
    frame_setting[fr]['fr_setting'] = setting # 用于生成代码时候需要调用到
    frame_setting[fr]['fr_html_content'] = tx1
    frame_setting[fr]['fr_local_set'] = tx2 # 当前解析脚本的方法类型以及配置
    frame_setting[fr]['fr_local_info'] = tx3 # 一个辅助说明的文本空间
    frame_setting[fr]['fr_parse_info'] = tx4
    frame_setting[fr]['fr_temp2'] = temp_fr2 # 解析输出的 Text 框，这里用外部frame是为了挂钩esc按键显示/关闭该窗口

    # 检查数据格式
    # 非常坑，后续再考虑，现在只考虑 ['utf-8','gbk'] 两种
    # def parse_content_type(content, types=['utf-8','gbk']):
    #     itype = iter(types)
    #     while True:
    #         try:
    #             tp = next(itype)
    #             content = content.decode(tp)
    #             return tp, content
    #         except StopIteration:
    #             try:
    #                 import chardet
    #                 tp = chardet.detect(content)['encoding']
    #                 types.append(tp)
    #                 content = content.decode(tp)
    #                 return tp, content
    #             except:
    #                 raise TypeError('not in {}'.format(types))
    #         except:
    #             continue

    # 统一数据格式
    def format_content(content):
        if type(content) is bytes:
            try:
                content = content.decode('utf-8')
                typ = 'utf-8'
            except:
                try:
                    content = content.decode('gbk')
                    typ = 'gbk'
                except:
                    content = content.decode('utf-8',errors='ignore')
                    typ = 'utf-8 ignore'
            insert_txt(tx3, '解析格式：{}'.format(typ))
            return typ,content
        else:
            einfo = 'type:{} is not in type:[bytes]'.format(type(content))
            raise TypeError(einfo)

    def quote_val(url):
        import urllib
        for i in re.findall('=([^=&]+)',url):
            url = url.replace(i,'{}'.format(urllib.parse.quote(i)))
        return url

    tp = None
    if setting is not None:
        method  = setting.get('method')
        url     = setting.get('url')
        headers = setting.get('headers')
        body    = setting.get('body')
        try:
            if method == 'GET':
                s = requests.get(quote_val(ps.unquote(url)),headers=headers,verify=False)
                tp,content = format_content(s.content)
                insert_txt(tx1, content)
            elif method == 'POST':
                # 这里的post 里面的body 暂时还没有进行处理
                s = requests.post(quote_val(ps.unquote(url)),headers=headers,data=body,verify=False)
                tp,content = format_content(s.content)
                insert_txt(tx1, content)
        except:
            einfo = traceback.format_exc()
            tkinter.messagebox.showinfo('Error',einfo)
            raise
            # insert_txt(tx1, traceback.format_exc())

    frame_setting[fr]['fr_parse_type'] = tp
    return fr




# 暂时考虑用下面的方式来试着挂钩函数执行的状态。
# 不过似乎还是有些漏洞，先就这样，后面再补充完整。
import sys
__org_stdout__ = sys.stdout
__org_stderr__ = sys.stderr
class stdhooker:
    def __init__(self, hook=None, style=None):
        if hook.lower() == 'stdout':
            self.__org_func__ = __org_stdout__
        elif hook.lower() == 'stderr':
            self.__org_func__ = __org_stderr__
        else:
            raise 'stdhooker init error'
        self.cache = ''
        self.style = style
        self.predk = {}

    def write(self,text):
        self.logtx = get_tx()
        if self.logtx not in self.predk:
            self.predk[self.logtx] = 0

        self.cache += text
        if '\n' in self.cache:
            _text = self.cache.rsplit('\n',1)
            self.cache = '' if len(_text) == 1 else _text[1]
            _text_ = _text[0] + '\n'
            if self.logtx:
                self.logtx.insert(tkinter.END, _text_)
                self.logtx.see(tkinter.END)
                self.logtx.update()

    def flush(self):
        self.__org_func__.flush()

def get_tx():
    for i in inspect.stack():
        if '__very_unique_cd__' in i[0].f_locals:
            return i[0].f_locals['cd']

sys.stdout = stdhooker('stdout',style='normal')



# 生成代码临时放在这里
def code_window(setting=None):
    fr = Frame()
    ft = Font(family='Consolas',size=10)

    def _execute_code(*a):
        from .tab import execute_code
        execute_code()

    btn1 = Button(fr, text='执行代码 [Alt+v]', command=_execute_code)
    btn1.pack(side=tkinter.TOP)
    tx = Text(fr,height=1,width=1,font=ft)
    cs = setting.get('code_string')
    if cs:
        tx.delete(0.,tkinter.END)
        tx.insert(0.,cs)
    tx.pack(fill=tkinter.BOTH,expand=True,padx=pdx,pady=pdy)

    temp_fr2 = Frame(fr,highlightthickness=lin)
    lb = Label (temp_fr2,text='执行结果[Esc 显示/隐藏执行结果]')
    cd = Text  (temp_fr2,height=1,width=1,font=ft)
    lb.pack(side=tkinter.TOP)
    cd.pack(fill=tkinter.BOTH,expand=True,padx=pdx,pady=pdy)

    def execute_func():
        __very_unique_cd__ = None
        nonlocal cd
        cd.delete(0.,tkinter.END)
        td = tempfile.mkdtemp()
        tf = os.path.join(td,'temp.py')
        cs = tx.get(0.,tkinter.END)
        with open(tf,'w',encoding='utf-8') as f:
            f.write(cs)
        s = sys.executable
        s = s + ' ' + tf
        import subprocess
        p = subprocess.Popen(s, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, encoding='utf-8')
        print('============================== start ==============================')
        for line in iter(p.stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break
        print('==============================  end  ==============================')
        p.wait()
        p.stdout.close()
        shutil.rmtree(td)

    frame_setting[fr] = {}
    frame_setting[fr]['type'] = 'code'
    frame_setting[fr]['execute_func'] = execute_func
    frame_setting[fr]['fr_temp2'] = temp_fr2 # 代码执行框，这里仍需挂钩esc按键显示/关闭该窗口

    try:
        from idlelib.colorizer import ColorDelegator
        from idlelib.percolator import Percolator
        p = ColorDelegator()
        Percolator(tx).insertfilter(p)
    except:
        traceback.print_exc()

    return fr


# 生成代码临时放在这里
def scrapy_code_window(setting=None):
    fr = Frame()
    ft = Font(family='Consolas',size=10)

    def _execute_scrapy_code(*a):
        from .tab import execute_scrapy_code
        execute_scrapy_code()

    def save_project_in_desktop(*a):
        name = askstring('项目名称','请输入项目名称，尽量小写无空格。')
        if not name: return
        desktop = os.path.join(os.path.expanduser("~"),'Desktop\\{}'.format(name))
        if not os.path.isdir(desktop):
            with open(script,'w',encoding='utf-8') as f:
                f.write(tx.get(0.,tkinter.END))
            shutil.copytree(scrapypath, desktop)
            toggle = tkinter.messagebox.askokcancel('创建成功',
                            '创建成功\n\n'
                            '注意！！！\n注意！！！\n注意！！！\n\n是否关闭当前工具并启动拷贝出的 shell 地址执行测试。\n'
                            '如果是，启动第一次shell测试后，后续需要再执行新的测试时请输入:\nscrapy crawl v\n\n'
                            '{}'.format(desktop))
            if not toggle:
                return
            # cmd = 'start explorer {}'.format(desktop) # 打开文件路径
            # os.system(cmd)
            pyscript = os.path.join(os.path.split(sys.executable)[0],'Scripts')
            toggle = any([True for i in os.listdir(pyscript) if 'scrapy.exe' in i.lower()])
            if toggle:
                scrapyexe = os.path.join(pyscript,'scrapy.exe')
                output = '-o {}'.format(et.get()) if va.get() else ''
                cwd = os.getcwd()
                os.chdir(desktop)
                try:
                    cmd = 'start powershell -NoExit "{}" crawl v -L {} {}'.format(scrapyexe,cbx.get(),output)
                    os.system(cmd)
                except:
                    cmd = 'start cmd /k "{}" crawl v -L {} {}'.format(scrapyexe,cbx.get(),output)
                    os.system(cmd)
                os.chdir(cwd)
                cwd = os.getcwd()             
            else:
                einfo = 'cannot find scrapy'
                tkinter.messagebox.showinfo('Error',einfo)
                raise EnvironmentError(einfo)
            exit()
        else:
            tkinter.messagebox.showwarning('文件夹已存在','文件夹已存在')

    home = os.environ.get('HOME')
    home = home if home else os.environ.get('HOMEDRIVE') + os.environ.get('HOMEPATH')
    filename = '.vscrapy'
    scrapypath = os.path.join(home,filename)
    scriptpath = os.path.join(scrapypath, 'v/spiders/')
    script = os.path.join(scriptpath, 'v.py')

    def local_collection(*a):
        def _show(*a, stat='show'):
            try:
                if stat == 'show': et.pack(side=tkinter.RIGHT)
                if stat == 'hide': et.pack_forget()
            except:
                pass
        _show(stat='show') if va.get() else _show(stat='hide')


    def pprint(*a):
        __org_stdout__.write(str(a)+'\n')
        __org_stdout__.flush()
    temp_fr0 = Frame(fr)
    va = tkinter.IntVar()
    rb = Checkbutton(temp_fr0,text='本地执行是否收集数据:',variable=va,command=local_collection)
    rb.deselect()
    et = Entry (temp_fr0,width=60)
    
    ltime = '%04d%02d%02d-%02d%02d%02d' % time.localtime()[:6]
    dtopfile = os.path.join('file:///' + os.path.expanduser("~"),'Desktop\\v{}.json'.format(ltime))
    et.insert(0,dtopfile)
    bt2 = Button(temp_fr0,text='拷贝项目文件到桌面',command=save_project_in_desktop)
    bt2.pack(side=tkinter.LEFT)
    btn1 = Button(temp_fr0, text='执行本地代码 [Alt+w]', command=_execute_scrapy_code)
    btn1.pack(side=tkinter.LEFT)
    cbx = Combobox(temp_fr0,width=10,state='readonly')
    cbx['values'] = ('DEBUG','INFO','WARNING','ERROR','CRITICAL')
    cbx.current(1)
    cbx.pack(side=tkinter.RIGHT)
    lab1 = Label(temp_fr0, text='本地日志等级:')
    lab1.pack(side=tkinter.RIGHT)
    def open_test(*a):
        cmd = 'start explorer {}'.format(scrapypath)
        os.system(cmd)
    bt1 = Button(temp_fr0,text='打开本地文件路径',command=open_test)
    bt1.pack(side=tkinter.RIGHT)
    rb.pack(side=tkinter.RIGHT)

    temp_fr1 = Frame(fr)
    temp_fr0.pack(fill=tkinter.X)
    temp_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)
    tx = Text(temp_fr1,height=1,width=1,font=ft)
    cs = setting.get('code_string')
    if cs:
        tx.delete(0.,tkinter.END)
        tx.insert(0.,cs)
    tx.pack(fill=tkinter.BOTH,expand=True,padx=pdx,pady=pdy)
    try:
        from idlelib.colorizer import ColorDelegator
        from idlelib.percolator import Percolator
        p = ColorDelegator()
        Percolator(tx).insertfilter(p)
    except:
        traceback.print_exc()

    def execute_func():
        if os.path.isdir(scriptpath):
            with open(script,'w',encoding='utf-8') as f:
                f.write(tx.get(0.,tkinter.END))
            pyscript = os.path.join(os.path.split(sys.executable)[0],'Scripts')
            toggle = any([True for i in os.listdir(pyscript) if 'scrapy.exe' in i.lower()])
            if toggle:
                scrapyexe = os.path.join(pyscript,'scrapy.exe')
                output = '-o {}'.format(et.get()) if va.get() else ''
                cwd = os.getcwd()
                os.chdir(scriptpath)
                try:
                    cmd = 'start powershell -NoExit "{}" crawl v -L {} {}'.format(scrapyexe,cbx.get(),output)
                    os.system(cmd)
                except:
                    cmd = 'start cmd /k "{}" crawl v -L {} {}'.format(scrapyexe,cbx.get(),output)
                    os.system(cmd)
                os.chdir(cwd)
            else:
                einfo = 'cannot find scrapy'
                tkinter.messagebox.showinfo('Error',einfo)
                raise EnvironmentError(einfo)
        else:
            einfo = 'cannot find path: {}'.format(scriptpath)
            tkinter.messagebox.showinfo('Error',einfo)
            raise EnvironmentError(einfo)
    frame_setting[fr] = {}
    frame_setting[fr]['type'] = 'scrapy'
    frame_setting[fr]['execute_func'] = execute_func
    return fr








# 帮助文档
def helper_window():
    fr = Frame()
    ft = Font(family='Consolas',size=10)
    hp = '''
vrequest：
基于 requests 和 lxml 库的爬虫请求测试工具
用于快速发起请求，快速生成且能执行的基于 requests 和 lxml 的代码
也可以生成且能执行 scrapy 代码，不过由于scrapy库依赖过重，该工具不会依赖下载
若需要执行 scrapy 代码，需额外下载 scrapy。

请求窗口快捷键：
(Ctrl + r) 发送请求任务并保存
*(Alt + c) 生成请求代码(一般建议在请求后处理分析再生成代码，那样包含解析代码)
           HEADERS 窗口接受 “:” 或 “=” 分割
           BODY    窗口接受 “:” 或 “=” 分割
                   若是BODY窗口需要传字符串可以在字符串前后加英文双引号
*(Alt + s) 生成 scrapy 请求代码，格式化结构同上

响应窗口快捷键：
*(Alt + r) 打开一个空的响应标签(不常用)
(Alt + f) 智能解析列表路径，解析后使用 xpath 解析功能会自动弹出解析选择窗
(Alt + x) <代码过程> 使用 xpath 解析
(Alt + z) <代码过程> 智能提取 json 数据
(Alt + d) <代码过程> 获取纯文字内容
(Alt + c) 生成请求代码，有<代码过程>则生成代码中包含过程代码 [在js代码窗同样适用]
(Alt + s) 生成 scrapy 请求代码，有<代码过程>则生成代码中包含过程代码
(Esc)     开启/关闭 response 解析窗口

代码窗口快捷键：
(Alt + v) 代码执行 [在js代码窗同样适用]
(Esc)     开启/关闭 代码执行结果窗口 [在js代码窗同样适用]

scrapy 代码窗口快捷键：
(Alt + w) scrapy 代码执行

通用快捷键：
(Ctrl + q) 创建新的请求标签
(Ctrl + j) 创建 js 代码执行窗口
(Ctrl + e) 修改当前标签名字
(Ctrl + w) 关闭当前标签
(Ctrl + h) 创建帮助标签
(Ctrl + s) 保存当前全部请求配置(只能保存请求配置)

开源代码：
https://github.com/cilame/vrequest
'''
    temp_fr1 = Frame(fr,highlightthickness=lin)
    lb1 = ttk.Label(temp_fr1,font=ft,text=hp)
    lb1.pack()
    temp_fr1.pack()

    return fr



def exec_js_window(setting=None):
    '''
    这里可能会使用两到三种js的加载方式，并且，js2py能生成 python 的代码，可能需要考虑生成python代码的功能
    目前暂时没有完全实现
    '''
    fr = Frame()
    ft = Font(family='Consolas',size=10)

    # js代码转python代码
    def translate_js_js2py():
        jscode = txt1.get(0.,tkinter.END)
        try:
            import js2py
            js2pycode = js2py.translate_js(jscode)
            txt2.delete(0.,tkinter.END)
            txt2.insert(0.,js2pycode)
        except:
            e = traceback.format_exc()
            txt2.delete(0.,tkinter.END)
            txt2.insert(0.,e)

    def change_module(*a):
        tp = cbx.get().strip()
        btn_create_python_code['text'] = re.sub(r'\[[^\[\]+]*\]',tp,btn_create_python_code['text'])

    def translate_js():
        tp = cbx.get().strip()
        jscode = txt1.get(0.,tkinter.END)
        if 'execjs' in tp:
            pythoncode = """
#coding=utf-8
jscode = r'''
$^^$jscode$^^$
'''

import execjs
ctx = execjs.compile(jscode)
result = ctx.call('func',10,20) # 执行函数，需要传参函数将参从第二个开始依次排在方法名后面
# result = ctx.eval('func(22,33)')
print(result)
""".replace('$^^$jscode$^^$', jscode.strip()).strip()
        if 'js2py' in tp:
            pythoncode = """
#coding=utf-8
jscode = r'''
$^^$jscode$^^$
'''

import js2py
js = js2py.eval_js(jscode) # eval_js模式会自动将js代码执行后最后一个 var赋值的参数返回出来。
print(js)
""".replace('$^^$jscode$^^$', jscode.strip()).strip()
        txt2.delete(0.,tkinter.END)
        txt2.insert(0.,pythoncode)

    def exec_javascript(*a):
        __very_unique_cd__ = None
        nonlocal cd
        cd.delete(0.,tkinter.END)
        td = tempfile.mkdtemp()
        tf = os.path.join(td,'temp.py')
        cs = txt2.get(0.,tkinter.END)
        with open(tf,'w',encoding='utf-8') as f:
            f.write(cs)
        s = sys.executable
        s = s + ' ' + tf
        import subprocess
        p = subprocess.Popen(s, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, encoding='utf-8')
        print('============================== start ==============================')
        for line in iter(p.stdout.readline, ''):
            if line:
                print(line, end='')
            else:
                break
        print('==============================  end  ==============================')
        p.wait()
        p.stdout.close()
        shutil.rmtree(td)

    def _exec_javascript(*a):
        from .tab import show_code_log
        show_code_log()
        exec_javascript()

    def js_beautify(*a):
        try:
            import jsbeautifier
            jscode = txt1.get(0.,tkinter.END)
            btjscode = jsbeautifier.beautify(jscode)
            txt1.delete(0.,tkinter.END)
            txt1.insert(0.,btjscode)
        except ImportError as e:
            txt2.delete(0.,tkinter.END)
            txt2.insert(0.,e)
        except:
            einfo = traceback.format_exc() + \
            '\n\njs代码美化在一些极端的 eval 函数美化时会出现一些问题' + \
            '\n所以出现错误时可以考虑检查代码的 eval 函数的处理'
            txt2.delete(0.,tkinter.END)
            txt2.insert(0.,einfo)

    # 查看常用的js解析器的引入状态
    support_modules = ['js2py', 'execjs']
    def get_js_import_stat(support_modules):
        s = []
        def _temp(module):
            try:
                __import__(module)
                s.append('+ Enable Use [{}] js driver.'.format(module))
            except:
                s.append('- Unable Use [{}] js driver.'.format(module))
        for module in support_modules:
            _temp(module)
        return s
    import_stat = get_js_import_stat(support_modules)
    temp_fr0 = Frame(fr)
    temp_fr0.pack(fill=tkinter.X)
    import_modules = [i[i.find('['):i.rfind(']')+1] for i in import_stat if i.startswith('+')]
    if not import_modules:
        einfo = 'unfind any of {} module.'.format(support_modules)
        tkinter.messagebox.showinfo('Error',einfo)
        raise EnvironmentError(einfo)
    cbx = Combobox(temp_fr0,width=13,state='readonly')
    cbx['values'] = import_modules
    cbx.current(0)
    cbx.pack(fill=tkinter.X,side=tkinter.LEFT)
    cbx.bind('<<ComboboxSelected>>', change_module)

    btn_js_beautify = Button(temp_fr0,text='js代码美化',command=js_beautify)
    btn_js_beautify.pack(side=tkinter.LEFT)
    btn_create_python_code = Button(temp_fr0,text='生成python[]代码 [Alt+c]',command=translate_js)
    btn_create_python_code.pack(side=tkinter.LEFT)
    btn_translate_js = Button(temp_fr0,text='翻译成[js2py]代码',command=translate_js_js2py)
    btn_translate_js.pack(side=tkinter.LEFT)
    btn2 = Button(temp_fr0, text='[执行代码] <Alt+v>', command=_exec_javascript)
    btn2.pack(side=tkinter.RIGHT)


    temp_fr0 = Frame(fr)
    temp_fr0.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)
    temp_fr1 = Frame(temp_fr0)
    temp_fr1_1 = Frame(temp_fr1)
    temp_fr1_1.pack(side=tkinter.TOP)
    temp_fr1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.LEFT)
    txt1 = Text(temp_fr1,height=1,width=1,font=ft)
    lab1 = Label(temp_fr1_1,text='js代码')
    lab1.pack(side=tkinter.TOP)
    txt1.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)
    temp_fr2 = Frame(temp_fr0)
    temp_fr2_1 = Frame(temp_fr2)
    temp_fr2_1.pack(fill=tkinter.X,side=tkinter.TOP)
    temp_fr2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.RIGHT)
    lab1 = Label(temp_fr2_1,text='python代码')
    lab1.pack(side=tkinter.TOP)
    txt2 = Text(temp_fr2,height=1,width=1,font=ft)
    txt2.pack(fill=tkinter.BOTH,expand=True,side=tkinter.TOP)

    temp_fr3 = Frame(fr)
    lab3 = Label(temp_fr3, text='代码结果 [Esc 切换显示状态]')
    lab3.pack(side=tkinter.TOP)
    cd = Text(temp_fr3,font=ft)
    cd.pack(fill=tkinter.BOTH,expand=True)


    test_code = '''
// test_code
function func(a,b){
    return a+b
}

var a = 123;
'''.strip()
    txt1.insert(0.,test_code)


    change_module()
    try:
        from idlelib.colorizer import ColorDelegator
        from idlelib.percolator import Percolator
        p = ColorDelegator()
        Percolator(txt2).insertfilter(p) # txt2 是js2py生成的python代码，需要填色
    except:
        e = traceback.format_exc()
        txt2.delete(0.,tkinter.END)
        txt2.insert(0.,e)




    frame_setting[fr] = {}
    frame_setting[fr]['type'] = 'js'
    frame_setting[fr]['execute_func0'] = translate_js
    frame_setting[fr]['execute_func1'] = translate_js_js2py
    frame_setting[fr]['execute_func'] = exec_javascript
    frame_setting[fr]['import_stat'] = import_stat
    frame_setting[fr]['fr_temp2'] = temp_fr3 # 代码执行框，这里仍需挂钩esc按键显示/关闭该窗口
    return fr



def encode_window(setting=None):
    '''
    处理简单的加密编码对比
    '''
    fr = tkinter.Toplevel()
    fr.resizable(False, False)

    f0 = Frame(fr)
    f0.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=True)

    f0_ = Frame(fr)
    f0_.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=True)

    f1 = Frame(f0)
    f2 = Frame(f0)
    f1.pack(fill=tkinter.BOTH,expand=True)
    f2.pack(fill=tkinter.BOTH,expand=True)

    import hashlib
    import hmac
    algorithms = hashlib.algorithms_available

    ipadx   = 0
    ipady   = 0
    padx    = 1
    pady    = 1
    width   = 60
    sticky  = None#'NESW'
    ft = Font(family='Consolas',size=10)

    crow = 0
    ls = []
    di = {}
    allow = ['blake2b',
             'blake2s',
             'md4',
             'md5',
             'ripemd160',
             'sha',
             'sha1',
             'sha224',
             'sha256',
             'sha384',
             'sha3_224',
             'sha3_256',
             'sha3_384',
             'sha3_512',
             'sha512',
             'whirlpool']
    for idx,name in enumerate(sorted(algorithms)):
        if name not in allow: continue
        l,e = Label(f2,text=name,font=ft),Entry(f2,width=width,font=ft)
        di[name] = e
        l.grid(row=idx,column=0,ipadx=ipadx,ipady=ipady,padx=padx,pady=pady,sticky=sticky)
        e.grid(row=idx,column=1,ipadx=ipadx,ipady=ipady,padx=padx,pady=pady,sticky=sticky)

    def func(*a):
        def _show(*a, stat='show'):
            try:
                if stat == 'show': ss.pack(side=tkinter.LEFT)
                if stat == 'hide': ss.pack_forget()
            except:
                pass
        _show(stat='show') if va.get() else _show(stat='hide')

    f11 = Frame(f1)
    f11.pack(fill=tkinter.X)

    def _switch_case(*a):
        for name,ge in di.items():
            try:
                v = ge.get().upper() if ca.get() else ge.get().lower()
                ge.delete(0,tkinter.END)
                ge.insert(0,v)
            except:
                import traceback; traceback.print_exc()
                print('error',name)

    ca = tkinter.IntVar()
    rb = Checkbutton(f11,text='是否大写',variable=ca,command=_switch_case)
    rb.pack(side=tkinter.RIGHT)
    rb.deselect()

    ss = Entry(f11)
    va = tkinter.IntVar()
    rb = Checkbutton(f11,text='加盐',variable=va,command=func)
    rb.pack(side=tkinter.LEFT,padx=10)

    Label(f1,text='加密文本').pack(side=tkinter.LEFT,padx=10)
    ee = Entry(f1)
    ee.pack(side=tkinter.LEFT)

    def _encode_all(*a):
        salt = ss.get().encode() if va.get() else b''
        text = ee.get().encode()
        for name,ge in di.items():
            try:
                v = hmac.new(salt,text,name).hexdigest()
                v = v.upper() if ca.get() else v.lower()
                ge.delete(0,tkinter.END)
                ge.insert(0,v)
            except:
                import traceback; traceback.print_exc()
                print('error',name)

    Button(f1,text='加密全部',command=_encode_all).pack(side=tkinter.RIGHT)

    f1_ = Frame(f0_)
    f1_.pack(fill=tkinter.BOTH)
    f2_ = Frame(f0_)
    f2_.pack(fill=tkinter.BOTH,expand=True)

    lb_ = Label(f1_,text='compare(对比字符串)')
    lb_.pack(side=tkinter.LEFT,padx=10,pady=pady)
    et_ = Entry(f1_,width=30)
    et_.pack(side=tkinter.LEFT,padx=padx,pady=pady)

    import difflib
    def _diff_log(a, b):
        d = difflib.Differ()
        s = d.compare(a.splitlines(), b.splitlines())
        for i in s:
            print(i)

    def print(*a):
        txt.insert(tkinter.END,' '.join(map(str,a)) + '\n')

    def _analysis_diff(*a):
        txt.delete(0.,tkinter.END)
        it = []
        for name,ge in di.items():
            try:
                a, b = et_.get(), ge.get()
                s = difflib.SequenceMatcher(None, a.upper(), b.upper())
                q = s.find_longest_match(0, len(a), 0, len(b))
                if q.size>0:
                    it.append([name, a, b, q.size])
            except:
                import traceback; traceback.print_exc()
                print('error',name)

        cnt = 0
        for name,a,b,max_match in sorted(it,key=lambda max_match:-max_match[3])[:5]:
            cnt += 1
            s = difflib.SequenceMatcher(None, a.upper(), b.upper())
            print('max_match_len:{}'.format(max_match))
            print('len[compare]:{}'.format(len(a), ))
            print('len[{}]:{}'.format(name, len(b)))
            for match in sorted(s.get_matching_blocks(),key=lambda i:-i.size):
                if match.size:
                    v = a[match.a:match.a+match.size]
                    print('    [match.size:{}]  {}'.format(match.size, v))
            print('---------------')
        if not cnt:
            print('not match.')

    def _creat_code(*a):
        import pprint
        txt.delete(0.,tkinter.END)
        compare_str = et_.get().strip()
        code = '''
import hmac
import difflib

allow = \
$allow

salt = '' # 字符串/byte类型  盐（默认空）
text = '' # 字符串/byte类型  需要被加密的数据
upper = True


def encode_all(salt, text):
    salt = salt.encode() if type(salt) == str else salt
    text = text.encode() if type(text) == str else text
    for name in allow:
        v = hmac.new(salt,text,name).hexdigest()
        v = v.upper() if upper else v.lower()
        print('{:<10}{}'.format(name, v))


def compare_encode(salt, text, compare_str):
    salt = salt.encode() if type(salt) == str else salt
    text = text.encode() if type(text) == str else text
    it = []
    for name in allow:
        v = hmac.new(salt,text,name).hexdigest()
        v = v.upper() if upper else v.lower()
        a, b = v, compare_str
        s = difflib.SequenceMatcher(None, a.upper(), b.upper())
        q = s.find_longest_match(0, len(a), 0, len(b))
        if q.size>0:
            it.append([name, a, b, q.size])
    # 因为这类加密的互异性很高，所以只获取前三个最长匹配的加密字符串对比查看
    p = '-'
    for name,a,b,max_match in sorted(it,key=lambda max_match:-max_match[3])[:3]:
        s = difflib.SequenceMatcher(None, a.upper(), b.upper())
        prefix = '[len:compare]:{:<5} {:<18}'.format(len(a), p + '[len:{}]:{}'.format(name, len(b)))
        p = '-' if p == '+' else '+'
        for match in sorted(s.get_matching_blocks(),key=lambda i:-i.size):
            if match.size:
                v = a[match.a:match.a+match.size]
                print('{} [match.size:{}]  {}'.format(prefix, match.size, v))


encode_all(salt, text)
compare_str = '$compare_str' # 需要被对比的字符串
compare_encode(salt, text, compare_str)
        '''.strip()
        code = code.replace('$allow', pprint.pformat(allow))
        code = code.replace('$compare_str', compare_str)
        print(code)


    bt_ = Button(f1_,text='分析对比[忽略大小写]',command=_analysis_diff)
    bt_.pack(side=tkinter.LEFT,padx=padx,pady=pady,)
    bt2_ = Button(f1_,text='测用代码',command=_creat_code)
    bt2_.pack(side=tkinter.LEFT,padx=padx,pady=pady,)

    txt = Text(f2_,font=ft)
    txt.pack(padx=padx,pady=pady,fill=tkinter.BOTH,expand=True)

    return fr


if __name__ == '__main__':
    # test
    fr = encode_window()
    fr.mainloop()