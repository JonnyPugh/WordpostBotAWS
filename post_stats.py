# Post a summary of the stats to the Facebook page

from stats import Stats
from boto3 import client, resource
from requests import Session

def make_post(event, context):
	posts = []
	paginator = client("dynamodb").get_paginator("scan")
	for page in paginator.paginate(TableName="WordpostBotPosts", FilterExpression="reactions = :t", ExpressionAttributeValues={":t": {"BOOL": False}}):
	    for item in page["Items"]:
	    	posts.append(item["id"]["S"])

	info_table = resource("dynamodb").Table("WordpostBotInfo")
	credentials = info_table.get_item(Key={"resource": "credentials"})["Item"]
	access_token = credentials["access_token"]
	stats_item = info_table.get_item(Key={"resource": "stats"})["Item"]
	stats = Stats(access_token, posts, stats_item["top_reactors"], stats_item["top_posts"], stats_item["total_posts"], stats_item["total_reactions"])
	session = Session()
	session.params = {"access_token": credentials["access_token"]}
	api_url = "https://graph.facebook.com/v2.10/"
	r = session.post(api_url+credentials["page_id"]+"/feed", data={"message": stats.get_top_reactor_message()})
	r.raise_for_status()
	post_id = r.json()["id"]
	session.post(api_url+post_id+"/comments", data={"message": stats.get_top_post_message()}).raise_for_status()
