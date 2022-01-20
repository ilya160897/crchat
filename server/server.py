import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from lib.data_structures import DataItem, Members, Actions, Messages, supported_reactions
import logging
from lib.loggers import CreateLogger

members_data_path = "data/members.json"
messages_data_path = "data/messages.json"
actions_data_path = "data/actions.json"

logger_srv = CreateLogger("server", "log/log_server", logging.INFO)

chat_members = Members(logger_srv, members_data_path)
chat_actions = Actions(logger_srv, actions_data_path)
chat_messages = Messages(logger_srv, messages_data_path)

client_ip_to_login = dict()

class CommentReactionChatServer(BaseHTTPRequestHandler):
    def show_request_debug_info(self, body):
        print("--- Client address --- ", self.client_address)
        print("Path: ", str(self.path))
        print("Headers: ", str(self.headers))
        print("Body: ", body)


    def _get_request_body_as_text(self):
        logger_srv.info("Getting request body")
        content_length = int(self.headers['Content-Length']) 
        post_data = self.rfile.read(content_length)
        body = post_data.decode('utf-8')
        logger_srv.info("Got request body")
        return body


    def send_response_code(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


    def do_GET(self):
        if "Get-Chat-State" in self.headers:
            self.handle_get_chat_state() 
        elif "Get-Chat-Actions" in self.headers:
            self.handle_get_chat_actions() 


    def do_POST(self):
        self.request_body = self._get_request_body_as_text()
        self.show_request_debug_info(self.request_body)

        if "Auth" in self.headers:
            self.handle_auth(self.headers["Login"], self.headers["Password"])
        elif "Sign-Up" in self.headers:
            self.handle_sign_up(self.headers["Login"], self.headers["Password"])
        elif "Send-Message" in self.headers:
            self.handle_chat_update("add_message")
        elif "Comment" in self.headers:
            self.handle_chat_update("add_comment")
        elif "Reaction" in self.headers:
            reaction = self.headers["Reaction"] 
            if not reaction in supported_reactions:
                logger_srv.error("Unsupported reaction {}!".format(reaction))
                self.send_response_code(400)
                return
            self.handle_chat_update("add_reaction")


    def handle_auth(self, login, password):
        if chat_members.Auth(login, password):
            self.send_response_code(200)
            welcome_response = "Welcome to Comment-Reaction Chat, {}!".format(login)
            self.wfile.write(welcome_response.encode('utf-8')) 
            client_ip_to_login[self.client_address[0]] = login
            logger_srv.info("Auth with login: {}, password: {} OK!".format(login, password))
            return
        logger_srv.info("Incorrect credentials: login: {}, password: {} !".format(login, password))
        self.send_response_code(401) # 401 Unauthorized response status code


    def handle_sign_up(self, login, password):
        if chat_members.IsLoginUsed(login):
            logger_srv.info("Registration: login {} is already used!".format(login))
            self.send_response_code(400)
            return
        item = DataItem("sign_up", login, None, password)
        chat_members.Add(item)
        chat_actions.Add(item)
        client_ip_to_login[self.client_address[0]] = login
        self.send_response_code(200)


    def handle_chat_update(self, action_type):
        if not self.client_address[0] in client_ip_to_login:
            print("client_ip_to_login: ", client_ip_to_login, "not found ip: ", self.client_address[0])
            self.send_response_code(401) # 401 Unauthorized response status code
            return

        item = DataItem(
            action_type = action_type, 
            login = client_ip_to_login[self.client_address[0]], 
            message_id = chat_messages.Size() if action_type == "add_message" else self.headers["Message-ID"], 
            content = self.headers["Reaction"] if action_type == "add_reaction" else self.request_body
        )
        chat_messages.Add(item)
        chat_actions.Add(item)
        self.send_response_code(200)


    def handle_get_chat_state(self):
        logger_srv.info("Handling get chat state")
        self.send_response_code(200)
        self.wfile.write(chat_messages.GetString().encode('utf-8'))
        

    def handle_get_chat_actions(self):
        logger_srv.info("Handling get chat actions")
        self.send_response_code(200)
        self.wfile.write(chat_actions.GetString().encode('utf-8'))


def run(server_class=HTTPServer, handler_class=CommentReactionChatServer, addr="localhost", port=19000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting server on {addr}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=19000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)

