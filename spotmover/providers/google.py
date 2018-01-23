
import logging

from gmusicapi import Mobileclient
from spotmover.cache import DiskCache
from .base import Provider, ProviderAuthError
from collections import defaultdict

logger = logging.getLogger(__name__)


class GoogleProvider(Provider):
    def __init__(self):
        self._setup_logging()
        self.api = Mobileclient(debug_logging=self._is_debug_logging())
        self._authenticated = False
        self._cache = self.init_cache()
        self._lazy_credentials = None

    def init_cache(self):
        return {}

    def _is_debug_logging(self):
        loglevel = logger.getEffectiveLevel()
        return loglevel == logging.DEBUG

    def _setup_logging(self):
        gmusic_logger = logging.getLogger("gmusicapi")

        if self._is_debug_logging():
            gmusic_logger.setLevel(logging.DEBUG)
        else:
            gmusic_logger.setLevel(logging.WARN)

    def lazy_authenticate(self, username, password):
        self._lazy_credentials = (username, password)

    def authenticate(self, username, password) -> bool:  # pylint: disable=W0221
        if self.is_authenticated():
            return True
        logger.info("Authenticating with google")
        result = self.api.login(username, password, Mobileclient.FROM_MAC_ADDRESS)
        if result:
            logger.info("Authentication succeed")
        else:
            logger.error("Authentication unsuccessful")
        self._authenticated = result
        return result

    def is_authenticated(self):
        return self._authenticated

    def need_authenticated(self):
        if not self.is_authenticated() and self._lazy_credentials:
            self.authenticate(*self._lazy_credentials)
            self._lazy_credentials = None

        if not self.is_authenticated():
            raise ProviderAuthError("Google provider is not authenticated")

    def get_all_songs(self):
        if "songs" in self._cache:
            logger.info("Using cache for songs")
            return self._cache["songs"]

        self.need_authenticated()
        logger.info("Fetching songs")
        songs = self.api.get_all_songs()
        retval = []

##        track_counts = defaultdict(int)
##        total_tracks = {}
#        import pdb
#        pdb.set_trace()
        for song in songs:
            ##            album_key = (song["albumArtist"], song["album"], song["discNumber"])
            ##            track_counts[album_key] += 1
            ##            total_tracks[album_key] = song["totalTrackCount"]

            retval.append({
                "artist": song["albumArtist"],
                "album": song["album"],
                "title": song["title"],
            })

# for album_key in total_tracks:
# if track_counts[album_key] == total_tracks[album_key]:
##                print("Full album", album_key)

        self._cache["songs"] = retval
        logger.info("Number of songs: {}".format(len(retval)))
        return retval

    def get_all_playlists(self):
        if "playlists" in self._cache:
            logger.info("Using cache for playlists")
            return self._cache["playlists"]

        self.need_authenticated()
        logger.info("Fetching playlists")
        playlists = self.api.get_all_user_playlist_contents()

        retval = []
        for playlist in playlists:
            if playlist["deleted"]:
                continue

            name = playlist["name"]
            tracks = []
            for playlist_track in playlist["tracks"]:
                if playlist_track["source"] == "2":
                    track = playlist_track["track"]
                    track_data = {
                        "artist": track["albumArtist"],
                        "album": track["album"],
                        "title": track["title"],
                    }
                    tracks.append(track_data)

            retval.append({
                "name": name,
                "tracks": tracks,
            })

        self._cache["playlists"] = retval

        for item in retval:
            logger.info("Playlist: {}".format(item["name"]))
        return retval

    def dump(self):
        retval = {
            "songs": self.get_all_songs(),
            "playlists": self.get_all_playlists(),

        }
        return retval


class CachedGoogleProvider(GoogleProvider):
    def init_cache(self):
        return DiskCache("spotmover-google")
