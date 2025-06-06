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
    relations_data: list[list[int]] 

    def __init__(self, personCount: int, ids: list[int], names: list[str], ages: list[int], 
                 relations_data: list[list[int]]):
        self.personCount = personCount
        if len(ids) != personCount or len(names) != personCount or len(ages) != personCount:
            raise ValueError("Mismatch in lengths for LoadNetwork person data.")
        
        expected_relation_lines = personCount - 1 if personCount > 1 else 0
        if len(relations_data) != expected_relation_lines :
            raise ValueError(f"Expected {expected_relation_lines} lines of relation data for {personCount} persons, got {len(relations_data)}")
        
        # Validate structure of relations_data: line k (0-indexed) must have k+1 values
        for k, row in enumerate(relations_data): # k from 0 to personCount-2
            expected_values_in_row = k + 1
            if len(row) != expected_values_in_row: 
                raise ValueError(f"Relation data line {k} (for person {k+2}) expected {expected_values_in_row} values, got {len(row)}")

        self.ids = ids
        self.names = names
        self.ages = ages
        self.relations_data = relations_data

    def __str__(self):
        command_parts = [f"ln {self.personCount}"]
        if self.personCount > 0: 
            command_parts.append(" ".join(map(str, self.ids)))
            command_parts.append(" ".join(self.names))
            command_parts.append(" ".join(map(str, self.ages)))
            for relation_line in self.relations_data: # Should be personCount-1 lines if personCount > 1
                command_parts.append(" ".join(map(str, relation_line)))
        
        return "\n".join(command_parts)


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
    
class OperationAddMessage(Operation):
    messageId: int
    socialValue: int
    type: int
    personId1: int
    personId2: int | None 
    tagId: int | None
    
    def __init__(self, messageId: int, socialValue: int, type: int,  personId1: int, Id2: int):
        self.messageId = messageId
        self.socialValue = socialValue
        self.type = type
        self.personId1 = personId1
        self.personId2 = None
        self.tagId = None
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
    personId2: int | None
    tagId: int | None
    def __init__(self, messageId: int, emojiId: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.emojiId = emojiId
        self.type = type
        self.personId1 = personId1
        self.personId2 = None
        self.tagId = None
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
    personId2: int | None
    tagId: int | None
    def __init__(self, messageId: int, money: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.money = money
        self.type = type
        self.personId1 = personId1
        self.personId2 = None
        self.tagId = None
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
    personId2: int | None
    tagId: int | None
    def __init__(self, messageId: int, articleId: int, type: int, personId1: int, Id2: int):
        self.messageId = messageId
        self.articleId = articleId
        self.type = type
        self.personId1 = personId1
        self.personId2 = None
        self.tagId = None
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
    emojiId: int # Changed from personId
    def __init__(self, emojiId: int): # Changed parameter name
        self.emojiId = emojiId
    def __str__(self):
        return f"qp {self.emojiId}"

class OperationQueryMoney(Operation):
    personId: int
    def __init__(self, personId: int):
        self.personId = personId
    def __str__(self):
        return f"qm {self.personId}"