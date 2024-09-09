import sys
import yaml
import argparse
import json

import time
import threading
import rclpy

from LiftClientAPI import LiftClientAPI
## Using from lift_adapter.LiftClientAPI import LiftClientAPI while build
from rclpy.node import Node
from rclpy.time import Time
from rmf_door_msgs.msg import DoorRequest, DoorState, DoorMode
from rmf_lift_msgs.msg import LiftRequest, LiftState, RobotFloorThrough
from rmf_fleet_msgs.msg import FleetState
## Before using this door_adapter, you need to modify door.common.cpp and lift.common.cpp to avoid door node pub its' state firstly
## Remenber to colcon after that
## Then modify your common.launch.xml to ban door_supervisor and lift_supervisor and set to launch door_adapter and lift_adapter
## The code is listed following:
## <!-- Door Adapter -->

## <node pkg="door_adapter" exec="door_adapter" args="--config_file '/opt/ros/galactic/share/rmf_door_adapter/config.yaml'" output="both">
##   <param name="use_sim_time" value="$(var use_sim_time)"/>
## </node>
##<!-- Lift Adapter -->

## <node pkg="lift_adapter" exec="lift_adapter" args="--config_file '/opt/ros/galactic/share/rmf_lift_adapter/config.yaml'" output="both">
##   <param name="use_sim_time" value="$(var use_sim_time)"/>
## </node>
## Do not forget to change the config.yaml adress

###############################################################################

class LiftAdapter(Node):
    def __init__(self,config_yaml):
        super().__init__('lift_adapter')
        self.get_logger().info('Starting lift adapter...')
        self.door_state_publish_period = config_yaml['door_publisher']['door_state_publish_period']
        door_pub = config_yaml['door_publisher']
        lift_pub = config_yaml['lift_publisher']
        door_requests_pub = config_yaml['door_requests_publisher']
        lift_requests_pub = config_yaml['lift_requests_publisher']
        lift_sub = config_yaml['lift_subscriber']
        fleet_sub = config_yaml['fleet_subscriber']
        robot_floor_through_sub = config_yaml['robot_floor_through_subscriber']
        ## Init publishers and subscribers details
        ## Init the pub frequency
        self.robotinfo = config_yaml['robotinfo']
        self.liftinfo = config_yaml['liftinfo']
        ## Init a list to store all lifts' and robots' info,detail is in config
        self.api = LiftClientAPI()
        ## Init DoorClientAPI
        self.door_states_pub = self.create_publisher(
            DoorState, door_pub['topic_name'], 10)

        self.lift_states_pub = self.create_publisher(
            LiftState, lift_pub['topic_name'], 10)

        self.robot_floor_through_sub = self.create_subscription(
            RobotFloorThrough,robot_floor_through_sub['topic_name'],self.robot_floor_through_cb(), 10)  
        #in test using "/robot_floor_through" and lambda msg: self.robot_floor_through_cb(msg)
        self.lift_request_sub = self.create_subscription(
            LiftRequest, lift_sub['topic_name'], self.lift_request_cb, 10)   

        self.fleet_sub = self.create_subscription(
            FleetState, fleet_sub['topic_name'], self.fleet_cb, 10) 

        self.periodic_timer = self.create_timer(
            self.door_state_publish_period, self.time_cb)
        
        self.door_requests_pub = self.create_publisher(
           DoorRequest, door_requests_pub['topic_name'], 10)
        
        self.lift_requests_pub = self.create_publisher(
            LiftRequest, lift_requests_pub['topic_name'], 10)

        ## Init publishers and a subscriber
        self.tokenupdate()
        ## Get and store robot token information
        self.tokencount = 259200
	## Change token count to modify the cycle to update token

    def robot_floor_through_cb(self,msg:RobotFloorThrough):
        ## Get and store through floors of every robot in moving plan
        i = len(self.robotinfo)-1
        while i>= 0:
            if self.robotinfo[i]["requester_id"].endswith(msg.robot_name) :
                self.robotinfo[i]["through_floors"] = msg.through_floors
            i-=1

    def fleet_cb(self,msg: FleetState):
        ## Get and store the floor on where the robot is currently 
        i = len(msg.robots)-1
        while i >= 0:
            k = len(self.robotinfo)-1
            while k >= 0:
                if self.robotinfo[k]["requester_id"].endswith(msg.robots[i].name):
                    self.robotinfo[k]["floor"] = msg.robots[i].location.level_name[1]
                k-=1
            i-=1
            

    def lift_request_cb(self,msg: LiftRequest):
        ## Handle adapter_lift_requests
        i = len(self.liftinfo)-1
        while i >= 0:
            if self.liftinfo[i]["lift_name"] == msg.lift_name:
                break
            i -= 1
        ## Find the lift
        k = len(self.liftinfo[i]["available_floors"])-1
        while k >= 0:
            if msg.destination_floor[1] == self.liftinfo[i]["available_floors"][k]:
                break
            k -= 1
        if k < 0:
            print("this lift can not support this task")
        ## Check wether the lift can support this task
        else:
            j = len(self.robotinfo)-1
            while j >= 0:
                if msg.session_id == self.robotinfo[j]["requester_id"]:
                    break
                j -= 1
            if j < 0 :
                print ("Can't find correct robot")
            ## Find the robot which pub requests
            else :
                self.liftinfo[i]["session_id"] = msg.session_id
                self.liftinfo[i]["token"] = self.robotinfo[j]["token"]
                self.liftinfo[i]["robotId"] = self.robotinfo[j]["robotId"]
                ## Get info from msg and robotinfo to lift info to support time_cb
                if msg.request_type == 0 and self.liftinfo[i]["step"] == '4':
                    ## Which means that the task should be end
                    self.liftinfo[i]["keep_open"] = '0'
                    if self.api.close(self.robotinfo[j]["robotId"],self.liftinfo[i]["deviceUnique"],self.liftinfo[i]["token"],'out'):
                        ## Close door out of lift successfully
                        self.liftinfo[i]["from"] = '1'
                        self.liftinfo[i]["to"] = '1'
                        self.liftinfo[i]["session_id"] = ''
                        self.liftinfo[i]["intask"] = 0
                        self.liftinfo[i]["step"] = ''
                        self.liftinfo[i]["token"] = ''
                        self.liftinfo[i]["motion_state"] = 0
                        self.liftinfo[i]["door_state"] = 0
                        self.liftinfo[i]["robotId"] = ''
                        print("end lift task success")
                        ## Set relevant info to default
                    else:
                        print("end lift task error,retry")
                else:
                    print("please wait until step 4")
                if msg.request_type == 1:
                    ## Which means that the task is on or just begins
                    ## In test using the following code
                    ##if self.robotinfo[j]['floor'] == self.robotinfo[j]['through_floors'][0][1]:
                        ## Task starts from the first of through_floors
                        ##self.liftinfo[i]["to"] = self.robotinfo[j]['through_floors'][1][1]
                    ##elif self.robotinfo[j]['floor'] != self.robotinfo[j]['through_floors'][0][1]:
                        ## Task starts from robot's current floor to the first of through_floors
                        ##self.liftinfo[i]["to"] = self.robotinfo[j]['through_floors'][0][1]
                        ## Judgement can be modify after confirm whether the through_floors include current floor
                    if self.liftinfo[i]["intask"] == 0:
                        ## Task hasn't been on
                        self.liftinfo[i]["from"] = self.robotinfo[j]['floor']
                        self.liftinfo[i]["to"] = self.robotinfo[j]['through_floors'][1][1]
                        if self.api.call_lift(self.robotinfo[j]["robotId"],self.liftinfo[i]["deviceUnique"],self.liftinfo[i]["token"],self.liftinfo[i]["from"],self.liftinfo[i]["to"]):
                            ## Set flag and default step value after call lift successfully 
                            self.liftinfo[i]["intask"] = 1
                            self.liftinfo[i]["step"] = '1'
                            print("call lift success")
                        else:
                            print("call lift error,retry")
                    elif self.liftinfo[i]["intask"] == 1:
                        ## Task has been on
                        if msg.destination_floor[1] == self.liftinfo[i]["from"] and self.liftinfo[i]["step"] == '2' :
                            ## Which means that robot is still out of lift on the start floor and lift is ready
                            self.liftinfo[i]["keep_open"] = '2'
                            if self.api.extend_opentime(self.robotinfo[j]["robotId"],self.liftinfo[i]["deviceUnique"],self.liftinfo[i]["token"],'out'):
                                print ("extend opentime success")
                            else:
                                print("extend opentime error,maybe need to wait")
                        elif msg.destination_floor[1] == self.liftinfo[i]["to"] and self.robotinfo[j]["floor"] == self.liftinfo[i]["from"] and self.liftinfo[i]["step"] == '2':
                            ## Which means that robot is inside of lift on the start floor and lift is ready
                            self.liftinfo[i]["keep_open"] = '0'
                            if self.api.close(self.robotinfo[j]["robotId"],self.liftinfo[i]["deviceUnique"],self.liftinfo[i]["token"],'in'):
                                print ("close success")
                            else:
                                print("close error,maybe need to wait")
                        elif msg.destination_floor[1] == self.liftinfo[i]["to"] and self.robotinfo[j]["floor"] == self.liftinfo[i]["to"] and self.liftinfo[i]["step"] == '4':
                            ## Which means that robot is inside of lift on the destination floor and lift is ready
                            self.liftinfo[i]["keep_open"] = '4'
                            if self.api.extend_opentime(self.robotinfo[j]["robotId"],self.liftinfo[i]["deviceUnique"],self.liftinfo[i]["token"],'in'):
                                print ("extend opentime success")
                            else:
                                print("extend opentime error,maybe need to wait")

    def time_cb(self):
        ## Get lift states from web and pub them and door_states
        l = len(self.liftinfo) -1 
        ## Go over all lifts in liftinfo
        while l >= 0:
            if self.liftinfo[l]["intask"] == 0:
                ## Lift isn't in task
                lift_state_msg= LiftState()
                lift_state_msg.lift_time = self.get_clock().now().to_msg()
                lift_state_msg.lift_name = self.liftinfo[l].get("lift_name")
                lift_state_msg.available_floors = []
                h = len(self.liftinfo[l]["available_floors"])-1
                while h >= 0:
                    lift_state_msg.available_floors.append('L'+self.liftinfo[l].get("available_floors")[h])
                    h-=1
                lift_state_msg.current_floor = 'L'+str(self.liftinfo[l].get("now"))
                lift_state_msg.destination_floor = 'L'+str(self.liftinfo[l].get("now"))
                lift_state_msg.door_state = 0
                lift_state_msg.motion_state = 0
                if self.liftinfo[l].get("available modes") != []:
                    lift_state_msg.available_modes = self.liftinfo[l].get("available modes")
                lift_state_msg.current_mode = 2
                lift_state_msg.session_id = ''
                self.lift_states_pub.publish(lift_state_msg)
                ## Pub default lift_states
                door_state_msg = DoorState()
                door_state_msg.door_time = self.get_clock().now().to_msg()
                door_state_msg.door_name = "CabinDoor_"+self.liftinfo[l].get("lift_name")+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                door_state_msg.current_mode = DoorMode()
                door_state_msg.current_mode.value = 0
                self.door_states_pub.publish(door_state_msg)
                n = len(self.liftinfo[l]["available_floors"])-1
                while n >= 0:
                    door_state_msg = DoorState()
                    door_state_msg.door_time = self.get_clock().now().to_msg()
                    door_state_msg.door_name = "ShaftDoor_"+self.liftinfo[l].get("lift_name")+"_L"+str(self.liftinfo[l]["available_floors"][n])+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                    door_state_msg.current_mode.value = 0
                    self.door_states_pub.publish(door_state_msg)
                    n-=1
                ## Pub default door_states
            elif self.liftinfo[l]["intask"] == 1:
                ## Lift is in task,need to update lift's state
                if self.liftinfo[l]["step"] == '2' or self.liftinfo[l]["step"] == '4':
                    if self.liftinfo[l]["keep_open"] == '2':
                        if self.api.extend_opentime(self.liftinfo[l]["robotId"],self.liftinfo[l]["deviceUnique"],self.liftinfo[l]["token"],'out'):
                            print("keep open successfully in the start floor")
                    if self.liftinfo[l]["keep_open"] == '4':
                        if self.api.extend_opentime(self.liftinfo[l]["robotId"],self.liftinfo[l]["deviceUnique"],self.liftinfo[l]["token"],'in'):
                            print("keep open successfully in the start floor")
                result = self.api.get_Taskinfo(self.liftinfo[l]["robotId"],self.liftinfo[l]["token"])
                if result == 4:
                    print("can't get task info")
                    k = len(self.robotinfo) - 1
                    while k >= 0:
                        if self.robotinfo[k]["robotId"] == self.liftinfo[l]["robotId"]:
                            break
                        k -= 1
                    if k >= 0:
                        if self.api.cancel_Task(self.liftinfo[l]["robotId"],self.liftinfo[l]["token"]):
                            self.liftinfo[l]["from"] = '1'
                            self.liftinfo[l]["to"] = '1'
                            self.liftinfo[l]["session_id"] = ''
                            self.liftinfo[l]["keep_open"] = '0'
                            self.liftinfo[l]["intask"] = 0
                            self.liftinfo[l]["step"] = ''
                            self.liftinfo[l]["token"] = ''
                            self.liftinfo[l]["motion_state"] = 0
                            self.liftinfo[l]["door_state"] = 0
                            self.liftinfo[l]["robotId"] = ''
                            print("Cancel Task Success")
                    ## Code used to handle cancel task situation hasn't been test!
                else:                   
                    self.liftinfo[l]["step"] = result["step"]
                    self.liftinfo[l]["now"] = result["floor"]
                    ## Set lift's current floor and task step
                    if self.liftinfo[l]["step"] == '2' or self.liftinfo[l]["step"] == '1' :
                        if self.robotinfo[k]["through_floors"][1][1] != self.liftinfo[l]["to"]:
                            k = len(self.robotinfo) - 1
                            while k >= 0:
                                if self.robotinfo[k]["robotId"] == self.liftinfo[l]["robotId"]:
                                    break
                                k -= 1
                            if k >= 0:
                                if self.api.cancel_Task(self.liftinfo[l]["robotId"],self.liftinfo[l]["token"]):
                                    self.liftinfo[l]["from"] = '1'
                                    self.liftinfo[l]["to"] = '1'
                                    self.liftinfo[l]["session_id"] = ''
                                    self.liftinfo[l]["keep_open"] = '0'
                                    self.liftinfo[l]["intask"] = 0
                                    self.liftinfo[l]["step"] = ''
                                    self.liftinfo[l]["token"] = ''
                                    self.liftinfo[l]["motion_state"] = 0
                                    self.liftinfo[l]["door_state"] = 0
                                    self.liftinfo[l]["robotId"] = ''
                                    print("Cancel Task Success")
                ## Code used to handle cancel task situation hasn't been test!
                    if result["step"] == '2' or result["step"] == '4':
                        ## Which means lift has stopped and open it's door
                        self.liftinfo[l]["motion_state"] = 0
                        self.liftinfo[l]["door_state"] = 2
                        self.liftinfo[l]["keep_open"] = result["step"]
                    elif result["step"] == '1':
                        ## Which means lift is moving
                        if int(result["floor"]) >= int(self.liftinfo[l]["from"]):
                            ## Check lift is moving up or down
                            self.liftinfo[l]["motion_state"] = 2
                        else:
                            self.liftinfo[l]["motion_state"] = 1
                        if int(result["floor"]) == int(self.liftinfo[l]["from"]):
                            ## Check whether door is moving
                            self.liftinfo[l]["door_state"] = 1
                        else:
                            self.liftinfo[l]["door_state"] = 0
                    elif result["step"] == '3':
                        ## Which means lift is moving
                        if int(result["floor"]) >= int(self.liftinfo[l]["to"]):
                            ## Check lift is moving up or down
                            self.liftinfo[l]["motion_state"] = 2
                        else:
                            self.liftinfo[l]["motion_state"] = 1
                        if int(result["floor"]) == int(self.liftinfo[l]["to"]):
                            ## Check whether door is moving
                            self.liftinfo[l]["door_state"] = 1
                        else:
                            self.liftinfo[l]["door_state"] = 0
                lift_state_msg= LiftState()
                lift_state_msg.lift_time = self.get_clock().now().to_msg()
                lift_state_msg.lift_name = self.liftinfo[l].get("lift_name")
                lift_state_msg.available_floors = []
                h = len(self.liftinfo[l]["available_floors"])-1
                while h >= 0:
                    lift_state_msg.available_floors.append('L'+self.liftinfo[l].get("available_floors")[h])
                    h-=1
                lift_state_msg.current_floor = 'L'+str(self.liftinfo[l].get("now"))
                if self.liftinfo[l]["step"] == '3' or self.liftinfo[l]["step"] == '4':
                    lift_state_msg.destination_floor = 'L'+str(self.liftinfo[l].get("to"))
                elif self.liftinfo[l]["step"] == '1' or self.liftinfo[l]["step"] == '2':
                    lift_state_msg.destination_floor = 'L'+str(self.liftinfo[l].get("from"))
                lift_state_msg.door_state = self.liftinfo[l].get("door_state")
                lift_state_msg.motion_state = self.liftinfo[l].get("motion_state")
                if self.liftinfo[l].get("available modes") != []:
                    lift_state_msg.available_modes = self.liftinfo[l].get("available modes")
                lift_state_msg.current_mode = 2
                lift_state_msg.session_id = self.liftinfo[l].get("session_id")
                self.lift_states_pub.publish(lift_state_msg)
                ## Pub lift_state
                door_state_msg = DoorState()
                door_state_msg.door_time = self.get_clock().now().to_msg()
                door_state_msg.door_name = "CabinDoor_"+self.liftinfo[l].get("lift_name")+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                door_state_msg.current_mode = DoorMode()
                if self.liftinfo[l]["step"] == '2' or self.liftinfo[l]["step"] == '4':
                    door_state_msg.current_mode.value = 2
                elif self.liftinfo[l]["step"] == '1' or self.liftinfo[l]["step"] == '3':
                    if self.liftinfo[l]["now"] == self.liftinfo[l]["from"] or self.liftinfo[l]["now"] == self.liftinfo[l]["to"]:
                        door_state_msg.current_mode.value = 1
                    else:
                        door_state_msg.current_mode.value = 0
                self.door_states_pub.publish(door_state_msg)
                n = len(self.liftinfo[l]["available_floors"])-1
                if self.liftinfo[l]["step"] == '1' or self.liftinfo[l]["step"] == '3':
                    while n>=0:
                        door_state_msg = DoorState()
                        door_state_msg.door_time = self.get_clock().now().to_msg()
                        door_state_msg.door_name = "ShaftDoor_"+self.liftinfo[l].get("lift_name")+"_L"+str(self.liftinfo[l]["available_floors"][n])+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                        door_state_msg.current_mode.value = 0
                        self.door_states_pub.publish(door_state_msg)
                        n-=1
                    door_state_msg = DoorState()
                    door_state_msg.door_time = self.get_clock().now().to_msg()
                    door_state_msg.door_name = "CabinDoor_"+self.liftinfo[l].get("lift_name")+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                    door_state_msg.current_mode = DoorMode()
                    door_state_msg.current_mode.value = 0
                    self.door_states_pub.publish(door_state_msg)
                elif self.liftinfo[l]["step"] == '2' or self.liftinfo[l]["step"] == '4':
                    while n>=0:
                        if self.liftinfo[l]["available_floors"][n] != self.liftinfo[l]["now"]:
                            door_state_msg = DoorState()
                            door_state_msg.door_time = self.get_clock().now().to_msg()
                            door_state_msg.door_name = "ShaftDoor_"+self.liftinfo[l].get("lift_name")+"_L"+str(self.liftinfo[l]["available_floors"][n])+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                            door_state_msg.current_mode.value = 0
                            self.door_states_pub.publish(door_state_msg)
                        elif self.liftinfo[l]["available_floors"][n] == self.liftinfo[l]["now"]:
                            door_state_msg = DoorState()
                            door_state_msg.door_time = self.get_clock().now().to_msg()
                            door_state_msg.door_name = "ShaftDoor_"+self.liftinfo[l].get("lift_name")+"_L"+str(self.liftinfo[l]["available_floors"][n])+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                            door_state_msg.current_mode.value = 2
                            self.door_states_pub.publish(door_state_msg)
                        n-=1
                    door_state_msg = DoorState()
                    door_state_msg.door_time = self.get_clock().now().to_msg()
                    door_state_msg.door_name = "CabinDoor_"+self.liftinfo[l].get("lift_name")+"_"+self.liftinfo[l].get("lift_name").lower()+"_door"
                    door_state_msg.current_mode = DoorMode()
                    door_state_msg.current_mode.value = 2
                    self.door_states_pub.publish(door_state_msg)
                ## Pub door_states
            l=l-1

    
    def count(self):
        self.tokencount-=1
        if self.tokencount <= 0:
        ## Update token and reset timer
            self.tokenupdate()
            self.tokencount = 259200
    

    def tokenupdate(self):
        k = len(self.robotinfo)-1
        while k >= 0:
            self.robotinfo[k]['token'] = self.api.check_connection(self.robotinfo[k].get('robotId'))
            k-=1

###############################################################################

def main(argv=sys.argv):
    rclpy.init(args=argv)
    args_without_ros = rclpy.utilities.remove_ros_args(argv)
    parser = argparse.ArgumentParser(
        prog="lift_adapter",
        description="Configure and spin up lift adapter for lift ")
    parser.add_argument("-c", "--config_file", type=str, required=True,
                        help="Path to the config.yaml file for this lift adapter")
    args = parser.parse_args(args_without_ros[1:])
    config_path = args.config_file

    # Load config and nav graph yamls
    with open(config_path, "r") as f:
        config_yaml = yaml.safe_load(f)

    lift_adapter = LiftAdapter(config_yaml)
    rclpy.spin(lift_adapter)

    lift_adapter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
