

class Dump:
    def __init__(self, data):
        self.set_data(data)

    def set_data(self, data):
        self.data = data
        self.origin = data["origin"]
        if "albums" not in data:
            data["albums"] = []

    @property
    def songs(self):
        return self.data["songs"]

    @property
    def playlists(self):
        return self.data["playlists"]

    @property
    def albums(self):
        return self.data["albums"]

    def group_songs_by_albums(self, source):
        seen = set()
        for song in source:
            key = (song["artist"], song["album"])
            if key in seen:
                continue

            seen.add(key)
            yield key

    def remove_songs_by_albums(self):
        albums_set = set(self.albums)
        new_songs = []
        for song in self.data["songs"]:
            key = (song["artist"], song["album"])
            if key not in albums_set:
                new_songs.append(song)

        self.data["songs"] = new_songs
