spotmover
~~~~~~~~~

spotmover is a software which migrates music library, playlists and liked songs
from Google Play Music to Spotify service.

This is a working software which helped me to move my library, however I think 
it is still in pre-alpha stage so it should be used with caution.

How to use
~~~~~~~~~~
Before you start using it, make sure you have a valid subscription to Google 
Play Music. Also, I recommend to have a new spotify account.

Then, you need to create a config file in ``$HOME/.config/spotmover/config.ini``.
This should look like this:

.. code-block::

    [google]
    username=<your username@gmail.com>
    password=<your google password or application password>

    [spotify]
    username=<spotify username>
    client_id=<client id for the application>
    client_secret=<client secret for the application>
    redirect_uri=<redirect uri of the application>

For the last 3 entries, you need to create a new application in spotify 
developer console and copy&paste those settings to here.

Make sure you copied the redirect_uri exactly as shown on the dashboard.

Moving the library
~~~~~~~~~~~~~~~~~~
You can dump your google library to a json file by running:

.. code-block::

    spotmover dump google -o dump.json

Then you can load the dump.json into spotify:

.. code-block::

    spotmover load spotify dump.json

Troubleshooting
~~~~~~~~~~~~~~~
By setting the ``SPOTMOVER_DEBUG`` environment variable to ``1``, you will be
dropped to a debugger when there's an unhandled exception.

Use ``-v`` to have more verbose output.

