from pymongo import MongoClient
from datetime import datetime
import hashlib  
import requests
from util import session
from util import log
import os
import traceback
from util import delay

# client = MongoClient("mongodb://purkylin.com:27017")
# db = client.dev
# dogs = db.Dog
# # print(dogs, dogs.count())
# for o in dogs.find():
# 	print(o['name'], o['age'])

# now = datetime.datetime.utcnow()
# dog = {"_created_at": now, '_updated_at': now, 'name': 'hisi', 'age':22}
# myid = dogs.insert_one(dog).inserted_id
# print(myid)

client = MongoClient("mongodb://purkylin.com:27017")
db = client.dev
songs = db.Songs
print('count', songs.count())

# 榜单歌曲批量下载
# 网易原创歌曲榜 云音乐飙升榜 云音乐热歌榜 云音乐新歌榜 itune
list_id = ['2884035', '19723756', '3778678', '3778678', '11641012']
header = {'Cookie': 'appver=1.5.0.75771', 'Referer': 'http://music.163.com/'}


def downMusic(url, sid):
	if os.path.exists('mp3/%s.mp3' % sid):
		log.info('Already downloaded')
		return

	r = session.get(url, timeout=30)
	with open('mp3/%s.mp3' % sid, 'wb') as fp:
		fp.write(r.content)

	log.info('Down finish')

def isSongExists(sid):
	if not sid:
		print('Warn: sid is empty')
		return True
	song = songs.find_one({'sid': sid})

	if song:
		log.info(song['sid'])
		return True
	else:
		return False


class Song:
	def __init__(self, sid, name, artist, url, createTime, source='163'):
		self.sid = sid
		self.name = name
		self.artist = artist
		self.url = url
		self.createTime = createTime
		self.source = source

	def toJSON(self):
		return {'sid': self.sid,
				'name': self.name, 
				'artist': self.artist,
				'url': self.url, 
				'createTime': self.createTime, 
				'source': self.source
		}

	def isExists(self):
		return songs.find({'sid': self.sid}) != None

	def __str__(self):
		return 'id:{}, name:{}'.format(self.sid, self.name)


	def download(self):
		downMusic(self.url, self.sid)

	def save(self, needDownload=True):
		if needDownload:
			try:
				self.download()
			except Exception as e:
				log.error('May timeout')

		d = self.toJSON()
		iid = songs.insert_one(d).inserted_id
		if iid:
			log.info('insert success')
		else:
			log.error('insert fail')


# http://music.163.com/api/song/detail/?id=28377211&ids=%5B28377211%5D


def test163():
	url = 'http://music.163.com/api/playlist/detail?id={}'.format(list_id[0])
	log.info(url)
	log.info('Grab album ...')
	r = requests.get(url)
	data = r.json()
	result = data['result']
	tracks = result['tracks']
	total = len(tracks)

	for i, item in enumerate(tracks):
		log.info('Deal with {}th/{} song'.format(i + 1, total))
		stamp = int(item['album']['publishTime']) / 1000
		t = datetime.fromtimestamp(stamp)

		if isSongExists(item['id']):
			log.warn('The song exists and skip')
			continue

		song = Song(item['id'], item['name'], item['artists'][0]['name'], item['mp3Url'], t, '163')
		song.save()
		delay(1)


def clearDB():
	log.info('Clear database')
	songs.delete_many({'sid': {"$gt": 0}})


if __name__ == '__main__':
	log.info('Begin')
	# clearDB()
	try:
		test163()
	except Exception as e:
		log.info(traceback.format_exc(3)) 

	log.info('Finish')
