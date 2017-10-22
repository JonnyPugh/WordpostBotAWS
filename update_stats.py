# Update the stats in DynamoDB to include all posts up until 2 days ago

from stats import Stats
from boto3 import client, resource

def update(event, context):
	posts = []
	paginator = client("dynamodb").get_paginator("scan")
	for page in paginator.paginate(TableName="WordpostBotPosts", FilterExpression="reactions = :t", ExpressionAttributeValues={":t": {"BOOL": False}}):
	    for item in page["Items"]:
	    	item["word"] = item["word"]["S"]
	    	item["id"] = item["id"]["S"]
	    	item["reactions"] = True
	    	posts.append(item)

	sorted_posts = sorted(posts, key=lambda x: x["id"])[0:len(posts) - 96]

	dynamodb = resource("dynamodb")
	info_table = dynamodb.Table("WordpostBotInfo")
	access_token = info_table.get_item(Key={"resource": "credentials"})["Item"]["access_token"]
	stats_item = info_table.get_item(Key={"resource": "stats"})["Item"]

	stats = Stats(access_token, [post["id"] for post in sorted_posts], stats_item["top_reactors"], stats_item["top_posts"], stats_item["total_posts"], stats_item["total_reactions"])

	stats_item["total_posts"] = stats.total_posts
	stats_item["total_reactions"] = stats.total_reactions
	stats_item["top_posts"] = [post_info[0] for post_info in stats.get_top_posts()]
	stats_item["top_reactors"] = stats.get_top_reactors()
	info_table.put_item(Item=stats_item)

	posts_table = dynamodb.Table("WordpostBotPosts")
	for post in sorted_posts:
		posts_table.put_item(Item=post)
