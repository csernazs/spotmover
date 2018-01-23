from configobj import ConfigObj


class ConfigError(Exception):
    pass


class GoogleCredentials:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @classmethod
    def from_dict(cls, config_dict):
        try:
            return cls(config_dict["username"], config_dict["password"])
        except KeyError as err:
            raise ConfigError("No such key: {}".format(err))


class SpotifyCredentials:
    def __init__(self, username, client_id, client_secret, redirect_uri):
        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @classmethod
    def from_dict(cls, config_dict):
        return cls(
            config_dict["username"],
            config_dict["client_id"],
            config_dict["client_secret"],
            config_dict["redirect_uri"]
        )


class Config:
    def __init__(self, config_dict):
        self.google = None
        self.spotify = None
        if "google" in config_dict:
            self.google = GoogleCredentials.from_dict(config_dict["google"])
        if "spotify" in config_dict:
            self.spotify = SpotifyCredentials.from_dict(config_dict["spotify"])

    @classmethod
    def from_file(cls, path):
        config_dict = ConfigObj(path)
        return cls(config_dict)
