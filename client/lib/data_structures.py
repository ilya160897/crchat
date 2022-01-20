from .json_storage import JsonStorage
from abc import ABC, abstractmethod

supported_reactions = set(("Thumbs Up", "Thumbs Down", "Love", "Fire", "Pile of Poo"))
 
class ManagerBase(ABC):
    def __init__(self, storage_path, default_state, logger):
        self.logger = logger
        self.storage = JsonStorage(storage_path, default_state, self.logger)


    @abstractmethod
    def BasicCheckCorrectness(self, storage):
        raise NotImplementedError


    @abstractmethod
    def UpdateUI(self, storage):
        raise NotImplementedError


    def UpdateState(self, storage):
        self.BasicCheckCorrectness(storage)
        self.UpdateUI(storage)
        self.storage.Update(storage)


# Similar to DataItem in server
class Action(ABC):
    def __init__(self, id, action_type, login, message_id, content):
        self.id = id
        self.action_type = action_type
        self.login = login
        self.message_id = message_id
        self.content = content


    @abstractmethod
    def ConsoleString(self):
        raise NotImplementedError


class SignUp(Action):
    def ConsoleString(self):
        return "{} joined the Comment-Reaction Chat!".format(self.login)


class Message(Action):
    def ConsoleString(self):
        return "[#{}][{}]: {}".format(self.message_id, self.login, self.content)


class Comment(Action):
    def ConsoleString(self):
        return "[{} commented on message #{}]: {}".format(self.login, self.message_id, self.content)


class Reaction(Action):
    def ConsoleString(self):
        if self.content == "Thumbs Up":
            return "[{} liked message {}]".format(self.login, self.message_id)
        elif self.content == "Thumbs Down":
            return "[{} disliked message {}]".format(self.login, self.message_id)
        elif self.content == "Love":
            return "[{} reacted with Love emoji on message {}]".format(self.login, self.message_id)
        elif self.content == "Fire":
            return "[{} reacted with Fire emoji on message {}]".format(self.login, self.message_id)
        elif self.content == "Pile of Poo":
            return "[{} reacted with Pile of Poo emoji on message {}]".format(self.login, self.message_id)
        else:
            return "Unsupported emoji"


class ConsoleChatStateManager(ManagerBase):

    default_state = []

    def __init__(self, storage_path, logger):
        super().__init__(storage_path, FileChatStateManager.default_state, logger)


    def UpdateUI(self, storage):
        current_storage = self.storage.Get()
        current_actions = [ConsoleChatStateManager.JsonToAction(json_action) for json_action in current_storage]
        updated_actions = [ConsoleChatStateManager.JsonToAction(json_action) for json_action in storage]
        for action in  updated_actions[len(current_actions):]:
            print(action.ConsoleString())    


    def LoadLast(self, n_last_messages):
        last_n_actions = [ConsoleChatStateManager.JsonToAction(json_action) for json_action in self.storage.Get()[-n_last_messages:]]
        for action in last_n_actions: 
            print(action.ConsoleString())    


    @staticmethod
    def BasicCheckCorrectness(storage):
        assert isinstance(storage, list), "Console State storage must be a list"
        if len(storage) > 0:
            last_action = storage[-1]
            ConsoleChatStateManager.CheckActionIsCorrect(last_action)


    @staticmethod 
    def CheckActionIsCorrect(action_json):
        error_msg = "Mising key in Action json" 
        assert "id" in action_json, error_msg 
        assert "action_type" in action_json, error_msg
        assert "login" in action_json, error_msg
        assert "message_id" in action_json, error_msg
        assert "content" in action_json, error_msg


    @staticmethod 
    def JsonToAction(action_json):
        action_type_to_subclass = {
            "sign_up" : SignUp,
            "add_message" : Message,
            "add_comment" : Comment,
            "add_reaction" : Reaction
        }
        ActionSubclass = action_type_to_subclass[action_json["action_type"]]    
        return ActionSubclass(
            id = action_json["id"],
            action_type = action_json["action_type"],
            login = action_json["login"],
            message_id = action_json["message_id"],
            content = action_json["content"]
        )

"""
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


comment = {
    "login" : item.login,
    "content": item.content
}
"""


class FileChatStateManager(ManagerBase):

    default_state = []

    def __init__(self, ui_file_path, storage_path, logger):
        super().__init__(storage_path, FileChatStateManager.default_state, logger)
        self.ui_file_path = ui_file_path


    def UpdateUI(self, storage):
        with open(self.ui_file_path, "w") as ui:
            chat_state = "\n\n".join([FileChatStateManager.MessageDisplayString(message) for message in reversed(storage)]) + "\n"
            ui.write(chat_state)

 
    @staticmethod
    def BasicCheckCorrectness(storage):
        assert isinstance(storage, list), "File State Storage must be a list of messages"
        if len(storage) > 0:
            last_message = storage[-1]
            FileChatStateManager.CheckMessageIsCorrect(last_message)
    

    @staticmethod
    def CheckMessageIsCorrect(message):
        error_msg = "Mising key in mesage struct" 
        assert "id" in message, error_msg 
        assert "login" in message, error_msg
        assert "content" in message, error_msg
        assert "comments" in message, error_msg
        assert "reactions" in message, error_msg


    @staticmethod
    def CommentDisplayString(comment):
        return "- - - [{}]: {}".format(comment["login"], comment["content"])


    @staticmethod
    def ReactionsDisplayString(reactions):
        result = "[Like: {} | Dislike: {} | Love: {} | Fire: {} | Pile of Poo: {} ]".format(
            reactions["Thumbs Up"], 
            reactions["Thumbs Down"],
            reactions["Love"],
            reactions["Fire"],
            reactions["Pile of Poo"]
        )
        return result


    @staticmethod
    def MessageDisplayString(message):
        text_part = "[#{}][{}]: {}".format(message["id"], message["login"], message["content"])
        reactions_part = FileChatStateManager.ReactionsDisplayString(message["reactions"])
        comments_part = "\n".join([FileChatStateManager.CommentDisplayString(comment) for comment in message["comments"]])
        return "\n".join((text_part, reactions_part, comments_part))


