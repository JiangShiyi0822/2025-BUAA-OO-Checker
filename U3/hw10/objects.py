from __future__ import annotations # Allow type hinting with the class itself
import math # For variance calculation
import sys

class Person:
    id : int
    name : str
    age : int
    tag_list : list[Tag] # Stores Tag objects *owned* by this person
    # Use dict for acquaintances for faster lookup and value storage
    # Key: acquaintance Person object, Value: relation value
    acquaintances : dict[Person, int]

    def __init__(self, id: int, name: str, age: int):
        if not isinstance(id, int): raise TypeError("Person ID must be an integer")
        if not isinstance(name, str): raise TypeError("Person name must be a string")
        if not isinstance(age, int) or age <= 0: raise TypeError("Person age must be a positive integer")
        self.id = id
        self.name = name
        self.age = age
        self.tag_list = []
        self.acquaintances = {} # Use dict {Person: value}

    def __str__(self):
        tagIdList = sorted([tag.id for tag in self.tag_list])
        # Sort acquaintances by ID for consistent output
        acquaintanceInfo = sorted([(p.id, v) for p, v in self.acquaintances.items()], key=lambda item: item[0])
        return f"Person(id={self.id}, name={self.name}, age={self.age}, tagIdList={tagIdList}, acquaintances={acquaintanceInfo})"

    def __eq__(self, other):
        # Two persons are equal if they have the same ID
        return isinstance(other, Person) and self.id == other.id

    def __hash__(self):
        # Hash based on ID, required for using Person objects as dict keys or in sets
        return hash(self.id)

    def add_tag(self, tag: Tag) -> bool:
        """Adds a tag to the person's owned tags if not already present by ID."""
        if not isinstance(tag, Tag): return False
        # Check if a tag with the same ID already exists
        if any(existing_tag.id == tag.id for existing_tag in self.tag_list):
            return False # Tag with this ID already exists
        self.tag_list.append(tag)
        return True

    def remove_tag(self, tag_to_remove: Tag) -> bool:
        """Removes a tag from the person's owned tags."""
        # We need to compare tag objects, or more reliably, find by ID
        initial_len = len(self.tag_list)
        self.tag_list = [tag for tag in self.tag_list if tag.id != tag_to_remove.id]
        return len(self.tag_list) < initial_len # Return True if removed

    def find_tag(self, tag_id: int) -> Tag | None:
        """Finds an owned tag by its ID."""
        for tag in self.tag_list:
            if tag.id == tag_id:
                return tag
        return None

    def add_acquaintance(self, person: Person, value: int) -> bool:
        """Adds a relationship with another person."""
        if not isinstance(person, Person) or person == self or value <= 0:
            return False # Invalid input or self-relation or non-positive value
        if person in self.acquaintances:
            return False # Relation already exists
        self.acquaintances[person] = value
        return True

    def remove_acquaintance(self, person: Person) -> bool:
        """Removes a relationship with another person."""
        if person in self.acquaintances:
            del self.acquaintances[person]
            return True
        return False

    def get_acquaintance_value(self, person: Person) -> int | None:
        """Gets the value of the relationship with another person."""
        return self.acquaintances.get(person) # Returns None if person not in dict

    def modify_acquaintance_value(self, person: Person, modify_value: int) -> tuple[bool, bool]:
        """
        Modifies the value of a relationship by adding modify_value.
        Returns: (success: bool, needs_removal: bool)
        success is True if the person was an acquaintance.
        needs_removal is True if the modification resulted in value <= 0.
        """
        if person in self.acquaintances:
            self.acquaintances[person] += modify_value
            needs_removal = self.acquaintances[person] <= 0
            if needs_removal:
                 # We don't delete here, just signal. Network handles symmetric removal.
                 pass
            return True, needs_removal
        return False, False # Not an acquaintance, modification failed

    def has_relation(self, person: Person) -> bool:
        """Checks if there is a relationship with another person."""
        return person in self.acquaintances

    def clear_relations(self):
        """Removes all relationships (used for LN maybe)."""
        self.acquaintances.clear()

    def clear_tags(self):
         """Removes all owned tags."""
         self.tag_list.clear()

class Tag:
    id : int
    # personList stores Person objects *added to this tag* by the tag's owner.
    personList : list[Person]

    def __init__(self, id: int):
        if not isinstance(id, int): raise TypeError("Tag ID must be an integer")
        self.id = id
        self.personList = []

    def __str__(self):
        personIdList = sorted([person.id for person in self.personList])
        return f"Tag(id={self.id}, personIdList={personIdList})"

    def __eq__(self, other):
        # Two tags are equal if they have the same ID.
        # Note: The personList content doesn't define tag equality.
        return isinstance(other, Tag) and self.id == other.id

    def __hash__(self):
        # Hash based on ID
        return hash(self.id)

    def add_person(self, person: Person) -> bool:
        """Adds a person to this tag's list if not already present."""
        if not isinstance(person, Person): return False
        if person not in self.personList:
            self.personList.append(person)
            return True
        return False

    def remove_person(self, person: Person) -> bool:
        """Removes a person from this tag's list."""
        initial_len = len(self.personList)
        self.personList = [p for p in self.personList if p != person]
        return len(self.personList) < initial_len # True if removed

    def has_person(self, person: Person) -> bool:
        """Checks if a person is in this tag's list."""
        return person in self.personList

    def get_size(self) -> int:
        """Returns the number of people in this tag's list."""
        return len(self.personList)

    def get_value_sum(self, owner_person: Person) -> int:
        """Calculates sum of relation values between owner_person and people in this tag."""
        if not isinstance(owner_person, Person): return 0
        total_value = 0
        for person_in_tag in self.personList:
            # Owner must have a relation with the person in the tag list
            value = owner_person.get_acquaintance_value(person_in_tag)
            if value is not None: # Check if relation exists
                total_value += value
        return total_value

    def get_age_stats(self) -> tuple[int, int, int]:
         """Calculates sum, sum_sq, count for age variance."""
         n = len(self.personList)
         if n == 0:
             return 0, 0, 0
         age_sum = sum(p.age for p in self.personList)
         age_sum_sq = sum(p.age * p.age for p in self.personList)
         return age_sum, age_sum_sq, n

    def get_age_mean(self) -> float:
        """Calculates the mean age of people in the tag."""
        age_sum, _, n = self.get_age_stats()
        return age_sum / n if n > 0 else 0.0

    def get_age_var(self) -> int:
        """Calculates the variance of ages of people in the tag (integer part)."""
        age_sum, age_sum_sq, n = self.get_age_stats()
        if n <= 1: # Variance is 0 if 0 or 1 person
            return 0
        # Variance Formula: E[X^2] - (E[X])^2 = (sum_sq / n) - (sum / n)^2
        mean = age_sum / n
        variance = (age_sum_sq / n) - (mean * mean)
        # Ensure non-negative due to potential float precision issues
        return int(max(0, variance))


class Network:
    person_map : dict[int, Person]
    account_map : dict[int, OfficialAccount]
    # No global tag map; tags are owned by Persons.

    def __init__(self):
        self.person_map = {}
        self.account_map = {}

    def __str__(self):
        person_ids = sorted(self.person_map.keys())
        account_ids = sorted(self.account_map.keys())
        return f"Network(persons={len(person_ids)}, accounts={len(account_ids)})"

    def reset(self):
        """Clears the network state."""
        self.person_map.clear()
        self.account_map.clear()

    def add_person(self, person : Person) -> bool:
        """Adds a person to the network."""
        if not isinstance(person, Person): return False
        if person.id in self.person_map:
            return False # Person with this ID already exists
        self.person_map[person.id] = person
        return True

    def find_person(self, id : int) -> Person | None:
        """Finds a person by ID."""
        return self.person_map.get(id)

    def add_relation(self, personId1 : int, personId2 : int, value : int) -> bool:
        """Adds a symmetric relation between two persons."""
        if personId1 == personId2 or value <= 0:
            return False # Self-relation or non-positive value not allowed
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not person1 or not person2:
            return False # One or both persons don't exist
        # Add relation symmetrically, check if already exists
        success1 = person1.add_acquaintance(person2, value)
        success2 = person2.add_acquaintance(person1, value)
        # If one succeeded but the other failed (shouldn't happen if logic is correct), roll back
        if success1 != success2:
             print(f"Warning: Asymmetric relation add detected between {personId1} and {personId2}", file=sys.stderr)
             if success1: person1.remove_acquaintance(person2)
             if success2: person2.remove_acquaintance(person1)
             return False
        return success1 # Both must succeed or fail together

    def modify_relation(self, personId1: int, personId2: int, modifyValue: int) -> bool:
        """Modifies a relation value symmetrically. Removes if value <= 0."""
        if personId1 == personId2: return False
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not person1 or not person2: return False # Persons must exist

        success1, remove1 = person1.modify_acquaintance_value(person2, modifyValue)
        success2, remove2 = person2.modify_acquaintance_value(person1, modifyValue)

        if not success1: # Relation didn't exist in the first place
            return False

        # If modification resulted in value <= 0, remove relation symmetrically
        if remove1 or remove2:
            person1.remove_acquaintance(person2)
            person2.remove_acquaintance(person1)

        return True # Modification (or subsequent removal) was processed

    def add_tag(self, personId : int, tag : Tag) -> bool:
        """Adds a tag to a person's owned list."""
        person = self.find_person(personId)
        if person and isinstance(tag, Tag):
            return person.add_tag(tag)
        return False

    def add_person_to_tag(self, ownerId : int, personToAddId : int, tagId : int) -> bool:
        """Adds personToAdd to the list of tagId owned by ownerId."""
        if ownerId == personToAddId: return False # Cannot add owner to their own tag list
        owner = self.find_person(ownerId)
        personToAdd = self.find_person(personToAddId)
        if not owner or not personToAdd: return False # Both must exist
        # Owner and personToAdd must have a relation
        if not owner.has_relation(personToAdd): return False
        # Owner must have the tag
        tag = owner.find_tag(tagId)
        if not tag: return False
        # Add personToAdd to the tag's list
        return tag.add_person(personToAdd)

    def del_person_from_tag(self, ownerId : int, personToRemoveId : int, tagId : int) -> bool:
        """Removes personToRemove from the list of tagId owned by ownerId."""
        owner = self.find_person(ownerId)
        personToRemove = self.find_person(personToRemoveId) # Person to remove must exist
        if not owner or not personToRemove: return False
        tag = owner.find_tag(tagId)
        if not tag: return False
        return tag.remove_person(personToRemove)

    def del_tag(self, personId : int, tagId : int) -> bool:
        """Deletes a tag owned by a person."""
        person = self.find_person(personId)
        if not person: return False
        tag_to_delete = person.find_tag(tagId)
        if not tag_to_delete: return False

        # Also remove this person from any other person's tag that references this tag ID?
        # -> The spec usually implies 'dt pid tid' only affects the tag owned by 'pid'.
        # -> If tag IDs were meant to be globally unique objects, the model would be different.
        # -> Sticking to the simpler interpretation: just remove from owner.

        return person.remove_tag(tag_to_delete) # Use the object found

    def has_person(self, personId : int) -> bool:
        """Checks if a person exists in the network."""
        return personId in self.person_map

    def has_relation(self, personId1 : int, personId2 : int) -> bool:
        """Checks if a relation exists between two persons."""
        if personId1 == personId2: return False
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        # Check existence and relation (only need one direction due to symmetry)
        return bool(person1 and person2 and person1.has_relation(person2))

    # --- Official Account Methods ---

    def add_official_account(self, account: OfficialAccount) -> bool:
        """Adds an official account to the network."""
        if not isinstance(account, OfficialAccount): return False
        # Account ID must be unique, Owner must exist
        if account.id in self.account_map or not self.has_person(account.ownerId):
            return False
        self.account_map[account.id] = account
        return True

    def find_official_account(self, id: int) -> OfficialAccount | None:
        """Finds an official account by ID."""
        return self.account_map.get(id)

    def delete_official_account(self, accountId: int) -> bool:
        """Deletes an official account."""
        if accountId in self.account_map:
            del self.account_map[accountId]
            # Note: Followers are not explicitly notified or removed here.
            # Their Person objects still exist, but the account they followed is gone.
            return True
        return False

    def contribute_article(self, accountId: int, articleId: int) -> bool:
        """Adds an article ID to an official account."""
        account = self.find_official_account(accountId)
        # Assuming article IDs are just integers and don't need separate objects
        if account and isinstance(articleId, int):
            return account.add_article(articleId)
        return False

    def delete_article(self, accountId: int, articleId: int) -> bool:
        """Removes an article ID from an official account."""
        account = self.find_official_account(accountId)
        if account:
            return account.remove_article(articleId)
        return False

    def follow_official_account(self, personId: int, accountId: int) -> bool:
        """Makes a person follow an official account."""
        person = self.find_person(personId)
        account = self.find_official_account(accountId)
        owner = self.find_person(account.ownerId) if account else None

        if not person or not account or not owner: return False # All must exist

        # Calculate initial contribution based on relation value with owner
        # Spec might define this differently (e.g., always 0 initially)
        contribution = person.get_acquaintance_value(owner) or 0 # Default to 0 if no relation

        return account.add_follower(person, contribution)

    def load_network(self, ids: list[int], names: list[str], ages: list[int], relations_data: list[list[int]]) -> bool:
        """Loads a network from specific data structures (for ln command)."""
        self.reset() # Clear existing network first
        if not (len(ids) == len(names) == len(ages) == len(relations_data)):
            print("Error: Mismatched lengths in load_network data.", file=sys.stderr)
            return False

        # Add persons first
        for i in range(len(ids)):
             try:
                 person = Person(ids[i], names[i], ages[i])
                 if not self.add_person(person):
                     print(f"Error: Duplicate or invalid person data for ID {ids[i]} in load_network.", file=sys.stderr)
                     self.reset() # Failed load, clear network
                     return False
             except TypeError as e:
                  print(f"Error: Invalid person data for ID {ids[i]} in load_network: {e}", file=sys.stderr)
                  self.reset()
                  return False

        # Add relations (handle potential errors)
        person_count = len(ids)
        adj = [[] for _ in range(person_count)] # Adjacency list for LN format [[neigh, val],...]
        id_to_index = {id_val: index for index, id_val in enumerate(ids)}

        for i in range(person_count):
             line_data = relations_data[i]
             # Assuming relations_data[i] = [person_id, neighbor1_id, value1, neighbor2_id, value2, ...]
             # Validate the first element matches the person's ID
             if not line_data or line_data[0] != ids[i]:
                  print(f"Error: Relation data line {i+1} does not start with correct person ID {ids[i]}.", file=sys.stderr)
                  self.reset()
                  return False
             # Process pairs
             if len(line_data) % 2 == 0: # Must have odd length (id + pairs)
                  print(f"Error: Relation data line {i+1} has incorrect number of elements.", file=sys.stderr)
                  self.reset()
                  return False
             for j in range(1, len(line_data), 2):
                  neighbor_id = line_data[j]
                  value = line_data[j+1]
                  if neighbor_id not in id_to_index or value <= 0:
                      print(f"Error: Invalid neighbor ID {neighbor_id} or value {value} on line {i+1}.", file=sys.stderr)
                      self.reset()
                      return False
                  if ids[i] == neighbor_id: # Check self-loops
                      print(f"Error: Self-loop detected for ID {ids[i]} on line {i+1}.", file=sys.stderr)
                      self.reset()
                      return False

                  # Add relation (use add_relation for consistency checks)
                  # Need to be careful about duplicates if input provides both directions
                  # Let's assume input provides relations for one direction, add symmetrically
                  if not self.has_relation(ids[i], neighbor_id):
                       if not self.add_relation(ids[i], neighbor_id, value):
                            print(f"Error adding relation between {ids[i]} and {neighbor_id} during load.", file=sys.stderr)
                            self.reset()
                            return False
                  else:
                       # Check if value matches if relation already added from other direction
                       p1 = self.find_person(ids[i])
                       p2 = self.find_person(neighbor_id)
                       if p1 and p2 and p1.get_acquaintance_value(p2) != value:
                            print(f"Error: Conflicting relation values between {ids[i]} and {neighbor_id} during load.", file=sys.stderr)
                            self.reset()
                            return False

        return True # Load successful


class OfficialAccount:
    ownerId : int
    id : int
    name : str
    # Use dict for followers {Person: contribution}
    followers : dict[Person, int]
    articleList : list[int] # List of article IDs

    def __init__(self, ownerId: int, id: int, name: str):
        if not isinstance(ownerId, int): raise TypeError("OA Owner ID must be int")
        if not isinstance(id, int): raise TypeError("OA ID must be int")
        if not isinstance(name, str): raise TypeError("OA name must be str")
        self.ownerId = ownerId
        self.id = id
        self.name = name
        self.followers = {}
        self.articleList = []

    def __str__(self):
        # Sort followers by ID for consistent representation
        followerInfo = sorted([(f.id, c) for f, c in self.followers.items()], key=lambda item: item[0])
        article_ids = sorted(self.articleList)
        return f"OA(owner={self.ownerId}, id={self.id}, name={self.name}, followers={followerInfo}, articles={article_ids})"

    def __eq__(self, other):
        return isinstance(other, OfficialAccount) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def get_id(self) -> int:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_ownerId(self) -> int:
        return self.ownerId

    def add_follower(self, person: Person, contribution: int) -> bool:
        """Adds a follower if not already present."""
        if not isinstance(person, Person) or person in self.followers:
            return False
        self.followers[person] = contribution
        return True

    def contains_follower(self, person: Person) -> bool:
        """Checks if a person is a follower."""
        return person in self.followers

    def remove_follower(self, person: Person) -> bool:
         """Removes a follower."""
         if person in self.followers:
             del self.followers[person]
             return True
         return False

    def add_article(self, articleId: int) -> bool:
        """Adds an article ID if not already present."""
        if isinstance(articleId, int) and articleId not in self.articleList:
            self.articleList.append(articleId)
            return True
        return False

    def contains_article(self, articleId: int) -> bool:
        """Checks if the account has a specific article ID."""
        return articleId in self.articleList

    def remove_article(self, articleId: int) -> bool:
        """Removes an article ID if present."""
        if articleId in self.articleList:
            self.articleList.remove(articleId) # list.remove is O(n) but likely fine
            return True
        return False

    def get_follower_contribution(self, person: Person) -> int | None:
        """Gets the contribution of a specific follower."""
        return self.followers.get(person)

    def modify_follower_contribution(self, person: Person, modify_value: int) -> bool:
        """Modifies a follower's contribution by adding modify_value."""
        if person in self.followers:
            self.followers[person] += modify_value
            # Add constraints if needed (e.g., contribution >= 0)
            # self.followers[person] = max(0, self.followers[person])
            return True
        return False # Follower not found