"""
SQLite数据库连接和管理模块

负责创建数据库连接、初始化表结构以及提供数据访问层
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# 定义数据库文件路径
DATABASE_FILE = "data/sequoiamq.db"

def ensure_db_dir():
    """确保数据库目录存在"""
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

def get_db_connection():
    """获取数据库连接"""
    ensure_db_dir()
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表结构"""
    try:
        print("开始初始化数据库...")
        conn = get_db_connection()
        
        # 创建自选股表
        conn.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            code TEXT PRIMARY KEY,
            name TEXT,
            add_time TEXT,
            notes TEXT
        )
        ''')
        print("创建自选股表成功")
        
        # 创建设置表
        conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        print("创建设置表成功")
        
        # 创建用户表
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            avatar_url TEXT,
            mobile TEXT NOT NULL UNIQUE,
            energy_coin INTEGER DEFAULT 0,
            create_time TEXT,
            update_time TEXT,
            is_deleted INTEGER DEFAULT 0
        )
        ''')
        print("创建用户表成功")
        
        # 创建分析结果缓存表
        conn.execute('''
        CREATE TABLE IF NOT EXISTS analysis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            batch_id TEXT,
            data_date TEXT,
            result_json TEXT,
            created_at TEXT
        )
        ''')
        print("创建分析结果缓存表成功")
        
        # 创建股票信息表
        conn.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            market TEXT,
            industry TEXT,
            last_update TEXT
        )
        ''')
        print("创建股票信息表成功")
        
        conn.commit()
        
        # 检查是否存在自选股数据
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM watchlist")
        count = cursor.fetchone()["count"]
        print(f"当前自选股数量: {count}")
        
        # 检查是否需要更新股票数据
        cursor.execute("SELECT value FROM settings WHERE key='stocks_last_update'")
        last_update = cursor.fetchone()
        
        # 如果没有更新记录或超过一周，则更新股票数据
        if not last_update or (datetime.now() - datetime.fromisoformat(last_update['value'])).days > 7:
            # 异步更新股票数据，避免阻塞启动
            import threading
            thread = threading.Thread(target=update_stock_database)
            thread.daemon = True
            thread.start()
        
        conn.close()
        print("数据库初始化完成")
        
        # 如果已有JSON文件数据，迁移到数据库
        migrate_from_json()
    except Exception as e:
        print(f"初始化数据库出错: {str(e)}")
        raise

def migrate_from_json():
    """从JSON文件迁移数据到SQLite数据库"""
    try:
        # 迁移自选股数据
        watchlist_file = "data/watchlist.json"
        if os.path.exists(watchlist_file):
            try:
                with open(watchlist_file, "r", encoding="utf-8") as f:
                    watchlist_data = json.load(f)
                
                if watchlist_data and isinstance(watchlist_data, list):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    for item in watchlist_data:
                        if isinstance(item, dict) and "code" in item:
                            cursor.execute(
                                "INSERT OR REPLACE INTO watchlist (code, name, add_time, notes) VALUES (?, ?, ?, ?)",
                                (
                                    item.get("code"),
                                    item.get("name", "未知"),
                                    item.get("add_time", datetime.now().isoformat()),
                                    item.get("notes", "")
                                )
                            )
                    
                    conn.commit()
                    conn.close()
                    print(f"已将 {len(watchlist_data)} 条自选股数据从JSON迁移到SQLite")
            except Exception as e:
                print(f"迁移自选股数据出错: {str(e)}")
    except Exception as e:
        print(f"数据迁移过程发生错误: {str(e)}")

# 自选股相关数据操作

def get_watchlist() -> List[Dict[str, Any]]:
    """获取自选股列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM watchlist")
    result = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return result

def add_to_watchlist(item: Dict[str, Any]) -> Dict[str, Any]:
    """添加股票到自选股"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR REPLACE INTO watchlist (code, name, add_time, notes) VALUES (?, ?, ?, ?)",
        (
            item.get("code"),
            item.get("name", "未知"),
            item.get("add_time", datetime.now().isoformat()),
            item.get("notes", "")
        )
    )
    
    conn.commit()
    
    # 获取插入的数据
    cursor.execute("SELECT * FROM watchlist WHERE code = ?", (item.get("code"),))
    result = dict(cursor.fetchone())
    
    conn.close()
    return result

def remove_from_watchlist(code: str) -> Optional[Dict[str, Any]]:
    """从自选股删除股票"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先获取要删除的项目
    cursor.execute("SELECT * FROM watchlist WHERE code = ?", (code,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return None
    
    # 删除项目
    cursor.execute("DELETE FROM watchlist WHERE code = ?", (code,))
    conn.commit()
    
    conn.close()
    return dict(item)

def update_watchlist_item(code: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新自选股信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查项目是否存在
    cursor.execute("SELECT * FROM watchlist WHERE code = ?", (code,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return None
    
    # 准备更新的字段
    updates = []
    params = []
    
    if "name" in data:
        updates.append("name = ?")
        params.append(data["name"])
    
    if "notes" in data:
        updates.append("notes = ?")
        params.append(data["notes"])
    
    if updates:
        # 添加代码参数
        params.append(code)
        
        # 执行更新
        cursor.execute(f"UPDATE watchlist SET {', '.join(updates)} WHERE code = ?", params)
        conn.commit()
    
    # 获取更新后的项目
    cursor.execute("SELECT * FROM watchlist WHERE code = ?", (code,))
    updated_item = cursor.fetchone()
    
    conn.close()
    return dict(updated_item) if updated_item else None

def clear_watchlist() -> int:
    """清空自选股列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM watchlist")
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count

# 用户相关数据库操作函数
def get_users(page: int = 1, page_size: int = 10, search_term: str = None) -> Dict[str, Any]:
    """获取用户列表
    
    Args:
        page: 页码，从1开始
        page_size: 每页大小
        search_term: 搜索关键词
        
    Returns:
        包含分页数据的字典
    """
    conn = get_db_connection()
    offset = (page - 1) * page_size
    
    query_conditions = "WHERE is_deleted = 0"
    query_params = []
    
    if search_term:
        query_conditions += " AND (name LIKE ? OR mobile LIKE ?)"
        query_params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    # 获取总数
    count_query = f"SELECT COUNT(*) as total FROM users {query_conditions}"
    total = conn.execute(count_query, query_params).fetchone()["total"]
    
    # 获取分页数据
    users_query = f"""
    SELECT id, name, avatar_url, mobile, energy_coin, create_time, update_time
    FROM users {query_conditions}
    ORDER BY id DESC
    LIMIT ? OFFSET ?
    """
    query_params.extend([page_size, offset])
    users = conn.execute(users_query, query_params).fetchall()
    
    result = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(user) for user in users]
    }
    
    conn.close()
    return result

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """通过ID获取用户信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户信息字典或None
    """
    conn = get_db_connection()
    user = conn.execute(
        """
        SELECT id, name, avatar_url, mobile, energy_coin, create_time, update_time
        FROM users
        WHERE id = ? AND is_deleted = 0
        """,
        (user_id,)
    ).fetchone()
    
    conn.close()
    return dict(user) if user else None

def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建新用户
    
    Args:
        user_data: 用户数据字典
        
    Returns:
        创建的用户信息字典
    """
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    # 检查手机号是否已存在
    existing = conn.execute(
        "SELECT id FROM users WHERE mobile = ? AND is_deleted = 0",
        (user_data["mobile"],)
    ).fetchone()
    
    if existing:
        conn.close()
        raise ValueError(f"手机号 {user_data['mobile']} 已存在")
    
    cursor = conn.execute(
        """
        INSERT INTO users (name, avatar_url, mobile, energy_coin, create_time, update_time)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_data["name"],
            user_data.get("avatar_url"),
            user_data["mobile"],
            user_data.get("energy_coin", 0),
            now,
            now
        )
    )
    
    user_id = cursor.lastrowid
    conn.commit()
    
    # 获取新创建的用户
    user = get_user_by_id(user_id)
    conn.close()
    
    return user

def update_user(user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新用户信息
    
    Args:
        user_id: 用户ID
        user_data: 要更新的用户数据
        
    Returns:
        更新后的用户信息字典或None
    """
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    # 如果要更新手机号，检查是否已存在
    if "mobile" in user_data and user_data["mobile"] != user["mobile"]:
        existing = conn.execute(
            "SELECT id FROM users WHERE mobile = ? AND is_deleted = 0 AND id != ?",
            (user_data["mobile"], user_id)
        ).fetchone()
        
        if existing:
            conn.close()
            raise ValueError(f"手机号 {user_data['mobile']} 已存在")
    
    # 构建更新语句
    fields = []
    params = []
    
    for key, value in user_data.items():
        if key in ["name", "avatar_url", "mobile", "energy_coin"] and value is not None:
            fields.append(f"{key} = ?")
            params.append(value)
    
    if not fields:
        conn.close()
        return user  # 没有字段更新，返回原用户信息
    
    fields.append("update_time = ?")
    params.append(now)
    params.append(user_id)
    
    conn.execute(
        f"""
        UPDATE users
        SET {", ".join(fields)}
        WHERE id = ?
        """,
        params
    )
    
    conn.commit()
    
    # 获取更新后的用户
    updated_user = get_user_by_id(user_id)
    conn.close()
    
    return updated_user

def delete_user(user_id: int) -> bool:
    """软删除用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        删除是否成功
    """
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    conn.execute(
        """
        UPDATE users
        SET is_deleted = 1, update_time = ?
        WHERE id = ?
        """,
        (now, user_id)
    )
    
    conn.commit()
    conn.close()
    
    return True

def update_stock_database():
    """更新股票数据库"""
    try:
        from utils import get_stock_info
        stocks = get_stock_info()
        
        if not stocks:
            print("获取股票列表失败，无法更新股票数据库")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 批量插入或更新股票数据
        now = datetime.now().isoformat()
        for stock in stocks:
            cursor.execute(
                """
                INSERT INTO stocks (code, name, market, industry, last_update)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    name = excluded.name,
                    market = excluded.market,
                    industry = excluded.industry,
                    last_update = excluded.last_update
                """,
                (
                    stock['code'],
                    stock['name'],
                    stock.get('market', ''),
                    stock.get('industry', ''),
                    now
                )
            )
        
        # 更新股票数据库更新时间
        cursor.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ('stocks_last_update', ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value
            """,
            (now,)
        )
        
        conn.commit()
        
        # 计算相关统计信息
        cursor.execute("SELECT COUNT(*) as count FROM stocks")
        count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT market, COUNT(*) as count FROM stocks GROUP BY market")
        market_stats = cursor.fetchall()
        
        stats = f"股票数据库更新完成，共 {count} 只股票"
        for stat in market_stats:
            stats += f"\n - {stat['market'] or '其他'}: {stat['count']} 只"
        
        print(stats)
        
        conn.close()
    except Exception as e:
        print(f"更新股票数据库失败: {str(e)}")

def get_stocks_from_db(keyword=None, limit=100):
    """从数据库获取股票列表
    
    Args:
        keyword: 搜索关键词，为None时返回所有股票
        limit: 返回的最大数量
        
    Returns:
        List[Dict]: 股票信息列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if keyword:
            # 模糊搜索股票代码和名称
            cursor.execute(
                """
                SELECT code, name, market, industry, last_update
                FROM stocks
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY 
                    CASE 
                        WHEN code = ? THEN 0 
                        WHEN name = ? THEN 1
                        WHEN code LIKE ? THEN 2
                        WHEN name LIKE ? THEN 3
                        ELSE 4
                    END
                LIMIT ?
                """,
                (
                    f"%{keyword}%", 
                    f"%{keyword}%",
                    keyword,
                    keyword, 
                    f"{keyword}%",
                    f"{keyword}%",
                    limit
                )
            )
        else:
            cursor.execute(
                """
                SELECT code, name, market, industry, last_update
                FROM stocks
                LIMIT ?
                """,
                (limit,)
            )
            
        results = []
        for row in cursor.fetchall():
            results.append({
                'code': row['code'],
                'name': row['name'],
                'market': row['market'],
                'industry': row['industry']
            })
            
        return results
    finally:
        conn.close()

def get_stock_by_code(code):
    """根据股票代码获取股票信息
    
    Args:
        code: 股票代码
        
    Returns:
        Dict: 股票信息，不存在时返回None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT code, name, market, industry, last_update
            FROM stocks
            WHERE code = ?
            """,
            (code,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            'code': row['code'],
            'name': row['name'],
            'market': row['market'],
            'industry': row['industry'],
            'last_update': row['last_update']
        }
    finally:
        conn.close()

# 初始化数据库
init_db() 