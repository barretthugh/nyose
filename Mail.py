from __future__ import print_function
from apiclient.discovery import build
from apiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
import base64
import email
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os
import sys
import time

class Communicator(object):

	def __init__(self):
		self.server_name = 'thebluesday@gmail.com'
		self.master_name = 'thtrieu@apcs.vn'
		self.server = self.getService(self.server_name)
		self.master = self.getService(self.master_name)
	#Used
	def getService(self, name):
		CLIENT_SECRET = 'clientSecrets.json'
		SCOPES = ['https://mail.google.com/']
		SCOPES += ['https://www.googleapis.com/auth/gmail.compose']
		SCOPES += ['https://www.googleapis.com/auth/gmail.modify']
		SCOPES += ['https://www.googleapis.com/auth/gmail.settings.sharing']
		SCOPES += ['https://www.googleapis.com/auth/gmail.settings.basic']
		store = file.Storage('storage_{}.json'.format(name))
		creds = store.get()
		if not creds or creds.invalid:
			print('Credentials for {}'.format(name))
			flow = client.flow_from_clientsecrets(CLIENT_SECRET, SCOPES)
			creds = tools.run_flow(flow, store)
		return build('gmail', 'v1', http=creds.authorize(Http()))
	#Used
	def ListMessagesFromSender(self, service, sender):
		user_id = 'me'
		query = 'from:{}'.format(sender)
		try:
			response = service.users().messages().list(userId=user_id,q=query).execute()
			messages = []
			if 'messages' in response:
				messages.extend(response['messages'])

			while 'nextPageToken' in response:
				page_token = response['nextPageToken']
				response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
				messages.extend(response['messages'])

			return messages
		except errors.HttpError, error:
			print('An error occurred: {}'.format(error))
			return False
	#Used
	def pretty(self, decode):
		d = decode.split('\n')
		res = list()
		for i in range(0, len(d)):
			d_i = d[i]
			d_i = d_i.strip()
			# to detect quoting in replies
			s = '{}'.format(self.server_name)
			m = '{}'.format(self.master_name)
			if s in d_i or m in d_i:
				break
			if d_i == '': continue
			res.append(d_i)
		return res
	#Used
	def GetMessage(self, service, msg_id):
		user_id = 'me'
		try:
			message = service.users().messages().get(userId=user_id, id=msg_id, format=u'full').execute()
			raw = message['payload']['parts'][0]['body']['data']
			hds = message['payload']['headers']
			subject = str()
			for hd in hds:
				if hd['name'] == 'Subject':
					subject = hd['value']
					break
			#print (subject)
			decoded = base64.urlsafe_b64decode(str(raw))
			return (subject, self.pretty(decoded))
		except errors.HttpError, error:
			print('An error occurred: {}'.format(error))
			return False
	#Used
	def SendMessage(self, service, message):
		user_id = 'me'
		try:
			message = (service.users().messages().send(
				userId=user_id, body=message).execute())
			return message
		except errors.HttpError, error:
			print(message)
			print('An error occurred: {}'.format(error))
			return False
	#Used
	def CreateMessage(self, sender, to, subject, 
		message_text, thread_id = ''):
		
		message = MIMEText(message_text)
		message['to'] = to
		message['from'] = sender
		message['subject'] = subject
		send = {'raw': base64.urlsafe_b64encode(message.as_string())}
		if thread_id != '':	send['threadId'] = thread_id
		return send

	def CreateMessageWithAttachment(self, sender, to, subject, 
		message_text, file_dir, filename, thread_id):

		message = MIMEMultipart()
		message['to'] = to
		message['from'] = sender
		message['subject'] = subject

		msg = MIMEText(message_text)
		message.attach(msg)
		path = os.path.join(file_dir, filename)
		content_type, encoding = mimetypes.guess_type(path)

		if content_type is None or encoding is not None:
			content_type = 'application/octet-stream'
		main_type, sub_type = content_type.split('/', 1)
		if main_type == 'text':
			fp = open(path, 'rb')
			msg = MIMEText(fp.read(), _subtype=sub_type)
			fp.close()
		elif main_type == 'image':
			fp = open(path, 'rb')
			msg = MIMEImage(fp.read(), _subtype=sub_type)
			fp.close()
		elif main_type == 'audio':
			fp = open(path, 'rb')
			msg = MIMEAudio(fp.read(), _subtype=sub_type)
			fp.close()
		else:
			fp = open(path, 'rb')
			msg = MIMEBase(main_type, sub_type)
			msg.set_payload(fp.read())
			fp.close()

		msg.add_header('Content-Disposition', 'attachment', filename=filename)
		message.attach(msg)

		send = {'raw': base64.urlsafe_b64encode(message.as_string())}
		if thread_id != '':
			send['threadId'] = thread_id
		return send
	#Used
	def DeleteThread(self, service, thread_id):
		user_id = 'me'
		try:
			m = (service.users().threads().delete(
								userId=user_id,id=thread_id).execute())
			return m
		except errors.HttpError, error:
			print('An error occurred: {}'.format(error))
			return False


class Mail(object):
	def __init__(self, reinit, debug, file = 'newest'):
		self.file = file
		self.debug = debug
		self.load()
		self.newestMailSig = self.newestProcess
		self.compiled = self.compileDefault()
		self.sigs = {'plan': ['del','add','fix','mov'],
				'jnal': ['fin','log','qry'],
				'wtab': ['set','qry'],
				'tenw': ['qry','mig','pin','dln','sbm','del'],
				'conf': ['int','nti','dye','ref','kil','upd'],
				'mail': ['how']}
		self.composing = dict()
		self.instruction = self.buildHowTo()
		self.c = Communicator()
		self.thread_and_subj = (str(), str())
		self.sendSeparateList = dict()
		if not reinit:
			print ('clean communications')
			self.clean()

	def compileDefault(self):
		default = dict()
		default['conf'] = [0, 0, 0, 0, False, False]
		return default

	#=======================+
	# API Related functions |
	#=======================+

	def tryUntil(self, obj, *args, **kwargs):
		flag = False
		while not flag:
			r = obj(*args, **kwargs)
			if r is False:
				print('operation failed, tryin again')
				time.sleep(5)
			else:
				flag = True
		return r

	def clean(self):
		
		def clean_ft(from_name, to_service):
			messes = self.tryUntil(
				self.c.ListMessagesFromSender, 
				to_service, from_name)
			threadIds = set()
			for mess in messes:
				threadIds.add(mess['threadId'])
			for threadId in threadIds:
				_ = self.tryUntil(self.c.DeleteThread,
					to_service, threadId)

		clean_ft(self.c.master_name, self.c.server)
		clean_ft(self.c.server_name, self.c.master)
		self.dlnsThread = str()
		self.planThread = str()
		self.evntThread = str()
		self.jnalThread = str()
		self.caldThread = str()

	def update(self):
		# build self.compiled here, assume init with compileDefault
		# set self.thread here
		# Set self.newestMailSig here
		orders = self.tryUntil(
			self.c.ListMessagesFromSender, 
			self.c.server, self.c.master_name)
		flag = False
		i = 0
		while i < len(orders) and orders[i]['id'] != self.newestProcess:
			mail_i = self.tryUntil(
				self.c.GetMessage,
				self.c.server, orders[i]['id'])
			if i == 0:
				flag = True
				self.newestMailSig = orders[0]['id']
				self.thread_and_subj = (orders[0]['threadId'], mail_i[0])
				self.compiled['compile'] = list()
			self.compiled['compile'] = mail_i[1] + self.compiled['compile']
			i += 1
		if not flag: return
		self.parse()

	def parse(self):

		def add(key, content):
			if key in self.compiled:
				self.compiled[key].append(content)
			else:
				self.compiled[key] = [content]

		def paste(order, i):
			return order[:i] + [' '.join(order[i:])]

		for line in self.compiled['compile']:
			order = line.split()
			order[0] = order[0].lower()
			sig = order[0]

			kind = 'jnal'
			# For definite kind
			for key in self.sigs:
				if sig in self.sigs[key]:
					kind = key
					break

			# To solve ambiguity in kind
			if sig == 'qry':
				if len(order) == 1:
					kind = 'jnal'
				else:
					try:
						temp = int(order[1])
						kind = 'jnal'
					except:
						if '/' in order[1]:
							kind = 'tenw'
						else:
							if order[1].lower() == 'ten':
								kind = 'tenw'
							else:
								kind = 'wtab'
			if sig == 'del':
				if '/' in order[1]:
					kind = 'tenw'
				else:
					kind = 'plan'
			if sig == 'how':
				if len(order) > 1:
					kind = 'jnal'

			content = False
			# To solve ambiguity in content
			if sig == 'add':
				content = paste(order, 2)
			if sig == 'fix':
				try:
					num = int(order[1])
					if num < 100:
						content = paste(order, 2)
					else:
						content = paste(order, 3)
				except:
					content = paste(order, 3)
			if sig == 'log':
				content = paste(order, 1)
			if sig == 'set':
				try:
					start = int(order[2])
					try:
						end = int(order[3])
						content = paste(order, 4)
					except:
						content = paste(order, 3)
				except:
					content = paste(order, 2)
			if sig == 'pin':
				if order[1].find('/') > -1:
					content = paste(order, 2)
				else:
					content = paste(order, 1)
			if sig == 'dln':
				content = paste(order, 2)

			# jump straigt to config
			if sig == 'int':
				self.compiled['conf'][0] = int(order[1])
			if sig == 'nti':
				self.compiled['conf'][1] = int(order[1])
			if sig == 'dye':
				self.compiled['conf'][2] = int(order[1])
			if sig == 'ref':
				self.compiled['conf'][3] = int(order[1])
			if sig == 'kil':
				self.compiled['conf'][4] = True
			if sig == 'upd':
				self.compiled['conf'][5] = True
			
			# Now for the rest cases
			if kind != 'conf': 
				if not content: 
					if kind == 'jnal' and sig not in ['fin', 'qry']:
						content = ['log'] + paste(order,0)
					else:
						content = order
				add(kind, content)

		del self.compiled['compile']

	def send(self, mail):
		subject = str()
		thread_id = str()
		evnt = False
		dlns = False
		plan = False
		jnal = False
		cald = False
		if self.thread_and_subj != (str(), str()):
			thread_id = self.thread_and_subj[0]
			subject = self.thread_and_subj[1]
		else:
			subject = '[nyose] ' + mail['title']
			evnt = 'event' in subject
			dlns = 'deadlines' in subject
			plan = 'plan' in subject
			jnal = 'journal' in subject
			cald = 'calendar' in subject
			if evnt: thread_id = self.evntThread
			if dlns: thread_id = self.dlnsThread
			if plan: thread_id = self.planThread
			if jnal: thread_id = self.jnalThread
			if cald: thread_id = self.caldThread
		if thread_id != str():
			subject = 'Re: ' + subject
		del mail['title']
		message_text = ''

		keys = mail.keys()
		keys.sort()
		
		# delete the redundant
		i = 0
		while i < len(keys):
			if keys[i] == '':
				del keys[i]
				i -= 1
			i += 1

		manyKey = int(len(keys) > 1)
		for i in range(0,len(keys)):
			key = keys[i]
			mail_key = mail[key]
			manyContent = int(len(mail_key) > 1)
			if mail_key == list(): continue
			yesKey = int(key != '')
			message_text += manyKey * '{}. '.format(chr(i+97)) 
			message_text += yesKey * '{}:'.format(key) 
			message_text += manyContent * '\n'
			for j in range(0, len(mail_key)):
				message_text += manyContent * '\t{}.'.format(j+1)
				message_text += ' {}\n'.format(mail_key[j].strip())
		mes = self.c.CreateMessage(self.c.server_name, self.c.master_name, 
			subject, message_text, thread_id)
		thread_id = self.tryUntil(
			self.c.SendMessage,
			self.c.server, mes)['threadId']
		if evnt: self.evntThread = thread_id
		if plan: self.planThread = thread_id
		if jnal: self.jnalThread = thread_id
		if dlns: self.dlnsThread = thread_id
		if cald: self.caldThread = thread_id

	def sendExit(self):
		mail = dict()
		mail['title'] = 'bye bye!'
		mail['message'] = ["I am terminating the moment you read this email"
			+". Revive me soon!"]
		self.send(mail)

	#======================+
	# After parse checking |
	#======================+

	def received(self):
		return self.newestMailSig != self.newestProcess

	def conf(self):
		return self.compiled['conf'] 

	def plan(self):
		return 'plan' in self.compiled

	def jnal(self):
		return 'jnal' in self.compiled

	def wtab(self):
		return 'wtab' in self.compiled

	def tenw(self):
		return 'tenw' in self.compiled

	def howto(self):
		return 'mail' in self.compiled

	#================+
	# Execute orders |
	#================+

	def tutorial(self, order):
		mail = dict()
		mail['transfer'] = 'how to give order'
		mail['instructions'] = '\n' + self.instruction
		return mail

	def doHowto(self):
		self.compose('', self.tutorial, [])
		
	def doPlan(self, plan):
		doings = self.compiled['plan']
		for item in doings:
			if item[0] == 'del':
				self.compose(item, plan.delete, item[1:])
			if item[0] == 'add':
				self.compose(item, plan.add, item[1:])
			if item[0] == 'fix':
				self.compose(item, plan.change, item[1:])
			if item[0] == 'mov':
				self.compose(item, plan.move, item[1:])
		self.sendSeparate(plan.mailFormat())

	def doTenWeek(self, time, plan, tenw, dayend):
		flag = False
		plan_changed = False
		if time.timeStamp >= dayend:
			planFor = time.tmrSig
		else:
			planFor = time.tdSig
		doings = self.compiled['tenw']
		for item in doings:
			if item[0] == 'qry':
				self.compose(item, tenw.query, time, item[1:])
			if item[0] == 'mig':
				self.compose(item, tenw.migrate, time, plan, item[1:])
				self.sendSeparate(plan.mailFormat())
			if item[0] == 'pin':
				self.compose(item, tenw.pin, time, item[1:])
			if item[0] == 'dln':
				plan_changed = self.compose(item, tenw.deadline, planFor, item[1:])
				flag = True
			if item[0] == 'sbm':
				plan_changed = self.compose(item, tenw.submitted, planFor, item[1:])
				flag = True
			if item[0] == 'del':
				plan_changed = self.compose(item, tenw.delete, planFor, item[1:])
				flag = True
		if flag:
			self.sendSeparate(tenw.todayDlMailFormat(time, dayend))
		if plan_changed is True:
			plan.newestPlanList['DEADLINE'] = tenw.dlns(planFor)
			self.sendSeparate(plan.mailFormat())

	def doJournal(self, plan, jnal, time):
		doings = self.compiled['jnal']
		for item in doings:
			if item[0] == 'fin':
				self.compose(item, jnal.finish, item[1:], plan, time)
				self.sendSeparate(plan.mailFormat())
			if item[0] == 'log':
				self.compose(item, jnal.log, item[1:], time)
			if item[0] == 'qry':
				self.compose(item, jnal.review, item[1:], time)

	def doWeekTable(self, wtab):
		doings = self.compiled['wtab']
		for item in doings:
			if item[0] == 'set':
				self.compose(item, wtab.set, item[1:])
			if item[0] == 'qry':
				self.compose(item, wtab.tableQuery, item[1:])


	#====================+
	# Replying to orders |
	#====================+

	def compose(self, item, obj, *args, **kwargs):
		try:
			mailPart = obj(*args, **kwargs)
			flag = False
			if 'plan_changed' in mailPart:
				flag = True
				del mailPart['plan_changed']
			self.composeSuccess(mailPart)
			return flag
		except:
			if self.debug:
				raise
			err = str(sys.exc_info()[0])
			self.composeFailure("{} : {}".format(str(item), err))

	def composeFailure(self, mess):
		key = 'execute fail'
		if key in self.composing:
			self.composing[key].append(mess)
		else:
			self.composing[key] = [mess]

	def composeSuccess(self, mailPart):
		# If the mailPart is too large, it is for a separate mail
		if 'transfer' in mailPart:
			title = mailPart['transfer']
			del mailPart['transfer']
			self.composeSeparateAndSend(part = mailPart, title = title)
		else:
		# mailPart = dict(key: str, key: str, ...)
			for key in mailPart:
				if key in self.composing:
					self.composing[key].append(mailPart[key])
				else:
					self.composing[key] = [mailPart[key]]

	def sendSeparate(self, mailFormat):
		self.sendSeparateList[mailFormat['title']] = mailFormat

	def composeSeparateAndSend(self, part, title):
		composing = self.composing
		thread_and_subj = self.thread_and_subj
		self.composing = dict()
		self.thread_and_subj = (str(),str())
		self.composeSuccess(part)
		self.composing['title'] = title
		self.send(self.composing)
		self.thread_and_subj = thread_and_subj
		self.composing = composing

	def load(self):
		with open(self.file,'r') as f:
			ids = f.readlines()
		l = len(ids)
		if l < 6: ids += [''] * (6-l)
		self.newestProcess = ids[0].strip()
		self.evntThread = ids[1].strip()
		self.planThread = ids[2].strip()
		self.dlnsThread = ids[3].strip()
		self.jnalThread = ids[4].strip()
		self.caldThread = ids[5].strip()

	def dump(self):
		with open(self.file,'w') as f:
			f.write(self.newestProcess+'\n')
			f.write(self.evntThread+'\n')
			f.write(self.planThread+'\n')
			f.write(self.dlnsThread+'\n')
			f.write(self.jnalThread+'\n')
			f.write(self.caldThread)

	def allProcessed(self, title = 'order served'):
		self.composing['title'] = title
		if len(self.composing.keys()) != 1:
			self.send(self.composing)
		self.newestProcess = self.newestMailSig
		self.dump()
		self.composing = dict()
		self.thread_and_subj = (str(), str())
		self.compiled = self.compileDefault()
		for key in self.sendSeparateList:
			self.send(self.sendSeparateList[key])
		self.sendSeparateList = dict()

	#============+
	# Helper     |
	#============+

	def buildHowTo(self):
		return """
			# To delete a plan item
			del <?char>:todo <num>

			# To delete a calenda item
			del <date> <td/dl> <num>

			# To add a plan item:
			add <char/stamp/todo> <content> 

			# To change content of a plan item
			fix <?char/stamp>:todo <num> <content>

			# To move a todo item to a timed item
			mov <num> <char/stamp>

			# To move a timed item to a todo item
			mov <char/stamp> <num>

			# To mark that a todo item is done
			fin <?char>:todo <num>

			# To log a thought
			log <content>

			# To review the journal of a few recent days
			qry <?num>:1

			# To set new content inside the week table
			set <wday> <?start>:0600 <?end>:start <content>

			# To query contents from the table
			qry <wday> <?start>:0600 <?end>:start

			# To check todo and deadlines during a period of time
			qry <start-date> <?end-date>:start-date

			# To migrate a plan item to tomorrow
			mig <?char>:todo <num>

			# To pin a todo onto caledar
			pin <?date>:tomorrow <content> 

			# To pin a deadline onto calendar
			dln <date> <content>

			# To check a that some deadlines in notice list is submitted
			sbm <num> <num> <num>...

			# To query the 10-week calendar
			qry ten

			# To set a new interval
			int <num>

			# To set a new notification time
			nti <num>

			# To set a new dayend
			dye <num>

			# To set a new refresh interval for mail service
			ref <num_minute>

			# To terminate nyose
			kil

			# To update code
			upd
			"""