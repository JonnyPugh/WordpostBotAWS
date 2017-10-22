from boto3 import client, resource

client = client("dynamodb")
paginator = client.get_paginator("scan")

posts = []
for page in paginator.paginate(TableName="WordpostBotPosts"):
    posts.extend(page["Items"])
print len(posts)

posts_table = resource("dynamodb").Table("WordpostBotPosts")
count = 1
for post in posts:
	post["word"] = post["word"]["S"]
	post["id"] = post["id"]["S"]
	post["reactions"] = False
	print str(count) + ": Updating " + post["id"]
	posts_table.put_item(Item=post)
	count += 1
