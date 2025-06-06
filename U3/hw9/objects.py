class Person:
    id : int
    name : str
    age : int
    tag_list : list['Tag'] # Forward reference Tag
    acquaintance_list : list['Person'] # Forward reference Person
    value_list : list[int] # Corresponding values for acquaintances

    def __init__(self, id, name, age):
        self.id = id
        self.name = name
        self.age = age
        self.tag_list = []
        self.acquaintance_list = []
        self.value_list = [] # Initialize value_list

    def __str__(self):
        tagIdList = sorted([tag.id for tag in self.tag_list]) # Sort for consistency
        # Sort acquaintances by ID for consistency
        acq_tuples = sorted([(p.id, v) for p, v in zip(self.acquaintance_list, self.value_list)])
        acquaintanceListStr = [f"({id},{val})" for id, val in acq_tuples]
        return f"Person(id={self.id}, name={self.name}, age={self.age}, tagIdList={tagIdList}, acquaintanceList=[{', '.join(acquaintanceListStr)}])"

    def __repr__(self): # Add repr for easier debugging
        return f"Person(id={self.id})"

    def __eq__(self, value):
        # Check type and ID for equality
        return isinstance(value, Person) and self.id == value.id

    def __hash__(self): # Add hash for using Person in sets/dicts
        return hash(self.id)

    def add_tag(self, tag: 'Tag'):
        if tag not in self.tag_list:
            self.tag_list.append(tag)
            # Keep tag_list sorted by id? Optional, but helps consistency
            # self.tag_list.sort(key=lambda t: t.id)

    def remove_tag(self, tag: 'Tag'):
        if tag in self.tag_list:
            self.tag_list.remove(tag)

    def find_tag(self, tag_id: int) -> 'Tag | None':
        for tag in self.tag_list:
            if tag.id == tag_id:
                return tag
        return None

    def add_acquaintance(self, person: 'Person', value: int):
        if person not in self.acquaintance_list:
            self.acquaintance_list.append(person)
            self.value_list.append(value)

    def remove_acquaintance(self, person: 'Person'):
        if person in self.acquaintance_list:
            try:
                index = self.acquaintance_list.index(person)
                self.acquaintance_list.pop(index)
                self.value_list.pop(index)
            except ValueError: # Should not happen if check passes, but safe
                pass

    def get_acquaintance_value(self, person: 'Person') -> int | None:
        if person in self.acquaintance_list:
            try:
                index = self.acquaintance_list.index(person)
                return self.value_list[index]
            except ValueError: # Should not happen
                return None
        else:
            return None

    def modify_acquaintance_value(self, person: 'Person', new_value: int):
         if person in self.acquaintance_list:
            try:
                index = self.acquaintance_list.index(person)
                self.value_list[index] = new_value
            except ValueError: # Should not happen
                pass

    def has_relation(self, person: 'Person') -> bool:
        return person in self.acquaintance_list

    def has_tag(self, tag_id: int) -> bool:
        return self.find_tag(tag_id) is not None

class Tag:
    id : int
    personList : list[Person]
    def __init__(self, id):
        self.id = id
        self.personList = []

    def __str__(self):
        personIdList = sorted([person.id for person in self.personList]) # Sort for consistency
        return f"Tag(id={self.id}, personIdList={personIdList})"

    def __repr__(self): # Add repr
        return f"Tag(id={self.id})"

    def __eq__(self, value):
         # Check type and ID for equality
        return isinstance(value, Tag) and self.id == value.id

    def __hash__(self): # Add hash for using Tag in sets/dicts
        return hash(self.id)

    def add_person(self, person: Person):
        if person not in self.personList:
            self.personList.append(person)
            # Keep personList sorted by id? Optional.
            # self.personList.sort(key=lambda p: p.id)

    def remove_person(self, person: Person):
        # Use list.remove which handles finding the element
        if person in self.personList:
             try:
                 self.personList.remove(person)
             except ValueError: # Should not happen if check passes
                 pass


class Network:
    person_list : list[Person]
    # Store persons in a dictionary for faster lookup by ID
    persons_map : dict[int, Person]

    def __init__(self):
        self.person_list = []
        self.persons_map = {}

    def __str__(self):
        # Sort person list by ID for consistent output
        sorted_persons = sorted(self.person_list, key=lambda p: p.id)
        return f"Network(person_list={sorted_persons})" # Use sorted list

    def add_person(self, person : Person):
        if person.id not in self.persons_map:
            self.person_list.append(person)
            self.persons_map[person.id] = person
            # Keep person_list sorted? Optional, depends if order matters elsewhere.
            # self.person_list.sort(key=lambda p: p.id)

    def find_person(self, person_id : int) -> Person | None:
        # Use the map for O(1) average time lookup
        return self.persons_map.get(person_id)

    def add_relation(self, personId1 : int, personId2 : int, value : int):
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        # Ensure persons exist, are distinct, and relation doesn't already exist
        if person1 and person2 and personId1 != personId2 and not person1.has_relation(person2):
            person1.add_acquaintance(person2, value)
            person2.add_acquaintance(person1, value)

    def add_tag(self, personId : int, tag : Tag):
        """Adds a tag to a person's list. Assumes tag object is managed externally."""
        person = self.find_person(personId)
        if person:
            person.add_tag(tag)
            # The caller should also ensure person is added to tag.personList

    def add_person_to_tag(self, personId1 : int, personId2 : int, tagId : int):
        """Adds person2 to the tag (identified by tagId) held by person1."""
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if person1 and person2 and personId1 != personId2:
            tag = person1.find_tag(tagId) # Find the specific tag instance held by person1
            if tag: # Check if person1 actually has this tag
                # Add person2 to this tag instance
                tag.add_person(person2)
                # Also add the tag to person2's list
                person2.add_tag(tag)


    def del_person_from_tag(self, personId1 : int, personId2 : int, tagId : int):
        """Removes person2 from the tag (identified by tagId) held by person1."""
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if person1 and person2 and personId1 != personId2:
            tag = person1.find_tag(tagId) # Find the tag instance via person1
            if tag and person2 in tag.personList: # Check p1 has tag AND p2 is in that tag
                # Remove person2 from this tag instance
                tag.remove_person(person2)
                # Also remove the tag from person2's list
                person2.remove_tag(tag)


    def del_tag(self, personId : int, tagId : int):
        """Removes a tag from a person's list and the person from the tag's list."""
        person = self.find_person(personId)
        if person:
            tag = person.find_tag(tagId) # Find the specific tag instance
            if tag:
                person.remove_tag(tag)
                tag.remove_person(person)
                # Note: This doesn't delete the global tag object, only the link.
                # Global tag cleanup might need external handling (e.g., in Generator).


    def has_person(self, personId : int) -> bool:
        # Use the map for efficiency
        return personId in self.persons_map

    def has_relation(self, personId1 : int, personId2 : int) -> bool:
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        # Check both persons exist and person1 has relation to person2
        if person1 and person2:
            return person1.has_relation(person2)
        else:
            return False
