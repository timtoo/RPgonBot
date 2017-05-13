
import rpgonbot

titles = (
    ('(F)alling into your arms',
        'Falling into your limbs'),
    ('Twist and turn.',
        'Twist and turn.'),
    ('Showing all my holes',
        'Showing all my empty spaces'),
    ('Weekly Loop OC Challenge/Streak!',
        'Weekly Loop OC Challenge/Streak!'),
    ('Curves upon curves',
        'Arcs upon arcs'),
    ('I love the way you move',
        "It's nice the way some things move"),
    ('Rainbow [r]efraction',
        'Rainbow refraction'),
    ('Fits in perfectly, and I LO[V]E twirling it around!',
        "Fits in perfectly, and IT'S NICE twirling it around!"),
    ('You like me from this angle?',
        'Some things like me from this angle?'),
    ('Curvy',
        'Wavy'),
    ('arcs',
        'arcs'),
    ('You should see my leg[s] now',
        'You should see my appendages now'),
    ('You [M]ove me',
        'Some things Move me'),
    ('Straight Hole, Curved Pole',
        'Straight Empty space, Curved Line'),
    ('[S]pinning in place',
        'Spinning in place'),
    ('Deeper and [d]eeper',
        'Deeper and deeper'),
    ('Perfectly [p]roportioned curves',
        'Perfectly proportioned arcs'),
    ('Honeycomb [h]ole',
        'Honeycomb empty space'),
    ('Check out [m]y hole (x-post from r/loadingicon)',
        'Check out my empty space (x-post from r/loadingicon)'),
    ('Twist and turn. [x-post /r/oddlysatisfying]',
        'Twist and turn. [x-post /r/oddlysatisfying]'),
    ('pumping [h]ard',
        'pulsing solid'),
    ('feeling frisky tonight',
        'feeling whimsical tonight'),
    ('epiMorph into me',
        'epiMorph into something'),
    ('Stick it in me [MMF]',
        'Stick it in object'),
    ('[F]irst post, be gentle. [OC]',
        'Hello, such good. OC'),
)

bot = rpgonbot.RPGonBot('d', 't')
errors = []

for title in titles:
    #print ("    ({!r},\n        {!r}),".format(title, bot.clean_title(title)))
    original = title[0]
    hacked = bot.clean_title(original)
    print ("ORIGINAL: " + repr(original))
    print ("HACKED:   " + repr(hacked))
    if hacked != title[1]:
        errors.push(title)
        print ("!!ERROR!! " + repr(title[1]))

    if errors:
        print (str(len(errors)) + " errors! See above.")
    else:
        print (str(len(titles)) + " translations as expected.")



