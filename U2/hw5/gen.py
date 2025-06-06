import shutil
import random
from random import randint, uniform
import math
HW = 1
min_floor = 1
max_floor = 100
r=5
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
def generate(length, serial):
    ans = []
    time_ans = []
    if(HW == 1):
        unique_ids = set()
        while len(unique_ids) < length:
            unique_ids.add(gen_id())
        nique_ids = list(unique_ids)
        for i in range(length):
            """ b=gen_building() """
            """ from_building, to_building = b,b """
            elevator = gen_elevator()
            priority = gen_priority()
            [from_floor, to_floor] = gen_floor()
            while (from_floor == to_floor):
                from_floor, to_floor = gen_floor(), gen_floor()
            time_ans.append(float(format(uniform(1.0, 2.0), '.1f')))
            ans.append(f"-PRI-{priority}-FROM-{from_floor}-TO-{to_floor}-BY-{elevator}\n")
        time_ans.sort()
    else:
        for i in range(length):
            """ from_building, to_building = gen_building(),gen_building() """
            from_floor, to_floor = gen_floor(), gen_floor()
            while (from_floor == to_floor):
                """ from_building, to_building = gen_building(),gen_building() """
                from_floor, to_floor = gen_floor(), gen_floor()
            time_ans.append(float(format(uniform(1.0, 2.0), '.1f')))
            ans.append()
        time_ans.sort()
    f = open("stdin.txt", "w")
    for i in range(length):
        f.write('[' + str(time_ans[i]) + ']'+str(nique_ids[i]) + ans[i])
    f.close()
    """ shutil.copyfile("input.txt", "stdin_serial/stdin" + str(serial) + ".txt") """
#generate(100, 1)
