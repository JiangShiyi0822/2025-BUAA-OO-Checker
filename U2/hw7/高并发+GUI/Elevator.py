from enum import Enum
from Person import Person
from Operation import OutOperationType, ScheOperationType

class ElevatorState(Enum):
    CLOSE = 0
    OPEN = 1

class Elevator:
    index: int
    minFloor: int
    maxFloor: int
    moveInterval: float
    openInterval: float
    requestLimit: int
    initFloor: int

    currentFloor: int
    requests: list[Person]
    state: ElevatorState
    receivedPersons: list[Person]
    timestamp: float

    acceptingSche: bool
    acceptScheTime: float
    processingSche: bool
    moveCountBeforeSche: int
    openDoorTimestamp: float
    scheMoveInterval: float
    scheFloor: int

    acceptingUpdate: bool
    acceptUpdateTime: float
    processingUpdate: bool
    beginUpdateTime: float
    updated: bool
    isTopElevator: bool
    transFloor: int
    moveCountBeforeUpdate: int

    ifHaveOpenDoor: bool

    def __init__(self, index: int, minFloor: int, maxFloor: int, moveInterval: float, openInterval: float, requestLimit: int, initFloor: int):
        self.index = index
        self.minFloor = minFloor
        self.maxFloor = maxFloor
        self.moveInterval = moveInterval
        self.openInterval = openInterval
        self.requestLimit = requestLimit
        self.initFloor = initFloor
        self.reset()
        self.ifHaveOpenDoor = False
    
    def reset(self):
        self.processingSche = False
        self.currentFloor = self.initFloor
        self.requests = []
        self.receivedPersons = []
        self.state = ElevatorState.CLOSE
        self.timestamp = -1000000000
        self.acceptScheTime = 0.0
        self.openDoorTimestamp = 0.0
        self.acceptingSche = False
        self.moveCountBeforeSche = 0
        self.scheMoveInterval = 0.4
        self.scheFloor = 0

        self.acceptingUpdate = False
        self.acceptUpdateTime = 0.0
        self.processingUpdate = False
        self.beginUpdateTime = 0.0
        self.updated = False
        self.transFloor = 0
        self.moveCountBeforeUpdate = 0
        self.isTopElevator = False
        self.ifHaveOpenDoor = False
    
    def closeDoor(self, timestamp: float, floor: int):
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: closeDoor in elevator {self.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: closeDoor in elevator {self.index}.")
        if (timestamp - self.timestamp < self.openInterval - 0.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: closeDoor in elevator {self.index}.")
        if (self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: closeDoor in elevator {self.index} when it is updating.")
        self.state = ElevatorState.CLOSE
        self.timestamp = timestamp
    
    def openDoor(self, timestamp: float, floor: int):
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: openDoor in elevator {self.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: openDoor in elevator {self.index}.")
        if (self.processingSche and floor != self.scheFloor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: openDoor in wrong floor when inSche in elevator {self.index}.")
        if (self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: openDoor in elevator {self.index} when it is updating.")
        if (self.processingSche and floor == self.scheFloor):
            self.ifHaveOpenDoor = True
        self.openDoorTimestamp = timestamp
        self.state = ElevatorState.OPEN
        self.timestamp = timestamp
    
    def move(self, timestamp: float, targetFloor: int):
        if (not self.receivedPersons and not self.processingSche):
            if (not (self.updated and self.currentFloor == self.transFloor)):
                raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Elevator move when received no person in elevator {self.index}.")
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: move in elevator {self.index}.")
        if (not (self.minFloor <= targetFloor and targetFloor <= self.maxFloor)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor out of bound in operation: move in elevator {self.index}.")
        if (targetFloor == self.currentFloor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is current floor in operation: move in elevator {self.index}.")
        if (not (targetFloor == self.currentFloor + 1 or targetFloor == self.currentFloor - 1)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is too far in operation: move in elevator {self.index}.")
        if (self.acceptingSche and self.moveCountBeforeSche >= 2):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Move too many times before beginSche in elevator {self.index}.")
        if (self.acceptingUpdate and self.moveCountBeforeUpdate >= 2):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Move too many times before beginUpdate in elevator {self.index}.")
        if (self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: move in elevator {self.index} when it is updating.")
        if (self.acceptingSche):
            self.moveCountBeforeSche += 1
        if (self.acceptingUpdate):
            self.moveCountBeforeUpdate += 1
        self.currentFloor = targetFloor
        self.timestamp = timestamp
    
    def addPerson(self, timestamp: float, person: Person, floor: int):
        if (self.processingSche):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: addPerson in elevator {self.index} when it is inSche.")
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: addPerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != self.index):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of elevator in operation: addPerson in elevator {self.index} and person {person.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: addPerson in elevator {self.index} and person {person.index}.")
        if (person.currentFloor != self.currentFloor):
            raise Exception(f"Time {self.timestamp} Mismatch of floor in operation: addPerson in elevator {self.index} and person {person.index}.")
        if (person.isInElevator):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-In: addPerson in elevator {self.index} and person {person.index}.")
        if (len(self.requests) >= self.requestLimit):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Too many persons in operation: addPerson in elevator {self.index} and person {person.index}.")
        self.requests.append(person)
        person.isInElevator = True
    
    def removePerson(self, timestamp: float, person: Person, floor: int, outType: OutOperationType):
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: removePerson in elevator {self.index} and person {person.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != self.index):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of elevator in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (not person.isInElevator):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-Out or Not-In: removePerson in elevator {self.index} and person {person.index}.")
        if (outType == OutOperationType.S and person.toFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: Successful removePerson in elevator {self.index} and person {person.index}.")
        if (outType == OutOperationType.F and person.toFloor == floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} fRemovePerson when he/she is acctually successfully arrived. In elevator {self.index} and person {person.index}.")
        self.requests.remove(person)
        if (person in self.receivedPersons):
            self.receivedPersons.remove(person)
        person.currentFloor = self.currentFloor
        person.isInElevator = False
        person.targetElevator = -1
        if (outType == OutOperationType.F):
            person.fromFloor = floor

    def receivePerson(self, timestamp: float, person: Person):
        if (person.targetElevator != -1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: receivePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != -1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-Receive: receivePerson in elevator {self.index} and person {person.index}.")
        if (self.processingSche):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: receivePerson in elevator {self.index} and person {person.index} when it is scheduling.")
        if (self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: receivePerson in elevator {self.index} and person {person.index} when it is updating.")
        person.targetElevator = self.index
        self.receivedPersons.append(person)

    def beginSche(self, timestamp: float):
        if (self.processingSche):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginSche in elevator {self.index} when it is inSche.")
        self.acceptingSche = False
        self.processingSche = True
        self.moveInterval = self.scheMoveInterval
        self.moveCountBeforeSche = 0
        self.openInterval = 1.0
        for person in self.receivedPersons:
            if person not in self.requests:
                person.targetElevator = -1
        self.receivedPersons.clear()

    def endSche(self, timestamp: float):
        if (not self.processingSche):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: endSche in elevator {self.index} when it is not inSche.")
        if (timestamp - self.acceptScheTime > 6.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Sche time too long in elevator {self.index}.")
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: endSche in elevator {self.index} when the door is not close.")
        if (len(self.requests) != 0):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: endSche in elevator {self.index} when there are still persons.")
        if (not self.ifHaveOpenDoor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} You did not open the door when reach the target floor during SCHE in elevator {self.index}.")
        self.processingSche = False
        self.moveInterval = 0.4
        self.openInterval = 0.4
        self.ifHaveOpenDoor = False

    def acceptSche(self, timestamp: float, speed: float, scheFloor: int):
        if (not (speed == 0.2 or speed == 0.3 or speed == 0.4 or speed == 0.5)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid speed in operation: acceptSche in elevator {self.index}.")
        if (not (-1 <= scheFloor and scheFloor <= 5)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid scheFloor in operation: acceptSche in elevator {self.index}.")
        self.scheMoveInterval = speed
        self.acceptingSche = True
        self.acceptScheTime = timestamp
        self.scheFloor = scheFloor

    def acceptUpdate(self, timestamp: float, isTopElevator: bool, transFloor: int):
        if (not (self.minFloor <= transFloor and transFloor <= self.maxFloor)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid transFloor in operation: acceptUpdate in elevator {self.index}.")
        if (self.acceptingSche or self.processingSche):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: acceptUpdate in elevator {self.index} when it is scheduling.")
        if (self.acceptingUpdate or self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: acceptUpdate in elevator {self.index} when it is updating.")
        if (self.updated):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: acceptUpdate in elevator {self.index} when it is updated.")
        if (not (-1 <= transFloor and transFloor <= 5)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid transFloor in operation: acceptUpdate in elevator {self.index}.")
        self.acceptingUpdate = True
        self.acceptUpdateTime = timestamp
        self.transFloor = transFloor
        self.moveCountBeforeUpdate = 0
        self.isTopElevator = isTopElevator
    
    def beginUpdate(self, timestamp: float):
        if (not self.acceptingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginUpdate in elevator {self.index} when it is not accepting update.")
        if (self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginUpdate in elevator {self.index} when it is updating.")
        if (self.updated):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginUpdate in elevator {self.index} when it is updated.")
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginUpdate in elevator {self.index} when the door is not close.")
        if (len(self.requests) != 0):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginUpdate in elevator {self.index} when there are still persons.")
        self.acceptingUpdate = False
        self.moveCountBeforeUpdate = 0
        self.processingUpdate = True
        self.beginUpdateTime = timestamp
        for person in self.receivedPersons:
            if person not in self.requests:
                person.targetElevator = -1
        self.receivedPersons.clear()
    
    def endUpdate(self, timestamp: float):
        if (not self.processingUpdate):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: endUpdate in elevator {self.index} when it is not updating.")
        if (timestamp - self.acceptUpdateTime > 6.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Update time too long in elevator {self.index}.")
        if (timestamp - self.beginUpdateTime < 0.99999):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Update time too short in elevator {self.index}.")
        self.processingUpdate = False
        self.updated = True
        self.moveInterval = 0.2
        if (self.isTopElevator):
            self.minFloor = self.transFloor
            self.currentFloor = self.transFloor + 1
        else:
            self.maxFloor = self.transFloor
            self.currentFloor = self.transFloor - 1