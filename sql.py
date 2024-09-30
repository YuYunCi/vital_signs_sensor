import sys
import flask
import mysql.connector
from mysql.connector import Error
import time
import numpy as np
import json
from io import BytesIO
import os
from datetime import datetime

db = None
data = None
heart_rates = 0
breath_rates = 0
high_temperature = 0

DATA_TITLE = ['heart_rate', 'breath_rate', 'temperature', 'sensor_id', 'room_number', 'bed_number']
INSERT_KEY = ['sensor_id', 'room_number', 'bed_number', 'breath_rate', 'heart_rate', 'temperature', 'high_temperature']
data_dicts = [dict() for _ in range(4)]
bed_images_number = [0, 0, 0, 0]

class ErrorMessage():
    def __init__(self, message):
        self.message = message
    def add(self, message):
        self.message = f"{self.message}\n{message}"

class SuccessMessage():
    def __init__(self, message):
        self.message = message
    def add(self, message):
        self.message = f"{self.message}\n{message}"

class SqlCommands:
    db = None
    def __init__(self,
                host="localhost",
                user="stust",
                password="1234",
                db_name="fmcw",#fmcw
                table_name="abnormal_data",
                insert_key=INSERT_KEY):
        # 初始化資料庫連接參數
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        self.table_name = table_name
        # 資料庫連接次數
        self.db_conn_times = 10
        # 初始化插入數據的鍵
        self.insert_key = insert_key
     # 預存程序名稱
        self.insert_procedure = "insert_data"
        self.get_procedure = "get_data"
    ############################################################
    # 重新設定參數 ###############################################
    ############################################################
    # 重新設定資料庫連接次數
    def set_db_conn_times(self, times):
        self.db_conn_times = times

    # 重新設定插入預存程序的名稱
    def set_insert_procedure(self, procedure_name):
        self.insert_procedure = procedure_name

    # 重新設定搜尋預存程序的名稱
    def set_get_procedure(self, procedure_name):
        self.get_procedure = procedure_name
    ############################################################
    ############################################################
    
    ############################################################
    # 資料庫操作 ################################################
    ############################################################

    # 連接到資料庫
    def connect_to_database(self):
        try:
            db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
                connection_timeout=100  # 設置連接超時時間
            )
            db.autocomit=True
            conn = db.cursor()
            conn.execute(f"USE {self.db_name};")
            return db, conn
        except Error as e:
            message = ErrorMessage(f"Error connecting to MySQL: {e}")
            return message
        
    # 重複連接到資料庫
    def reconnect_to_database(self):
        for _ in range(self.db_conn_times):
            result = self.connect_to_database()
            if not isinstance(result, ErrorMessage):
                db, conn = result
                return db, conn
        return result

    
    # 關閉資料庫
    def close_db(self, db):
        try:
            db.close()
            return None
        except Error as e:
            message = ErrorMessage(f"close_db error: {e}")
            return message
    
    # 關閉資料庫連接
    def close_conn(self, conn):
        try:
            conn.close()
            return None
        except Error as e:
            message = ErrorMessage(f"close_conn error: {e}")
            return message

    # 插入數據
    def insert_data(self, data):
        result = self.reconnect_to_database()
        if isinstance(result, ErrorMessage):
            result.add("DB connect error[insert_data]:result is None")
            return result
        if len(result) != 2:
            result.add("DB connect error[insert_data]:result length is not 2")
            return result
        else:
            db, conn = result
        
        message = "insert_data:"
        try:
            # 插入數據
            value = tuple([data[key] for key in self.insert_key])
            conn.callproc(self.insert_procedure, value)
            db.commit()
            insert_len = conn.rowcount
            message = f"{message}\n\tinsert_data: {insert_len} record inserted."
            
            # 關閉資料庫連接
            result = self.close_db(db)
            if isinstance(result, ErrorMessage):
                message = f"{message}\n\t{result.message}"
            result = self.close_conn(conn)
            if isinstance(result, ErrorMessage):
                message = f"{message}\n\t{result.message}"

            message = SuccessMessage(message)
            return message
        except Error as e:
            message = ErrorMessage(message)
            error_message = f"\tinsert_data error: {e}"
            message.add(error_message)
            return message

    # 獲取數據
    def get_data(self, room_number, sensor_id, show_data=False):
        result = self.connect_to_database()
        if isinstance(result, ErrorMessage):
            result.add("DB connect error[get_data]:result is None")
            return result
        if len(result) != 2:
            result.add("DB connect error[get_data]:result length is not 2")
            return result
        else:
            db, conn = result

        message = "get_data:"
        try:
            # 獲取數據
            value = (room_number, sensor_id)
            conn.callproc(self.get_procedure, value)
            for r in conn.stored_results():
                data = r.fetchall()
            if show_data:
                message = f"{message}\n\tget_data: {data}"
            message = f"{message}\n\tget_data: success [sensor_id:{sensor_id}, room_number:{room_number}]"
            
            # 關閉資料庫連接
            result = self.close_db(db)
            if isinstance(result, ErrorMessage):
                message = f"{message}\n\t{result.message}"
            result = self.close_conn(conn)
            if isinstance(result, ErrorMessage):
                message = f"{message}\n\t{result.message}"
            
            message = SuccessMessage(message)
            return data, message
        except Error as e:
            message = ErrorMessage(message)
            error_message = f"\tget_data error: {e}"
            message.add(error_message)
            return message

    ############################################################
    ############################################################