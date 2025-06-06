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

    currentFloor: int
    requests: list[Person]
    state: ElevatorState
    timestamp: float

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
        self.currentFloor = self.initFloor
        self.requests = []
        self.state = ElevatorState.CLOSE
        self.timestamp = -1000000000
    
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
        self.state = ElevatorState.OPEN
        self.timestamp = timestamp
    
    def move(self, timestamp: float, targetFloor: int):
        if (self.state != ElevatorState.CLOSE):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Invalid operation: move in elevator {self.index}.")
        if (not (self.minFloor <= targetFloor and targetFloor <= self.maxFloor)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor out of bound in operation: move in elevator {self.index}.")
        if (targetFloor == self.currentFloor):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is current floor in operation: move in elevator {self.index}.")
        if (not (targetFloor == self.currentFloor + 1 or targetFloor == self.currentFloor - 1)):
            raise Exception(f"selfTime {self.timestamp} inputTime {timestamp} Target Floor is too far in operation: move in elevator {self.index}.")
        self.currentFloor = targetFloor
        self.timestamp = timestamp
    
    def addPerson(self, timestamp: float, person: Person, floor: int):
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
    
    def removePerson(self, timestamp: float, person: Person, floor: int):
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
        self.requests.remove(person)
        person.currentFloor = self.currentFloor
        person.isInElevator = False
    