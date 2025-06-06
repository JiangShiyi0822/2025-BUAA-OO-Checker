from Elevator import *
from Person import Person
from Operation import *

class Checker:
    elevators: dict[int, Elevator]
    persons: dict[int, Person]
    operations: list[Operation]
    def __init__(self, elevators: list[Elevator], persons: list[Person], operations: list[Operation]):
        self.elevators = {}
        self.persons = {}
        for elevator in elevators:
            if (elevator.index in self.elevators.keys()):
                raise Exception(f"Re-exist index in elevator {elevator.index}.")
            self.elevators[elevator.index] = elevator
        for person in persons:
            if (person.index in self.persons.keys()):
                raise Exception(f"Re-exist index in person {person.index}.")
            self.persons[person.index] = person
        self.operations = operations
        self.reset()
    
    def reset(self):
        for elevator in self.elevators.values():
            elevator.reset()
        for person in self.persons.values():
            person.reset()

    # [时间戳]ARRIVE-所在层-电梯ID
    # [时间戳]OPEN-所在层-电梯ID
    # [时间戳]CLOSE-所在层-电梯ID
    # [时间戳]IN-乘客ID-所在层-电梯ID
    # [时间戳]OUT-S/F-乘客ID-所在层-电梯ID
    # [时间戳]RECEIVE-乘客ID-电梯ID
    # [时间戳]SCHE-BEGIN-电梯ID
    # [时间戳]SCHE-END-电梯ID
    # [时间戳]SCHE-ACCEPT-电梯ID-临时运行速度-目标楼层

    def check(self):
        self.reset()
        lastTimestamp = -10000
        for operation in self.operations:
            if (operation.timestamp - lastTimestamp < -0.000001):
                raise Exception(f"The order of operation is incorrect: {operation.timestamp} > {lastTimestamp}.")
            if (operation.opType == OperationType.ARRIVE):
                self.processArrive(operation.timestamp, operation.floor, operation.elevatorIndex)
            elif (operation.opType == OperationType.OPEN):
                self.processOpen(operation.timestamp, operation.floor, operation.elevatorIndex)
            elif (operation.opType == OperationType.CLOSE):
                self.processClose(operation.timestamp, operation.floor, operation.elevatorIndex)
            elif (operation.opType == OperationType.IN):
                self.processIn(operation.timestamp, operation.personIndex, operation.floor, operation.elevatorIndex)
            elif (operation.opType == OperationType.OUT):
                self.processOut(operation.timestamp,operation.outType, operation.personIndex, operation.floor, operation.elevatorIndex)
            elif (operation.opType == OperationType.SCHE):
                self.processSche(operation.timestamp, operation.scheType, operation.elevatorIndex, operation.speed, operation.floor)
            elif (operation.opType == OperationType.RECEIVE):
                self.processReceive(operation.timestamp, operation.personIndex, operation.elevatorIndex)    
        for elevator in self.elevators.values():
            if (elevator.state != ElevatorState.CLOSE):
                raise Exception(f"The door is not close in elevator {elevator.index}.")
        for person in self.persons.values():
            if (person.isInElevator):
                raise Exception(f"The person {person.index} is trapped in the elevator.")
            if (person.currentFloor != person.toFloor):
                raise Exception(f"The person {person.index} is not in the correct floor.")

    def calcPerfomanceInfo(self):
        systemRunTime = self.operations[-1].timestamp
        avgTaskCompleteTime = 0
        powerConsumption = 0

        taskCompleteTimeSum = 0
        taskWeightSum = 0
        personLeaveTime = {}
        for operation in self.operations:
            if (operation.opType == OperationType.OUT):
                personLeaveTime[operation.personIndex] = operation.timestamp
            
            if (operation.opType == OperationType.ARRIVE):
                powerConsumption += 0.4
            elif (operation.opType == OperationType.OPEN):
                powerConsumption += 0.1
            elif (operation.opType == OperationType.CLOSE):
                powerConsumption += 0.1
        for person in self.persons.values():
            taskCompleteTimeSum += person.priority * (personLeaveTime[person.index] - person.arriveTime)
            taskWeightSum += person.priority
        avgTaskCompleteTime = taskCompleteTimeSum / taskWeightSum
        return (systemRunTime, avgTaskCompleteTime, powerConsumption) 

    def processArrive(self, timestamp: float, floor: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        self.elevators[elevatorIndex].move(timestamp, floor)
    
    def processOpen(self, timestamp: float, floor: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        self.elevators[elevatorIndex].openDoor(timestamp, floor)
    
    def processClose(self, timestamp: float, floor: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
        
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        self.elevators[elevatorIndex].closeDoor(timestamp, floor)
    
    def processIn(self, timestamp: float, personIndex: int, floor: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        if (not (personIndex in self.persons.keys())):
            raise Exception(f"Unexist index in person {personIndex}.")
        self.elevators[elevatorIndex].addPerson(timestamp, self.persons[personIndex], floor)
    
    def processOut(self, timestamp: float, outTpye: int, personIndex: int, floor: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        if (not (personIndex in self.persons.keys())):
            raise Exception(f"Unexist index in person {personIndex}.")
        if (outTpye == 1):
            self.elevators[elevatorIndex].sRemovePerson(timestamp, self.persons[personIndex], floor)
        if (outTpye == 0):
            self.elevators[elevatorIndex].fRemovePerson(timestamp, self.persons[personIndex], floor)

    def processSche(self, timestamp: float, scheType: int, elevatorIndex: int, speed: float, scheFloor: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        if (scheType == 1):
            self.elevators[elevatorIndex].endSche(timestamp)
        elif (scheType == 0):
            self.elevators[elevatorIndex].beginSche(timestamp)
        elif (scheType == -1):
            self.elevators[elevatorIndex].acceptSche(timestamp, speed, scheFloor)
        
        
    def processReceive(self, timestamp: float, personIndex: int, elevatorIndex: int):
        if (not (elevatorIndex in self.elevators.keys())):
            raise Exception(f"Unexist index in elevator {elevatorIndex}.")
        if (not (personIndex in self.persons.keys())):
            raise Exception(f"Unexist index in person {personIndex}.")
        self.elevators[elevatorIndex].receivePerson(timestamp, self.persons[personIndex])
    
def getPersons(filepath: str):
    persons = []
    with open(filepath, mode='r') as f:
        personInfos = f.readlines()
        for personInfo in personInfos:
            if "SCHE" in personInfo:
                continue
            persons.append(Person.parse(personInfo))
    return persons

def getOperations(filepath: str):
    operations = []
    with open(filepath, mode='r') as f:
        operationInfos = f.readlines()
        for operationInfo in operationInfos:
            operations.append(Operation.parse(operationInfo))
    return operations

def getElevators():
    elevators = []
    for i in range(6):
        elevators.append(Elevator(i + 1, -3, 7, 0.4, 0.4, 6, 1))
    return elevators

def check(input, output):
    checker = Checker(getElevators(), getPersons(input), getOperations(output))
    checker.check()
    return checker.calcPerfomanceInfo()