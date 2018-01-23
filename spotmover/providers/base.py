
from abc import ABC, abstractmethod
from spotmover.dump import Dump


class ProviderError(Exception):
    pass


class ProviderAuthError(ProviderError):
    pass


class Provider(ABC):
    @abstractmethod
    def authenticate(self, *args, **kwargs) -> bool:
        pass

    def dump(self):
        raise NotImplementedError()

    def load_songs(self, data: Dump):
        raise NotImplementedError()

    def load_playlists(self, data: Dump, force: bool):
        raise NotImplementedError()
