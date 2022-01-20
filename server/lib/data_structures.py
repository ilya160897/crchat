import json
from abc import ABC, abstractmethod
from .json_storage import JsonStorage

supported_reactions = set(("Thumbs Up", "Thumbs Down", "Love", "Fire", "Pile of Poo"))

class DataItem:
    def __init__(self, action_type, login, message_id, content):
        self.action_type = action_type
        self.login = login
        self.message_id = message_id
        self.content = content


class DataBase(ABC):
    def __init__(self, storage_path, default_state, logger):
        self.logger = logger
        self.storage = JsonStorage(storage_path, default_state, self.logger)


    @abstractmethod
    def CreateItem(self, storage, item):
        raise NotImplementedError


    def Add(self, item):
        storage = self.storage.Get()
        self.CheckStorageCorrect(storage)
        self.CreateItem(storage, item)
        self.storage.Update(storage)


    def GetString(self):
        return json.dumps(self.storage.Get())


    def Size(self):
        return len(self.storage.Get())


    def CheckStorageCorrect(self, storage):
        if isinstance(storage, list) and len(storage) > 0:
            assert isinstance(storage[-1], dict), "Array must consist of dicts!"
            assert "id" in storage[-1], "Each item should have and id!"
            assert len(storage) == storage[-1]["id"] + 1, "Check correct id-ing"


class Members(DataBase):

    default_state = dict()

    def __init__(self, logger, path):
        self.logins = set()
        super().__init__(path, Members.default_state, logger)

    
    def IsLoginUsed(self, login):
        return login in self.logins


    def Auth(self, login, password):
        kv_storage = self.storage.Get()
        if password in kv_storage:
            found_login = kv_storage[password]
            if login == found_login:
                self.logger.info("Auth member with login {}: successfull!".format(found_login)) 
                return True
        self.logger.info("Auth: member was NOT found!") 
        return False 
    
    
    # Sign up
    def CreateItem(self, storage, item):
        self.logins.add(item.login)
        storage[str(item.content)] = item.login # content is a password
        self.logger.info("Member with login {} registered!".format(item.login))


class Actions(DataBase):

    default_state = list()

    def __init__(self, logger, path):
        super().__init__(path, Actions.default_state, logger)


    def CreateItem(self, storage, item):
        next_id = len(storage)
        action = {
            "id" : next_id, 
            "action_type": item.action_type, 
            "login": item.login, 
            "message_id" : item.message_id,
            "content": item.content
        }
        storage.append(action)


class Messages(DataBase):

    default_state = list()

    def __init__(self, logger, path):
        super().__init__(path, Messages.default_state, logger)
 

    def CreateItem(self, storage, item):
        if item.action_type == "add_message":         
            self.AddMessage(storage, item)
        elif item.action_type == "add_comment":
            self.AddComment(storage, item)
        elif item.action_type == "add_reaction":
            self.AddReaction(storage, item)


    def AddMessage(self, storage, item):
        next_id = len(storage)
        message = {
            "id": next_id,
            "login": item.login,
            "content": item.content,
            "comments": [],
            "reactions": {
                "Thumbs Up": 0,
                "Thumbs Down": 0,
                "Love": 0,
                "Fire": 0,
                "Pile of Poo": 0
            }
        }
        storage.append(message)
        self.logger.info("New message \"{}\" with message_id {} by (login) {}!".format(item.content, item.message_id, item.login))


    def AddComment(self, storage, item):
        if self.MessageIdIsIncorrect(item.message_id):
            return

        comment = {
            "login" : item.login,
            "content": item.content
        }
        storage[int(item.message_id)]["comments"].append(comment)
        self.logger.info("Comment \"{}\" for message_id {} by (login) {}!".format(item.content, item.message_id, item.login))


    def AddReaction(self, storage, item):
        if self.MessageIdIsIncorrect(item.message_id):
            return

        if item.content in supported_reactions:
            storage[int(item.message_id)]["reactions"][item.content] += 1
            self.logger.info("Reaction \"{}\" for message_id {} by (login) {}!".format(item.content, item.message_id, item.login))


    def MessageIdIsIncorrect(self, message_id):
        storage_size = len(self.storage.Get())
        is_incorrect = int(message_id) < 0 or int(message_id) >= storage_size 
        if is_incorrect:
            self.logger.info("Message ID {} is incorrect: storage's size is {}".format(message_id, storage_size))
        return is_incorrect 

