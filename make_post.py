from requests import Session
from re import match
from boto3 import resource

dynamodb = resource("dynamodb")
info_table = dynamodb.Table("WordpostBotInfo")
credentials = info_table.get_item(Key={"resource": "credentials"})["Item"]

def get_wordnik_json(route):
	r = get_wordnik_json.session.get("https://api.wordnik.com/v4/"+route)
	r.raise_for_status()
	return r.json()
get_wordnik_json.session = Session()
get_wordnik_json.session.params = {"limit": 1, "minLength": 0, "api_key": credentials["wordnik_key"]}

def post_to_page(route, message):
	r = post_to_page.session.post("https://graph.facebook.com/v2.10/"+route, data={"message": message})
	r.raise_for_status()
	return r.json()["id"]
post_to_page.session = Session()
post_to_page.session.params = {"access_token": credentials["access_token"]}

def post_word(route, word):
	word_info = get_wordnik_json("word.json/"+word+"/definitions")[0]
	definition = word_info["text"]
	return post_to_page(route, word+(" - "+word_info["partOfSpeech"] if "partOfSpeech" in word_info else "")+"\n"+definition), definition

def post_root_word(post_id, word, definition):
	# If the definition matches any of these patterns, post
	# the word that is referenced in the definition
	for pattern in [s + " ([^ ]*)[.]" for s in [".* form of", ".* participle of", "See", "Variant of", ".*[.] See Synonyms at", "Alternative spelling of", "Relating to", "An abbreviation of", "Common misspelling of", "Of or pertaining to", "Superlative of", "Obsolete spelling of", "Informal", "To", "The act or process of", "One who believes in"]] + ["([^ .]*)[.]?", "Alternative capitalization of ([^ ]*)", "In an? ([^ ]*) manner."]:
		reference_word = match("^"+pattern+"$", definition)
		if reference_word:
			root_word = reference_word.group(1)

			# If the definition is a single word, make it lowercase because
			# the wordnik API is case sensitive and single word definitions
			# may have been capitalized
			if pattern == "([^ .]*)[.]?":
				root_word = root_word.lower()

			# Post the root word and write to the log
			post_id, new_definition = post_word(post_id+"/comments", root_word)

			# Save off the id of the first posted comment because all subsequent
			# comments should be replies to this initial comment
			if not post_root_word.comment_id:
				post_root_word.comment_id = post_id

			# Check the root word's definition for other referenced words
			post_root_word(post_root_word.comment_id, root_word, new_definition)
post_root_word.comment_id = None

def make_post(event, context):
	posts = dynamodb.Table("WordpostBotPosts")

	# Get a random word that has not been posted yet
	while True:
		word = get_wordnik_json("words.json/randomWord")["word"]
		if "Item" not in posts.get_item(Key={"word": word}):
			break

	# Make a post and insert its data into the database
	post_id, definition = post_word(credentials["page_id"]+"/feed", word)
	posts.put_item(Item={"word": word, "id": post_id, "reactions": False})

	# If the posted word references a root word, post the 
	# definition of the root word as a comment
	post_root_word(post_id, word, definition)
