from enum import Enum
import Operation
import re

class OperationType(Enum):
    ARRIVE = 0
    OPEN = 1
    CLOSE = 2
    IN = 3
    OUT = 4
    RECEIVE = 5
    SCHE = 6
    UPDATE = 7

class OutOperationType(Enum):
    NONE = -1
    S = 0
    F = 1

class ScheOperationType(Enum):
    NONE = -1
    ACCEPT = 0
    BEGIN = 1
    END = 2

class UpdateOperationType(Enum):
    NONE = -1
    ACCEPT = 0
    BEGIN = 1
    END = 2

class Operation:
    opType: OperationType
    elevatorIndex: int
    floor: int
    personIndex: int
    timestamp: float

    outType: OutOperationType
    scheType: ScheOperationType
    scheSpeed: float
    updateType: UpdateOperationType
    updateTopElevatorIndex: int
    updateBottomElevatorIndex: int
    updateTransFloor: int

    # outType 0: F, 1: S
    # scheType 0: BEGIN, 1: END, -1: ACCEPT
    def __init__(
            self, 
            opType: OperationType, 
            elevatorIndex: int, 
            floor: int, 
            personIndex: int, 
            outType: OutOperationType, 
            scheType: ScheOperationType, 
            scheMoveInterval: float, 
            updateType: UpdateOperationType, 
            updateTopElevatorIndex: int, 
            updateBottomElevatorIndex: int, 
            updateTransFloor: int, 
            timestamp: float
            ):
        self.opType = opType
        self.elevatorIndex = elevatorIndex
        self.floor = floor
        self.personIndex = personIndex

        self.outType = outType
        self.scheType = scheType
        self.scheSpeed = scheMoveInterval
        self.updateType = updateType
        self.updateTopElevatorIndex = updateTopElevatorIndex
        self.updateBottomElevatorIndex = updateBottomElevatorIndex
        self.updateTransFloor = updateTransFloor
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
    # [时间戳]UPDATE-BEGIN-上层电梯ID-下层电梯ID
    # [时间戳]UPDATE-END-上层电梯ID-下层电梯ID

    @staticmethod
    def parseFloor(floorInfo: str):
        if (floorInfo[0] == 'B'):
            result = -int(floorInfo[1:]) + 1
        else:
            result = int(floorInfo[1:])
        if (not (-3 <= result and result <= 7)):
            raise Exception(f"Invalid index of floor info: {floorInfo}")
        return result
    
    @staticmethod
    def parsePersonIndex(personIndexInfo: str):
        result = int(personIndexInfo)
        if (not (1 <= result and result <= 2147483647)):
            raise Exception(f"Invalid index of personIndex info: {personIndexInfo}")
        return result

    @staticmethod
    def parseElevatorIndex(elevatorIndexInfo: str):
        result = int(elevatorIndexInfo)
        if (not (1 <= result and result <= 6)):
            raise Exception(f"Invalid index of elevatorIndex info: {elevatorIndexInfo}")
        return result

    @staticmethod
    def parseArrive(match: re.Match[str]):
        timestamp = float(match.group(1))
        floor = Operation.parseFloor(match.group(2))
        elevatorIndex = Operation.parseElevatorIndex(match.group(3))
        return Operation(
            opType=OperationType.ARRIVE, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseOpen(match: re.Match[str]):
        timestamp = float(match.group(1))
        floor = Operation.parseFloor(match.group(2))
        elevatorIndex = Operation.parseElevatorIndex(match.group(3))
        return Operation(
            opType=OperationType.OPEN, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseClose(match: re.Match[str]):
        timestamp = float(match.group(1))
        floor = Operation.parseFloor(match.group(2))
        elevatorIndex = Operation.parseElevatorIndex(match.group(3))
        return Operation(
            opType=OperationType.CLOSE, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )

    @staticmethod
    def parseIn(match: re.Match[str]):
        timestamp = float(match.group(1))
        personIndex = Operation.parsePersonIndex(match.group(2))
        floor = Operation.parseFloor(match.group(3))
        elevatorIndex = Operation.parseElevatorIndex(match.group(4))
        return Operation(
            opType=OperationType.IN, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=personIndex,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseOut(match: re.Match[str]):
        timestamp = float(match.group(1))
        outType = match.group(2)
        if (outType == 'S'):
            outType = OutOperationType.S
        else:
            outType = OutOperationType.F
        personIndex = Operation.parsePersonIndex(match.group(3))
        floor = Operation.parseFloor(match.group(4))
        elevatorIndex = Operation.parseElevatorIndex(match.group(5))
        return Operation(
            opType=OperationType.OUT, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=personIndex,
            outType=outType,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )

    @staticmethod
    def parseReceive(match: re.Match[str]):
        timestamp = float(match.group(1))
        personIndex = Operation.parsePersonIndex(match.group(2))
        elevatorIndex = Operation.parseElevatorIndex(match.group(3))
        return Operation(
            opType=OperationType.RECEIVE, 
            elevatorIndex=elevatorIndex, 
            floor=-1,
            personIndex=personIndex,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseScheAccept(match: re.Match[str]):
        timestamp = float(match.group(1))
        elevatorIndex = Operation.parseElevatorIndex(match.group(2))
        speed = float(match.group(3))                
        floor = Operation.parseFloor(match.group(4))
        return Operation(
            opType=OperationType.SCHE, 
            elevatorIndex=elevatorIndex, 
            floor=floor,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.ACCEPT, 
            scheMoveInterval=speed,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseSche(match: re.Match[str]):
        timestamp = float(match.group(1))
        scheType = match.group(2)
        if (scheType == "BEGIN"):
            scheType = ScheOperationType.BEGIN
        else:
            scheType = ScheOperationType.END
        elevatorIndex = Operation.parseElevatorIndex(match.group(3))
        return Operation(
            opType=OperationType.SCHE, 
            elevatorIndex=elevatorIndex, 
            floor=-1,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=scheType, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.NONE,
            updateTopElevatorIndex=-1,
            updateBottomElevatorIndex=-1,
            updateTransFloor=-1,
            timestamp=timestamp
        )

    @staticmethod
    def parseUpdateAccept(match: re.Match[str]):
        timestamp = float(match.group(1))
        topElevatorIndex = Operation.parseElevatorIndex(match.group(2))
        bottomElevatorIndex = Operation.parseElevatorIndex(match.group(3))
        transFloor = Operation.parseFloor(match.group(4))
        return Operation(
            opType=OperationType.UPDATE, 
            elevatorIndex=-1, 
            floor=-1,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=UpdateOperationType.ACCEPT,
            updateTopElevatorIndex=topElevatorIndex,
            updateBottomElevatorIndex=bottomElevatorIndex,
            updateTransFloor=transFloor,
            timestamp=timestamp
        )
    
    @staticmethod
    def parseUpdate(match: re.Match[str]):
        timestamp = float(match.group(1))
        updateType = match.group(2)
        if (updateType == "BEGIN"):
            updateType = UpdateOperationType.BEGIN
        else:
            updateType = UpdateOperationType.END
        topElevatorIndex = Operation.parseElevatorIndex(match.group(3))
        bottomElevatorIndex = Operation.parseElevatorIndex(match.group(4))
        return Operation(
            opType=OperationType.UPDATE, 
            elevatorIndex=-1, 
            floor=-1,
            personIndex=-1,
            outType=OutOperationType.NONE,
            scheType=ScheOperationType.NONE, 
            scheMoveInterval=0.4,
            updateType=updateType,
            updateTopElevatorIndex=topElevatorIndex,
            updateBottomElevatorIndex=bottomElevatorIndex,
            updateTransFloor=-1,
            timestamp=timestamp
        )

    @staticmethod
    def parse(operationInfo: str):
        operationInfo = operationInfo.replace(" ", "")
        operationInfo = operationInfo.replace("\n", "")
        float_pattern = "(\\d*\\.?\\d+)"
        timestampPattern = "\\[" + float_pattern + "]"
        intPattern = "(\\d+)"
        floorPattern = "(F\\d+|B\\d+)"
        outPattern = "(S|F)"
        beginEndPattern = "(BEGIN|END)"
        patternArrive = timestampPattern + "ARRIVE" + "-" + floorPattern + "-" + intPattern
        patternOpen = timestampPattern + "OPEN" + "-" + floorPattern + "-" + intPattern
        patternClose = timestampPattern + "CLOSE" + "-" + floorPattern + "-" + intPattern
        patternIn = timestampPattern + "IN" + "-" + intPattern + "-" + floorPattern + "-" + intPattern
        patternOut = timestampPattern + "OUT" + "-" + outPattern + "-" + intPattern + "-" + floorPattern + "-" + intPattern
        patternReceive = timestampPattern + "RECEIVE" + "-" + intPattern + "-" + intPattern
        patternScheAccept = timestampPattern + "SCHE" + "-" + "ACCEPT" + "-" + intPattern + "-" + float_pattern + "-" + floorPattern
        patternSche = timestampPattern + "SCHE" + "-" + beginEndPattern + "-" + intPattern
        patternUpdateAccept = timestampPattern + "UPDATE" + "-" + "ACCEPT" + "-" + intPattern + "-" + intPattern + "-" + floorPattern
        patternUpdate = timestampPattern + "UPDATE" + "-" + beginEndPattern + "-" + intPattern + "-" + intPattern
        
        patternArrive = re.compile(patternArrive)           # ARRIVE
        patternOpen = re.compile(patternOpen)               # OPEN
        patternClose = re.compile(patternClose)             # CLOSE
        patternIn = re.compile(patternIn)                   # IN
        patternOut = re.compile(patternOut)                 # OUT
        patternReceive = re.compile(patternReceive)         # RECEIVE
        patternScheAccept = re.compile(patternScheAccept)   # SCHE-ACCEPT
        patternSche = re.compile(patternSche)               # SCHE-BEGIN/END
        patternUpdateAccept = re.compile(patternUpdateAccept) # UPDATE-ACCEPT
        patternUpdate = re.compile(patternUpdate)           # UPDATE-BEGIN/END
        match = re.fullmatch(patternArrive, operationInfo)
        if (match):
            return Operation.parseArrive(match)
        match = re.fullmatch(patternOpen, operationInfo)
        if (match):
            return Operation.parseOpen(match)
        match = re.fullmatch(patternClose, operationInfo)
        if (match):
            return Operation.parseClose(match)
        match = re.fullmatch(patternIn, operationInfo)
        if (match):
            return Operation.parseIn(match)
        match = re.fullmatch(patternOut, operationInfo)
        if (match):
            return Operation.parseOut(match)
        match = re.fullmatch(patternReceive, operationInfo)
        if (match):
            return Operation.parseReceive(match)
        match = re.fullmatch(patternScheAccept, operationInfo)
        if (match):
            return Operation.parseScheAccept(match)
        match = re.fullmatch(patternSche, operationInfo)
        if (match):
            return Operation.parseSche(match)
        match = re.fullmatch(patternUpdateAccept, operationInfo)
        if (match):
            return Operation.parseUpdateAccept(match)
        match = re.fullmatch(patternUpdate, operationInfo)
        if (match):
            return Operation.parseUpdate(match)
        # Invalid format
        raise Exception(f"Invalid format of operation info: {operationInfo}")

if __name__ == "__main__":
    operation = Operation.parse("[ 9.7610]ARRIVE-B1-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)
    operation = Operation.parse("[ 11.3930]OUT-98-F3-6")
    print(operation.timestamp, operation.opType.name, operation.personIndex, operation.floor, operation.elevatorIndex)