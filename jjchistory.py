import os
import sqlite3

import hoshino

JJCHistory_DB_PATH = os.path.expanduser('~/.hoshino/jjchistory.db')


class JJCHistoryStorage:
    def __init__(self):
        os.makedirs(os.path.dirname(JJCHistory_DB_PATH), exist_ok=True)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(JJCHistory_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS JJCHistoryStorage
                (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                 UID INT  NOT NULL,
                 DATETIME DATETIME DEFAULT(datetime('now','localtime')),
                 ITEM INT NOT NULL,
                 BEFORE INT NOT NULL,
                 AFTER INT NOT NULL
                  )
                '''
                                    )
        except Exception as e:
            raise Exception('创建JJCHistory表失败')

    def _add(self, uid, item, before, after):
        conn = self._connect()
        try:
            conn.execute('''INSERT INTO JJCHistoryStorage (UID,ITEM,BEFORE,AFTER)
            VALUES (?,?,?,?)'''
                         , (uid, item, before, after))
            conn.commit()
        except Exception as e:
            raise Exception('新增记录异常')

    def _refresh(self, UID, ITEM):
        conn = self._connect()
        try:
            conn.execute('''delete from JJCHistoryStorage
where ID in
(select ID from JJCHistoryStorage 
where UID=? and ITEM = ?
order by DATETIME desc 
limit(select count(*) FROM JJCHistoryStorage WHERE UID = ? and ITEM = ?) offset 10)
            ''', (UID, ITEM, UID, ITEM))
            conn.commit()
        except Exception as e:
            raise Exception('更新记录异常')

    def _select(self, UID, ITEM):
        conn = self._connect().cursor()
        try:
            if ITEM == 1:
                item_name = '竞技场'
            else:
                item_name = '公主竞技场'
            result = conn.execute('''
            select * from JJCHistoryStorage WHERE UID=? and ITEM = ? ORDER  BY DATETIME desc''', (UID, ITEM))
            result_list = list(result)
            # print(result_list)
            # print(f"长度{len(result_list)}")
            if len(result_list) != 0:
                msg = f'竞技场绑定ID: {UID}\n{item_name}历史记录'
                for row in result_list:
                    if row[4] > row[5]:
                        jjc_msg = f'\n【{row[2]}】{row[4]}->{row[5]} ▲{row[4]-row[5]}'
                    else:
                        jjc_msg = f'\n【{row[2]}】{row[4]}->{row[5]} ▼{row[5]-row[4]}'
                    msg = msg + jjc_msg
                return msg
            else:
                msg = f'竞技场绑定ID: {UID}\n{item_name}历史记录\n无记录'
                return msg
        except Exception as e:
            raise Exception('查找记录异常')

    def _remove(self, UID):
        conn = self._connect()
        try:
            conn.execute('delete from JJCHistoryStorage where UID = ?', (UID,))
            conn.commit()
            hoshino.logger.info(f'移除ID:{UID}的竞技场记录')
        except Exception as e:
            raise Exception('移除记录异常')