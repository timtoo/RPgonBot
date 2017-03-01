# RPGonBot - a reddit repost bot

This bot was written for a single purpose, but its engineered with generic use
in mind, so it shouldn't be too hard to adapt to other purposes. A few things
remain hard coded, but they are pretty obvious.

The purpose this bot was created for is to repost new /r/gonwild submissions to a
subreddit that is not flagged NSFW, and to remove the square brackets from post title
(which is supposed to be jokingly referring to the practices of the well-known porn
subreddit which has a similar name. The /r/gonwild subreddit was created as a parody
of the similarly named porn subreddit, but only posts geometrical animations.

## Features

- uses the [praw](https://praw.readthedocs.io) reddit bot library.
  (This needs to be installed seperately and available to load.)
- uses local SQLite3 database for logging and keeping track of data
- supports flairing crossposts ("x-post" flair is hard coded)
- a comment is added to every crosspost pointing to the original post
- single script file

## praw.ini

The bot requires a configuration file called praw.ini, containing the following:

    [rpgonbot]
    client_id=<reddit api id>
    client_secret=<reddit api secret>
    password=<password of reddit bot user>
    username=<reddit username of bot>
    owner=ragica
    source=gonwild
    destination=geomation
    source_limit=10
    debug=1

### General script help:

    usage: rpgonbot.py [-h] [-c <praw.ini>] [-b <rpgonbot>] {run,test,show} ...

    Reddit repost bot

    positional arguments:
      {run,test,show}
        run                 Run the bot and repost new posts
        test                Various testing fuctions
        show                Bot information

    optional arguments:
      -h, --help            show this help message and exit
      -c <praw.ini>, --config <praw.ini>
                            Name of config file to load
      -b <rpgonbot>, --bot <rpgonbot>
                            Name of bot (used in config file, and user agent, and
                            other places)

### Run command help:

    usage: rpgonbot.py run [-h] [--reset RESET]

    optional arguments:
      -h, --help     show this help message and exit
      --reset RESET  Reset the last repost date to the given reddit submission ID
                     (eg. 5wxv94)

### Show command help:

    usage: rpgonbot.py show [-h] [--all] [--database] [--log [count]]
                            [--reposts [count]] [--source-posts]

    optional arguments:
      -h, --help         show this help message and exit
      --all              Show all (or most) data
      --database         Show info about database
      --log [count]      Show latest # log entries
      --reposts [count]  Show latest # reposts logged
      --source-posts     Show latest posts in source subreddit

### Test command help:

    usage: rpgonbot.py test [-h] [--clean-title "TITLE TO CLEAN"]
                            [--flair-id "FLAIR TEXT"] [--post-id ID]

    optional arguments:
      -h, --help            show this help message and exit
      --clean-title "TITLE TO CLEAN"
                            Test the title cleaner
      --flair-id "FLAIR TEXT"
                            Return flair ID for the given flair (uses most recent
                            repost, if post-id not specified)
      --post-id ID          Submission ID to use with tests if needed


