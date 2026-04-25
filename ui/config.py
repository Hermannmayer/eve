import os
import sys

# 数据库路径：eve/database/items.db
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'database', 'items.db'
)

# 支持中文显示的字体
if sys.platform == 'win32':
    CJK_FONT = ('Microsoft YaHei UI', 10)
    CJK_LARGE = ('Microsoft YaHei UI', 16)
else:
    CJK_FONT = ('PingFang SC', 10)
    CJK_LARGE = ('PingFang SC', 16)
