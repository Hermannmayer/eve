import sqlite3
import requests
import json
import time
form tenacity import retry, stop_after_attempt, wait_fixed

def create_tables():
    
    conn = sqlite3.connect('./Datas/database.db')
    cursor = conn.cursor()

    '''
    en_name = 物品英文名称
    zh_name = 物品中文名称
    group_id = 物品组ID
    group_name = 物品组名称
    market_group_id = 市场组ID
    market_group_name = 市场组名称 
    mass = 物品体积
    volume = 物品体积
    '''
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item'")
    table_exists = cursor.fetchone()
    if not table_exists:
        # 创建表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item (
                type_id INTEGER PRIMARY KEY,
                en_name TEXT,
                zh_name TEXT,
                group_id INTEGER,
                en_group_name TEXT,
                zh_group_name TEXT,
                market_group_id INTEGER,
                en_market_group_name TEXT,
                zh_market_group_name TEXT,
                volume REAL
            )
        ''')
    else:
        # 从esi读取所有物品id
        getidapi()

    conn.commit()
    conn.close()

def getidapi():
    idapi='https://sde.jita.space/latest/universe/types'
    response=requests.get(idapi)
    type_ids=response.json()
    conn=sqlite3.connect('./Datas/database.db')
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

def getitemapi(): #从esi读取物品信息

    database_path = './Datas/database.db'
    api_url = 'https://sde.jita.space/latest'
    REQUEST_DELAY = 0.1#请求频率 
    BATCH_SIZE = 100#批量更新数据
    #缓存group_id和market_group_id
    group_cache = {}
    makrket_group_cache = {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)) 
    def fetch_api_data(url):#重试
        response=requests.get(url)
        requests.raise_for_status()
        return response.json()

    def get_group_info(group_id):
        #获取分组名称
        if group_id in group_cache:
            return group_cache[group_id]
        url = f'{api_url}/universe/groups/{group_id}/'
        try:
            data = fetch_api_data(url)
            en_name=data.get('name'{}.get('en', ''))
            zh_name=data.get('name'{}.get('zh', ''))
            group_cache[group_id] = (en_name, zh_name)
            return en_name, zh_name
        except Exception as e:
            print(f"failed to fetch group info for group_id {group_id}: {str(e)}")

create_tables()