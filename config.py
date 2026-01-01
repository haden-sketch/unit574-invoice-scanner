"""
Configuration for Unit 574 Mechanic Invoice Scanner
"""
import os

# =============================================================================
# TRUCK IDENTIFICATION - Unit 574
# =============================================================================
UNIT_NUMBER = "574"
FULL_VIN = "3AKJHHDR7KSKE1598"

# Derived search terms from VIN
VIN_LAST_8 = FULL_VIN[-8:]  # KSKE1598
VIN_LAST_6 = FULL_VIN[-6:]  # SE1598
VIN_LAST_4 = FULL_VIN[-4:]  # 1598

# All search terms to look for in emails
SEARCH_TERMS = [
    FULL_VIN,           # 3AKJHHDR7KSKE1598
    VIN_LAST_8,         # KSKE1598
    VIN_LAST_6,         # SE1598
    VIN_LAST_4,         # 1598
    UNIT_NUMBER,        # 574
    f"Unit {UNIT_NUMBER}",
    f"Unit#{UNIT_NUMBER}",
    f"Unit-{UNIT_NUMBER}",
    f"Truck {UNIT_NUMBER}",
    f"Truck#{UNIT_NUMBER}",
    f"Unit: {UNIT_NUMBER}",
]

# =============================================================================
# INVOICE TYPE FILTERS - What we WANT
# =============================================================================
MECHANIC_KEYWORDS = [
    # Repair & Maintenance
    "invoice",
    "repair",
    "mechanic",
    "service",
    "maintenance",
    "preventive maintenance",
    "pm service",
    
    # Towing
    "tow",
    "towing",
    "roadside",
    "breakdown",
    "recovery",
    
    # Oil & Fluids
    "oil change",
    "lube",
    "lubricant",
    "fluid",
    "coolant",
    "antifreeze",
    "def",
    "diesel exhaust fluid",
    
    # Parts & Components
    "parts",
    "brake",
    "tire",
    "battery",
    "filter",
    "belt",
    "hose",
    "alternator",
    "starter",
    "transmission",
    "engine",
    "exhaust",
    "dpf",
    "egr",
    "turbo",
    "suspension",
    "steering",
    "axle",
    "wheel",
    "bearing",
    
    # Labor
    "labor",
    "labour",
    "diagnostic",
    "inspection",
    "dot inspection",
    "annual inspection",
    
    # Shop types
    "truck shop",
    "truck repair",
    "diesel repair",
    "freightliner",
    "peterbilt",
    "kenworth",
    "volvo",
    "international",
    "mack",
    "ta petro",
    "loves",
    "pilot",
    "speedco",
    "rush truck",
]

# =============================================================================
# EXCLUSION FILTERS - What we DO NOT want
# =============================================================================
EXCLUDE_KEYWORDS = [
    # Rate confirmations & Load documents
    "rate confirmation",
    "rate con",
    "ratecon",
    "rate sheet",
    "load confirmation",
    "load tender",
    "dispatch",
    "broker",
    "freight",
    "shipment",
    "pickup",
    "delivery",
    "bol",
    "bill of lading",
    "pod",
    "proof of delivery",
    "lumper",
    "detention",
    "accessorial",
    
    # Insurance & Registration (unless explicitly needed)
    "insurance policy",
    "certificate of insurance",
    "ifta",
    "2290",
    "registration renewal",
    
    # Fuel reports & receipts (NOT mechanic invoices)
    "fuel discount report",
    "rxo fuel discount",
    "fuel receipt",
    "comdata",
    "efs",
    "tcheck",
    "pilot flying j",
    "pricing - pilot",
    
    # Settlement & Pay
    "settlement",
    "pay stub",
    "payroll",
    "direct deposit",
    "1099",
    "w2",
    
    # Zelle payments (not actual invoices)
    "zelle",
    "payment has been sent",
]

# Senders to always skip
EXCLUDE_SENDERS = [
    "no-reply@dat.com",
    "no-reply@truckstop.com", 
    "notifications@keeptruckin.com",
    "notifications@motive.com",
    "noreply@uber.com",  # Uber Freight
]

# =============================================================================
# FILE PATHS - Change these for your server
# =============================================================================
# For cloud server deployment (uses env var) or local testing (uses current dir)
_default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_invoices")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", _default_dir)

# Gmail API credentials - Railway puts secret files in /app/
# Check multiple possible locations
def _find_file(filename):
    possible_paths = [
        f"/app/{filename}",  # Railway secret files location
        filename,  # Current directory
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),  # Same dir as script
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return filename  # Default fallback

CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", _find_file("credentials.json"))
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", _find_file("token.json"))

# =============================================================================
# GMAIL API SETTINGS
# =============================================================================
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# How many emails to fetch per batch
BATCH_SIZE = 100

# How far back to search (in days)
SEARCH_DAYS_BACK = 365  # 1 year

