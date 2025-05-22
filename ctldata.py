import sqlite3
import requests
import json


def create_tables():
    
    conn = sqlite3.connect('./Datas/iteamdata.db')
    cursor = conn.cursor()

    # 主表：存储类型基本信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS types (
            type_id INTEGER PRIMARY KEY,
            en_name TEXT,
            zh_name TEXT,
            group_id INTEGER,
            group_name TEXT,
            market_group_id INTEGER,
            market_group_name TEXT,
            mass REAL,
            volume REAL,
            published BOOLEAN
        )
        ''')
    conn.commit()
    conn.close()
def getidapi():
    idapi='https://sde.jita.space/latest/universe/types'
    response=requests.get(idapi)
    type_ids=response.json()
    conn=sqlite3.connect('./Datas/iteamdata.db')
    cursor=conn.cursor()
    insert_count = 0
    for type_id in type_ids:
        try:
            cursor.execute('INSERT INTO item (type_id) VALUES (?)', (type_id,))
            insert_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()    
    print(f"Inserted {insert_count} type IDs into the database.")

    
getidapi()