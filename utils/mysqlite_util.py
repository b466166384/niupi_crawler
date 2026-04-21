import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Optional


class DownloadFileDB:
    def __init__(self):
        """初始化数据库连接参数"""
        self.host = "localhost"
        self.port = 3306
        self.user = "root"
        self.password = "1m_0833n"
        self.db_name = "python_data"
        self.conn = None  # 数据库连接对象
        self.cursor = None  # 游标对象

    def _connect(self) -> None:
        """建立数据库连接（私有方法，内部调用）"""
        try:
            self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset="utf8mb4",
                cursorclass=DictCursor  # 游标返回字典格式（键为字段名）
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise ConnectionError(f"数据库连接失败：{str(e)}")

    def _close(self) -> None:
        """关闭数据库连接（私有方法，内部调用）"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def insert(self, title: str, year: Optional[int]) -> int:
        """
        新增一条记录
        :param title: 标题（非空，最长255字符）
        :param year: 年份（可为None）
        :return: 新增记录的id（自增主键）
        """
        if not title or len(title) > 255:
            raise ValueError("标题不能为空且长度不能超过255字符")

        sql = "INSERT INTO download_file (title, year) VALUES (%s, %s)"
        try:
            self._connect()
            self.cursor.execute(sql, (title, year))
            self.conn.commit()  # 提交事务
            return self.cursor.lastrowid  # 返回自增id
        except Exception as e:
            self.conn.rollback()  # 出错回滚
            raise RuntimeError(f"新增记录失败：{str(e)}")
        finally:
            self._close()

    def get_by_id(self, id: int) -> Optional[Dict]:
        """
        根据id查询单条记录
        :param id: 记录id
        :return: 记录字典（含id、title、year），无结果则返回None
        """
        sql = "SELECT id, title, year FROM download_file WHERE id = %s"
        try:
            self._connect()
            self.cursor.execute(sql, (id,))
            return self.cursor.fetchone()  # 返回单条结果（字典）
        except Exception as e:
            raise RuntimeError(f"查询记录失败：{str(e)}")
        finally:
            self._close()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        查询所有记录（支持分页）
        :param limit: 每页条数（默认100）
        :param offset: 偏移量（从第几条开始，默认0）
        :return: 记录列表（每个元素为字典）
        """
        sql = "SELECT id, title, year FROM download_file LIMIT %s OFFSET %s"
        try:
            self._connect()
            self.cursor.execute(sql, (limit, offset))
            return self.cursor.fetchall()  # 返回所有结果（列表）
        except Exception as e:
            raise RuntimeError(f"查询所有记录失败：{str(e)}")
        finally:
            self._close()

    def update(self, id: int, title: Optional[str] = None, year: Optional[int] = None) -> bool:
        """
        更新记录（支持部分字段更新）
        :param id: 要更新的记录id
        :param title: 新标题（为None则不更新）
        :param year: 新年份（为None则不更新）
        :return: 是否更新成功
        """
        if title is None and year is None:
            raise ValueError("至少需要更新一个字段（title或year）")
        if title is not None and len(title) > 255:
            raise ValueError("标题长度不能超过255字符")

        # 动态拼接更新字段（只更新非None的参数）
        update_fields = []
        params = []
        if title is not None:
            update_fields.append("title = %s")
            params.append(title)
        if year is not None:
            update_fields.append("year = %s")
            params.append(year)
        params.append(id)  # 最后添加where条件的id

        sql = f"UPDATE download_file SET {', '.join(update_fields)} WHERE id = %s"
        try:
            self._connect()
            affected_rows = self.cursor.execute(sql, params)
            self.conn.commit()
            return affected_rows > 0  # 受影响行数>0表示更新成功
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"更新记录失败：{str(e)}")
        finally:
            self._close()

    def delete(self, id: int) -> bool:
        """
        根据id删除记录
        :param id: 要删除的记录id
        :return: 是否删除成功
        """
        sql = "DELETE FROM download_file WHERE id = %s"
        try:
            self._connect()
            affected_rows = self.cursor.execute(sql, (id,))
            self.conn.commit()
            return affected_rows > 0  # 受影响行数>0表示删除成功
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"删除记录失败：{str(e)}")
        finally:
            self._close()

    def get_by_title_and_year(
            self,
            title: Optional[str] = None,
            year: Optional[int] = None,
            fuzzy: bool = False  # 是否模糊匹配标题
    ) -> List[Dict]:
        """
        根据 title 和 year 查询记录（支持联合查询和模糊匹配）
        :param title: 标题（为 None 则不按标题筛选）
        :param year: 年份（为 None 则不按年份筛选）
        :param fuzzy: 是否对标题进行模糊匹配（默认精确匹配）
        :return: 符合条件的记录列表（每个元素为字典）
        """
        if title is None and year is None:
            raise ValueError("至少需要提供 title 或 year 作为查询条件")

        # 构建查询条件和参数
        conditions = []
        params = []

        # 处理标题条件（支持模糊匹配）
        if title is not None:
            if fuzzy:
                # 模糊匹配：标题包含该字符串（前后加 %）
                conditions.append("title LIKE %s")
                params.append(f"%{title}%")
            else:
                # 精确匹配：标题完全相等
                conditions.append("title = %s")
                params.append(title)

        # 处理年份条件（精确匹配）
        if year is not None:
            conditions.append("year = %s")
            params.append(year)

        # 拼接 SQL 语句
        sql = f"SELECT id, title, year FROM download_file WHERE {' AND '.join(conditions)}"

        try:
            self._connect()
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()  # 返回所有匹配的记录
        except Exception as e:
            raise RuntimeError(f"查询失败：{str(e)}")
        finally:
            self._close()


    def get_by_title_custom(
            self,
            table_name: str,
            title: Optional[str] = None,
            fuzzy: bool = False  # 是否模糊匹配标题
    ) -> List[Dict]:
        """
        根据 title 和 year 查询记录（支持联合查询和模糊匹配）
        :param title: 标题（为 None 则不按标题筛选）
        :param year: 年份（为 None 则不按年份筛选）
        :param fuzzy: 是否对标题进行模糊匹配（默认精确匹配）
        :return: 符合条件的记录列表（每个元素为字典）
        """
        if title is None and table_name is None:
            raise ValueError("至少需要提供 title 和table_namen表名 作为查询条件")
        # 构建查询条件和参数
        conditions = []
        params = []
        # 处理标题条件（支持模糊匹配）
        if title is not None:
            if fuzzy:
                # 模糊匹配：标题包含该字符串（前后加 %）
                conditions.append("title LIKE %s")
                params.append(f"%{title}%")
            else:
                # 精确匹配：标题完全相等
                conditions.append("title = %s")
                params.append(title)
        # 拼接 SQL 语句
        sql = f"SELECT id, title FROM {table_name} WHERE {' AND '.join(conditions)}"
        try:
            self._connect()
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()  # 返回所有匹配的记录
        except Exception as e:
            raise RuntimeError(f"查询失败：{str(e)}")
        finally:
            self._close()

    def insert_custom(self, title: str, table_name:str) -> int:
        """
        新增一条记录
        :param title: 标题（非空，最长255字符）
        :param year: 年份（可为None）
        :return: 新增记录的id（自增主键）
        """
        if not title or len(title) > 255:
            raise ValueError("标题不能为空且长度不能超过255字符")

        sql = f"INSERT INTO {table_name} (title) VALUES (%s)"
        try:
            self._connect()
            self.cursor.execute(sql, (title,))
            self.conn.commit()  # 提交事务
            return self.cursor.lastrowid  # 返回自增id
        except Exception as e:
            self.conn.rollback()  # 出错回滚
            raise RuntimeError(f"新增记录失败：{str(e)}")
        finally:
            self._close()