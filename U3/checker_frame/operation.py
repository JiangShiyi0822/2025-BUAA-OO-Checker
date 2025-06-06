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
        for i in range(len(self.relations)):
            commandRelations += " ".join(map(str, self.relations[i])) + "\n"
        commandRelations = commandRelations.rstrip()
        return f"{commandHeader}\n{commandIds}\n{commandNames}\n{commandAges}\n{commandRelations}"

class OperationLoadNetworkLocal(Operation):
    pass

class OperationCreateOfficialAccount(Operation):
    personId: int
    accountId: int
    accountName: str
    def __init__(self, personId: int, accountId: int, accountName: str):
        self.personId = personId
        self.accountId = accountId
        self.accountName = accountName
    def __str__(self):
        return f"coa {self.personId} {self.accountId} {self.accountName}"

class OperationDeleteOfficialAccount(Operation):
    personId: int
    accountId: int
    def __init__(self, personId: int, accountId: int):
        self.personId = personId
        self.accountId = accountId
    def __str__(self):
        return f"doa {self.personId} {self.accountId}"

class OperationContributeArticle(Operation):
    personId: int
    accountId: int
    articleId: int
    articleName: str
    def __init__(self, personId: int, accountId: int, articleId: int, articleName: str):
        self.personId = personId
        self.accountId = accountId
        self.articleId = articleId
        self.articleName = articleName
    def __str__(self):
        return f"ca {self.personId} {self.accountId} {self.articleId} {self.articleName}"

class OperationDeleteArticle(Operation):
    personId: int
    accountId: int
    articleId: int
    def __init__(self, personId: int, accountId: int, articleId: int):
        self.personId = personId
        self.accountId = accountId
        self.articleId = articleId
    def __str__(self):
        return f"da {self.personId} {self.accountId} {self.articleId}"

class OperationFollowOfficialAccount(Operation):
    personId: int
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
    personId: int
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
    
""" hw11
add_message id(int) social_value(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
add_emoji_message id(int) emoji_id(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
add_red_envelope_message id(int) money(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
add_forward_message id(int) article_id(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
send_message id(int)
store_emoji_id id(int)
delete_cold_emoji limit(int)

query_social_value id(int)
query_received_messages id(int)
query_popularity id(int)
query_money id(int)
"""

class OperationAddMessage(Operation):
    messageId: int
    socialValue: int
    type: int
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, messageId: int, socialValue: int, type: int,  personId1: int, Id2: int):
        self.messageId = messageId
        self.socialValue = socialValue
        self.type = type
        self.personId1 = personId1
        if (type == 0):
            self.personId2 = Id2
        else:
            self.tagId = Id2
    def __str__(self):
        if (self.type == 0):
            return f"am {self.messageId} {self.socialValue} {self.type} {self.personId1} {self.personId2}"
        else:
            return f"am {self.messageId} {self.socialValue} {self.type} {self.personId1} {self.tagId}"

class OperationAddEmojiMessage(Operation):
    messageId: int
    emojiId: int
    type: int
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, messageId: int, emojiId: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.emojiId = emojiId
        self.type = type
        self.personId1 = personId1
        if (type == 0):
            self.personId2 = Id2
        else:
            self.tagId = Id2
    def __str__(self):
        if (self.type == 0):
            return f"aem {self.messageId} {self.emojiId} {self.type} {self.personId1} {self.personId2}"
        else:
            return f"aem {self.messageId} {self.emojiId} {self.type} {self.personId1} {self.tagId}"

class OperationAddRedEnvelopeMessage(Operation):
    messageId: int
    money: int
    type: int
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, messageId: int, money: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.money = money
        self.type = type
        self.personId1 = personId1
        if (type == 0):
            self.personId2 = Id2
        else:
            self.tagId = Id2
    def __str__(self):
        if (self.type == 0):
            return f"arem {self.messageId} {self.money} {self.type} {self.personId1} {self.personId2}"
        else:
            return f"arem {self.messageId} {self.money} {self.type} {self.personId1} {self.tagId}"
        
class OperationAddForwardMessage(Operation):
    messageId: int
    articleId: int
    type: int
    personId1: int
    personId2: int
    tagId: int
    def __init__(self, messageId: int, articleId: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.articleId = articleId
        self.type = type
        self.personId1 = personId1
        if (type == 0):
            self.personId2 = Id2
        else:
            self.tagId = Id2
    def __str__(self):
        if (self.type == 0):
            return f"afm {self.messageId} {self.articleId} {self.type} {self.personId1} {self.personId2}"
        else:
            return f"afm {self.messageId} {self.articleId} {self.type} {self.personId1} {self.tagId}"

class OperationSendMessage(Operation):
    messageId: int
    def __init__(self, messageId: int):
        self.messageId = messageId
    def __str__(self):
        return f"sm {self.messageId}"
    
class OperationStoreEmojiId(Operation):
    emojiId: int
    def __init__(self, emojiId: int):
        self.emojiId = emojiId
    def __str__(self):
        return f"sei {self.emojiId}"
    
class OperationDeleteColdEmoji(Operation):
    limit: int
    def __init__(self, limit: int):
        self.limit = limit
    def __str__(self):
        return f"dce {self.limit}"
    
class OperationQuerySocialValue(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qsv {self.personId}"

class OperationQueryReceivedMessages(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qrm {self.personId}"

class OperationQueryPopularity(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qp {self.personId}"

class OperationQueryMoney(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qm {self.personId}"

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
    op = OperationLoadNetwork(3, [1, 2, 3], ["Alice", "Bob", "Charlie"], [20, 30, 40], [[1], [2, 3], [3, 1, 5]])
    print(op)