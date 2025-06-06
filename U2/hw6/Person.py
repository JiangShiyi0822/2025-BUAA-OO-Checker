import re

class Person:
    index: int
    priority: int
    fromFloor: int
    toFloor: int
    targetElevator: int
    arriveTime: float
    currentFloor: int
    isInElevator: bool
    
    def __init__(self, index: int, priority: int, fromFloor: int, toFloor: int, targetElevator: int, arriveTime: float):
        self.index = index
        self.priority = priority
        self.fromFloor = fromFloor
        self.toFloor = toFloor
        self.targetElevator = targetElevator
        self.arriveTime = arriveTime
        self.reset()
    
    def reset(self):
        self.currentFloor = self.fromFloor
        self.isInElevator = False

    @staticmethod
    def parse(personInfo: str):
        personInfo = personInfo.replace(" ", "")
        personInfo = personInfo.replace("\n", "")
        float_pattern = "(\\d*\\.?\\d+)"
        int_pattern = "(\\d+)"
        floor_pattern = "(F\\d+|B\\d+)"
        pattern = "\\[" + float_pattern + "]" + int_pattern + "-PRI-" + int_pattern + "-FROM-" + floor_pattern + "-TO-" + floor_pattern
        def parseFloor(floorInfo: str):
            if (floorInfo[0] == 'B'):
                return -int(floorInfo[1:]) + 1
            else:
                return int(floorInfo[1:])
        pattern = re.compile(pattern)
        match = re.fullmatch(pattern, personInfo)
        if (not match):
            raise Exception(f"Invalid format of person info: {personInfo}")
        arriveTime = float(match.group(1))
        index = int(match.group(2))
        priority = int(match.group(3))
        fromFloor = parseFloor(match.group(4))
        toFloor = parseFloor(match.group(5))
        targetElevator = -1
        if (not (1 <= index and index <= 2147483647)):
            raise Exception(f"Invalid index of person info: {personInfo}")
        if (not (1 <= priority and priority <= 100)):
            raise Exception(f"Invalid index of priority info: {personInfo}")
        if (not (-3 <= fromFloor and fromFloor <= 7)):
            raise Exception(f"Invalid index of fromFloor info: {personInfo}")
        if (not (-3 <= toFloor and toFloor <= 7)):
            raise Exception(f"Invalid index of toFloor info: {personInfo}")
        return Person(index, priority, fromFloor, toFloor, targetElevator, arriveTime)

if __name__ == "__main__":
    person = Person.parse("[1.0]2147483647-PRI-19-FROM-F3-TO-F5-BY-1")
    print(person.arriveTime, person.priority, person.fromFloor, person.toFloor, person.targetElevator)
    person = Person.parse("[1.0]1030755460-PRI-46-FROM-F2-TO-B1-BY-2")
    print(person.arriveTime, person.priority, person.fromFloor, person.toFloor, person.targetElevator)