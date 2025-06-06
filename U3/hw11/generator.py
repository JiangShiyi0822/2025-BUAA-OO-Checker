import random
import string

from operation import * 
from objects import *

class Generator:
    network : Network
    operations : list[Operation] 
    official_accounts: list[OfficialAccount]
    messages: list[Message] 
    stored_emoji_ids: set[int] 

    _next_person_id: int
    _next_account_id: int
    _next_article_id: int 
    _next_message_id: int
    _next_emoji_id: int 
    
    weights : dict[type[Operation], float]

    # --- Constants for Data Generation ---
    MAX_STRING_LEN = 10
    MIN_ID = 1 
    MAX_ID = 2000 
    MIN_AGE = 1
    MAX_AGE = 150 
    MIN_VALUE = 1 
    MAX_VALUE = 200
    MIN_M_VAL = -200 
    MAX_M_VAL = 200
    MIN_SOCIAL_VALUE = -1000
    MAX_SOCIAL_VALUE = 1000
    MIN_MONEY = 0
    MAX_MONEY = 200
    MIN_EMOJI_ID = 1 
    MAX_EMOJI_ID = 1000 
    MIN_ARTICLE_ID = 1
    MAX_ARTICLE_ID = 1000

    # --- Configurable Parameters for Load Network ---
    LOAD_NETWORK_MIN_PERSONS: int = 100
    LOAD_NETWORK_MAX_PERSONS: int = 300
    LOAD_NETWORK_RELATION_PROBABILITY: float = 0.9 

    DEFAULT_ADD_PERSON_WEIGHT = 2
    DEFAULT_ADD_RELATION_WEIGHT = 2
    DEFAULT_MODIFY_RELATION_WEIGHT = 3
    DEFAULT_ADD_TAG_WEIGHT = 1
    DEFAULT_DEL_TAG_WEIGHT = 1
    DEFAULT_ADD_TO_TAG_WEIGHT = 1
    DEFAULT_DEL_FROM_TAG_WEIGHT = 1
    DEFAULT_QUERY_VALUE_WEIGHT = 1
    DEFAULT_QUERY_CIRCLE_WEIGHT = 3
    DEFAULT_QUERY_TRIPLE_SUM_WEIGHT = 4
    DEFAULT_QUERY_TAG_AGE_VAR_WEIGHT = 2
    DEFAULT_QUERY_BEST_ACQUAINTANCE_WEIGHT = 2
    DEFAULT_CREATE_OFFICIAL_ACCOUNT_WEIGHT = 1
    DEFAULT_DELETE_OFFICIAL_ACCOUNT_WEIGHT = 1
    DEFAULT_CONTRIBUTE_ARTICLE_WEIGHT = 3
    DEFAULT_DELETE_ARTICLE_WEIGHT = 3
    DEFAULT_FOLLOW_OFFICIAL_ACCOUNT_WEIGHT = 2
    DEFAULT_QUERY_SHORTEST_PATH_WEIGHT = 2
    DEFAULT_QUERY_BEST_CONTRIBUTOR_WEIGHT = 3
    DEAFULT_QUERY_RECEIVED_ARTICLES_WEIGHT = 3
    DEFAULT_QUERY_TAG_VALUE_SUM_WEIGHT = 4
    DEFAULT_QUERY_COUPLE_SUM_WEIGHT = 3
    DEFAULT_LOAD_NETWORK_WEIGHT = 0 
    DEAFULT_ADD_MESSAGE_WEIGHT = 3
    DEAFULT_ADD_EMOJI_MESSAGE_WEIGHT = 3
    DEAFULT_ADD_RED_ENVELOPE_MESSAGE_WEIGHT = 1
    DEAFULT_ADD_FORWARD_MESSAGE_WEIGHT = 2
    DEAFULT_SEND_MESSAGE_WEIGHT = 2
    DEAFULT_STORE_EMOJI_ID_WEIGHT = 2
    DEAFULT_DELETE_COLD_EMOJI_WEIGHT = 3
    DEFAULT_QUERY_SOCIAL_VALUE_WEIGHT = 2
    DEFAULT_QUERY_RECEIVED_MESSAGES_WEIGHT = 2
    DEFAULT_QUERY_POPULARITY_WEIGHT = 2 # popularity of emoji
    DEFAULT_QUERY_MONEY_WEIGHT = 1            

    def __init__(self, 
                 load_network_min_persons: int | None = None,
                 load_network_max_persons: int | None = None,
                 load_network_relation_probability: float | None = None):        
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

        if load_network_min_persons is not None:
            if load_network_min_persons >= 0:
                self.LOAD_NETWORK_MIN_PERSONS = load_network_min_persons
            else:
                print(f"Warning: Invalid load_network_min_persons ({load_network_min_persons}). Using default {self.LOAD_NETWORK_MIN_PERSONS}.")
        
        if load_network_max_persons is not None:
            if load_network_max_persons >= self.LOAD_NETWORK_MIN_PERSONS:
                self.LOAD_NETWORK_MAX_PERSONS = load_network_max_persons
            else:
                print(f"Warning: Invalid load_network_max_persons ({load_network_max_persons}) < min_persons. Adjusting max_persons to {self.LOAD_NETWORK_MIN_PERSONS}.")
                self.LOAD_NETWORK_MAX_PERSONS = self.LOAD_NETWORK_MIN_PERSONS
        
        # Ensure min is not greater than max after potential individual adjustments
        if self.LOAD_NETWORK_MIN_PERSONS > self.LOAD_NETWORK_MAX_PERSONS:
            print(f"Warning: Corrected LOAD_NETWORK_MIN_PERSONS ({self.LOAD_NETWORK_MIN_PERSONS}) to match MAX_PERSONS ({self.LOAD_NETWORK_MAX_PERSONS}) as min exceeded max.")
            self.LOAD_NETWORK_MIN_PERSONS = self.LOAD_NETWORK_MAX_PERSONS


        if load_network_relation_probability is not None:
            if 0.0 <= load_network_relation_probability <= 1.0:
                self.LOAD_NETWORK_RELATION_PROBABILITY = load_network_relation_probability
            else:
                print(f"Warning: Invalid load_network_relation_probability ({load_network_relation_probability}). Using default {self.LOAD_NETWORK_RELATION_PROBABILITY}.")

        self.reset_internal_state_and_ops() 

    def reset_internal_state_and_ops(self):
        """Resets network-specific data, ID counters, AND self.operations."""
        self.network = Network()
        self.official_accounts = []
        self.messages = []
        self.stored_emoji_ids = set()
        self._next_person_id = 1
        self._next_account_id = 1
        self._next_article_id = 1
        self._next_message_id = 1
        self._next_emoji_id = 1
        self.operations = [] 

    # ... (ID generation and random entity getters remain the same) ...
    def _get_new_person_id(self) -> int:
        pid = self._next_person_id
        self._next_person_id += 1
        return pid

    def _get_new_account_id(self) -> int:
        aid = self._next_account_id
        self._next_account_id += 1
        return aid
        
    def _get_new_article_id(self) -> int:
        aid = self._next_article_id
        self._next_article_id += 1
        return aid

    def _get_new_message_id(self) -> int:
        mid = self._next_message_id
        self._next_message_id += 1
        return mid
        
    def _get_new_emoji_id_for_sei_aem(self) -> int: 
        eid = self._next_emoji_id
        self._next_emoji_id += 1
        return eid

    def _get_random_existing_person(self) -> Person | None:
        if not self.network.person_list:
            return None
        return random.choice(self.network.person_list)

    def _get_random_existing_person_id(self, default_if_empty=True) -> int:
        person = self._get_random_existing_person()
        if person:
            return person.id
        return self.random_id(min_id=self.MIN_ID, max_id=self.MAX_ID) if default_if_empty else -1 

    def _get_random_pair_of_person_ids(self, must_exist=False, must_be_different=False) -> tuple[int, int]:
        if must_exist and len(self.network.person_list) < (2 if must_be_different else 1):
            return self.random_id(), self.random_id()

        p1_id = self._get_random_existing_person_id() if must_exist else self.random_id()
        p2_id = self._get_random_existing_person_id() if must_exist else self.random_id()

        if must_be_different and p1_id == p2_id:
            if must_exist and len(self.network.person_list) >= 2:
                others = [p for p in self.network.person_list if p.id != p1_id]
                if others:
                    p2_id = random.choice(others).id
                else: 
                    p2_id = self.random_id() 
                    while p2_id == p1_id: p2_id = self.random_id()
            elif not must_exist:
                 p2_id = self.random_id() 
                 while p2_id == p1_id: p2_id = self.random_id()
        return p1_id, p2_id

    def _get_random_existing_tag_for_person(self, person: Person) -> Tag | None:
        if person and person.tag_list:
            return random.choice(person.tag_list)
        return None

    def _get_random_existing_official_account(self) -> OfficialAccount | None:
        if not self.official_accounts:
            return None
        return random.choice(self.official_accounts)

    def _get_random_existing_official_account_id(self, default_if_empty=True) -> int:
        acc = self._get_random_existing_official_account()
        if acc:
            return acc.id
        return self.random_id() if default_if_empty else -1

    def _get_random_message(self) -> Message | None:
        if not self.messages:
            return None
        return random.choice(self.messages)

    def _get_random_message_id(self, default_if_empty=True) -> int:
        msg = self._get_random_message()
        if msg:
            return msg.messageId
        return self.random_id(min_id=self.MIN_ID, max_id=self.MAX_ID) if default_if_empty else -1
        
    def _get_random_stored_emoji_id(self, default_if_empty=True) -> int:
        if self.stored_emoji_ids:
            return random.choice(list(self.stored_emoji_ids))
        if default_if_empty:
            return self.random_id(min_id=self.MIN_EMOJI_ID, max_id=self.MAX_EMOJI_ID)
        return self._get_new_emoji_id_for_sei_aem() 


    def get_result(self) -> list[str]:
        return [str(operation) for operation in self.operations]

    def add_operation_load_network(self):
        self.network = Network()
        self.official_accounts = []
        self.messages = []
        self.stored_emoji_ids = set()
        
        _ln_person_id_counter = 1 

        # Use configurable min/max persons for ln
        person_count = random.randint(self.LOAD_NETWORK_MIN_PERSONS, self.LOAD_NETWORK_MAX_PERSONS)
        
        # If chosen count is 1, and we prefer more interesting networks,
        # there's a chance to reroll to 0 or >1.
        if person_count == 1 and self.LOAD_NETWORK_MAX_PERSONS > 1 : 
             if random.random() < 0.8: # 80% chance to avoid exactly 1 person if range allows others
                if self.LOAD_NETWORK_MIN_PERSONS == 0 and self.LOAD_NETWORK_MAX_PERSONS >=2:
                    person_count = random.choice([0] + list(range(max(2,self.LOAD_NETWORK_MIN_PERSONS), self.LOAD_NETWORK_MAX_PERSONS + 1)))
                elif self.LOAD_NETWORK_MAX_PERSONS >=2: # Min is >= 1
                     person_count = random.randint(max(2,self.LOAD_NETWORK_MIN_PERSONS), self.LOAD_NETWORK_MAX_PERSONS)
                # If min=1, max=1, it will stay 1.
        elif person_count == 1 and self.LOAD_NETWORK_MAX_PERSONS <=1 and self.LOAD_NETWORK_MIN_PERSONS <=1:
             pass # person_count remains 1, which is fine.


        ids = []
        names = []
        ages = []
        
        for _ in range(person_count):
            ids.append(_ln_person_id_counter) 
            _ln_person_id_counter +=1
            names.append(self.random_name())
            ages.append(self.random_age())

        relations_data: list[list[int]] = []
        if person_count > 1:
            for k in range(person_count - 1): 
                line_values: list[int] = []
                for _ in range(k + 1): 
                    if random.random() < self.LOAD_NETWORK_RELATION_PROBABILITY: 
                        line_values.append(self.random_value(min_value=self.MIN_VALUE, max_value=self.MAX_VALUE))
                    else:
                        line_values.append(0) 
                relations_data.append(line_values)
        
        ln_op = OperationLoadNetwork(person_count, ids, names, ages, relations_data)
        self.operations.append(ln_op)

        for i in range(person_count):
            p = Person(ids[i], names[i], ages[i])
            self.network.add_person(p) 
        
        for k in range(len(relations_data)): 
            person1_loaded_id = ids[k+1] 
            for j in range(len(relations_data[k])): 
                person2_loaded_id = ids[j] 
                value = relations_data[k][j]
                if value > 0:
                    self.network.add_relation(person1_loaded_id, person2_loaded_id, value)
        
        if ids:
            self._next_person_id = max(ids) + 1
        else: 
            self._next_person_id = 1 
        
        # Reset other ID counters as ln implies a fresh start for accounts, messages etc.
        # within the context of the *current test case*.
        self._next_account_id = 1
        self._next_article_id = 1
        self._next_message_id = 1
        self._next_emoji_id = 1


    # --- Other add_operation_X methods remain unchanged from the previous full correct version ---
    def add_operation_add_person(self, new_person_percentage: float = 0.9):
        # ... (implementation from previous complete version) ...
        operation : OperationAddPerson
        NEW_PERSON = 0
        EXISTING_ID_NEW_DATA = 1
        
        choice = random.choices([NEW_PERSON, EXISTING_ID_NEW_DATA], 
                                weights=[new_person_percentage, 1-new_person_percentage])[0]
        
        id_val: int
        name_val = self.random_name()
        age_val = self.random_age()

        if choice == NEW_PERSON or not self.network.person_list:
            id_val = self._get_new_person_id()
            new_person = Person(id_val, name_val, age_val)
            self.network.add_person(new_person)
        else: 
            existing_person = self._get_random_existing_person()
            if existing_person: 
                 id_val = existing_person.id
            else: 
                 id_val = self._get_new_person_id()
                 new_person = Person(id_val, name_val, age_val)
                 self.network.add_person(new_person)


        operation = OperationAddPerson(id_val, name_val, age_val)
        self.operations.append(operation)

    def add_operation_add_relation(self, new_relation_percentage: float = 0.8):
        # ... (implementation from previous complete version) ...
        operation : OperationAddRelation
        NEW_VALID_RELATION = 0 
        EXISTING_RELATION = 1  
        RANDOM_IDS = 2         

        if len(self.network.person_list) < 2: 
            choice = RANDOM_IDS
        else:
            choice = random.choices(
                [NEW_VALID_RELATION, EXISTING_RELATION, RANDOM_IDS], 
                weights=[new_relation_percentage, (1-new_relation_percentage)/2, (1-new_relation_percentage)/2]
            )[0]

        personId1, personId2 = -1, -1
        value = self.random_value()

        if choice == NEW_VALID_RELATION:
            ids_persons = random.sample(self.network.person_list, 2)
            p1, p2 = ids_persons[0], ids_persons[1]
            
            if p1.has_relation(p2): 
                found_unrelated = False
                for _ in range(min(len(self.network.person_list)**2, 10)): 
                    p1_cand, p2_cand = random.sample(self.network.person_list, 2)
                    if not p1_cand.has_relation(p2_cand):
                        p1, p2 = p1_cand, p2_cand
                        found_unrelated = True
                        break
                if not found_unrelated: 
                    pass 
            
            personId1, personId2 = p1.id, p2.id
            # Ensure p1 and p2 are actually found in the current network before checking relation
            p1_in_network = self.network.find_person(p1.id)
            p2_in_network = self.network.find_person(p2.id)
            if p1_in_network and p2_in_network and not p1_in_network.has_relation(p2_in_network): 
                 self.network.add_relation(personId1, personId2, value)


        elif choice == EXISTING_RELATION:
            p1_with_relations = [p for p in self.network.person_list if p.acquaintance_list]
            if p1_with_relations:
                p1 = random.choice(p1_with_relations)
                p2 = random.choice(p1.acquaintance_list)
                personId1, personId2 = p1.id, p2.id
            else: 
                if len(self.network.person_list) >= 2:
                     personId1, personId2 = self._get_random_pair_of_person_ids(must_exist=True, must_be_different=True)
                elif len(self.network.person_list) == 1:
                     personId1 = self.network.person_list[0].id
                     personId2 = self.random_id() 
                     if personId2 == personId1: personId2 = self.random_id(min_id = personId1 +1 if personId1 < self.MAX_ID else self.MIN_ID) 
                else: 
                     personId1, personId2 = self.random_id(), self.random_id()

        
        else: 
            personId1, personId2 = self.random_id(), self.random_id()
            if random.random() < 0.1 : 
                 personId2 = personId1
            elif personId1 == personId2 : 
                 if len(self.network.person_list) > 1 or random.random() < 0.8: 
                    while personId2 == personId1: personId2 = self.random_id()

        operation = OperationAddRelation(personId1, personId2, value)
        self.operations.append(operation)
    
    def add_operation_modify_relation(self, modify_value_percentage: float = 0.7, 
                                      set_to_zero_percentage: float = 0.2): 
        # ... (implementation from previous complete version) ...
        operation : OperationModifyRelation
        
        MODIFY_EXISTING_VALUE = 0 
        SET_EXISTING_TO_ZERO = 1  
        NON_EXISTENT_RELATION = 2 
        RANDOM_ANYTHING = 3

        if not self.network.person_list or len(self.network.person_list) < 1:
            choice = RANDOM_ANYTHING
        else:
            has_relations = any(p.acquaintance_list for p in self.network.person_list)
            
            weights = [0.0]*4 
            if has_relations:
                weights[0] = modify_value_percentage
                weights[1] = set_to_zero_percentage
            
            if len(self.network.person_list) >= 1:
                 weights[2] = (1.0 - weights[0] - weights[1]) * 0.5 if (1.0 - weights[0] - weights[1]) > 0.01 else 0.1
            
            weights[3] = max(0.05, 1.0 - sum(weights)) 

            current_sum = sum(weights)
            if current_sum <= 0.01: 
                 weights = [0.0,0.0,0.5,0.5] if len(self.network.person_list) >=1 else [0.0,0.0,0.0,1.0]
            else: 
                 weights = [w/current_sum for w in weights]


            choice = random.choices(
                [MODIFY_EXISTING_VALUE, SET_EXISTING_TO_ZERO, NON_EXISTENT_RELATION, RANDOM_ANYTHING],
                weights=weights
            )[0]

        p1_id, p2_id = -1, -1
        new_value = self.random_m_val() 

        if choice == MODIFY_EXISTING_VALUE:
            p1_with_relations = [p for p in self.network.person_list if p.acquaintance_list]
            if p1_with_relations:
                p1 = random.choice(p1_with_relations)
                p2 = random.choice(p1.acquaintance_list)
                p1_id, p2_id = p1.id, p2.id
                while new_value == 0: new_value = self.random_m_val() 
                p1.modify_acquaintance_value(p2, new_value)
                p2.modify_acquaintance_value(p1, new_value)
            else: 
                choice = RANDOM_ANYTHING 

        if choice == SET_EXISTING_TO_ZERO:
            p1_with_relations = [p for p in self.network.person_list if p.acquaintance_list]
            if p1_with_relations:
                p1 = random.choice(p1_with_relations)
                p2 = random.choice(p1.acquaintance_list)
                p1_id, p2_id = p1.id, p2.id
                new_value = 0
                p1.modify_acquaintance_value(p2, new_value)
                p2.modify_acquaintance_value(p1, new_value)
            else: 
                choice = RANDOM_ANYTHING 


        if choice == NON_EXISTENT_RELATION:
            if len(self.network.person_list) >= 2:
                p1_cand, p2_cand = random.sample(self.network.person_list, 2)
                if p1_cand.has_relation(p2_cand): 
                    found_unrelated = False
                    for _ in range(5): 
                        p1_c, p2_c = random.sample(self.network.person_list, 2)
                        if not p1_c.has_relation(p2_c):
                            p1_cand, p2_cand = p1_c, p2_c
                            found_unrelated = True
                            break
                    if not found_unrelated: choice = RANDOM_ANYTHING 
                if choice != RANDOM_ANYTHING:
                    p1_id, p2_id = p1_cand.id, p2_cand.id
            elif len(self.network.person_list) == 1: 
                p1_id = self.network.person_list[0].id
                p2_id = self.random_id() 
                count = 0
                while (p2_id == p1_id or self.network.find_person(p2_id)) and count < 100 : 
                     p2_id = self.random_id() 
                     count +=1
                if p2_id == p1_id or self.network.find_person(p2_id): 
                     p2_id = self.MAX_ID + 100 
            else: 
                choice = RANDOM_ANYTHING
        
        if choice == RANDOM_ANYTHING: 
            p1_id, p2_id = self.random_id(), self.random_id()
            if random.random() < 0.1: 
                p2_id = p1_id

        operation = OperationModifyRelation(p1_id, p2_id, new_value)
        self.operations.append(operation)

    def add_operation_add_tag(self, valid_percentage: float = 0.8):
        # ... (implementation from previous complete version) ...
        operation : OperationAddTag
        VALID_NEW_TAG = 0; VALID_EXISTING_TAG = 1; RANDOM_IDS = 2          

        if not self.network.person_list: choice = RANDOM_IDS
        else:
            choice = random.choices(
                [VALID_NEW_TAG, VALID_EXISTING_TAG, RANDOM_IDS],
                weights=[valid_percentage * 0.7, valid_percentage * 0.3, 1 - valid_percentage]
            )[0]
        
        person_id = -1; tag_id = self.random_id(min_id=1, max_id=100) 

        if choice == VALID_NEW_TAG:
            person = self._get_random_existing_person()
            person_id = person.id
            existing_tag_ids = {t.id for t in person.tag_list}
            original_tag_id = tag_id; count = 0
            while tag_id in existing_tag_ids and count < 100: 
                tag_id = self.random_id(min_id=1, max_id=100); count +=1
            if tag_id in existing_tag_ids : tag_id = max(existing_tag_ids) + 1 if existing_tag_ids else original_tag_id 
            new_tag_obj = Tag(tag_id); person.add_tag(new_tag_obj)
        
        elif choice == VALID_EXISTING_TAG:
            person = self._get_random_existing_person()
            person_id = person.id
            existing_tag_obj = self._get_random_existing_tag_for_person(person)
            if existing_tag_obj: tag_id = existing_tag_obj.id
            if not person.find_tag(tag_id): person.add_tag(Tag(tag_id))
            
        else: person_id = self.random_id()
            
        operation = OperationAddTag(person_id, tag_id); self.operations.append(operation)
    
    def add_operation_del_tag(self, valid_percentage: float = 0.7, 
                              tag_unexist_percentage: float = 0.15,
                              person_unexist_percentage: float = 0.1):
        # ... (implementation from previous complete version) ...
        operation : OperationDelTag
        VALID_DELETE = 0; TAG_UNEXIST_FOR_PERSON = 1; PERSON_UNEXIST = 2; RANDOM_ANYTHING = 3

        if not self.network.person_list:
            choice = random.choices([PERSON_UNEXIST, RANDOM_ANYTHING], weights=[0.5,0.5])[0]
        else:
            person_with_tags_exists = any(p.tag_list for p in self.network.person_list)
            weights = [0.0]*4
            weights[0] = valid_percentage if person_with_tags_exists else 0.0
            weights[1] = tag_unexist_percentage 
            weights[2] = person_unexist_percentage
            weights[3] = max(0.05, 1.0 - sum(weights))
            current_sum = sum(weights)
            if current_sum <= 0.01: weights = [0.0,0.0,0.5,0.5] if self.network.person_list else [0.0,0.0,0.0,1.0]
            else: weights = [w/current_sum for w in weights]
            choice = random.choices(
                [VALID_DELETE, TAG_UNEXIST_FOR_PERSON, PERSON_UNEXIST, RANDOM_ANYTHING],
                weights=weights
            )[0]

        person_id = -1; tag_id = self.random_id(min_id=1, max_id=100)

        if choice == VALID_DELETE:
            persons_with_tags = [p for p in self.network.person_list if p.tag_list]
            if persons_with_tags:
                person = random.choice(persons_with_tags)
                tag_to_delete = random.choice(person.tag_list)
                person_id = person.id; tag_id = tag_to_delete.id
                person.remove_tag(tag_to_delete) 
            else: choice = RANDOM_ANYTHING

        if choice == TAG_UNEXIST_FOR_PERSON: 
            person = self._get_random_existing_person() 
            person_id = person.id
            existing_tag_ids = {t.id for t in person.tag_list}
            original_tag_id = tag_id; count = 0
            while tag_id in existing_tag_ids and count < 100: 
                 tag_id = self.random_id(min_id=1, max_id=100); count += 1
            if tag_id in existing_tag_ids: tag_id = max(existing_tag_ids) +1 if existing_tag_ids else original_tag_id
        
        if choice == PERSON_UNEXIST:
            person_id = self.random_id(); count = 0
            while self.network.find_person(person_id) and count < 100: 
                person_id = self.random_id(); count += 1
            if self.network.find_person(person_id): person_id = self.MAX_ID + 100
        
        if choice == RANDOM_ANYTHING: person_id = self.random_id()
            
        operation = OperationDelTag(person_id, tag_id); self.operations.append(operation)

    def add_operation_add_to_tag(self, valid_percentage: float = 0.7, tag_unexist_percentage: float = 0.15):
        # ... (implementation from previous complete version) ...
        operation : OperationAddToTag
        VALID = 0; TAG_UNEXIST_FOR_P1 = 1; P1_OR_P2_UNEXIST = 2; RANDOM_ANYTHING = 3

        if len(self.network.person_list) < 1: 
            choice = random.choices([P1_OR_P2_UNEXIST, RANDOM_ANYTHING], weights=[0.5,0.5])[0]
        else:
            person_with_tags_exists = any(p.tag_list for p in self.network.person_list)
            weights = [0.0]*4
            weights[0] = valid_percentage if person_with_tags_exists and len(self.network.person_list) >=1 else 0.0
            weights[1] = tag_unexist_percentage if len(self.network.person_list) >=1 else 0.0
            weights[2] = (1.0 - weights[0] - weights[1]) * 0.5 if (1.0 - weights[0] - weights[1]) > 0.01 else 0.05
            weights[3] = max(0.05, 1.0 - sum(weights))
            current_sum = sum(weights)
            if current_sum <= 0.01: weights = [0.0,0.0,0.5,0.5] if len(self.network.person_list) >=1 else [0.0,0.0,0.0,1.0]
            else: weights = [w/current_sum for w in weights]
            choice = random.choices(
                [VALID, TAG_UNEXIST_FOR_P1, P1_OR_P2_UNEXIST, RANDOM_ANYTHING],
                weights=weights
            )[0]

        p1_id, p2_id = -1,-1; tag_id_val = self.random_id(min_id=1, max_id=100)

        if choice == VALID:
            persons_with_tags = [p for p in self.network.person_list if p.tag_list]
            if persons_with_tags:
                p1 = random.choice(persons_with_tags)
                tag_obj = random.choice(p1.tag_list) 
                possible_p2s = [p_other for p_other in self.network.person_list if p_other.id != p1.id and p_other not in tag_obj.personList]
                if not possible_p2s: 
                    possible_p2s = [p_other for p_other in self.network.person_list if p_other.id != p1.id] 
                    if not possible_p2s and self.network.person_list : possible_p2s = [p1] 
                if possible_p2s:
                    p2 = random.choice(possible_p2s)
                    p1_id, p2_id, tag_id_val = p1.id, p2.id, tag_obj.id
                    tag_obj.add_person(p2) 
                else: choice = RANDOM_ANYTHING 
            else: choice = RANDOM_ANYTHING
        
        if choice == TAG_UNEXIST_FOR_P1: 
            p1 = self._get_random_existing_person() 
            p1_id = p1.id
            existing_tag_ids = {t.id for t in p1.tag_list}
            original_tag_id = tag_id_val; count = 0
            while tag_id_val in existing_tag_ids and count < 100: 
                 tag_id_val = self.random_id(min_id=1, max_id=100); count += 1
            if tag_id_val in existing_tag_ids : tag_id_val = max(existing_tag_ids)+1 if existing_tag_ids else original_tag_id
            p2_id = self._get_random_existing_person_id() if len(self.network.person_list)>0 else self.random_id()

        if choice == P1_OR_P2_UNEXIST:
            if random.random() < 0.5 or not self.network.person_list: 
                p1_id = self.random_id()
                while self.network.find_person(p1_id): p1_id = self.random_id() 
                p2_id = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            else: 
                p1_id = self._get_random_existing_person_id()
                p2_id = self.random_id()
                while self.network.find_person(p2_id): p2_id = self.random_id() 
        
        if choice == RANDOM_ANYTHING: p1_id, p2_id = self.random_id(), self.random_id()
            
        operation = OperationAddToTag(p1_id, p2_id, tag_id_val); self.operations.append(operation)

    def add_operation_del_from_tag(self, valid_percentage: float = 0.7, tag_unexist_percentage: float = 0.15):
        # ... (implementation from previous complete version) ...
        operation : OperationDelFromTag
        VALID = 0; TAG_UNEXIST_FOR_P1 = 1; P2_NOT_IN_TAG = 2; P1_OR_P2_UNEXIST = 3; RANDOM_ANYTHING = 4

        if not self.network.person_list:
             choice = random.choices([P1_OR_P2_UNEXIST, RANDOM_ANYTHING], weights=[0.5,0.5])[0]
        else:
            can_do_valid = False
            for p1_cand in self.network.person_list:
                for tag_cand in p1_cand.tag_list:
                    if tag_cand.personList: can_do_valid = True; break
                if can_do_valid: break
            weights = [0.0]*5
            weights[0] = valid_percentage if can_do_valid else 0.0
            if self.network.person_list:
                weights[1] = tag_unexist_percentage * 0.4 
                weights[2] = tag_unexist_percentage * 0.6 
            weights[3] = (1.0 - sum(weights[:3])) * 0.5 if (1.0 - sum(weights[:3])) > 0.01 else 0.05
            weights[4] = max(0.05, 1.0 - sum(weights))
            current_sum = sum(weights)
            if current_sum <= 0.01 : weights = [0.0,0.0,0.0,0.5,0.5] if self.network.person_list else [0.0,0.0,0.0,0.0,1.0]
            else: weights = [w/current_sum for w in weights]
            choice = random.choices(
                [VALID, TAG_UNEXIST_FOR_P1, P2_NOT_IN_TAG, P1_OR_P2_UNEXIST, RANDOM_ANYTHING],
                weights=weights
            )[0]

        p1_id, p2_id = -1,-1; tag_id_val = self.random_id(min_id=1, max_id=100)

        if choice == VALID:
            valid_p1_tag_pairs = []
            for p1_cand in self.network.person_list:
                for tag_cand in p1_cand.tag_list:
                    if tag_cand.personList: valid_p1_tag_pairs.append((p1_cand, tag_cand))
            if valid_p1_tag_pairs:
                p1, tag_obj = random.choice(valid_p1_tag_pairs)
                p2 = random.choice(tag_obj.personList) 
                p1_id, p2_id, tag_id_val = p1.id, p2.id, tag_obj.id
                tag_obj.remove_person(p2) 
            else: choice = RANDOM_ANYTHING
        
        if choice == TAG_UNEXIST_FOR_P1:
            p1 = self._get_random_existing_person() 
            if p1:
                p1_id = p1.id; existing_tag_ids = {t.id for t in p1.tag_list}
                original_tag_id = tag_id_val; count = 0
                while tag_id_val in existing_tag_ids and count < 100:
                    tag_id_val = self.random_id(min_id=1, max_id=100); count += 1
                if tag_id_val in existing_tag_ids: tag_id_val = max(existing_tag_ids)+1 if existing_tag_ids else original_tag_id
                p2_id = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            else: choice = RANDOM_ANYTHING

        if choice == P2_NOT_IN_TAG:
            p1_with_tags = [p for p in self.network.person_list if p.tag_list]
            if p1_with_tags:
                p1 = random.choice(p1_with_tags); tag_obj = random.choice(p1.tag_list)
                p1_id, tag_id_val = p1.id, tag_obj.id
                possible_p2s = [p_other for p_other in self.network.person_list if p_other not in tag_obj.personList]
                if possible_p2s: p2_id = random.choice(possible_p2s).id
                else: 
                    p2_id = self.random_id(); count = 0
                    while self.network.find_person(p2_id) and count < 100: p2_id = self.random_id(); count+=1
                    if self.network.find_person(p2_id): p2_id = self.MAX_ID + 101
            else: choice = RANDOM_ANYTHING
        
        if choice == P1_OR_P2_UNEXIST: 
            if random.random() < 0.5 or not self.network.person_list : 
                p1_id = self.random_id()
                while self.network.find_person(p1_id): p1_id = self.random_id()
                p2_id = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            elif self.network.person_list: 
                p1_id = self._get_random_existing_person_id()
                p2_id = self.random_id()
                while self.network.find_person(p2_id): p2_id = self.random_id()
            else: p1_id, p2_id = self.random_id(), self.random_id()

        if choice == RANDOM_ANYTHING: p1_id, p2_id = self.random_id(), self.random_id()
            
        operation = OperationDelFromTag(p1_id, p2_id, tag_id_val); self.operations.append(operation)
    
    def add_operation_query_value(self, valid_percentage: float = 0.85):
        operation : OperationQueryValue; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        p1_id, p2_id = -1, -1
        if choice == VALID:
            p1_with_acq = [p for p in self.network.person_list if p.acquaintance_list]
            if p1_with_acq:
                p1 = random.choice(p1_with_acq); p2 = random.choice(p1.acquaintance_list)
                p1_id, p2_id = p1.id, p2.id
            else: choice = RANDOM
        if choice == RANDOM:
            p1_id, p2_id = self._get_random_pair_of_person_ids(must_exist=False, must_be_different=False)
            if random.random() < 0.1: p2_id = p1_id
        operation = OperationQueryValue(p1_id, p2_id); self.operations.append(operation)

    def add_operation_query_circle(self, valid_percentage: float = 0.85):
        operation : OperationQueryCircle; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        p1_id, p2_id = -1, -1
        if choice == VALID and len(self.network.person_list) > 0 :
             if len(self.network.person_list) >=2:
                  p1, p2 = random.sample(self.network.person_list, 2); p1_id, p2_id = p1.id, p2.id
             else: 
                  p1_id = self.network.person_list[0].id
                  p2_id = p1_id if random.random() < 0.5 else self.random_id() 
        else: 
            p1_id, p2_id = self._get_random_pair_of_person_ids(must_exist=False, must_be_different=False)
            if random.random() < 0.1: p2_id = p1_id
        operation = OperationQueryCircle(p1_id, p2_id); self.operations.append(operation)

    def add_operation_query_triple_sum(self):
        operation = OperationQueryTripleSum(); self.operations.append(operation)

    def add_operation_query_tag_age_var(self, valid_percentage: float = 0.85):
        operation : OperationQueryTagAgeVar; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id = -1; tag_id = self.random_id(min_id=1, max_id=100)
        if choice == VALID:
            persons_with_tags = [p for p in self.network.person_list if p.tag_list]
            if persons_with_tags:
                person = random.choice(persons_with_tags); tag_obj = random.choice(person.tag_list)
                person_id, tag_id = person.id, tag_obj.id
            else: choice = RANDOM
        if choice == RANDOM:
            person_id = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
        operation = OperationQueryTagAgeVar(person_id, tag_id); self.operations.append(operation)
    
    def add_operation_query_best_acquaintance(self, valid_percentage: float = 0.85):
        operation : OperationQueryBestAcquaintance; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id = -1
        if choice == VALID and self.network.person_list: person_id = self._get_random_existing_person_id()
        else: person_id = self.random_id()
        operation = OperationQueryBestAcquaintance(person_id); self.operations.append(operation)
    
    def add_operation_create_official_account(self, valid_percentage: float = 0.8):
        operation: OperationCreateOfficialAccount; VALID_NEW = 0; EXISTING_ACC_ID = 1; PERSON_UNEXIST = 2
        if not self.network.person_list: choice = PERSON_UNEXIST
        else:
            choice = random.choices(
                [VALID_NEW, EXISTING_ACC_ID, PERSON_UNEXIST],
                weights=[valid_percentage, (1-valid_percentage)*0.7, (1-valid_percentage)*0.3]
            )[0]
        owner_id = -1; account_id_val = -1; account_name = self.random_name()
        if choice == VALID_NEW:
            owner = self._get_random_existing_person(); owner_id = owner.id
            account_id_val = self._get_new_account_id()
            new_acc = OfficialAccount(owner_id, account_id_val, account_name); self.official_accounts.append(new_acc)
        elif choice == EXISTING_ACC_ID:
            owner_id = self._get_random_existing_person_id() 
            existing_acc = self._get_random_existing_official_account()
            if existing_acc: account_id_val = existing_acc.id
            else: account_id_val = self._get_new_account_id()
        elif choice == PERSON_UNEXIST:
            owner_id = self.random_id()
            while self.network.find_person(owner_id): owner_id = self.random_id()
            account_id_val = self._get_new_account_id()
        operation = OperationCreateOfficialAccount(owner_id, account_id_val, account_name); self.operations.append(operation)

    def add_operation_delete_official_account(self, valid_percentage: float = 0.8):
        operation: OperationDeleteOfficialAccount
        VALID_DELETE = 0; ACCOUNT_UNEXIST = 1; WRONG_OWNER = 2; RANDOM_IDS = 3
        if not self.official_accounts: 
            choice = random.choices([ACCOUNT_UNEXIST, RANDOM_IDS], weights=[0.5,0.5])[0]
        else:
            weights = [0.0]*4; weights[0] = valid_percentage; weights[1] = (1.0-valid_percentage)*0.4
            weights[2] = (1.0-valid_percentage)*0.3 if self.network.person_list and len(self.network.person_list) >=1 else 0.0
            weights[3] = max(0.05, 1.0 - sum(weights))
            current_sum = sum(weights)
            if current_sum <= 0.01: weights = [0.0,0.5,0.0,0.5] if not (self.network.person_list and len(self.network.person_list) >=1) else [0.0,0.0,0.0,1.0]
            else: weights = [w/current_sum for w in weights]
            choice = random.choices([VALID_DELETE, ACCOUNT_UNEXIST, WRONG_OWNER, RANDOM_IDS], weights=weights)[0]
        person_id_val = -1; account_id_val = -1
        if choice == VALID_DELETE:
            acc_to_delete = self._get_random_existing_official_account() 
            person_id_val = acc_to_delete.ownerId 
            if not self.network.find_person(person_id_val): choice = RANDOM_IDS 
            else: account_id_val = acc_to_delete.id; self.official_accounts.remove(acc_to_delete)
        if choice == ACCOUNT_UNEXIST: 
            person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            account_id_val = self.random_id()
            while any(acc.id == account_id_val for acc in self.official_accounts): account_id_val = self.random_id()
        if choice == WRONG_OWNER: 
            acc_obj = self._get_random_existing_official_account() 
            if acc_obj and self.network.person_list : 
                account_id_val = acc_obj.id
                non_owners = [p for p in self.network.person_list if p.id != acc_obj.ownerId]
                if non_owners: person_id_val = random.choice(non_owners).id
                else: choice = RANDOM_IDS 
            else: choice = RANDOM_IDS
        if choice == RANDOM_IDS: person_id_val = self.random_id(); account_id_val = self.random_id()
        operation = OperationDeleteOfficialAccount(person_id_val, account_id_val); self.operations.append(operation)

    def add_operation_contribute_article(self, valid_percentage: float = 0.7, account_unexist_percentage: float = 0.15):
        operation: OperationContributeArticle
        VALID = 0; ACCOUNT_UNEXIST = 1; PERSON_UNEXIST = 2; RANDOM_ANYTHING = 3
        if not self.network.person_list: choice = random.choices([PERSON_UNEXIST, ACCOUNT_UNEXIST, RANDOM_ANYTHING], weights=[0.4,0.3,0.3])[0]
        elif not self.official_accounts: choice = random.choices([ACCOUNT_UNEXIST, RANDOM_ANYTHING], weights=[0.6,0.4])[0]
        else:
            weights = [0.0]*4; weights[0] = valid_percentage; weights[1] = account_unexist_percentage
            weights[2] = (1.0 - weights[0] - weights[1]) * 0.5 if (1.0 - weights[0] - weights[1]) > 0.01 else 0.05
            weights[3] = max(0.05, 1.0 - sum(weights)); current_sum = sum(weights)
            if current_sum <= 0.01: weights=[0.0,0.0,0.5,0.5]; 
            else: weights = [w/current_sum for w in weights]
            choice = random.choices([VALID, ACCOUNT_UNEXIST, PERSON_UNEXIST, RANDOM_ANYTHING], weights=weights)[0]
        person_id_val = -1; account_id_val = -1
        article_id_val = self._get_new_article_id(); article_name = self.random_name()
        if choice == VALID:
            person_id_val = self._get_random_existing_person_id(); acc_obj = self._get_random_existing_official_account() 
            account_id_val = acc_obj.id; acc_obj.add_article(article_id_val)
        if choice == ACCOUNT_UNEXIST:
            person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            account_id_val = self.random_id()
            while any(acc.id == account_id_val for acc in self.official_accounts): account_id_val = self.random_id()
        if choice == PERSON_UNEXIST:
            person_id_val = self.random_id()
            while self.network.find_person(person_id_val): person_id_val = self.random_id()
            if self.official_accounts: account_id_val = self._get_random_existing_official_account_id()
            else: account_id_val = self.random_id() 
        if choice == RANDOM_ANYTHING: 
            person_id_val = self.random_id(); account_id_val = self.random_id()
            article_id_val = self.random_id(min_id=self.MIN_ARTICLE_ID, max_id=self.MAX_ARTICLE_ID)
        operation = OperationContributeArticle(person_id_val, account_id_val, article_id_val, article_name); self.operations.append(operation)

    def add_operation_delete_article(self, valid_percentage: float = 0.7, article_unexist_percentage: float = 0.15):
        operation: OperationDeleteArticle
        VALID = 0; ARTICLE_UNEXIST_IN_ACC = 1; ACCOUNT_UNEXIST = 2; RANDOM_ANYTHING = 3
        accounts_with_articles = [acc for acc in self.official_accounts if acc.articleList]
        if not accounts_with_articles:
            choice = random.choices([ARTICLE_UNEXIST_IN_ACC, ACCOUNT_UNEXIST, RANDOM_ANYTHING], weights=[0.3,0.4,0.3])[0]
            if choice == ARTICLE_UNEXIST_IN_ACC and not self.official_accounts: 
                choice = ACCOUNT_UNEXIST if random.random() < 0.7 else RANDOM_ANYTHING
        else:
            weights = [0.0]*4; weights[0] = valid_percentage; weights[1] = article_unexist_percentage
            weights[2] = (1.0-weights[0]-weights[1])*0.5 if (1.0-weights[0]-weights[1]) > 0.01 else 0.05
            weights[3] = max(0.05, 1.0 - sum(weights)); current_sum = sum(weights)
            if current_sum <= 0.01: weights=[0.0,0.0,0.5,0.5]; 
            else: weights = [w/current_sum for w in weights]
            choice = random.choices([VALID, ARTICLE_UNEXIST_IN_ACC, ACCOUNT_UNEXIST, RANDOM_ANYTHING], weights=weights)[0]
        person_id_val = -1; account_id_val = -1; article_id_val = -1
        if choice == VALID: 
            acc_obj = random.choice(accounts_with_articles)
            article_id_val = random.choice(acc_obj.articleList); account_id_val = acc_obj.id
            person_id_val = acc_obj.ownerId 
            if not self.network.find_person(person_id_val): 
                 person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            acc_obj.remove_article(article_id_val)
        if choice == ARTICLE_UNEXIST_IN_ACC:
            if self.official_accounts: 
                acc_obj = self._get_random_existing_official_account(); account_id_val = acc_obj.id
                person_id_val = acc_obj.ownerId 
                if not self.network.find_person(person_id_val): person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
                article_id_val = self.random_id(min_id=self.MIN_ARTICLE_ID, max_id=self.MAX_ARTICLE_ID)
                while article_id_val in acc_obj.articleList : article_id_val = self.random_id(min_id=self.MIN_ARTICLE_ID, max_id=self.MAX_ARTICLE_ID)
            else: choice = RANDOM_ANYTHING 
        if choice == ACCOUNT_UNEXIST:
            person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
            account_id_val = self.random_id()
            while any(acc.id == account_id_val for acc in self.official_accounts): account_id_val = self.random_id()
            article_id_val = self.random_id(min_id=self.MIN_ARTICLE_ID, max_id=self.MAX_ARTICLE_ID)
        if choice == RANDOM_ANYTHING: 
            person_id_val = self.random_id(); account_id_val = self.random_id()
            article_id_val = self.random_id(min_id=self.MIN_ARTICLE_ID, max_id=self.MAX_ARTICLE_ID)
        operation = OperationDeleteArticle(person_id_val, account_id_val, article_id_val); self.operations.append(operation)

    def add_operation_follow_official_account(self, valid_percentage: float = 0.8):
        operation: OperationFollowOfficialAccount
        VALID = 0; ALREADY_FOLLOWER = 1; PERSON_OR_ACC_UNEXIST = 2; RANDOM_ANYTHING = 3
        if not self.network.person_list or not self.official_accounts:
             choice = random.choices([PERSON_OR_ACC_UNEXIST, RANDOM_ANYTHING], weights=[0.5,0.5])[0]
        else: 
            weights = [valid_percentage, (1-valid_percentage)*0.3, (1-valid_percentage)*0.3, max(0.05, (1-valid_percentage)*0.4)]
            current_sum = sum(weights)
            if current_sum <= 0.01: weights=[0.0,0.0,0.5,0.5]; 
            else: weights = [w/current_sum for w in weights]
            choice = random.choices([VALID, ALREADY_FOLLOWER, PERSON_OR_ACC_UNEXIST, RANDOM_ANYTHING], weights=weights)[0]
        person_id_val = -1; account_id_val = -1
        if choice == VALID or choice == ALREADY_FOLLOWER: 
            person_obj = self._get_random_existing_person(); acc_obj = self._get_random_existing_official_account()
            person_id_val = person_obj.id; account_id_val = acc_obj.id
            is_follower = acc_obj.contains_follower(person_obj)
            if choice == VALID and is_follower: choice = ALREADY_FOLLOWER 
            if choice == ALREADY_FOLLOWER and not is_follower: choice = VALID 
            if choice == VALID: acc_obj.add_follower(person_obj, 0) 
        if choice == PERSON_OR_ACC_UNEXIST:
            if random.random() < 0.5 or not self.network.person_list: 
                person_id_val = self.random_id()
                while self.network.find_person(person_id_val): person_id_val = self.random_id()
                account_id_val = self._get_random_existing_official_account_id() if self.official_accounts else self.random_id()
            else: 
                person_id_val = self._get_random_existing_person_id()
                account_id_val = self.random_id()
                while any(acc.id == account_id_val for acc in self.official_accounts): account_id_val = self.random_id()
        if choice == RANDOM_ANYTHING: person_id_val = self.random_id(); account_id_val = self.random_id()
        operation = OperationFollowOfficialAccount(person_id_val, account_id_val); self.operations.append(operation)

    def add_operation_query_shortest_path(self, valid_percentage: float = 0.85): 
        operation : OperationQueryShortestPath; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        p1_id, p2_id = -1, -1
        if choice == VALID and len(self.network.person_list) > 0 :
             if len(self.network.person_list) >=2:
                  p1, p2 = random.sample(self.network.person_list, 2); p1_id, p2_id = p1.id, p2.id
             else: 
                  p1_id = self.network.person_list[0].id
                  p2_id = p1_id if random.random() < 0.5 else self.random_id()
        else: 
            p1_id, p2_id = self._get_random_pair_of_person_ids(must_exist=False, must_be_different=False)
            if random.random() < 0.1: p2_id = p1_id 
        operation = OperationQueryShortestPath(p1_id, p2_id); self.operations.append(operation)

    def add_operation_query_best_contributor(self, valid_percentage: float = 0.85):
        operation : OperationQueryBestContributor; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        account_id_val = -1
        if choice == VALID and self.official_accounts: account_id_val = self._get_random_existing_official_account_id()
        else: account_id_val = self.random_id()
        operation = OperationQueryBestContributor(account_id_val); self.operations.append(operation)

    def add_operation_query_received_articles(self, valid_percentage: float = 0.85):
        operation : OperationQueryReceivedArticles; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id_val = -1
        if choice == VALID and self.network.person_list: person_id_val = self._get_random_existing_person_id()
        else: person_id_val = self.random_id()
        operation = OperationQueryReceivedArticles(person_id_val); self.operations.append(operation)

    def add_operation_query_tag_value_sum(self,valid_percentage: float = 0.85):
        operation : OperationQueryTagValueSum; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id_val = -1; tag_id_val = self.random_id(min_id=1, max_id=100)
        if choice == VALID:
            persons_with_tags = [p for p in self.network.person_list if p.tag_list]
            if persons_with_tags:
                person = random.choice(persons_with_tags); tag_obj = random.choice(person.tag_list)
                person_id_val, tag_id_val = person.id, tag_obj.id
            else: choice = RANDOM
        if choice == RANDOM:
            person_id_val = self._get_random_existing_person_id() if self.network.person_list else self.random_id()
        operation = OperationQueryTagValueSum(person_id_val, tag_id_val); self.operations.append(operation)

    def add_operation_query_couple_sum(self):
        operation = OperationQueryCoupleSum(); self.operations.append(operation)   

    def _add_any_message(self, msg_type_str: str, tag_percentage: float = 0.4):
        op_to_add : Operation | None = None; message_obj: Message | None = None
        TO_PERSON = 0; TO_TAG = 1    
        if not self.network.person_list: 
            p1_id = self.random_id(); msg_id = self._get_new_message_id()
            type_val = random.randint(0,1); id2 = self.random_id() 
            if msg_type_str == "am": social_val = self.random_social_value(); op_to_add = OperationAddMessage(msg_id, social_val, type_val, p1_id, id2)
            elif msg_type_str == "aem": emoji_id_val = self._get_new_emoji_id_for_sei_aem(); op_to_add = OperationAddEmojiMessage(msg_id, emoji_id_val, type_val, p1_id, id2)
            elif msg_type_str == "arem": money = self.random_money(); op_to_add = OperationAddRedEnvelopeMessage(msg_id, money, type_val, p1_id, id2)
            elif msg_type_str == "afm": article_id_val = self.random_id(self.MIN_ARTICLE_ID, self.MAX_ARTICLE_ID); op_to_add = OperationAddForwardMessage(msg_id, article_id_val, type_val, p1_id, id2)
            if op_to_add: self.operations.append(op_to_add)
            return
        p1 = self._get_random_existing_person(); p1_id = p1.id
        msg_id = self._get_new_message_id()
        choice = random.choices([TO_PERSON, TO_TAG], weights=[1 - tag_percentage, tag_percentage])[0]
        type_val = -1; id2 = -1 
        if choice == TO_PERSON:
            type_val = 0
            if len(self.network.person_list) > 0 and random.random() < 0.8 : 
                 p2_cand = self._get_random_existing_person(); id2 = p2_cand.id
                 if random.random() < 0.1 and p1_id == id2 and len(self.network.person_list) > 1: 
                      others = [person for person in self.network.person_list if person.id != p1_id]
                      if others: id2 = random.choice(others).id
            else: id2 = self.random_id()
        else: 
            type_val = 1
            tag_for_p1 = self._get_random_existing_tag_for_person(p1)
            if tag_for_p1 and random.random() < 0.8: id2 = tag_for_p1.id
            else: id2 = self.random_id(min_id=1, max_id=100) 
        if msg_type_str == "am":
            social_val = self.random_social_value()
            op_to_add = OperationAddMessage(msg_id, social_val, type_val, p1_id, id2)
            message_obj = Message(msg_id, social_val, type_val, p1_id, id2)
        elif msg_type_str == "aem":
            emoji_id_val = self.random_id(self.MIN_EMOJI_ID, self.MAX_EMOJI_ID) 
            if self.stored_emoji_ids and random.random() < 0.7: emoji_id_val = self._get_random_stored_emoji_id(default_if_empty=False) 
            elif not self.stored_emoji_ids or random.random() < 0.1: emoji_id_val = self._get_new_emoji_id_for_sei_aem()
            op_to_add = OperationAddEmojiMessage(msg_id, emoji_id_val, type_val, p1_id, id2)
            message_obj = EmojiMessage(msg_id, emoji_id_val, type_val, p1_id, id2)
        elif msg_type_str == "arem":
            money = self.random_money()
            op_to_add = OperationAddRedEnvelopeMessage(msg_id, money, type_val, p1_id, id2)
            message_obj = RedEnvelopeMessage(msg_id, money, type_val, p1_id, id2)
        elif msg_type_str == "afm":
            article_id_val = self.random_id(self.MIN_ARTICLE_ID, self.MAX_ARTICLE_ID) 
            if self.official_accounts and random.random() < 0.7:
                acc_with_articles = [acc for acc in self.official_accounts if acc.articleList]
                if acc_with_articles: chosen_acc = random.choice(acc_with_articles); article_id_val = random.choice(chosen_acc.articleList) 
            op_to_add = OperationAddForwardMessage(msg_id, article_id_val, type_val, p1_id, id2)
            message_obj = ForwardMessage(msg_id, article_id_val, type_val, p1_id, id2)
        if op_to_add: self.operations.append(op_to_add)
        if message_obj: self.messages.append(message_obj)

    def add_operation_add_message(self, tag_percentage: float = 0.4): self._add_any_message("am", tag_percentage)
    def add_operation_add_emoji_message(self, tag_percentage: float = 0.4): self._add_any_message("aem", tag_percentage)
    def add_operation_add_red_envelope_message(self, tag_percentage: float = 0.4): self._add_any_message("arem", tag_percentage)
    def add_operation_add_forward_message(self, tag_percentage: float = 0.4): self._add_any_message("afm", tag_percentage)

    def add_operation_send_message(self, valid_percentage: float = 0.9):
        operation : OperationSendMessage; VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        msg_id_to_send = -1
        if choice == VALID and self.messages:
            msg_id_to_send = self._get_random_message_id(default_if_empty=False) 
            if msg_id_to_send == -1 : msg_id_to_send = self.random_id()
        else: msg_id_to_send = self.random_id() 
        operation = OperationSendMessage(msg_id_to_send); self.operations.append(operation)

    def add_operation_store_emoji_id(self): 
        if random.random() < 0.7 and self.stored_emoji_ids: 
            emoji_id_to_store = self._get_random_stored_emoji_id(default_if_empty=False)
        else: emoji_id_to_store = self._get_new_emoji_id_for_sei_aem()
        operation = OperationStoreEmojiId(emoji_id_to_store); self.operations.append(operation)
        self.stored_emoji_ids.add(emoji_id_to_store)

    def add_operation_delete_cold_emoji(self): 
        limit = random.randint(0, 10) 
        if self.stored_emoji_ids: limit = random.randint(0, len(self.stored_emoji_ids) + 5)
        operation = OperationDeleteColdEmoji(limit); self.operations.append(operation)

    def add_operation_query_social_value(self, valid_percentage: float = 0.9):
        VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id = self._get_random_existing_person_id() if choice == VALID and self.network.person_list else self.random_id()
        operation = OperationQuerySocialValue(person_id); self.operations.append(operation)

    def add_operation_query_received_messages(self, valid_percentage: float = 0.9):
        VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id = self._get_random_existing_person_id() if choice == VALID and self.network.person_list else self.random_id()
        operation = OperationQueryReceivedMessages(person_id); self.operations.append(operation)

    def add_operation_query_popularity(self, valid_percentage: float = 0.9):
        VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        emoji_id_to_query = -1
        if choice == VALID:
            if self.stored_emoji_ids: emoji_id_to_query = self._get_random_stored_emoji_id(default_if_empty=False)
            elif self._next_emoji_id > 1 : emoji_id_to_query = self.random_id(min_id=self.MIN_EMOJI_ID, max_id=self._next_emoji_id -1)
            else: emoji_id_to_query = self.random_id(min_id=self.MIN_EMOJI_ID, max_id=self.MAX_EMOJI_ID)
        else: emoji_id_to_query = self.random_id(min_id=self.MIN_EMOJI_ID, max_id=self.MAX_EMOJI_ID + 100) 
        op = OperationQueryPopularity(emoji_id_to_query); self.operations.append(op)

    def add_operation_query_money(self, valid_percentage: float = 0.9):
        VALID = 0; RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]
        person_id = self._get_random_existing_person_id() if choice == VALID and self.network.person_list else self.random_id()
        operation = OperationQueryMoney(person_id); self.operations.append(operation)    

    def add_operations_randomly(self, num_operations: int):
        """Adds a specified number of random operations (excluding load_network)."""
        for _ in range(num_operations):
            self.add_one_random_operation_excluding_ln() 

    def add_one_random_operation_excluding_ln(self):
        """Selects and adds one random operation, ensuring load_network is not chosen."""
        possible_ops = []
        op_weights = []
        for op_type, weight in self.weights.items():
            if op_type == OperationLoadNetwork: 
                continue 
            if weight > 0:
                possible_ops.append(op_type)
                op_weights.append(weight)
        
        if not possible_ops: 
            if self.DEFAULT_ADD_PERSON_WEIGHT > 0: 
                 self.add_operation_add_person() 
            return

        operation_type = random.choices(possible_ops, weights=op_weights)[0]
        
        method_name_part = operation_type.__name__.replace("Operation", "")
        method_name_snake = ''.join(['_' + i.lower() if i.isupper() else i for i in method_name_part]).lstrip('_')
        method_to_call_name = f"add_operation_{method_name_snake}"

        if hasattr(self, method_to_call_name):
            method_to_call = getattr(self, method_to_call_name)
            method_to_call() 
        else:
            print(f"Warning: No generator method '{method_to_call_name}' for {operation_type.__name__}")


    @staticmethod
    def random_id(min_id : int = MIN_ID, max_id : int = MAX_ID) -> int: 
        actual_min = min(min_id, max_id)
        actual_max = max(min_id, max_id)
        if actual_min > actual_max: 
            return actual_min 
        return random.randint(actual_min, actual_max)

    @staticmethod
    def random_name() -> str:
        length = random.randint(1, Generator.MAX_STRING_LEN)
        return ''.join(random.choices(string.ascii_lowercase, k=length))

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