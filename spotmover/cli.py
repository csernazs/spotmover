# pylint: disable=W1202,C0301

import sys
import os
import logging
import json

import click
from texttable import Texttable

from spotmover.providers.google import GoogleProvider, CachedGoogleProvider
from spotmover.providers.spotify import SpotifyProvider, CachedSpotifyProvider
from spotmover.providers.base import ProviderAuthError

from .config import Config, ConfigError
from .dump import Dump

pjoin = os.path.join
logger = logging.getLogger(__name__)


@click.group()
def dump():
    pass


@click.group()
def load():
    pass


@click.command("google")
@click.option("-o", "--output", help="Output file to dump", required=True)
@click.option("--no-cache", is_flag=True, help="Do not use on-disk cache")
@click.pass_context
def dump_google(ctx, output, no_cache):
    config = ctx.obj["CONFIG"]
    if not config.google:
        raise click.UsageError("'google' section is missing from config")

    if no_cache:
        provider = GoogleProvider()
    else:
        provider = CachedGoogleProvider()
    provider.lazy_authenticate(config.google.username, config.google.password)

    logger.info("Collecting data")
    try:
        data = provider.dump()
    except ProviderAuthError:
        ctx.abort()

    data["origin"] = "google"
    with open(output, "w") as outfile:
        json.dump(data, outfile, indent=4)

    logger.info("Dump completed to {}".format(output))


def edit_albums(albums):
    table = Texttable(max_width=0)
    table.set_deco(Texttable.VLINES)
    table.add_rows(albums, header=False)
    albums_text = click.edit(table.draw())
    if albums_text is None:
        return albums

    retval = []
    for line in albums_text.split("\n"):
        if line == "" or line.startswith("#"):
            continue
        retval.append(tuple([x.strip() for x in line.split("|")]))

    return retval


@click.command("spotify")
@click.argument("input_path")
@click.option("-f", "--force", is_flag=True, help="No interactive use")
@click.option("-p", "--force-playlists", is_flag=True, help="Re-create playlists even if they exist")
@click.option("--no-cache", is_flag=True, help="Do not use on-disk cache")
@click.pass_context
def load_spotify(ctx, input_path, force, force_playlists, no_cache):
    config = ctx.obj["CONFIG"]
    if not config.spotify:
        raise click.UsageError("'spotify' section is missing from config")

    with open(input_path, "r") as infile:
        data = Dump(json.load(infile))

    logger.info("Collection loaded with {} songs and {} playlists".format(len(data.songs), len(data.playlists)))

    albums = sorted(data.group_songs_by_albums(data.songs))
    if not force:
        albums = edit_albums(albums)

    if len(data.albums) > 0:
        raise NotImplementedError()

    albums = [{"artist": x[0], "album": x[1]} for x in albums]
    data = Dump({"songs": [], "albums": albums, "playlists": data.playlists, "origin": data.origin})

    if no_cache:
        provider = SpotifyProvider()
    else:
        provider = CachedSpotifyProvider()

    provider.authenticate(
        config.spotify.username,
        config.spotify.client_id,
        config.spotify.client_secret,
        config.spotify.redirect_uri
    )
    return
    
    provider.load_songs(data)
    provider.load_playlists(data, force, force_playlists)


@click.group()
@click.option("-c", "--config", "config_path", help="Configuration file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def click_main(ctx, config_path, verbose):
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(msg)s")

    if not config_path:
        config_path = pjoin(click.get_app_dir("spotmover"), "config.ini")

    try:
        open(config_path).close()
    except IOError:
        raise click.UsageError("Unable to open config file: {}".format(config_path))

    logger.debug("Opening config file {}".format(config_path))
    try:
        config = Config.from_file(config_path)
    except ConfigError as err:
        print(err)
        raise ctx.abort()
    ctx.obj = {"CONFIG": config}
    return 0


def main():
    try:
        click_main()  # pylint: disable=E1120
    except Exception:  # pylint: disable=W0703
        if "SPOTMOVER_DEBUG" in os.environ:
            import pdb
            import traceback
            type, value, tb = sys.exc_info()  # pylint: disable=W0612
            traceback.print_exc()
            pdb.post_mortem(tb)
        raise


click_main.add_command(dump)
click_main.add_command(load)

dump.add_command(dump_google)
load.add_command(load_spotify)
