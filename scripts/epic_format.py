"""The EPIC formats a published card may carry, and the key the site searches by.

    ABC1234567          3 letters + 7 digits: nearly every card
    ABC12345678         3 letters + 8 digits: a few series
    KA/01/234/567890    the old state format (state/AC/part/serial), kept as printed:
                        cards of voters who moved in from another state
    ABC123456, AB12345678, 123456, ABC123456X
                        a handful of cards both rolls print irregularly (a digit
                        short, two letters, no letters, a letter last): kept
                        exactly as printed, since that is what the voter's
                        entry says; only a person sets these

The readers only settle the first; the others are set by a person reading the
crops of both rolls (xreview.py). The site's key is the EPIC's letters and
digits (slashes dropped): what a visitor types, with or without the slashes, is
cleaned the same way before it is hashed (site/app.js, scripts/ci/build.mjs).
"""
import re

STANDARD = re.compile(r'^[A-Z]{3}[0-9]{7}$')
ANY = re.compile(r'^(?:[A-Z]{3}[0-9]{7,8}|[A-Z]{2}/[0-9]{2}/[0-9]{3}/[0-9]{6,7}|(?=[A-Z]*[0-9])[A-Z0-9]{6,10})$')


def valid(epic) -> bool:
    """A format a published card may carry."""
    return bool(epic and ANY.match(epic))


def key(epic: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', epic)
