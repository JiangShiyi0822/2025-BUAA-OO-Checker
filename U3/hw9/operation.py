class Operation:
    def __str__(self):
        return "<BaseOperation>"

class OperationAddPerson(Operation):
    id: int
    name: str
    age: int
    def __init__(self, id: int, name: str, age: int):
        self.id = id
        self.name = name
        self.age = age
    def __str__(self):
        return f"ap {self.id} {self.name} {self.age}"

class OperationAddRelation(Operation):
    personId1: int
    personId2: int
    value: int
    def __init__(self, personId1: int, personId2: int, value: int):
        self.personId1 = personId1
        self.personId2 = personId2
        self.value = value
    def __str__(self):
        return f"ar {self.personId1} {self.personId2} {self.value}"

class OperationModifyRelation(Operation):
    personId1: int
    personId2: int
    modifyValue: int
    def __init__(self, personId1: int, personId2: int, modifyValue: int):
        self.personId1 = personId1
        self.personId2 = personId2
        self.modifyValue = modifyValue
    def __str__(self):
        return f"mr {self.personId1} {self.personId2} {self.modifyValue}"

class OperationAddTag(Operation):
    personId: int
    tagId: int
    def __init__(self, personId: int, tagId: int):
        self.personId = personId
        self.tagId = tagId
    def __str__(self):
        return f"at {self.personId} {self.tagId}"

class OperationDelTag(Operation):
    personId: int
    tagId: int
    def __init__(self, personId: int, tagId: int):
        self.personId = personId
        self.tagId = tagId
    def __str__(self):
        return f"dt {self.personId} {self.tagId}"

class OperationAddToTag(Operation):
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, personId1: int, personId2: int, tagId: int):
        self.personId1 = personId1
        self.personId2 = personId2
        self.tagId = tagId
    def __str__(self):
        return f"att {self.personId1} {self.personId2} {self.tagId}"

class OperationDelFromTag(Operation):
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, personId1: int, personId2: int, tagId: int):
        self.personId1 = personId1
        self.personId2 = personId2
        self.tagId = tagId
    def __str__(self):
        return f"dft {self.personId1} {self.personId2} {self.tagId}"

class OperationQueryValue(Operation):
    personId1: int
    personId2: int
    def __init__(self, personId1: int, personId2: int):
        self.personId1 = personId1
        self.personId2 = personId2
    def __str__(self):
        return f"qv {self.personId1} {self.personId2}"

class OperationQueryCircle(Operation):
    personId1: int
    personId2: int
    def __init__(self, personId1: int, personId2: int):
        self.personId1 = personId1
        self.personId2 = personId2
    def __str__(self):
        return f"qci {self.personId1} {self.personId2}"

class OperationQueryTripleSum(Operation):
    def __init__(self):
        pass
    def __str__(self):
        return f"qts"

class OperationQueryTagAgeVar(Operation):
    personId: int
    tagId: int
    def __init__(self, personId: int, tagId: int):
        self.personId = personId
        self.tagId = tagId
    def __str__(self):
        return f"qtav {self.personId} {self.tagId}"

class OperationQueryBestAcquaintance(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qba {self.personId}"

class OperationLoadNetwork(Operation):
    personCount: int
    ids: list[int]
    names: list[str]
    ages: list[int]
    relations: list[list[int]]
    def __init__(self, personCount: int, ids: list[int], names: list[str], ages: list[int], relations: list[list[int]]):
        self.personCount = personCount
        self.ids = ids
        self.names = names
        self.ages = ages
        self.relations = relations
    def __str__(self):
        commandHeader = f"ln {self.personCount}"
        commandIds = " ".join(map(str, self.ids))
        commandNames = " ".join(self.names)
        commandAges = " ".join(map(str, self.ages))
        commandRelations = ""
        # Corrected relation string generation
        for row in self.relations: # Iterate through rows of the adjacency matrix/list
            commandRelations += " ".join(map(str, row)) + "\n" # Join elements of the row
        commandRelations = commandRelations.rstrip() # Remove trailing newline
        # Assemble the multi-line command string
        return f"{commandHeader}\n{commandIds}\n{commandNames}\n{commandAges}\n{commandRelations}"


class OperationLoadNetworkLocal(Operation):
    # This seems unused in the generator logic, keeping as is.
    pass

if __name__ == "__main__":
    op = OperationAddPerson(1, "Alice", 20)
    print(op)
    op = OperationAddRelation(1, 2, 3)
    print(op)
    op = OperationModifyRelation(1, 2, 4)
    print(op)
    op = OperationAddTag(1, 2)
    print(op)
    op = OperationDelTag(1, 2)
    print(op)
    op = OperationAddToTag(1, 2, 3)
    print(op)
    op = OperationDelFromTag(1, 2, 3)
    print(op)
    op = OperationQueryValue(1, 2)
    print(op)
    op = OperationQueryCircle(1, 2)
    print(op)
    op = OperationQueryTripleSum()
    print(op)
    op = OperationQueryTagAgeVar(1, 2)
    print(op)
    op = OperationQueryBestAcquaintance(1)
    print(op)
    # Example with a more typical relation representation (adjacency list style maybe?)
    # The original example `[[1], [2, 3], [3, 1, 5]]` is ambiguous.
    # Assuming it's meant to be like an adjacency matrix for 3 people:
    # rels = [[0, 1, 0], [1, 0, 1], [0, 1, 0]] # Example: Person 1 connected to 2, 2 to 1&3, 3 to 2
    rels = [[1, 50, 0], [50, 1, 30], [0, 30, 1]] # Example with values (diagonal often ignored)
    op = OperationLoadNetwork(3, [10, 20, 30], ["Alice", "Bob", "Charlie"], [20, 30, 40], rels)
    print(op)