
import rpgonbot

titles = (
    '(F)alling into your arms',
    'Twist and turn.',
    'Showing all my holes',
    'Weekly Loop OC Challenge/Streak!',
    'Curves upon curves',
    'I love the way you move',
    'Rainbow [r]efraction',
    'Fits in perfectly, and I LO[V]E twirling it around!',
    'You like me from this angle?',
    'Curvy',
    'arcs',
    'You should see my leg[s] now',
    'You [M]ove me',
    'Straight Hole, Curved Pole',
    '[S]pinning in place',
    'Deeper and [d]eeper',
    'Perfectly [p]roportioned curves',
    'Honeycomb [h]ole',
    'Check out [m]y hole (x-post from r/loadingicon)',
    'Twist and turn. [x-post /r/oddlysatisfying]',
)

bot = rpgonbot.RPGonBot('d', 't')

for title in titles:
    print ("ORIGINAL: " + repr(title))
    print ("HACKED:   " + repr(bot.clean_title(title)))



