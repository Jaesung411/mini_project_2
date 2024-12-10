import pymysql

class DBConnect:
    @classmethod
    def get_db(self):
        return pymysql.connect(
            host='database-1.cbwk5avem9qx.ap-northeast-3.rds.amazonaws.com',
            user='admin',
            passwd='qwer1234',
            db='mini2',
            charset='utf8',
            autocommit=True
        )

class imageDAO:
    # select
    def get_stores(self):
        ret = []
        cursor = DBConnect.get_db().cursor()
        sql_select = 'select * from files'
        try:
            cursor.execute(sql_select)
            rows = cursor.fetchall()
            for row in rows :
                temp = {
                    'store_id' : row[0],
                    'name' : row[1],
                    'address' : row[2],
                    'image' : row[3],
                    'rate' : row[4],
                    'food_type' : row[5]
                }
                ret.append(temp)
        except :
            pass
        finally :
            DBConnect.get_db().close()
        return ret
    
    # 유저가 만든 모든 파일 불러오기
    def get_files_by_userid(self, userid):
        ret = []
        cursor = DBConnect.get_db().cursor()
        sql_select = 'SELECT * FROM files WHERE userid=%s'
        # cursor.execute(sql_select, (userid,))
        # rows = cursor.fetchall()  # 단일 행 가져오기
        DBConnect.get_db().close()
    
        try:
            cursor.execute(sql_select, (userid,))
            rows = cursor.fetchall() 
            for row in rows :
                temp = {
                    'file_id' : row[0],
                    'userid' : row[1],
                    'file_name' : row[2],
                    'qr_info' : row[3],
                    'update_at' : row[4],
                    'image_path' : row[5],
                    'video_path' : row[6]
                }
                ret.append(temp)
        except :
            pass
        finally :
            DBConnect.get_db().close()
        return ret
    
    # 이미지 ID 불러오기
    def get_image_by_id(store_id):
        cursor = DBConnect.get_db().cursor()
        sql_select = 'SELECT * FROM files WHERE file_id = %s'
        cursor.execute(sql_select, (store_id,))
        row = cursor.fetchone()
        DBConnect.get_db().close()
        if row:
            return {
                'store_id': row[0],
                'name': row[1],
                'address': row[2],
                'image': row[3],
                'rate': row[4],
                'food_type': row[5]
            }
        return None  # 가게가 없으면 None 반환
    
    def get_file_by_id(self, file_id):
        cursor = DBConnect.get_db().cursor()
        sql_select = 'SELECT * FROM files WHERE file_id = %s'
        cursor.execute(sql_select, (file_id,))
        row = cursor.fetchone()
        DBConnect.get_db().close()
        if row:
            return {
                'file_id': row[0],
                'userid': row[1],
                'file_name': row[2],
                'qr_info': row[3],
                'update_at': row[4],
                'image_path': row[5],
                'video_path': row[6]
        }
        return None  # 파일이 없으면 None 반환
    
    def search_images_by_query(self, user_id, query):
        ret = []
        db = DBConnect.get_db()
        cursor = db.cursor()
        # query를 file_name에 포함하는 파일 검색
        sql_select = "SELECT * FROM files WHERE userid=%s AND file_name LIKE %s"
        try:
            cursor.execute(sql_select, (user_id, f"%{query}%"))
            rows = cursor.fetchall()
            for row in rows:
                temp = {
                    'file_id': row[0],
                    'userid': row[1],
                    'file_name': row[2],
                    'qr_info': row[3],
                    'update_at': row[4],
                    'image_path': row[5],
                    'video_path': row[6]
                }
                ret.append(temp)
        except Exception as e:
            print("search_images_by_query Error:", e)
        finally:
            db.close()
        return ret
    
    # insert
    def insert_file(self, userid, title, qr_info, upload_at, image_path, video_path):
        cursor = DBConnect.get_db().cursor()
        sql_insert = 'insert into files ( userid, file_name, qr_info, upload_at, image_path, video_path) values ( %s, %s, %s, %s, %s, %s)'
        ret_cnt = cursor.execute(sql_insert, ( userid, title, qr_info, upload_at, image_path, video_path))
        DBConnect.get_db().close()
        return f'insert OK : {ret_cnt}'
    
    def delete_file(self, file_id):
        query = "DELETE FROM files WHERE file_id = %s"
        params = (file_id,)
        db = DBConnect.get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()
        cursor.close()
        db.close()

    
    # # update
    # def update_store(store_id, name, address, image, rate, food_type):
    #     cursor = DBConnect.get_db().cursor()
    #     sql_update = 'update files set name=%s, address=%s, image=%s, rate=%s, food_type=%s where store_id=%s'
    #     ret_cnt = cursor.execute(sql_update, (name, address, image, rate, food_type, store_id))
    #     DBConnect.get_db().close()
    #     return f'update OK : {ret_cnt}'
    
    # # update rate only
    # def update_store_rate(store_id, rate):
    #     cursor = DBConnect.get_db().cursor()
    #     sql_update = 'UPDATE STORE SET RATE=%s WHERE STORE_ID=%s'
    #     ret_cnt = cursor.execute(sql_update, (rate, store_id))
    #     DBConnect.get_db().close()
    #     return f'update OK : {ret_cnt}'
    
    # # delete
    # def delete_store(self, store_id):
    #     cursor = DBConnect.get_db().cursor()
    #     sql_delete = 'delete from files where store_id=%s'
    #     ret_cnt = cursor.execute(sql_delete, (store_id))
    #     DBConnect.get_db().close()
    #     return f'delete OK : {ret_cnt}'
