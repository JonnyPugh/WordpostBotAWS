from boto3 import resource

dynamodb = resource("dynamodb")

table = dynamodb.create_table(
    TableName="WordpostBotPosts",
    KeySchema=[
        {
            "AttributeName": "word",
            "KeyType": "HASH"
        }
    ],
    AttributeDefinitions=[
        {
            "AttributeName": "word",
            "AttributeType": "S"
        }
    ],
    ProvisionedThroughput={
        "ReadCapacityUnits": 1,
        "WriteCapacityUnits": 1
    }
)

table.meta.client.get_waiter("table_exists").wait(TableName="WordpostBotPosts")

print(table.item_count)
