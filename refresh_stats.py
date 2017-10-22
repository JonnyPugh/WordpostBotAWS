# Refresh the stats that are currently in DynamoDB

from stats import Stats
from boto3 import client, resource

client = client("dynamodb")
paginator = client.get_paginator("scan")

posts = []
for page in paginator.paginate(TableName="WordpostBotPosts", FilterExpression="reactions = :t", ExpressionAttributeValues={":t": {"BOOL": True}}):
    for item in page["Items"]:
    	item["word"] = item["word"]["S"]
    	item["id"] = item["id"]["S"]
    	item["reactions"] = item["reactions"]["BOOL"]
    	posts.append(item)

info_table = resource("dynamodb").Table("WordpostBotInfo")
access_token = info_table.get_item(Key={"resource": "credentials"})["Item"]["access_token"]

stats = Stats(access_token, [post["id"] for post in posts])
stats_item = {"resource": "stats"}
stats_item["total_posts"] = stats.total_posts
stats_item["total_reactions"] = stats.total_reactions
stats_item["top_posts"] = [post_info[0] for post_info in stats.get_top_posts()]
stats_item["top_reactors"] = stats.get_top_reactors()
info_table.put_item(Item=stats_item)
