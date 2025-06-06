from enum import Enum
from Person import Person

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

    inSche: int
    currentFloor: int
    requests: list[Person]
    state: ElevatorState
    receivedPersons: list[Person]
    timestamp: float
    acceptScheTime: float
    acceptedSche: int
    moveBeforeBeginSche: int
    openDoorTimeinSche: float
    scheSpeed: float
    scheFloor: int

    def __init__(self, index: int, minFloor: int, maxFloor: int, moveInterval: float, openInterval: float, requestLimit: int, initFloor: int):
        self.index = index
        self.minFloor = minFloor
        self.maxFloor = maxFloor
        self.moveInterval = moveInterval
        self.openInterval = openInterval
        self.requestLimit = requestLimit
        self.initFloor = initFloor
        self.reset()
    
    def reset(self):
        self.inSche = 0
        self.currentFloor = self.initFloor
        self.requests = []
        self.receivedPersons = []
        self.state = ElevatorState.CLOSE
        self.timestamp = -1000000000
        self.acceptScheTime = 0.0
        self.openDoorTimeinSche = 0.0
        self.acceptedSche = 0
        self.moveBeforeBeginSche = 0
        self.scheSpeed = 0.4
        self.scheFloor = 0
    
    def closeDoor(self, timestamp: float, floor: int):
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: closeDoor in elevator {self.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: closeDoor in elevator {self.index}.")
        if (timestamp - self.timestamp < self.openInterval - 0.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: closeDoor in elevator {self.index}.")
        self.state = ElevatorState.CLOSE
        self.timestamp = timestamp
    
    def openDoor(self, timestamp: float, floor: int):
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: openDoor in elevator {self.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: openDoor in elevator {self.index}.")
        if (self.inSche == 1 and floor != self.scheFloor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: openDoor in wrong floor when inSche in elevator {self.index}.")
        if (self.inSche == 1):
            self.openDoorTimeinSche = timestamp
        self.state = ElevatorState.OPEN
        self.timestamp = timestamp
    
    def move(self, timestamp: float, targetFloor: int):
        if (not self.receivedPersons and self.inSche == 0):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Elevator move when received no person in elevator {self.index}.")
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: move in elevator {self.index}.")
        if (not (self.minFloor <= targetFloor and targetFloor <= self.maxFloor)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor out of bound in operation: move in elevator {self.index}.")
        if (targetFloor == self.currentFloor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is current floor in operation: move in elevator {self.index}.")
        if (not (targetFloor == self.currentFloor + 1 or targetFloor == self.currentFloor - 1)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is too far in operation: move in elevator {self.index}.")
        if (self.acceptedSche == 1 and self.moveBeforeBeginSche > 2):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Move too many times before beginSche in elevator {self.index}.")
        if (timestamp - self.timestamp < self.moveInterval - 0.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Move too fast in operation: move in elevator {self.index}.")
        if (self.acceptedSche == 1):
            self.moveBeforeBeginSche += 1
        self.currentFloor = targetFloor
        self.timestamp = timestamp
    
    def addPerson(self, timestamp: float, person: Person, floor: int):
        if (self.inSche == 1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: addPerson in elevator {self.index} when it is inSche.")
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: addPerson in elevator {self.index} and person {person.index}.")
        if (timestamp < person.arriveTime):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: addPerson in elevator {self.index} and person {person.index}.")
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
    
    def sRemovePerson(self, timestamp: float, person: Person, floor: int):
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: removePerson in elevator {self.index} and person {person.index}.")
        if (timestamp < person.arriveTime):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != self.index):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of elevator in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (not person.isInElevator):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-Out or Not-In: removePerson in elevator {self.index} and person {person.index}.")
        if (person.toFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: Successful removePerson in elevator {self.index} and person {person.index}.")
        self.requests.remove(person)
        if (person in self.receivedPersons):
            self.receivedPersons.remove(person)
        person.currentFloor = self.currentFloor
        person.isInElevator = False

    def fRemovePerson(self, timestamp: float, person: Person, floor: int):
        if (self.state != ElevatorState.OPEN):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: removePerson in elevator {self.index} and person {person.index}.")
        if (timestamp < person.arriveTime):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: removePerson in elevator {self.index} and person {person.index}.")        
        if (self.currentFloor != floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of floor({floor}) in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != self.index):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Mismatch of elevator in operation: removePerson in elevator {self.index} and person {person.index}.")
        if (not person.isInElevator):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-Out or Not-In: removePerson in elevator {self.index} and person {person.index}.")
        if (person.toFloor == floor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} fRemovePerson when he/she is acctually successfully arrived. In elevator {self.index} and person {person.index}.")
        self.requests.remove(person)
        if (person in self.receivedPersons):
            self.receivedPersons.remove(person)
        person.currentFloor = self.currentFloor
        person.isInElevator = False
        person.fromFloor = floor
        person.targetElevator = -1

    def receivePerson(self, timestamp: float, person: Person):
        if (timestamp < person.arriveTime):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Operation too fast in operation: receivePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != -1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: receivePerson in elevator {self.index} and person {person.index}.")
        if (person.targetElevator != -1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Re-Receive: receivePerson in elevator {self.index} and person {person.index}.")
        person.targetElevator = self.index
        self.receivedPersons.append(person)

    def beginSche(self, timestamp: float):
        if (self.inSche != 0):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: beginSche in elevator {self.index} when it is inSche.")
        self.inSche = 1
        self.acceptedSche = 0
        self.moveInterval = self.scheSpeed
        self.moveBeforeBeginSche = 0
        self.openInterval = 1.0
        for person in self.receivedPersons:
            if person not in self.requests:
                person.targetElevator = -1
        self.receivedPersons.clear()

    def endSche(self, timestamp: float):
        if (self.inSche != 1):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: endSche in elevator {self.index} when it is not inSche.")
        if (timestamp - self.acceptScheTime > 6.00001):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Sche time too long in elevator {self.index}.")
        self.inSche = 0
        self.moveInterval = 0.4
        self.openInterval = 0.4

    def acceptSche(self, timestamp: float, speed: float, scheFloor: int):
        if (not (speed == 0.2 or speed == 0.3 or speed == 0.4 or speed == 0.5)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid speed in operation: acceptSche in elevator {self.index}.")
        if (not (-1 <= scheFloor and scheFloor <= 5)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid scheFloor in operation: acceptSche in elevator {self.index}.")
        self.scheSpeed = speed
        self.acceptedSche = 1
        self.acceptScheTime = timestamp
        self.scheFloor = scheFloor
