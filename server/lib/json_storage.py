import os
import json

class JsonStorage:
    def __init__(self, data_path, default_state, logger):
        self.data_path = data_path
        self.default_state = default_state
        self.logger = logger

        if not os.path.isfile(self.data_path):
            self.logger.info(
                "Data with the path {} does not exist, creating default state {}"
                .format(self.data_path, self.default_state)
            )
            with open(self.data_path, "w") as file:
                file.write(json.dumps(default_state))
        else:
            self.logger.info(
                "Data with the path {} already exists"
                .format(self.data_path)
            )


    def Get(self):
        self.logger.info("Loading storage from {}".format(self.data_path))
        with open(self.data_path, "r") as file:
            state = json.load(file)
            return state


    def Update(self, new_state):
        self.logger.info("Updating state of {}".format(self.data_path))
        with open(self.data_path, "w") as file:
            file.write(json.dumps(new_state))

