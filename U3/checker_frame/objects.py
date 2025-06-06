class Person:
    id : int
    name : str
    age : int
    tag_list : list
    acquaintance_list : list
    value_list : list

    def __init__(self, id, name, age):
        self.id = id
        self.name = name
        self.age = age
        self.tag_list = []
        self.acquaintance_list = []
    def __str__(self):
        tagIdList = [tag.id for tag in self.tag_list]
        acquaintanceList = [(id, value) for id, value in zip(self.acquaintance_list, self.value_list)]
        return f"Person(id={self.id}, name={self.name}, age={self.age}, tagIdList={tagIdList}, acquaintanceList={acquaintanceList})"
    def __eq__(self, value):
        return isinstance(value, Person) and self.id == value.id

    def add_tag(self, tag):
        if not (tag in self.tag_list):
            self.tag_list.append(tag)
    def remove_tag(self, tag):
        if (tag in self.tag_list):
            self.tag_list.remove(tag)
    def find_tag(self, id):
        for tag in self.tag_list:
            if (tag.id == id):
                return tag
        return None
    def add_acquaintance(self, person, value):
        if not (person in self.acquaintance_list):
            self.acquaintance_list.append(person)
            self.value_list.append(value)
    def remove_acquaintance(self, person):
        if (person in self.acquaintance_list):
            index = self.acquaintance_list.index(person)
            self.acquaintance_list.pop(index)
            self.value_list.pop(index)
    def get_acquaintance_value(self, person):
        if (person in self.acquaintance_list):
            index = self.acquaintance_list.index(person)
            return self.value_list[index]
        else:
            return None
    def modify_acquaintance_value(self, person, modify_value):
        if (person in self.acquaintance_list):
            index = self.acquaintance_list.index(person)
            self.value_list[index] = modify_value
    
    def has_relation(self, person):
        return person in self.acquaintance_list

class Tag:
    id : int
    personList : list[Person]
    def __init__(self, id):
        self.id = id
        self.personList = []
    def __str__(self):
        personIdList = [person.id for person in self.personList]
        return f"Tag(id={self.id}, personIdList={personIdList})"
    def __eq__(self, value):
        return isinstance(value, Tag) and self.id == value.id
    
    def add_person(self, person):
        if not (person in self.personList):
            self.personList.append(person)
    def remove_person(self, person):
        if (person in self.personList):
            index = self.personList.index(person)
            self.personList.pop(index)

class Network:
    person_list : list[Person]
    def __init__(self):
        self.person_list = []
    def __str__(self):
        return f"Network(person_list={self.person_list})"
    def add_person(self, person : Person):
        if not (person in self.person_list):
            self.person_list.append(person)
    def find_person(self, id : int):
        for person in self.person_list:
            if (person.id == id):
                return person
        return None
    def add_relation(self, personId1 : int, personId2 : int, value : int):
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not (person1 is None or person2 is None):
            person1.add_acquaintance(person2, value)
            person2.add_acquaintance(person1, value)
    def add_tag(self, personId : int, tag : Tag):
        person = self.find_person(personId)
        if not (person is None):
            person.add_tag(tag)
    def add_person_to_tag(self, personId1 : int, personId2 : int, tagId : int):
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not (person1 is None or person2 is None):
            tag = person1.find_tag(tagId)
            if not (tag is None):
                tag.add_person(person2)
    def del_person_from_tag(self, personId1 : int, personId2 : int, tagId : int):
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not (person1 is None or person2 is None):
            tag = person1.find_tag(tagId)
            if not (tag is None):
                tag.remove_person(person2)
    def del_tag(self, personId : int, tagId : int):
        person = self.find_person(personId)
        if not (person is None):
            tag = person.find_tag(tagId)
            if not (tag is None):
                person.remove_tag(tag)
    
    def has_person(self, personId : int) -> bool:
        for person in self.person_list:
            if (person.id == personId):
                return True
        return False
    def has_relation(self, personId1 : int, personId2 : int) -> bool:
        person1 = self.find_person(personId1)
        person2 = self.find_person(personId2)
        if not (person1 is None or person2 is None):
            return person1.has_relation(person2)
        else:
            return False

class OfficialAccount:
    ownerId : int
    id : int
    name : str
    followerList : list[Person]
    followerContribution : list[int]
    articleList : list[int]
    def __init__(self, ownerId, id, name):
        self.ownerId = ownerId
        self.id = id
        self.name = name
        self.followerList = []
        self.followerContribution = []
        self.articleList = []
    def __str__(self):
        followerIdList = [follower.id for follower in self.followerList]
        return f"OfficialAccount(ownerId={self.ownerId}, id={self.id}, name={self.name}, followerIdList={followerIdList})"    
    def __eq__(self, value):
        return isinstance(value, OfficialAccount) and self.id == value.id
    
    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name
    
    def get_ownerId(self):
        return self.ownerId
    
    def add_follower(self, person, contribution):
        if not (person in self.followerList):
            self.followerList.append(person)
            self.followerContribution.append(contribution)
    
    def contains_follower(self, person):
        return person in self.followerList
    
    def add_article(self, articleId):
        if not (articleId in self.articleList):
            self.articleList.append(articleId)

    def contains_article(self, articleId):
        return articleId in self.articleList
    
    def remove_article(self, articleId):
        if (articleId in self.articleList):
            index = self.articleList.index(articleId)
            self.articleList.pop(index)
    
    def get_follower_contribution(self, person):
        if (person in self.followerList):
            index = self.followerList.index(person)
            return self.followerContribution[index]
        else:
            return None
    
    def modify_follower_contribution(self, person, modify_value):
        if (person in self.followerList):
            index = self.followerList.index(person)
            self.followerContribution[index] = modify_value


class Message:
    messageId : int
    socialValue : int
    type : int
    person1Id : int
    person2Id : int
    tagId : int
    def __init__(self, messageId, socialValue, type, person1Id, Id2):
        self.messageId = messageId
        self.socialValue = socialValue
        self.type = type
        self.person1Id = person1Id
        if (type == 0):
            self.person2Id = Id2
        else:
            self.tagId = Id2

    def __str__(self):
        return f"Message(messageId={self.messageId}, socialValue={self.socialValue}, type={self.type}, person1Id={self.person1Id}, Id2={self.person2Id})"
    
    def __eq__(self, value):
        return isinstance(value, Message) and self.messageId == value.messageId
    
    def get_id(self):
        return self.messageId
    
    def get_social_value(self):
        return self.socialValue
    
    def get_type(self):
        return self.type

    def get_person1Id(self):
        return self.person1Id
    
    def get_person2Id(self):
        return self.person2Id
    
    def get_tagId(self):
        return self.tagId
    


"""
add_emoji_message id(int) emoji_id(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
add_red_envelope_message id(int) money(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
add_forward_message id(int) article_id(int) type(int) person_id1(int) person_id2(int)|tag_id(int)
"""

class EmojiMessage(Message):
    def __init__(self, messageId, emojiId, type, person1Id, Id2):
        super().__init__(messageId, emojiId, type, person1Id, Id2)
        self.emojiId = emojiId
    
    def __str__(self):
        return f"EmojiMessage(messageId={self.messageId}, socialValue={self.emojiId}, type={self.type}, person1Id={self.person1Id}, emojiId={self.Id2})"
    
    def get_emojiId(self):
        return self.emojiId
    
class RedEnvelopeMessage(Message):
    def __init__(self, messageId, money, type, person1Id, Id2):
        super().__init__(messageId, money * 5, type, person1Id, Id2)
        self.money = money
    
    def __str__(self):
        return f"RedEnvelopeMessage(messageId={self.messageId}, socialValue={self.money}, type={self.type}, person1Id={self.person1Id}, money={self.Id2})"
    
    def get_money(self):
        return self.money
    
class ForwardMessage(Message):
    def __init__(self, messageId, articleId, type, person1Id, Id2):
        super().__init__(messageId, abs(articleId) % 200, type, person1Id, Id2)
        self.articleId = articleId
    
    def __str__(self):
        return f"ForwardMessage(messageId={self.messageId}, socialValue={self.articleId}, type={self.type}, person1Id={self.person1Id}, articleId={self.Id2})"
    
    def get_articleId(self):
        return self.articleId