"""
使用python的sqlite操作位于./Datas/database数据库创建prices表，item表已经存在并存有相应数据，表结构为：type_id INTEGER PRIMARY KEY,
                en_name TEXT,
                zh_name TEXT,
                group_id INTEGER,
                en_group_name TEXT,
                zh_group_name TEXT,
                market_group_id INTEGER,
                en_market_group_name TEXT,
                zh_market_group_name TEXT,
                volume REAL,
                iconID INTEGER。
在prices表中database数据库item表的主键type_id存入pricesd表的type_id,表设计为type_id(主键), jtbuy_price, jtsell_price,,
ambuy_price,amsell_price,
hkbuy_price,hksell_price，
ddxbuy_price,ddxsell_price
启用外键，type_id参照item表的type_id
实现自动从item表同步type_id到prices表并初始化价格字段

用/markets/{region_id}/orders/ 根据type_id获取物品价格信息：包含买单和卖单，只获取要求的星系中卖单最低价和买单最高价的价格信息，存储到./Datas/database.db中prices表中，

并预留接口方便后续图形化界面调用更新价格，同时分别记录更新时间（不用写在数据库中）
只更新以下四个星系内的订单价格、
30000142    Jita
30002187    Amarr
30002659    Dodixie
30002053    Hek

在初始化时，获取所有物品的价格信息
同时设计程序时单独设计每个星系的价格更新函数，方便后续用户单独更新某个信息的物品价格
在关键步骤设置log，方便后续调试

"""


"""
常用地点ID
星系

    30000142    Jita
    30000144    Perimeter
    30002187    Amarr
    30003491    Ashab
    30002659    Dodixie
    30002661    Botane
    30002053    Hek
    30002510    Rens
    30002526    Frarn
    
空间站

    60003760    Jita IV - Moon 4 - Caldari Navy Assembly Plant
    60008494    Amarr VIII (Oris) - Emperor Family Academy
    60011866    Dodixie IX - Moon 20 - Federation Navy Assembly Plant
    60005686    Hek VIII - Moon 12 - Boundless Creation Factory
    60004588    Rens VI - Moon 8 - Brutor Tribe Treasury
    
玩家建筑 (宁静服务器)

    1028858195912   Perimeter - Tranquility Trading Tower
    1023968078820   Ashab - Tranquility Trade & Prod Center
    1025824394754   Botane - IChooseYou Market and Industry
    1031058135975   Hek - IChooseYou Market and Industry
    1031084757448   Frarn - IChooseYou Market and Industry

"""



"""增强错误处理和日志记录的最终版"""
import sqlite3
import logging
import asyncio
import aiohttp
import time
import sys
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# Windows事件循环配置
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 增强日志配置
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('price_updater.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 性能配置
MAX_CONCURRENT_REQUESTS = 20  # 降低并发量
BATCH_SIZE = 100
REQUEST_TIMEOUT = 30

# 星系配置
SYSTEMS = [
    {'name': 'Jita', 'system_id': 30000142, 'region_id': 10000002, 'prefix': 'jt'},
    {'name': 'Amarr', 'system_id': 30002187, 'region_id': 10000043, 'prefix': 'am'},
    {'name': 'Dodixie', 'system_id': 30002659, 'region_id': 10000032, 'prefix': 'ddx'},
    {'name': 'Hek', 'system_id': 30002053, 'region_id': 10000042, 'prefix': 'hk'}
]

class HyperESIClient:
    """增强错误处理的ESI客户端"""
    def __init__(self):
        self.base_url = "https://esi.evetech.net/latest"
        self.session = None
        self.connector = aiohttp.TCPConnector(limit=50)  # 限制总连接数
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            headers={'User-Agent': 'PriceTracker/1.0'},
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        )
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        
    async def bulk_fetch(self, region_id: int, type_ids: List[int]) -> Dict[int, list]:
        """带重试机制的批量请求"""
        results = {}
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        async def _fetch_with_retry(tid: int, retries=3):
            for attempt in range(retries):
                try:
                    async with semaphore:
                        url = f"{self.base_url}/markets/{region_id}/orders/"
                        params = {
                            'datasource': 'tranquility',
                            'type_id': tid,
                            'page': 1
                        }
                        async with self.session.get(url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                logger.debug(f"成功获取 {tid} 数据，数量：{len(data)}")
                                return tid, data
                            else:
                                logger.warning(f"[{tid}] HTTP {resp.status}: {await resp.text()}")
                                await asyncio.sleep(2**attempt)
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"[{tid}] 请求失败（尝试 {attempt+1}/{retries}）: {str(e)}")
                    await asyncio.sleep(2**attempt)
                except Exception as e:
                    logger.error(f"[{tid}] 意外错误: {str(e)}", exc_info=True)
                    break
            return tid, []
        
        tasks = [_fetch_with_retry(tid) for tid in type_ids]
        for future in asyncio.as_completed(tasks):
            tid, data = await future
            results[tid] = data
            logger.debug(f"进度: {len(results)}/{len(type_ids)} ({(len(results)/len(type_ids)):.1%})")
        return results

class TurboDatabaseManager:
    """增强数据库日志的管理器"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._init_db()
        
    def _init_db(self):
        try:
            with self._get_conn() as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("""CREATE TABLE IF NOT EXISTS prices (
                    type_id INTEGER PRIMARY KEY,
                    jtbuy_price REAL DEFAULT -1,
                    jtsell_price REAL DEFAULT -1,
                    ambuy_price REAL DEFAULT -1,
                    amsell_price REAL DEFAULT -1,
                    hkbuy_price REAL DEFAULT -1,
                    hksell_price REAL DEFAULT -1,
                    ddxbuy_price REAL DEFAULT -1,
                    ddxsell_price REAL DEFAULT -1,
                    FOREIGN KEY (type_id) REFERENCES item(type_id))""")
                
                # 同步type_id
                cur = conn.execute("SELECT COUNT(*) FROM prices")
                if cur.fetchone()[0] == 0:
                    conn.execute("INSERT INTO prices (type_id) SELECT type_id FROM item")
                    logger.info(f"初始化插入{conn.total_changes}条type_id")
                conn.commit()
        except Exception as e:
            logger.critical(f"数据库初始化失败: {str(e)}")
            raise
        
    @lru_cache(maxsize=1)
    def get_all_type_ids(self) -> List[int]:
        with self._get_conn() as conn:
            return [row[0] for row in conn.execute("SELECT type_id FROM item")]
    
    async def turbo_update(self, updates: List[Tuple]):
        """带验证的批量更新"""
        if not updates:
            logger.warning("没有有效数据需要更新")
            return
            
        logger.debug(f"准备更新{len(updates)}条记录，示例数据：{updates[0]}")
        
        def _execute():
            try:
                with self._get_conn() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.executemany(
                        """UPDATE prices SET
                            jtbuy_price=?,jtsell_price=?,
                            ambuy_price=?,amsell_price=?,
                            hkbuy_price=?,hksell_price=?,
                            ddxbuy_price=?,ddxsell_price=?
                        WHERE type_id=?""", 
                        updates
                    )
                    changes = conn.total_changes
                    conn.commit()
                    logger.info(f"成功更新{changes}条记录")
                    if changes == 0:
                        logger.warning("更新影响0条记录，请检查WHERE条件")
            except sqlite3.Error as e:
                logger.error(f"数据库错误: {str(e)}", exc_info=True)
                raise
                
        await asyncio.get_event_loop().run_in_executor(self._pool, _execute)
    
    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)

class WarpSpeedUpdater:
    """增强数据验证的更新器"""
    def __init__(self, db_path: str):
        self.db = TurboDatabaseManager(db_path)
        self.last_updated = {}
        
    async def update_all_systems(self):
        type_ids = self.db.get_all_type_ids()
        logger.info(f"总物品数量：{len(type_ids)}")
        
        # 测试用：仅处理前10个物品
        # type_ids = type_ids[:10]
        
        await asyncio.gather(*[
            self._process_system(system, type_ids)
            for system in SYSTEMS
        ])
        
    async def _process_system(self, system: Dict, type_ids: List[int]):
        logger.info(f"== 开始处理 {system['name']} ==")
        try:
            async with HyperESIClient() as esi:
                # 获取数据
                logger.debug(f"获取{len(type_ids)}个物品数据...")
                orders_data = await esi.bulk_fetch(system['region_id'], type_ids)
                valid_data = len([d for d in orders_data.values() if d])
                logger.info(f"获取到{valid_data}个有效物品数据")
                
                # 分析数据
                updates = []
                for tid, data in orders_data.items():
                    if not data:
                        continue
                    buy, sell = self._analyze_orders(data, system['system_id'])
                    if buy is None and sell is None:
                        logger.debug(f"物品{tid}无有效订单")
                        continue
                    updates.append(self._create_tuple(system['prefix'], tid, buy, sell))
                
                logger.info(f"生成{len(updates)}条更新记录")
                
                # 分批更新
                for i in range(0, len(updates), BATCH_SIZE):
                    logger.debug(f"提交批次 {i//BATCH_SIZE+1}...")
                    await self.db.turbo_update(updates[i:i+BATCH_SIZE])
                    
        except Exception as e:
            logger.error(f"处理{system['name']}失败: {str(e)}", exc_info=True)
        finally:
            logger.info(f"== 完成 {system['name']} 处理 ==\n")
    
    def _create_tuple(self, prefix: str, tid: int, buy: float, sell: float) -> tuple:
        """验证数据类型"""
        try:
            buy_val = float(buy) if buy is not None else None
            sell_val = float(sell) if sell is not None else None
        except (TypeError, ValueError) as e:
            logger.error(f"无效价格类型 tid:{tid} buy:{buy} sell:{sell} - {str(e)}")
            return (None,)*8 + (tid,)
            
        template = [None]*8
        index = {'jt':0, 'am':2, 'hk':4, 'ddx':6}[prefix]
        template[index] = buy_val
        template[index+1] = sell_val
        return (*template, tid)
    
    def _analyze_orders(self, orders: list, system_id: int) -> Tuple[float, float]:
        """增强数据验证"""
        valid_orders = [o for o in orders if o.get('system_id') == system_id]
        if not valid_orders:
            return None, None
            
        try:
            buy_orders = [o['price'] for o in valid_orders if o.get('is_buy_order')]
            sell_orders = [o['price'] for o in valid_orders if not o.get('is_buy_order')]
            
            max_buy = max(buy_orders) if buy_orders else None
            min_sell = min(sell_orders) if sell_orders else None
        except KeyError as e:
            logger.error(f"订单数据缺少关键字段: {str(e)}")
            return None, None
            
        return max_buy, min_sell

async def main():
    updater = WarpSpeedUpdater('./Datas/database.db')
    try:
        logger.info("=== 启动价格更新 ===")
        start_time = time.time()
        await updater.update_all_systems()
        logger.info(f"=== 更新完成 总耗时: {time.time()-start_time:.2f}s ===")
        
        # 验证写入结果
        with sqlite3.connect('./Datas/database.db') as conn:
            cur = conn.execute("SELECT COUNT(*) FROM prices WHERE jtbuy_price IS NOT NULL")
            logger.info(f"Jita有效价格记录数: {cur.fetchone()[0]}")
    except Exception as e:
        logger.critical(f"主程序错误: {str(e)}", exc_info=True)
    finally:
        await asyncio.sleep(0.1)  # 等待后台任务完成

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"未捕获的异常: {str(e)}", exc_info=True)