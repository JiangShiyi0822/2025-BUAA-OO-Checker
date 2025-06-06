import shutil
import random
from random import randint, uniform
import math
HW = 2
time_max = 30.0 # 最大时间
time_min = 1.0 # 最小时间
r=5
lastSche = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0} # 记录上次调度的时间
p_sche_not = 0.9 # 不生成调度指令的概率
try_num = 10 # 生成调度指令的最大尝试次数
arr = [0] * 7
def gen_floor():
    choices = [f'F{randint(1, 6)}', f'B{randint(1, 4)}']
    return random.sample(choices, 2)
""" def gen_building():
    return chr(randint(ord('A'), ord('E'))) """
def gen_elevator():
    return randint(1, 6)
def gen_id():
    return randint(1, 2147483647)
def gen_priority():
    return randint(1, 100)
def gen_speed():
    return random.choice([0.2, 0.3, 0.4, 0.5])
def gen_scheFloor():
    return random.choice(["B1", "B2", "F1", "F2", "F3", "F4", "F5"])
def gen_random_zeroAndOne():
    return 1 if random.random() < p_sche_not else 0
def gen_time():
    return float(format(uniform(time_min, time_max), '.1f'))
# [0.8]SCHE-6-0.2-F1
# [1.2]417-PRI-15-FROM-B2-TO-B4

def generate(length, serial):
    ans = []
    time_ans = []
    combined = []
    if(HW == 2):
        unique_ids = set()
        while len(unique_ids) < length:
            unique_ids.add(gen_id())
        nique_ids = list(unique_ids)
        for i in range(length):
            """ b=gen_building() """
            """ from_building, to_building = b,b """
            priority = gen_priority()
            [from_floor, to_floor] = gen_floor()
            while (from_floor == to_floor):
                from_floor, to_floor = gen_floor(), gen_floor()
            time = gen_time()
            time_ans.append(time)
            choice = gen_random_zeroAndOne()
            if (choice == 1):
                ans.append(f"{nique_ids[i]}-PRI-{priority}-FROM-{from_floor}-TO-{to_floor}\n")
            else:
                elevator = gen_elevator()
                speed = gen_speed()
                scheFloor = gen_scheFloor()
                reTry = 0
                while (lastSche[elevator] != 0.0 and ((time - lastSche[elevator]) <= 6.0) and reTry < try_num and arr[elevator] == 1):
                    elevator = gen_elevator()
                    reTry += 1
                if (reTry == try_num):    
                    ans.append(f"{nique_ids[i]}-PRI-{priority}-FROM-{from_floor}-TO-{to_floor}\n")
                else: 
                    ans.append(f"SCHE-{elevator}-{speed}-{scheFloor}\n")
                    lastSche[elevator] = time
                    arr[elevator] = 1
        combined = [f"[{time_ans[i]}]{ans[i]}" for i in range(length)]
        """ print(combined)
        print("\n") """
        combined.sort(key=lambda x: float(x.split(']')[0][1:]))        
    f = open("stdin.txt", "w")
    for i in range(length):
            f.write(combined[i])
    f.close()
    """ shutil.copyfile("input.txt", "stdin_serial/stdin" + str(serial) + ".txt") """
# generate(100, 1)
