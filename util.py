#!/usr/bin/python3

import urllib
# import http.cookiejar

import shlex
import requests
import json
import traceback
import logging
import time
# from http.cookiejar import LWPCookieJar

import smtplib
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText

ME = 'orighost@sina.com'
USERNAME = 'orighost@sina.com'
PASSWORD = 'xxxxxx'
SMTP = 'smtp.sina.com'
RECEIPT = ['qujinshan@hujiang.com', 'orighost@sina.com', 'liuxiaolong@hujiang.com']

header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0"}
session = requests.Session()
session.headers.update(header)


# create logger
logger = logging.getLogger('music_163')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

fh = logging.FileHandler('163.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

log = logger


def parseCurlCommand(s):
	# 'curl -H "Host: www.renren.com" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" -H "Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3" -H "X-Requested-With: XMLHttpRequest" -H "Referer: http://www.renren.com/ajaxproxy.htm" -H "Cookie: anonymid=iqspb2qi-rp8hdc; depovince=GW; jebecookies=257e3ec3-9a35-405e-b697-0d56d6b96629|||||; _r01_=1; ick_login=87749530-8717-46c5-a0dc-bf2cebadd3fd; jebe_key=7b60a391-d2f5-4496-a464-57c54f55a8c7%7Ccfcd208495d565ef66e7dff9f98764da%7C1468886856874%7C0%7C1468886856894" --data "email=pengyouya123&icode=&origURL=http%3A%2F%2Fwww.renren.com%2Fhome&domain=renren.com&key_id=1&captcha_type=web_login&password=109233144d177ac10fe2412ea1e3a84136d25d2c33f9e205216827b31214abda&rkey=9801aa5c0a76cd5b3569ef42cbc8520b&f=" --compressed http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=201662834507'
	lexer = shlex.shlex(s)
	lexer.wordchars += '-'

	tokens = []
	parms = None
	url = None

	url = shlex.split(s)[-1]

	while True:
		t = lexer.read_token()
		if not t:
			break

		if t == '-H':
			tokens.append(lexer.get_token())
		elif t == '--data-binary':  # may just --data
			tmp = lexer.get_token().strip('"')
			tmpData = urllib.parse.parse_qsl(tmp, keep_blank_values=True)
			parms = {key: value for key, value in tmpData}

	def hs(s):
		x = s.strip('"')
		t = x.split(': ')
		return {t[0]: t[1]}

	r = list(map(hs, tokens))
	headers = {}

	for item in r:
		headers.update(item)

	return (url, parms, headers)


def formatCURL(cmd):
	(url, parms, headers) = parseCurlCommand(cmd)
	print(url)
	print(parms)
	print(headers)


def simulateCURL(session, cmd):
	(url, parms, headers) = parseCurlCommand(cmd)
	# Cookie 自动传不需要设置
	headers['Cookie'] = None
	r = session.post(url, parms, headers=headers, verify=False)
	# print(r.text)
	return r


# Read web page
def readPage(url, timeout=10, json=False):
	try:
		r = session.get(url, timeout=10, verify=False)
	except:
		traceback.print_exc()
		return None

	if r.history:
		print('Warn: Occur redirect')
		return None

	if json:
		return r.json()
	else:
		return r.text


# Format json string
def formatJSONString(s):
	data = json.loads(s)
	result = json.dumps(data, sort_keys=True, indent=4)
	return result


def sendEmail(subject, body):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['To'] = ','.join(RECEIPT)
	msg['From'] = ME

	s = smtplib.SMTP(SMTP)
	try:
		s.login(USERNAME, PASSWORD)
		s.sendmail(ME, RECEIPT, msg.as_string())
	except SMTPAuthenticationError:
		print('邮箱认证失败')
	except Exception:
		print('发送失败')
	finally:
		s.quit()


def delay(interval):
	time.sleep(interval)
