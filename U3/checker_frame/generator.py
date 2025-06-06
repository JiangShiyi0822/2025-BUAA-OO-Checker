import random

from operation import *
from objects import *

class Generator:
    network : Network
    weights : dict[Operation, float]
    operations : list[Operation]

    MAX_STRING_LEN = 10
    MIN_ID = -1000
    MAX_ID = 1000
    MIN_AGE = 1
    MAX_AGE = 200
    MIN_VALUE = 1
    MAX_VALUE = 200
    MIN_M_VAL = -200
    MAX_M_VAL = 200
    MIN_SOCIAL_VALUE = -1000
    MAX_SOCIAL_VALUE = 1000
    MIN_MONEY = 0
    MAX_MONEY = 200

    DEFAULT_ADD_PERSON_WEIGHT = 1
    DEFAULT_ADD_RELATION_WEIGHT = 1
    DEFAULT_MODIFY_RELATION_WEIGHT = 1
    DEFAULT_ADD_TAG_WEIGHT = 1
    DEFAULT_DEL_TAG_WEIGHT = 1
    DEFAULT_ADD_TO_TAG_WEIGHT = 1
    DEFAULT_DEL_FROM_TAG_WEIGHT = 1
    DEFAULT_QUERY_VALUE_WEIGHT = 1
    DEFAULT_QUERY_CIRCLE_WEIGHT = 1
    DEFAULT_QUERY_TRIPLE_SUM_WEIGHT = 1
    DEFAULT_QUERY_TAG_AGE_VAR_WEIGHT = 1
    DEFAULT_QUERY_BEST_ACQUAINTANCE_WEIGHT = 1
    DEFAULT_CREATE_OFFICIAL_ACCOUNT_WEIGHT = 1
    DEFAULT_DELETE_OFFICIAL_ACCOUNT_WEIGHT = 1
    DEFAULT_CONTRIBUTE_ARTICLE_WEIGHT = 1
    DEFAULT_DELETE_ARTICLE_WEIGHT = 1
    DEFAULT_FOLLOW_OFFICIAL_ACCOUNT_WEIGHT = 1
    DEFAULT_QUERY_SHORTEST_PATH_WEIGHT = 1
    DEFAULT_QUERY_BEST_CONTRIBUTOR_WEIGHT = 1
    DEAFULT_QUERY_RECEIVED_ARTICLES_WEIGHT = 1
    DEFAULT_QUERY_TAG_VALUE_SUM_WEIGHT = 1
    DEFAULT_QUERY_COUPLE_SUM_WEIGHT = 1
    DEFAULT_LOAD_NETWORK_WEIGHT = 0
    DEAFULT_ADD_MESSAGE_WEIGHT = 1
    DEAFULT_ADD_EMOJI_MESSAGE_WEIGHT = 1
    DEAFULT_ADD_RED_ENVELOPE_MESSAGE_WEIGHT = 1
    DEAFULT_ADD_FORWARD_MESSAGE_WEIGHT = 1
    DEAFULT_SEND_MESSAGE_WEIGHT = 1
    DEAFULT_STORE_EMOJI_ID_WEIGHT = 1
    DEAFULT_DELETE_COLD_EMOJI_WEIGHT = 1
    DEFAULT_QUERY_SOCIAL_VALUE_WEIGHT = 1
    DEFAULT_QUERY_RECEIVED_MESSAGES_WEIGHT = 1
    DEFAULT_QUERY_POPULARITY_WEIGHT = 1
    DEFAULT_QUERY_MONEY_WEIGHT = 1

    def __init__(self):        
        self.weights = {
            OperationAddPerson: self.DEFAULT_ADD_PERSON_WEIGHT,
            OperationAddRelation: self.DEFAULT_ADD_RELATION_WEIGHT,
            OperationModifyRelation: self.DEFAULT_MODIFY_RELATION_WEIGHT,
            OperationAddTag: self.DEFAULT_ADD_TAG_WEIGHT,
            OperationDelTag: self.DEFAULT_DEL_TAG_WEIGHT,
            OperationAddToTag: self.DEFAULT_ADD_TO_TAG_WEIGHT,
            OperationDelFromTag: self.DEFAULT_DEL_FROM_TAG_WEIGHT,
            OperationQueryValue: self.DEFAULT_QUERY_VALUE_WEIGHT,
            OperationQueryCircle: self.DEFAULT_QUERY_CIRCLE_WEIGHT,
            OperationQueryTripleSum: self.DEFAULT_QUERY_TRIPLE_SUM_WEIGHT,
            OperationQueryTagAgeVar: self.DEFAULT_QUERY_TAG_AGE_VAR_WEIGHT,
            OperationQueryBestAcquaintance: self.DEFAULT_QUERY_BEST_ACQUAINTANCE_WEIGHT,
            OperationCreateOfficialAccount: self.DEFAULT_CREATE_OFFICIAL_ACCOUNT_WEIGHT,
            OperationDeleteOfficialAccount: self.DEFAULT_DELETE_OFFICIAL_ACCOUNT_WEIGHT,
            OperationContributeArticle: self.DEFAULT_CONTRIBUTE_ARTICLE_WEIGHT,
            OperationDeleteArticle: self.DEFAULT_DELETE_ARTICLE_WEIGHT,
            OperationFollowOfficialAccount: self.DEFAULT_FOLLOW_OFFICIAL_ACCOUNT_WEIGHT,
            OperationQueryShortestPath: self.DEFAULT_QUERY_SHORTEST_PATH_WEIGHT,
            OperationQueryBestContributor: self.DEFAULT_QUERY_BEST_CONTRIBUTOR_WEIGHT,
            OperationQueryReceivedArticles: self.DEAFULT_QUERY_RECEIVED_ARTICLES_WEIGHT,
            OperationQueryTagValueSum: self.DEFAULT_QUERY_TAG_VALUE_SUM_WEIGHT,
            OperationQueryCoupleSum: self.DEFAULT_QUERY_COUPLE_SUM_WEIGHT,
            OperationLoadNetwork: self.DEFAULT_LOAD_NETWORK_WEIGHT,
            OperationAddMessage: self.DEAFULT_ADD_MESSAGE_WEIGHT,
            OperationAddEmojiMessage: self.DEAFULT_ADD_EMOJI_MESSAGE_WEIGHT,
            OperationAddRedEnvelopeMessage: self.DEAFULT_ADD_RED_ENVELOPE_MESSAGE_WEIGHT,
            OperationAddForwardMessage: self.DEAFULT_ADD_FORWARD_MESSAGE_WEIGHT,
            OperationSendMessage: self.DEAFULT_SEND_MESSAGE_WEIGHT,
            OperationStoreEmojiId: self.DEAFULT_STORE_EMOJI_ID_WEIGHT,
            OperationDeleteColdEmoji: self.DEAFULT_DELETE_COLD_EMOJI_WEIGHT,
            OperationQuerySocialValue: self.DEFAULT_QUERY_SOCIAL_VALUE_WEIGHT,
            OperationQueryReceivedMessages: self.DEFAULT_QUERY_RECEIVED_MESSAGES_WEIGHT,
            OperationQueryPopularity: self.DEFAULT_QUERY_POPULARITY_WEIGHT,
            OperationQueryMoney: self.DEFAULT_QUERY_MONEY_WEIGHT
        }
        self.reset()

    def reset(self):
        self.network = Network()
        self.operations = []

    def get_result(self) -> list[str]:
        return [str(operation) for operation in self.operations]

    def add_operations(self, num_operations: int):
        for i in range(num_operations):
            self.add_operation()

    def add_operation_add_person(self, new_person_percentage: float = 0.9):
        operation : OperationAddPerson = None
        NEW_PERSON = 0
        RANDOM = 1
        choice = random.choices([NEW_PERSON, RANDOM], weights=[new_person_percentage, 1-new_person_percentage])[0]
        if (choice == NEW_PERSON):
            pass # TODO: generate a new person. if impossible, generate a person that already exists
        else:
            pass # TODO: Generate a person that already exists
        self.operations.append(operation)

    def add_operation_add_relation(self, new_relation_percentage: float = 0.9):
        operation : OperationAddRelation = None
        NEW_RELATION = 0
        RANDOM = 1
        choice = random.choices([NEW_RELATION, RANDOM], weights=[new_relation_percentage, 1-new_relation_percentage])[0]
        if (choice == NEW_RELATION):
            pass # TODO: generate a new relation. if impossible, generate a relation that already exists
        else:
            pass # TODO: generate a relation that already exists
        self.operations.append(operation)
    
    def add_operation_modify_relation(self, modify_value_percentage: float = 0.4, 
                                      remove_relation_percentage: float = 0.4, 
                                      only_person_exist_percentage: float = 0.1):
        operation : OperationModifyRelation = None
        MODIFY_VALUE = 0
        REMOVE_RELATION = 1
        ONLY_PERSON_EXIST = 2
        RANDOM = 3
        choice = random.choices([MODIFY_VALUE, REMOVE_RELATION, ONLY_PERSON_EXIST, RANDOM], weights=[modify_value_percentage, remove_relation_percentage, only_person_exist_percentage, 1-modify_value_percentage-remove_relation_percentage-only_person_exist_percentage])[0]
        if (choice == MODIFY_VALUE):
            pass # TODO: modify relation value, if impossible, modify random relation
        elif (choice == REMOVE_RELATION):   
            pass # TODO: remove relation, if impossible, remove random relation
        elif (choice == ONLY_PERSON_EXIST):
            pass # TODO: try to modify relation unexist but person exist, if impossible, modify a random relation
        else:
            pass # TODO: modify a random relation
        self.operations.append(operation)

    def add_operation_add_tag(self, valid_percentage: float = 0.9):
        operation : OperationAddTag = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: add a new tag to an existing person, if impossible, add a tag that already exists
        else:
            pass # TODO: add a tag that already exists to an existing person
        self.operations.append(operation)
    
    def add_operation_del_tag(self, valid_percentage: float = 0.85, tag_unexist_percentage: float = 0.05,
                               person_unexist_percentage: float = 0.05):
        operation : OperationDelTag = None
        VALID = 0
        TAG_UNEXIST = 1
        PERSON_UNEXIST = 2
        RANDOM = 3
        choice = random.choices([VALID, TAG_UNEXIST, PERSON_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, person_unexist_percentage, 1-valid_percentage-tag_unexist_percentage-person_unexist_percentage])[0]
        if (choice == VALID):
            pass # TODO: delete a existing tag from an existing person, if impossible, delete a random tag  
        elif (choice == TAG_UNEXIST):
            pass # TODO: delete a tag that doesn't exist, if impossible, delete a random tag
        elif (choice == PERSON_UNEXIST):
            pass # TODO: delete a tag from a person that doesn't exist, if impossible, delete a random tag
        else:
            pass # TODO: delete a random tag
        self.operations.append(operation)

    def add_operation_add_to_tag(self, valid_percentage: float = 0.8, tag_unexist_percentage: float = 0.1):
        operation : OperationAddToTag = None
        VALID = 0
        TAG_UNEXIST = 1
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]
        if (choice == VALID):
            pass # TODO: add person to an existing tag, if impossible, add a random person to a random tag
        elif (choice == TAG_UNEXIST):
            pass # TODO: add person to a tag that doesn't exist, if impossible, add a random person to a random tag
        else:
            pass # TODO: add a random person to a random tag
        self.operations.append(operation)

    def add_operation_del_from_tag(self, valid_percentage: float = 0.8, tag_unexist_percentage: float = 0.1):
        operation : OperationDelFromTag = None
        VALID = 0
        TAG_UNEXIST = 1
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]
        if (choice == VALID):
            pass # TODO: remove an existing person from an existing tag, if impossible, remove a random person from a random tag
        elif (choice == TAG_UNEXIST):
            pass # TODO: remove a person from a tag that doesn't exist, if impossible, remove a random person from a random tag
        else:
            pass # TODO: remove a random person from a random tag
        self.operations.append(operation)
    
    def add_operation_query_value(self, valid_percentage: float = 0.9):
        operation : OperationQueryValue = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query value of an existing relation , if impossible, query value of an random relation
        else:
            pass # TODO: query value of an random relation
        self.operations.append(operation)

    def add_operation_query_circle(self, valid_percentage: float = 0.9):
        operation : OperationQueryCircle = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query circle of two existing persons, if impossible, query circle of two random persons
        else:
            pass # TODO: query circle of two random persons
        self.operations.append(operation)

    def add_operation_query_triple_sum(self):
        return OperationQueryTripleSum()

    def add_operation_query_tag_age_var(self, valid_percentage: float = 0.9):
        operation : OperationQueryTagAgeVar = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query tag age variance of an existing tag, if impossible, query tag age variance of a tag that doesn't exist
        else:
            pass # TODO: query tag age variance of a tag that doesn't exist
        self.operations.append(operation)
    
    def add_operation_query_best_acquaintance(self, valid_percentage: float = 0.9):
        operation : OperationQueryBestAcquaintance = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query best acquaintance of an existing person, if impossible, query best acquaintance of a person that doesn't exist
        else:
            pass # TODO: query best acquaintance of a person that doesn't exist
        self.operations.append(operation)
    
    def add_operation_load_network(self):
        # TODO: generate network args
        return OperationLoadNetwork()
    
    def add_operation_create_official_account(self, valid_percentage: float = 0.9):
        operation : OperationCreateOfficialAccount = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: create a new official account. if impossible, create a official account that already exists
        else:
            pass # TODO: create a official account that already exists
        self.operations.append(operation)

    def add_operation_delete_official_account(self, valid_percentage: float = 0.9):
        operation : OperationDeleteOfficialAccount = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: delete an existing official account, if impossible, delete a random official account
        else:
            pass # TODO: delete a random official account
        self.operations.append(operation)

    def add_operation_contribute_article(self, valid_percentage: float = 0.8, account_unexist_percentage: float = 0.1):
        operation : OperationContributeArticle = None
        VALID = 0
        ACCOUNT_UNEXIST = 1
        RANDOM = 2
        choice = random.choices([VALID, ACCOUNT_UNEXIST, RANDOM], weights=[valid_percentage, account_unexist_percentage, 1-valid_percentage-account_unexist_percentage])[0]
        if (choice == VALID):
            pass # TODO: contribute an article to an existing official account, if impossible, contribute a random article to a random official account
        elif (choice == ACCOUNT_UNEXIST):
            pass # TODO: contribute an article to an official account that doesn't exist, if impossible, contribute a random article to a random official account
        else:
            pass # TODO: contribute a random article to a random official account
        self.operations.append(operation)

    def add_operation_delete_article(self, valid_percentage: float = 0.8, article_unexist_percentage: float = 0.1):
        operation : OperationDeleteArticle = None
        VALID = 0
        ARTICLE_UNEXIST = 1
        RANDOM = 2
        choice = random.choices([VALID, ARTICLE_UNEXIST, RANDOM], weights=[valid_percentage, article_unexist_percentage, 1-valid_percentage-article_unexist_percentage])[0]
        if (choice == VALID):
            pass # TODO: delete an existing article from an existing official account, if impossible, delete a random article from a random official account
        elif (choice == ARTICLE_UNEXIST):
            pass # TODO: delete an article that doesn't exist, if impossible, delete a random article from a random official account
        else:
            pass # TODO: delete a random article from a random official account
        self.operations.append(operation)

    def add_operation_follow_official_account(self, valid_percentage: float = 0.9):
        operation : OperationFollowOfficialAccount = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: follow an existing official account, if impossible, follow a random official account
        else:
            pass # TODO: follow a random official account
        self.operations.append(operation)

    def add_operation_query_shortest_path(self, vaild_percentage: float = 0.9):
        operation : OperationQueryShortestPath = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[vaild_percentage, 1-vaild_percentage])[0]
        if (choice == VALID):
            pass # TODO: query shortest path of two existing persons, if impossible, query shortest path of two random persons
        else:
            pass # TODO: query shortest path of two random persons
        self.operations.append(operation)

    def add_operation_query_best_contributor(self, valid_percentage: float = 0.9):
        operation : OperationQueryBestContributor = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query best contributor of an existing official account, if impossible, query best contributor of a random official account
        else:
            pass # TODO: query best contributor of a random official account
        self.operations.append(operation)

    def add_operation_query_received_articles(self, valid_percentage: float = 0.9):
        operation : OperationQueryReceivedArticles = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query received articles of an existing person, if impossible, query received articles of a random person
        else:
            pass # TODO: query received articles of a random person
        self.operations.append(operation)

    def add_operation_query_tag_value_sum(self,valid_percentage: float = 0.9):
        operation : OperationQueryTagValueSum = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query tag value sum of an existing person and tag, if impossible, query tag value sum of a random person and tag
        else:
            pass # TODO: query tag value sum of a random person and tag
        self.operations.append(operation)

    def add_operation_query_couple_sum(self):
        operation : OperationQueryCoupleSum = None
        pass # TODO: query couple sum
        self.operations.append(operation)        

    def add_operation_add_message(self, tag_percentage: float = 0.5):
        operation : OperationAddMessage = None
        toPerson = 0
        toTag = 1
        choice = random.choices([toPerson, toTag], weights=[1 - tag_percentage, tag_percentage])[0]
        if (choice == toPerson):
            pass # TODO: add a message to an existing person1, and the message is sent to his acquaintance person2, if impossible, add a message to a random person1 and the message is sent to a random person2
        else:
            pass # TODO: add a message to an existing person1, and the choose a tag of his, if impossible, add a message to a random person1 and the choose a tag of his
        self.operations.append(operation)

    def add_operation_add_emoji_message(self, tag_percentage: float = 0.5):
        operation : OperationAddEmojiMessage = None
        toPerson = 0
        toTag = 1
        choice = random.choices([toPerson, toTag], weights=[1 - tag_percentage, tag_percentage])[0]
        if (choice == toPerson):
            pass # TODO: add a emoji message to an existing person1, and the message is sent to his acquaintance person2, if impossible, add a emoji message to a random person1 and the message is sent to a random person2
        else:   
            pass # TODO: add a emoji message to an existing person1, and the choose a tag of his, if impossible, add a emoji message to a random person1 and the choose a tag of his
        self.operations.append(operation)
    
    def add_operation_add_red_envelope_message(self, tag_percentage: float = 0.5):
        operation : OperationAddRedEnvelopeMessage = None
        toPerson = 0
        toTag = 1
        choice = random.choices([toPerson, toTag], weights=[1 - tag_percentage, tag_percentage])[0]
        if (choice == toPerson):
            pass # TODO: add a red envelope message to an existing person1, and the message is sent to an acquaintance person2, if impossible, add a red envelope message to a random person1 and the message is sent to a random person2
        else:
            pass # TODO: add a red envelope message to an existing person1, and the choose a tag of his, if impossible, add a red envelope message to a random person1 and the choose a tag of his
        self.operations.append(operation)

    def add_operation_add_forward_message(self, tag_percentage: float = 0.5):
        operation : OperationAddForwardMessage = None
        toPerson = 0
        toTag = 1
        choice = random.choices([toPerson, toTag], weights=[1 - tag_percentage, tag_percentage])[0]
        if (choice == toPerson):
            pass # TODO: add a forward message to an existing person1, and the message is sent to his acquaintance person2, if impossible, add a forward message to a random person1 and the message is sent to a random person2
        else:   
            pass # TODO: add a forward message to an existing person1, and the choose a tag of his, if impossible, add a forward message to a random person1 and the choose a tag of his
        self.operations.append(operation)

    def add_operation_send_message(self, valid_percentage: float = 0.95):
        operation : OperationSendMessage = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: send an existing message
        else:
            pass # TODO: send a random message        
        self.operations.append(operation)

    def add_operation_store_emoji_id(self, valid_percentage: float = 0.9):
        operation : OperationStoreEmojiId = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: store an existing emoji id, if impossible, store a random emoji id
        else:
            pass # TODO: store a random emoji id
        self.operations.append(operation)

    def add_operation_delete_cold_emoji(self, valid_percentage: float = 0.9):
        operation : OperationDeleteColdEmoji = None
        pass # TODO: delete a cold emoji with random limit
        self.operations.append(operation)

    def add_operation_query_social_value(self, valid_percentage: float = 0.9):
        operation : OperationQuerySocialValue = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query social value of an existing person, if impossible, query social value of a random person
        else:   
            pass # TODO: query social value of a random person
        self.operations.append(operation)

    def add_operation_query_received_messages(self, valid_percentage: float = 0.9):
        operation : OperationQueryReceivedMessages = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query received messages of an existing person, if impossible, query received messages of a random person
        else:
            pass # TODO: query received messages of a random person
        self.operations.append(operation)

    def add_operation_query_popularity(self, valid_percentage: float = 0.9):
        operation : OperationQueryPopularity = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query popularity of an existing emojiId, if impossible, query popularity of a random emojiId
        else:
            pass # TODO: query popularity of a random emojiId
        self.operations.append(operation)

    def add_operation_query_money(self, valid_percentage: float = 0.9):
        operation : OperationQueryMoney = None
        VALID = 0
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        if (choice == VALID):
            pass # TODO: query money of an existing person, if impossible, query money of a random person
        else:
            pass # TODO: query money of a random person
        self.operations.append(operation)    

    def add_operation(self):
        operation_type = random.choices(list(self.weights.keys()), weights=list(self.weights.values()))[0]
        if (operation_type == OperationAddPerson):
            self.add_operation_add_person()
        elif (operation_type == OperationAddRelation):
            self.add_operation_add_relation()
        elif (operation_type == OperationModifyRelation):
            self.add_operation_modify_relation()
        elif (operation_type == OperationAddTag):
            self.add_operation_add_tag()
        elif (operation_type == OperationDelTag):
            self.add_operation_del_tag()
        elif (operation_type == OperationAddToTag):
            self.add_operation_add_to_tag()
        elif (operation_type == OperationDelFromTag):
            self.add_operation_del_from_tag()
        elif (operation_type == OperationQueryValue):
            self.add_operation_query_value()
        elif (operation_type == OperationQueryCircle):
            self.add_operation_query_circle()
        elif (operation_type == OperationQueryTripleSum):
            self.add_operation_query_triple_sum()
        elif (operation_type == OperationQueryTagAgeVar):
            self.add_operation_query_tag_age_var()
        elif (operation_type == OperationQueryBestAcquaintance):
            self.add_operation_query_best_acquaintance()
        elif (operation_type == OperationLoadNetwork):
            self.add_operation_load_network()
        elif (operation_type == OperationCreateOfficialAccount):
            self.add_operation_create_official_account()
        elif (operation_type == OperationDeleteOfficialAccount):
            self.add_operation_delete_official_account()
        elif (operation_type == OperationContributeArticle):
            self.add_operation_contribute_article()
        elif (operation_type == OperationDeleteArticle):
            self.add_operation_delete_article()
        elif (operation_type == OperationFollowOfficialAccount):    
            self.add_operation_follow_official_account()
        elif (operation_type == OperationQueryShortestPath):
            self.add_operation_query_shortest_path()
        elif (operation_type == OperationQueryBestContributor): 
            self.add_operation_query_best_contributor()
        elif (operation_type == OperationQueryReceivedArticles):
            self.add_operation_query_received_articles()
        elif (operation_type == OperationQueryTagValueSum):
            self.add_operation_query_tag_value_sum()
        elif (operation_type == OperationQueryCoupleSum):
            self.add_operation_query_couple_sum()
        elif (operation_type == OperationAddMessage):
            self.add_operation_add_message()
        elif (operation_type == OperationAddEmojiMessage):
            self.add_operation_add_emoji_message()
        elif (operation_type == OperationAddRedEnvelopeMessage):
            self.add_operation_add_red_envelope_message()
        elif (operation_type == OperationAddForwardMessage):
            self.add_operation_add_forward_message()
        elif (operation_type == OperationSendMessage):
            self.add_operation_send_message()
        elif (operation_type == OperationStoreEmojiId):
            self.add_operation_store_emoji_id()
        elif (operation_type == OperationDeleteColdEmoji):
            self.add_operation_delete_cold_emoji()
        elif (operation_type == OperationQuerySocialValue):
            self.add_operation_query_social_value()
        elif (operation_type == OperationQueryReceivedMessages):
            self.add_operation_query_received_messages()
        elif (operation_type == OperationQueryPopularity):
            self.add_operation_query_popularity()
        elif (operation_type == OperationQueryMoney):
            self.add_operation_query_money()
        else:
            raise ValueError("Invalid operation type")

    @staticmethod
    def random_id(min_id : int = MIN_ID, max_id : int = MAX_ID) -> int:
        return random.randint(min_id, max_id)

    @staticmethod
    def random_name() -> str:
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, Generator.MAX_STRING_LEN)))

    @staticmethod
    def random_age(min_age : int = MIN_AGE, max_age : int = MAX_AGE) -> int:
        return random.randint(min_age, max_age)
    
    @staticmethod
    def random_value(min_value : int = MIN_VALUE, max_value : int = MAX_VALUE) -> int:
        return random.randint(min_value, max_value)
    
    @staticmethod
    def random_m_val(min_m_val : int = MIN_M_VAL, max_m_val : int = MAX_M_VAL) -> int:
        return random.randint(min_m_val, max_m_val)

    @staticmethod
    def random_social_value(min_social_value : int = MIN_SOCIAL_VALUE, max_social_value : int = MAX_SOCIAL_VALUE) -> int:
        return random.randint(min_social_value, max_social_value)

    @staticmethod
    def random_money(min_money : int = MIN_MONEY, max_money : int = MAX_MONEY) -> int:
        return random.randint(min_money, max_money)
