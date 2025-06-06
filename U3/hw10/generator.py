import random
import string
import sys

# Assuming objects.py and operation.py are available
try:
    from operation import *
    from objects import *
except ImportError as e:
     print(f"Error importing from operation.py or objects.py: {e}", file=sys.stderr)
     # Cannot proceed without these base classes
     # Define dummy classes to prevent NameErrors if needed for basic script execution
     class Operation: pass
     class Network: pass
     # ... define other dummies if absolutely necessary for script loading
     # sys.exit(1) # Or just exit

class Generator:
    network : Network # Internal model of the network state
    weights : dict[type[Operation], float] # Use type for keys
    operations : list[Operation]
    # Keep track of existing entity IDs using sets for efficiency
    existing_person_ids : set[int]
    existing_tag_ids : set[int] # Global pool of tag IDs *ever created*
    existing_account_ids: set[int]
    existing_article_ids: set[int] # Global pool of article IDs *ever created*
    # Track person-tag ownership {person_id: set(tag_id)}
    person_owned_tags: dict[int, set[int]]
    # Track account-article ownership {account_id: set(article_id)}
    account_owned_articles: dict[int, set[int]]


    # --- Constants ---
    MAX_STRING_LEN = 10
    MIN_ID = 1 # Often IDs are positive
    MAX_ID = 1000 # Range for generating new IDs
    MIN_AGE = 1
    MAX_AGE = 100
    MIN_VALUE = 1
    MAX_VALUE = 100
    MIN_M_VAL = -150 # Allow modification to remove relations
    MAX_M_VAL = 150

    # --- Weights for Operation Selection (Adjust to focus tests) ---
    DEFAULT_ADD_PERSON_WEIGHT = 1
    DEFAULT_ADD_RELATION_WEIGHT = 3
    DEFAULT_MODIFY_RELATION_WEIGHT = 3
    DEFAULT_ADD_TAG_WEIGHT = 1
    DEFAULT_DEL_TAG_WEIGHT = 1
    DEFAULT_ADD_TO_TAG_WEIGHT = 3
    DEFAULT_DEL_FROM_TAG_WEIGHT = 2
    DEFAULT_QUERY_VALUE_WEIGHT = 1
    DEFAULT_QUERY_CIRCLE_WEIGHT = 2 # qci
    DEFAULT_QUERY_TRIPLE_SUM_WEIGHT = 2 # qts
    DEFAULT_QUERY_TAG_AGE_VAR_WEIGHT = 2 # qtav
    DEFAULT_QUERY_BEST_ACQUAINTANCE_WEIGHT = 2 # qba
    # HW12 Additions
    DEFAULT_CREATE_OFFICIAL_ACCOUNT_WEIGHT = 1 # coa
    DEFAULT_DELETE_OFFICIAL_ACCOUNT_WEIGHT = 1 # doa
    DEFAULT_CONTRIBUTE_ARTICLE_WEIGHT = 1      # ca
    DEFAULT_DELETE_ARTICLE_WEIGHT = 1          # da
    DEFAULT_FOLLOW_OFFICIAL_ACCOUNT_WEIGHT = 1 # foa
    DEFAULT_QUERY_SHORTEST_PATH_WEIGHT = 2     # qsp
    DEFAULT_QUERY_BEST_CONTRIBUTOR_WEIGHT = 2  # qbc
    DEAFULT_QUERY_RECEIVED_ARTICLES_WEIGHT = 2 # qra
    DEFAULT_QUERY_TAG_VALUE_SUM_WEIGHT = 2     # qtvs
    DEFAULT_QUERY_COUPLE_SUM_WEIGHT = 2        # qcs
    DEFAULT_LOAD_NETWORK_WEIGHT = 0 # Usually not mixed, set > 0 only for specific LN tests


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
            OperationLoadNetwork: self.DEFAULT_LOAD_NETWORK_WEIGHT,
            # HW12 Additions
            OperationCreateOfficialAccount: self.DEFAULT_CREATE_OFFICIAL_ACCOUNT_WEIGHT,
            OperationDeleteOfficialAccount: self.DEFAULT_DELETE_OFFICIAL_ACCOUNT_WEIGHT,
            OperationContributeArticle: self.DEFAULT_CONTRIBUTE_ARTICLE_WEIGHT,
            OperationDeleteArticle: self.DEFAULT_DELETE_ARTICLE_WEIGHT,
            OperationFollowOfficialAccount: self.DEFAULT_FOLLOW_OFFICIAL_ACCOUNT_WEIGHT,
            OperationQueryShortestPath: self.DEFAULT_QUERY_SHORTEST_PATH_WEIGHT,
            OperationQueryBestContributor: self.DEFAULT_QUERY_BEST_CONTRIBUTOR_WEIGHT,
            OperationQueryReceivedArticles: self.DEAFULT_QUERY_RECEIVED_ARTICLES_WEIGHT,
            OperationQueryTagValueSum: self.DEFAULT_QUERY_TAG_VALUE_SUM_WEIGHT,
            OperationQueryCoupleSum: self.DEFAULT_QUERY_COUPLE_SUM_WEIGHT
        }
        self.network = Network() # Initialize the internal model
        self.reset() # Call reset to initialize tracking sets

    def reset(self):
        """Resets the generator state for a new test case."""
        self.network.reset() # Clear the internal network model
        self.operations = []
        self.existing_person_ids = set()
        self.existing_tag_ids = set()
        self.existing_account_ids = set()
        self.existing_article_ids = set()
        self.person_owned_tags = {}
        self.account_owned_articles = {}

    def get_result(self) -> list[str]:
        """Returns the list of generated operation strings."""
        return [str(op) for op in self.operations]

    def add_operations(self, num_operations: int):
        """Generates a specified number of operations."""
        # Handle Load Network separately if its weight is > 0
        if self.weights.get(OperationLoadNetwork, 0) > 0 and random.random() < 0.1: # Small chance to start with LN
             print("Info: Generating LoadNetwork operation first.")
             self.add_operation_load_network(target_size=num_operations // 10) # Example size
             # LN replaces other ops usually, so we might return here or adjust num_operations
             # For now, let's assume LN replaces all other ops for this testcase
             return
        # Generate other operations
        for _ in range(num_operations):
            self.add_operation()

    # --- Helper methods for picking entities ---

    def _get_random_existing_person_id(self) -> int | None:
        """Returns a random existing person ID, or None if none exist."""
        return random.choice(list(self.existing_person_ids)) if self.existing_person_ids else None

    def _get_two_random_existing_person_ids(self) -> tuple[int | None, int | None]:
        """Returns two different existing person IDs, or Nones if not enough."""
        if len(self.existing_person_ids) < 2:
            p_list = list(self.existing_person_ids)
            return (p_list[0] if p_list else None, None)
        id1, id2 = random.sample(list(self.existing_person_ids), 2)
        return id1, id2

    def _get_random_new_person_id(self) -> int:
        """Generates a person ID guaranteed not to exist currently."""
        new_id = self.random_id()
        while new_id in self.existing_person_ids:
            new_id = self.random_id()
        return new_id

    def _get_random_existing_tag_id(self) -> int | None:
        """Returns a random tag ID that has been created."""
        return random.choice(list(self.existing_tag_ids)) if self.existing_tag_ids else None

    def _get_random_new_tag_id(self) -> int:
        """Generates a tag ID guaranteed not to have been used yet."""
        new_id = self.random_id(max_id=self.MAX_ID + 1000) # Use slightly different range maybe
        while new_id in self.existing_tag_ids:
            new_id = self.random_id(max_id=self.MAX_ID + 1000)
        return new_id

    def _get_random_person_owned_tag(self) -> tuple[int, int] | None:
         """Returns a random (person_id, tag_id) pair that exists."""
         valid_owners = [pid for pid, tags in self.person_owned_tags.items() if tags]
         if not valid_owners: return None
         owner_id = random.choice(valid_owners)
         tag_id = random.choice(list(self.person_owned_tags[owner_id]))
         return owner_id, tag_id

    def _get_random_existing_account_id(self) -> int | None:
        return random.choice(list(self.existing_account_ids)) if self.existing_account_ids else None

    def _get_random_new_account_id(self) -> int:
        new_id = self.random_id()
        while new_id in self.existing_account_ids or new_id in self.existing_person_ids:
            new_id = self.random_id()
        return new_id

    def _get_random_existing_article_id(self) -> int | None:
        return random.choice(list(self.existing_article_ids)) if self.existing_article_ids else None

    def _get_random_new_article_id(self) -> int:
        new_id = self.random_id(max_id=self.MAX_ID + 2000)
        while new_id in self.existing_article_ids or new_id in self.existing_person_ids or new_id in self.existing_account_ids:
            new_id = self.random_id(max_id=self.MAX_ID + 2000)
        return new_id

    def _get_random_account_owned_article(self) -> tuple[int, int] | None:
         """Returns a random (account_id, article_id) pair that exists."""
         valid_accounts = [aid for aid, articles in self.account_owned_articles.items() if articles]
         if not valid_accounts: return None
         account_id = random.choice(valid_accounts)
         article_id = random.choice(list(self.account_owned_articles[account_id]))
         return account_id, article_id

    # --- Operation Generation Methods ---
    # These methods generate parameters, create the Operation object,
    # update the internal model *if applicable*, and append the operation.

    def add_operation_add_person(self, new_person_percentage: float = 0.9):
        pid, name, age = -1, "", -1
        op = None

        # Decide whether to generate a command for a new ID or an existing one (tests duplicate add)
        if random.random() < new_person_percentage or not self.existing_person_ids:
            # Generate new person details
            pid = self._get_random_new_person_id()
            name = self.random_name()
            age = self.random_age()
            # Try adding to internal model
            try:
                 person = Person(pid, name, age)
                 if self.network.add_person(person):
                     self.existing_person_ids.add(pid)
                     self.person_owned_tags[pid] = set() # Initialize owned tags set
                     # print(f"Gen: Added Person {pid}") # Debug
                 # Create operation regardless of model success (might be duplicate ID)
                 op = OperationAddPerson(pid, name, age)
            except TypeError as e:
                 print(f"Warning: Invalid person data generated ({pid}, {name}, {age}): {e}", file=sys.stderr)
                 # Fallback: generate completely random invalid data? Or skip? Skip for now.
                 return
        else:
            # Generate command targeting an existing person ID
            existing_pid = self._get_random_existing_person_id()
            # Fetch details from model *if* it exists, otherwise generate random
            p = self.network.find_person(existing_pid) if existing_pid is not None else None
            if p:
                op = OperationAddPerson(p.id, p.name, p.age)
            else: # Should not happen if existing_pid is not None, but fallback
                 pid = self.random_id() # Make up an ID
                 name = self.random_name()
                 age = self.random_age()
                 op = OperationAddPerson(pid, name, age)

        if op: self.operations.append(op)


    def add_operation_add_relation(self, new_relation_percentage: float = 0.8):
        pid1, pid2 = self._get_two_random_existing_person_ids()
        value = self.random_value()
        op = None

        if pid1 is None or pid2 is None: # Not enough people
             # Generate random IDs (likely invalid command)
             rand_id1 = self.random_id()
             rand_id2 = self.random_id()
             while rand_id1 == rand_id2: rand_id2 = self.random_id()
             op = OperationAddRelation(rand_id1, rand_id2, value)
        elif random.random() < new_relation_percentage and not self.network.has_relation(pid1, pid2):
            # Try adding a valid new relation to the model
            self.network.add_relation(pid1, pid2, value) # Update model (ignore success/fail here)
            op = OperationAddRelation(pid1, pid2, value)
        else:
            # Generate command targeting existing relation (test duplicate add) or random pair
            # Let's favour targeting existing if possible
            if self.network.has_relation(pid1, pid2):
                op = OperationAddRelation(pid1, pid2, value) # Target existing
            else:
                # Target potentially non-existent pair using existing IDs
                op = OperationAddRelation(pid1, pid2, value)

        if op: self.operations.append(op)


    def add_operation_modify_relation(self, modify_existing_percentage: float = 0.85):
        pid1, pid2 = -1, -1
        mod_value = self.random_m_val()
        op = None

        # Find existing relations
        existing_relations = []
        for p1_id in self.existing_person_ids:
            p1 = self.network.find_person(p1_id)
            if p1:
                for p2_obj in p1.acquaintances: # Iterate through Person objects directly
                    if p1.id < p2_obj.id: # Add canonically
                        existing_relations.append((p1.id, p2_obj.id))

        # Decide target
        if existing_relations and random.random() < modify_existing_percentage:
            # Target an existing relation
            pid1, pid2 = random.choice(existing_relations)
            # Update model (Network's modify_relation handles removal if value <= 0)
            self.network.modify_relation(pid1, pid2, mod_value)
            op = OperationModifyRelation(pid1, pid2, mod_value)
        else:
            # Target non-existent or random relation
            t_pid1, t_pid2 = self._get_two_random_existing_person_ids()
            if t_pid1 is None or t_pid2 is None: # Not enough people
                 pid1 = self.random_id()
                 pid2 = self.random_id()
                 while pid1 == pid2: pid2 = self.random_id()
            else:
                 # Ensure we target a non-existing relation if possible
                 if self.network.has_relation(t_pid1, t_pid2) and len(self.existing_person_ids) >= 3:
                      # Try to find a non-related pair
                      found_non_related = False
                      for _ in range(5): # Try a few times
                           p1_try, p2_try = self._get_two_random_existing_person_ids()
                           if p1_try and p2_try and not self.network.has_relation(p1_try, p2_try):
                                pid1, pid2 = p1_try, p2_try
                                found_non_related = True
                                break
                      if not found_non_related: # Fallback if couldn't find non-related
                          pid1, pid2 = t_pid1, t_pid2
                 else:
                      pid1, pid2 = t_pid1, t_pid2 # Use the pair (might be non-related already)

            op = OperationModifyRelation(pid1, pid2, mod_value)

        if op: self.operations.append(op)


    def add_operation_add_tag(self, valid_percentage: float = 0.9):
        person_id = self._get_random_existing_person_id()
        tag_id = -1
        op = None

        if person_id is None: # No people exist
             op = OperationAddTag(self.random_id(), self.random_id())
        elif random.random() < valid_percentage:
             # Add a new tag ID for this person
             tag_id = self._get_random_new_tag_id()
             new_tag = Tag(tag_id)
             if self.network.add_tag(person_id, new_tag):
                 self.existing_tag_ids.add(tag_id) # Add to global pool
                 self.person_owned_tags[person_id].add(tag_id) # Track ownership
             op = OperationAddTag(person_id, tag_id)
        else:
             # Add an existing tag ID (tests duplicate add for this person, or using another tag's ID)
             tag_id = self._get_random_existing_tag_id()
             if tag_id is None: # No existing tags yet, create new instead
                 tag_id = self._get_random_new_tag_id()
                 new_tag = Tag(tag_id)
                 if self.network.add_tag(person_id, new_tag):
                     self.existing_tag_ids.add(tag_id)
                     self.person_owned_tags[person_id].add(tag_id)
             else:
                 # Try adding; model handles if person already owns this tag ID
                 tag_obj_for_add = Tag(tag_id) # Use a temporary object
                 if self.network.add_tag(person_id, tag_obj_for_add):
                      self.person_owned_tags[person_id].add(tag_id) # Track ownership if added

             op = OperationAddTag(person_id, tag_id)

        if op: self.operations.append(op)


    def add_operation_del_tag(self, valid_percentage: float = 0.85):
        person_id, tag_id = -1, -1
        op = None
        owned_tag_pair = self._get_random_person_owned_tag()

        if owned_tag_pair and random.random() < valid_percentage:
            # Target deleting a tag the person actually owns
            person_id, tag_id = owned_tag_pair
            tag_obj_to_del = Tag(tag_id) # Need object for network.del_tag
            if self.network.del_tag(person_id, tag_obj_to_del):
                 if person_id in self.person_owned_tags:
                      self.person_owned_tags[person_id].discard(tag_id)
                 # Don't remove from global existing_tag_ids easily
            op = OperationDelTag(person_id, tag_id)
        else:
            # Target non-existent person, non-existent tag, or tag not owned by person
            if random.random() < 0.3 and self.existing_person_ids:
                 person_id = self._get_random_existing_person_id()
                 tag_id = self._get_random_new_tag_id() # Tag doesn't exist
            elif random.random() < 0.6 and owned_tag_pair:
                 # Pick existing person and existing tag, but likely not owned by them
                 person_id = self._get_random_existing_person_id()
                 tag_id = self._get_random_existing_tag_id()
                 if person_id is None: person_id = self.random_id()
                 if tag_id is None: tag_id = self.random_id()
                 # Ensure it's likely not owned
                 if person_id in self.person_owned_tags and tag_id in self.person_owned_tags[person_id]:
                      tag_id = self._get_random_new_tag_id() # Change tag to non-existent
            else:
                 person_id = self.random_id() # Non-existent person
                 tag_id = self.random_id()    # Non-existent tag

            op = OperationDelTag(person_id, tag_id)

        if op: self.operations.append(op)


    def add_operation_add_to_tag(self, valid_percentage: float = 0.8):
        pid1, pid2, tag_id = -1, -1, -1 # owner, person_to_add, tag
        op = None

        # Find potential valid candidates (owner, related_person, owned_tag)
        # where related_person is not already in the tag's list.
        candidates = []
        for p1_id in self.person_owned_tags: # Iterate owner IDs
             p1 = self.network.find_person(p1_id)
             if not p1: continue
             owned_tags = self.person_owned_tags[p1_id]
             if not owned_tags: continue

             for tag_obj in p1.tag_list: # Get actual Tag objects
                 for p2_acquaintance in p1.acquaintances: # Get related people
                      if not tag_obj.has_person(p2_acquaintance):
                           candidates.append((p1_id, p2_acquaintance.id, tag_obj.id))

        if candidates and random.random() < valid_percentage:
             pid1, pid2, tag_id = random.choice(candidates)
             self.network.add_person_to_tag(pid1, pid2, tag_id) # Update model
             op = OperationAddToTag(pid1, pid2, tag_id)
        else:
            # Generate invalid or random
            t_pid1 = self._get_random_existing_person_id()
            t_pid2 = self._get_random_existing_person_id()
            t_tag_id = self._get_random_existing_tag_id() # Could be valid or not owned

            if t_pid1 is None or t_pid2 is None: # Not enough people
                 pid1, pid2 = self.random_id(), self.random_id()
                 tag_id = self.random_id()
            elif t_pid1 == t_pid2: # Cannot add self
                 pid1 = t_pid1
                 pid2 = self.random_id()
                 tag_id = t_tag_id if t_tag_id is not None else self.random_id()
            else:
                 pid1, pid2, tag_id = t_pid1, t_pid2, t_tag_id
                 # Make invalid: non-related, tag not owned, already in tag?
                 if random.random() < 0.5 and self.network.has_relation(pid1, pid2):
                      # Try finding unrelated pair
                      unrelated_p2_id = self._get_random_existing_person_id()
                      if unrelated_p2_id and pid1 != unrelated_p2_id and not self.network.has_relation(pid1, unrelated_p2_id):
                           pid2 = unrelated_p2_id
                 elif random.random() < 0.7 and tag_id is not None:
                      # Use tag not owned by pid1
                      if pid1 not in self.person_owned_tags or tag_id not in self.person_owned_tags[pid1]:
                            pass # Already not owned or pid1 has no tags
                      else: # pid1 owns tag_id, try finding another tag
                           other_tag = self._get_random_existing_tag_id()
                           if other_tag and other_tag != tag_id and other_tag not in self.person_owned_tags.get(pid1, set()):
                                tag_id = other_tag
                           else: # Or just use a new tag ID
                                tag_id = self._get_random_new_tag_id()

                 if tag_id is None: tag_id = self.random_id() # Ensure tag_id is set

            op = OperationAddToTag(pid1, pid2, tag_id)

        if op: self.operations.append(op)


    def add_operation_del_from_tag(self, valid_percentage: float = 0.8):
        pid1, pid2, tag_id = -1, -1, -1 # owner, person_to_remove, tag
        op = None

        # Find potential valid candidates (owner, person_in_tag, tag_id)
        candidates = []
        for p1_id in self.person_owned_tags:
             p1 = self.network.find_person(p1_id)
             if not p1: continue
             for tag_obj in p1.tag_list: # Get actual Tag objects
                 for p2_in_tag in tag_obj.personList: # Get people in tag
                      candidates.append((p1_id, p2_in_tag.id, tag_obj.id))

        if candidates and random.random() < valid_percentage:
             pid1, pid2, tag_id = random.choice(candidates)
             self.network.del_person_from_tag(pid1, pid2, tag_id) # Update model
             op = OperationDelFromTag(pid1, pid2, tag_id)
        else:
            # Generate invalid or random
            owned_tag_pair = self._get_random_person_owned_tag()
            if owned_tag_pair:
                 pid1, tag_id = owned_tag_pair
                 # Find someone *not* in the tag
                 p1_obj = self.network.find_person(pid1)
                 tag_obj = p1_obj.find_tag(tag_id) if p1_obj else None
                 if tag_obj:
                      # Pick random existing person, likely not in tag
                      pid2 = self._get_random_existing_person_id()
                      if pid2 is None or pid2 == pid1: pid2 = self.random_id() # Fallback
                      # Ensure pid2 is likely not in tag
                      p2_obj = self.network.find_person(pid2)
                      if p2_obj and tag_obj.has_person(p2_obj):
                           pid2 = self.random_id() # If by chance they were in, use random
                 else: # Tag object not found in model (shouldn't happen if owned_tag_pair is valid)
                      pid2 = self.random_id()
            else: # No owned tags exist
                 pid1 = self._get_random_existing_person_id()
                 pid2 = self._get_random_existing_person_id()
                 tag_id = self._get_random_existing_tag_id()
                 # Fill Nones with random
                 if pid1 is None: pid1 = self.random_id()
                 if pid2 is None: pid2 = self.random_id()
                 if tag_id is None: tag_id = self.random_id()

            op = OperationDelFromTag(pid1, pid2, tag_id)

        if op: self.operations.append(op)

    # --- Query Operations (Generally don't modify state) ---

    def add_operation_query_value(self, valid_percentage: float = 0.9):
        pid1, pid2 = -1, -1
        if random.random() < valid_percentage:
            pid1, pid2 = self._get_two_random_existing_person_ids()
            if pid1 is None or pid2 is None: # Fallback if not enough people
                 pid1, pid2 = self.random_id(), self.random_id()
        else:
             pid1, pid2 = self.random_id(), self.random_id()
        op = OperationQueryValue(pid1, pid2)
        self.operations.append(op)

    def add_operation_query_circle(self, valid_percentage: float = 0.9): # qci
        pid1, pid2 = -1, -1
        if random.random() < valid_percentage:
            pid1, pid2 = self._get_two_random_existing_person_ids()
            if pid1 is None or pid2 is None:
                 pid1, pid2 = self.random_id(), self.random_id()
        else:
             pid1, pid2 = self.random_id(), self.random_id()
        # Ensure pid1 != pid2 for query
        while pid1 == pid2: pid2 = self.random_id()
        op = OperationQueryCircle(pid1, pid2)
        self.operations.append(op)

    def add_operation_query_triple_sum(self): # qts
        op = OperationQueryTripleSum()
        self.operations.append(op)

    def add_operation_query_tag_age_var(self, valid_percentage: float = 0.9): # qtav
        person_id, tag_id = -1, -1
        owned_tag_pair = self._get_random_person_owned_tag()

        if owned_tag_pair and random.random() < valid_percentage:
            person_id, tag_id = owned_tag_pair
        else: # Target non-existent or random
            person_id = self._get_random_existing_person_id()
            tag_id = self._get_random_existing_tag_id()
            if person_id is None: person_id = self.random_id()
            if tag_id is None: tag_id = self.random_id()
            # Make more likely invalid
            if person_id in self.person_owned_tags and tag_id in self.person_owned_tags.get(person_id, set()):
                 tag_id = self._get_random_new_tag_id() # Use tag not owned

        op = OperationQueryTagAgeVar(person_id, tag_id)
        self.operations.append(op)

    def add_operation_query_best_acquaintance(self, valid_percentage: float = 0.9): # qba
        person_id = -1
        if self.existing_person_ids and random.random() < valid_percentage:
            person_id = self._get_random_existing_person_id()
        else:
             person_id = self.random_id() # Target non-existent person
        op = OperationQueryBestAcquaintance(person_id)
        self.operations.append(op)

    def add_operation_load_network(self, target_size=50): # ln
        """Generates a single Load Network operation, replacing others."""
        print(f"Info: Generating OperationLoadNetwork with target size {target_size}...")
        person_count = max(1, target_size) # Ensure at least one person
        ids, names, ages = [], [], []
        relations_map = {i: [] for i in range(person_count)} # {index: [(neighbor_idx, val), ...]}

        # Generate people
        temp_ids = set()
        for _ in range(person_count):
            pid = self._get_random_new_person_id()
            while pid in temp_ids: pid = self._get_random_new_person_id()
            ids.append(pid)
            temp_ids.add(pid)
            names.append(self.random_name())
            ages.append(self.random_age())

        # Generate relations (e.g., Erdos-Renyi model)
        edge_prob = 0.1 # Probability of an edge between any two nodes
        for i in range(person_count):
            for j in range(i + 1, person_count):
                if random.random() < edge_prob:
                    value = self.random_value()
                    relations_map[i].append((j, value))
                    relations_map[j].append((i, value))

        # Format relations_data: list of lists [person_id, n1_id, v1, n2_id, v2, ...]
        relations_data_formatted = []
        for i in range(person_count):
            line = [ids[i]]
            for neighbor_idx, value in relations_map[i]:
                line.append(ids[neighbor_idx])
                line.append(value)
            relations_data_formatted.append(line)

        # Create the operation
        op = OperationLoadNetwork(person_count, ids, names, ages, relations_data_formatted)

        # Update the generator's internal model to match
        if self.network.load_network(ids, names, ages, relations_data_formatted):
            # Update tracking sets
            self.existing_person_ids = set(ids)
            self.existing_tag_ids = set() # LN clears tags, accounts etc.
            self.existing_account_ids = set()
            self.existing_article_ids = set()
            self.person_owned_tags = {pid: set() for pid in ids}
            self.account_owned_articles = {}
            print("Info: Internal network model updated after LoadNetwork.")
        else:
            print("Error: Failed to update internal network model after LoadNetwork.", file=sys.stderr)
            self.reset() # Reset generator state if internal load failed

        self.operations = [op] # Replace all previous operations


    def add_operation_create_official_account(self, valid_percentage: float = 0.9): # coa
        owner_id = self._get_random_existing_person_id()
        account_id = -1
        account_name = self.random_name()
        op = None

        if owner_id is None: # Cannot create if no potential owner
             op = OperationCreateOfficialAccount(self.random_id(), self.random_id(), account_name)
        elif random.random() < valid_percentage:
             account_id = self._get_random_new_account_id()
             new_account = OfficialAccount(owner_id, account_id, account_name)
             if self.network.add_official_account(new_account):
                 self.existing_account_ids.add(account_id)
                 self.account_owned_articles[account_id] = set() # Init owned articles
             op = OperationCreateOfficialAccount(owner_id, account_id, account_name)
        else: # Invalid: existing account ID or non-existent owner
             if random.random() < 0.5 and self.existing_account_ids:
                 account_id = self._get_random_existing_account_id() # Use existing ID
             else:
                 account_id = self._get_random_new_account_id()
                 owner_id = self.random_id() # Use non-existent owner ID
             op = OperationCreateOfficialAccount(owner_id, account_id, account_name)

        if op: self.operations.append(op)


    def add_operation_delete_official_account(self, valid_percentage: float = 0.9): # doa
        account_id = -1
        person_id = -1
        op = None
        existing_account_id = self._get_random_existing_account_id()
        existing_person_id = self._get_random_existing_person_id()

        if existing_account_id and random.random() < valid_percentage:
            account_id = existing_account_id
            person_id = existing_person_id
            if self.network.delete_official_account(account_id):
                 self.existing_account_ids.discard(account_id)
                 if account_id in self.account_owned_articles:
                      # Remove associated articles from global pool too? Maybe not necessary.
                      del self.account_owned_articles[account_id]
            # Create operation using the account ID (constructor takes only ID)
            op = OperationDeleteOfficialAccount(person_id, account_id)
        else: # Target non-existent account ID
            account_id = self._get_random_new_account_id()
            op = OperationDeleteOfficialAccount(person_id, account_id)

        if op: self.operations.append(op)


    def add_operation_contribute_article(self, valid_percentage: float = 0.85): # ca
        person_id = self._get_random_existing_person_id() # Contributor
        account_id = self._get_random_existing_account_id()
        article_id = -1
        op = None
        # article_name = self.random_name() # If name needed by model/op

        if person_id is None or account_id is None: # Need person and account
             op = OperationContributeArticle(self.random_id(), self.random_id(), self.random_id())
        elif random.random() < valid_percentage:
             article_id = self._get_random_new_article_id()
             # Model update: Add article ID to account's list
             if self.network.contribute_article(account_id, article_id):
                  self.existing_article_ids.add(article_id)
                  self.account_owned_articles.setdefault(account_id, set()).add(article_id)
             op = OperationContributeArticle(person_id, account_id, article_id)
        else: # Invalid: non-existent account, existing article ID, non-existent person
            if random.random() < 0.4:
                account_id = self._get_random_new_account_id() # Target non-existent account
            elif random.random() < 0.7 and self.existing_article_ids:
                article_id = self._get_random_existing_article_id() # Use existing article ID
            else:
                person_id = self.random_id() # Use non-existent person
            if article_id == -1: article_id = self._get_random_new_article_id() # Ensure article ID is set
            op = OperationContributeArticle(person_id, account_id, article_id)

        if op: self.operations.append(op)


    def add_operation_delete_article(self, valid_percentage: float = 0.85): # da
        person_id, account_id, article_id = -1, -1, -1
        op = None
        owned_article_pair = self._get_random_account_owned_article()

        if owned_article_pair and random.random() < valid_percentage:
             # Target deleting an article owned by an account
             account_id, article_id = owned_article_pair
             account_obj = self.network.find_official_account(account_id)
             # Use owner ID for the command string
             person_id = account_obj.ownerId if account_obj else self.random_id()

             if self.network.delete_article(account_id, article_id):
                  # Update tracking (don't remove from global easily)
                  if account_id in self.account_owned_articles:
                       self.account_owned_articles[account_id].discard(article_id)
             op = OperationDeleteArticle(person_id, account_id, article_id)
        else: # Invalid: non-existent article/account, wrong owner?
            account_id = self._get_random_existing_account_id()
            article_id = self._get_random_existing_article_id()
            person_id = self._get_random_existing_person_id() # Potentially wrong owner

            if account_id is None or article_id is None or person_id is None: # Make random if needed
                account_id = self.random_id() if account_id is None else account_id
                article_id = self.random_id() if article_id is None else article_id
                person_id = self.random_id() if person_id is None else person_id
            else: # Make invalid more likely
                if random.random() < 0.4:
                    article_id = self._get_random_new_article_id() # Non-existent article
                elif random.random() < 0.7:
                    acc = self.network.find_official_account(account_id)
                    if acc and acc.ownerId != person_id: pass # Already wrong owner
                    else: person_id = self.random_id() # Make owner invalid

            op = OperationDeleteArticle(person_id, account_id, article_id)

        if op: self.operations.append(op)


    def add_operation_follow_official_account(self, valid_percentage: float = 0.9): # foa
        person_id = self._get_random_existing_person_id()
        account_id = self._get_random_existing_account_id()
        op = None

        if person_id is None or account_id is None: # Need both entities
             op = OperationFollowOfficialAccount(self.random_id(), self.random_id())
        elif random.random() < valid_percentage:
             # Try following; model handles if already following
             self.network.follow_official_account(person_id, account_id)
             op = OperationFollowOfficialAccount(person_id, account_id)
        else: # Invalid: non-existent person/account
             if random.random() < 0.5: person_id = self.random_id()
             else: account_id = self._get_random_new_account_id()
             op = OperationFollowOfficialAccount(person_id, account_id)

        if op: self.operations.append(op)


    def add_operation_query_shortest_path(self, valid_percentage: float = 0.9): # qsp
        pid1, pid2 = -1, -1
        if random.random() < valid_percentage:
            pid1, pid2 = self._get_two_random_existing_person_ids()
            if pid1 is None or pid2 is None:
                 pid1, pid2 = self.random_id(), self.random_id()
        else:
             pid1, pid2 = self.random_id(), self.random_id()
        while pid1 == pid2: pid2 = self.random_id() # Ensure different IDs
        op = OperationQueryShortestPath(pid1, pid2)
        self.operations.append(op)


    def add_operation_query_best_contributor(self, valid_percentage: float = 0.9): # qbc
        account_id = -1
        if self.existing_account_ids and random.random() < valid_percentage:
            account_id = self._get_random_existing_account_id()
        else:
             account_id = self.random_id() # Target non-existent account
        op = OperationQueryBestContributor(account_id)
        self.operations.append(op)


    def add_operation_query_received_articles(self, valid_percentage: float = 0.9): # qra
        person_id = -1
        if self.existing_person_ids and random.random() < valid_percentage:
            person_id = self._get_random_existing_person_id()
        else:
             person_id = self.random_id() # Target non-existent person
        op = OperationQueryReceivedArticles(person_id)
        self.operations.append(op)


    def add_operation_query_tag_value_sum(self,valid_percentage: float = 0.9): # qtvs
        person_id, tag_id = -1, -1
        owned_tag_pair = self._get_random_person_owned_tag()

        if owned_tag_pair and random.random() < valid_percentage:
            person_id, tag_id = owned_tag_pair
        else: # Target non-existent or random
            person_id = self._get_random_existing_person_id()
            tag_id = self._get_random_existing_tag_id()
            if person_id is None: person_id = self.random_id()
            if tag_id is None: tag_id = self.random_id()
            # Make more likely invalid
            if person_id in self.person_owned_tags and tag_id in self.person_owned_tags.get(person_id, set()):
                 tag_id = self._get_random_new_tag_id() # Use tag not owned

        op = OperationQueryTagValueSum(person_id, tag_id)
        self.operations.append(op)


    def add_operation_query_couple_sum(self): # qcs
        op = OperationQueryCoupleSum()
        self.operations.append(op)

    # --- Main Dispatcher ---

    def add_operation(self):
        """Chooses and generates the next operation based on weights and feasibility."""
        possible_ops = []
        current_weights = []
        num_persons = len(self.existing_person_ids)
        num_accounts = len(self.existing_account_ids)
        # Check complex conditions
        has_relations = any(p.acquaintances for p in self.network.person_map.values())
        has_person_tags = any(tags for tags in self.person_owned_tags.values())
        has_people_in_tags = any(t.personList for p in self.network.person_map.values() for t in p.tag_list)
        has_articles_in_accounts = any(arts for arts in self.account_owned_articles.values())

        # Filter operations based on prerequisites
        for op_type, weight in self.weights.items():
            if weight <= 0: continue # Skip ops with zero weight

            prereq_met = True
            # Add checks based on minimum requirements for *potentially valid* generation
            if op_type in [OperationAddRelation, OperationModifyRelation, OperationQueryCircle, OperationQueryShortestPath, OperationAddToTag, OperationDelFromTag]:
                if num_persons < 2: prereq_met = False
            elif op_type in [OperationAddTag, OperationDelTag, OperationQueryTagAgeVar, OperationQueryBestAcquaintance, OperationQueryReceivedArticles, OperationQueryTagValueSum, OperationCreateOfficialAccount, OperationFollowOfficialAccount, OperationContributeArticle, OperationDeleteArticle]:
                 if num_persons < 1: prereq_met = False
            # Checks for operations requiring existing complex states
            elif op_type == OperationModifyRelation:
                 if not has_relations: pass # Allow generating invalid MR
            elif op_type == OperationDelTag:
                 if not has_person_tags: pass # Allow invalid DT
            elif op_type == OperationAddToTag:
                 # Need owner, related person, and owned tag
                 if not has_relations or not has_person_tags: pass # Allow invalid ATT
            elif op_type == OperationDelFromTag:
                 if not has_people_in_tags: pass # Allow invalid DFT
            elif op_type == OperationDeleteOfficialAccount:
                 if num_accounts < 1: pass # Allow invalid DOA
            elif op_type == OperationContributeArticle:
                 if num_persons < 1 or num_accounts < 1: prereq_met = False
            elif op_type == OperationDeleteArticle:
                 if not has_articles_in_accounts: pass # Allow invalid DA
            elif op_type == OperationFollowOfficialAccount:
                 if num_persons < 1 or num_accounts < 1: prereq_met = False
            elif op_type == OperationQueryBestContributor:
                 if num_accounts < 1: pass # Allow query on non-existent account
            elif op_type == OperationLoadNetwork:
                 # Usually handled separately, but include if weight > 0
                 pass # No prereqs for generating the command itself


            if prereq_met:
                possible_ops.append(op_type)
                current_weights.append(weight)

        if not possible_ops:
             # Fallback: If nothing else possible, usually means no people yet. Add one.
             # print("Warning: No possible operations based on current state, forcing AddPerson.")
             self.add_operation_add_person()
             return

        # Choose operation type from possible ones
        try:
            operation_type = random.choices(possible_ops, weights=current_weights)[0]
        except IndexError: # Should not happen if possible_ops is not empty
             print("Error: random.choices failed unexpectedly. Forcing AddPerson.", file=sys.stderr)
             self.add_operation_add_person()
             return


        # --- Call the corresponding generation method ---
        method_map = {
            OperationAddPerson: self.add_operation_add_person,
            OperationAddRelation: self.add_operation_add_relation,
            OperationModifyRelation: self.add_operation_modify_relation,
            OperationAddTag: self.add_operation_add_tag,
            OperationDelTag: self.add_operation_del_tag,
            OperationAddToTag: self.add_operation_add_to_tag,
            OperationDelFromTag: self.add_operation_del_from_tag,
            OperationQueryValue: self.add_operation_query_value,
            OperationQueryCircle: self.add_operation_query_circle,
            OperationQueryTripleSum: self.add_operation_query_triple_sum,
            OperationQueryTagAgeVar: self.add_operation_query_tag_age_var,
            OperationQueryBestAcquaintance: self.add_operation_query_best_acquaintance,
            OperationLoadNetwork: self.add_operation_load_network,
            OperationCreateOfficialAccount: self.add_operation_create_official_account,
            OperationDeleteOfficialAccount: self.add_operation_delete_official_account,
            OperationContributeArticle: self.add_operation_contribute_article,
            OperationDeleteArticle: self.add_operation_delete_article,
            OperationFollowOfficialAccount: self.add_operation_follow_official_account,
            OperationQueryShortestPath: self.add_operation_query_shortest_path,
            OperationQueryBestContributor: self.add_operation_query_best_contributor,
            OperationQueryReceivedArticles: self.add_operation_query_received_articles,
            OperationQueryTagValueSum: self.add_operation_query_tag_value_sum,
            OperationQueryCoupleSum: self.add_operation_query_couple_sum
        }

        generation_method = method_map.get(operation_type)

        if generation_method:
            try:
                generation_method()
            except Exception as e:
                 # Catch errors during generation of a specific operation type
                 print(f"\nError generating operation of type {operation_type.__name__}: {e}", file=sys.stderr)
                 # Optionally print traceback:
                 # import traceback
                 # traceback.print_exc()
                 print("Attempting fallback: Add Person", file=sys.stderr)
                 try:
                     self.add_operation_add_person()
                 except Exception as fallback_e:
                     print(f"Error during fallback Add Person: {fallback_e}", file=sys.stderr)
                     # If even adding a person fails, something is very wrong
                     print("Cannot generate further operations. Stopping.", file=sys.stderr)
                     # We might want to stop the whole test case generation here
                     # Or just log and hope the next add_operation call works
                     pass
        else:
            # This should not happen if method_map is complete
            print(f"Error: No generation method found for {operation_type.__name__}. Forcing AddPerson.", file=sys.stderr)
            self.add_operation_add_person()


    # --- Static Utility Methods ---

    @staticmethod
    def random_id(min_id : int = MIN_ID, max_id : int = MAX_ID) -> int:
        return random.randint(min_id, max_id)

    @staticmethod
    def random_name() -> str:
        """Generates a random name (letters only)."""
        length = random.randint(3, Generator.MAX_STRING_LEN)
        # Use letters only, maybe start with uppercase
        first_char = random.choice(string.ascii_uppercase)
        rest_chars = ''.join(random.choices(string.ascii_lowercase, k=length-1))
        return first_char + rest_chars

    @staticmethod
    def random_age(min_age : int = MIN_AGE, max_age : int = MAX_AGE) -> int:
        return random.randint(min_age, max_age)

    @staticmethod
    def random_value(min_value : int = MIN_VALUE, max_value : int = MAX_VALUE) -> int:
        return random.randint(min_value, max_value)

    @staticmethod
    def random_m_val(min_m_val : int = MIN_M_VAL, max_m_val : int = MAX_M_VAL) -> int:
        return random.randint(min_m_val, max_m_val)