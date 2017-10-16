from config import db_info
from MySQLdb import connect
from MySQLdb.cursors import DictCursor
from boto3 import resource

def connect_to_database():
    options = {
        "host": db_info["host"],
        "user": db_info["user"],
        "passwd": db_info["password"],
        "db": db_info["db"],
        "cursorclass" : DictCursor
    }
    db = connect(**options)
    db.autocommit(True)
    return db
db = connect_to_database()

def execute_query(query, params=None):
    cursor = db.cursor()
    cursor.execute(query, params)
    query_results = cursor.fetchall()
    cursor.close()
    return query_results

table = resource("dynamodb").Table("WordpostBotPosts")

for post in execute_query("select word from Posts"):
	table.put_item(Item={"word": post["word"], "id": post["id"], "reactions": None})
