from sql import *
import flask
from flask import jsonify, request, send_from_directory, Response
from room_information import RoomInformation
import threading
from datetime import datetime
import keyboard
#from msvcrt import getch
import sys
import signal
from werkzeug.serving import make_server

ROOM_INFORMATION = [
    RoomInformation(0, [1, 2, 3, 4]),
                    ]
SQL = None
SQL_DATA = dict()
DICT_INDEX = ["breath_rate", "heart_rate", "hight_temperature", "timestamp"] 

# def get_key():
        # try:
            # key = getch().decode('utf-8')
            # return key
        # except UnicodeDecodeError:
            # return None

def check_delay(last_time, delay=1):
    now_time = datetime.now()
    if (now_time - last_time).seconds < delay:
        return None
    return now_time

def initialize_sql():
    global SQL
    if SQL is None:
        SQL = SqlCommands()
    return SQL

def handle_sql_data(result):
    if isinstance(result, ErrorMessage):
        print("Error: get data failed", end="\n\t")
        print(result.message)
        return None
    if isinstance(result, tuple):
        if len(result) != 2:
            print("Error: result length is not 2")
            return None
        data, message = result
        print(message.message)
        if len(data) == 0:
            print("Error: no data found")
            return None
        data = data[0]
        return data

def store_sql_data(data, room_number, sensor_id):
    global DICT_INDEX
    dict_index = DICT_INDEX
    if isinstance(data, type(None)):
        return None
    for i, r in enumerate(data):
        if room_number not in SQL_DATA:
            SQL_DATA[room_number] = {}
        if i < len(data) - 1:
            key = f"{dict_index[i]}_{sensor_id}"
            SQL_DATA[room_number][f"{dict_index[i]}_{sensor_id}"] = float(r)
        else:
            date_time = str(r)
            date_time = date_time.split('.')[0]
            key = f"{dict_index[i]}_{sensor_id}"
            SQL_DATA[room_number][key] = date_time

def get_sql_data():
    global SQL_DATA
    sql = initialize_sql()
    while True:
        for room_info in ROOM_INFORMATION:
            for room, sensor_id in room_info.info_iter():
                result = sql.get_data(room, sensor_id, True)
                data = handle_sql_data(result)
                store_sql_data(data, room, sensor_id)
            print(f"\n\nSQL get data [{room_info.room_number}]\n\n")
        time.sleep(5)
        # key = get_key()
        # if key == 'q':
        #     print("DB Exiting...")
        #     return
        # while not check_delay(last_time):
        #     key = get_key()
        #     if key == 'q':
        #         print("DB Exiting...")
        #         return

def is_valid_temperature(temperature):
    # 確保數據行以指定標識符開頭和結尾
    if isinstance(temperature,list):
        # 檢查數據長度是否為32 * 24
        if len(temperature) == 32 * 24:
            flag = any(element != 0 for element in temperature)
            if flag:
                return True
            print("Error data: all zero")
        print("Error data: size too small")
    print("Error data: data not list")
    return False

# 創建 Flask 應用
app = flask.Flask(__name__)

# 定義根路由，返回 index.html 模板
@app.route('/')
def index():
    return flask.render_template('testindex.html', heart_rate=heart_rates, breath_rate=breath_rates, high_temperature=high_temperature)

# 定義 /get_data 路由，處理 POST 請求
@app.route('/get_data', methods=['POST'])
def data():
    global heart_rates, breath_rates, high_temperature
    
    # ESP32 IP 地址
    client_ip = request.remote_addr
    print(f"Client IP: {client_ip}")
    
    # 從請求中獲取 JSON 數據
    if request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type"}), 415
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Bad Request", "message": "Failed to decode JSON object"}), 400
    
    # 將數據轉換為字典
    data_dict = dict()
    for key in DATA_TITLE:
        data_dict[key] = data.get(key)
    
    temperature = data_dict['temperature']
    temperature_json = json.dumps(temperature)
    data_dict['temperature'] = temperature_json
    data_dict['high_temperature'] = max(temperature)
    data_dicts[int(data_dict['bed_number']) - 1] = data_dict
    # 檢查是否有缺少的數據
    if not all(data_dict.values()) or not is_valid_temperature(temperature):
        return jsonify({"error": "Missing data"}), 400
    print(f"Success: get {data_dict['sensor_id']} data")

    print("aaaaaa")
    sql = SqlCommands()
    # 轉換數據類型
    value = data_dict
    temperature_json = data_dict.get('temperature', '')
    temperature_json_length = len(temperature_json)
    print(f"Length of temperature_json: {temperature_json_length}")
    # SQL 插入資料
    result = sql.insert_data(value)
    if isinstance(result, ErrorMessage):
        print(result.message)
        return jsonify({"error": "Failed to insert data"}), 500
    else:
        print(result.message)
        return jsonify({"message": "Data inserted successfully"}), 201
        


@app.route('/return_data', methods=['GET'])
def return_data():
    print("sssssss")
    global SQL_DATA
    # room_number = request.json.get('room_number')
    room_number = 0
    if room_number not in SQL_DATA:
        return jsonify({"error": "Room number not found"}), 404
    return_data = SQL_DATA[room_number]
    print(return_data)
    return jsonify(return_data)    

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('0.0.0.0', 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print("Starting server")
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

def signal_handler(sig, frame):
    global stop_threads
    print('Exiting...')
    stop_threads = True
    server.shutdown()
    data_thread.join()
    sys.exit(0)

# 設置信號處理器
signal.signal(signal.SIGINT, signal_handler)

# 全局變數來控制線程的運行
stop_threads = False

# 啟動 Flask 應用
if __name__ == '__main__':
    data_thread = threading.Thread(target=get_sql_data)
    data_thread.start()
    server = ServerThread(app)
    server.start()
    try:
        while True:
            if keyboard.is_pressed('q'):
                signal_handler(None, None)
                break
    except KeyboardInterrupt:
        signal_handler(None, None)
    finally:
        data_thread.join()
        server.join()