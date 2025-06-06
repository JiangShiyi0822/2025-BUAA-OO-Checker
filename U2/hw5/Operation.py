from enum import Enum
import re

class OperationType(Enum):
    ARRIVE = 0
    OPEN = 1
    CLOSE = 2
    IN = 3
    OUT = 4

class Operation:
    opType: OperationType
    elevatorIndex: int
    floor: int
    personIndex: int
    timestamp: float

    def __init__(self, opType: OperationType, elevatorIndex: int, floor: int, personIndex: int, timestamp: float):
        self.opType = opType
        self.elevatorIndex = elevatorIndex
        self.floor = floor
        self.personIndex = personIndex
        self.timestamp = timestamp
    
    @staticmethod
    def parse(operationInfo: str):
        operationInfo = operationInfo.replace(" ", "")
        operationInfo = operationInfo.replace("\n", "")
        float_pattern = "(\\d*\\.?\\d+)"
        int_pattern = "(\\d+)"
        floor_pattern = "(F\\d+|B\\d+)"
        type1_pattern = "(ARRIVE|OPEN|CLOSE)"
        type2_pattern = "(IN|OUT)"
        pattern1 = "\\[" + float_pattern + "]" + type1_pattern + "-" + floor_pattern + "-" + int_pattern
        pattern2 = "\\[" + float_pattern + "]" + type2_pattern + "-" + int_pattern + "-" + floor_pattern + "-" + int_pattern
        pattern1 = re.compile(pattern1)
        pattern2 = re.compile(pattern2)
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
            raise Exception("Unknown type: {type}")
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
            return Operation(opType, elevatorIndex, floor, -1, timestamp)
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
            return Operation(opType, elevatorIndex, floor, personIndex, timestamp)
        raise Exception(f"Invalid format of operation info: {operationInfo}")

if __name__ == "__main__":
    operation = Operation.parse("[ 9.7610]ARRIVE-B1-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)
    operation = Operation.parse("[ 11.3930]OUT-98-F3-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)