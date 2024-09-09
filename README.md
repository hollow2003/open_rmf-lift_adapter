# lift_adapter手册
------
## 1.1 简介
* 该代码主要目的是将**RMF**系统与[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)中的云设备（电梯）进行连接，从而实现**RMF**系统控制及获取云设备（电梯）状态。
## 1.2 使用方法
### 1.2.1 部署RMF
根据gitlab中的[RMF服务器部署手册](https://git.lejurobot.com/rmf-leju/rmf-all)部署RMF。
### 1.2.2 配置文件修改
* 配置文件格式为.yaml，路径为**rmf-leju/lift-adapter/config.yaml**，包含以下格式的内容。
```
api:
  appId: "1607616596640403457" 
  appSecret: "8490A1713F369A0A"
  appCode: "00014V3"
  test_robotId: '000060615259' 
  projectId: '00006061'
```
* **api**中各项内容根据[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)所提供信息填写。
* **test_robotId**填写[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)所提供任意一个可用机器人**robotId**。
```
robotinfo: 
    - {robotId: '000060615259',requester_id: 'tinyRobot/tinyRobot1',token: '',floor: '0',intask: 0,through_floors: [],location: {},fleet_name: '',robot_name: '',task_id: ''}
    - {robotId: '000060618769',requester_id: 'tinyRobot/tinyRobot2',token: '',floor: '0',intask: 0,through_floors: [],location: {},fleet_name: '',robot_name: '',task_id: ''}
```
* **robotinfo**中**robotId**根据[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)所提供可用机器人Id信息填写，**requester_id**为RMF中该robotId对应所在机器人队列名与机器人名字按照示例组合。
* 其他值按照示例填写。
```
liftinfo: 
    - {lift_name: 'lift',now: '1',deviceUnique: '0000606110001',intask: 0,robotId: '',token: '',available_floors: ['1','2','3','4','5','6','7','9'],available modes: [],session_id: '',to: '1',from: '1',door_state: 0,currtent_mode: 2,motion_state: 0,step: '', keep_open: '0', cancel_flag: 0,cancel_excute: 0}
```
* **liftinfo**中**deviceUnique**根据[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)所提供可用电梯**deviceUnique**信息填写，**lift_name**为RMF中该**deviceUnique**对应电梯名字。
* 其他值按照示例填写。
### 1.2.3 启动lift_adapter
* 运行**rmf-leju/lift-adapter/start-command**中的**lift.sh**及**lift_recall.sh**脚本，**lift_adapter**会根据**config.yaml**配置文件启动。
## 1.3 接口说明
### 1.3.1 函数接口
* 以下为**LiftClientAPI.py**中的函数。
  class LiftClientAPI:
  &nbsp;
   ```
  def __init__(self,appCode,appId,appSecret,test_robotId,projectId):
  ```
  接口描述：初始化LiftClientAPI
  参数：
  **appCode**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供的**appCode**信息。
  **appId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供的**appId**信息。
  **appSecret**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供的**appSecret**信息。
  **test_robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **projectId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供的**projectId**信息。
  接口输出：
  连接正常无输出机器人；连接异常打印Unable to connect to lift client API。
  &nbsp;
  &nbsp;
  ```
  def check_connection(self,robotId):
  ```
  接口描述：根据输入的**robotId**获取**token**，以此检测与[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)的网络连接情况。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  接口输出：
  连接正常输出机器人对应**token**或''；连接异常打印Connection Error:原因并返回''。
  &nbsp;
  &nbsp;
  ```
  def get_DeviceInfo(self,robotId,token):
  ```
  接口描述：根据输入的**robotId**及**token**，查询该机器人拥有的项目下设备信息。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  接口输出：
  获取成功打印该机器人拥有的项目下设备信息，返回**True**；获取失败返回**False**；网络原因导致获取失败打印Connection Error:原因并返回**False**。
* 注：在此项目中任意机器人都拥有控制所有设备的权限，因此该接口在**lift_adapter.py**中并未使用。
  &nbsp;
  &nbsp;
  ```
  def call_lift(self,robotId,deviceUnique,token,fromFloor,toFloor):
  ```
  接口描述：根据输入的**robotId**、**deviceUnique**、**token**、**fromFloor**及**toFloor**，以该机器人的名义申请**deviceUnique**对应电梯任务，该任务内容为到**fromFloor**接到机器人后送至**toFloor**。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **deviceUnique**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用电梯**deviceUnique**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  **fromFloor**：机器人当前楼层（字符串类型）。
  **toFloor**：机器人当前楼层（字符串类型）。
  接口输出：
  预约成功打印返回消息，返回**True**；预约失败打印返回消息，打印"Can't call the lift now"并返回**False**；网络原因导致预约失败打印Connection Error:原因并返回**False**。
  &nbsp;
  &nbsp;
  ```
  def callNoninductive_lift(self,robotId,deviceUnique,token,fromFloor,toFloor):
  ```
  接口描述：根据输入的**robotId**、**deviceUnique**、**token**、**fromFloor**及**toFloor**，以该机器人的名义申请**deviceUnique**对应无感电梯任务，该任务内容为到**fromFloor**接到机器人后送至**toFloor**。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **deviceUnique**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用电梯**deviceUnique**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  **fromFloor**：机器人当前楼层（字符串类型）。
  **toFloor**：机器人当前楼层（字符串类型）。
  接口输出：
  预约成功打印返回消息，返回**True**；预约失败打印返回消息，打印"Can't call the lift now"并返回**False**；网络原因导致预约失败打印Connection Error:原因并返回**False**。
* 注：该接口与**call_lift**接口区别只在于预约的电梯是否为无感电梯。该接口在**lift_adapter.py**中并未使用。
  &nbsp;
  &nbsp;
  ```
  def extend_opentime(self,robotId,deviceUnique,token,position):
  ```
  接口描述：发送开门指令，在电梯门状态为开门到位时，如果发现开门时长不够，调用此接口维持开门状态。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **deviceUnique**：该机器人当前任务执行电梯的**deviceUnique**。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  **position**：发送该指令时机器人位置（字符串）。**in**代表机器人未完全进入电梯，**out**为机器人未完全出电梯。
  接口输出：
  延长成功返回**True**；延长失败返回**False**；网络原因导致延长失败打印Connection Error:原因并返回**False**。
  &nbsp;
  &nbsp;
  ```
  def close(self,robotId,deviceUnique,token,position):
  ```
  接口描述：发送关门指令。在电梯门状态为开门到位时，如果机器人完全进入电梯或出电梯，调用此接口关门进入下个任务阶段或结束任务。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **deviceUnique**：该机器人当前任务执行电梯的**deviceUnique**。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  **position**：发送该指令时机器人位置（字符串）。**in**代表机器完全进入电梯，**out**为机器人完全出电梯。
  接口输出：
  关门成功返回**True**；关门失败返回**False**；网络原因导致关门失败打印Connection Error:原因并返回**False**。
  &nbsp;
  &nbsp;
  ```
  def get_Taskinfo(self,robotId,token):
  ```
  接口描述：查询对应机器人所在任务状态。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  接口输出：
  获取成功返回返回消息**data**部分；获取失败返回**4**；网络原因导致获取失败打印Connection Error:原因并返回**4**。
  &nbsp;
  &nbsp;
  ```
  def cancel_Task(self,robotId,token):
  ```
  接口描述：取消对应机器人所在任务状态。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  接口输出：
  取消成功返回**True**；网络原因导致获取失败打印Connection Error:原因并返回**False**。
  &nbsp;
  &nbsp;
  ```
  def get_Devicestate(self,robotId,token,deviceUnique):
  ```
  接口描述：	查询电梯的状态信息。
  参数：
  **robotId**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供可用机器人**robotId**信息。
  **token**：对应机器人通过**check_connection**接口从[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)获得的**token**值。
  **deviceUnique**：该机器人当前任务执行电梯的**deviceUnique**。
  接口输出：
  获取成功打印返回信息，返回电梯当前所在楼层；获取失败返回**4**；网络原因导致获取失败打印Connection Error:原因并返回**4**。
* 注：只能查询当前正在移动且有任务的电梯，并且只能由以预约该任务的机器人的名义查询，否则会失败。
  &nbsp;
  &nbsp;
  ```
  def getUUID(self):
  ```
  接口描述：生成UUID。
  参数：
  无
  接口输出：
  返回生成的UUID。
  &nbsp;
  &nbsp;
  class Aes_ECB(object):
  &nbsp;
  ```
  def __init__(self,key):
  ```
  接口描述：初始化Aes_ECB。
  参数：
  **key**：[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)提供的**appSecret**信息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def add_to_16(value):
  ```
  接口描述：将加密后的信息补零至长度16的倍数。
  参数：
  **value**：AES加密后信息。
  接口输出：
  返回补完的AES加密信息。
  &nbsp;
  &nbsp;
  ```
  def AES_encrypt(self, text):
  ```
  接口描述：AES加密。
  参数：
  **text**：要AES加密的信息。
  接口输出：
  返回AES加密后的信息。
  &nbsp;
  &nbsp;
  ```
  def AES_decrypt(self, text):
  ```
  接口描述：AES解密。
  参数：
  **text**：要AES解密的信息。
  接口输出：
  返回AES解密后的信息。
  &nbsp;
* 不属于这两个类的函数：
  ```
  def md5value(s):
  ```
  接口描述：计算字符串MD5值。
  参数：
  **s**：要进行MD5计算的信息。（用于生成sign）
  接口输出：
  返回字符串对应MD5值。
  &nbsp;
  &nbsp;
* 以下为**lift_adapter.py**中的函数。
  class LiftAdapter(Node):
  &nbsp;
  ```
  def __init__(self,config_yaml):
  ```
  接口描述：初始化lift_adapter。
  参数：
  **config_yaml**：lift_adapter配置文件。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def find_index(self,arr, key, target):
  ```
  接口描述：在指定数组中根据要求匹配的键值查找对应元素。
  参数：
  **arr**：要查找的数组。
  **key**：要匹配的键值所对应键。
  **target**：要匹配的键值。
  接口输出：
  查找成功返回对应位置；未查找到返回-1.
  &nbsp;
  &nbsp;
  ```
  def robot_floor_through_cb(self,msg:RobotFloorThrough):
  ```
  接口描述：**robot_floor_through**话题响应函数，获取机器人任务所需经过的楼层。（不包括在电梯内经过楼层）
  参数：
  **msg:RobotFloorThrough**：**robot_floor_through**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def lift_signal_cb(self,msg:LiftSignal):
  ```
  接口描述：**lift_signal**话题响应函数，获取需要取消任务的电梯。
  参数：
  **msg:LiftSignal**：**lift_signal**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def blocked_info_cb(self,msg:BlockedInfo):
  ```
  接口描述：**blocked_info**话题响应函数，获取机器人受阻碍信息。
  参数：
  **msg:BlockedInfo**：**blocked_info**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def fleet_cb(self,msg: FleetState):
  ```
  接口描述：**fleet_states**话题响应函数，获取机器人包括当前楼层等状态信息。
  参数：
  **FleetState**：**fleet_states**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def fleet_cb(self,msg: FleetState):
  ```
  接口描述：**fleet_states**话题响应函数，获取机器人包括当前楼层、当前任务id等状态信息。
  参数：
  **FleetState**：**fleet_states**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def init_lift(self,l:int):
  ```
  接口描述：初始化某个电梯。
  参数：
  **l**：要初始化的电梯位于**liftinfo**中的位置。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def lift_request_cb(self,msg: LiftRequest):
  ```
  接口描述：**lift_requests**话题响应函数，根据话题消息存储电梯应执行操作或初始化等。
  参数：
  **msg: LiftRequest**：**lift_requests**话题消息。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def get_door_state(self,l,n)->DoorState:
  ```
  接口描述：构建**door_states**话题消息类型电梯外门默认状态消息。
  参数：
  **l**：要构建的电梯位于**liftinfo**中的位置。
  接口输出：
  构建的**door_states**话题消息。
  &nbsp;
  &nbsp;
  ```
  def get_inner_door_state(self,l)->DoorState:
  ```
  接口描述：构建**door_states**话题消息类型电梯内门默认状态消息。
  参数：
  **l**：要构建的电梯位于**liftinfo**中的位置。
  接口输出：
  构建的**door_states**话题消息。
  &nbsp;
  &nbsp;
  ```
  def get_lift_state(self,l)->LiftState:
  ```
  接口描述：构建**lift_states**话题消息类型电梯默认状态消息。
  参数：
  **l**：要构建的电梯位于**liftinfo**中的位置。
  接口输出：
  构建的**lift_states**话题消息。
  &nbsp;
  &nbsp;
  ```
  def time_cb(self):
  ```
  接口描述：计时器触发响应，维护电梯状态、机器人状态、任务状态，并根据存储的需执行的操作进行处理。
  参数：
  无。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def count(self):
  ```
  接口描述：计时器，更新距离下次更新token时间。
  参数：
  无。
  接口输出：
  无。
  &nbsp;
  &nbsp;
  ```
  def tokenupdate(self):
  ```
  接口描述：更新所有机器人token。
  参数：
  无。
  接口输出：
  无。
