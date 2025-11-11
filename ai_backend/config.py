
import os
from dotenv import load_dotenv

load_dotenv()

# Validate environment variables
def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"❌ Missing environment variable: {var_name}")
    return value

# Get all required variables
try:
    REPLICATE_API_TOKEN = get_env_variable("REPLICATE_API_TOKEN")
    AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET = get_env_variable("AWS_S3_BUCKET")
    AWS_REGION = get_env_variable("AWS_REGION")
    print("✅ All environment variables loaded successfully")
except ValueError as e:
    print(str(e))
    exit(1)

THEMES = {
    "MINIMAL SCANDINAVIAN": [
        "https://ethnicraft.com/",
        "https://kavehome.com/",
        "https://www.nordicnest.com/",
        "https://nordicknots.com/",
        "https://swyfthome.com/",
        "https://www.boconcept.com/",
        "https://www.zarahome.com/",
        "https://fermliving.com/",
        "https://www.heals.com/"
    ],
    "TIMELESS LUXURY": [
        "https://rh.com/",
        "https://nordicknots.com/",
        "https://www.eichholtz.com/",
        "https://loaf.com/",
        "https://portaromana.com/",
        "https://www.starkcarpet.com/",
        "https://www.cultfurniture.com/",
        "https://www.dusk.com/",
        "https://www.oka.com/",
        "https://www.pooky.com/",
        "https://www.radilum.com/",
        "https://www.kavehome.com/"
    ],
    "MODERN LIVING": [
        "https://www.liangandeimil.com/",
        "https://www.eichholtz.com/",
        "https://www.gillmorespace.com/",
        "https://nordicknots.com/",
        "https://www.cultfurniture.com/",
        "https://www.sohohome.com/",
        "https://www.swooneditions.com/",
        "https://fermliving.com/",
        "https://www.heals.com/",
        "https://www2.hm.com/",
        "https://www.made.com/",
        "https://www.radilum.com/",
        "https://www.heals.com/",
        "https://www.ligne-roset.com/",
        "https://loopandtwist.com/",
        "https://www.themasie.com/",
        "https://www.kavehome.com/"
    ],
    "MODERN MEDITERRANEAN": [
        "https://www.zarahome.com/",
        "https://loopandtwist.com/",
        "https://rh.com/",
        "https://swyfthome.com/",
        "https://nordicknots.com/",
        "https://www.kavehome.com/"
    ],
    "BOHO ECLECTIC": [
        "https://www.themasie.com/",
        "https://www.sklum.com/",
        "https://loopandtwist.com/",
        "https://www.dusk.com/",
        "https://www.cultfurniture.com/",
        "https://www.heals.com/",
        "https://www.kavehome.com/",
        "https://www.perchandparrow.com/"
    ]
}

# Other constants like room types can be added here if needed