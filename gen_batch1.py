#!/usr/bin/env python3
"""Generate one batch of memory-bank entries and append them to
memory_bank.jsonl (deduped, append-only), then refresh bank_progress.json.

Usage:  python3 gen_batch1.py
Safe to re-run: already-present questions/facts are skipped.
Batch size here is 300 (50 per kind) — the first real batch.
Future batches: copy this file, change BATCH_ID and ENTRIES.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bank  # noqa: E402  (for normalize + KINDS)

BATCH_ID = "batch-001"
BANK_FILE = bank.BANK_FILE
PROGRESS_FILE = bank.PROGRESS_FILE

ENTRIES = [
    # ------------------------------------------------------------------
    # general — general knowledge Q&A
    # ------------------------------------------------------------------
    {"kind": "general", "q": "What is the capital of France?", "a": "Paris."},
    {"kind": "general", "q": "What is the capital of Japan?", "a": "Tokyo."},
    {"kind": "general", "q": "What is the capital of Thailand?", "a": "Bangkok."},
    {"kind": "general", "q": "What is the capital of China?", "a": "Beijing."},
    {"kind": "general", "q": "What is the capital of India?", "a": "New Delhi."},
    {"kind": "general", "q": "What is the capital of the United Kingdom?", "a": "London."},
    {"kind": "general", "q": "What is the capital of Germany?", "a": "Berlin."},
    {"kind": "general", "q": "What is the capital of Italy?", "a": "Rome."},
    {"kind": "general", "q": "What is the capital of Spain?", "a": "Madrid."},
    {"kind": "general", "q": "What is the capital of Russia?", "a": "Moscow."},
    {"kind": "general", "q": "What is the capital of Australia?", "a": "Canberra."},
    {"kind": "general", "q": "What is the capital of Canada?", "a": "Ottawa."},
    {"kind": "general", "q": "What is the capital of Brazil?", "a": "Brasília."},
    {"kind": "general", "q": "What is the capital of Egypt?", "a": "Cairo."},
    {"kind": "general", "q": "What is the capital of South Korea?", "a": "Seoul."},
    {"kind": "general", "q": "What is the largest planet in our solar system?", "a": "Jupiter."},
    {"kind": "general", "q": "What is the closest star to Earth?", "a": "The Sun."},
    {"kind": "general", "q": "How many planets are in our solar system?", "a": "Eight."},
    {"kind": "general", "q": "What is the largest ocean on Earth?", "a": "The Pacific Ocean."},
    {"kind": "general", "q": "What is the longest river in the world?", "a": "The Nile — about 6,650 km long. The Amazon carries more water."},
    {"kind": "general", "q": "What is the tallest mountain on Earth?", "a": "Mount Everest (8,849 m)."},
    {"kind": "general", "q": "What gas do plants absorb from the air?", "a": "Carbon dioxide."},
    {"kind": "general", "q": "What is H2O?", "a": "Water."},
    {"kind": "general", "q": "How many continents are there on Earth?", "a": "Seven."},
    {"kind": "general", "q": "What is the capital of Myanmar?", "a": "Naypyidaw."},
    {"kind": "general", "q": "What is the largest country in the world by area?", "a": "Russia."},
    {"kind": "general", "q": "What is the smallest planet in our solar system?", "a": "Mercury."},
    {"kind": "general", "q": "Which planet is known as the Red Planet?", "a": "Mars."},
    {"kind": "general", "q": "What is the chemical symbol for gold?", "a": "Au."},
    {"kind": "general", "q": "What is the chemical symbol for oxygen?", "a": "O."},
    {"kind": "general", "q": "How many days are there in a leap year?", "a": "366."},
    {"kind": "general", "q": "How many minutes are in one hour?", "a": "60."},
    {"kind": "general", "q": "How many seconds are in one minute?", "a": "60."},
    {"kind": "general", "q": "What is the largest desert in the world?", "a": "The Antarctic desert. The largest hot desert is the Sahara."},
    {"kind": "general", "q": "What is the main language spoken in Brazil?", "a": "Portuguese."},
    {"kind": "general", "q": "What is the currency of Japan?", "a": "The yen."},
    {"kind": "general", "q": "What is the currency of the United Kingdom?", "a": "The pound sterling."},
    {"kind": "general", "q": "What is the currency of Thailand?", "a": "The baht."},
    {"kind": "general", "q": "What is the currency of Myanmar?", "a": "The kyat."},
    {"kind": "general", "q": "Who wrote Romeo and Juliet?", "a": "William Shakespeare."},
    {"kind": "general", "q": "Who painted the Mona Lisa?", "a": "Leonardo da Vinci."},
    {"kind": "general", "q": "What is the largest mammal in the world?", "a": "The blue whale."},
    {"kind": "general", "q": "How many legs does a spider have?", "a": "Eight."},
    {"kind": "general", "q": "What do bees produce?", "a": "Honey."},
    {"kind": "general", "q": "What is the fastest land animal?", "a": "The cheetah."},
    {"kind": "general", "q": "What is the capital of Vietnam?", "a": "Hanoi."},
    {"kind": "general", "q": "What is the capital of Laos?", "a": "Vientiane."},
    {"kind": "general", "q": "What is the capital of Cambodia?", "a": "Phnom Penh."},
    {"kind": "general", "q": "What is the capital of Malaysia?", "a": "Kuala Lumpur."},
    {"kind": "general", "q": "What is the capital of Singapore?", "a": "Singapore."},
    # ------------------------------------------------------------------
    # burmese — Burmese language & culture
    # ------------------------------------------------------------------
    {"kind": "myanmar", "q": "What is Myanmar's capital city?", "a": "Naypyidaw."},
    {"kind": "myanmar", "q": "What is the largest city in Myanmar?", "a": "Yangon."},
    {"kind": "myanmar", "q": "What is the second largest city in Myanmar?", "a": "Mandalay."},
    {"kind": "myanmar", "q": "How many consonants are there in the Myanmar alphabet?", "a": "33."},
    {"kind": "myanmar", "q": "How many vowels are there in the Myanmar alphabet?", "a": "12."},
    {"kind": "myanmar", "q": "What currency is used in Myanmar?", "a": "The kyat."},
    {"kind": "myanmar", "q": "What is Myanmar's New Year festival?", "a": "Thingyan."},
    {"kind": "myanmar", "q": "In which month is the Thingyan festival held?", "a": "In Tagu (April)."},
    {"kind": "myanmar", "q": "What is a famous pagoda in Myanmar?", "a": "Shwedagon Pagoda."},
    {"kind": "myanmar", "q": "How many pagodas are there in Bagan?", "a": "Thousands."},
    {"kind": "myanmar", "q": "What is the longest river in Myanmar?", "a": "The Ayeyarwady River."},
    {"kind": "myanmar", "q": "What is the highest mountain in Myanmar?", "a": "Hkakabo Razi."},
    {"kind": "myanmar", "q": "In which state is Inle Lake?", "a": "In Shan State."},
    {"kind": "myanmar", "q": "What is Myanmar's national food?", "a": "Mohinga."},
    {"kind": "myanmar", "q": "Why is tea famous in Myanmar?", "a": "Because it is a drink Myanmar people enjoy every day."},
    {"kind": "myanmar", "q": "How many regions and states are there in Myanmar?", "a": "7 regions and 7 states - 14 in total."},
    {"kind": "myanmar", "q": "When is Myanmar's Independence Day?", "a": "January 4."},
    {"kind": "myanmar", "q": "What colours are in Myanmar's flag?", "a": "Yellow, green, red, and a white star."},
    {"kind": "myanmar", "q": "In which city is Shwedagon Pagoda?", "a": "In Yangon."},
    {"kind": "myanmar", "q": "In which city is Mandalay Hill?", "a": "In Mandalay."},
    {"kind": "myanmar", "q": "What is the largest lake in Myanmar?", "a": "Inle Lake."},
    {"kind": "myanmar", "q": "What do people do during Thingyan?", "a": "They splash water and celebrate the New Year joyfully."},
    {"kind": "myanmar", "q": "In which direction is Myanmar script written?", "a": "From left to right."},
    {"kind": "myanmar", "q": "What is traditional Myanmar clothing?", "a": "Longyi and taikpon."},
    {"kind": "myanmar", "q": "Is rice the main food of Myanmar people?", "a": "Yes."},
    {"kind": "myanmar", "q": "What is the official language of Myanmar?", "a": "Burmese (the Myanmar language)."},
    {"kind": "myanmar", "q": "Is Buddhism the main religion in Myanmar?", "a": "Yes, most people practise it."},
    {"kind": "myanmar", "q": "What is Myanmar's time zone?", "a": "UTC+06:30."},
    {"kind": "myanmar", "q": "In which region is Bagan?", "a": "In Mandalay Region."},
    {"kind": "myanmar", "q": "What is the capital of Kachin State?", "a": "Myitkyina."},
    {"kind": "myanmar", "q": "What is the capital of Shan State?", "a": "Taunggyi."},
    {"kind": "myanmar", "q": "What is the capital of Rakhine State?", "a": "Sittwe."},
    {"kind": "myanmar", "q": "What is the capital of Mon State?", "a": "Mawlamyine."},
    {"kind": "myanmar", "q": "What is the capital of Kayin State?", "a": "Hpa-an."},
    {"kind": "myanmar", "q": "What is the capital of Ayeyarwady Region?", "a": "Pathein."},
    {"kind": "myanmar", "q": "What is the capital of Sagaing Region?", "a": "Sagaing."},
    {"kind": "myanmar", "q": "What is the capital of Magway Region?", "a": "Magway."},
    {"kind": "myanmar", "q": "What is the capital of Bago Region?", "a": "Bago."},
    {"kind": "myanmar", "q": "What is the capital of Tanintharyi Region?", "a": "Dawei."},
    {"kind": "myanmar", "q": "What is the capital of Chin State?", "a": "Hakha."},
    {"kind": "myanmar", "q": "What is the capital of Kayah State?", "a": "Loikaw."},
    {"kind": "myanmar", "q": "What is the national sport of Myanmar?", "a": "Chinlone."},
    {"kind": "myanmar", "q": "What is the main ingredient of mohinga?", "a": "Fish and rice noodles."},
    {"kind": "myanmar", "q": "Shan noodles are the food of which region?", "a": "Shan State."},
    {"kind": "myanmar", "q": "What is lahpet thoke made of?", "a": "Tea leaves, beans, sesame, garlic, and oil."},
    {"kind": "myanmar", "q": "How many digits are there in Myanmar numerals?", "a": "10, from 0 to 9."},
    {"kind": "myanmar", "q": "What does 'Mingalaba' mean?", "a": "It is a greeting that means 'may you be blessed'."},
    {"kind": "myanmar", "q": "What does 'Kyeizu tin ba de' mean?", "a": "It means 'thank you'."},
    {"kind": "myanmar", "q": "What is a traditional Myanmar musical instrument?", "a": "The saung gauk (Burmese harp)."},
    {"kind": "myanmar", "q": "In which region is Naypyidaw?", "a": "In the Naypyidaw Union Territory."},
    # ------------------------------------------------------------------
    # business — business & marketing
    # ------------------------------------------------------------------
    {"kind": "business", "q": "What is the first thing to do when starting a business?", "a": "Find a problem customers really need solved, then build a product that solves it."},
    {"kind": "business", "q": "What is profit?", "a": "The money left after subtracting all costs from revenue."},
    {"kind": "business", "q": "What is COGS?", "a": "The direct cost of making or buying a product."},
    {"kind": "business", "q": "What should you look at when setting a price?", "a": "Costs, competitor prices, and customer value."},
    {"kind": "business", "q": "What is a target customer?", "a": "The group of people most likely to buy your product."},
    {"kind": "business", "q": "What is marketing?", "a": "The process of making customers aware of, interested in, and buying your product."},
    {"kind": "business", "q": "What is branding?", "a": "The identity that makes customers remember your business."},
    {"kind": "business", "q": "What is word of mouth marketing?", "a": "Marketing where satisfied customers tell others about your product."},
    {"kind": "business", "q": "What is one of the best ways to increase sales?", "a": "Truly solve the customer's problem and offer a quality product."},
    {"kind": "business", "q": "What is cash flow?", "a": "The flow of money coming into and going out of a business."},
    {"kind": "business", "q": "What is profit margin?", "a": "Profit shown as a percentage of revenue."},
    {"kind": "business", "q": "What is the break-even point?", "a": "The point where revenue equals costs - no profit, no loss."},
    {"kind": "business", "q": "What is customer retention?", "a": "Keeping existing customers buying from you."},
    {"kind": "business", "q": "Which is cheaper: finding new customers or keeping existing ones?", "a": "Keeping existing customers is cheaper."},
    {"kind": "business", "q": "What is a USP?", "a": "Unique Selling Proposition - the advantage that makes your product different from competitors."},
    {"kind": "business", "q": "Why is social media marketing important?", "a": "Because your customers spend most of their time there, so your business can reach them there."},
    {"kind": "business", "q": "What is content marketing?", "a": "Attracting customers by giving them useful content."},
    {"kind": "business", "q": "Is giving discounts always good?", "a": "No. Frequent discounts train customers to expect cheap prices."},
    {"kind": "business", "q": "What is inventory?", "a": "The list of products kept in stock to sell."},
    {"kind": "business", "q": "What is a supplier?", "a": "The person who supplies products to your business."},
    {"kind": "business", "q": "What is the difference between revenue and profit?", "a": "Revenue is total sales; profit is what remains after subtracting costs."},
    {"kind": "business", "q": "What is the most important thing for a small business to succeed?", "a": "Giving customers a product and service that is truly valuable."},
    {"kind": "business", "q": "What is a pricing strategy?", "a": "A plan for how to set your prices."},
    {"kind": "business", "q": "What is competitor analysis?", "a": "Studying what competitors sell, at what price, and how they market."},
    {"kind": "business", "q": "Why should you listen to customer feedback?", "a": "To improve your product and make customers happy."},
    {"kind": "business", "q": "What does an online shop need?", "a": "Product photos, prices, payment methods, a delivery plan, and contact details."},
    {"kind": "business", "q": "What is important for selling on a Facebook Page?", "a": "Good-quality photos, clear prices, and fast replies."},
    {"kind": "business", "q": "Why is a Telegram channel good for sales?", "a": "You can send news directly to customers and posts don't get lost."},
    {"kind": "business", "q": "Why is trust important in sales?", "a": "Customers only buy when they trust you - trust is the foundation of sales."},
    {"kind": "business", "q": "Why should you have a refund policy?", "a": "It reassures customers and builds trust."},
    {"kind": "business", "q": "What is upselling?", "a": "Suggesting a better version of the product the customer is buying."},
    {"kind": "business", "q": "What is cross-selling?", "a": "Suggesting another product related to the one being bought."},
    {"kind": "business", "q": "What makes a good brand name?", "a": "Easy to remember, easy to pronounce, and a good fit for your business."},
    {"kind": "business", "q": "What is a business plan?", "a": "A document that sets out the business's goals, market, and financial plan."},
    {"kind": "business", "q": "What is bootstrapping?", "a": "Starting a business with your own money, without outside investment."},
    {"kind": "business", "q": "What is a side hustle?", "a": "Work done alongside your main job to earn extra income."},
    {"kind": "business", "q": "What is passive income?", "a": "Income earned without spending much time (for example, money from selling books)."},
    {"kind": "business", "q": "What is a digital product?", "a": "A product sold online (for example, an ebook, a course, or a template)."},
    {"kind": "business", "q": "What is affiliate marketing?", "a": "Recommending someone else's product and earning a commission on each sale."},
    {"kind": "business", "q": "Why is email marketing effective?", "a": "It reaches customers directly and gets repeat purchases at low cost."},
    {"kind": "business", "q": "What is a conversion rate?", "a": "The percentage of visitors who actually buy."},
    {"kind": "business", "q": "What is a landing page?", "a": "A single page designed to persuade customers to buy."},
    {"kind": "business", "q": "Why is a free trial effective?", "a": "Because customers can try the product and buy only if they like it."},
    {"kind": "business", "q": "What makes good customer service?", "a": "Fast replies, politeness, and solving the problem."},
    {"kind": "business", "q": "What is negotiation?", "a": "Discussing to reach an agreement both sides accept."},
    {"kind": "business", "q": "What is networking?", "a": "Connecting with people in your business and finding opportunities."},
    {"kind": "business", "q": "What is time management?", "a": "Managing your time effectively."},
    {"kind": "business", "q": "What is delegation?", "a": "Handing work to someone else so you can focus on what matters most."},
    {"kind": "business", "q": "What is risk management?", "a": "Finding possible risks in advance and protecting against them."},
    {"kind": "business", "q": "What does scaling a business mean?", "a": "Growing the business bigger to increase revenue."},
    # ------------------------------------------------------------------
    # science — science & technology
    # ------------------------------------------------------------------
    {"kind": "science", "q": "What planet is closest to the Sun?", "a": "Mercury."},
    {"kind": "science", "q": "What planet is known as the Morning Star?", "a": "Venus."},
    {"kind": "science", "q": "What is the largest moon in our solar system?", "a": "Ganymede, a moon of Jupiter."},
    {"kind": "science", "q": "What force keeps us on the ground?", "a": "Gravity."},
    {"kind": "science", "q": "What is the speed of light in a vacuum?", "a": "About 300,000 kilometres per second."},
    {"kind": "science", "q": "What is the boiling point of water at sea level?", "a": "100 degrees Celsius."},
    {"kind": "science", "q": "What is the freezing point of water?", "a": "0 degrees Celsius."},
    {"kind": "science", "q": "What gas do humans need to breathe?", "a": "Oxygen."},
    {"kind": "science", "q": "What organ pumps blood around the human body?", "a": "The heart."},
    {"kind": "science", "q": "How many bones are in the adult human body?", "a": "206."},
    {"kind": "science", "q": "What is the powerhouse of the cell?", "a": "The mitochondria."},
    {"kind": "science", "q": "What is DNA?", "a": "The molecule that carries genetic instructions in living things."},
    {"kind": "science", "q": "What is the chemical formula of carbon dioxide?", "a": "CO2."},
    {"kind": "science", "q": "What is the chemical symbol for iron?", "a": "Fe."},
    {"kind": "science", "q": "What is the chemical symbol for sodium?", "a": "Na."},
    {"kind": "science", "q": "What metal is liquid at room temperature?", "a": "Mercury."},
    {"kind": "science", "q": "What is the main function of red blood cells?", "a": "To carry oxygen around the body."},
    {"kind": "science", "q": "What part of the plant makes food using sunlight?", "a": "The leaf, through photosynthesis."},
    {"kind": "science", "q": "What is photosynthesis?", "a": "The process by which plants use sunlight, water and carbon dioxide to make food and oxygen."},
    {"kind": "science", "q": "What is the largest organ in the human body?", "a": "The skin."},
    {"kind": "science", "q": "How many chambers does the human heart have?", "a": "Four."},
    {"kind": "science", "q": "What is an atom?", "a": "The smallest unit of ordinary matter."},
    {"kind": "science", "q": "What is the centre of an atom called?", "a": "The nucleus."},
    {"kind": "science", "q": "What is electricity?", "a": "The flow of electric charge, usually electrons."},
    {"kind": "science", "q": "What does CPU stand for?", "a": "Central Processing Unit."},
    {"kind": "science", "q": "What does RAM stand for?", "a": "Random Access Memory."},
    {"kind": "science", "q": "What does HTML stand for?", "a": "HyperText Markup Language."},
    {"kind": "science", "q": "What does AI stand for?", "a": "Artificial Intelligence."},
    {"kind": "science", "q": "What is a byte?", "a": "A unit of digital data made of 8 bits."},
    {"kind": "science", "q": "How many bits are in a byte?", "a": "Eight."},
    {"kind": "science", "q": "What is the internet?", "a": "A global network of connected computers."},
    {"kind": "science", "q": "What is a computer program?", "a": "A set of instructions a computer follows."},
    {"kind": "science", "q": "What is Python?", "a": "A popular programming language."},
    {"kind": "science", "q": "What is an algorithm?", "a": "A step-by-step procedure for solving a problem."},
    {"kind": "science", "q": "What is the Moon?", "a": "Earth's only natural satellite."},
    {"kind": "science", "q": "How long does it take the Moon to orbit Earth?", "a": "About 27 days."},
    {"kind": "science", "q": "How long does Earth take to orbit the Sun?", "a": "About 365 days."},
    {"kind": "science", "q": "What causes the seasons?", "a": "The tilt of Earth's axis."},
    {"kind": "science", "q": "What is the hottest planet in our solar system?", "a": "Venus."},
    {"kind": "science", "q": "What is a black hole?", "a": "A region of space where gravity is so strong that not even light can escape."},
    {"kind": "science", "q": "What is the Big Bang?", "a": "The leading theory for how the universe began, about 13.8 billion years ago."},
    {"kind": "science", "q": "What is gravity?", "a": "A force that attracts objects with mass toward each other."},
    {"kind": "science", "q": "What is energy?", "a": "The ability to do work."},
    {"kind": "science", "q": "What is the unit of electric current?", "a": "The ampere."},
    {"kind": "science", "q": "What is the unit of force?", "a": "The newton."},
    {"kind": "science", "q": "What is the main source of energy for Earth?", "a": "The Sun."},
    {"kind": "science", "q": "What are the three states of matter?", "a": "Solid, liquid and gas."},
    {"kind": "science", "q": "What is evaporation?", "a": "When a liquid turns into a gas."},
    {"kind": "science", "q": "What is condensation?", "a": "When a gas turns into a liquid."},
    {"kind": "science", "q": "What do we call animals that eat only plants?", "a": "Herbivores."},
    # ------------------------------------------------------------------
    # daily — daily life & practical skills
    # ------------------------------------------------------------------
    {"kind": "daily", "q": "When cooking rice, what is the ratio of rice to water?", "a": "About 1 cup of rice to 1.5 cups of water. It depends on the rice type."},
    {"kind": "daily", "q": "How long does it take to boil an egg?", "a": "After the water boils, about 8-10 minutes for a firm yolk."},
    {"kind": "daily", "q": "How much water should you drink in a day?", "a": "About 2 litres on average (8 glasses)."},
    {"kind": "daily", "q": "What is the best way to save money?", "a": "Set money aside as soon as you get paid, then spend the rest."},
    {"kind": "daily", "q": "What is the first thing to do when you wake up in the morning?", "a": "Drink a glass of water and get some sunlight for a while."},
    {"kind": "daily", "q": "How much sleep do you need?", "a": "7-9 hours a night for an adult."},
    {"kind": "daily", "q": "What should you watch out for when charging your phone?", "a": "Don't charge it in a very hot place, and use the original charging cable."},
    {"kind": "daily", "q": "How do you start a reading habit?", "a": "Start with 10 minutes a day and read at a regular time."},
    {"kind": "daily", "q": "What is a way to stay focused while working?", "a": "The Pomodoro method - work for 25 minutes, rest for 5."},
    {"kind": "daily", "q": "What is the Pomodoro technique?", "a": "A time management method: focus and work for 25 minutes, then rest for 5."},
    {"kind": "daily", "q": "What house cleaning should you do every week?", "a": "Mop the floor, dust, clean the bathroom, and take out the trash."},
    {"kind": "daily", "q": "How should you wash white clothes?", "a": "Wash them separately from other colours and dry them in the sun."},
    {"kind": "daily", "q": "How long can you keep food in the fridge?", "a": "Cooked food should be eaten within 3-4 days."},
    {"kind": "daily", "q": "How long should you wash your hands?", "a": "At least 20 seconds with soap."},
    {"kind": "daily", "q": "How long should you brush your teeth?", "a": "Twice a day, about 2 minutes each time."},
    {"kind": "daily", "q": "How often should you get a health check-up?", "a": "Once a year for a general check-up."},
    {"kind": "daily", "q": "How can you reduce phone screen time?", "a": "Don't use your phone for 1 hour before bed; read a book instead."},
    {"kind": "daily", "q": "Why is it important to track your spending?", "a": "So you know where your money goes and can cut unnecessary spending."},
    {"kind": "daily", "q": "How much emergency money should you save?", "a": "At least 3 months of expenses."},
    {"kind": "daily", "q": "What is most important when driving a car?", "a": "Wearing a seatbelt, controlling your speed, and not using your phone."},
    {"kind": "daily", "q": "What should you do during a power outage?", "a": "Keep candles or a lamp ready and unplug electrical appliances."},
    {"kind": "daily", "q": "What should you take when you go out in the rain?", "a": "Take an umbrella or a raincoat."},
    {"kind": "daily", "q": "What should you do when you go out in the sun?", "a": "Apply sunscreen and wear a hat."},
    {"kind": "daily", "q": "What should you check when buying food?", "a": "The expiry date, packaging, and quality."},
    {"kind": "daily", "q": "Why is writing a shopping list good?", "a": "It saves money by stopping you from buying things you don't need."},
    {"kind": "daily", "q": "What should you do for internet security?", "a": "Use a strong password and don't share it with others."},
    {"kind": "daily", "q": "How do you make a strong password?", "a": "Mix letters, numbers, and symbols, and use at least 12 characters."},
    {"kind": "daily", "q": "What should you do first if you lose your phone?", "a": "Find it with Find My Device and block the SIM if needed."},
    {"kind": "daily", "q": "What should you prepare for a job interview?", "a": "Study the company and prepare to explain your experience clearly."},
    {"kind": "daily", "q": "What should a CV be like?", "a": "Short and clear, with your experience and skills standing out."},
    {"kind": "daily", "q": "What is important when taking an exam?", "a": "Read the questions carefully and manage your time."},
    {"kind": "daily", "q": "What is the best way to learn a new language?", "a": "Practise a little every day and actually use it."},
    {"kind": "daily", "q": "How can you reduce stress?", "a": "Breathe deeply, go for a walk, and get enough sleep."},
    {"kind": "daily", "q": "What should you do for fire safety at home?", "a": "Watch the stove and keep a fire extinguisher."},
    {"kind": "daily", "q": "What should you do when giving first aid?", "a": "If there is bleeding, press on it and call the emergency number."},
    {"kind": "daily", "q": "What should you do if you get food poisoning?", "a": "Drink plenty of water, rest, and go to the hospital if it is severe."},
    {"kind": "daily", "q": "What should you do if you have a headache?", "a": "Drink water, rest, and take medicine if needed."},
    {"kind": "daily", "q": "Where do you get vitamin D?", "a": "From sunlight, fish, and eggs."},
    {"kind": "daily", "q": "What should you look at when buying meat or fish?", "a": "Freshness, colour, and smell."},
    {"kind": "daily", "q": "How much salt should you add when cooking?", "a": "Add a little at a time and taste as you go."},
    {"kind": "daily", "q": "How should you store leftover rice?", "a": "Let it cool, then put it in the fridge."},
    {"kind": "daily", "q": "How do you make a phone battery last longer?", "a": "Charge between 20-80% and don't let it get too hot."},
    {"kind": "daily", "q": "What should you watch when sitting at a work desk?", "a": "Sit up straight and keep the screen at eye level."},
    {"kind": "daily", "q": "What are the signs of dehydration?", "a": "Thirst, headache, and tiredness."},
    {"kind": "daily", "q": "What should you watch when using a washing machine?", "a": "Don't overload it, and wash colours separately."},
    {"kind": "daily", "q": "What should you do before bed?", "a": "Put your phone away and read a book or do breathing exercises."},
    {"kind": "daily", "q": "Why is breakfast important?", "a": "It gives you energy and focus for the day."},
    {"kind": "daily", "q": "What is the best time for a student to study?", "a": "In the morning or evening, when focus is best."},
    {"kind": "daily", "fact": "Keep emergency phone numbers saved: family, hospital, and police."},
    {"kind": "daily", "fact": "When renting a house, check the water and electricity, security, contract, and neighbourhood."},
    # ------------------------------------------------------------------
    # health — health & wellbeing
    # ------------------------------------------------------------------
    {"kind": "health", "q": "How much sleep do adults need per night?", "a": "7 to 9 hours."},
    {"kind": "health", "q": "How much water should you drink per day?", "a": "About 2 litres (around 8 glasses)."},
    {"kind": "health", "q": "What is a healthy heart rate at rest?", "a": "About 60 to 100 beats per minute."},
    {"kind": "health", "q": "What exercise is good for the heart?", "a": "Brisk walking, running, swimming or cycling."},
    {"kind": "health", "q": "How often should adults exercise?", "a": "At least 150 minutes of moderate exercise per week."},
    {"kind": "health", "q": "What is BMI?", "a": "Body Mass Index — a measure of body fat based on height and weight."},
    {"kind": "health", "q": "What foods are rich in protein?", "a": "Eggs, fish, chicken, beans and lentils."},
    {"kind": "health", "q": "What foods are rich in vitamin C?", "a": "Oranges, lemons, guava, bell peppers and tomatoes."},
    {"kind": "health", "q": "What is vitamin D good for?", "a": "Healthy bones and the immune system."},
    {"kind": "health", "q": "Why should you eat breakfast every morning?", "a": "It gives you energy and focus for the day."},
    {"kind": "health", "q": "What is stress?", "a": "The body's response to pressure or demands."},
    {"kind": "health", "q": "What are some ways to lower stress?", "a": "Deep breathing, walking, enough sleep and talking to someone you trust."},
    {"kind": "health", "q": "What is meditation?", "a": "A practice of focusing the mind to feel calm and clear."},
    {"kind": "health", "q": "How long should brushing your teeth take?", "a": "Two minutes, twice a day."},
    {"kind": "health", "q": "How often should you wash your hands?", "a": "Before eating, after using the toilet and after touching dirty things."},
    {"kind": "health", "q": "What is a fever?", "a": "A body temperature above the normal 37°C, often a sign of infection."},
    {"kind": "health", "q": "What is the normal body temperature?", "a": "About 37°C (98.6°F)."},
    {"kind": "health", "q": "What should you do for a small cut?", "a": "Clean it with water, apply antiseptic and cover it."},
    {"kind": "health", "q": "What is dehydration?", "a": "When the body loses more water than it takes in."},
    {"kind": "health", "q": "How can you tell if you are dehydrated?", "a": "Thirst, headache, tiredness and dark urine."},
    {"kind": "health", "q": "Why is sleep important for memory?", "a": "The brain organises memories during sleep."},
    {"kind": "health", "q": "What is a balanced diet?", "a": "Eating a variety of foods — grains, vegetables, fruits, protein and healthy fats."},
    {"kind": "health", "q": "What is fibre good for?", "a": "Digestion and keeping you full."},
    {"kind": "health", "q": "What foods are high in fibre?", "a": "Vegetables, fruits, whole grains, beans and nuts."},
    {"kind": "health", "q": "How can you improve your posture?", "a": "Sit straight, keep your screen at eye level and stretch often."},
    {"kind": "health", "q": "What is stretching good for?", "a": "Flexibility and preventing injuries."},
    {"kind": "health", "q": "How can you protect your eyes from screens?", "a": "Follow the 20-20-20 rule — every 20 minutes, look at something 20 feet away for 20 seconds."},
    {"kind": "health", "q": "What is the 20-20-20 rule?", "a": "Every 20 minutes of screen time, look at something 20 feet away for 20 seconds."},
    {"kind": "health", "q": "What is mindfulness?", "a": "Paying attention to the present moment without judgement."},
    {"kind": "health", "q": "What is a healthy snack?", "a": "Fruits, nuts, yoghurt or boiled eggs."},
    {"kind": "health", "q": "Why should you avoid too much sugar?", "a": "It can cause tooth decay, weight gain and energy crashes."},
    {"kind": "health", "q": "What is high blood pressure?", "a": "When blood pushes too hard against artery walls. It is called the silent killer because it often has no symptoms."},
    {"kind": "health", "q": "How can you lower blood pressure naturally?", "a": "Less salt, regular exercise, healthy weight and less stress."},
    {"kind": "health", "q": "What is diabetes?", "a": "A condition where blood sugar is too high because the body cannot use insulin properly."},
    {"kind": "health", "q": "What is the best time to exercise?", "a": "Whenever you can do it regularly — morning or evening both work."},
    {"kind": "health", "q": "What is yoga?", "a": "A practice combining body postures, breathing and meditation."},
    {"kind": "health", "q": "How can you sleep better?", "a": "Keep a regular bedtime, avoid phones before bed and keep the room dark and cool."},
    {"kind": "health", "q": "What is a cold?", "a": "A common viral infection of the nose and throat."},
    {"kind": "health", "q": "How can you avoid catching a cold?", "a": "Wash hands often, avoid touching your face and get enough sleep."},
    {"kind": "health", "q": "What is the immune system?", "a": "The body's defence against infections and disease."},
    {"kind": "health", "q": "What foods boost immunity?", "a": "Citrus fruits, garlic, ginger, yoghurt and green vegetables."},
    {"kind": "health", "q": "Why is walking good for you?", "a": "It improves heart health, mood and burns calories with low injury risk."},
    {"kind": "health", "q": "How many steps a day should you walk?", "a": "About 7,000 to 10,000 steps is a good target."},
    {"kind": "health", "q": "What is mental health?", "a": "How you think, feel and cope with life's challenges."},
    {"kind": "health", "q": "When should you see a doctor?", "a": "When symptoms are severe, last more than a few days, or worry you."},
    {"kind": "health", "q": "What is a vaccine?", "a": "A preparation that trains the immune system to fight a disease."},
    {"kind": "health", "q": "What is first aid?", "a": "Immediate help given to an injured or sick person before professional care."},
    {"kind": "health", "q": "What should be in a first aid kit?", "a": "Bandages, antiseptic, cotton, scissors, pain relief and emergency numbers."},
    {"kind": "health", "q": "Is a little exercise also good for your health?", "a": "Yes. Even walking every day is good for your heart and mind."},
    {"kind": "health", "q": "What can happen if you don't get enough sleep?", "a": "Poor focus, irritability, and a weaker immune system."},
]


def _entry_key(entry):
    if "q" in entry:
        return "q:" + bank.normalize(entry["q"])
    return "f:" + bank.normalize(entry["fact"])


def _existing_keys():
    keys = set()
    if not os.path.exists(BANK_FILE):
        return keys
    with open(BANK_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(obj, dict) or obj.get("kind") not in bank.KINDS:
                continue
            if "q" in obj:
                keys.add("q:" + bank.normalize(str(obj["q"])))
            elif "fact" in obj:
                keys.add("f:" + bank.normalize(str(obj["fact"])))
    return keys


def _recount():
    per_kind = {k: 0 for k in bank.KINDS}
    total = 0
    malformed = 0
    if os.path.exists(BANK_FILE):
        with open(BANK_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    malformed += 1
                    continue
                if not isinstance(obj, dict) or obj.get("kind") not in bank.KINDS:
                    malformed += 1
                    continue
                if ("q" in obj and "a" in obj) or "fact" in obj:
                    per_kind[obj["kind"]] += 1
                    total += 1
                else:
                    malformed += 1
    return per_kind, total, malformed


def main():
    seen = _existing_keys()
    new_entries = [e for e in ENTRIES if _entry_key(e) not in seen]
    skipped = len(ENTRIES) - len(new_entries)
    if new_entries:
        with open(BANK_FILE, "a", encoding="utf-8") as f:
            for entry in new_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    per_kind, total, malformed = _recount()
    progress = {
        "total": total,
        "per_kind": per_kind,
        "capacity": bank.CAPACITY,
        "goal": 950000,
        "per_kind_goal": 150000,
        "last_batch_id": BATCH_ID,
        "last_batch_added": len(new_entries),
        "malformed_lines": malformed,
    }
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESS_FILE)
    print("batch %s: +%d new, %d skipped (already in bank)" % (BATCH_ID, len(new_entries), skipped))
    print("bank total: %d  per-kind: %s  malformed: %d" % (total, per_kind, malformed))


if __name__ == "__main__":
    main()

