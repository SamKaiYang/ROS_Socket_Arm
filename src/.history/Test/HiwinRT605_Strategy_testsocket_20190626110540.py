#!/usr/bin/env python3
# license removed for brevity
#策略 機械手臂 四點來回跑
import rospy
import os
import numpy as np
from std_msgs.msg import String
from ROS_Socket.srv import *
from ROS_Socket.msg import *
import math
import enum
import Hiwin_RT605_Arm_Command as ArmTask
##----Arm state-----------
Arm_state_flag = 0
Strategy_flag = 0
Sent_data_flag = False
##----Arm status enum
class Arm_status(enum.IntEnum):
    Idle = 0
    Isbusy = 1
    Error = 2
    shutdown = 6
##-----------server feedback arm state----------
def Arm_state(req):
    global CurrentMissionType,Strategy_flag,Arm_state_flag
    Arm_state_flag = int('%s'%req.Arm_state)
    if Arm_state_flag  == Arm_status.Isbusy: #表示手臂忙碌
        Strategy_flag = False
        return(1)
    if Arm_state_flag  == Arm_status.Idle: #表示手臂準備
        Strategy_flag = True
        return(0)
    if Arm_state_flag  == Arm_status.shutdown: #表示程式中斷
        Strategy_flag = 6
        return(6)
##-----------server feedback Sent_flag----------
def Sent_flag(req):
    global Sent_data_flag
    Sent_data_flag = int('%s'%req.sent_flag)
    return(1)
def arm_state_server():
    #rospy.init_node(NAME)
    s = rospy.Service('arm_state',arm_state, Arm_state) ##server arm state
    a = rospy.Service('sent_flag',sent_flag,Sent_flag)
    #rospy.spin() ## spin one
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

##------------class-------
class point():
    def __init__(self,x,y,z,pitch,roll,yaw):
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw
pos = point(0,36.8,11.35,-90,0,0)


##-------------------------strategy---------------------
action = 0

def Mission_Trigger(ItemNo):
    global action,Arm_state_flag,Sent_data_flag
    if Arm_state_flag == Arm_status.Idle and Sent_data_flag == 1:
        for case in switch(ItemNo): #傳送指令給socket選擇手臂動作
            if case(0):
                pos.x = 10
                pos.y = 36.8
                pos.z = 11.35
                pos.pitch = -90
                pos.roll = 0
                pos.yaw = 0
                action = 1
                break
            if case(): # default, could also just omit condition or 'if True'
                ArmTask.rospy.on_shutdown(myhook)
            # No need to break here, it'll stop anyway
        print('x: ',pos.x,' y: ',pos.y,' z: ',pos.z,' pitch: ',pos.pitch,' roll: ',pos.roll,' yaw: ',pos.yaw)
        ArmTask.strategy_client_Arm_Mode(2,1,0,SpeedValue,2)#action,ra,grip,vel,both
        ArmTask.strategy_client_pos_move(pos.x,pos.y,pos.z,pos.pitch,pos.roll,pos.yaw)

    #action: ptp line
    #ra : abs rel
    #grip 夾爪
    #vel speed
    #both : Ctrl_Mode
##-------------strategy end ------------
def myhook():
    print ("shutdown time!")
if __name__ == '__main__':
    argv = rospy.myargv()
    rospy.init_node('strategy', anonymous=True)
    GetInfoFlag = True #Test no data
    arm_state_server()
    while 1:
        Mission_Trigger(action)
    ArmTask.rospy.spin()
    rospy.spin()
