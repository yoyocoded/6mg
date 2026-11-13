"""
6mg - Tata 1mg counterface prototype (Flet), built from the Figma file "6mg".
Screens (exactly the ones in Figma): phone number -> preferences -> home -> product / accounts / checkout.
Added at your request (not in the Figma): care plan, insights, nucoins, past orders (all reached from accounts),
and the prescription screen (reached from checkout when a medicine that needs a prescription is in the cart).

Run:   flet run main.py

WHERE TO EDIT THE POP-UP BOXES
    -> the EXPLANATIONS dict just below (search for "EXPLANATIONS").
       One entry per green-underlined phrase. "" = the box opens empty.

WHERE TO PUT THE ITEM IMAGES
    1. Make a folder called  assets  next to main.py and put the picture files in it.
    2. PRODUCT_IMAGES (just under PRODUCTS) says which file belongs to which item - change the file names there.
       An item with no file (or "") keeps its grey square. A web address (https://...) also works.
    The pictures appear in three places, all drawn by item_image():
       item cards on home / "frequently bought together"   71 x 71, rounded corners 8    (item_card)
       the product page                                    231 x 231, rounded corners 12  (product_screen)
       the cart rows on checkout                           64 x 64, rounded corners 8     (checkout_screen)
    Pictures are cropped to fill the square, so square pictures look best.

WHERE EACH PREFERENCE SHOWS UP (everything else in the prefs list has no place in the Figma yet)
    location          home        location pill: "Enter delivery address" -> current location
    reference_prices  home + product page   reference (struck-through) price next to the price
    <any data pref>   home        "recommended" chip: shortcuts are picked from the data the user shares
    <data prefs>      checkout    "What we've learnt from you:" lists what was collected
    (see PREF_PLACES for the full table, including the preferences that have no place yet)

To change a preference later (e.g. from a settings screen):  State.prefs["reference_prices"] = False ; navigate(App.current)
"""
import sys
import asyncio
import calendar
import datetime
import inspect
import os
import re
import time
import flet as ft

# =====================================================================
# CONFIG
# =====================================================================

# ---- Colours: the Tata 1mg palette (sampled from the reference screenshots) ----
C_PRIMARY = "#FF5443"      # 1mg coral. Decorative only (dots, icons, borders): white text on it would only be 3.2:1
C_PRIMARY_DARK = "#CC3322" # the same coral, darkened until white-on-coral and coral-on-white text both reach 5.2:1
C_TEXT = "#191A1F"         # 1mg near-black
C_GREY = "#626A77"         # 1mg slate, for secondary text (5.4:1 on white)
C_BORDER = "#E3E6ED"       # card / field outlines (never used for text)
C_DIVIDER = "#F0F0F0"      # thin lines between rows
C_PAGE = "#F4F5F9"         # the light grey page behind white cards (checkout)
C_ORANGE = "#F28C28"       # the "re-order" button (dark text on it: 6.7:1; white would only be 2.5:1)
C_MINT = "#EEFCF5"         # green pop-up background (same as the phone-screen bubble)
C_MINT_LINE = "#BFEBD3"
C_REFILL = "#FBF1E5"       # refill card (1mg cream, maroon outline)
C_PINK = "#FDE9E6"         # countdown card (pale coral)
C_BADGE = "#CC3322"        # cart count badge
C_RED = "#C00000"          # the "low stock" text (pure red is too faint on white)
C_MAROON = "#8F3F38"       # care plan card (1mg maroon)
C_WHITE = "#FFFFFF"
C_PEACH = "#FFF1EF"        # light coral tint (selected / secondary fills)
C_PEACH_LINE = "#FFC9C2"
C_BLUE = "#E7F1FD"         # 1mg pale blue tile (category icons)
C_SLOT = "#F0F1F5"         # empty image / shortcut placeholders
TRANSPARENT = "#00000000"
C_UNDERLINE = "#2DBE7B"    # the green underline on tappable words
C_INFO = "#12A150"
C_DISABLED_BG = "#EDEDF0"
C_DISABLED_LINE = "#DCDCE0"
RADIUS = 12                # corner radius of cards, fields and buttons (1mg uses small, even corners)
BTN_RADIUS = 8

FONT = "Figtree"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/figtree/Figtree%5Bwght%5D.ttf"
WINDOW_W, WINDOW_H = 360, 800

# ---- Text that IS in the Figma -----------------------------------------
TXT_BUBBLE_1 = "Click on words underlined like "
TXT_BUBBLE_TERM = "this"
TXT_BUBBLE_2 = " to learn more."
TXT_PHONE_TITLE_1 = "Enter your "
TXT_PHONE_TITLE_TERM = "phone number"
TXT_COUNTRY = "+91"
TXT_CONTINUE = "Continue"
TXT_SKIP = "Skip\n(you'll be able to browse, but not order)"
# The OTP screen is not in the Figma: it reuses the phone screen's look. Texts are placeholders. Any 4 digits are accepted.
TXT_OTP_TITLE = "Enter the OTP"
TXT_OTP_SUB = "We’ve sent a 4-digit code to +91 {phone}"
TXT_OTP_HINT = "4-digit OTP"
TXT_PREFS_TITLE = "Customise your experience"      # title of the preferences screen; also the name of its settings row and shortcut
TXT_PREFS_NOTE = "Please read these carefully! You’re practically building the app for yourself."      # under the title of the preferences screen
TXT_REQUIRED_TITLE = "Required information:"
REQUIRED_ITEMS = [
    "Your delivery address",
    "Your phone number (for purchases only) and an OTP",
    "Prescription verification for medicines that require it (personal details can be censored)",
]
TXT_LOCATION_DEFAULT = "Enter delivery address"
TXT_SEARCH = "Search"
TABS = ["Popular categories", "Pharmacy", "Labs", "Consults", "Vaccines"]
TXT_SHORTCUTS = "Your shortcuts"
TXT_RECOMMENDED = "recommended"
TXT_CARE_TITLE = "Get more out of 6mg with our care plan!"
TXT_CARE_SUB = "₹275 for 6 months"
TXT_CARE_HIDE = "Hide for 7 days"
TXT_ADD_TO_CART_SMALL = "Add to cart"
TXT_PICKED = "Picked for you"
TXT_LOW_STOCK = "Low stock!"
TXT_FBT = "Frequently bought together"
# Prescriptions (not in the Figma - placeholder texts, EDIT HERE)
TXT_RX_REQUIRED = "Prescription required"          # product page, beside the Rx symbol (the green-underlined part opens EXPLANATIONS["rx_required"])
TXT_RX_UPLOAD = "Upload prescription"              # checkout button (shown while a medicine that needs a prescription is in the cart)
TXT_RX_UPLOADED = "Prescription uploaded"          # the same button once the prescription has been uploaded
TXT_RX_TITLE = "Prescription"                      # title of the editing screen
TXT_RX_MANUAL = "Manual edit"                           # dead button: does nothing
TXT_RX_AUTO = "Auto edit"                               # puts black bars over the personal details
TXT_RX_DONE = "Done"                               # back to checkout, prescription uploaded
# "Your prescriptions: ..." line under "What we've learnt from you" (one line, whichever of the two preferences are on)
TXT_RX_LINE = "Your prescriptions: {what}"
RX_KEEP = "the contents are stored and the image is deleted"
RX_SHARE = "the contents are shared with advertising, analytics and AI model partners"
RX_BOTH = "the contents are stored and the image is deleted, and the contents are shared with advertising, analytics and AI model partners"

# ---- PLACEHOLDER ITEMS (your Figma only says "Item 1" / ₹100 - names and prices below are made up) ----
# id: (name, unit price in rupees).  EDIT NAMES / PRICES HERE.
PRODUCTS = {
    "cold_tablets": ("Cold tablets", 90),
    "cough_syrup": ("Cough syrup", 120),
    "paracetamol": ("Paracetamol", 30),
    "vitamin_c": ("Vitamin C", 150),
    "antacid": ("Antacid", 60),
    "ors": ("ORS sachets", 40),
    "sanitiser": ("Sanitiser", 80),
    "thermometer": ("Thermometer", 250),
    # added for the two new rows (placeholder names and prices, like the rest)
    "nasal_drops": ("Nasal drops", 70),
    "ibuprofen": ("Ibuprofen", 45),
    "pain_gel": ("Pain relief gel", 110),
    "digestive_tablets": ("Digestive tablets", 55),
    "gas_drops": ("Gas relief drops", 95),
    "probiotic": ("Probiotic", 130),
}

# ---- ITEM IMAGES: put the files in a folder called  assets  next to this file, then name them here. ----
# The file name (relative to assets/) or a web address for each item. "" or a missing file = the grey square stays.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
PRODUCT_IMAGES = {
    "cold_tablets": "cold_tablets.png",
    "cough_syrup": "cough_syrup.png",
    "paracetamol": "paracetamol.png",
    "vitamin_c": "vitamin_c.png",
    "antacid": "antacid.png",
    "ors": "ors.png",
    "sanitiser": "sanitiser.png",
    "thermometer": "thermometer.png",
    "nasal_drops": "nasal_drops.png",
    "ibuprofen": "ibuprofen.png",
    "pain_gel": "pain_gel.png",
    "digestive_tablets": "digestive_tablets.png",
    "gas_drops": "gas_drops.png",
    "probiotic": "probiotic.png",
}
# The rows on home, one medicine class each: (heading, items). Headings are placeholders - EDIT HERE.
HOME_ROW = ["cold_tablets", "cough_syrup", "nasal_drops"]          # first row of items on home
FEVER_ROW = ["paracetamol", "ibuprofen", "pain_gel"]
STOMACH_ROW = ["antacid", "digestive_tablets", "gas_drops"]
HOME_SECTIONS = [("Cold medicine", HOME_ROW), ("Fever medicine", FEVER_ROW), ("Stomach care", STOMACH_ROW)]
PICKED_ROW = ["vitamin_c", "antacid", "ors"]                     # "Picked for you" row
FBT_POOL = ["cough_syrup", "paracetamol", "ors", "vitamin_c", "sanitiser", "cold_tablets"]   # "frequently bought together" (the open item is skipped)
# Medicines that need a prescription ("a few random ones" - EDIT HERE). Their product page shows "Prescription required",
# and checkout offers "Upload prescription" while one of them is in the cart.
RX_PRODUCTS = {"cough_syrup", "ibuprofen", "nasal_drops"}
REFERENCE_MARKUP = 1.25        # reference price shown = price x this (placeholder rule; Figma gives no value)

# ---- PLACEHOLDER past orders (feed the "past orders" screen, the insights calendar, the refill card and re-order). EDIT HERE. ----
# One entry per order: placeholder id, date, status and {item id: quantity}. Add more entries and everything follows.
PAST_ORDERS = [
    {"id": "#6MG-1001", "date": datetime.date(2026, 11, 5), "status": "Delivered",
     "items": {"paracetamol": 2, "cough_syrup": 1}},
]
# The refill card uses the latest order: (item id, days of supply left). The 5 days are placeholders.
PREVIOUS_ORDER = [(pid, 5) for pid in PAST_ORDERS[-1]["items"]]
TXT_PAST_ORDERS = "Past orders"
TXT_NEW_ORDER_STATUS = "Placed"          # status of an order placed in this session (the placeholder one says "Delivered")
TXT_ONE_TAP_ORDER = "Re-order"           # the orange button beside each order (shown when "Display one-tap re-order button" is ON)
TXT_REFILL_TITLE = "Medicines that need refilling:"
TXT_REFILL_FOOTER = "These are based on your past orders."

# ---- Countdown card (pref: Countdown timers ...). Texts are placeholders. ----
TXT_COUNTDOWN_HEAD = "Flash sale ends soon!"
TXT_COUNTDOWN_SUB = "time left"
COUNTDOWN_START_SECONDS = 23 * 60 + 59     # shows 00:23:59 and counts down (format HH:MM:SS). 23 hours would be 23*3600.

# ---- Care plan (settings > care plan). Dates / texts are placeholders. ----
TXT_CARE_PLAN = "care plan"
# The user starts UNSUBSCRIBED. "Subscribe" starts it today and it runs for `months`.
CARE_PLAN = {
    "name": "Care plan",
    "price": "₹275 for 6 months",
    "months": 6,
    "renewal_charge": "₹275",
}

# ---- Insights (settings > insights): a calendar of what medicines were bought on which day. ----
# Classes and their colours (EDIT HERE). Every colour has dark text on it at 7:1 or better.
TXT_INSIGHTS = "insights"
MEDICINE_CLASSES = {            # class name: colour
    "Pain & fever": "#F6A65B",
    "Cold & cough": "#7DB8F5",
    "Stomach care": "#6FD0A0",
    "Vitamins": "#F2D14B",
}
# Which class each item belongs to (items not listed - sanitiser, thermometer - are not medicines, so they are not coloured).
MEDICINE_CLASS = {
    "paracetamol": "Pain & fever", "ibuprofen": "Pain & fever", "pain_gel": "Pain & fever",
    "cold_tablets": "Cold & cough", "cough_syrup": "Cold & cough", "nasal_drops": "Cold & cough",
    "antacid": "Stomach care", "ors": "Stomach care", "digestive_tablets": "Stomach care", "gas_drops": "Stomach care",
    "probiotic": "Stomach care",
    "vitamin_c": "Vitamins",
}

# ---- MOCK NuCoins balance (settings > nucoins). Placeholder numbers - EDIT HERE. ----
TXT_NUCOINS_PAGE = "NuCoins"
NUCOINS_START_BALANCE = 120
NUCOIN_VALUE = 0.5       # rupees per NuCoin (half a rupee)

# ---- Checkout maths -------------------------------------------------------------------------
HANDLING_FEE = 10
DELIVERY_FEE = 51
NUCOINS_FRACTION = 0.10  # the "NuCoins used" box takes off this share of the cart amount (items, before fees) - a placeholder
ROUND_UP_TO = 10         # the bill is rounded up to the next multiple of this (a maximum of Rs 10 is added)
QTY_OPTIONS = list(range(1, 11))     # what the quantity pills offer (not in Figma)


def rupees(n):
    """₹60 for whole amounts, ₹60.50 when there are paise (NuCoins are worth half a rupee)."""
    return f"₹{int(n)}" if float(n).is_integer() else f"₹{n:.2f}"


def pname(pid):
    return PRODUCTS[pid][0]


def pprice(pid):
    return PRODUCTS[pid][1]


def pref_price(pid):
    return rupees(round(pprice(pid) * REFERENCE_MARKUP))


TXT_HANDLING = "Handling charges"
TXT_ROUND_UP = "Round up donation"
TXT_NUCOINS = "NuCoins used"
TXT_DELIVERY = "Delivery fee"
TXT_TOTAL = "Total"
TXT_LEARNT = "What we’ve learnt from you:"
TXT_LEARNT_NOTE = [("If there’s anything here that you’d prefer not to share, ", None), ("change your preferences", "GO_PREFS")]

# ---- PLACEHOLDERS: not in the Figma, filled in only so the logic can be seen working.
#      Replace with your own text. ------------------------------------------------------
TXT_LOCATION_CURRENT = "Your current location"     # shown instead of "Enter delivery address" when "Use my location" is ON
TXT_ENTER_PHONE = "Enter phone number"            # replaces "Place order" until the phone number has been entered and verified
TXT_PLACE_ORDER = "Place order"                   # the bottom-bar button (same look as the old prototype's "Proceed to pay")
TXT_ORDER_PLACED = "Your order has been placed."   # pop-up after tapping it
TXT_EMPTY_CART = "Your cart is empty"           # shown on checkout when nothing has been added
ERROR_NO_SHARED_DATA = "No shared data to pick shortcuts from"   # error when "recommended" is tapped and no data is shared

# {pref} is replaced with the exact label of the preference that switched this on (see EXPLANATION_PREF below).
SEEN_BECAUSE = "You’re seeing this because you selected this preference: {pref}. You can change this in settings."
SEEN_BECAUSE_ORDERS = "You’re seeing this because of this preference: {pref}. Edit in settings."   # your note on the refill card

# =====================================================================
# EXPLANATIONS  <---- EDIT THE CONTENTS OF THE POP-UP BOXES HERE
# One entry per green-underlined phrase. "" = the box opens empty.
# =====================================================================
EXPLANATIONS = {
    # phone screen
    "bubble_this": "Additional information will show up in a box like this.",
    "phone_number": "Your phone number will be used to coordinate delivery.",
    # preferences screen - Data collection (your Figma note: "the underlined comments will explain why this data is required")
    "share_data": "This includes browsing and purchase history, inferred health conditions, time spent in the app, your approximate location, contents of prescriptions (medicine names, course duration and diagnoses).",
    "track_search": "This will be shared with advertising, analytics and AI model partners.",     # (you haven't written this one yet - it opens empty)
    "keep_rx": "The contents of your prescription (medicine names, course duration, diagnoses) will be stored and the image of the prescription will be deleted.",
    "share_rx": "The contents of your prescription (medicine names, course duration, diagnoses) will be shared with advertising, analytics and AI model partners.",
    "location": "Location access is used to determine your delivery point. This can also be entered manually.",
    "taps": "This will be shared with analytics partners.",
    # preferences screen - In-app behaviour
    "round_up": "A maximum of ₹10 will be rounded up to your bill to support local NGOs.",
    # preferences screen - Payments and subscriptions
    "reorder_button": "A button beside a past order that automatically adds the same things to your cart.",
    # product page
    "rx_required": "This medicine can only be bought with a valid prescription from a doctor. You can upload it at checkout.",     # (placeholder - edit)
    # checkout screen
    "handling_charges": "This covers the labour, processing and packing charges.",
    # the pop-up on every preference-driven item (your Figma comment + notes: "you're seeing this because you selected this preference. you can change this in settings")
    "picked_for_you": SEEN_BECAUSE,
    "frequently_bought": SEEN_BECAUSE,
    "low_stock": SEEN_BECAUSE,
    "acc_insights": SEEN_BECAUSE,
    "acc_nucoins": SEEN_BECAUSE,
    "refill_footer": SEEN_BECAUSE_ORDERS,
    "reference_price": SEEN_BECAUSE,       # product page: the struck-through reference price
    # your Figma note: "clicking this displays the ngo details" (no details given, so empty)
    "round_up_donation": SEEN_BECAUSE,   # checkout "Round up donation" row (your NGO-details note: still no details given)
    "nucoins_used": SEEN_BECAUSE,   # checkout "NuCoins used" row: names the preference that switched it on
}

# =====================================================================
# PREFERENCES  (labels copied word for word from the Figma)
# Each row: (key, [(text, term_key_or_None), ...])   term_key = green underline, opens EXPLANATIONS[term_key]
# =====================================================================
PREF_GROUPS = [
    ("Data collection", [
        ("share_data", [("Share my data", "share_data"), (" with advertising & marketing partners", None)]),
        ("track_search", [("Track what I search and browse", "track_search"), (" inside the app", None)]),
        ("infer_health", [("Use my purchases to infer health conditions", None)]),
        ("keep_rx", [("Keep my prescriptions", "keep_rx"), (" after my order is delivered", None)]),
        ("share_rx", [("Share my prescription", "share_rx"), (" with anyone beyond the pharmacist", None)]),
        ("location", [("Use my location", "location")]),
        ("train_models", [("Use my data to train recommendation or AI models", None)]),
        ("taps", [("Record my taps and scrolls", "taps")]),
    ]),
    ("Personalisation", [
        ("picked_for_you", [("Show “picked for you” recommendations based on my history", None)]),
        ("frequently_bought", [("Suggest “frequently bought together” items", None)]),
        ("reference_prices", [("Show deals and reference prices", None)]),
        ("refill_reminders", [("Send refill reminders based on my past orders", None)]),
        ("health_articles", [("Show health articles and tips based on my past orders", None)]),
    ]),
    ("Offers and marketing", [
        ("promo_push", [("Promotional push notifications", None)]),
        ("promo_sms", [("Promotional SMS", None)]),
        ("whatsapp", [("WhatsApp offers and promotions", None)]),
        ("marketing_email", [("Marketing emails and newsletters", None)]),
        ("flash_push", [("Flash-sale and limited time offer push notifications", None)]),
        ("cart_reminder", [("“You left something in your cart” reminders (push notifications)", None)]),
        ("nucoins_prompts", [("NuCoins and cashback prompts", None)]),
        ("rating_requests", [("Rating requests and feedback surveys", None)]),
    ]),
    ("In-app behaviour", [
        ("countdown", [("Countdown timers (for sales and limited-time offers) and “ends soon” messages", None)]),
        ("low_stock", [("Display when an item is low in stock/ selling fast", None)]),
        ("preselect_addons", [("Pre-select free add-ons", None)]),
        ("earn_spend_nucoins", [("Earn and spend NuCoins", None)]),
        ("round_up", [("Add ", None), ("round-up donations", "round_up"), (" to my bill", None)]),
    ]),
    ("Payments and subscriptions", [
        ("auto_renew", [("Automatically renew subscriptions", None)]),
        ("save_card", [("Save my card details", None)]),
        ("save_upi", [("Save my UPI ID", None)]),
        ("reorder_button", [("Display one-tap re-order button", "reorder_button")]),
    ]),
]
ALL_PREF_KEYS = [k for _, rows in PREF_GROUPS for k, _ in rows]
PREF_LABEL = {k: "".join(t for t, _ in parts) for _, rows in PREF_GROUPS for k, parts in rows}

# Nothing is pre-selected: the user opts IN. Flip any of these to True to test an output.
DEFAULT_PREFS = {k: False for k in ALL_PREF_KEYS}

# ---- Where each preference shows up in the flow (None = no place for it in the Figma yet) ----
PREF_PLACES = {
    "share_data": "checkout: 'What we've learnt from you' (+ home: shortcut source)",
    "infer_health": "checkout: 'What we've learnt'; accounts: 'insights' row and page (GUESS); home: shortcut source",
    "track_search": "checkout: 'What we've learnt from you' (+ home: shortcut source)",
    "keep_rx": "checkout: 'What we've learnt from you' (+ home: shortcut source)",
    "share_rx": "checkout: 'What we've learnt from you'",
    "location": "home: location pill; checkout: 'What we've learnt from you' (+ home: shortcut source)",
    "train_models": "checkout: 'What we've learnt from you'",
    "taps": "checkout: 'What we've learnt from you' (+ home: shortcut source)",
    "picked_for_you": "home: the 'Picked for you' section",
    "frequently_bought": "product page: the 'frequently bought together' section",
    "reference_prices": "home + product page: reference price next to every item price",
    "refill_reminders": "home: the refill card (items from the previous order and the days of supply left)",
    "low_stock": "product page: 'low stock'",
    "round_up": "checkout: 'Round up donation' row",
    "earn_spend_nucoins": "checkout: 'NuCoins used' row (spend); accounts: 'nucoins' row and page (GUESS). 'Earn' has no place yet",
    "reorder_button": "past orders: orange 're-order' button beside each order; home: 'One-tap re-order' shortcut",
    # --- no place for these in the Figma yet ---
    "health_articles": None, "promo_push": None, "promo_sms": None, "whatsapp": None,
    "marketing_email": None, "flash_push": None, "cart_reminder": None, "nucoins_prompts": None,
    "rating_requests": None, "preselect_addons": None,
    "countdown": "home: the countdown card",
    "save_card": "care plan page: 'Payment method' (once subscribed)", "save_upi": "care plan page: 'Payment method' (once subscribed)",
    # auto_renew: no place - the care plan's own Auto renew switch is separate from this preference
    "auto_renew": None,
}

# ---------------------------------------------------------------------------------------
# CHECKOUT: "What we've learnt from you:"      <---- EDIT THE WORDING OF THESE LINES HERE
# What the app could gather from the user during this flow. A preference's lines appear only
# when that preference is ON. {placeholders} are filled in from what the user actually did:
#   {time_spent}  time on the app this session      {features}  screens / features they used
#   {looked_at}   items whose page they opened      {bought}    what is in this purchase
#   {conditions}  health conditions inferred from what they bought (see PRODUCT_CONDITIONS)
#   {location}    their location (placeholder text, see TXT_LOCATION_CURRENT)
# ---------------------------------------------------------------------------------------
RECEIPT_KEYS = ["share_data", "track_search", "infer_health", "keep_rx",
                "share_rx", "location", "train_models", "taps"]
RECEIPT_LINES = {
    "share_data": ["Shared with advertising & marketing partners: everything listed here"],
    "track_search": ["What you looked at: {looked_at}"],
    "infer_health": ["What you bought: {bought}",
                     "Health conditions we inferred from it: {conditions}"],
    "location": ["Your location: {location}"],
    "train_models": ["Used to train recommendation and AI models: what you bought ({bought}) and what you looked at ({looked_at})"],
    "taps": ["Time spent on the app: {time_spent}",
             "Features you used: {features}"],
}
NOTHING = "nothing yet"
# placeholder inference used for {conditions} (made up - edit freely)
PRODUCT_CONDITIONS = {
    "cold_tablets": "cold", "cough_syrup": "cough", "paracetamol": "fever or pain", "vitamin_c": "low immunity",
    "antacid": "acidity", "ors": "dehydration", "thermometer": "fever",
    "nasal_drops": "blocked nose", "ibuprofen": "pain or fever", "pain_gel": "muscle pain",
    "digestive_tablets": "indigestion", "gas_drops": "gas", "probiotic": "gut health",
}
# names shown in {features} for each screen the user opens
SCREEN_FEATURES = {"home": "Home", "product": "Item page", "checkout": "Checkout", "accounts": "Settings",
                   "careplan": "Care plan", "prefs": "Customise your experience",
                   "insights": "Insights", "nucoins": "NuCoins", "pastorders": "Past orders", "prescription": "Prescription upload"}

# Home "recommended" chip: which shortcut each data preference produces (PROVISIONAL, not in Figma).
# Preferences not listed here don't produce a shortcut. If none of the listed ones is ON -> error message.
RECOMMEND_FROM = {
    "track_search": "Cold medicines",
    "taps": "Past orders",
    "infer_health": "Book a consult",
    "keep_rx": "Upload prescription",
}
# Everything the "+" dropdown (and a shortcut's "Change") offers. Edit / extend freely.
# Only these have a destination: One-tap re-order, Customise experience, Account management, Care plan, Past orders.
SHORTCUT_PREFS = "Customise experience"      # the shortcut that opens the preferences screen (short so it fits the pill)
SHORTCUT_CUSTOM = "Custom"                   # first in the list: lets the user turn any button on screen into a shortcut
SHORTCUT_OPTIONS = [SHORTCUT_CUSTOM, "One-tap re-order", SHORTCUT_PREFS, "Cold medicines", "Fever medicines", "Stomach care",
                    "Vitamins", "Skin care", "Upload prescription", "Book a consult", "Account management",
                    "Care plan", "Past orders"]
SHORTCUT_NEEDS_PREF = {"One-tap re-order": "reorder_button"}     # only offered when that preference is ON

# ---- "Custom" shortcut: the user double taps any button to turn it into a shortcut (texts are placeholders) ----
TXT_CUSTOM_PROMPT = "Double tap a button to make it a shortcut"      # the pop-up shown after choosing "Custom"
TXT_CUSTOM_CANCEL = "Cancel"                                         # the corner button while a custom shortcut is being made
TXT_RENAME = "Rename"                                                # in the three-dot menu of a custom shortcut
TXT_RENAME_TITLE = "Rename shortcut"
TXT_SAVE = "Save"
CUSTOM_PREFIX = "custom"                                             # new ones are called custom1, custom2 ... (lowest free number)
CUSTOM_NAME_MAX = 20                                                 # longest name accepted when renaming
DOUBLE_TAP_SECONDS = 0.5                                             # two taps on the same button within this time = a double tap

# Which preference each of those pop-ups names (explanation key -> preference key). Change a pairing here.
EXPLANATION_PREF = {
    "picked_for_you": "picked_for_you",
    "frequently_bought": "frequently_bought",
    "low_stock": "low_stock",
    "acc_insights": "infer_health",     # GUESS (also see ACCOUNT_ROWS)
    "acc_nucoins": "earn_spend_nucoins",             # GUESS (also see ACCOUNT_ROWS)
    "refill_footer": "refill_reminders",
    "nucoins_used": "earn_spend_nucoins",
    "round_up_donation": "round_up",
    "reference_price": "reference_prices",
}

FIELD_H = 44                          # height of the phone / OTP boxes (the text field draws the box itself)
PHONE_RE = re.compile(r"^\d{10}$")    # a valid number = any 10 digits
OTP_RE = re.compile(r"^\d{4}$")       # a valid OTP = any 4 digits

# =====================================================================
# HELPERS
# =====================================================================

def outlined_field(height=None, **kw):
    """A TextField that draws its OWN outline (rounded, grey) and fills a box `height` tall with the text centred in it, so the box and the
    text can't end up out of step with each other. Settings this Flet version doesn't have are left out instead of crashing."""
    border = getattr(ft, "InputBorder", None)
    opts = dict(dense=True, height=height, text_size=14, color=C_TEXT, cursor_color=C_TEXT, bgcolor=C_WHITE, filled=True,
                content_padding=pad_xy(12, 0), text_vertical_align=0,
                border=border.OUTLINE if border else None, border_radius=BTN_RADIUS, border_color=C_GREY, border_width=1,
                focused_border_color=C_PRIMARY_DARK, focused_border_width=2)
    opts.update(kw)
    opts = {k: v for k, v in opts.items() if v is not None}
    try:
        params = inspect.signature(ft.TextField).parameters
        if not any(p.kind is p.VAR_KEYWORD for p in params.values()):
            opts = {k: v for k, v in opts.items() if k in params}
    except (TypeError, ValueError):
        pass
    return ft.TextField(**opts)


def pad(left=0, top=0, right=0, bottom=0):
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def pad_xy(x=0, y=0):
    return pad(x, y, x, y)


def border_all(width, color):
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


CENTER = ft.Alignment(0, 0)
W = {400: ft.FontWeight.W_400, 500: ft.FontWeight.W_500, 600: ft.FontWeight.W_600, 700: ft.FontWeight.W_700, 800: ft.FontWeight.W_800}


def txt(value, size, weight=400, color=C_TEXT, **kw):
    return ft.Text(value, size=size, weight=W[weight], color=color, font_family=FONT, **kw)


def style(size, weight=400, color=C_TEXT, **kw):
    return ft.TextStyle(size=size, weight=W[weight], color=color, font_family=FONT, **kw)


WEB_IMAGES = "https://yoyocoded.github.io/6mg/images/"   # where the pictures are hosted online


def find_image(pid):
    """The file to show for an item: a web address as given, the hosted copy when running in the browser,
    otherwise the exact name from PRODUCT_IMAGES if that file is in the assets folder, else None (grey square)."""
    src = PRODUCT_IMAGES.get(pid) or ""
    if not src:
        return None
    if src.startswith(("http://", "https://")):
        return src
    local = os.path.join(ASSETS_DIR, src)
    return src if os.path.isfile(local) else WEB_IMAGES + src


def item_image(pid, size, radius, on_click=None):
    """The picture square for an item: its picture from PRODUCT_IMAGES (cropped to fill), or the grey placeholder if there isn't one."""
    src = find_image(pid)
    fit = getattr(ft, "BoxFit", None) or getattr(ft, "ImageFit", None)          # renamed in newer Flet
    picture = ft.Image(src=src, width=size, height=size, fit=fit.COVER) if src and fit else None
    return ft.Container(width=size, height=size, border_radius=radius, bgcolor=C_SLOT, on_click=on_click,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=picture)


def strike(value, size, color):
    return ft.Text(spans=[ft.TextSpan(value, style=ft.TextStyle(
        size=size, color=color, font_family=FONT, decoration=ft.TextDecoration.LINE_THROUGH))])


def struck_term(label, key, size, color):
    """A struck-through price that also has the green wavy underline and opens EXPLANATIONS[key] when tapped.
    One text decoration can't be both a straight strike and a wavy green line, so two identical texts are layered:
    the lower one is struck through; the upper one is see-through, carries the wavy underline and the tap."""
    lower = strike(label, size, color)
    upper = ft.Text(spans=[term_span(label, key, size, 400, TRANSPARENT)], size=size, font_family=FONT)
    return ft.Stack(controls=[lower, upper])


def show_dialog(page, dlg):
    if hasattr(page, "show_dialog"):
        page.show_dialog(dlg)
    else:
        page.open(dlg)


def close_dialog(page, dlg):
    if hasattr(page, "pop_dialog"):
        page.pop_dialog()
    else:
        page.close(dlg)


def green_dialog(content, actions=None, modal=False):
    """Every pop-up box uses this: same mint fill, green outline and rounded corners as the phone-screen bubble."""
    rr = getattr(ft, "RoundedRectangleBorder", None)
    extra = {"shape": rr(radius=28, side=ft.BorderSide(1, C_MINT_LINE))} if rr else {}
    return ft.AlertDialog(bgcolor=C_MINT, content_padding=pad(24, 20, 24, 20),
                          content=content, actions=actions, modal=modal, **extra)


def message_box(text):
    """Small pop-up used for the shortcut error."""
    page = App.page
    dlg = green_dialog(
        txt(text, 13, 500, C_TEXT),
        actions=[ft.Container(padding=pad_xy(12, 8), on_click=lambda _: close_dialog(page, dlg),
                              content=txt("OK", 13, 600, C_PRIMARY_DARK))])
    show_dialog(page, dlg)


INFO_ICON = getattr(ft.Icons, "INFO_OUTLINE", None) or ft.Icons.INFO


# ---- green-underlined words ---------------------------------------------------------
def explanation_text(key):
    """EXPLANATIONS[key], with {pref} replaced by the label of the preference that causes this item to show."""
    text = EXPLANATIONS.get(key, "")
    pref = EXPLANATION_PREF.get(key)
    if pref and "{pref}" in text:
        text = text.replace("{pref}", PREF_LABEL[pref])
    return text


def explanation_body(key):
    """The pop-up text. When it names the preference that switched the item on, that preference's label is in bold."""
    text = EXPLANATIONS.get(key, "")
    pref = EXPLANATION_PREF.get(key)
    if pref and "{pref}" in text:
        before, after = text.split("{pref}", 1)
        spans = [ft.TextSpan(before, style=style(13, 500, C_TEXT)),
                 ft.TextSpan(PREF_LABEL[pref], style=style(13, 700, C_TEXT)),
                 ft.TextSpan(after, style=style(13, 500, C_TEXT))]
        return ft.Text(spans=spans, size=13, font_family=FONT)
    return txt(text, 13, 500, C_TEXT)


def open_explanation(key):
    """The little box. Its contents come from EXPLANATIONS[key] (empty string = empty box).
    It is a pop-up over the same page - it never navigates anywhere. Tap outside it to close."""
    page = App.page
    log_feature("Learn-more pop-ups")
    dlg = green_dialog(ft.Container(width=240, content=explanation_body(key),
                                    height=None if EXPLANATIONS.get(key) else 90))
    show_dialog(page, dlg)


UNDERLINE_THICKNESS = 1        # the green wavy underline: bigger = taller, bolder waves (1 is the thin default)


def term_span(label, key, size, weight=400, color=C_TEXT):
    """One underlined, tappable piece of text. `key` = an EXPLANATIONS key (opens the pop-up) or a function (called instead, e.g. to go to another screen)."""
    ul = getattr(ft, "TextDecorationStyle", None)
    extra = {"decoration_style": ul.WAVY} if ul is not None and hasattr(ul, "WAVY") else {}
    extra["decoration_thickness"] = UNDERLINE_THICKNESS
    return ft.TextSpan(
        label,
        style=style(size, weight, color, decoration=ft.TextDecoration.UNDERLINE,
                    decoration_color=C_UNDERLINE, **extra),
        on_click=(lambda e, k=key: k()) if callable(key) else (lambda e, k=key: open_explanation(k)))


def rich(parts, size, weight=400, color=C_TEXT, **kw):
    """parts = [(text, term_key_or_None), ...] -> one Text. Underlined parts open their box when tapped."""
    spans = [term_span(t, k, size, weight, color) if k else ft.TextSpan(t, style=style(size, weight, color))
             for t, k in parts]
    return ft.Text(spans=spans, size=size, font_family=FONT, **kw)


# ---- absolute positioning (the Figma frames are 360 x 800) --------------------------
def at(control, left, top, width=None, height=None):
    return ft.Container(content=control, left=left, top=top, width=width, height=height)


BOTTOM_BAR_H = 68


def frame(*controls, height=WINDOW_H, bottom=None, bg=C_WHITE):
    """A 360-wide screen. If height > 800 the screen scrolls. `bottom` = a bar fixed to the bottom edge. `bg` = the page colour."""
    view_h = WINDOW_H - (BOTTOM_BAR_H if bottom is not None else 0)
    stack = ft.Stack(width=WINDOW_W, height=height, controls=list(controls))
    if height <= view_h:
        body = ft.Container(width=WINDOW_W, height=view_h, bgcolor=bg, content=stack)
    else:
        body = ft.Container(width=WINDOW_W, height=view_h, bgcolor=bg,
                            content=ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO,
                                              controls=[ft.Container(width=WINDOW_W, height=height, content=stack)]))
    if bottom is None:
        return body
    return ft.Container(width=WINDOW_W, height=WINDOW_H, bgcolor=bg,
                        content=ft.Column(spacing=0, controls=[body, bottom]))


def style_button(btn, enabled, primary, label):
    """The one button look used everywhere (Continue, Skip, Subscribe ...): solid coral for the main action, white with a coral
    outline for the second one, grey when it can't be used yet. The label colours all reach 4.5:1 or better."""
    if not enabled:
        btn.bgcolor, btn.border, colour = C_DISABLED_BG, border_all(1, C_DISABLED_LINE), C_GREY
    elif primary:
        btn.bgcolor, btn.border, colour = C_PRIMARY_DARK, border_all(1, C_PRIMARY_DARK), C_WHITE
    else:
        btn.bgcolor, btn.border, colour = C_WHITE, border_all(1, C_PRIMARY_DARK), C_PRIMARY_DARK
    btn.content = button_label(label, colour)


def button_label(label, colour):
    """The text inside a button, centred. A label with a line break ("Skip\n(you'll be able to ...)") gets a bold first line and a
    smaller second line."""
    first, *rest = label.split("\n")
    top = txt(first, 14, 700, colour, text_align=ft.TextAlign.CENTER)
    if not rest:
        return top
    return ft.Column(tight=True, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER,
                     controls=[top, *[txt(line, 12, 500, colour, text_align=ft.TextAlign.CENTER) for line in rest]])


def pill_button(label, on_click=None, enabled=True, width=231, height=None, primary=True):
    """A button. The height grows with the label: 44 for one line, 17 more for every extra line."""
    lines = label.count("\n") + 1
    height = height or (44 if lines == 1 else 41 + 17 * (lines - 1))
    btn = ft.Container(width=width, height=height, border_radius=BTN_RADIUS, alignment=CENTER,
                       on_click=on_click if enabled else None, content=txt(label, 14, 700))
    style_button(btn, enabled, primary, label)
    return btn


def cart_count():
    """Number on the cart badge = total quantity in the cart."""
    return sum(State.cart.values())


def qty_pill(pid, width=None, height=24):
    """The little '1 v' selector for an item in the cart (coral outline, like 1mg's quantity control). Tap it to pick a quantity."""
    page = App.page
    cur = State.cart.get(pid, 1)

    def choose(n):
        def handler(e):
            log_feature("Quantity selector")
            State.cart[pid] = n
            close_dialog(page, dlg)
            navigate(App.current)
        return handler

    options = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, height=240, controls=[
        ft.Container(padding=pad_xy(16, 10), on_click=choose(n),
                     content=txt(str(n), 14, 600 if n == cur else 400,
                                 C_PRIMARY_DARK if n == cur else C_TEXT))
        for n in QTY_OPTIONS])
    dlg = green_dialog(ft.Container(width=120, content=options))

    return ft.Container(
        height=height, width=width, padding=None if width else pad_xy(8, 0), border_radius=BTN_RADIUS,
        border=border_all(1, C_PRIMARY_DARK), bgcolor=C_PEACH, alignment=CENTER,
        on_click=lambda e: show_dialog(page, dlg),
        content=ft.Row(spacing=0, tight=True, alignment=ft.MainAxisAlignment.CENTER,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            txt(str(cur), 12, 700, C_PRIMARY_DARK), ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=16, color=C_PRIMARY_DARK)]))


def add_to_cart(pid):
    """Only ever called from a tap by the user."""
    log_feature("Add to cart")
    State.cart[pid] = 1
    navigate(App.current)


def cart_control(pid, width, height=26):
    """'Add to cart' button (white, coral outline, like 1mg's ADD) until the item is in the cart, then its quantity pill."""
    if pid in State.cart:
        return ft.Container(width=width, height=height, alignment=CENTER, content=qty_pill(pid, width, height))
    return ft.Container(width=width, height=height, border_radius=BTN_RADIUS, bgcolor=C_WHITE, alignment=CENTER,
                        border=border_all(1, C_PRIMARY_DARK), on_click=lambda e: add_to_cart(pid),
                        content=txt(TXT_ADD_TO_CART_SMALL, 11, 700, C_PRIMARY_DARK))


def open_product(pid):
    if pid not in State.viewed:
        State.viewed.append(pid)
    if App.current == "product" and State.selected != pid:
        State.product_trail.append(State.selected)         # opened from another item's page: remember it for Back
    elif App.current != "product":
        State.product_trail.clear()
    State.selected = pid
    navigate("product")


def product_back():
    """Back on a product page: the item you came from, or home if you came from home."""
    if State.product_trail:
        State.selected = State.product_trail.pop()
        navigate("product")
    else:
        navigate("home")


def item_card(pid, x, y):
    """One item card, drawn like a 1mg product tile: white card, thin outline, picture, name, price, coral-outlined button.
    (x, y) is the card's top-left corner. Tapping the card (but not its button) opens the product page."""
    go = lambda e: open_product(pid)
    price_row = [txt(rupees(pprice(pid)), 13, 700)]
    if State.prefs["reference_prices"]:
        price_row.append(strike(pref_price(pid), 12, C_GREY))
    return [
        at(ft.Container(width=CARD_W, height=CARD_H, border_radius=RADIUS, bgcolor=C_WHITE,
                        border=border_all(1, C_BORDER), on_click=go), x, y),
        at(item_image(pid, 71, 8, go), x + (CARD_W - 71) / 2, y + 10),
        at(ft.Container(width=CARD_W - 8, height=32, alignment=CENTER, on_click=go,         # room for a two-line name
                        content=txt(pname(pid), 12, 600, text_align=ft.TextAlign.CENTER)), x + 4, y + 86),
        at(ft.Container(width=CARD_W - 8, height=20, alignment=CENTER, on_click=go,
                        content=ft.Row(spacing=4, tight=True, alignment=ft.MainAxisAlignment.CENTER, controls=price_row)),
           x + 4, y + 120),
        at(cart_control(pid, CARD_W - 24), x + 12, y + 144)]


def icon(*names):
    """The first icon name that exists in this version of Flet (so one missing name can't crash the app)."""
    for n in names:
        found = getattr(ft.Icons, n, None)
        if found:
            return found
    return ft.Icons.CIRCLE


def back_button(target, left=8, top=8, on_click=None):
    """1mg's back arrow: a plain arrow in the top bar (no circle)."""
    return round_button(ft.Icons.ARROW_BACK, left, top, on_click=on_click or (lambda e: navigate(target)))


def round_button(icon_name, left, top, on_click=None):
    """A plain 40 x 40 icon button, no outline (1mg's top-bar icons)."""
    return at(ft.Container(width=40, height=40, border_radius=20, alignment=CENTER, on_click=on_click,
                           content=ft.Icon(icon_name, size=24, color=C_TEXT)), left, top)


def app_bar(title=None, key=None):
    """The white bar at the top of every inner screen: a thin divider under it, the title (if any) beside the back arrow."""
    out = [at(ft.Container(width=WINDOW_W, height=56, bgcolor=C_WHITE, border=ft.Border(bottom=ft.BorderSide(1, C_DIVIDER))), 0, 0)]
    if title:
        out.append(at(rich([(title, key)], 18, 700) if key else txt(title, 18, 700), 56, 16))
    return out


def cart_button(left, top):
    """Cart icon with a number badge (coral circle, top right) once something is in the cart."""
    n = cart_count()
    btn = ft.Container(width=40, height=40, border_radius=20, alignment=CENTER, left=0, bottom=0,
                       content=ft.Icon(icon("SHOPPING_CART_OUTLINED", "SHOPPING_BAG_OUTLINED"), size=24, color=C_TEXT))
    controls = [btn]
    if n > 0:
        controls.append(ft.Container(width=18, height=18, border_radius=9, bgcolor=C_BADGE, alignment=CENTER,
                                     right=0, top=0, content=txt(str(n) if n < 100 else "99+", 10, 700, C_WHITE)))
    return at(ft.Container(width=44, height=44, on_click=lambda e: navigate("checkout"),
                           content=ft.Stack(width=44, height=44, controls=controls)), left, top - 4)


# =====================================================================
# STATE / APP
# =====================================================================

class State:
    prefs = dict(DEFAULT_PREFS)
    phone = ""
    phone_verified = False                  # true once a phone number and its OTP have been entered
    phone_from = "start"                    # "start" (first screens) or "checkout" (asked for at the Place order button)
    otp = ""
    shortcuts = [None, None, None, None]    # the 4 shortcut boxes; each empty one has its own "+", filled in any order
    open_groups = {name: True for name, _ in PREF_GROUPS}
    custom_slot = None                      # the shortcut slot being filled by "Custom" (None = not making one)
    cart = {}                               # item id -> quantity. Items go in ONLY when the user taps something.
    selected = HOME_ROW[0]                  # item shown on the product page
    product_trail = []                      # items opened before this one (from "frequently bought together"), for Back
    care_hidden = False                     # "hide for 7 days" tapped
    care_subscribed = False                 # the user starts unsubscribed from the care plan
    care_started = None                     # date the subscription started (set when they subscribe)
    care_cancelled = False                  # care plan cancelled in settings (still active until the end date)
    care_auto_renew = False                 # the care plan's own auto-renew switch: Off until the user turns it on there
    careplan_from = "accounts"               # where the care plan page was opened from (its back button returns there)
    roundup_checked = False                 # checkout boxes: unticked until the user ticks them
    nucoins_checked = False
    nucoins_balance = NUCOINS_START_BALANCE   # mock balance; goes down when an order is placed with NuCoins ticked
    viewed = []                             # items whose page was opened, in order (for {looked_at})
    features = []                           # features used, in order of first use (for {features})
    started = time.time()                   # when the session began (for {time_spent})
    rx_uploaded = False                     # the fake prescription has been uploaded (Done tapped on the prescription screen)
    rx_redacted = False                     # "Auto" has put the black bars on it
    prefs_from = "phone"                    # where the preferences screen was opened from (back / Continue return there)


class App:
    countdown_label = None
    page = None
    root = None
    current = "phone"


# =====================================================================
# SCREENS
# =====================================================================

def submit_phone():
    """Continue on the phone screen -> OTP screen."""
    State.otp = ""
    navigate("otp")


def skip_phone():
    """Skip on the phone screen: on the first run go on to preferences; from checkout just go back (the button stays 'Enter phone number')."""
    if State.phone_from == "checkout":
        State.phone_from = "start"
        navigate("checkout")
    else:
        first_prefs()


def verify_otp():
    """Continue on the OTP screen: any 4 digits. First run -> preferences; from checkout -> back to the checkout."""
    State.phone_verified = True
    if State.phone_from == "checkout":
        State.phone_from = "start"
        navigate("checkout")
    else:
        first_prefs()


def ask_phone():
    """The 'Enter phone number' button on checkout: phone screen -> OTP screen -> back to the checkout."""
    State.phone_from = "checkout"
    navigate("phone")


def first_prefs():
    """First visit: phone screen -> preferences."""
    State.prefs_from = "phone"
    navigate("prefs")


def open_prefs():
    """Open the (already filled-in) preferences list from settings / a shortcut. Back / Continue return to where you came from."""
    State.prefs_from = App.current
    navigate("prefs")


def leave_prefs(continuing):
    if continuing and State.prefs_from == "phone":
        navigate("home")
    else:
        navigate(State.prefs_from)


def phone_screen():
    refs = {}

    def valid():
        return bool(PHONE_RE.match(State.phone))

    def restyle():
        btn = refs["continue"]
        ok = valid()
        style_button(btn, ok, True, TXT_CONTINUE)
        btn.on_click = (lambda e: submit_phone()) if ok else None
        btn.update()

    def changed(e):
        State.phone = "".join(ch for ch in (e.control.value or "") if ch.isdigit())[:10]
        if e.control.value != State.phone:          # drop non-digits / anything past 10 digits
            e.control.value = State.phone
            e.control.update()
        restyle()

    flt = getattr(ft, "NumbersOnlyInputFilter", None)
    field = outlined_field(
        FIELD_H, value=State.phone, on_change=changed, keyboard_type=getattr(ft, "KeyboardType", None) and ft.KeyboardType.NUMBER,
        input_filter=flt() if flt else None)
    refs["continue"] = pill_button(TXT_CONTINUE, (lambda e: submit_phone()) if valid() else None, valid(), width=308)

    bubble = ft.Container(          # one line: as wide as the 12px margins allow, same right edge as before
        width=324, height=40, border_radius=20, bgcolor=C_MINT, border=border_all(1, C_MINT_LINE),
        padding=pad_xy(12, 0), alignment=CENTER,
        content=ft.Text(spans=[ft.TextSpan(TXT_BUBBLE_1, style=style(11)),
                               term_span(TXT_BUBBLE_TERM, "bubble_this", 11),
                               ft.TextSpan(TXT_BUBBLE_2, style=style(11))],
                        font_family=FONT, text_align=ft.TextAlign.CENTER, no_wrap=True))
    return frame(
        at(bubble, 24, 74),
        at(ft.Icon(INFO_ICON, size=15, color=C_INFO), 320, 51),
        at(rich([(TXT_PHONE_TITLE_1, None), (TXT_PHONE_TITLE_TERM, "phone_number")], 18, 700), 26, 248),
        at(ft.Container(width=308, height=175, border_radius=RADIUS, border=border_all(1, C_BORDER)), 26, 312),
        at(txt(TXT_COUNTRY, 14, 600), 43, 392),
        at(ft.Container(width=233, height=FIELD_H, content=field), 83, 378),
        at(refs["continue"], 26, 549),
        at(pill_button(TXT_SKIP, lambda e: skip_phone(), width=308, primary=False), 26, 605),
        *([*app_bar(), back_button("checkout")] if State.phone_from == "checkout" else []))


def otp_screen():
    """4-digit OTP, laid out like the phone screen. Continue is enabled once 4 digits are typed."""
    refs = {}

    def restyle():
        btn = refs["continue"]
        ok = bool(OTP_RE.match(State.otp))
        style_button(btn, ok, True, TXT_CONTINUE)
        btn.on_click = (lambda e: verify_otp()) if ok else None
        btn.update()

    def changed(e):
        State.otp = "".join(ch for ch in (e.control.value or "") if ch.isdigit())[:4]
        if e.control.value != State.otp:
            e.control.value = State.otp
            e.control.update()
        restyle()

    flt = getattr(ft, "NumbersOnlyInputFilter", None)
    field = outlined_field(
        FIELD_H, value=State.otp, on_change=changed, hint_text=TXT_OTP_HINT, hint_style=style(14, 400, C_GREY),
        keyboard_type=getattr(ft, "KeyboardType", None) and ft.KeyboardType.NUMBER, text_align=ft.TextAlign.CENTER,
        input_filter=flt() if flt else None)
    refs["continue"] = pill_button(TXT_CONTINUE, (lambda e: verify_otp()) if OTP_RE.match(State.otp) else None, bool(OTP_RE.match(State.otp)), width=308)
    return frame(
        *app_bar(), back_button("phone"),
        at(txt(TXT_OTP_TITLE, 18, 700), 26, 248),
        at(txt(TXT_OTP_SUB.format(phone=State.phone), 12, 500, C_GREY), 26, 280, 308),
        at(ft.Container(width=308, height=130, border_radius=RADIUS, border=border_all(1, C_BORDER)), 26, 312),
        at(ft.Container(width=233, height=FIELD_H, content=field), 63, 355),
        at(refs["continue"], 26, 480))


def pref_row(key, parts):
    def toggled(e):
        State.prefs[key] = e.control.value

    cb = ft.Checkbox(value=State.prefs[key], active_color=C_PRIMARY_DARK, check_color=C_WHITE, on_change=toggled)
    return ft.Row(spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
        ft.Container(width=30, content=cb),
        ft.Container(expand=True, content=rich(parts, 12, 500))])


def prefs_screen():
    def group(name, rows):
        body = ft.Column(spacing=0, visible=State.open_groups[name],
                         controls=[pref_row(k, p) for k, p in rows])

        def toggle(e):
            State.open_groups[name] = not State.open_groups[name]
            body.visible = State.open_groups[name]
            arrow.name = ft.Icons.ARROW_DROP_DOWN if State.open_groups[name] else ft.Icons.ARROW_RIGHT
            arrow.update()
            body.update()

        arrow = ft.Icon(ft.Icons.ARROW_DROP_DOWN if State.open_groups[name] else ft.Icons.ARROW_RIGHT,
                        size=24, color=C_TEXT)
        header = ft.Container(on_click=toggle, content=ft.Row(spacing=0, controls=[
            txt(name, 16, 700), arrow]))
        return ft.Column(spacing=6, controls=[header, body])

    required = ft.Column(spacing=2, controls=[
        ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.START,
               controls=[txt("•", 12, 500), ft.Container(expand=True, content=txt(t, 12, 500))])
        for t in REQUIRED_ITEMS])

    box = ft.Container(
        margin=pad(26, 28, 26, 20), padding=pad(13, 24, 13, 30), border_radius=RADIUS,
        border=border_all(1, C_BORDER),
        content=ft.Column(spacing=20, controls=[
            txt(TXT_REQUIRED_TITLE, 16, 700), required,
            *[group(n, r) for n, r in PREF_GROUPS],
            ft.Row(alignment=ft.MainAxisAlignment.CENTER,
                   controls=[pill_button(TXT_CONTINUE, lambda e: leave_prefs(True))])]))
    return ft.Container(
        width=WINDOW_W, height=WINDOW_H, bgcolor=C_WHITE,
        content=ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, controls=[
            ft.Container(height=56, padding=pad(8, 0, 0, 0), border=ft.Border(bottom=ft.BorderSide(1, C_DIVIDER)),
                         content=ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(width=40, height=40, border_radius=20, alignment=CENTER, on_click=lambda e: leave_prefs(False),
                             content=ft.Icon(ft.Icons.ARROW_BACK, size=24, color=C_TEXT)),
                txt(TXT_PREFS_TITLE, 18, 700)])),
            ft.Container(padding=pad(26, 8, 26, 0), content=txt(TXT_PREFS_NOTE, 15, 700, C_RED)),
            box]))


# ---- shortcuts ---------------------------------------------------------------------
def shortcut_options(slot):
    """What the '+' dropdown / 'Change' offers for this slot: everything not already used in another slot ("Custom" is always offered)."""
    used = {str(n) for i, n in enumerate(State.shortcuts) if n and i != slot}
    out = []
    for o in SHORTCUT_OPTIONS:
        need = SHORTCUT_NEEDS_PREF.get(o)
        if (o in used and o != SHORTCUT_CUSTOM) or (need and not State.prefs[need]):
            continue
        out.append(o)
    return out


class Custom(str):
    """The name of a custom shortcut. It is a string (so it is shown and compared like any other shortcut name) that also
    remembers what tapping it does: `action` is the button's own on_click, captured when it was double tapped."""
    def __new__(cls, name, action=None):
        obj = super().__new__(cls, name)
        obj.action = action
        return obj


class _Tap:
    """Stands in for the click event when a custom shortcut runs a button's handler."""
    control = None
    data = None


def next_custom_name(slot):
    taken = {str(n) for i, n in enumerate(State.shortcuts) if n and i != slot}
    i = 1
    while f"{CUSTOM_PREFIX}{i}" in taken:
        i += 1
    return f"{CUSTOM_PREFIX}{i}"


def make_custom_shortcut(action):
    """A button was double tapped: it becomes the shortcut in the waiting slot, then we go home to show it."""
    slot = State.custom_slot
    if slot is None:
        return
    log_feature("Shortcuts")
    State.shortcuts[slot] = Custom(next_custom_name(slot), lambda: action(_Tap()))
    State.custom_slot = None
    navigate("home")


def custom_tap(original):
    """Replaces a button's on_click while a custom shortcut is being made: one tap does nothing, a second tap within
    DOUBLE_TAP_SECONDS on the same button makes it the shortcut."""
    last = [None]

    def tap(e):
        now = time.monotonic()
        if last[0] is not None and now - last[0] <= DOUBLE_TAP_SECONDS:
            last[0] = None
            make_custom_shortcut(original)
        else:
            last[0] = now
    return tap


def arm_custom(control):
    """Walks a freshly built screen and makes every button (anything with an on_click) wait for a double tap.
    The shortcut pills themselves (marked NO_CUSTOM) are left alone."""
    if not isinstance(control, ft.Control):
        return
    if getattr(control, "on_click", None) and getattr(control, "data", None) != NO_CUSTOM:
        control.on_click = custom_tap(control.on_click)
    arm_custom(getattr(control, "content", None))
    for child in (getattr(control, "controls", None) or []):
        arm_custom(child)


def custom_cancel_button():
    """The corner button shown while a custom shortcut is being made (bottom right, above the checkout bar's height)."""
    return ft.Container(right=12, bottom=BOTTOM_BAR_H + 16, height=40, padding=pad_xy(20, 0), border_radius=BTN_RADIUS,
                        bgcolor=C_TEXT, alignment=CENTER, on_click=lambda e: cancel_custom(),
                        content=txt(TXT_CUSTOM_CANCEL, 14, 700, C_WHITE))


def start_custom(slot):
    """"Custom" was picked: show the prompt; the screen now waits for a double tap (see navigate)."""
    State.custom_slot = slot
    navigate("home")
    message_box(TXT_CUSTOM_PROMPT)


def cancel_custom():
    State.custom_slot = None
    navigate(App.current)


def choose_shortcut(slot):
    """The dropdown menu: a list of shortcuts to pick from."""
    page = App.page

    def pick(name):
        def handler(e):
            log_feature("Shortcuts")
            close_dialog(page, dlg)
            if name == SHORTCUT_CUSTOM:
                start_custom(slot)
                return
            State.shortcuts[slot] = name
            navigate("home")
        return handler

    options = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, height=260, controls=[
        ft.Container(padding=pad_xy(12, 10), on_click=pick(o), content=txt(o, 14, 500, C_TEXT))
        for o in shortcut_options(slot)])
    dlg = green_dialog(ft.Container(width=220, content=options))
    show_dialog(page, dlg)





def rename_shortcut(slot):
    """Rename a custom shortcut (an empty name keeps the old one)."""
    page = App.page
    current = State.shortcuts[slot]

    def save(e=None):
        new = (field.value or "").strip()[:CUSTOM_NAME_MAX]
        if new:
            log_feature("Shortcuts")
            State.shortcuts[slot] = Custom(new, current.action)
        close_dialog(page, dlg)
        navigate("home")

    field = outlined_field(value=str(current), autofocus=True, max_length=CUSTOM_NAME_MAX, on_submit=save)
    dlg = green_dialog(
        ft.Container(width=220, content=ft.Column(tight=True, spacing=12, controls=[txt(TXT_RENAME_TITLE, 14, 700), field])),
        actions=[ft.Container(padding=pad_xy(12, 8), on_click=lambda e: close_dialog(page, dlg), content=txt(TXT_CUSTOM_CANCEL, 13, 600, C_GREY)),
                 ft.Container(padding=pad_xy(12, 8), on_click=save, content=txt(TXT_SAVE, 13, 700, C_PRIMARY_DARK))])
    show_dialog(page, dlg)


def shortcut_menu(slot):
    """The three-dot menu on a shortcut: rename (custom ones only), change or delete it."""
    page = App.page

    def rename(e):
        close_dialog(page, dlg)
        rename_shortcut(slot)

    def change(e):
        close_dialog(page, dlg)
        choose_shortcut(slot)

    def delete(e):
        log_feature("Shortcuts")
        State.shortcuts[slot] = None
        close_dialog(page, dlg)
        navigate("home")

    row = lambda label, handler: ft.Container(width=160, padding=pad_xy(12, 10), on_click=handler, content=txt(label, 14, 500, C_TEXT))
    rows = [row(TXT_RENAME, rename)] if isinstance(State.shortcuts[slot], Custom) else []
    dlg = green_dialog(ft.Column(tight=True, spacing=0, controls=[*rows, row("Change", change), row("Delete", delete)]))
    show_dialog(page, dlg)


def reorder(order, then):
    """One-tap order: puts the items of that order in the cart, with the same quantities (only when the user taps it).
    then = the screen to show afterwards ("checkout" from past orders, so the cart can be seen)."""
    log_feature("Re-order")
    for pid, qty in order["items"].items():
        State.cart.setdefault(pid, qty)
    navigate(then)


def reorder_previous():
    """The 'One-tap re-order' shortcut: re-orders the latest order, staying on the same screen (the cart badge updates)."""
    reorder(PAST_ORDERS[-1], App.current)


def run_shortcut(name):
    if isinstance(name, Custom):                       # a button the user turned into a shortcut: do what that button does
        if name.action:
            name.action()
        return
    if name == "One-tap re-order":
        reorder_previous()
    elif name == SHORTCUT_PREFS:
        open_prefs()
    elif name == "Account management":
        navigate("accounts")
    elif name == "Care plan":
        open_care_plan()
    elif name == "Past orders":
        navigate("pastorders")
    # the other shortcuts have no destination screen yet


def pick_shortcuts():
    """The 'recommended' chip: fills the slots from the data the user has opted to share."""
    log_feature("Recommended shortcuts")
    picks = []
    for key, label in RECOMMEND_FROM.items():
        need = SHORTCUT_NEEDS_PREF.get(label)
        if State.prefs.get(key) and label not in picks and not (need and not State.prefs[need]):
            picks.append(label)
    if not picks:
        message_box(ERROR_NO_SHARED_DATA)
        return
    picks = picks[:SLOT_COUNT]
    State.shortcuts = picks + [None] * (SLOT_COUNT - len(picks))
    navigate("home")


CARDS_DY, SECTION_PITCH = 34, 236                  # a section: heading, cards 34px below it, next section 236px after
CARD_W, CARD_H = 104, 178                          # one item card (a 1mg-style white tile)
ITEM_X = (12, 128, 244)                            # left edges of the three cards: 12px margins, 12px gaps

# The four pills (the "+" and the three shortcuts) are spaced evenly with the same 12px margin as the rest of the page.
SLOT_W, SLOT_H, SLOT_Y = 76, 46, 297
NO_CUSTOM = "no_custom"       # marks the shortcut boxes themselves, so a double tap on them never makes a shortcut
# the five category tiles' icons, in the order of TABS (a function each, so a missing name in an old Flet can't crash the app)
TAB_ICONS = [lambda: icon("GRID_VIEW", "APPS"), lambda: icon("MEDICATION_OUTLINED", "MEDICAL_SERVICES_OUTLINED"),
             lambda: icon("SCIENCE_OUTLINED", "BIOTECH"), lambda: icon("MEDICAL_SERVICES_OUTLINED", "HEALTH_AND_SAFETY"),
             lambda: icon("VACCINES_OUTLINED", "VACCINES")]
SLOT_COUNT = 4
SLOT_X = [12 + i * (SLOT_W + (WINDOW_W - 24 - SLOT_COUNT * SLOT_W) / (SLOT_COUNT - 1)) for i in range(SLOT_COUNT)]


def shortcut_slot(slot, name, x):
    """A pill: the three dots sit in its top-right, the name is centred underneath (up to two lines), with clear space around both."""
    base = dict(width=SLOT_W, height=SLOT_H, border_radius=RADIUS, bgcolor=C_SLOT, border=border_all(1, C_BORDER))
    if name is None:                                   # an empty box: its own "+" (pick what goes in it)
        return at(ft.Container(width=SLOT_W, height=SLOT_H, border_radius=RADIUS, bgcolor=C_PEACH, alignment=CENTER,
                               border=border_all(1, C_PEACH_LINE), data=NO_CUSTOM, on_click=lambda e: choose_shortcut(slot),
                               content=ft.Icon(ft.Icons.ADD, size=24, color=C_PRIMARY_DARK)), x, SLOT_Y)
    label = ft.Container(left=6, top=14, width=SLOT_W - 12, height=28, alignment=CENTER, data=NO_CUSTOM,
                         on_click=lambda e: run_shortcut(name),
                         content=txt(name, 10, 500, C_TEXT, text_align=ft.TextAlign.CENTER, max_lines=2))
    dots = ft.Container(left=SLOT_W - 32, top=1, width=24, height=16, alignment=CENTER, data=NO_CUSTOM,
                        on_click=lambda e: shortcut_menu(slot),
                        content=ft.Icon(ft.Icons.MORE_HORIZ, size=14, color=C_TEXT))
    return at(ft.Container(content=ft.Stack(width=SLOT_W, height=SLOT_H, controls=[label, dots]), **base), x, SLOT_Y)


# ---- home cards -----------------------------------------------------------------------
def open_care_plan():
    """Open the care plan page in settings. Back returns to wherever it was opened from (home card, shortcut or settings)."""
    State.careplan_from = App.current
    navigate("careplan")


def care_card(y):
    """Care plan card: title, price and 'hide for 7 days', laid out with padding (no loose absolute text)."""
    def hide(e):
        log_feature("Hide care plan card")
        State.care_hidden = True
        navigate("home")

    hide_btn = ft.Container(width=114, height=26, border_radius=BTN_RADIUS, bgcolor=C_WHITE,
                            alignment=CENTER, on_click=hide, content=txt(TXT_CARE_HIDE, 10, 700, C_MAROON))
    return [ft.Container(
        left=12, top=y, width=336, height=130, border_radius=RADIUS, bgcolor=C_MAROON, padding=pad(20, 18, 16, 16),
        on_click=lambda e: open_care_plan(),
        content=ft.Column(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Container(width=250, content=txt(TXT_CARE_TITLE, 18, 700, C_WHITE)),      # breaks after "our" like the Figma
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                   controls=[txt(TXT_CARE_SUB, 16, 600, C_WHITE, no_wrap=True), hide_btn])]))], 130


def refill_card(y):
    """Shown only if 'Send refill reminders based on my past orders' is ON. Information only (no button)."""
    n = len(PREVIOUS_ORDER)
    h = 34 + 15 * (n + 2) + 10 * (n + 2) + 14
    rows = [txt(f"{pname(pid)} : {days} days", 12, 500, C_TEXT) for pid, days in PREVIOUS_ORDER]
    return [ft.Container(
        left=12, top=y, width=336, height=h, border_radius=RADIUS, bgcolor=C_REFILL, border=border_all(1, C_MAROON),
        padding=pad(20, 18, 20, 16),
        content=ft.Column(spacing=10, controls=[
            txt(TXT_REFILL_TITLE, 12, 700, C_TEXT), *rows, ft.Container(height=4),
            rich([(TXT_REFILL_FOOTER, "refill_footer")], 12, 500)]))], h


COUNTDOWN = {"left": COUNTDOWN_START_SECONDS}      # shared, so it keeps running between screens


def fmt_time(sec):
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def countdown_card(y):
    """Countdown card, styled like the previous prototype's sale banner (pink, maroon text)."""
    label = txt(fmt_time(COUNTDOWN["left"]), 32, 700, C_MAROON)
    App.countdown_label = label
    return [ft.Container(
        left=12, top=y, width=336, height=118, border_radius=RADIUS, bgcolor=C_PINK, padding=pad(20, 16, 20, 16),
        content=ft.Column(spacing=2, controls=[
            txt(TXT_COUNTDOWN_HEAD, 18, 700, C_MAROON), label, txt(TXT_COUNTDOWN_SUB, 12, 500, C_MAROON)]))], 118


async def countdown_ticker():
    while True:
        await asyncio.sleep(1)
        COUNTDOWN["left"] = COUNTDOWN["left"] - 1 if COUNTDOWN["left"] > 0 else COUNTDOWN_START_SECONDS
        label = App.countdown_label
        if App.current == "home" and label is not None:
            label.value = fmt_time(COUNTDOWN["left"])
            try:
                label.update()
            except Exception:
                pass


# ---- home --------------------------------------------------------------------------
def home_screen():
    location_text = TXT_LOCATION_CURRENT if State.prefs["location"] else TXT_LOCATION_DEFAULT
    App.countdown_label = None

    tabs = []
    tab_step = (WINDOW_W - 24 - 48) / (len(TABS) - 1)        # tiles are 48 wide, spread evenly between the 12px margins
    for i, label in enumerate(TABS):
        x = 12 + tab_step * i
        tabs.append(at(ft.Container(width=48, height=48, border_radius=RADIUS, bgcolor=C_BLUE, alignment=CENTER,
                                    content=ft.Icon(TAB_ICONS[i](), size=24, color=C_TEXT)), x, 129))
        tabs.append(at(ft.Container(width=72, alignment=ft.Alignment(0, -1),         # label box centred on its tile; "Popular categories" wraps to two lines
                                    content=txt(label, 11, 600, text_align=ft.TextAlign.CENTER)), x - 12, 183))
    tabs.append(at(ft.Container(width=32, height=3, border_radius=2, bgcolor=C_PRIMARY_DARK), 20, 217))

    slots = [shortcut_slot(i, name, x) for i, (x, name) in enumerate(zip(SLOT_X, State.shortcuts))]

    # ---- below the shortcuts: stacked top to bottom; a section that is switched off simply isn't there
    body = []
    y = 432
    if State.prefs["countdown"]:
        c, h = countdown_card(y)
        body += c
        y += h + 28
    if State.prefs["refill_reminders"]:
        c, h = refill_card(y)
        body += c
        y += h + 36
    for heading_text, row in HOME_SECTIONS:               # heading, then the row of cards 34px below it (same spacing as "Picked for you")
        body.append(at(txt(heading_text, 16, 700), 12, y))
        for i, pid in enumerate(row):
            body += item_card(pid, ITEM_X[i], y + CARDS_DY)
        y += SECTION_PITCH
    if State.prefs["picked_for_you"]:
        body.append(at(rich([(TXT_PICKED, "picked_for_you")], 16, 700), 12, y))
        for i, pid in enumerate(PICKED_ROW):
            body += item_card(pid, ITEM_X[i], y + CARDS_DY)
        y += SECTION_PITCH
    if not State.care_hidden and not State.care_subscribed:        # the card is the invitation to subscribe
        c, h = care_card(y)
        body += c
        y += h
    height = max(WINDOW_H, y + 40)

    return frame(
        # header: location on the left (pin, text, arrow), person and cart on the right
        at(ft.Container(width=244, height=40, alignment=ft.Alignment(-1, 0), content=ft.Row(
            spacing=4, controls=[ft.Container(margin=pad(0, 0, 0, 0), content=ft.Icon(icon("LOCATION_ON", "PLACE"), size=24, color=C_PRIMARY)),
                                 txt(location_text, 15, 700, no_wrap=True),
                                 ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=20, color=C_TEXT)])), 12, 16.3),
        round_button(icon("PERSON_OUTLINE"), 264, 16.5, on_click=lambda e: navigate("accounts")),
        cart_button(308, 16.5),
        at(ft.Container(width=336, height=48, border_radius=RADIUS, bgcolor=C_PAGE, border=border_all(1, C_BORDER),
                        padding=pad(14, 0, 0, 0), alignment=ft.Alignment(-1, 0), content=ft.Row(spacing=10, controls=[
                            ft.Icon(ft.Icons.SEARCH, size=22, color=C_GREY), txt(TXT_SEARCH, 14, 400, C_GREY)])), 12, 69),
        *tabs,
        at(txt(TXT_SHORTCUTS, 16, 700), 12, 254),
        *slots,
        at(ft.Container(width=78, height=24, border_radius=12, border=border_all(1, C_PRIMARY_DARK), alignment=CENTER, data=NO_CUSTOM,
                        bgcolor=C_WHITE, on_click=lambda e: pick_shortcuts(), content=txt(TXT_RECOMMENDED, 10, 700, C_PRIMARY_DARK)),
           WINDOW_W - 12 - 78, 359),
        *body,
        height=height)


# ---- product page --------------------------------------------------------------------
def price_line(pid):
    """Product page price. With 'Show deals and reference prices' ON the reference price follows it, underlined."""
    parts = [txt(rupees(pprice(pid)), 18, 700)]
    if State.prefs["reference_prices"]:
        parts.append(struck_term(pref_price(pid), "reference_price", 14, C_GREY))
    return ft.Row(spacing=8, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=parts)


def product_screen():
    pid = State.selected
    controls = [
        *app_bar(),
        round_button(ft.Icons.ARROW_BACK, 8, 8, on_click=lambda e: product_back()),
        cart_button(308, 16.5),
        at(item_image(pid, 231, RADIUS), 64, 169)]
    if State.prefs["low_stock"]:
        controls.append(at(rich([(TXT_LOW_STOCK, "low_stock")], 12, 700, C_RED), 64, 410))
    controls += [
        at(txt(pname(pid), 20, 700), 64, 440),
        at(price_line(pid), 64, 472),
        at(cart_control(pid, 111, 36), 184, 466)]         # right edge lines up with the picture (64 + 231)

    if needs_rx(pid):                                   # the Rx symbol and "Prescription required" (underlined: tap for the explanation)
        controls.append(at(ft.Row(spacing=8, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            txt("\u211e", 22, 700), rich([(TXT_RX_REQUIRED, "rx_required")], 13, 600)]), 64, 508))
    if State.prefs["frequently_bought"]:
        controls.append(at(rich([(TXT_FBT, "frequently_bought")], 16, 700), 12, 551))
        related = [p for p in FBT_POOL if p != pid][:3]
        for i, rid in enumerate(related):
            controls += item_card(rid, ITEM_X[i], 551 + CARDS_DY)
    return frame(*controls)


# ---- accounts ("settings") ------------------------------------------------------------
# (label, preference that must be ON for the row to show (None = always), what tapping it does)
# No row is underlined here: insights / nucoins carry their green underline on their own page's heading.
ACCOUNT_ROWS = [
    ("Edit details", None, None),
    (TXT_PREFS_TITLE, None, "prefs"),          # "customise your experience" (settings rows are lower-case)
    (TXT_PAST_ORDERS, None, "pastorders"),
    (TXT_INSIGHTS, "infer_health", "insights"),          # which preference drives this one is a GUESS (only shown when that preference is ON)
    (TXT_NUCOINS_PAGE, "earn_spend_nucoins", "nucoins"),   # which preference drives this one is a GUESS (only shown when that preference is ON)
    ("Care plan", None, "careplan"),                 # added at your request (not in the Figma)
    ("Delete account", None, None),
]
# The icon at the start of each settings row (1mg's account page has one per row). Edit freely.
ACCOUNT_ICONS = {
    TXT_PREFS_TITLE: ("TUNE", "SETTINGS"), "Care plan": ("HEALTH_AND_SAFETY_OUTLINED", "FAVORITE_BORDER"),
    "Delete account": ("DELETE_OUTLINE", "DELETE"), "Edit details": ("EDIT_OUTLINED", "EDIT"),
    TXT_INSIGHTS: ("INSIGHTS", "BAR_CHART"), TXT_NUCOINS_PAGE: ("MONETIZATION_ON_OUTLINED", "PAID"),
    TXT_PAST_ORDERS: ("RECEIPT_LONG_OUTLINED", "RECEIPT"),
}
ACCOUNT_ROW_H = 52


def accounts_screen():
    controls = [*app_bar(), back_button("home"),
                at(ft.Container(width=56, height=56, border_radius=28, bgcolor=C_PEACH, alignment=CENTER,
                                content=ft.Icon(icon("PERSON_OUTLINE"), size=32, color=C_PRIMARY_DARK)), 16, 76)]
    y = 156                                              # a list of full-width rows: icon, label, arrow, thin divider (like 1mg's account page)
    for label, pref, action in ACCOUNT_ROWS:
        if pref and not State.prefs[pref]:
            continue
        if action == "prefs":
            go = lambda e: open_prefs()
        elif action == "careplan":
            go = lambda e: open_care_plan()
        elif action:
            go = lambda e, a=action: navigate(a)
        else:
            go = None
        controls.append(at(ft.Container(
            width=WINDOW_W, height=ACCOUNT_ROW_H, on_click=go, padding=pad(16, 0, 12, 0), alignment=ft.Alignment(-1, 0),
            border=ft.Border(bottom=ft.BorderSide(1, C_DIVIDER)),
            content=ft.Row(spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Icon(icon(*ACCOUNT_ICONS.get(label, ("CIRCLE",))), size=22, color=C_GREY),
                ft.Container(expand=True, content=txt(label, 14, 600)),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=C_GREY)])), 0, y))
        y += ACCOUNT_ROW_H
    return frame(*controls)


def info_rows(rows, y, left=16):
    """Grey label over a value, one row after another (the same look as the care plan screen). Returns (controls, next y)."""
    out = []
    for label, value in rows:
        out.append(at(txt(label, 12, 400, C_GREY), left, y))
        out.append(at(txt(value, 14, 600, C_TEXT), left, y + 18, 328))
        y += 58
    return out, y


def heading(label, key=None):
    """Page heading in the top bar, beside the back arrow. With `key` it carries the green underline and opens that pop-up."""
    return at(rich([(label, key)], 18, 700) if key else txt(label, 18, 700), 56, 16)


# ---- insights (settings > insights): calendar of what medicines were bought each day ----
CELL, GAP = 44, 3                                   # one day = 44x44; 7 columns = 326px wide, centred on the 360px screen
CAL_X = (WINDOW_W - (7 * CELL + 6 * GAP)) / 2


def classes_by_day():
    """{date: [medicine classes bought that day, in order]} from PAST_ORDERS."""
    out = {}
    for order in PAST_ORDERS:
        for pid in order["items"]:
            cls = MEDICINE_CLASS.get(pid)
            if cls and cls not in out.setdefault(order["date"], []):
                out[order["date"]].append(cls)
    return {d: c for d, c in out.items() if c}


def day_cell(day, classes):
    """No medicines = no colour. One class = the whole day in its colour. Several = small swatches (so all of them fit)."""
    num = txt(str(day), 12, 500, C_TEXT)
    base = dict(width=CELL, height=CELL, alignment=CENTER)
    if not classes:
        return ft.Container(content=num, **base)
    if len(classes) == 1:
        return ft.Container(border_radius=BTN_RADIUS, bgcolor=MEDICINE_CLASSES[classes[0]], content=num, **base)
    size = 12 if len(classes) <= 3 else 10
    swatches = [ft.Container(width=size, height=size, border_radius=3, bgcolor=MEDICINE_CLASSES[c]) for c in classes]
    rows = [ft.Row(spacing=2, alignment=ft.MainAxisAlignment.CENTER, controls=swatches[i:i + 3])
            for i in range(0, len(swatches), 3)]
    return ft.Container(content=ft.Column(spacing=2, alignment=ft.MainAxisAlignment.CENTER,
                                          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                          controls=[num, *rows]), **base)


def insights_screen():
    by_day = classes_by_day()
    shown = max(by_day) if by_day else datetime.date.today()           # the month of the latest order
    controls = [*app_bar(), back_button("accounts"), heading(TXT_INSIGHTS, "acc_insights"),
                at(txt(f"{calendar.month_name[shown.month]} {shown.year}", 16, 700), CAL_X, 84)]
    for i, name in enumerate(calendar.day_abbr):                        # Mon ... Sun
        controls.append(at(txt(name, 11, 500, C_GREY, text_align=ft.TextAlign.CENTER), CAL_X + i * (CELL + GAP), 122, CELL))
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(shown.year, shown.month)
    for r, week in enumerate(weeks):
        for c, day in enumerate(week):
            if day:
                controls.append(at(day_cell(day, by_day.get(datetime.date(shown.year, shown.month, day), [])),
                                   CAL_X + c * (CELL + GAP), 146 + r * (CELL + GAP)))
    y = 146 + len(weeks) * (CELL + GAP) + 18
    controls.append(at(txt("Key", 12, 700), CAL_X, y))
    for i, (name, colour) in enumerate(MEDICINE_CLASSES.items()):
        controls.append(at(ft.Row(spacing=10, controls=[
            ft.Container(width=16, height=16, border_radius=4, bgcolor=colour), txt(name, 12, 500)]), CAL_X, y + 24 + i * 26))
    return frame(*controls, height=max(WINDOW_H, y + 24 + len(MEDICINE_CLASSES) * 26 + 40))


# ---- nucoins (settings > nucoins): MOCK balance ----------------------------------------
def nucoins_screen():
    bal = State.nucoins_balance
    big = at(ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[txt(str(bal), 44, 700), txt("NuCoins", 16, 600)]), 16, 108)
    rows = [("Worth", rupees(bal * NUCOIN_VALUE)),
            ("Value of one NuCoin", rupees(NUCOIN_VALUE)),
            ("Taken off at checkout", f"{NUCOINS_FRACTION:.0%} of your cart amount, when ticked")]
    body, _ = info_rows(rows, 190)
    return frame(*app_bar(), back_button("accounts"), heading(TXT_NUCOINS_PAGE, "acc_nucoins"),
                 at(txt("Your balance", 12, 400, C_GREY), 16, 90), big, *body)


# ---- past orders (settings > past orders): the placeholder past order(s) -------------------
def order_card(order):
    qty = order["items"]
    sub = sum(pprice(pid) * q for pid, q in qty.items())
    total = order.get("total", sub + HANDLING_FEE + DELIVERY_FEE)         # the placeholder order has no stored total
    rule = lambda: ft.Container(height=1, bgcolor=C_DIVIDER)

    def line(left, right, weight=500):
        return ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                      controls=[txt(left, 13, weight), txt(right, 13, weight)])

    date_row = [txt(fmt_date(order["date"]), 12, 400, C_GREY)]
    if State.prefs["reorder_button"]:                                  # shown only if "Display one-tap re-order button" is ON
        date_row.append(ft.Container(height=28, border_radius=BTN_RADIUS, bgcolor=C_ORANGE, padding=pad_xy(12, 0), alignment=CENTER,
                                     on_click=lambda e, o=order: reorder(o, "checkout"),
                                     content=txt(TXT_ONE_TAP_ORDER, 11, 700, C_TEXT)))
    status = ft.Container(height=22, border_radius=6, bgcolor=C_MINT, border=border_all(1, C_MINT_LINE),
                          padding=pad_xy(10, 0), alignment=CENTER, content=txt(order["status"], 11, 700))
    return ft.Container(
        width=336, border_radius=RADIUS, bgcolor=C_WHITE, border=border_all(1, C_BORDER), padding=pad(16, 16, 16, 16),
        content=ft.Column(spacing=10, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                   controls=[txt(order["id"], 14, 700), status]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                   controls=date_row),
            rule(),
            *[line(f"{pname(pid)} x{q}", rupees(pprice(pid) * q)) for pid, q in qty.items()],
            line(TXT_HANDLING, rupees(HANDLING_FEE)),
            line(TXT_DELIVERY, rupees(DELIVERY_FEE)),
            *([line(TXT_ROUND_UP, rupees(order["round_up"]))] if order.get("round_up") else []),
            *([line(TXT_NUCOINS, "-" + rupees(order["nucoins_off"]))] if order.get("nucoins_off") else []),
            rule(),
            line(TXT_TOTAL, rupees(total), 700)]))


def past_orders_screen():
    cards = ft.Column(spacing=16, controls=[order_card(o) for o in reversed(PAST_ORDERS)])      # newest first
    h = 72 + sum(202 + 26 * (len(o["items"]) + bool(o.get("round_up")) + bool(o.get("nucoins_off"))) + 16 for o in PAST_ORDERS) + 24                    # card height is auto; this is an estimate
    return frame(*app_bar(), back_button("accounts"), heading(TXT_PAST_ORDERS), at(cards, 12, 72), height=max(WINDOW_H, h), bg=C_PAGE)


# ---- care plan (settings > care plan) -------------------------------------------------
def fmt_date(d):
    return f"{d.day} {d.strftime('%b')} {d.year}"


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def care_plan_screen():
    subscribed, cancelled = State.care_subscribed, State.care_cancelled
    auto = State.care_auto_renew and subscribed and not cancelled
    ends = add_months(State.care_started, CARE_PLAN["months"]) if subscribed else None

    def toggle_auto(e):
        State.care_auto_renew = e.control.value          # separate from the preference list: ticking "Automatically renew subscriptions" there does not switch this on
        navigate("careplan")

    def subscribe(e):
        log_feature("Care plan subscription")
        State.care_subscribed, State.care_cancelled = True, False
        State.care_started = datetime.date.today()
        navigate("careplan")

    def toggle_cancel(e):
        log_feature("Care plan subscription")
        State.care_cancelled = not State.care_cancelled
        if State.care_cancelled:
            State.care_auto_renew = False
        navigate("careplan")

    if not subscribed:
        rows = [("Plan", CARE_PLAN["name"]), ("Status", "Not subscribed"), ("Price", CARE_PLAN["price"]),
                ("Auto renew", "Off")]
        button = ("Subscribe", subscribe)
    else:
        pay = []
        if State.prefs["save_card"]:
            pay.append("Saved card")
        if State.prefs["save_upi"]:
            pay.append("Saved UPI ID")
        rows = [
            ("Plan", CARE_PLAN["name"]),
            ("Status", f"Cancelled, active until {fmt_date(ends)}" if cancelled else "Active"),
            ("Price", CARE_PLAN["price"]),
            ("Started on", fmt_date(State.care_started)),
            ("Renews on" if auto else "Ends on", fmt_date(ends)),
            ("Auto renew", "On" if auto else "Off"),
            ("Next charge", f"{CARE_PLAN['renewal_charge']} on {fmt_date(ends)}" if auto else "None"),
            ("Payment method", " and ".join(pay) if pay else "Not saved (asked for at renewal)"),
        ]
        button = ("Resume subscription" if cancelled else "Cancel subscription", toggle_cancel)
    controls = [*app_bar(), back_button(State.careplan_from), at(txt(TXT_CARE_PLAN, 18, 700), 56, 16)]
    y = 90
    for label, value in rows:
        controls.append(at(txt(label, 12, 400, C_GREY), 16, y))
        controls.append(at(txt(value, 14, 600, C_TEXT), 16, y + 18, 230 if label == "Auto renew" else 328))
        if label == "Auto renew":
            controls.append(at(ft.Switch(value=auto, active_color=C_PRIMARY_DARK, disabled=cancelled or not subscribed,
                                         on_change=toggle_auto), 284, y + 4))
        y += 58
    controls.append(at(pill_button(button[0], button[1], width=328), 16, y + 14))
    return frame(*controls)


# ---- checkout ----------------------------------------------------------------------
def learnt_values():
    """What the app actually saw the user do this session."""
    bought = ", ".join(f"{pname(p)} x{q}" for p, q in State.cart.items())
    looked = ", ".join(pname(p) for p in State.viewed)
    conds = []
    for p in State.cart:
        c = PRODUCT_CONDITIONS.get(p)
        if c and c not in conds:
            conds.append(c)
    return {
        "time_spent": fmt_time(int(time.time() - State.started)),
        "features": ", ".join(State.features) or NOTHING,
        "looked_at": looked or NOTHING,
        "bought": bought or NOTHING,
        "conditions": ", ".join(conds) or "none",
        "location": TXT_LOCATION_CURRENT,
    }


def needs_rx(pid):
    return pid in RX_PRODUCTS


def cart_has_rx():
    return any(needs_rx(pid) for pid in State.cart)


def rx_line():
    """The single "Your prescriptions: ..." line. Only when the cart holds a medicine that needs a prescription, and at least one of
    "Keep my prescriptions" / "Share my prescription" is ON; it says what happens to the contents under whichever are ON."""
    keep, share = State.prefs["keep_rx"], State.prefs["share_rx"]
    if not (keep or share) or not cart_has_rx():
        return None
    return TXT_RX_LINE.format(what=RX_BOTH if keep and share else RX_KEEP if keep else RX_SHARE)


def learnt_lines():
    """The lines under "What we've learnt from you". The "shared with advertising..." line only appears if something else is listed."""
    vals = learnt_values()
    out = []
    rx_done = False
    for key in RECEIPT_KEYS:
        if key in ("keep_rx", "share_rx"):               # both preferences make ONE line
            if not rx_done:
                rx_done = True
                if rx_line():
                    out.append(rx_line())
        elif key != "share_data" and State.prefs.get(key):
            out += [line.format(**vals) for line in RECEIPT_LINES[key]]
    if out and State.prefs.get("share_data"):
        out = [RECEIPT_LINES["share_data"][0].format(**vals)] + out
    return out


def checkout_numbers():
    """All checkout maths in one place. Rows for round-up / NuCoins exist only if the matching preference is ON."""
    items_sum = sum(pprice(pid) * q for pid, q in State.cart.items())
    subtotal = items_sum + (HANDLING_FEE + DELIVERY_FEE if State.cart else 0)
    show_round = State.prefs["round_up"]
    show_nucoins = State.prefs["earn_spend_nucoins"]
    round_amt = (-subtotal) % ROUND_UP_TO                 # rupees needed to reach the next multiple
    # NuCoins cover a fraction of the cart amount (whole rupees, rounded down), never more than the balance is worth
    nucoins_off = min(int(items_sum * NUCOINS_FRACTION), int(State.nucoins_balance * NUCOIN_VALUE))
    nucoins_used = int(nucoins_off / NUCOIN_VALUE)        # how many NuCoins that is
    total = subtotal
    if show_round and State.roundup_checked:
        total += round_amt
    if show_nucoins and State.nucoins_checked:
        total -= nucoins_off
    return dict(subtotal=subtotal, show_round=show_round, show_nucoins=show_nucoins,
                round_amt=round_amt, nucoins_off=nucoins_off, nucoins_used=nucoins_used, total=total)


def reset_checkout_boxes():
    """Round up and NuCoins start unticked for every new checkout."""
    State.roundup_checked = State.nucoins_checked = False


def place_order():
    """Place order: record it in past orders (and so in the insights calendar), then confirm, empty the cart and go home."""
    log_feature("Place order")
    page = App.page
    n = checkout_numbers()
    uses_nucoins = n["show_nucoins"] and State.nucoins_checked
    if uses_nucoins:
        State.nucoins_balance = max(0, State.nucoins_balance - n["nucoins_used"])
    PAST_ORDERS.append({
        "id": f"#6MG-{1001 + len(PAST_ORDERS)}", "date": datetime.date.today(), "status": TXT_NEW_ORDER_STATUS,
        "items": dict(State.cart), "total": n["total"],
        "round_up": n["round_amt"] if n["show_round"] and State.roundup_checked else 0,
        "nucoins_off": n["nucoins_off"] if uses_nucoins else 0})

    def done(e):
        State.cart.clear()
        reset_checkout_boxes()
        State.rx_uploaded = State.rx_redacted = False
        close_dialog(page, dlg)
        navigate("home")

    dlg = green_dialog(
        txt(TXT_ORDER_PLACED, 13, 500, C_TEXT), modal=True,
        actions=[ft.Container(padding=pad_xy(12, 8), on_click=done, content=txt("OK", 13, 600, C_PRIMARY_DARK))])
    show_dialog(page, dlg)


def place_order_bar(total):
    """Bottom bar: total on the left, big coral button on the right (the darker coral, so the white text is readable).
    Until the phone number has been entered and verified the button reads "Enter phone number" and goes through the phone / OTP screens."""
    ready = State.phone_verified
    return ft.Container(
        height=BOTTOM_BAR_H, padding=pad_xy(16, 10), bgcolor=C_WHITE,
        border=ft.Border(top=ft.BorderSide(1, C_BORDER)),
        content=ft.Row(spacing=16, controls=[
            txt(rupees(total), 18, 700),
            ft.Container(height=48, border_radius=BTN_RADIUS, bgcolor=C_PRIMARY_DARK, alignment=CENTER, expand=True,
                         on_click=(lambda e: place_order()) if ready else (lambda e: ask_phone()),
                         content=txt(TXT_PLACE_ORDER if ready else TXT_ENTER_PHONE, 16, 700, C_WHITE))]))


def remove_from_cart(pid):
    log_feature("Remove from cart")
    State.cart.pop(pid, None)
    if not State.cart:
        reset_checkout_boxes()
    navigate("checkout")


CK_L, CK_R = 24, 336                                   # checkout: left and right edge of the content (inside the 12px-margin white cards)


def checkout_screen():
    """Three white cards on the light grey page (like 1mg's cart): the items, the bill (label left, amount right-aligned, same line),
    and what the app has learnt. Everything is placed on fixed rows so labels, ticks and amounts line up."""
    items = list(State.cart.items())
    if not items:
        return frame(*app_bar(), back_button("home"), at(txt(TXT_EMPTY_CART, 14, 600), 16, 72))
    n = checkout_numbers()
    card = lambda top, h: at(ft.Container(width=336, height=h, border_radius=RADIUS, bgcolor=C_WHITE, border=border_all(1, C_BORDER)), 12, top)
    left_cell = lambda control, x, rc, w, h=24: at(ft.Container(width=w, height=h, alignment=ft.Alignment(-1, 0), content=control), x, rc - h / 2)
    amount = lambda value, rc, weight=600, size=13: at(ft.Container(width=64, height=24, alignment=ft.Alignment(1, 0), content=txt(value, size, weight)), CK_R - 64, rc - 12)

    def tick(attr):
        def handler(e):
            log_feature("Round up donation" if attr == "roundup_checked" else "NuCoins")
            setattr(State, attr, e.control.value)
            navigate("checkout")
        return handler

    rx = cart_has_rx()                                    # a medicine that needs a prescription is in the cart: offer the upload (44px + 12px gaps)
    controls = [*app_bar(), back_button("home"), card(68, 80 * len(items))]
    if rx:
        controls.append(at(pill_button(TXT_RX_UPLOADED if State.rx_uploaded else TXT_RX_UPLOAD, lambda e: open_rx(), width=336, primary=False),
                           12, 68 + 80 * len(items) + 12))
    y = 76
    for pid, qty in items:                                # one row per item: picture, name, quantity, bin, price (80px apart)
        rc = y + 32
        controls += [
            at(item_image(pid, 64, 8), CK_L, y),
            at(ft.Container(width=88, height=32, alignment=ft.Alignment(-1, 0), content=txt(pname(pid), 13, 600)), 96, rc - 16),
            at(qty_pill(pid, 52), 188, rc - 12),
            at(ft.Container(width=28, height=28, alignment=CENTER, on_click=lambda e, p=pid: remove_from_cart(p),
                            content=ft.Icon(icon("DELETE_OUTLINE"), size=20, color=C_GREY)), 244, rc - 14),
            amount(rupees(pprice(pid) * qty), rc)]
        y += 80
    top = 68 + 80 * len(items) + 12 + (56 if rx else 0)   # the bill card
    rows = [(rich([(TXT_HANDLING, "handling_charges")], 13, 500), rupees(HANDLING_FEE), None),
            (txt(TXT_DELIVERY, 13, 500), rupees(DELIVERY_FEE), None)]
    if n["show_round"]:
        rows.append((rich([(TXT_ROUND_UP, "round_up_donation")], 13, 500), rupees(n["round_amt"]), "roundup_checked"))
    if n["show_nucoins"]:
        rows.append((rich([(TXT_NUCOINS, "nucoins_used")], 13, 500), "\u2212" + rupees(n["nucoins_off"]), "nucoins_checked"))
    controls.append(card(top, 56 + 40 * len(rows)))
    rc = top + 24                                         # summary rows, 40px apart
    for label, value, attr in rows:
        controls += [left_cell(label, CK_L, rc, 200), amount(value, rc)]
        if attr:                                          # the tick sits in the same column on both optional rows
            controls.append(at(ft.Checkbox(value=getattr(State, attr), active_color=C_PRIMARY_DARK, check_color=C_WHITE, on_change=tick(attr)), 224, rc - 24))
        rc += 40
    controls += [at(ft.Container(width=CK_R - CK_L, height=1, bgcolor=C_DIVIDER), CK_L, rc - 16),
                 left_cell(txt(TXT_TOTAL, 14, 700), CK_L, rc + 8, 200), amount(rupees(n["total"]), rc + 8, 700, 14)]
    ty = top + 56 + 40 * len(rows) + 12                   # "What we've learnt from you" card
    lines = learnt_lines()
    note_parts = [(t, open_prefs if k == "GO_PREFS" else k) for t, k in TXT_LEARNT_NOTE]     # the underlined part opens preferences
    per_line = 44                                         # rough characters per line at 12px in 312px, for the height estimate
    note_h = (15 * -(-sum(len(t) for t, _ in note_parts) // per_line) + 12) if lines else 0
    lines_h = sum(15 * max(1, -(-len(l) // per_line)) + 6 for l in lines)
    card_h = 16 + 26 + note_h + lines_h + 16 if lines else 16 + 20 + 16
    controls.append(card(ty, card_h))
    controls.append(at(txt(TXT_LEARNT, 14, 700), CK_L, ty + 16))
    if lines:
        controls.append(at(rich(note_parts, 12, 400, C_GREY), CK_L, ty + 42, CK_R - CK_L))
        controls.append(at(ft.Column(spacing=6, controls=[txt(l, 12, 400, C_GREY) for l in lines]), CK_L, ty + 42 + note_h, CK_R - CK_L))
    return frame(*controls, height=max(WINDOW_H, ty + card_h + 24), bottom=place_order_bar(n["total"]), bg=C_PAGE)


# ---- prescription (checkout > "Upload prescription"): a FAKE prescription to upload, then markup ----
# Everything on it is made up. The patient details are what "Auto" covers with black bars; the doctor and the medicines stay readable.
FAKE_RX = {"clinic": "Sample Clinic", "doctor": "Dr A. Sample, MBBS", "reg": "Reg. no. 00000", "date": "12 Nov 2026",
           "name": "Anita Sharma", "age": "34 / F", "phone": "98765 43210", "address": "12, Sample Street, Bengaluru"}
FAKE_RX_PERSONAL = [("Name:", "name"), ("Age / sex:", "age"), ("Phone:", "phone"), ("Address:", "address")]     # covered by "Auto"
FAKE_RX_DOSES = {"cough_syrup": "5 ml, 3 times a day, for 5 days", "ibuprofen": "1 tablet, twice a day, for 3 days",
                 "nasal_drops": "2 drops in each nostril, twice a day, for 5 days"}
RX_PAPER_H = 420


def open_rx():
    """"Upload prescription": shows the (fake) prescription that was uploaded. A fresh upload starts without the bars."""
    log_feature("Prescription upload")
    if not State.rx_uploaded:
        State.rx_redacted = False
    navigate("prescription")


def auto_markup():
    log_feature("Prescription markup")
    State.rx_redacted = True
    navigate("prescription")


def rx_done():
    State.rx_uploaded = True
    navigate("checkout")


def rx_screen():
    red = State.rx_redacted
    rule = lambda: ft.Container(height=1, bgcolor=C_DIVIDER)

    def personal(label, key):                             # the value, or a black bar the same size while "Auto" has covered it
        value = FAKE_RX[key]
        shown = ft.Container(width=7 * len(value), height=16, bgcolor=C_TEXT) if red else txt(value, 12, 600)
        return ft.Container(height=20, content=ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                      controls=[txt(label, 12, 400, C_GREY), shown]))

    meds = [ft.Column(spacing=2, controls=[txt(f"{i}. {pname(pid)}", 13, 600), txt(FAKE_RX_DOSES.get(pid, "as directed"), 12, 400, C_GREY)])
            for i, pid in enumerate([p for p in PRODUCTS if p in RX_PRODUCTS], 1)]
    paper = ft.Container(
        left=24, top=72, width=312, height=RX_PAPER_H, border_radius=BTN_RADIUS, bgcolor=C_WHITE, border=border_all(1, C_BORDER),
        padding=pad(16, 16, 16, 16),
        content=ft.Column(spacing=8, controls=[
            txt(FAKE_RX["clinic"], 16, 700), txt(FAKE_RX["doctor"], 12, 600), txt(FAKE_RX["reg"], 12, 400, C_GREY), rule(),
            ft.Container(height=20, content=ft.Row(spacing=6, controls=[txt("Date:", 12, 400, C_GREY), txt(FAKE_RX["date"], 12, 600)])),
            *[personal(label, key) for label, key in FAKE_RX_PERSONAL], rule(),
            txt("\u211e", 22, 700), *meds]))
    y = 72 + RX_PAPER_H + 16
    return frame(*app_bar(), back_button("checkout"), at(txt(TXT_RX_TITLE, 18, 700), 56, 16), paper,
                 at(pill_button(TXT_RX_MANUAL, None, width=150, primary=False), 24, y),            # dead: does nothing
                 at(pill_button(TXT_RX_AUTO, lambda e: auto_markup(), width=150, primary=False), 186, y),
                 at(pill_button(TXT_RX_DONE, lambda e: rx_done(), width=312), 24, y + 56), bg=C_PAGE)


SCREENS = {"phone": phone_screen, "otp": otp_screen, "prefs": prefs_screen, "home": home_screen,
           "product": product_screen, "checkout": checkout_screen, "accounts": accounts_screen,
           "careplan": care_plan_screen, "insights": insights_screen, "nucoins": nucoins_screen,
           "pastorders": past_orders_screen, "prescription": rx_screen}


def log_feature(name):
    """Remember that the user used a feature (feeds 'What we've learnt from you')."""
    if name not in State.features:
        State.features.append(name)


def navigate(name):
    App.current = name
    if name in SCREEN_FEATURES:
        log_feature(SCREEN_FEATURES[name])
    screen = SCREENS[name]()
    if State.custom_slot is not None:                  # making a custom shortcut: buttons wait for a double tap, Cancel shows in a corner
        arm_custom(screen)
        screen = ft.Stack(width=WINDOW_W, height=WINDOW_H, controls=[screen, custom_cancel_button()])
    App.root.content = screen
    App.root.update()


def fit_numbers(width, height):
    """(scale, left, top) that puts the 360 x 800 screen in the middle of a width x height window, shrunk to fit if needed (never enlarged)."""
    width = width or WINDOW_W
    height = height or WINDOW_H
    return min(1.0, width / WINDOW_W, height / WINDOW_H), (width - WINDOW_W) / 2, (height - WINDOW_H) / 2


def fit_to_window(page):
    """The screen stays 360 x 800 and is scaled about its centre, so it is never clipped - on a phone-sized window, a window whose
    title bar takes some of the 800px, or a laptop screen. Anything left over around it is the light grey page colour."""
    scale, left, top = fit_numbers(getattr(page, "width", None), getattr(page, "height", None))
    App.root.scale, App.root.left, App.root.top = scale, left, top
    try:
        App.root.update()
    except Exception:
        pass


def main(page: ft.Page):
    page.title = "6mg"
    page.fonts = {FONT: FONT_URL}
    page.theme = ft.Theme(font_family=FONT)
    page.theme_mode = ft.ThemeMode.LIGHT          # stops dark-mode defaults clashing with our fixed colours
    page.bgcolor = C_WHITE
    page.padding = 0
    page.spacing = 0
    try:
        page.window.width, page.window.height = WINDOW_W, WINDOW_H
    except AttributeError:                       # older Flet
        page.window_width, page.window_height = WINDOW_W, WINDOW_H

    def on_key(e):                               # prototype-only: Esc goes back home from product / checkout
        if e.key == "Escape" and State.custom_slot is not None:
            cancel_custom()
        elif e.key == "Escape" and App.current in ("product", "checkout", "accounts", "careplan", "insights", "nucoins", "pastorders", "prescription"):
            navigate("home")
    page.on_keyboard_event = on_key

    App.page = page
    # the 360 x 800 screen sits (positioned, so it keeps its exact size) in a full-window stage and is scaled to fit it
    App.root = ft.Container(width=WINDOW_W, height=WINDOW_H, left=0, top=0, bgcolor=C_WHITE, clip_behavior=ft.ClipBehavior.HARD_EDGE)
    page.add(ft.Container(expand=True, bgcolor=C_PAGE, content=ft.Stack(expand=True, controls=[App.root])))
    navigate("phone")
    fit_to_window(page)
    for hook in ("on_resize", "on_resized"):                                  # the name differs between Flet versions
        try:
            setattr(page, hook, lambda e: fit_to_window(page))
        except Exception:
            pass
    if hasattr(page, "run_task"):
        page.run_task(countdown_ticker)


if __name__ == "__main__":
    assets = {"assets_dir": ASSETS_DIR} if os.path.isdir(ASSETS_DIR) else {}       # lets Flet find the item pictures
    if hasattr(ft, "run"):
        ft.run(main, **assets)
    else:
        ft.app(target=main, **assets)
