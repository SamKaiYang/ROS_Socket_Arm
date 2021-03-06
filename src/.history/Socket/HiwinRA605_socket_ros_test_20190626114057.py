#!/usr/bin/env python3
# license removed for brevity

#接收策略端命令 用Socket傳輸至控制端電腦
import socket
##多執行序
import threading
import time
##
import sys
import os
import numpy as np
import rospy
import matplotlib as plot
from std_msgs.msg import String
from ROS_Socket.srv import *
from ROS_Socket.msg import *
import HiwinRA605_socket_TCPcmd as TCP
import HiwinRA605_socket_Taskcmd as Taskcmd
import enum
Socket = 0
data = '0' #設定傳輸資料初始值
Arm_feedback = 1 #假設手臂忙碌
state_feedback = 0
NAME = 'socket_server'
client_response = 0 #回傳次數初始值
point_data_flag = False
arm_mode_flag = False
speed_mode_flag = False
Socket_sent_flag = False
##------------class pos-------
class point():
    def __init__(self, x, y, z, pitch, roll, yaw):
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw
pos = point(0,36.8,11.35,-90,0,0)
##------------class socket_cmd---------
class socket_cmd():
    def __init__(self, grip, setvel, ra, delay, setboth, action,Speedmode):
        self.grip = grip
        self.setvel = setvel
        self.ra = ra
        self.delay = delay
        self.setboth = setboth
        self.action = action
        self.Speedmode = Speedmode
##-----------switch define------------##
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False
##-----------client feedback arm state----------
def socket_client_arm_state(Arm_state):
    global state_feedback

    rospy.wait_for_service('arm_state')
    try:
        Arm_state_client = rospy.ServiceProxy('arm_state', arm_state)
        state_feedback = Arm_state_client(Arm_state)
        #pos_feedback_times = pos_feedback.response
        return state_feedback
    except rospy.ServiceException as e:
        print ("Service call failed: %s"%e)
##----------socket sent data flag-------------
def socket_client_sent_flag(Sent_flag):
    global sent_feedback

    rospy.wait_for_service('sent_flag')
    try:
        Sent_flag_client = rospy.ServiceProxy('sent_flag', sent_flag)
        sent_feedback = Sent_flag_client(Sent_flag)
        #pos_feedback_times = pos_feedback.response
        return sent_feedback
    except rospy.ServiceException as e:
        print ("Service call failed: %s"%e)
##-----------client feedback arm state end----------
##------------server 端-------
def point_data(req): ##接收策略端傳送位姿資料
    global client_response,point_data_flag
    pos.x = '%s'%req.x
    pos.y = '%s'%req.y
    pos.z = '%s'%req.z
    pos.pitch = '%s'%req.pitch
    pos.roll = '%s'%req.roll
    pos.yaw = '%s'%req.yaw
    point_data_flag = True
    client_response = client_response + 1
    return(client_response)
##----------Arm Mode-------------###
def Arm_Mode(req): ##接收策略端傳送手臂模式資料
    global arm_mode_flag
    socket_cmd.action = int('%s'%req.action)
    socket_cmd.grip = int('%s'%req.grip)
    socket_cmd.ra = int('%s'%req.ra)
    socket_cmd.setvel = int('%s'%req.vel)
    socket_cmd.setboth = int('%s'%req.both)
    arm_mode_flag = True
    return(1)
##-------Arm Speed Mode------------###
def Speed_Mode(req): ##接收策略端傳送手臂模式資料
    global speed_mode_flag
    socket_cmd.Speedmode = int('%s'%req.Speedmode)
    speed_mode_flag = True
    return(1)
# def Grip_Mode(req): ##接收策略端傳送夾爪動作資料
#     socket_cmd.grip = int('%s'%req.grip)
#     return(1)
def socket_server(): ##創建Server node
    rospy.init_node(NAME)
    a = rospy.Service('arm_mode',arm_mode, Arm_Mode) ##server arm mode data
    s = rospy.Service('arm_pos',arm_data, point_data) ##server arm point data
    b = rospy.Service('speed_mode',speed_mode, Speed_Mode) ##server speed mode data
    #c = rospy.Service('grip_mode',grip_mode, Grip_Mode) ##server grip mode data
    print ("Ready to connect")
    rospy.spin() ## spin one
##------------server 端 end-------
##----------socket 封包傳輸--------------##
def Socket_command():
    for case in switch(socket_cmd.action):
        #-------PtP Mode--------
        if case(Taskcmd.Action_Type.PtoP):
            for case in switch(socket_cmd.setboth):
                if case(Taskcmd.Ctrl_Mode.CTRL_POS):
                    data = TCP.SetPtoP(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_POS,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel)
                    break
                if case(Taskcmd.Ctrl_Mode.CTRL_EULER):
                    data = TCP.SetPtoP(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_EULER,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel)
                    break
                if case(Taskcmd.Ctrl_Mode.CTRL_BOTH):
                    data = TCP.SetPtoP(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_BOTH,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel)
                    break
            break
        #-------Line Mode--------
        if case(Taskcmd.Action_Type.Line):
            for case in switch(socket_cmd.setboth):
                if case(Taskcmd.Ctrl_Mode.CTRL_POS):
                    data = TCP.SetLine(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_POS,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel)
                    break
                if case(Taskcmd.Ctrl_Mode.CTRL_EULER):
                    data = TCP.SetLine(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_EULER,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel )
                    break
                if case(Taskcmd.Ctrl_Mode.CTRL_BOTH):
                    data = TCP.SetLine(socket_cmd.grip,Taskcmd.RA.ABS,Taskcmd.Ctrl_Mode.CTRL_BOTH,pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw,socket_cmd.setvel )
                    break
            break
        #-------設定手臂速度--------
        if case(Taskcmd.Action_Type.SetVel):
            data = TCP.SetVel(socket_cmd.grip, socket_cmd.setvel)
            break
        #-------設定手臂Delay時間--------
        if case(Taskcmd.Action_Type.Delay):
            data = TCP.SetDelay(socket_cmd.grip,0)
            break
        #-------設定手臂急速&安全模式--------
        if case(Taskcmd.Action_Type.Mode):
            data = TCP.Set_SpeedMode(socket_cmd.grip,socket_cmd.Speedmode)
            break
    socket_cmd.action= 5 ##切換初始mode狀態
    Socket.send(data.encode('utf-8'))#socket傳送for python to translate str
##-----------socket client--------
def socket_client():
    global Socket,Arm_feedback,data,Socket_sent_flag,arm_mode_flag
    try:
        Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Socket.connect(('192.168.0.1', 8080))#iclab 5 ＆ iclab hiwin
        #s.connect(('192.168.1.102', 8080))#iclab computerx
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('Connection has been successful')
    print(Socket.recv(1024))
    #start_input=int(input('開始傳輸請按1,離開請按3 : ')) #輸入開始指令
    start_input = 1
    if start_input==1:
        while 1:
        ##---------------socket 傳輸手臂命令-----------------
            #if Arm_feedback == 0:
            if arm_mode_flag == True:
                arm_mode_flag = False
                
            feedback_str = Socket.recv(1024)
            #手臂端傳送手臂狀態
            if str(feedback_str[2]) == '70':# F 手臂為Ready狀態準備接收下一個運動指令
                Arm_feedback = 0
                socket_client_arm_state(Arm_feedback)
                #print("isbusy false")
            if str(feedback_str[2]) == '84':# T 手臂為忙碌狀態無法執行下一個運動指令
                Arm_feedback = 1
                socket_client_arm_state(Arm_feedback)
                #print("isbusy true")
            if str(feedback_str[2]) == '54':# 6 策略完成
                Arm_feedback = 6
                socket_client_arm_state(Arm_feedback)
                print("shutdown")
            #確認傳送旗標
            if str(feedback_str[4]) == '48':#回傳0 false
                Socket_sent_flag = False
                socket_client_sent_flag(Socket_sent_flag)
            if str(feedback_str[4]) == '49':#回傳1 true
                Socket_sent_flag = True
                socket_client_sent_flag(Socket_sent_flag)
        ##---------------socket 傳輸手臂命令 end-----------------
            if Arm_feedback == Taskcmd.Arm_feedback_Type.shutdown:
                rospy.on_shutdown(myhook)
                break
    if start_input == 3:
        pass
    Socket.close()
##-----------socket client end--------
##-------------socket 封包傳輸 end--------------##
## 多執行緒
def thread_test():
    socket_client()
## 多執行序 end
def myhook():
    print ("shutdown time!")
if __name__ == '__main__':
    socket_cmd.action = 5##切換初始mode狀態
    t = threading.Thread(target=thread_test)
    t.start() # 開啟多執行緒
    socket_server()
    t.join()

    # Ctrl+K Ctrl+C	添加行注释 Add line comment
    # Ctrl+K Ctrl+U	删除行注释 Remove line comment
    #Ctrl+] / [	缩进/缩进行 Indent/outdent line