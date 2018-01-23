import logging

import spotipy
from spotmover.providers.spotify.util import obtain_token_localhost
from spotmover.providers.base import Provider, ProviderAuthError
from spotmover.dump import Dump
from spotmover.cache import DiskCache

logger = logging.getLogger(__name__)


def confirm(msg):
    answer = input(msg + " ")
    return answer.lower() in ("y", "yes")


class NotFoundError(Exception):
    pass


class SpotifyProvider(Provider):
    def __init__(self):
        self.token = None
        self.api = None
        self._cache = self.init_cache()
        self.username = None

    def init_cache(self):
        return {}

    def authenticate(self, username: str, client_id: str, client_secret: str, redirect_uri: str):  # pylint: disable=W0221
        scope = 'user-library-modify playlist-modify-private playlist-modify-public playlist-read-private playlist-read-collaborative'
        token = obtain_token_localhost(username, client_id, client_secret, redirect_uri, scope=scope)
        if not token:
            raise ProviderAuthError("Unable to authenticate user {}".format(username))
        self.token = token
        self.api = spotipy.Spotify(auth=token)
        self.username = username

    def is_authenticated(self):
        return self.api is not None

    def need_authentication(self):
        if not self.is_authenticated():
            raise ProviderAuthError("User is not authenticated")

    def get_album(self, artist, album):
        album_cache = self._cache.get("albums")
        if album_cache is None:
            self._cache["albums"] = {}
            album_cache = self._cache.get("albums")

        cache_key = (artist, album)
        if cache_key in album_cache:
            cache_value = album_cache[cache_key]
            if isinstance(cache_value, Exception):
                raise cache_value
            else:
                return album_cache[cache_key]

        self.need_authentication()

        result = self.api.search("artist:{} album:{}".format(artist, album), type="album")

        album_l = album.lower()

        if len(result["albums"]["items"]) == 0:
            exc = NotFoundError("No such album: {}".format(album))
            album_cache[cache_key] = exc
            self._cache["albums"] = album_cache
            raise exc

        retval = None
        for album in result["albums"]["items"]:
            if album["name"].lower() == album_l:
                retval = album
                break

        if not retval:
            exc = NotFoundError("No exact match for the album: {}".format(album))
            album_cache[cache_key] = exc
            self._cache["albums"] = album_cache
            raise exc

        album_cache[cache_key] = retval
        self._cache["albums"] = album_cache
        return retval

    def fetch_all(self, results, items_key="items", limit=50):
        retval = results[items_key]

        while results["next"]:
            results = self.api.next(results)
            retval.extend(results[items_key])
        return retval

    def iter_current_user_saved_albums(self):
        self.need_authentication()
        saved_items = self.fetch_all(self.api.current_user_saved_albums())

        for album in saved_items:
            album_name = album["album"]["name"]
            for artist in album["album"]["artists"]:
                artist_name = artist["name"]

                yield (artist_name, album_name)

    def load_songs(self, data: Dump):
        self.need_authentication()

        album_ids = []
        not_found = []
        current_albums = set([(x[0].lower(), x[1].lower()) for x in self.iter_current_user_saved_albums()])

        for src_album in data.albums:
            src_album_artist = (src_album["artist"], src_album["album"])
            src_album_artist_lower = (src_album["artist"].lower(), src_album["album"].lower())
            if src_album_artist_lower in current_albums:
                logger.info("Already added; {}: {}".format(*src_album_artist))
                continue

            try:
                album = self.get_album(*src_album_artist)
            except NotFoundError:
                logger.warn("Not found; {}: {}".format(*src_album_artist))
                not_found.append(src_album_artist)
            else:
                logger.info("Album found; {}: {}".format(*src_album_artist))
                album_ids.append(album["id"])

        logger.info("Albums not found in spotify:")
        for album in not_found:
            logger.info("    {}: {}".format(*album))

        logger.info("Found {} albums, saving...".format(len(album_ids)))

        for start_idx in range(0, len(album_ids), 50):
            self.api.current_user_saved_albums_add(albums=album_ids[start_idx: start_idx + 50])
        logger.info("Done.")

    def find_song(self, artist, album, song):
        if "find_song" not in self._cache:
            cache_obj = self._cache["find_song"] = {}
        else:
            cache_obj = self._cache["find_song"]

        cache_key = (artist, album, song)
        if cache_key in cache_obj:
            cache_value = cache_obj[cache_key]
            if isinstance(cache_value, Exception):
                raise cache_value
            else:
                return cache_value

        result = self.api.search("artist:{} album:{} track:{}".format(artist, album, song), type="track")
        items = result["tracks"]["items"]
        if len(items) == 0:
            logger.warning("find_song {}/{} {}: NOT FOUND".format(artist, album, song))
            exc = NotFoundError("Song not found: {}".format(song))
            cache_obj[cache_key] = exc
            self._cache["find_song"] = cache_obj
            raise exc

        if len(items) == 1:
            logger.info("find_song {}/{} {}: FOUND".format(artist, album, song))
            return items[0]["id"]

        for item in items:
            item_album_name = item["album"]["name"]
            item_track_name = item["name"]
            for artist_result in item["artists"]:
                item_artist_name = artist_result["name"]
                if item_album_name.lower() == album.lower() and \
                        item_artist_name.lower() == artist.lower() and \
                        item_track_name.lower() == song.lower():
                    logger.info("find_song {}/{} {}: FOUND".format(artist, album, song))
                    cache_obj[cache_key] = item["id"]
                    self._cache["find_song"] = cache_obj
                    return item["id"]

        logger.warn("find_song {}/{} {}: NOT FOUND".format(artist, album, song))
        exc = NotFoundError("No exact match for song: {}".format(song))
        cache_obj[cache_key] = exc
        self._cache["find_song"] = cache_obj
        raise exc

    def get_track_ids_for_songs(self, songs):
        track_ids = []
        not_found = []
        for song in songs:
            artist = song["artist"]
            album = song["album"]
            title = song["title"]
            try:
                track_id = self.find_song(artist, album, title)
            except NotFoundError:
                not_found.append(song)
                logger.warning("Not found: {}/{}".format(artist, title))
                continue
            track_ids.append(track_id)
        return (track_ids, not_found)

    def create_playlist(self, name, track_ids):
        logger.info("Creating playlist '{}' with {} tracks".format(name, len(track_ids)))
        playlist = self.api.user_playlist_create(self.username, name, public=False)
        playlist_id = playlist["id"]
        for start_idx in range(0, len(track_ids), 100):
            self.api.user_playlist_add_tracks(self.username, playlist_id, track_ids[start_idx:start_idx + 100])

    def load_playlist(self, playlist, force: bool):
        name = playlist["name"]
        songs = playlist["tracks"]

        track_ids, not_found = self.get_track_ids_for_songs(songs)
        if len(track_ids) == 0:
            logger.error("No songs found")
            return
        if len(track_ids) != len(songs):
            logger.warning("Some songs were not found")
            if not force:
                for song in not_found:
                    logger.info("- {artist}/{album}: {title}".format(**song))

                if not confirm("Are you sure to create the playlist? (y/n)"):
                    logger.info("Skipping...")
                    return

        self.create_playlist(name, track_ids)

    #            tracks = self.api.user_playlist(self.username, playlist["id"], fields="tracks")

    # self.api.user_playlist_add_tracks(self.username, playlist_id, track_ids)

    def load_playlists(self, data: Dump, force: bool, force_create: bool):
        self.need_authentication()
        current_playlists = {x["name"]: x for x in self.fetch_all(self.api.current_user_playlists())}
        #        import pdb
        #        pdb.set_trace()
        for playlist in data.playlists:
            name = playlist["name"]
            if not confirm("Do you want to import playlist '{}'? (y/n)".format(name)):
                logger.info("Skipping...")
                continue
            if name in current_playlists and not force_create:
                logger.info("Playlist {} already exists, skipping".format(name))
                continue

            self.load_playlist(playlist, force)


class CachedSpotifyProvider(SpotifyProvider):
    def init_cache(self):
        return DiskCache("spotmover-spotify")
