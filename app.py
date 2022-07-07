from pyngrok import conf, ngrok, installer
import os
import stat
from flask import Flask, request, abort
import asyncio
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import json
import ssl
from logging import config
import time
import datetime
from middleware.environment_settings import Env
from middleware.save_log import jsonl_to_csv

# logging settings
from middleware.log_util import StringHandler
config.dictConfig({
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'string': {
            'class': 'middleware.log_util.StringHandler',
            'formatter': 'simple'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['string']
    }
})

def logger():
    current_length = 1
    while True:
        current_log = StringHandler.str_io.getvalue()
        time.sleep(0.1)
        log_array = current_log.rsplit('\n')
        if current_length != len(log_array):
            log.config(text=log_array[-2].replace('(Press CTRL+C to quit)', ''))
        current_length = len(log_array)

logging_loop = asyncio.new_event_loop()
logging_loop.call_soon(logger)
logging_loop.run_in_executor(None, logger)


# global var
app = Flask(__name__)
app_name: str = 'simpleGUIserver'
settings: Env = None
ngrok_https_url = None
log_file_name: str = None

def find_app_file():
    current_path = os.path.expanduser('~')
    fullpath = current_path + '/Library/Application Support/' + app_name
    if not os.path.isfile(fullpath + '/.env'):
        if not os.path.isdir(fullpath):
            os.makedirs(fullpath, exist_ok=True)
            os.chmod(fullpath, 0o744)
        f = open(fullpath + '/.env.txt', 'w')
        f.write("PORT='4000'\n")
        f.write("SAVE_PATH=''\n")
        f.close()
        os.rename(fullpath + '/.env.txt', fullpath + '/.env')
    conf.get_default().ngrok_path = fullpath + '/ngrok'
    global settings
    settings = Env(fullpath)

def json_fix_indent(jsonText):
    try:
        return json.dumps(jsonText, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return ''

@app.route('/recieve_json',methods=['POST'])
def webhook_recieve():
    verified = True
    if not verified:
        abort(401)
    json_data = request.get_json()
    date_now = datetime.datetime.now()
    recieve_json.insert(tk.END, '\n{}\n'.format(date_now.strftime('[%d/%b/%Y %H:%M:%S]')))
    recieve_json.insert(tk.END, json_fix_indent(json_data))
    log_append = open(log_file_name, 'a')
    log_append.write(json.dumps(json_data,ensure_ascii=False)+'\n')
    log_append.close()
    try:
        return 'success', 200
    except Exception:
        return 'success', 200

def start_ngrok(port):
    ngrok.kill()
    ngrok.connect(port, 'http')
    tunnels: list[ngrok.NgrokTunnel] = ngrok.get_tunnels()
    for ngrok_tunnel in tunnels:
        if 'https://' in ngrok_tunnel.public_url:
            global ngrok_https_url
            ngrok_https_url = ngrok_tunnel.public_url
    return

def create_server_sync():
    port_number = settings.get('PORT')
    start_ngrok(port_number)
    if ngrok_https_url is None:
        messagebox.showerror('エラー','failed to start tunnels.')
    sample_cmd.insert(tk.END,
    '''curl -X POST -H "Content-Type: application/json" -d '{"名前":"和田大河", "学籍番号":24020075}' %s/recieve_json'''%(ngrok_https_url))
    server_status_page.tkraise()
    start_btn["state"] = tk.ACTIVE
    start_btn.config(text='起動')
    start_btn.update_idletasks()
    app.run(port=int(port_number))
    
def create_server(loop: asyncio.AbstractEventLoop):
    if not port_input.get():
        messagebox.showerror('エラー', 'ポート番号が未設定です')
        return
    if not save_dir_input.get():
        messagebox.showerror('エラー', 'ログ保存先が未設定です')
        return
    start_btn["state"] = tk.DISABLED
    pyngrok_config_path: str = conf.get_default().ngrok_path
    now_date = datetime.datetime.now()
    global log_file_name
    log_file_name = os.path.join(settings.get('SAVE_PATH'),now_date.strftime('%Y-%m-%dT%H:%M:%S.jsonl'))
    log_file = open(log_file_name, 'w')
    log_file.close()
    if not os.path.exists(pyngrok_config_path):
        start_btn.config(text='ngrok downloading...')
        start_btn.update_idletasks()
        myssl = ssl.create_default_context()
        myssl.check_hostname = False
        myssl.verify_mode = ssl.CERT_NONE
        installer.install_ngrok(pyngrok_config_path.replace('ngrok', ''), context = myssl)
        os.chmod(pyngrok_config_path, stat.S_IXUSR)
    start_btn.config(text='now starting...')
    start_btn.update_idletasks()
    if (port_input.get() != settings.get('PORT')):
        settings.changeENV('PORT', port_input.get())
    loop.run_in_executor(None, create_server_sync)
    return

def on_exit():
    ngrok.kill()
    if log_file_name is not None:
        jsonl_to_csv(log_file_name, jsonl_save.get())
    os._exit(0) # flask is allowed only _exit of os module.

class Application(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master.title(app_name)
        self.master.geometry("1920x1080")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.master.protocol("WM_DELETE_WINDOW", self.delete_window)
    def delete_window(self):
        on_exit()

def dirdialog_clicked(path):
    if not os.path.isdir(path):
        path = os.path.expanduser('~')
    iDir = os.path.abspath(path)
    iDirPath = filedialog.askdirectory(initialdir = iDir)
    if iDirPath:
        settings.changeENV('SAVE_PATH', iDirPath)
        save_dir_input.delete(0,tk.END)
        save_dir_input.insert(0, iDirPath)

# file initialize
find_app_file()

root = tk.Tk()
tk_app = Application(master=root)

#landing page
landing_page = tk.Frame()
landing_page.grid(row=0, column=0, sticky="nsew")

titleLabel = tk.Label(landing_page, text='設定', font=('Helvetica', '25'))
titleLabel.pack(anchor=tk.W, padx=100, pady=20)
port_text = tk.Label(landing_page, text="port番号", font=('Helvetica', '18'))
port_text.pack(anchor=tk.W, padx=100, pady=5)
port_input = tk.Entry(landing_page, width=20)
port_input.insert(0, settings.get('PORT'))
port_input.pack(anchor=tk.W, padx=100, pady=5)
save_dir_text = tk.Label(landing_page, text="ログ保存先", font=('Helvetica', '18'))
save_dir_text.pack(anchor=tk.W, padx=100, pady=5)
save_dir_input = tk.Entry(landing_page, width=50)
save_dir_input.insert(0, settings.get('SAVE_PATH'))
save_dir_input.pack(anchor=tk.W, padx=100, pady=5)
save_dir_btn = tk.Button(landing_page, text="参照", command=lambda:dirdialog_clicked(settings.get('SAVE_PATH')), padx=14, pady=5)
save_dir_btn.pack(anchor=tk.W, padx=100, pady=5)
jsonl_save = tk.BooleanVar()
jsonl_save.set(True)
jsonl_save_check = tk.Checkbutton(landing_page, variable=jsonl_save, text='JSONLファイルを残す')
jsonl_save_check.pack(anchor=tk.W, padx=100, pady=5)
server_loop = asyncio.new_event_loop()
server_loop.call_soon(create_server_sync)
start_btn = tk.Button(landing_page, text="起動", command=lambda:create_server(server_loop), padx=14, pady=5)
start_btn.pack(pady=10)

#server_status_page
server_status_page = tk.Frame()
server_status_page.grid(row=0, column=0, sticky="nsew")
stop_btn = tk.Button(server_status_page, text="終了", command=on_exit, padx=14, pady=5)
stop_btn.pack(anchor=tk.W, pady=10)
text1 = tk.Label(server_status_page, text='サンプルコマンド(ターミナルで実行してください)')
text1.pack()
sample_cmd = tk.Entry(server_status_page, width=170)
sample_cmd.pack()
text1 = tk.Label(server_status_page, text='ログ')
text1.pack(pady=15)
log = tk.Label(server_status_page, text='')
log.pack(pady=15)
recieve_json = tk.Text(server_status_page, width=170, height=20)
recieve_json.pack()
landing_page.tkraise()

tk_app.mainloop()