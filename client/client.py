import time
import http.client
import json
import threading
from lib.data_structures import ConsoleChatStateManager, FileChatStateManager 
import logging
from lib.loggers import CreateLogger


client_logger = CreateLogger("client", "log/log_client", logging.CRITICAL)

actions_data_path = "data/actions.json"
messages_data_path = "data/messages.json"
ui_path = "ui.txt"


console_chat_state_manager = ConsoleChatStateManager(actions_data_path, client_logger)
file_chat_state_manager = FileChatStateManager(ui_path, messages_data_path, client_logger)

def log_response_debug_info(response):
    client_logger.info("Status: {} and reason: {}".format(response.status, response.reason))
    client_logger.info("Response headers: {}".format(response.getheaders()))
    client_logger.info("Response body: {}".format(response.read()))


def _log_chat_state(manager):
    if isinstance(manager, ConsoleChatStateManager):
        client_logger.info("Console Chat state: {")
    if isinstance(manager, FileChatStateManager):
        client_logger.info("File Chat state: {")
    client_logger.info(manager.storage.Get())
    client_logger.info("}")
    

def update_one_of_chat_states(connection, state_manager):
    headers = dict() 
    if isinstance(state_manager, ConsoleChatStateManager):
        client_logger.info("Updating Actions state")
        headers={"Get-Chat-Actions": "true"}
    if isinstance(state_manager, FileChatStateManager):
        client_logger.info("Updating File Chat state")
        headers={"Get-Chat-State": "true"}
    connection.request("GET", url="/", headers=headers)
    new_state = json.loads(connection.getresponse().read().decode("utf-8"))
    state_manager.UpdateState(new_state)
    _log_chat_state(state_manager)


lock = threading.Lock()


def update_chat_states_thread_safe(connection):
    lock.acquire()
    update_one_of_chat_states(connection, file_chat_state_manager)
    update_one_of_chat_states(connection, console_chat_state_manager)
    lock.release()


def sign_in(connection, login, password):
    connection.request("POST", url="/",  headers={"Auth": "true", "Login": login, "Password": password})
    response = connection.getresponse() 
    log_response_debug_info(response) 
    if response.status == 200:
        print("Sign in OK.")
        return True
    if response.status == 401:
        print("Could not sign in: incorrect login and password")
        return False


def sign_up(connection, login, password):
    connection.request("POST", url="/",  headers={"Sign-Up": "true", "Login": login, "Password": password})
    response = connection.getresponse() 
    log_response_debug_info(response) 
    if response.status == 200:
        print("Sign up OK. Welcome to Comment-Reaction Chat, {}!".format(login))
        return True
    if response.status == 400:
        print("Could not sign up: login {} is already used".format(login)) 
        return False


def send_message(connection, message_text):
    logging.info("Sending message: {}".format(message_text)) 
    connection.request("POST", url="/",  headers={"Send-Message": "true"}, body=message_text) 
    response = connection.getresponse() 
    log_response_debug_info(response) 


def send_comment(connection, message_id, comment_text):
    logging.info("Sending comment to message_id {}: {}".format(message_id, comment_text)) 
    connection.request("POST", url="/",  headers={"Comment": "true", "Message-ID": message_id}, body=comment_text) 
    response = connection.getresponse()
    log_response_debug_info(response) 


def send_reaction(connection, message_id, reaction):
    logging.info("Sending reaction to message_id {}: {}".format(message_id, reaction)) 
    connection.request("POST", url="/",  headers={"Reaction": reaction, "Message-ID": message_id}) 
    response = connection.getresponse()
    log_response_debug_info(response) 


def suggest_and_load_last_actions(n_last):
    command = None
    while command not in ('y', 'n'): 
        print("Load last {} actions? Enter 'y' for 'yes' and 'n' for 'no'".format(n_last))
        command = input()
    if command == 'y':
        console_chat_state_manager.LoadLast(n_last)


def read_login_password():
    print("Enter login:")
    login = input()
    print("Enter password:")
    password = input()
    return login, password


def parse_command_and_execute(connection, command):
    if not command.startswith("/"):
        send_message(connection, command)
    else:
        tokens = command.split(" ")
        assert len(tokens) > 1, "There should be at least a word after command"
        command_code, message_id = tokens[0], tokens[1]

        if command_code in ("/c", "/comment"):
            send_comment(connection, message_id=message_id, comment_text=' '.join(tokens[2:]))
        else:
            command_code_to_reaction = {
                "/like" : "Thumbs Up",
                "/l" : "Thumbs Up",
                "/dislike" : "Thumbs Down",
                "/d" : "Thumbs Down",
                "/love" : "Love",
                "/f" : "Fire",
                "/fire" : "Fire",
                "/p" : "Pile of Poo",
                "/poo" : "Pile of Poo"
            } 
            if not command_code in command_code_to_reaction:
                print("Could not parse special command (one that starts with '/'). Please, enter your command again.")
                return
            send_reaction(connection, message_id=message_id, reaction=command_code_to_reaction[command_code])

    update_chat_states_thread_safe(connection)

connection = http.client.HTTPConnection(host="localhost", port=19000, timeout=10)

def worker_chat_update(sleep_time):
    while True:
        update_chat_states_thread_safe(connection) 
        time.sleep(sleep_time)


thread_chat_update = threading.Thread(target=worker_chat_update, args=(0.5,))
thread_chat_update.start()


""" USER CLI LOGIC """

print(""" - - - Comment-Reaction Chat - - -
Enter 's' to SIGN UP and any other key to continue and SIGN IN""")

if input() == 's':
    print("Please, SIGN UP.")
    sign_up_ok = False
    while not sign_up_ok:
        login, password = read_login_password()
        sign_up_ok = sign_up(connection, login, password)

print("Please, SIGN IN.")
sign_in_ok = False
while not sign_in_ok:
    login, password = read_login_password()
    sign_in_ok = sign_in(connection, login, password)

print("Welcome to Comment-Reaction Chat!")
n_last_messages_to_suggest = 10
suggest_and_load_last_actions(n_last_messages_to_suggest)

print("--- Now you can start typing ---")
while True:
    command = input()
    parse_command_and_execute(connection, command)

connection.close()

