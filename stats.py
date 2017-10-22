from Queue import Queue
from requests import Session
import threading

class Stats(object):
	def __request(self, path):
		r = self.__session.get(path)
		r.raise_for_status()
		return r.json()

	def __get_post_data(self):
		while not self.__ids_to_process.empty():
			post_id = self.__ids_to_process.get()
			reactions = self.__request("https://graph.facebook.com/v2.10/" + post_id + "/reactions")
			while reactions["data"]:
				for reaction in reactions["data"]:
					user_id = reaction["id"]
					reaction_type = reaction["type"]

					self.__lock.acquire()
					self.__user_names[user_id] = reaction["name"]
					if user_id not in self.__users:
						self.__users[user_id] = {}
						self.__user_reactions[user_id] = 0
					if reaction_type not in self.__users[user_id]:
						self.__users[user_id][reaction_type] = 0
					if post_id not in self.__initial_top_posts:
						self.__users[user_id][reaction_type] += 1
						self.__user_reactions[user_id] += 1
						self.__total_reactions += 1
					self.__posts[post_id] += 1
					self.__lock.release()
				if "next" not in reactions["paging"]:
					break
				reactions = self.__request(reactions["paging"]["next"])
			self.__ids_to_process.task_done()

	def __init__(self, access_token, post_ids, top_reactors=[], top_posts=[], total_posts=0, total_reactions=0, num_threads=64):
		self.__users = {}
		self.__user_names = {}
		self.__user_reactions = {}
		for user_info in top_reactors:
			user_id = user_info["id"]
			reactions = user_info["reactions"]
			self.__users[user_id] = reactions
			self.__user_names[user_id] = user_info["name"]
			self.__user_reactions[user_id] = sum(reactions.values())

		self.__posts = {post_id: 0 for post_id in post_ids + top_posts}
		self.__total_posts = len(post_ids) + total_posts
		self.__total_reactions = total_reactions
		self.__initial_top_posts = set(top_posts)

		self.__session = Session()
		self.__session.params = {"access_token": access_token}
		self.__lock = threading.Lock()
		self.__ids_to_process = Queue()
		for post_id in post_ids + top_posts:
			self.__ids_to_process.put(post_id)

		for _ in range(num_threads):
			thread = threading.Thread(target=self.__get_post_data)
			thread.daemon = True
			thread.start()

	def __calculate_stats(self):
		self.__ids_to_process.join()
		try: 
			self.__top_posts
		except AttributeError:
			self.__top_posts = sorted([(post_id, reactions) for post_id, reactions in self.__posts.items()], key=lambda x: x[1], reverse=True)
			self.__top_reactors = []
			for reactor_info in sorted([(user_id, reactions) for user_id, reactions in self.__user_reactions.items()], key=lambda x: x[1], reverse=True):
				user_id = reactor_info[0]
				self.__top_reactors.append({"id": user_id, "name": self.__user_names[user_id], "reactions": self.__users[user_id]})

	def get_top_posts(self, num_posts=100):
		self.__calculate_stats()
		return self.__top_posts[0:num_posts]

	def get_top_post_message(self, num_posts=10):
		self.__calculate_stats()
		message = "***Top "+str(num_posts)+" Posts***\n"
		total_reactions = 0
		ranking = 1
		for post_id, reactions in self.get_top_posts(num_posts):
			message += str(ranking)+". facebook.com/"+post_id+"\n"
			total_reactions += reactions
			ranking += 1
		return message + "Average reactions per post: "+str(float(total_reactions) / num_posts)

	def get_top_reactors(self, num_reactors=100):
		self.__calculate_stats()
		return self.__top_reactors[0:num_reactors]

	def get_top_reactor_message(self, num_reactors=10):
		self.__calculate_stats()
		emoticons = {
		    "LIKE": "\xF0\x9F\x91\x8D",
		    "LOVE": "\xF0\x9F\x92\x9F",
		    "HAHA": "\xF0\x9F\x98\x86",
		    "WOW": "\xF0\x9F\x98\xAE",
		    "SAD": "\xF0\x9F\x98\xA2",
		    "ANGRY": "\xF0\x9F\x98\xA1",
		    "THANKFUL": "\xF0\x9F\x8C\xB8",
		    "PRIDE": "\xF0\x9F\x8C\x88"
		}
		message = "***Top "+str(num_reactors)+" Reactors***\n"
		ranking = 1
		for reactor_info in self.get_top_reactors(num_reactors):
			user_id = reactor_info["id"]
			reactions = self.__user_reactions[user_id]
			reactions_breakdown = " ".join([" ".join([emoticons[reaction_type], str(num)]) for (reaction_type, num) in sorted(self.__users[user_id].items(), key=lambda x: x[1], reverse=True)])
			message += str(ranking)+". "+self.__user_names[user_id]+" - "+str(reactions)+": "+reactions_breakdown.decode("utf-8")+"\n"
			ranking += 1
		return message + "Average reactions per post: "+str(float(self.__total_reactions) / float(self.__total_posts))

	@property
	def total_posts(self):
		self.__calculate_stats()
		return self.__total_posts

	@property
	def total_reactions(self):
		self.__calculate_stats()
		return self.__total_reactions

	@property
	def reactors(self):
		self.__calculate_stats()
		return self.__user_names
