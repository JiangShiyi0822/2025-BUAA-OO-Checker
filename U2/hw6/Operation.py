from enum import Enum
import re

class OperationType(Enum):
    ARRIVE = 0
    OPEN = 1
    CLOSE = 2
    IN = 3
    OUT = 4
    RECEIVE = 5
    SCHE = 6

class Operation:
    opType: OperationType
    elevatorIndex: int
    floor: int
    personIndex: int
    timestamp: float

    # outType 0: F, 1: S
    # scheType 0: BEGIN, 1: END, -1: ACCEPT
    def __init__(self, opType: OperationType, elevatorIndex: int, outType: int, floor: int, personIndex: int, scheType: int, speed: float, timestamp: float):
        self.opType = opType
        self.elevatorIndex = elevatorIndex
        self.outType = outType
        self.floor = floor
        self.personIndex = personIndex
        self.scheType = scheType
        self.speed = speed
        self.timestamp = timestamp
    
    # [时间戳]ARRIVE-所在层-电梯ID
    # [时间戳]OPEN-所在层-电梯ID
    # [时间戳]CLOSE-所在层-电梯ID
    # [时间戳]IN-乘客ID-所在层-电梯ID
    # [时间戳]OUT-S/F-乘客ID-所在层-电梯ID
    # [时间戳]RECEIVE-乘客ID-电梯ID
    # [时间戳]SCHE-BEGIN-电梯ID
    # [时间戳]SCHE-END-电梯ID
    # [时间戳]SCHE-ACCEPT-电梯ID-临时运行速度-目标楼层

    @staticmethod
    def parse(operationInfo: str):
        operationInfo = operationInfo.replace(" ", "")
        operationInfo = operationInfo.replace("\n", "")
        float_pattern = "(\\d*\\.?\\d+)"
        int_pattern = "(\\d+)"
        floor_pattern = "(F\\d+|B\\d+)"
        out_pattern = "(S|F)"
        sche_pattern = "(BEGIN|END)"
        accept_pattern = "(ACCEPT)"
        type1_pattern = "(ARRIVE|OPEN|CLOSE)"
        type2_pattern = "(IN)"
        type3_pattern = "(OUT)"
        type4_pattern = "(RECEIVE)"
        type5_pattern = "(SCHE)"
        type6_pattern = "(SCHE)"
        pattern1 = "\\[" + float_pattern + "]" + type1_pattern + "-" + floor_pattern + "-" + int_pattern
        pattern2 = "\\[" + float_pattern + "]" + type2_pattern + "-" + int_pattern + "-" + floor_pattern + "-" + int_pattern
        pattern3 = "\\[" + float_pattern + "]" + type3_pattern + "-" + out_pattern + "-" + int_pattern + "-" + floor_pattern + "-" + int_pattern
        pattern4 = "\\[" + float_pattern + "]" + type4_pattern + "-" + int_pattern + "-" + int_pattern
        pattern5 = "\\[" + float_pattern + "]" + type5_pattern + "-" + accept_pattern + "-" + int_pattern + "-" + float_pattern + "-" + floor_pattern
        pattern6 = "\\[" + float_pattern + "]" + type6_pattern + "-" + sche_pattern + "-" + int_pattern
        pattern1 = re.compile(pattern1)        # ARRIVE-OPEN-CLOSE
        pattern2 = re.compile(pattern2)        # IN
        pattern3 = re.compile(pattern3)        # OUT
        pattern4 = re.compile(pattern4)        # RECEIVE
        pattern5 = re.compile(pattern5)        # SCHE-ACCEPT
        pattern6 = re.compile(pattern6)        # SCHE-BEGIN/END
        def parseFloor(floorInfo: str):
            if (floorInfo[0] == 'B'):
                return -int(floorInfo[1:]) + 1
            else:
                return int(floorInfo[1:])
        def parseType(type: str):
            if (type == "ARRIVE"):
                return OperationType.ARRIVE
            elif (type == "OPEN"):
                return OperationType.OPEN
            elif (type == "CLOSE"):
                return OperationType.CLOSE
            elif (type == "IN"):
                return OperationType.IN
            elif (type == "OUT"):
                return OperationType.OUT
            elif (type == "RECEIVE"):
                return OperationType.RECEIVE
            elif (type == "SCHE"):
                return OperationType.SCHE
            raise Exception("Unknown type: {type}")
        # ARRIVE-OPEN-CLOSE
        match = re.fullmatch(pattern1, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            floor = parseFloor(match.group(3))
            elevatorIndex = int(match.group(4))
            if (not (-3 <= floor and floor <= 7)):
                raise Exception(f"Invalid index of floor info: {operationInfo}")
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            return Operation(opType, elevatorIndex, 1, floor, -1, 1, 0.4, timestamp)
        # IN
        match = re.fullmatch(pattern2, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            personIndex = int(match.group(3))
            floor = parseFloor(match.group(4))
            elevatorIndex = int(match.group(5))
            if (not (1 <= personIndex and personIndex <= 2147483647)):
                raise Exception(f"Invalid index of personIndex info: {operationInfo}")
            if (not (-3 <= floor and floor <= 7)):
                raise Exception(f"Invalid index of floor info: {operationInfo}")
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            return Operation(opType, elevatorIndex, 1, floor, personIndex, 1, 0.4, timestamp)
        # OUT
        match = re.fullmatch(pattern3, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            outType = match.group(3) 
            if (outType == 'S'):
                outType = 1
            else:
                outType = 0
            personIndex = int(match.group(4))
            floor = parseFloor(match.group(5))
            elevatorIndex = int(match.group(6))
            if (not (1 <= personIndex and personIndex <= 2147483647)):
                raise Exception(f"Invalid index of personIndex info: {operationInfo}")
            if (not (-3 <= floor and floor <= 7)):
                raise Exception(f"Invalid index of floor info: {operationInfo}")
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            return Operation(opType, elevatorIndex, outType, floor, personIndex, 1, 0.4, timestamp)
        # RECEIVE
        match = re.fullmatch(pattern4, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            elevatorIndex = int(match.group(4))     
            personIndex = int(match.group(3))
            if (not (1 <= personIndex and personIndex <= 2147483647)):
                raise Exception(f"Invalid index of personIndex info: {operationInfo}")
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            return Operation(opType, elevatorIndex, 1, -1, personIndex, 1, 0.4, timestamp)
        # SCHE-ACCEPT
        match = re.fullmatch(pattern5, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            elevatorIndex = int(match.group(4))
            speed = float(match.group(5))
            floor = parseFloor(match.group(6))
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            if (not (-3 <= floor and floor <= 7)):
                raise Exception(f"Invalid index of floor info: {operationInfo}")
            return Operation(opType, elevatorIndex, 1, floor, -1, -1, speed, timestamp)
        # SCHE-BEGIN/END
        match = re.fullmatch(pattern6, operationInfo)
        if (match):
            timestamp = float(match.group(1))
            opType = parseType(match.group(2))
            scheType = match.group(3)
            if (scheType == "BEGIN"):
                scheType = 0
            else:
                scheType = 1
            elevatorIndex = int(match.group(4))
            if (not (1 <= elevatorIndex and elevatorIndex <= 6)):
                raise Exception(f"Invalid index of elevatorIndex info: {operationInfo}")
            return Operation(opType, elevatorIndex, 1, -1, -1, scheType, 0.4, timestamp)
        # Invalid format
        raise Exception(f"Invalid format of operation info: {operationInfo}")

if __name__ == "__main__":
    operation = Operation.parse("[ 9.7610]ARRIVE-B1-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)
    operation = Operation.parse("[ 11.3930]OUT-98-F3-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)