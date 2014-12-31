#!/usr/bin/env python
#-*- coding:utf-8 -*-
Ver = 'CLI--0.0.1'

import select
import httplib
import re
import os, sys
import PIL.Image, PIL.ImageTk
import urllib2
import urllib
import cookielib
import time

import myOCR

#----------------------------------------------------
URL = {
	"Host" : "http://222.30.32.10/",
	"ValidateCode" : "http://222.30.32.10/ValidateCode",
	"Login" : "http://222.30.32.10/stdloginAction.do",
	"Post" : "http://222.30.32.10/xsxk/swichAction.do"
}

Login_S = False
StopSignal = False

STUDENT_ID='1210020'
PASSWORD='****'

HEADERS= {
'Accept':' application/x-ms-application, image/jpeg, application/xaml+xml, image/gif, image/pjpeg, application/x-ms-xbap, */*',
'Referer':' http://222.30.32.10/xsxk/swichAction.do',
'Accept-Language':' zh-CN',
'Content-Type':' application/x-www-form-urlencoded',
'Accept-Encoding':' gzip, deflate',
'User-Agent':' Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; InfoPath.3)',
'Host':' 222.30.32.10',
'Pragma':' no-cache',
'Cookie':''
}

PROCESSING = False

#--------------------------------------------------------------------------------------------
def ReLoadData():
	global HEADERS
	global PROCESSING
	global Login_S
	global headers
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","/")
		res=conn.getresponse()
		cookie=res.getheader("Set-Cookie")
		conn.close()
	except:
		return False
	headers= HEADERS
	headers['Cookie'] = cookie
	#get ValidateCode
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","http://222.30.32.10/ValidateCode","",headers)
		res=conn.getresponse()
		f=open("ValidateCode.jpg","w+b")
		f.write(res.read())
		f.close()
		conn.close()
	except:
		return False
	HEADERS = headers
	PROCESSING = False
	Login_S = False
	return True

#----------------------------------------------------
def INIT():
	global ValidateCode
	Network=True
	if not ReLoadData():
		Network=False
	ValidateCode=PIL.Image.open("ValidateCode.jpg")
	if not Network:
		print "网络连接错误，无法连接到选课系统。请检查网络连接！"
		return False
	return True


def Login():
	global HEADERS
	global STUDENT_ID
	global PASSWORD
	global Login_S
	global ValidateCode
	v_code=myOCR.myOCR_start(ValidateCode)
	try:
		logindata="operation=&usercode_text="+STUDENT_ID+"&userpwd_text="+PASSWORD+"&checkcode_text="+v_code+"&submittype=%C8%B7+%C8%CF"
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("POST","http://222.30.32.10/stdloginAction.do",logindata,HEADERS)
		res=conn.getresponse()
		response=res.read()
		content=response.decode("gb2312")
		conn.close()
	except:
		print "网络连接错误，无法连接到选课系统。请检查网络连接！"
		return False
	
	
	if content.find("stdtop") != -1:
		Login_S = True
		#print "登录成功！"
	
	err_code = "未知错误！"		
	if Login_S == False and (content.find(unicode("请输入正确的验证码","utf8")) != -1):
		err_code="验证码错误！"
		while not INIT():
			continue
		return Login()
		
	if Login_S == False and (content.find(u"用户不存在或密码错误") != -1):
		err_code="用户不存在或密码错误！"
		
	if Login_S == False and (content.find(u"忙") != -1 or content.find(u"负载") != -1):
		err_code="系统忙，请稍后再试！"
	
	if (Login_S != True):
		print err_code
	return Login_S
	
def AutoLogin():
	global STUDENT_ID
	global PASSWORD
	global Login_S
	if STUDENT_ID=='' or PASSWORD=='':
		err_code="无法验证用户名及密码，自动登录失败！"
		print err_code
		return False
	count=0
	while count<5:
		count+=1
		print '尝试重新登录...'
		if not INIT():
			continue
		else:
			Login()
		if not Login_S:
			print '重新登录失败...3秒后重试'
			for i in range(12):
				time.sleep(0.25)
		else:
			print "登录成功！"
			return True
	return False

def Start_Cmd(self, event=None):
	#------------------------------------------------------------------
	global PROCESSING
	global Login_S
	global HEADERS
	global StopSignal
	#------------------------------------------------------------------
	if not self.CheckLogin():
		err_code="请先登录！"
		self.Log.insert(1.0,err_code+'\n')
		self.Log.update()
		self.Stop_Cmd()
		return
	#------------------------------------------------------------------
	course=self.GetCourseCode()
	if course==None:
		err_code="请输入课程代号\n"
		self.Log.insert(1.0,err_code)
		self.Log.update()
		self.Stop_Cmd()
		return
	illegal=self.illegal_list(course)
	if illegal[0]!=[]:
		err_code="请核对后重新开始！\n"
		self.Log.insert(1.0,err_code)
		self.Log.update()
		for i in range(len(illegal[0])):
			err_code=illegal[0][i]+' '+illegal[1][i]+'\n'
			self.Log.insert(1.0,err_code)
			self.Log.update()
		err_code="以下课号有误：\n"
		self.Log.insert(1.0,err_code)
		self.Log.update()
		self.Stop_Cmd()
		return
	#------------------------------------------------------------------
	PROCESSING=True
	if not self.CheckSystemStatus():
		self.Log.delete(20.0,END)
		self.wait_for_system()
		if not self.CheckSystemStatus():
			if not StopSignal:
				err_code="未知错误。请重新点击“开始刷课”！"
				self.Log.insert(1.0,err_code+'\n')
				self.Stop_Cmd()
				StopSignal=False
			else:
				StopSignal=False
			return
	#------------------------------------------------------------------
	
	#------------------------------------------------------------------
	self.Log.delete(0.0,END)
	self.Log.insert(1.0,"Starting........Connecting............\n")
	self.Log.update()
	#------------------------------------------------------------------
	use_queue=True
	mode='queue'
	count=0
	if self.Var.get()=='1' or self.Var.get()=='':
		use_queue=True
	else:
		use_queue=False
	while PROCESSING:
		count += 1
		if use_queue:
			mode='queue'
		else:
			mode='stack'
		post_course,course=self.select_course(course,mode)
		#print post_course
		#course=self.select_course(course,mode)[1]
		#print course
		fail_course=self.PostData(post_course,count)
		#print fail_course
		course=self.merge_course_list(course,fail_course,mode)
		#print course
		if len(course)>0:
			pass
		else:
			succ_code="刷完啦~\n"
			self.Log.insert(1.0,succ_code)
			self.Log.update()
			self.Stop_Cmd()
			StopSignal=False

def Stop_Cmd(self, event=None):
	global PROCESSING
	global StopSignal
	if not PROCESSING:
		return
	self.Log.update()
	PROCESSING = False
	self.Log.insert(1.0,'>>>>>>已停止<<<<<<\n')
	self.Log.update()
	StopSignal=True
	return
	
def Refresh_Cmd(self, event=None):
	self.vcode.delete(0,END)
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=3)
		conn.request("GET","http://222.30.32.10/ValidateCode","",headers)
		res=conn.getresponse()
		f=open("ValidateCode.jpg","w+b")
		f.write(res.read())
		f.close()
		conn.close()
	except:
		return False
	#self.photo.close()
	self.photo=PIL.Image.open("ValidateCode.jpg")
	self.im = PIL.ImageTk.PhotoImage(self.photo)
	self.V_Pic= Label(self.top,image = self.im)
	self.V_Pic.place(relx=0.05, rely=0.203, relwidth=0.327, relheight=0.053)
	return True
	
def select_course(self, course_list, mode):
	selected_list=[]
	if mode=='queue':
		for i in range(min(4,len(course_list))):
			selected_list.append(course_list.pop(0))
		return (selected_list,course_list)
	else:
		for i in range(min(4,len(course_list))):
			selected_list.append(course_list.pop())
		return (selected_list,course_list)
	
def merge_course_list(self, course_list, selected_list, mode):
	if mode=='queue':
		for i in range(len(selected_list)):
			course_list.append(selected_list.pop(0))
		return course_list
	else:
		for i in range(len(selected_list)):
			course_list.append(selected_list.pop())
		return course_list
	
def PostData(self, post_course_list, count):
	self.Log.delete(20.0,END)
	self.Log2.delete(20.0,END)
	course=[]
	for i in range(4):
		course.append('')
	for i in range(len(post_course_list)):
		course[i]=post_course_list[i]
	info='第'+str(count)+'次抢课进行中……正在抢：\n'
	for i in range(len(post_course_list)):
		info += (course[i]+' '+self.GetName(course[i])+'\n')
	self.Log.insert(1.0,info)
	self.Log.update()
	
	postdata="operation=xuanke&index="
	for i in range(4):
		if i<len(course):
			postdata += ("&xkxh"+str(i+1)+"="+course[i])
		else:
			postdata += ("&xkxh"+str(i+1)+"=")
	postdata += "&de=%25&courseindex="
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("POST","http://222.30.32.10/xsxk/swichAction.do",postdata,headers)
		res=conn.getresponse()
	except:
		self.Log.insert(1.0,"网络连接错误。请检查网络连接！\n")
		if not self.AutoLogin():
			return post_course_list
	#太久不管的话cookie会失效
	if res.status == 302:
		self.Log.insert(1.0,"登录超时，请重新登录\n")
		Login_S = False
		if not self.AutoLogin():
			return post_course_list
	response=res.read()
	content=response.decode("gbk").encode('utf-8')
	#----------------------------------------------------------
	#----------------------抓取-------------
	reg = re.compile(u'"BlueBigText">[\s\S]*</font>') 
	Data = reg.findall(content)
	#---------------截取--------------------\
	if Data != []:
		Data=Data[0]
		Data=Data[14:]
		Data=Data[:-10]
		Err = re.compile(r'无效，')
		Err = Err.findall(Data)
		#------------是否存在无效序号---------
		if Err != [ ]:
			self.Log2.insert(1.0,('有无效序号无法判断\n'))
			self.Log2.update()
			self.Log.insert(1.0,('>>>>>>已停止<<<<<<\n\nERROR!\n\n'))
			self.Log.update()
			return
	else:
		Data = ''
	#---------------End---------------------
	#----------------------------------------
	fail_course=[]
	for course_code in post_course_list:
		if re.search(course_code,Data) != None:
			fail_course.append(course_code)
		else:
			self.Log2.insert(1.0,(course_code+' '+self.GetName(course_code)+'\n'))
	self.Log2.update()
	#--------------------输出选课系统状态返回---------------------
	self.Log.insert(1.0,(Data+'\n'))
	self.Log.update()
	if len(fail_course)==0:
		self.Log.insert(1.0,('刷完啦~\n'))
		self.Log.update()
		return fail_course
	#-----------------------------------------------------------
	if PROCESSING==False:
		return fail_course
	self.Log.insert(1.0,'-----------------休眠5秒--------------------\n')
	#-------------保持刷新防止假死------------
	for j in range (0,20):
		self.Log.update()
		time.sleep(0.2492)
		self.Log.update()
		if PROCESSING==False:
			return fail_course
	#---------------------------------------------
	return fail_course

	
def CheckLogin(self):
	global	Login_S
	return Login_S
		
def CheckSystemStatus(self):
	global PROCESSING
	XuanKeButton = re.compile(u'''<input type="button" name="xuanke"''')
	XKButton = []
	list=''
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","http://222.30.32.10/xsxk/selectMianInitAction.do",list,self.headers)
		XKButton = XuanKeButton.findall(conn.getresponse().read().decode("gbk").encode('utf-8'))
		if XKButton == [] :
			return False
		else:
			return True
	except:
		print "网络连接错误，无法连接到教务处系统。请检查网络连接！"
		if ReLoadData():
			self.Refresh_Cmd()
		else:
			PROCESSING=False
			return False
	return False
			
def wait_for_system(self):
	global PROCESSING
	while not self.CheckSystemStatus():
		if not PROCESSING:
			return
		print "Waiting... (3s)"
		for j in range (0,12):
			time.sleep(0.25)
			self.Log.update()
			if not PROCESSING:
				return
	return
	
def GetName(c_code):
	if c_code == "":
		return ""
	h={
			'Host': '222.30.32.3',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
			'Origin': 'http://222.30.32.3',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Referer': 'http://222.30.32.3/apps/xksc/index.asp',
			'Accept-Encoding': 'gzip,deflate,sdch',
	}
	try:
		conct = httplib.HTTPConnection('222.30.32.3',timeout=10)
		formdata = 'strsearch='+str(c_code)+'&radio=1&Submit=%CC%E1%BD%BB'
		conct.request('POST','http://jwc.nankai.edu.cn/apps/xksc/index.asp',formdata,h)
		contnt = conct.getresponse().read().decode("gb2312")
		conct.close()
	except:
		return "无法获取课程名称"
	pos=contnt.find('</TD></TR><TR><TD>')
	if pos == -1:
		return "wrong_course"
	else:
		contnt=contnt[pos:]
		HTMLTarget_re = re.compile('</*T(D|R)>')
		contnt = HTMLTarget_re.sub('|',contnt)
		return re.findall(u"[0-9a-zA-Z\u4e00-\u9fa5\uFF00-\uFFEF\-\+、]+",contnt)[1].encode('utf8')



if __name__ == "__main__":
	try:
		f=open("ValidateCode.jpg","r")
	except:
		f=open("ValidateCode","r")
		ff=open("ValidateCode.jpg","w+b")
		d=f.read()
		ff.write(d)
		f.close()
		ff.close()
	print ReLoadData()
	print INIT()
	print GetName('1920')
	AutoLogin()

