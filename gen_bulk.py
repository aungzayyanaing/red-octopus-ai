#!/usr/bin/env python3
"""Bulk bank generator for Red Octopus AI — grows the memory bank
toward 950,000 entries with verified-correct, machine-generated Q&A.

Every row is computed, never guessed: arithmetic from Python itself,
dates from datetime, primes by trial division, conversions from fixed
factors, Roman numerals and number words from exact algorithms.
Country/element/fact rows come from small hand-checked tables, and
every generated question is checked against the existing bank so no
duplicate is ever written.

Output: memory_bank_bulk.tsv.gz — tab-separated kind, normalised
question key, answer, gzipped (~4 MB, safe for GitHub). bank.py reads
both memory_bank.jsonl (the 300 hand-written rows) and this file.
bank_progress.json is recomputed from both files afterwards.

Usage:  python3 gen_bulk.py
Idempotent: re-running rewrites the same file (same rows, same order).
"""

import datetime
import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bank  # noqa: E402  (for normalize() + KINDS)

BULK_FILE = os.path.join(HERE, "memory_bank_bulk.tsv.gz")
CORE_FILE = os.path.join(HERE, "memory_bank.jsonl")
PROGRESS_FILE = os.path.join(HERE, "bank_progress.json")

MM_RE = re.compile(r"[\u1000-\u109F]")


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def fmt(x, dp=2):
    """Shortest clean rendering of a number: 6.21, 0.5, 579 (no .0)."""
    r = round(float(x), dp)
    if r == int(r):
        return str(int(r))
    return str(r)


def is_prime(n):
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


_ONES = ["", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen",
         "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
         "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty",
         "seventy", "eighty", "ninety"]


def number_words(n):
    """English words for 1..1000 (one, twenty-one, one hundred)."""
    if n == 1000:
        return "one thousand"
    parts = []
    if n >= 100:
        parts.append(_ONES[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        parts.append(_TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else ""))
    elif n > 0:
        parts.append(_ONES[n])
    return " ".join(parts)


_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
          (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
          (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def to_roman(n):
    out = []
    for value, numeral in _ROMAN:
        while n >= value:
            out.append(numeral)
            n -= value
    return "".join(out)


# ----------------------------------------------------------------------
# generators — each yields (kind, question, answer)
# ----------------------------------------------------------------------
def gen_addition():
    for a in range(0, 1000):
        for b in range(0, 450):
            yield ("math", "What is %d + %d?" % (a, b), "%d." % (a + b))


def gen_subtraction():
    for a in range(100, 1000):
        for b in range(0, 450):
            if a >= b:
                yield ("math", "What is %d - %d?" % (a, b), "%d." % (a - b))


def gen_multiplication():
    for a in range(2, 1000):
        for b in range(2, 100):
            yield ("math", "What is %d times %d?" % (a, b), "%d." % (a * b))


def gen_division():
    for b in range(2, 100):
        for c in range(2, 100):
            yield ("math", "What is %d divided by %d?" % (b * c, b), "%d." % c)


def gen_squares_cubes_roots():
    for n in range(1, 1001):
        yield ("math", "What is %d squared?" % n, "%d." % (n * n))
    for n in range(1, 101):
        yield ("math", "What is %d cubed?" % n, "%d." % (n ** 3))
    for n in range(1, 1001):
        yield ("math", "What is the square root of %d?" % (n * n), "%d." % n)


def gen_percentages():
    for p in range(5, 100, 5):
        for n in range(10, 1001, 10):
            yield ("math", "What is %d%% of %d?" % (p, n), "%s." % fmt(p * n / 100))


def gen_double_half():
    for n in range(1, 1001):
        yield ("math", "What is double %d?" % n, "%d." % (2 * n))
    for n in range(2, 2001, 2):
        yield ("math", "What is half of %d?" % n, "%d." % (n // 2))


def gen_dates():
    """Day of the week for every day 2000-01-01 .. 2030-12-31."""
    day = datetime.date(2000, 1, 1)
    end = datetime.date(2030, 12, 31)
    while day <= end:
        yield ("science", "What day of the week was %s %d, %d?"
               % (day.strftime("%B"), day.day, day.year),
               "%s." % day.strftime("%A"))
        day += datetime.timedelta(days=1)


def gen_roman():
    for n in range(1, 4000):
        yield ("general", "What is %d in Roman numerals?" % n, "%s." % to_roman(n))
    for n in range(1, 4000):
        yield ("general", "What number is %s in Roman numerals?" % to_roman(n),
               "%d." % n)


def gen_conversions():
    for n in range(1, 1001):
        yield ("daily", "How many miles are in %d kilometres?" % n,
               "%s miles." % fmt(n * 0.621371))
    for n in range(1, 1001):
        yield ("daily", "How many kilometres are in %d miles?" % n,
               "%s kilometres." % fmt(n * 1.60934))
    for n in range(1, 1001):
        yield ("daily", "How many pounds are in %d kilograms?" % n,
               "%s pounds." % fmt(n * 2.20462))
    for n in range(1, 1001):
        yield ("daily", "How many kilograms are in %d pounds?" % n,
               "%s kilograms." % fmt(n * 0.453592))
    for c in range(-40, 101):
        yield ("daily", "What is %d degrees Celsius in Fahrenheit?" % c,
               "%s degrees Fahrenheit." % fmt(c * 9 / 5 + 32, 1))
    for f in range(-40, 213, 2):
        yield ("daily", "What is %d degrees Fahrenheit in Celsius?" % f,
               "%s degrees Celsius." % fmt((f - 32) * 5 / 9, 1))
    for n in range(1, 501):
        yield ("daily", "How many gallons are in %d litres?" % n,
               "%s gallons." % fmt(n * 0.264172))
    for n in range(1, 1001):
        yield ("daily", "How many feet are in %d metres?" % n,
               "%s feet." % fmt(n * 3.28084))


def gen_number_facts():
    for n in range(1, 10001):
        if n % 2 == 0:
            yield ("general", "Is %d an even number?" % n, "Yes, %d is even." % n)
        else:
            yield ("general", "Is %d an even number?" % n, "No, %d is odd." % n)
    for n in range(1, 10001):
        if is_prime(n):
            yield ("general", "Is %d a prime number?" % n, "Yes, %d is prime." % n)
        else:
            yield ("general", "Is %d a prime number?" % n, "No, %d is not prime." % n)
    for n in range(1, 1001):
        yield ("general", "How do you write %d in words?" % n,
               "%s." % number_words(n).capitalize())


def gen_time_units():
    for h in range(1, 25):
        yield ("daily", "How many minutes are in %d hours?" % h, "%d minutes." % (h * 60))
    for m in range(1, 61):
        yield ("daily", "How many seconds are in %d minutes?" % m, "%d seconds." % (m * 60))
    for w in range(1, 53):
        yield ("daily", "How many days are in %d weeks?" % w, "%d days." % (w * 7))
    for y in range(1, 101):
        yield ("daily", "How many months are in %d years?" % y, "%d months." % (y * 12))
    for d in range(1, 31):
        yield ("daily", "How many hours are in %d days?" % d, "%d hours." % (d * 24))


# ----------------------------------------------------------------------
# hand-checked tables
# ----------------------------------------------------------------------
# (country, capital, currency, continent)
COUNTRIES = [
    ("Myanmar", "Naypyidaw", "kyat", "Asia"),
    ("Thailand", "Bangkok", "baht", "Asia"),
    ("China", "Beijing", "yuan", "Asia"),
    ("Japan", "Tokyo", "yen", "Asia"),
    ("India", "New Delhi", "rupee", "Asia"),
    ("South Korea", "Seoul", "won", "Asia"),
    ("Vietnam", "Hanoi", "dong", "Asia"),
    ("Singapore", "Singapore", "Singapore dollar", "Asia"),
    ("Malaysia", "Kuala Lumpur", "ringgit", "Asia"),
    ("Indonesia", "Jakarta", "rupiah", "Asia"),
    ("Philippines", "Manila", "peso", "Asia"),
    ("Laos", "Vientiane", "kip", "Asia"),
    ("Cambodia", "Phnom Penh", "riel", "Asia"),
    ("Bangladesh", "Dhaka", "taka", "Asia"),
    ("Pakistan", "Islamabad", "rupee", "Asia"),
    ("Sri Lanka", "Colombo", "rupee", "Asia"),
    ("Nepal", "Kathmandu", "rupee", "Asia"),
    ("Mongolia", "Ulaanbaatar", "tugrik", "Asia"),
    ("Taiwan", "Taipei", "New Taiwan dollar", "Asia"),
    ("Hong Kong", "Hong Kong", "Hong Kong dollar", "Asia"),
    ("United Kingdom", "London", "pound sterling", "Europe"),
    ("France", "Paris", "euro", "Europe"),
    ("Germany", "Berlin", "euro", "Europe"),
    ("Italy", "Rome", "euro", "Europe"),
    ("Spain", "Madrid", "euro", "Europe"),
    ("Portugal", "Lisbon", "euro", "Europe"),
    ("Netherlands", "Amsterdam", "euro", "Europe"),
    ("Belgium", "Brussels", "euro", "Europe"),
    ("Switzerland", "Bern", "Swiss franc", "Europe"),
    ("Austria", "Vienna", "euro", "Europe"),
    ("Greece", "Athens", "euro", "Europe"),
    ("Sweden", "Stockholm", "krona", "Europe"),
    ("Norway", "Oslo", "krone", "Europe"),
    ("Denmark", "Copenhagen", "krone", "Europe"),
    ("Finland", "Helsinki", "euro", "Europe"),
    ("Poland", "Warsaw", "zloty", "Europe"),
    ("Ireland", "Dublin", "euro", "Europe"),
    ("Russia", "Moscow", "ruble", "Europe"),
    ("Turkey", "Ankara", "lira", "Asia"),
    ("United States", "Washington DC", "US dollar", "North America"),
    ("Canada", "Ottawa", "Canadian dollar", "North America"),
    ("Mexico", "Mexico City", "peso", "North America"),
    ("Brazil", "Brasilia", "real", "South America"),
    ("Argentina", "Buenos Aires", "peso", "South America"),
    ("Chile", "Santiago", "peso", "South America"),
    ("Peru", "Lima", "sol", "South America"),
    ("Colombia", "Bogota", "peso", "South America"),
    ("Egypt", "Cairo", "Egyptian pound", "Africa"),
    ("South Africa", "Pretoria", "rand", "Africa"),
    ("Nigeria", "Abuja", "naira", "Africa"),
    ("Kenya", "Nairobi", "Kenyan shilling", "Africa"),
    ("Morocco", "Rabat", "dirham", "Africa"),
    ("Ethiopia", "Addis Ababa", "birr", "Africa"),
    ("Australia", "Canberra", "Australian dollar", "Oceania"),
    ("New Zealand", "Wellington", "New Zealand dollar", "Oceania"),
]


def gen_countries():
    for name, capital, currency, continent in COUNTRIES:
        yield ("general", "What is the capital of %s?" % name,
               "The capital of %s is %s." % (name, capital))
        yield ("general", "What is the currency of %s?" % name,
               "The currency of %s is the %s." % (name, currency))
        yield ("general", "Which continent is %s in?" % name,
               "%s is in %s." % (name, continent))


# (atomic number, name, symbol) — the standard periodic table
ELEMENTS = [
    (1, "Hydrogen", "H"), (2, "Helium", "He"), (3, "Lithium", "Li"),
    (4, "Beryllium", "Be"), (5, "Boron", "B"), (6, "Carbon", "C"),
    (7, "Nitrogen", "N"), (8, "Oxygen", "O"), (9, "Fluorine", "F"),
    (10, "Neon", "Ne"), (11, "Sodium", "Na"), (12, "Magnesium", "Mg"),
    (13, "Aluminium", "Al"), (14, "Silicon", "Si"), (15, "Phosphorus", "P"),
    (16, "Sulfur", "S"), (17, "Chlorine", "Cl"), (18, "Argon", "Ar"),
    (19, "Potassium", "K"), (20, "Calcium", "Ca"), (21, "Scandium", "Sc"),
    (22, "Titanium", "Ti"), (23, "Vanadium", "V"), (24, "Chromium", "Cr"),
    (25, "Manganese", "Mn"), (26, "Iron", "Fe"), (27, "Cobalt", "Co"),
    (28, "Nickel", "Ni"), (29, "Copper", "Cu"), (30, "Zinc", "Zn"),
    (31, "Gallium", "Ga"), (32, "Germanium", "Ge"), (33, "Arsenic", "As"),
    (34, "Selenium", "Se"), (35, "Bromine", "Br"), (36, "Krypton", "Kr"),
    (37, "Rubidium", "Rb"), (38, "Strontium", "Sr"), (39, "Yttrium", "Y"),
    (40, "Zirconium", "Zr"), (41, "Niobium", "Nb"), (42, "Molybdenum", "Mo"),
    (43, "Technetium", "Tc"), (44, "Ruthenium", "Ru"), (45, "Rhodium", "Rh"),
    (46, "Palladium", "Pd"), (47, "Silver", "Ag"), (48, "Cadmium", "Cd"),
    (49, "Indium", "In"), (50, "Tin", "Sn"), (51, "Antimony", "Sb"),
    (52, "Tellurium", "Te"), (53, "Iodine", "I"), (54, "Xenon", "Xe"),
    (55, "Caesium", "Cs"), (56, "Barium", "Ba"), (57, "Lanthanum", "La"),
    (58, "Cerium", "Ce"), (59, "Praseodymium", "Pr"), (60, "Neodymium", "Nd"),
    (61, "Promethium", "Pm"), (62, "Samarium", "Sm"), (63, "Europium", "Eu"),
    (64, "Gadolinium", "Gd"), (65, "Terbium", "Tb"), (66, "Dysprosium", "Dy"),
    (67, "Holmium", "Ho"), (68, "Erbium", "Er"), (69, "Thulium", "Tm"),
    (70, "Ytterbium", "Yb"), (71, "Lutetium", "Lu"), (72, "Hafnium", "Hf"),
    (73, "Tantalum", "Ta"), (74, "Tungsten", "W"), (75, "Rhenium", "Re"),
    (76, "Osmium", "Os"), (77, "Iridium", "Ir"), (78, "Platinum", "Pt"),
    (79, "Gold", "Au"), (80, "Mercury", "Hg"), (81, "Thallium", "Tl"),
    (82, "Lead", "Pb"), (83, "Bismuth", "Bi"), (84, "Polonium", "Po"),
    (85, "Astatine", "At"), (86, "Radon", "Rn"), (87, "Francium", "Fr"),
    (88, "Radium", "Ra"), (89, "Actinium", "Ac"), (90, "Thorium", "Th"),
    (91, "Protactinium", "Pa"), (92, "Uranium", "U"), (93, "Neptunium", "Np"),
    (94, "Plutonium", "Pu"), (95, "Americium", "Am"), (96, "Curium", "Cm"),
    (97, "Berkelium", "Bk"), (98, "Californium", "Cf"), (99, "Einsteinium", "Es"),
    (100, "Fermium", "Fm"), (101, "Mendelevium", "Md"), (102, "Nobelium", "No"),
    (103, "Lawrencium", "Lr"), (104, "Rutherfordium", "Rf"), (105, "Dubnium", "Db"),
    (106, "Seaborgium", "Sg"), (107, "Bohrium", "Bh"), (108, "Hassium", "Hs"),
    (109, "Meitnerium", "Mt"), (110, "Darmstadtium", "Ds"), (111, "Roentgenium", "Rg"),
    (112, "Copernicium", "Cn"), (113, "Nihonium", "Nh"), (114, "Flerovium", "Fl"),
    (115, "Moscovium", "Mc"), (116, "Livermorium", "Lv"), (117, "Tennessine", "Ts"),
    (118, "Oganesson", "Og"),
]


def gen_elements():
    for num, name, sym in ELEMENTS:
        yield ("science", "What is the chemical symbol for %s?" % name,
               "The chemical symbol for %s is %s." % (name, sym))
        yield ("science", "What is the atomic number of %s?" % name,
               "The atomic number of %s is %d." % (name, num))
        yield ("science", "Which element has the chemical symbol %s?" % sym,
               "%s has the chemical symbol %s." % (name, sym))


# Hand-written Q&A (kind, question, answer) — checked, no duplicates
# with the core 300 (the dedupe pass below drops any that collide).
HANDWRITTEN = [
    ("science", "What is the largest planet in the solar system?",
     "Jupiter is the largest planet in the solar system."),
    ("science", "Which planet is closest to the Sun?",
     "Mercury is the closest planet to the Sun."),
    ("science", "Which planet is known as the Red Planet?",
     "Mars is known as the Red Planet."),
    ("science", "Which planet has the most prominent rings?",
     "Saturn has the most prominent rings."),
    ("science", "Which planet is the hottest in the solar system?",
     "Venus is the hottest planet in the solar system."),
    ("science", "Which planet is farthest from the Sun?",
     "Neptune is the farthest planet from the Sun."),
    ("science", "How many planets are in the solar system?",
     "There are eight planets in the solar system."),
    ("science", "What is the speed of light in a vacuum?",
     "The speed of light in a vacuum is about 300,000 kilometres per second."),
    ("science", "At what temperature does water boil at sea level?",
     "Water boils at 100 degrees Celsius at sea level."),
    ("science", "At what temperature does water freeze?",
     "Water freezes at 0 degrees Celsius."),
    ("science", "What gas do plants absorb from the air?",
     "Plants absorb carbon dioxide from the air."),
    ("science", "What gas do humans need to breathe?",
     "Humans need oxygen to breathe."),
    ("science", "How many bones are in the adult human body?",
     "The adult human body has 206 bones."),
    ("science", "How many chambers does the human heart have?",
     "The human heart has four chambers."),
    ("science", "What is the powerhouse of the cell?",
     "The mitochondria is known as the powerhouse of the cell."),
    ("science", "What is the chemical formula for water?",
     "The chemical formula for water is H2O."),
    ("science", "What force keeps us on the ground?",
     "Gravity keeps us on the ground."),
    ("science", "How many days are in a leap year?",
     "A leap year has 366 days."),
    ("science", "How many continents are there on Earth?",
     "There are seven continents on Earth."),
    ("science", "What is the largest ocean on Earth?",
     "The Pacific Ocean is the largest ocean on Earth."),
    ("science", "What is the longest river in the world?",
     "The Nile is generally considered the longest river in the world."),
    ("science", "What is the tallest mountain on Earth?",
     "Mount Everest is the tallest mountain on Earth."),
    ("science", "How many minutes are in one hour?",
     "There are 60 minutes in one hour."),
    ("science", "How many seconds are in one minute?",
     "There are 60 seconds in one minute."),
    ("science", "How many hours are in one day?",
     "There are 24 hours in one day."),
    ("science", "How many days are in one week?",
     "There are 7 days in one week."),
    ("science", "How many months are in one year?",
     "There are 12 months in one year."),
    ("health", "How many hours of sleep do adults need each night?",
     "Most adults need 7 to 9 hours of sleep each night."),
    ("health", "How much water should you drink in a day?",
     "About 2 litres of water a day is a good guide for most adults."),
    ("health", "Why is walking good for your health?",
     "Walking improves heart health, mood, and energy with very low injury risk."),
    ("health", "What is a healthy resting heart rate for adults?",
     "A healthy resting heart rate for most adults is 60 to 100 beats per minute."),
    ("health", "Why should you eat vegetables every day?",
     "Vegetables provide fibre, vitamins, and minerals that protect long-term health."),
    ("health", "What does regular exercise do for your brain?",
     "Regular exercise improves memory, focus, and mood."),
    ("health", "Why is too much sugar bad for you?",
     "Too much sugar raises the risk of weight gain, tooth decay, and type 2 diabetes."),
    ("health", "How often should you brush your teeth?",
     "Brush your teeth twice a day, morning and night."),
    ("business", "What does ROI stand for?",
     "ROI stands for Return on Investment."),
    ("business", "What is profit?",
     "Profit is the money left after subtracting all costs from revenue."),
    ("business", "What is revenue?",
     "Revenue is the total money a business earns from selling its products or services."),
    ("business", "What is a business plan?",
     "A business plan is a written plan that explains what a business will sell, who will buy it, and how it will make money."),
    ("business", "What is marketing?",
     "Marketing is how a business finds customers and convinces them to buy."),
    ("business", "What is a target customer?",
     "A target customer is the specific kind of person a business aims to sell to."),
    ("business", "What is a budget?",
     "A budget is a plan for how much money will come in and go out over a period of time."),
    ("business", "What is cash flow?",
     "Cash flow is the movement of money in and out of a business."),
    ("business", "What is an invoice?",
     "An invoice is a document asking a customer to pay for goods or services they received."),
    ("business", "What is a discount?",
     "A discount is a reduction in the normal price of a product or service."),
    ("business", "What is branding?",
     "Branding is how a business presents itself so customers recognise and trust it."),
    ("business", "What is customer service?",
     "Customer service is the help a business gives its customers before, during, and after a sale."),
    ("business", "What is a startup?",
     "A startup is a young company trying to grow a new product or business idea."),
    ("business", "What is an entrepreneur?",
     "An entrepreneur is a person who starts and runs a business, taking on the risk to do it."),
    ("business", "What is a monopoly?",
     "A monopoly is a market where one company is the only seller of a product or service."),
    ("business", "What is inflation?",
     "Inflation is the general rise in prices over time, which reduces what money can buy."),
    ("business", "What is a stock?",
     "A stock is a share of ownership in a company."),
    ("business", "What is interest?",
     "Interest is the cost of borrowing money, or the reward for lending it."),
    ("business", "What is a loan?",
     "A loan is money borrowed that must be paid back, usually with interest."),
    ("business", "What is a tax?",
     "A tax is money paid to the government on income, purchases, or property."),
    ("myanmar", "What is the capital of Kachin State?",
     "The capital of Kachin State is Myitkyina."),
    ("myanmar", "What is the capital of Shan State?",
     "The capital of Shan State is Taunggyi."),
    ("myanmar", "What is the capital of Mandalay Region?",
     "The capital of Mandalay Region is Mandalay."),
    ("myanmar", "What is the capital of Yangon Region?",
     "The capital of Yangon Region is Yangon."),
    ("myanmar", "What is the capital of Kayin State?",
     "The capital of Kayin State is Hpa-An."),
    ("myanmar", "What is the capital of Rakhine State?",
     "The capital of Rakhine State is Sittwe."),
    ("myanmar", "What is the capital of Mon State?",
     "The capital of Mon State is Mawlamyine."),
    ("myanmar", "What is the capital of Chin State?",
     "The capital of Chin State is Hakha."),
    ("myanmar", "What is the capital of Kayah State?",
     "The capital of Kayah State is Loikaw."),
    ("myanmar", "What is the capital of Sagaing Region?",
     "The capital of Sagaing Region is Sagaing."),
    ("myanmar", "What is the capital of Bago Region?",
     "The capital of Bago Region is Bago."),
    ("myanmar", "What is the capital of Magway Region?",
     "The capital of Magway Region is Magway."),
    ("myanmar", "What is the capital of Ayeyarwady Region?",
     "The capital of Ayeyarwady Region is Pathein."),
    ("myanmar", "What is the capital of Tanintharyi Region?",
     "The capital of Tanintharyi Region is Dawei."),
    ("myanmar", "What is the longest river in Myanmar?",
     "The Ayeyarwady River is the longest river in Myanmar."),
    ("myanmar", "What is the most famous pagoda in Yangon?",
     "Shwedagon Pagoda is the most famous pagoda in Yangon."),
    ("myanmar", "What is Myanmar's national sport?",
     "Chinlone is the national sport of Myanmar."),
    ("myanmar", "What is the main language of Myanmar?",
     "Burmese is the main language of Myanmar."),
    ("myanmar", "What currency is used in Myanmar?",
     "The kyat is the currency used in Myanmar."),
    ("daily", "How many days are in February in a leap year?",
     "February has 29 days in a leap year."),
    ("daily", "What is the first month of the year?",
     "January is the first month of the year."),
    ("daily", "What is the last month of the year?",
     "December is the last month of the year."),
    ("daily", "How many colours are in a rainbow?",
     "A rainbow has seven colours."),
    ("daily", "What is the opposite of hot?",
     "The opposite of hot is cold."),
    ("daily", "How many legs does a spider have?",
     "A spider has eight legs."),
    ("daily", "How many legs does an insect have?",
     "An insect has six legs."),
    ("daily", "What do bees produce?",
     "Bees produce honey."),
    ("daily", "What is the fastest land animal?",
     "The cheetah is the fastest land animal."),
    ("daily", "What is the largest land animal?",
     "The African elephant is the largest land animal."),
]


def gen_handwritten():
    for kind, q, a in HANDWRITTEN:
        yield (kind, q, a)


GENERATORS = [
    ("addition", gen_addition),
    ("subtraction", gen_subtraction),
    ("multiplication", gen_multiplication),
    ("division", gen_division),
    ("squares/cubes/roots", gen_squares_cubes_roots),
    ("percentages", gen_percentages),
    ("double/half", gen_double_half),
    ("dates", gen_dates),
    ("roman", gen_roman),
    ("conversions", gen_conversions),
    ("number-facts", gen_number_facts),
    ("time-units", gen_time_units),
    ("countries", gen_countries),
    ("elements", gen_elements),
    ("handwritten", gen_handwritten),
]


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def existing_questions():
    """Normalised questions already in the core 300-row bank."""
    seen = set()
    try:
        with open(CORE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if "q" in obj:
                    seen.add(bank.normalize(str(obj["q"])))
    except FileNotFoundError:
        pass
    return seen


def recompute_progress(per_kind, total):
    """Rewrite bank_progress.json from the real file counts."""
    old = {}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
    except (FileNotFoundError, ValueError):
        pass
    old["per_kind"] = per_kind
    old["total"] = total
    old["capacity"] = bank.CAPACITY
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=2)
    return old


def main():
    seen = existing_questions()
    print("core bank questions to avoid duplicating: %d" % len(seen))
    per_kind = {k: 0 for k in bank.KINDS}
    total = 0
    skipped_dup = 0
    skipped_mm = 0
    written = 0
    with gzip.open(BULK_FILE, "wt", encoding="utf-8", compresslevel=6) as out:
        for name, gen in GENERATORS:
            count = 0
            skipped_here = 0
            for kind, q, a in gen():
                q = q.strip()
                a = a.strip()
                if not q or not a:
                    continue
                if MM_RE.search(q) or MM_RE.search(a):
                    skipped_mm += 1
                    skipped_here += 1
                    continue
                key = bank.normalize(q)
                if key in seen:
                    skipped_dup += 1
                    skipped_here += 1
                    if skipped_here <= 3:
                        print("  skipped dup: %r (key %r)" % (q, key))
                    continue
                seen.add(key)
                # TSV: kind TAB normalised-key TAB answer. The key is
                # normalised once here, so loading never re-parses JSON
                # or re-runs the normaliser.
                out.write("%s\t%s\t%s\n" % (kind, key, a))
                per_kind[kind] += 1
                total += 1
                count += 1
                written += 1
            print("%-22s %s rows" % (name, format(count, ",")))
    # add the core 300 to the counts
    core_per_kind = {k: 0 for k in bank.KINDS}
    core_total = 0
    with open(CORE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if obj.get("kind") in core_per_kind:
                core_per_kind[obj["kind"]] += 1
                core_total += 1
    combined = {k: core_per_kind[k] + per_kind[k] for k in bank.KINDS}
    progress = recompute_progress(combined, core_total + total)
    print("bulk rows written: %s" % format(written, ","))
    print("duplicates skipped (already in core bank): %s" % format(skipped_dup, ","))
    print("Myanmar-script rows skipped: %d" % skipped_mm)
    print("bulk file: %s (%s bytes)"
          % (BULK_FILE, format(os.path.getsize(BULK_FILE), ",")))
    print("TOTAL BANK: %s rows" % format(core_total + total, ","))
    print("per kind: %s" % progress["per_kind"])


if __name__ == "__main__":
    main()
