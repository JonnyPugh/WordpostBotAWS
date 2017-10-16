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
        "cursorclass" : DictCursor,
		"charset": "utf8"
    }
    db = connect(**options)
    db.autocommit(True)
    return db
db = connect_to_database()

def execute_query(query):
    cursor = db.cursor()
    cursor.execute(query, params)
    query_results = cursor.fetchall()
    cursor.close()
    return query_results

table = resource("dynamodb").Table("WordpostBotPosts")

for post in execute_query("select word, id from Posts"):
	print post["word"]
	table.put_item(Item={"word": post["word"], "id": post["id"], "reactions": None})
