#!/usr/bin/env python3

"""Visualize term frequency distributions via Rosette API analyses"""

import os

from collections import namedtuple
from getpass import getpass
from math import log

from bs4 import BeautifulSoup
from compare_vocabulary import fdist, load_stopwords, \
                               STOPWORDS_FILE, DEFAULT_ROSETTE_API_URL
from rosette.api import API

Pos = namedtuple('Pos', ['tag', 'name'])
Color = namedtuple('Color', ['hex', 'name'])

COLOR = {
    Pos('ADJ', 'Adjective'): Color('#4E8975', 'seagreen'),
    Pos('ADP', 'Adposition'): Color('#A52A2A', 'brown'),
    Pos('ADV', 'Adverb'): Color('#32CD32', 'limegreen'),
    Pos('AUX', 'Auxiliary verb'): Color('#0000FF', 'blue'),
    Pos('CONJ', 'Coordinating conjunction'): Color('#ff4500', 'orangered'),
    Pos('DET', 'Determiner'): Color('#c0c0c0', 'silver'),
    Pos('INTJ', 'Interjection'): Color('#493D26', 'mocha'),
    Pos('NOUN', 'Noun'): Color('#FFA500', 'orange'),
    Pos('NUM', 'Numeral'): Color('#6698FF', 'skyblue'),
    Pos('PART', 'Particle'): Color('#FF00FF', 'magenta'),
    Pos('PRON', 'Pronoun'): Color('#FF0000', 'red'),
    Pos('PROPN', 'Proper noun'): Color('#8D38C9', 'violet'),
    Pos('PUNCT', 'Punctuation'): Color('#008080', 'teal'),
    Pos('SCONJ', 'Subordinating conjunction'): Color('#EDDA74', 'goldenrod'),
    Pos('SYM', 'Symbol'): Color('#808000', 'olive'),
    Pos('VERB', 'Verb'): Color('#800080', 'purple'),
    Pos('X', 'Other'): Color('#000000', 'black'),
}

def color_key():
    """Generate a POS:color key as HTML"""
    html = '<h2>Color Key</h2>'
    html += '''
    <table cellpadding="3" style="border-collapse:collapse">
    <tr>
        <th style="border: 1px solid; text-align: left">Tag</th>
        <th style="border: 1px solid; text-align: left">Name</th>
        <th style="border: 1px solid; text-align: left">Color</th>
    </tr>
    '''
    html += '\n'.join(
        f'''<tr style="border: 1px solid">
        <td style="border: 1px solid">
            <font color="{color.hex}">{pos.tag}</font>
        </td>
        <td style="border: 1px solid">
            <font color="{color.hex}">{pos.name}</font>
        </td>
        <td style="border: 1px solid">
            <font color="{color.hex}">{color.name}</font>
        </td>
        </tr>
        ''' for pos, color in COLOR.items()
    )
    html += '</table>'
    return html

def rescale(range1, range2):
    """Return a function that resizes values from range1 to values in range2
    
    This is useful for interpolating values from one range to another
    """
    min1, max1, min2, max2 = min(range1), max(range1), min(range2), max(range2)
    def resize(value):
        return (((value - min1) * (max2 - min2)) / (max1 - min1)) + min2
    return resize

def visualize(fd, pos_tags=None):
    """Visualize a frequency distribution (fd) as a 'word-cloud' in HTML"""
    if pos_tags is not None:
        fd = {t: f for t, f in fd.items() if t.pos in pos_tags}
    color = {pos.tag: color.hex for pos, color in COLOR.items()}
    frequencies = sorted(fd.values())
    font_size = rescale(frequencies, range(75, 351))
    html = '\n'.join(
        f'''<font
            color="{color[t.pos]}"
            title="{t.lemma}/{t.pos} ({f})"
            style="font-size: {font_size(f)}%"
        >
        {t.lemma}
        </font>''' for t, f in fd.items()
    )
    return html

if __name__ == '__main__':
    import argparse
    stopwords = load_stopwords(STOPWORDS_FILE)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        'directories',
        nargs='+',
        help='a list of directories of text files'
    )
    parser.add_argument(
        '-n', '--top-n',
        type=int,
        default=None,
        help='how many lexical items to compare'
    )
    parser.add_argument(
        '-l', '--language',
        default=None,
        choices=sorted(stopwords.keys()),
        help=(
            'ISO 639-2/T three-letter language code (this indicates which '
            'stopword list to use)'
        )
    )
    parser.add_argument(
        '-t', '--pos-tags',
        default=None,
        metavar='POS',
        choices=sorted(pos.tag for pos in COLOR),
        nargs='+',
        help='a white-list of part-of-speech (POS) tags to include'
    )
    parser.add_argument(
        '-k', '--key',
        help='Rosette API Key',
        default=None
    )
    parser.add_argument(
        '-a', '--api-url',
        help='Alternative Rosette API URL',
        default=DEFAULT_ROSETTE_API_URL
    )
    args = parser.parse_args()
    # Get the user's Rosette API key
    key = (
        os.environ.get('ROSETTE_USER_KEY') or
        args.key or
        getpass(prompt='Enter your Rosette API key: ')
    )
    # Instantiate the Rosette API
    api = API(user_key=key, service_url=args.api_url)
    api.set_url_parameter('output', 'rosette')
    
    html = color_key()
    
    for directory in args.directories:
        html += f'<h1>{directory}<h1>'
        html += visualize(
            fdist(directory, api, args.top_n, stopwords.get(args.language, [])),
            pos_tags=args.pos_tags
        )
    
    page = BeautifulSoup(html, 'html5lib')
    print(page.prettify())
