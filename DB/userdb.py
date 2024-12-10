import pymysql

class UserDBConnect:
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
        
# DAO : DATA ACCESS OBJECT
# 기능 클래스로 사용
class userDAO :
    # select
    def get_users(self):
        cursor = UserDBConnect.get_db().cursor()
        sql = 'SELECT * FROM login'
        cursor.execute(sql)
        result = cursor.fetchall()
        UserDBConnect.get_db().close()
        return result
    
    # 사용자 인증
    def authenicate(self, useremail):
        try:
            cursor = UserDBConnect.get_db().cursor()
            sql = 'SELECT * FROM login WHERE email=%s'
            cursor.execute(sql,(useremail))
            user = cursor.fetchone()
 
            if user == None:
                return None
            else:
                return user
            
        except Exception as e:
            UserDBConnect.get_db().rollback()
            print("Error:", e)
            return None
        finally:
            UserDBConnect.get_db().close()
    
    # 회원 가입
    def create_user(self, email, passwd, nickname, name):
        try:
            cursor = UserDBConnect.get_db().cursor()

            # 중복 이메일이 있는지 확인
            check_email_sql = 'SELECT COUNT(*) FROM login WHERE email = %s'
            cursor.execute(check_email_sql, (email,))
            email_result = cursor.fetchone()
            
            # 중복 닉네임이 있는지 확인
            check_nickname_sql = 'SELECT COUNT(*) FROM login WHERE nickname = %s'
            cursor.execute(check_nickname_sql, (nickname,))
            nickname_result = cursor.fetchone()

            # 중복 검사 결과 확인
            if email_result[0] > 0:
                return [False, "이미 사용 중인 이메일입니다."]
            elif nickname_result[0] > 0:
                return [False, "이미 사용 중인 닉네임입니다."]

            sql = 'INSERT INTO login ( email, pwd, nickname, name ) VALUES (%s,%s,%s,%s)'
            cursor.execute(sql,(email, passwd, nickname, name))
            return [True,"회원 가입 성공했습니다."]
        
        except Exception as e:
            UserDBConnect.get_db().rollback()
            print("Error:", e)
            return [False,"서버 에러"]
        finally:
            UserDBConnect.get_db().close()
        
    # 회원 정보 수정
    def update_user(self, userno, email, name, nickname):
        try:
            cursor = UserDBConnect.get_db().cursor()
            sql = 'UPDATE login SET email=%s, name=%s, nickname=%s WHERE userno=%s'
            ret_cnt = cursor.execute(sql,( email,  name, nickname, userno))
        except Exception as e:
            UserDBConnect.get_db().rollback()
            print("Error:", e)
        finally:
            UserDBConnect.get_db().close()
    
    # 회원 비밀번호 수정
    def update_pwd(self, userno, new_password):
        try:
            cursor = UserDBConnect.get_db().cursor()
            sql = 'UPDATE login SET passwd=%s WHERE userno=%s'
            ret_cnt = cursor.execute(sql,( new_password, userno))
        except Exception as e:
            UserDBConnect.get_db().rollback()
            print("Error:", e)
        finally:
            UserDBConnect.get_db().close()

    # 회원 탈퇴
    def delete_user(self, userno):
        try:
            cursor = UserDBConnect.get_db().cursor()
            sql = 'DELETE FROM login WHERE userno=%s'
            ret_cnt = cursor.execute(sql,(userno))
        except Exception as e:
            UserDBConnect.get_db().rollback()
            print("Error:", e)
        finally:
            UserDBConnect.get_db().close()
        