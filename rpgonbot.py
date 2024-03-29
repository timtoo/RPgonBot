#!/usr/bin/env python

"""Bot for taking new posts from one subreddit and reposting them to another.

"""

import sys
import sqlite3
import datetime
import os
import re
import configparser
import argparse
import praw

DEFAULT_BOT_NAME='rpgonbot'
__version__ = '0.3'

def debug(*s):
    if DEBUG:
        if len(s)>1:
            print(datetime.datetime.now(), repr(s))
        else:
            print(datetime.datetime.now(), s[0].encode('utf-8'))


def print_all_fields(o):
    """Prints all attributes of object not starting with _"""
    for f in dir(o):
        if f.startswith('_'):
            continue
        a = getattr(o, f)
        print ("{}: {} [{}]".format(f, a, type(a)))


class RPGonBot(object):

    # look for any type of brackets with all non-whitespace and not "OC" between them.
    re_title_brackets = re.compile(r"[[({](?!OC)([^\s]*)[])}]")

    silly_thesaurus = {
        'curve': 'arc',
        'hole': 'empty space',
        'leg': 'appendage',
        'i love': 'it\'s nice',
        'pole': 'line',
        'curvy': 'wavy',
        'you': 'some things',
        'arm': 'limb',
        'pump': 'pulse',
        'pumping': 'pulsing',
        'hard': 'solid',
        'frisky': 'whimsical',
        'into me': 'into something',
        'in me': 'in object',
        'stick it': 'geometry',
        'mmf': '',
        'ffm': '',
        'first post': 'hello',
        'be gentle': 'such good',
        'baby': 'infant',
        'push': 'apply effort to',
        'deeper': 'more subsantially',
        'spread': 'distribute',
        'pleasure': 'good feeling',
    }

    def __init__(self, source, destination):
        self._db = None
        self._flairs = {}
        self._subreddit_source = None
        self._subreddit_destination = None
        self.source = source
        self.destination = destination

    @property
    def db(self):
        """Returns db connection"""
        if self._db is None:
            if not os.path.exists(dbfn):
                debug("creating DB")
                self._db = sqlite3.connect(dbfn)
                self.db_create()
                self._db.commit()
            else:
                self._db = sqlite3.connect(dbfn)

        return self._db

    @property
    def subreddit_destination(self):
        if self._subreddit_destination is None:
            self._subreddit_destination = reddit.subreddit(self.destination)
        return self._subreddit_destination

    @property
    def subreddit_source(self):
        if self._subreddit_source is None:
            self._subreddit_source = reddit.subreddit(self.source)
        return self._subreddit_source

    def dblog(self, code, text):
        self.db.execute("INSERT INTO rp_log (code, data) VALUES (?, ?)",
                (code, text))
        self.db.commit()

    def get_flair_id(self, flair_text, submission=None, subreddit=None):
        """return the flair_template_id for the given flair_text available
            for the given submission object. User link flairs need to be
            enabled on the subreddit.

            (Flairs could be looked up based on subreddit, but the user needs
            flair moderator permission to access.)

            All flairs are cached in dictionary so lookup only has to be done once.
        """
        if submission is None:
            sub = subreddit or self.subreddit_destination
            choices = sub.flair
            attr = 'display_name'
        else:
            sub = submission
            choices = sub.flair.choices
            attr = 'title'

        if flair_text not in self._flairs:
            try:
                for f in choices():
                    self._flairs[f['flair_text']] = f['flair_template_id']
            except Exception as e:
                debug("Could not load flairs for subreddit: {} ({}): {}".format(
                        getattr(sub, attr), sub.id, e))

        return self._flairs.get(flair_text)

    def db_create(self):
        statements = (
            """
            CREATE TABLE rp_post (
                added       integer NOT NULL DEFAULT (strftime('%s', 'now')),
                updated     integer NOT NULL DEFAULT (strftime('%s', 'now')),
                created_utc integer NOT NULL,
                reddit_id   text  NOT NULL PRIMARY KEY,
                author      text,
                score       integer,
                title       text,
                url         text,
                subreddit   text NOT NULL,
                num_comments integer,
                permalink   text,
                repost_id   text UNIQUE,
                commnt_id   text UNIQUE
                );
            """,
            """
            CREATE INDEX rp_post_created_utc_i ON rp_post (created_utc);
            """,
            """
            CREATE TABLE rp_data (
                subreddit text NOT NULL,
                key text NOT NULL,
                value text,
                PRIMARY KEY (subreddit, key)
                );
            """,
            """
            CREATE TRIGGER update_rp_data AFTER INSERT ON rp_post BEGIN
                UPDATE rp_data SET value = NEW.created_utc
                        WHERE subreddit=NEW.subreddit AND key='last_created_utc';
                UPDATE rp_data SET value = NEW.reddit_id
                        WHERE subreddit=NEW.subreddit AND key='last_post_id';
            END;
            """,
            """
            CREATE TABLE rp_log (
                id          integer PRIMARY KEY,
                date        integer NOT NULL DEFAULT (strftime('%s', 'now')),
                code        integer NOT NULL,
                data        text
            );
            """
        )

        for sql in statements:
            self.db.execute(sql)

        self.db.commit()
        self.dblog(0, 'Created database')

    def clean_title(self, text):
        """Clean up the gonwild title"""
        return self.hack_title(self.re_title_brackets.sub(r'\1', text))

    def hack_title(self, text):
        count = 0
        index = 0
        #print ('--', text)
        for k, v in self.silly_thesaurus.items():
            r = re.compile(r"\b({})(s?)\b".format(k), re.I)
            while True:
                count += 1
                if count>999:
                    break
                m = r.search(text, index)
                if not m:
                    break

                word = text[m.start(1):m.end(1)]
                #print(m, word)
                replacement = self.text_replacement(word) + text[m.start(2):m.end(2)]
                text = text[:m.start(0)] + replacement + text[m.end(0):]
                index = m.start(0) + (len(replacement) or 1)

        return text.strip()

    def text_replacement(self, word):
        """Find matching thesaurus item, and try to match case, etc"""
        result = self.silly_thesaurus.get(word.lower(), '')
        if result:
            if word == word.lower():
                pass
            elif word == word.upper():
                result = result.upper()
            elif word == word.capitalize():
                result = result.capitalize()
            elif word == word[:1].upper() + word[1:]:
                result = result[:1].upper() + result[1:]

        return result

    def crosspost(self, post, flair=None):
        """Create the crosspost from the provided submission; also add comment with link back."""
        title = self.clean_title(post.title)
        title = title + " - [via: " + post.author.name + "]"

        try:
            submission = self.subreddit_destination.submit(title,
                    url=post.url, resubmit=False, send_replies=False)
        except praw.exceptions.APIException as e:
            self.dblog(1, "{} : {} : {}".format(post.id, post.title, e))
            debug(str(e), post.title)
            return None

        flair_id = self.get_flair_id('x-post', submission=submission)
        submission.flair.select(flair_id)

        # if one uses /u/ in front of author/owner name they get private message on every
        # post due to being "mentioned" -- rather spammy
        comment_template = """Thanks to [Original Submission]({permalink}) by {author}
______

^^^Reposted ^^^by ^^^RPGonBot ^^^^(reddit ^^^user: ^^^""" + OWNER + ")"

        comment = submission.reply(comment_template.format(
                permalink=post.permalink, author=post.author.name))

        try:
            self.db.execute("""INSERT INTO rp_post
                    (created_utc, reddit_id, author, score,
                    title, url, subreddit, num_comments, permalink,
                    repost_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                        int(post.created_utc),
                        post.id,
                        post.author.name,
                        post.score,
                        post.title,
                        post.url,
                        self.source,
                        post.num_comments,
                        post.permalink,
                        submission.id
                    ))
            self.db.commit()
        except:
            print_all_fields(post)
            raise

        debug("Crossposted: <{}> {}".format(post.id, title))
        return submission

    def db_create_rp_data(self):
        """create the rows to store the last timestamp and id crossposted"""
        debug("Creating rp_data for sub", self.source)
        self.db.execute("INSERT INTO rp_data VALUES (?, 'last_created_utc', 0);", (self.source,))
        self.db.execute("INSERT INTO rp_data VALUES (?, 'last_post_id', NULL);", (self.source,))
        self.dblog(0, 'Created rp_data for: {}'.format(self.source))
        self.db.commit()

    def db_reset_rp_data(self, reddit_id):
        """find the timestamp of a submission and use it to reset the database to"""
        submission = next(reddit.submission(reddit_id))
        if submission:
            self.db.execute("""UPDATE rp_data SET value=? WHERE
                    subreddit=? and key='last_post_id'""", (reddit_id, self.source))
            self.db.execute("""UPDATE rp_data SET value=? WHERE
                    subreddit=? and key='last_post_id'""", (reddit_id, submission.created_utc))
            self.db.log(4, 'Reset rp_data for {} to post {} ({})'.format(
                    self.source, reddit_id, submission.created_utc))
            self.db.commit()

    def db_fetch_rp_data(self, subreddit, key):
        """Fetch value from the table that records various "last submission" data.
        And do some data casting in one case.
        """
        result = self.db.execute("""SELECT value FROM rp_data
                WHERE subreddit=? AND key=?""", (subreddit,key)).fetchone()
        if result:
            if key == 'last_created_utc':
                result = int(result[0])
            else:
                result = result[0]
        return result

    def check_for_posts(self):
        """Check for new posts in the source subreddit, and crosspost any found.

        Was going to update local database with old submission comment and score numbers,
        but then didn't.
        """
        submissions = self.subreddit_source.new(limit=source_limit)
        new_posts = []

        # load the last post data for the sub
        last_created_utc = self.db_fetch_rp_data(self.source,'last_created_utc')
        if last_created_utc is None:
            self.db_create_rp_data()
            last_created_utc = 0
        last_post_id = self.db_fetch_rp_data(self.source,'last_post_id')

        # go through posts and find new ones
        desc_format = "[{} - {}]: {} ({})"
        for s in submissions:
            desc = desc_format.format(
                    s.id,
                    datetime.datetime.utcfromtimestamp(int(s.created_utc)),
                    s.title,
                    s.score)
            # the equals is included in the wierd chance two things have same timestamp
            # dupliate is still rejected later
            if int(s.created_utc) >= last_created_utc:
                if s.score > 0:
                    if not s.is_self:
                        new_posts.insert(0,s)
                    else:
                        self.dblog(2, "Ignoring (self  post): " + desc)
                else:
                    self.dblog(2, "Ignoring (low score): " + desc)
            else:
                debug("Ignoring (older post): " + desc)

        # list of new posts in ascending chronological order
        for np in new_posts:
            if np.id != last_post_id:
                self.crosspost(np)
            else:
                debug("Ignoring (last xpost): " + desc_format.format(last_post_id,
                        datetime.datetime.utcfromtimestamp(int(np.created_utc)),
                        np.title, np.score))

    def show_database(self):
        print("Bot name: {} (database: {})".format(args.bot, dbfn))
        print("User-agent: " + my_user_agent)
        print("Repost records: " + str(self.db.execute(
                """SELECT count(*) FROM rp_post""").fetchone()[0]))
        print("Log entries: " + str(self.db.execute(
                """SELECT count(*) FROM rp_log""").fetchone()[0]))

        print("Repost data:")

        result = self.db.execute("""SELECT subreddit, key, value FROM
                rp_data ORDER BY subreddit, key""").fetchall()
        if len(result)>0:
            for r in result:
                if r[1] == 'last_created_utc' and r[2] != '0':
                    r = (r[0],r[1],datetime.datetime.utcfromtimestamp(int(r[2])))
                print("{:<16}{:<18}{}".format(*r))
        else:
            print("No rp_data found")

    def show_reposts(self, count):
        print("{} Most Recent Reposts:".format(count))

        result = self.db.execute("""SELECT
                    strftime('%Y-%m-%d %H:%M:%S', added, 'unixepoch') AS added_ts,
                    strftime('%Y-%m-%d %H:%M:%S', created_utc, 'unixepoch') AS created_ts,
                    reddit_id, author, substr(title,1,16), repost_id, substr(subreddit,1,8), url, permalink
                FROM rp_post
                ORDER BY added DESC LIMIT ?""", (count,))

        rows = 0
        format = "{0} ({1}) {6:<8} {4:<16} {2} {5}"

        for r in result:
            print(format.format(*r))
            rows+=1

        if rows == 0:
            print("No reposts found")


    def show_log(self, count):
        print("{} Most Log Entries:".format(count))

        result = self.db.execute("""SELECT
                    id, strftime('%Y-%m-%d %H:%M:%S', date, 'unixepoch') AS ts,
                    code, data
                FROM rp_log
                ORDER BY id DESC LIMIT ?""", (count,))

        rows = 0
        format = "[{1}] ({2}) {3}"

        for r in result:
            print(format.format(*r))
            rows+=1

        if rows == 0:
            print("No log entries found")

    def show_posts(self, subreddit_object):
        print("{} most recent posts in /r/{}:".format(source_limit, subreddit_object.display_name))
        submissions = subreddit_object.new(limit=source_limit)

        format = "{count:02}.[{timestamp}] <{id}> {title} - {domain} ({ups}^)"

        count = 1
        for s in submissions:
            print(format.format(
                    count = count,
                    timestamp = datetime.datetime.utcfromtimestamp(int(s.created_utc)),
                    id = s.id,
                    title = s.title,
                    domain = s.domain,
                    ups = s.ups
                    ))
            count += 1


parser = argparse.ArgumentParser(description='Reddit repost bot')
subparsers = parser.add_subparsers(dest="command")
subparser_run = subparsers.add_parser('run', help="Run the bot and repost new posts")
subparser_test = subparsers.add_parser('test', help="Various testing fuctions")
subparser_show = subparsers.add_parser('show', help="Bot information")

parser.add_argument('-c', '--config', type=str, default='praw.ini',
        metavar="<praw.ini>", help="Name of config file to load")
parser.add_argument('-b', '--bot', type=str, default=DEFAULT_BOT_NAME,
        metavar="<"+DEFAULT_BOT_NAME+">", help="Name of bot (used in config file, and user agent, and other places)")

subparser_test.add_argument('--clean-title', type=str, metavar='"TITLE TO CLEAN"',
                    help='Test the title cleaner')
subparser_test.add_argument('--flair-id', type=str, metavar='"FLAIR TEXT"',
                    help='Return flair ID for the given flair (uses most recent repost, if post-id not specified)')
subparser_test.add_argument('--post-id', type=str, metavar='ID',
                    help='Submission ID to use with tests if needed')

subparser_show.add_argument('--all', action="store_true", help="Show all (or most) data")
subparser_show.add_argument('--database', action="store_true", help="Show info about database")
subparser_show.add_argument('--log', type=int, default=0, metavar="[count]", help="Show latest # log entries")
subparser_show.add_argument('--reposts', type=int, default=0, metavar="[count]", help="Show latest # reposts logged")
subparser_show.add_argument('--posts', action="store_true", help="Show latest posts online in source & destination subreddits")

subparser_run.add_argument('--reset', type=str, help="Reset the last repost date to the given reddit submission ID (eg. 5wxv94)")

args = parser.parse_args()
#print(args)

config = configparser.ConfigParser()
config.read(args.config)

DEBUG = config[args.bot]['debug'] in ('1','Y','on') and True or False
OWNER = config[args.bot]['owner'] or "unknown"

dbfn = args.bot + '.db'
my_user_agent = '{3}:{0}:v{1} (by /u/{2})'.format(args.bot, __version__, OWNER, sys.platform)
source_limit = int(config[args.bot]['source_limit'] or 10)

reddit = praw.Reddit(args.bot, user_agent=my_user_agent)
bot = RPGonBot(config[args.bot]['source'], config[args.bot]['destination'])

if args.command == 'show':
    if args.all:
        args.database = True
        args.reposts = 10
        args.log = 10

    if args.database:
        bot.show_database()
        print()

    if args.reposts > 0:
        bot.show_reposts(args.reposts)
        print()

    if args.log > 0:
        bot.show_log(args.log)
        print()

    if args.posts > 0:
        bot.show_posts(bot.subreddit_source)
        print()
        bot.show_posts(bot.subreddit_destination)
        print()

if args.command == 'test':
    if args.clean_title:
        print("Cleaned title: " + repr(bot.clean_title(args.clean_title)))

    if args.flair_id:
        submissions = bot.subreddit_destination.new(limit=1)
        if submissions:
            print("Flair id: " + bot.get_flair_id(args.flair_id, submission=next(submissions)))

if args.command == 'run':
    if args.reset:
        bot.db_reset_rp_data(args.reset)
        print("Repost data has been reset")
    else:
        bot.check_for_posts()







