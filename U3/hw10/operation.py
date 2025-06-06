# Keep operation.py mostly as generated before.
# The __str__ methods define the command format.
# Assumptions about formats (e.g., which IDs are needed for doa, ca, da)
# remain and should be verified against the actual 'std.jar' requirements.

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
        # Ensure name doesn't contain spaces if format is strict
        safe_name = self.name.replace(" ", "_")
        return f"ap {self.id} {safe_name} {self.age}"

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
    personId1: int # Owner
    personId2: int # Person to add
    tagId: int
    def __init__(self, personId1: int, personId2: int, tagId: int):
        self.personId1 = personId1
        self.personId2 = personId2
        self.tagId = tagId
    def __str__(self):
        return f"att {self.personId1} {self.personId2} {self.tagId}"

class OperationDelFromTag(Operation):
    personId1: int # Owner
    personId2: int # Person to remove
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
        # Renamed to qci in original code, assuming that's correct
        return f"qci {self.personId1} {self.personId2}"

class OperationQueryTripleSum(Operation):
    def __init__(self):
        pass
    def __str__(self):
        return f"qts"

class OperationQueryTagAgeVar(Operation):
    personId: int # Tag owner
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
    # relations is list[list[int]] where each inner list is [id, n1, v1, n2, v2, ...]
    relations_data: list[list[int]]

    def __init__(self, personCount: int, ids: list[int], names: list[str], ages: list[int], relations_data: list[list[int]]):
        self.personCount = personCount
        self.ids = ids
        self.names = names
        self.ages = ages
        self.relations_data = relations_data # Store the raw data for __str__

    def __str__(self):
        commandHeader = f"ln {self.personCount}"
        # Ensure names don't contain spaces
        safe_names = [name.replace(" ", "_") for name in self.names]
        commandIds = " ".join(map(str, self.ids))
        commandNames = " ".join(safe_names)
        commandAges = " ".join(map(str, self.ages))
        commandRelations = ""
        for rel_line in self.relations_data:
            commandRelations += " ".join(map(str, rel_line)) + "\n"

        commandRelations = commandRelations.rstrip() # Remove trailing newline
        # Combine all parts with newlines
        return f"{commandHeader}\n{commandIds}\n{commandNames}\n{commandAges}\n{commandRelations}"

# class OperationLoadNetworkLocal(Operation): # Unused in generator
#    pass

class OperationCreateOfficialAccount(Operation):
    personId: int # Owner ID
    accountId: int
    accountName: str
    def __init__(self, personId: int, accountId: int, accountName: str):
        self.personId = personId
        self.accountId = accountId
        self.accountName = accountName
    def __str__(self):
        safe_name = self.accountName.replace(" ", "_")
        return f"coa {self.personId} {self.accountId} {safe_name}"

class OperationDeleteOfficialAccount(Operation):
    # Assumption: Only account ID is needed for the command string 'doa'
    # The generator might still track the owner ID if needed for its logic.
    accountId: int
    personId: int # Store if needed by generator, but maybe not in str()

    def __init__(self, accountId: int, personId: int): # Removed personId from constructor here
        self.accountId = accountId
        self.personId = personId

    def __str__(self):
        # Format based on common practice, adjust if spec differs
        return f"doa {self.personId} {self.accountId}"

class OperationContributeArticle(Operation):
    # Assumption: 'ca' command format is 'ca personId accountId articleId'
    # Article Name might be just for generator internal use.
    personId: int # Contributor ID
    accountId: int
    articleId: int
    # articleName: str # Store if needed by generator, but maybe not in str()

    def __init__(self, personId: int, accountId: int, articleId: int): # Removed articleName
        self.personId = personId
        self.accountId = accountId
        self.articleId = articleId
        # self.articleName = articleName

    def __str__(self):
        return f"ca {self.personId} {self.accountId} {self.articleId}"

class OperationDeleteArticle(Operation):
    # Assumption: 'da' command format is 'da personId accountId articleId'
    # where personId is likely the owner of the account.
    personId: int # Deleter ID (likely owner)
    accountId: int
    articleId: int
    def __init__(self, personId: int, accountId: int, articleId: int):
        self.personId = personId
        self.accountId = accountId
        self.articleId = articleId
    def __str__(self):
        return f"da {self.personId} {self.accountId} {self.articleId}"

class OperationFollowOfficialAccount(Operation):
    personId: int # Follower
    accountId: int
    def __init__(self, personId: int, accountId: int):
        self.personId = personId
        self.accountId = accountId
    def __str__(self):
        return f"foa {self.personId} {self.accountId}"

class OperationQueryShortestPath(Operation):
    personId1: int
    personId2: int
    def __init__(self, personId1: int, personId2: int):
        self.personId1 = personId1
        self.personId2 = personId2
    def __str__(self):
        return f"qsp {self.personId1} {self.personId2}"

class OperationQueryBestContributor(Operation):
    accountId: int
    def __init__(self, accountId: int):
        self.accountId = accountId
    def __str__(self):
        return f"qbc {self.accountId}"

class OperationQueryReceivedArticles(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qra {self.personId}"

class OperationQueryTagValueSum(Operation):
    personId: int # Tag owner
    tagId: int
    def __init__(self, personId: int, tagId: int):
        self.personId = personId
        self.tagId = tagId
    def __str__(self):
        return f"qtvs {self.personId} {self.tagId}"

class OperationQueryCoupleSum(Operation):
    def __init__(self):
        pass
    def __str__(self):
        return f"qcs"

# Example usage - check string formats
if __name__ == "__main__":
    print("--- Operation String Format Examples ---")
    print(OperationAddPerson(1, "Alice Smith", 20)) # ap 1 Alice_Smith 20
    print(OperationAddRelation(1, 2, 50)) # ar 1 2 50
    print(OperationModifyRelation(1, 2, -10)) # mr 1 2 -10
    print(OperationAddTag(1, 101)) # at 1 101
    print(OperationDelTag(1, 101)) # dt 1 101
    print(OperationAddToTag(1, 2, 101)) # att 1 2 101
    print(OperationDelFromTag(1, 2, 101)) # dft 1 2 101
    print(OperationQueryValue(1, 2)) # qv 1 2
    print(OperationQueryCircle(1, 2)) # qci 1 2
    print(OperationQueryTripleSum()) # qts
    print(OperationQueryTagAgeVar(1, 101)) # qtav 1 101
    print(OperationQueryBestAcquaintance(1)) # qba 1
    # Example ln data format: [[1], [2, 3, 50], [3, 1, 20, 2, 50]]
    # Note: Generator needs to create this format for OperationLoadNetwork
    ln_op = OperationLoadNetwork(3, [1, 2, 3], ["A", "B C", "D"], [20, 30, 40],
                             [[1], [2, 3, 50], [3, 1, 20, 2, 50]])
    print(ln_op)
    # Expected:
    # ln 3
    # 1 2 3
    # A B_C D
    # 20 30 40
    # 1
    # 2 3 50
    # 3 1 20 2 50
    print(OperationCreateOfficialAccount(1, 1001, "Official Account")) # coa 1 1001 Official_Account
    print(OperationDeleteOfficialAccount(1001)) # doa 1001
    print(OperationContributeArticle(2, 1001, 2001)) # ca 2 1001 2001
    print(OperationDeleteArticle(1, 1001, 2001)) # da 1 1001 2001
    print(OperationFollowOfficialAccount(3, 1001)) # foa 3 1001
    print(OperationQueryShortestPath(1, 3)) # qsp 1 3
    print(OperationQueryBestContributor(1001)) # qbc 1001
    print(OperationQueryReceivedArticles(3)) # qra 3
    print(OperationQueryTagValueSum(1, 101)) # qtvs 1 101
    print(OperationQueryCoupleSum()) # qcs
    print("--------------------------------------")