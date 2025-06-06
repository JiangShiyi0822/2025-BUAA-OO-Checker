from Elevator import Elevator

class TwinElevator:
    topElevator: Elevator 
    bottomElevator: Elevator

    def __init__(self, topElevator: Elevator, bottomElevator: Elevator):
        self.topElevator = topElevator
        self.bottomElevator = bottomElevator
    
    def checkElevatorHit(self):
        if(self.topElevator.currentFloor == self.bottomElevator.currentFloor):
            raise Exception(f"Both elevators {self.topElevator.index} and {self.bottomElevator.index} are on the same floor!")