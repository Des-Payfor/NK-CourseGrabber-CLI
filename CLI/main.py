#!/usr/bin/env python
#-*- coding:utf-8 -*-
Ver = 'CLI--0.0.1'

import httplib
import re
import PIL.Image, PIL.ImageTk
import time

import myOCR

#----------------------------------------------------
URL = {
	"Host" : "http://222.30.32.10/",
	"ValidateCode" : "http://222.30.32.10/ValidateCode",
	"Login" : "http://222.30.32.10/stdloginAction.do",
	"Post" : "http://222.30.32.10/xsxk/swichAction.do"
}

LoginStatus = False
StopSignal = False

STUDENT_ID = '1210020'
PASSWORD = '****'

HEADERS = {
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


#--------------------------------------------------------------------------------------------
def ReLoadData():
	global HEADERS
	global LoginStatus
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","/")
		res=conn.getresponse()
		cookie=res.getheader("Set-Cookie")
		conn.close()
	except:
		return False
	HEADERS['Cookie'] = cookie
	#get ValidateCode
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","http://222.30.32.10/ValidateCode","",HEADERS)
		res=conn.getresponse()
		f=open("ValidateCode.jpg","w+b")
		f.write(res.read())
		f.close()
		conn.close()
	except:
		return False
	LoginStatus = False
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
	global LoginStatus
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
		LoginStatus = True
		#print "登录成功！"

	err_code = "未知错误！"
	if LoginStatus == False and (content.find(unicode("请输入正确的验证码","utf8")) != -1):
		err_code="验证码错误！"
		while not INIT():
			continue
		return Login()

	if LoginStatus == False and (content.find(u"用户不存在或密码错误") != -1):
		err_code="用户不存在或密码错误！"

	if LoginStatus == False and (content.find(u"忙") != -1 or content.find(u"负载") != -1):
		err_code="系统忙，请稍后再试！"

	if (LoginStatus != True):
		print err_code
	return LoginStatus

def AutoLogin():
	global STUDENT_ID
	global PASSWORD
	global LoginStatus
	if STUDENT_ID=='' or PASSWORD=='':
		err_code="无法验证用户名及密码，自动登录失败！"
		print err_code
		return False
	#count=0
	while 1:#count<5:
		#count+=1
		print '尝试重新登录...'
		if not INIT():
			continue
		else:
			Login()
		if not LoginStatus:
			print '重新登录失败...重试...'
			time.sleep(1)
		else:
			print "登录成功！"
			return True
	return False

def Start():
	#------------------------------------------------------------------
	global LoginStatus
	global HEADERS
	global STUDENT_ID
	global PASSWORD
	#------------------------------------------------------------------
	#Welcome message
	#------------------------------------------------------------------
	#Get necessary information
	STUDENT_ID = raw_input("学号：")
	PASSWORD = raw_input("密码：")
	while not Login():
		print "Fail to login! Try again please."
		STUDENT_ID = raw_input("学号：")
		PASSWORD = raw_input("密码：")
	print "登录成功！"
	#------------------------------------------------------------------
	#Get course code
	course = []
	c_code = '#'
	try:
		c_code = raw_input("Enter course code(input # to terminate): ")
	except:
		pass
	while c_code != '' and c_code != '#':
		course.append(c_code)
		c_code = '#'
		try:
			c_code = raw_input("Enter course code(input # to terminate): ")
		except:
			pass
		if c_code == '#':
			break
	#------------------------------------------------------------------
	if not CheckSystemStatus(): # and False:
		print 'Waiting for 222.30.32.10...'
		wait_for_system()
		if not CheckSystemStatus():
			err_code = "Unexpected Error!"
			Stop()
	#------------------------------------------------------------------
	print "Using queue mode as default"
	#------------------------------------------------------------------
	print "Starting........"
	#------------------------------------------------------------------
	mode = 'queue'
	count = 0
	while True:
		count += 1
		post_course,course=select_course(course,mode)
		#print post_course
		#course=select_course(course,mode)[1]
		#print course
		fail_course=PostData(post_course,count)
		#print fail_course
		course=merge_course_list(course,fail_course,mode)
		#print course
		if len(course) > 0: # or 1:
			#course.append('0101')
			INIT()
			AutoLogin()
			pass
		else:
			print "刷完啦~\n"
			Stop()

def Stop():
	print ">>>>>>已停止<<<<<<"
	exit(0)
	return

def select_course(course_list, mode):
	selected_list = []
	if mode == 'queue':
		for i in range(min(4,len(course_list))):
			selected_list.append(course_list.pop(0))
		return (selected_list,course_list)
	else:
		for i in range(min(4,len(course_list))):
			selected_list.append(course_list.pop())
		return (selected_list,course_list)

def merge_course_list(course_list, selected_list, mode):
	if mode == 'queue':
		for i in range(len(selected_list)):
			course_list.append(selected_list.pop(0))
		return course_list
	else:
		for i in range(len(selected_list)):
			course_list.append(selected_list.pop())
		return course_list

def PostData(post_course_list, count):
	course=[]
	for i in range(4):
		course.append('')
	for i in range(len(post_course_list)):
		course[i]=post_course_list[i]
	info='第'+str(count)+'次抢课进行中……正在抢：\n'
	for i in range(len(post_course_list)):
		info += (course[i]+'\t'+GetName(course[i])+'\n')
	print info

	postdata="operation=xuanke&index="
	for i in range(4):
		if i<len(course):
			postdata += ("&xkxh"+str(i+1)+"="+course[i])
		else:
			postdata += ("&xkxh"+str(i+1)+"=")
	postdata += "&de=%25&courseindex="
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("POST","http://222.30.32.10/xsxk/swichAction.do",postdata,HEADERS)
		res=conn.getresponse()
	except:
		print "网络连接错误。请检查网络连接！"
		if not AutoLogin():
			return post_course_list
	#太久不管的话cookie会失效
	if res.status == 302:
		print "登录超时，重新登录中...\n"
		LoginStatus = False
		if not AutoLogin():
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
	else:
		Data = ''
	#---------------End---------------------
	#----------------------------------------
	fail_course=[]
	for course_code in post_course_list:
		if re.search(course_code,Data) != None:
			fail_course.append(course_code)
		else:
			print course_code+' '+GetName(course_code)
	#--------------------输出选课系统状态返回---------------------
	print Data
	if len(fail_course)==0:
		print '刷完啦~'
		return fail_course
	#-----------------------------------------------------------
	sleep_time = 5
	print '-----------------休眠'+str(sleep_time)+'秒--------------------'
	#-------------保持刷新防止假死------------
	for i in range(sleep_time):
		print sleep_time - i,
		time.sleep(0.25)
		for j in range(3):
			print '.',
			time.sleep(0.25)
		print ' ',
	print ''
	#---------------------------------------------
	return fail_course

def CheckSystemStatus():
	global HEADERS
	XuanKeButton = re.compile(u'''<input type="button" name="xuanke"''')
	XKButton = []
	list=''
	try:
		conn=httplib.HTTPConnection("222.30.32.10",timeout=10)
		conn.request("GET","http://222.30.32.10/xsxk/selectMianInitAction.do",list,HEADERS)
		XKButton = XuanKeButton.findall(conn.getresponse().read().decode("gbk").encode('utf-8'))
		if XKButton == [] :
			return False
		else:
			return True
	except:
		print "网络连接错误，无法连接到教务处系统。请检查网络连接！"
		return False
	return True

def wait_for_system():
	while not CheckSystemStatus():
		print "Waiting for 222.30.32.10... (3s)"
		for j in range (0,12):
			time.sleep(0.25)
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
	INIT()
	Start()
