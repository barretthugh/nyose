import os.path

class Journal(object):
	def __init__(self):
		self.logList = list()

	def logdown(self, time):
		if os.path.isfile('journals/'+time.tdSig):
			mode = 'a'
		else:
			mode = 'w'
		with open('journals/' + time.tdSig, mode) as f:
			for line in self.logList:
				f.write(line+'\n')
		self.logList = list()

	def finish(self, order, plan, time):
		mail = dict()
		todo_i = int(order[0])-1
		content = plan.newestPlanList['TODO'][todo_i]
		self.logList.append("[{}] done todo #{}: '{}'".format(
			time.timeStamp, order[0], content))
		mail['journal'] = "logged that at {}, done todo #{}: '{}'".format(
			time.timeStamp, order[0], content)
		plan.finish(order)
		mail['plan'] = "Marked that you did todo #{}: '{}'".format(
			order[0], content)
		return mail

	def log(self, order, time):
		mail = dict()
		self.logList.append("[{}] {}".format(
			time.timeStamp, order[0]))
		mail['journal'] = "journal logged at {}: '{}'".format(
			time.timeStamp, order[0])
		return mail

	def review(self, order, time):
		mail = dict()
		if len(order) == 0:
			num = 1
		if len(order):
			num = int(order[0])
		self.logdown(time)
		allJnals = os.listdir('journals')
		allJnals.sort()
		jnals = allJnals[-num:]
		content = ['review of {} recent day:'.format(num)]
		for i in range(0, num):
			jnal = jnals[num-i-1]
			with open('journals/'+jnal, 'r') as f:
				retrieved = f.read()
			content += ['\n>> {}:'.format(jnal)] + retrieved.split('\n')
		mail['jnal'] = '\n\t'.join(content)
		if len(content) >= 15:
			mail['transfer'] = content[0]
		return mail