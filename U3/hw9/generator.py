import random

from operation import *
from objects import *

class Generator:
    network : Network
    weights : dict[Operation, float]
    operations : list[Operation]
    tags: dict[int, Tag] # Global registry for tags

    MAX_STRING_LEN = 10
    MIN_ID = -2147483648
    MAX_ID = 2147483647
    MIN_AGE = 1
    MAX_AGE = 200
    MIN_VALUE = 1
    MAX_VALUE = 200
    MIN_M_VAL = -200
    MAX_M_VAL = 200

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
            OperationQueryBestAcquaintance: self.DEFAULT_QUERY_BEST_ACQUAINTANCE_WEIGHT
            # OperationLoadNetwork is typically not generated randomly mid-test
        }
        self.tags = {}
        self.reset()

    def reset(self):
        self.network = Network()
        self.operations = []
        self.tags = {} # Reset tags as well

    def get_result(self) -> list[str]:
        return [str(operation) for operation in self.operations]

    def add_operations(self, num_operations: int):
        for i in range(num_operations):
            self.add_operation()

    # --- Helper methods for generation ---

    def _generate_random_person_params(self) -> tuple[int, str, int]:
        """Generates random id, name, age."""
        person_id = self.random_id()
        name = self.random_name()
        age = self.random_age()
        return person_id, name, age

    def _generate_new_person_params(self, max_tries=10) -> tuple[int, str, int] | None:
        """Tries to generate parameters for a person with a unique ID."""
        for _ in range(max_tries):
            person_id, name, age = self._generate_random_person_params()
            if not self.network.has_person(person_id):
                return person_id, name, age
        return None # Could not find a unique ID easily

    def _generate_random_relation_params(self) -> tuple[int, int, int]:
        """Generates random personId1, personId2 (distinct), value."""
        id1 = self.random_id()
        id2 = self.random_id()
        while id1 == id2: # Ensure distinct IDs
            id2 = self.random_id()
        value = self.random_value()
        return id1, id2, value

    def _find_existing_person_id(self) -> int | None:
        """Returns the ID of a random existing person, or None if no persons exist."""
        if not self.network.person_list:
            return None
        return random.choice(self.network.person_list).id

    def _find_two_existing_distinct_person_ids(self) -> tuple[int, int] | None:
        """Returns IDs of two distinct existing persons, or None if less than 2 exist."""
        if len(self.network.person_list) < 2:
            return None
        p1, p2 = random.sample(self.network.person_list, 2)
        return p1.id, p2.id

    def _find_existing_relation(self) -> tuple[int, int] | None:
        """Finds a pair of existing person IDs with an existing relation."""
        existing_relations = []
        persons = self.network.person_list
        for i in range(len(persons)):
            p1 = persons[i]
            for acquaintance in p1.acquaintance_list:
                 # Ensure we don't add duplicates (like (1,2) and (2,1)) and only store pairs where id1 < id2
                 if p1.id < acquaintance.id:
                     existing_relations.append((p1.id, acquaintance.id))

        if not existing_relations:
            return None
        return random.choice(existing_relations)

    def _find_non_existing_relation_between_existing_persons(self) -> tuple[int, int] | None:
        """Finds a pair of existing, distinct person IDs without a relation."""
        if len(self.network.person_list) < 2:
            return None

        potential_pairs = []
        persons = self.network.person_list
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                p1 = persons[i]
                p2 = persons[j]
                if not self.network.has_relation(p1.id, p2.id):
                    potential_pairs.append((p1.id, p2.id))

        if not potential_pairs:
             return None # All existing pairs have relations
        return random.choice(potential_pairs)

    def _generate_random_tag_params(self) -> tuple[int, int]:
        """Generates random personId, tagId."""
        person_id = self.random_id()
        tag_id = self.random_id() # Tags can have arbitrary IDs
        return person_id, tag_id

    def _find_existing_tag_id(self) -> int | None:
        """Returns a random existing tag ID, or None."""
        if not self.tags:
            return None
        return random.choice(list(self.tags.keys()))

    def _find_person_with_tag(self) -> tuple[int, int] | None:
        """Finds a (person_id, tag_id) pair where the person has the tag."""
        eligible = []
        for person in self.network.person_list:
            for tag in person.tag_list:
                eligible.append((person.id, tag.id))
        if not eligible:
            return None
        return random.choice(eligible)

    def _find_person_and_tag_to_add_to(self) -> tuple[int, int, int] | None:
        """Finds (person1_id, person2_id, tag_id) where person1 has tag, person2 exists but doesn't have tag."""
        for _ in range(len(self.tags) + len(self.network.person_list) + 5): # Heuristic retries
            tag_id = self._find_existing_tag_id()
            if tag_id is None: continue
            tag = self.tags.get(tag_id)
            if tag is None or not tag.personList: continue

            person1_id = random.choice(tag.personList).id

            eligible_p2 = [p.id for p in self.network.person_list if p.id != person1_id and p not in tag.personList]
            if not eligible_p2: continue

            person2_id = random.choice(eligible_p2)
            return person1_id, person2_id, tag_id
        return None

    def _find_person_and_tag_to_remove_from(self) -> tuple[int, int, int] | None:
        """Finds (person1_id, person2_id, tag_id) where person1 has tag, person2 is in tag (and person2 != person1)."""
        for _ in range(len(self.tags) + len(self.network.person_list) + 5): # Heuristic retries
            tag_id = self._find_existing_tag_id()
            if tag_id is None: continue
            tag = self.tags.get(tag_id)
            if tag is None or len(tag.personList) < 1: continue # Need at least p1 in the tag

            person1 = random.choice(tag.personList) # p1 must be in the tag

            # Find p2 also in the tag, but different from p1
            eligible_p2 = [p.id for p in tag.personList if p.id != person1.id]
            if not eligible_p2: continue # Cannot remove if only p1 (or no one else) is in tag

            person2_id = random.choice(eligible_p2)
            return person1.id, person2_id, tag_id
        return None

    # --- Operation Generation Methods ---

    def add_operation_add_person(self, new_person_percentage: float = 0.9):
        operation : OperationAddPerson = None
        params = None

        NEW_PERSON = 0
        RANDOM = 1
        choice = random.choices([NEW_PERSON, RANDOM], weights=[new_person_percentage, 1-new_person_percentage])[0]

        if choice == NEW_PERSON:
            params = self._generate_new_person_params()

        # Fallback to random if new generation failed or was not chosen
        if params is None:
            params = self._generate_random_person_params()

        person_id, name, age = params
        operation = OperationAddPerson(person_id, name, age)
        self.operations.append(operation)

        # --- Update internal state ---
        if not self.network.has_person(person_id):
            new_person = Person(person_id, name, age)
            self.network.add_person(new_person)
        # If person already exists, state doesn't change per operation semantics

    def add_operation_add_relation(self,
                                   new_relation_percentage: float = 0.8,
                                   relation_exist_percentage: float = 0.1):
        operation : OperationAddRelation = None
        params = None
        id1, id2, value = 0, 0, 0 # Initialize

        NEW_RELATION = 0
        RELATION_EXIST = 1
        RANDOM = 2
        choice = random.choices([NEW_RELATION, RELATION_EXIST, RANDOM], weights=[new_relation_percentage, relation_exist_percentage, 1-new_relation_percentage-relation_exist_percentage])[0]

        if choice == NEW_RELATION:
            pair = self._find_non_existing_relation_between_existing_persons()
            if pair:
                id1, id2 = pair
                value = self.random_value()
                params = (id1, id2, value)
        elif choice == RELATION_EXIST:
            pair = self._find_existing_relation()
            if pair:
                id1, id2 = pair
                value = self.random_value()
                params = (id1, id2, value)

        # Fallback to random if specific generation failed or was not chosen
        if params is None:
            id1, id2, value = self._generate_random_relation_params()
            params = (id1, id2, value)

        id1, id2, value = params
        operation = OperationAddRelation(id1, id2, value)
        self.operations.append(operation)

        # --- Update internal state ---
        p1 = self.network.find_person(id1)
        p2 = self.network.find_person(id2)
        if p1 and p2 and id1 != id2 and not self.network.has_relation(id1, id2):
            self.network.add_relation(id1, id2, value)
        # If relation exists, or persons don't exist, state doesn't change

    def add_operation_modify_relation(self,
                                      modify_value_percentage: float = 0.4,
                                      remove_relation_percentage: float = 0.4,
                                      only_person_exist_percentage: float = 0.1):
        operation : OperationModifyRelation = None
        params = None
        id1, id2, m_val = 0, 0, 0 # Initialize

        MODIFY_VALUE = 0
        REMOVE_RELATION = 1
        ONLY_PERSON_EXIST = 2 # Modify non-existing relation between existing people
        RANDOM = 3
        choice = random.choices([MODIFY_VALUE, REMOVE_RELATION, ONLY_PERSON_EXIST, RANDOM], weights=[modify_value_percentage, remove_relation_percentage, only_person_exist_percentage, 1-modify_value_percentage-remove_relation_percentage-only_person_exist_percentage])[0]

        if choice == MODIFY_VALUE:
            pair = self._find_existing_relation()
            if pair:
                id1, id2 = pair
                # Generate m_val such that the relation likely remains (>0)
                current_val = self.network.find_person(id1).get_acquaintance_value(self.network.find_person(id2))
                m_val = self.random_m_val()
                # Try to avoid accidentally removing the relation unless m_val is naturally negative enough
                if current_val + m_val <= 0:
                    m_val = self.random_value(1) # Ensure positive modification if possible
                params = (id1, id2, m_val)
        elif choice == REMOVE_RELATION:
            pair = self._find_existing_relation()
            if pair:
                id1, id2 = pair
                p1 = self.network.find_person(id1)
                p2 = self.network.find_person(id2)
                current_val = p1.get_acquaintance_value(p2)
                # Calculate m_val needed to make sum <= 0
                m_val = -current_val - random.randint(0, self.MAX_VALUE) # Make it definitely <= 0
                m_val = max(m_val, self.MIN_M_VAL) # Clamp to allowed range
                params = (id1, id2, m_val)
        elif choice == ONLY_PERSON_EXIST:
            pair = self._find_non_existing_relation_between_existing_persons()
            if pair:
                id1, id2 = pair
                m_val = self.random_m_val()
                params = (id1, id2, m_val)

        # Fallback to random
        if params is None:
            r_id1, r_id2 = self.random_id(), self.random_id()
            while r_id1 == r_id2:
                r_id2 = self.random_id()
            m_val = self.random_m_val()
            params = (r_id1, r_id2, m_val)

        id1, id2, m_val = params
        operation = OperationModifyRelation(id1, id2, m_val)
        self.operations.append(operation)

        # --- Update internal state ---
        p1 = self.network.find_person(id1)
        p2 = self.network.find_person(id2)
        if p1 and p2 and id1 != id2:
            current_val = p1.get_acquaintance_value(p2)
            if current_val is not None: # Relation exists
                new_val = current_val + m_val
                if new_val > 0:
                    p1.modify_acquaintance_value(p2, new_val)
                    p2.modify_acquaintance_value(p1, new_val)
                else: # Remove relation
                    p1.remove_acquaintance(p2)
                    p2.remove_acquaintance(p1)
            else: # Relation does not exist
                if m_val > 0:
                    self.network.add_relation(id1, id2, m_val)


    def add_operation_add_tag(self,
                               valid_percentage: float = 0.8,
                               tag_exist_percentage: float = 0.1):
        operation : OperationAddTag = None
        params = None
        person_id, tag_id = 0, 0 # Initialize

        VALID = 0 # Add a tag (potentially new) to an existing person
        TAG_EXIST = 1 # Add an existing tag to an existing person (might already have it)
        RANDOM = 2
        choice = random.choices([VALID, TAG_EXIST, RANDOM], weights=[valid_percentage, tag_exist_percentage, 1-valid_percentage-tag_exist_percentage])[0]

        if choice == VALID:
            p_id = self._find_existing_person_id()
            if p_id is not None:
                 # Try adding a globally new tag ID first
                 t_id = self.random_id()
                 tries = 0
                 while t_id in self.tags and tries < 10:
                     t_id = self.random_id()
                     tries += 1
                 # If couldn't find new, or sometimes, pick any random tag id
                 if tries == 10 or random.random() < 0.3:
                     t_id = self.random_id()
                 params = (p_id, t_id)
        elif choice == TAG_EXIST:
            p_id = self._find_existing_person_id()
            t_id = self._find_existing_tag_id()
            if p_id is not None and t_id is not None:
                 params = (p_id, t_id)

        # Fallback to random
        if params is None:
            params = self._generate_random_tag_params()

        person_id, tag_id = params
        operation = OperationAddTag(person_id, tag_id)
        self.operations.append(operation)

        # --- Update internal state ---
        person = self.network.find_person(person_id)
        if person:
            # Get or create the global tag object
            if tag_id in self.tags:
                tag = self.tags[tag_id]
            else:
                tag = Tag(tag_id)
                self.tags[tag_id] = tag

            # Add tag to person and person to tag (if not already linked)
            if tag not in person.tag_list:
                 person.add_tag(tag)
            if person not in tag.personList:
                 tag.add_person(person)


    def add_operation_del_tag(self,
                               valid_percentage: float = 0.8,
                               tag_unexist_percentage: float = 0.1):
        operation : OperationDelTag = None
        params = None
        person_id, tag_id = 0, 0 # Initialize

        VALID = 0 # Delete a tag the person actually has
        TAG_UNEXIST = 1 # Try deleting a tag the person doesn't have (or doesn't exist globally)
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]

        if choice == VALID:
            pair = self._find_person_with_tag()
            if pair:
                 params = pair
        elif choice == TAG_UNEXIST:
            p_id = self._find_existing_person_id()
            if p_id is not None:
                person = self.network.find_person(p_id)
                person_tag_ids = {t.id for t in person.tag_list}
                # Try finding a globally existing tag the person doesn't have
                possible_tag_ids = list(self.tags.keys() - person_tag_ids)
                if possible_tag_ids:
                    t_id = random.choice(possible_tag_ids)
                else:
                    # Or generate a truly non-existent tag ID
                    t_id = self.random_id()
                    while t_id in self.tags:
                         t_id = self.random_id()
                params = (p_id, t_id)

        # Fallback to random
        if params is None:
            params = self._generate_random_tag_params()

        person_id, tag_id = params
        operation = OperationDelTag(person_id, tag_id)
        self.operations.append(operation)

        # --- Update internal state ---
        person = self.network.find_person(person_id)
        tag = self.tags.get(tag_id)
        if person and tag and tag in person.tag_list: # Check if person actually has the tag
            person.remove_tag(tag)
            tag.remove_person(person)
            # Optional: Clean up tag from global registry if no one uses it anymore
            # Note: The spec might not require this, and `dt` only targets one person.
            # if not tag.personList:
            #    del self.tags[tag_id]


    def add_operation_add_to_tag(self,
                                 valid_percentage: float = 0.8,
                                 tag_unexist_percentage: float = 0.1):
        operation : OperationAddToTag = None
        params = None
        id1, id2, tag_id = 0, 0, 0 # Initialize

        VALID = 0 # Add existing person2 to existing tag owned by person1
        TAG_UNEXIST = 1 # Try adding person2 to a non-existent tag via person1
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]

        if choice == VALID:
             found = self._find_person_and_tag_to_add_to()
             if found:
                 params = found
        elif choice == TAG_UNEXIST:
             pair = self._find_two_existing_distinct_person_ids()
             if pair:
                 id1, id2 = pair
                 # Generate a tag ID that doesn't exist
                 t_id = self.random_id()
                 while t_id in self.tags:
                      t_id = self.random_id()
                 params = (id1, id2, t_id)

        # Fallback to random
        if params is None:
            r_id1, r_id2 = self.random_id(), self.random_id()
            while r_id1 == r_id2:
                r_id2 = self.random_id()
            r_tag_id = self.random_id()
            params = (r_id1, r_id2, r_tag_id)

        id1, id2, tag_id = params
        operation = OperationAddToTag(id1, id2, tag_id)
        self.operations.append(operation)

        # --- Update internal state ---
        p1 = self.network.find_person(id1)
        p2 = self.network.find_person(id2)
        tag = self.tags.get(tag_id)

        # Conditions: p1 exists, p2 exists, tag exists, p1 has tag, p1!=p2, p2 not already in tag
        if p1 and p2 and tag and tag in p1.tag_list and id1 != id2 and p2 not in tag.personList:
            tag.add_person(p2)
            p2.add_tag(tag) # Add tag to person2's list as well

    def add_operation_del_from_tag(self,
                                   valid_percentage: float = 0.8,
                                   tag_unexist_percentage: float = 0.1):
        operation : OperationDelFromTag = None
        params = None
        id1, id2, tag_id = 0, 0, 0 # Initialize

        VALID = 0 # Remove existing person2 from tag (owned by p1, p2 is in it)
        TAG_UNEXIST = 1 # Try removing from non-existent tag
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]

        if choice == VALID:
             found = self._find_person_and_tag_to_remove_from()
             if found:
                 params = found
        elif choice == TAG_UNEXIST:
             pair = self._find_two_existing_distinct_person_ids()
             if pair:
                 id1, id2 = pair
                 # Generate a tag ID that doesn't exist
                 t_id = self.random_id()
                 while t_id in self.tags:
                      t_id = self.random_id()
                 params = (id1, id2, t_id)

        # Fallback to random
        if params is None:
            r_id1, r_id2 = self.random_id(), self.random_id()
            while r_id1 == r_id2:
                r_id2 = self.random_id()
            r_tag_id = self.random_id()
            params = (r_id1, r_id2, r_tag_id)

        id1, id2, tag_id = params
        operation = OperationDelFromTag(id1, id2, tag_id)
        self.operations.append(operation)

        # --- Update internal state ---
        p1 = self.network.find_person(id1)
        p2 = self.network.find_person(id2)
        tag = self.tags.get(tag_id)

        # Conditions: p1,p2 exist, tag exists, p1 has tag, p2 is in tag, p1!=p2
        if p1 and p2 and tag and tag in p1.tag_list and p2 in tag.personList and id1 != id2:
            tag.remove_person(p2)
            p2.remove_tag(tag) # Also remove from person2's list
            # Optional: clean up tag if empty? Usually not for dft.


    def add_operation_query_value(self,
                                  valid_percentage: float = 0.8,
                                  relation_unexist_percentage: float = 0.1):
        operation : OperationQueryValue = None
        params = None
        id1, id2 = 0, 0 # Initialize

        VALID = 0 # Query existing relation
        RELATION_UNEXIST = 1 # Query non-existing relation (between existing people)
        RANDOM = 2
        choice = random.choices([VALID, RELATION_UNEXIST, RANDOM], weights=[valid_percentage, relation_unexist_percentage, 1-valid_percentage-relation_unexist_percentage])[0]

        if choice == VALID:
             pair = self._find_existing_relation()
             if pair:
                 params = pair
        elif choice == RELATION_UNEXIST:
             pair = self._find_non_existing_relation_between_existing_persons()
             if pair:
                  params = pair

        # Fallback to random
        if params is None:
            r_id1, r_id2 = self.random_id(), self.random_id()
            while r_id1 == r_id2:
                r_id2 = self.random_id()
            params = (r_id1, r_id2)

        id1, id2 = params
        operation = OperationQueryValue(id1, id2)
        self.operations.append(operation)
        # No state change for queries

    def add_operation_query_circle(self,
                                   valid_percentage: float = 0.8,
                                   relation_unexist_percentage: float = 0.1):
        operation : OperationQueryCircle = None
        params = None
        id1, id2 = 0, 0 # Initialize

        VALID = 0 # Query circle between existing people (relation may or may not exist)
        # RELATION_UNEXIST case is implicitly covered by VALID/RANDOM, as qci checks reachability
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]

        if choice == VALID:
             pair = self._find_two_existing_distinct_person_ids()
             if pair:
                 params = pair

        # Fallback to random
        if params is None:
            r_id1, r_id2 = self.random_id(), self.random_id()
            while r_id1 == r_id2:
                r_id2 = self.random_id()
            params = (r_id1, r_id2)

        id1, id2 = params
        operation = OperationQueryCircle(id1, id2)
        self.operations.append(operation)
        # No state change for queries

    def add_operation_query_triple_sum(self):
        operation = OperationQueryTripleSum()
        self.operations.append(operation)
        # No state change

    def add_operation_query_tag_age_var(self,
                                        valid_percentage: float = 0.8,
                                        tag_unexist_percentage: float = 0.1):
        operation : OperationQueryTagAgeVar = None
        params = None
        person_id, tag_id = 0, 0 # Initialize

        VALID = 0 # Query existing tag via a person who has it
        TAG_UNEXIST = 1 # Query non-existent tag via an existing person
        RANDOM = 2
        choice = random.choices([VALID, TAG_UNEXIST, RANDOM], weights=[valid_percentage, tag_unexist_percentage, 1-valid_percentage-tag_unexist_percentage])[0]

        if choice == VALID:
             pair = self._find_person_with_tag()
             if pair:
                  params = pair
        elif choice == TAG_UNEXIST:
             p_id = self._find_existing_person_id()
             if p_id is not None:
                 # Generate a tag ID that doesn't exist
                 t_id = self.random_id()
                 while t_id in self.tags:
                      t_id = self.random_id()
                 params = (p_id, t_id)

        # Fallback to random
        if params is None:
             params = self._generate_random_tag_params()

        person_id, tag_id = params
        operation = OperationQueryTagAgeVar(person_id, tag_id)
        self.operations.append(operation)
        # No state change

    def add_operation_query_best_acquaintance(self,
                                              valid_percentage: float = 0.9):
        operation : OperationQueryBestAcquaintance = None
        person_id = None

        VALID = 0 # Query existing person
        RANDOM = 1
        choice = random.choices([VALID, RANDOM], weights=[valid_percentage, 1-valid_percentage])[0]

        if choice == VALID:
            p_id = self._find_existing_person_id()
            if p_id is not None:
                 person_id = p_id

        # Fallback to random
        if person_id is None:
            person_id = self.random_id()

        operation = OperationQueryBestAcquaintance(person_id)
        self.operations.append(operation)
        # No state change

    def add_operation_load_network(self):
        # TODO: This requires generating a full network structure.
        # Usually 'ln' is the *first* command, not generated randomly mid-sequence.
        # If needed, implement logic to create lists of people, relations, etc.
        # For now, let's assume it's not called by the random add_operation.
        print("Warning: OperationLoadNetwork generation not fully implemented.")
        # Example placeholder:
        op = OperationLoadNetwork(0, [], [], [], []) 
        self.operations.append(op)
        # Reset internal state if ln is used:
        self.reset()
        # (Need to then populate state based on generated ln args)


    def add_operation(self):
        # Filter out OperationLoadNetwork if it's in weights, as it needs special handling
        available_ops = [op for op in self.weights.keys() if op != OperationLoadNetwork]
        available_weights = [self.weights[op] for op in available_ops]

        operation_type = random.choices(available_ops, weights=available_weights)[0]

        # Call the corresponding add_operation_* method
        if operation_type == OperationAddPerson:
            self.add_operation_add_person()
        elif operation_type == OperationAddRelation:
            self.add_operation_add_relation()
        elif operation_type == OperationModifyRelation:
            self.add_operation_modify_relation()
        elif operation_type == OperationAddTag:
            self.add_operation_add_tag()
        elif operation_type == OperationDelTag:
            self.add_operation_del_tag()
        elif operation_type == OperationAddToTag:
            self.add_operation_add_to_tag()
        elif operation_type == OperationDelFromTag:
            self.add_operation_del_from_tag()
        elif operation_type == OperationQueryValue:
            self.add_operation_query_value()
        elif operation_type == OperationQueryCircle:
            self.add_operation_query_circle()
        elif operation_type == OperationQueryTripleSum:
            self.add_operation_query_triple_sum()
        elif operation_type == OperationQueryTagAgeVar:
            self.add_operation_query_tag_age_var()
        elif operation_type == OperationQueryBestAcquaintance:
            self.add_operation_query_best_acquaintance()
        # No else needed as we excluded OperationLoadNetwork

    @staticmethod
    def random_id(min_id : int = MIN_ID, max_id : int = MAX_ID) -> int:
        return random.randint(min_id, max_id)

    @staticmethod
    def random_name() -> str:
        # Ensure name does not contain spaces for simple parsing
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(1, Generator.MAX_STRING_LEN)))

    @staticmethod
    def random_age(min_age : int = MIN_AGE, max_age : int = MAX_AGE) -> int:
        return random.randint(min_age, max_age)

    @staticmethod
    def random_value(min_value : int = MIN_VALUE, max_value : int = MAX_VALUE) -> int:
        return random.randint(min_value, max_value)

    @staticmethod
    def random_m_val(min_m_val : int = MIN_M_VAL, max_m_val : int = MAX_M_VAL) -> int:
        return random.randint(min_m_val, max_m_val)