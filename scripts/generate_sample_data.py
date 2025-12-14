import json
from pathlib import Path
from datetime import date

# ---- Paths ----
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RFP_DIR = DATA_DIR / "rfps"
CATALOG_DIR = DATA_DIR / "catalog"
PRICING_DIR = DATA_DIR / "pricing"

CATALOG_DIR.mkdir(parents=True, exist_ok=True)
PRICING_DIR.mkdir(parents=True, exist_ok=True)

# ---- 1. RFP index (metadata about available RFP PDFs) ----
# For now we assume you have placed a file at data/rfps/rfp_001.pdf manually.
rfp_index = [
    {
        "id": "RFP-001",
        "title": "Supply of LT Power Cables for Metro Depot",
        "due_date": "2026-02-15",  # ISO format string
        "file_path": str(RFP_DIR / "rfp_001.pdf")
    },
    {
        "id": "RFP-002",
        "title": "Supply of HT Power & Control Cables for Refinery Project",
        "due_date": "2026-03-10",
        "file_path": str(RFP_DIR / "rfp_002.pdf")  # you can add this later
    }
]

# ---- 2. Product catalog (dummy OEM SKUs) ----
# You can expand this list later; start with a few realistic examples.
catalog = [
    {
        "sku": "XLPE-AL-3C-240-1_1KV",
        "type": "LT Power Cable",
        "voltage_kv": 1.1,
        "cores": 3,
        "conductor_material": "Aluminium",
        "area_sqmm": 240,
        "insulation": "XLPE",
        "armour": "Steel Tape",
        "standard": "IS 7098",
        "flame_class": "FRLS",
        "application": "Underground"
    },
    {
        "sku": "XLPE-AL-3C-185-1_1KV",
        "type": "LT Power Cable",
        "voltage_kv": 1.1,
        "cores": 3,
        "conductor_material": "Aluminium",
        "area_sqmm": 185,
        "insulation": "XLPE",
        "armour": "Steel Wire",
        "standard": "IS 7098",
        "flame_class": "FR",
        "application": "Underground"
    },
    {
        "sku": "PVC-CU-4C-16-1_1KV",
        "type": "LT Control Cable",
        "voltage_kv": 1.1,
        "cores": 4,
        "conductor_material": "Copper",
        "area_sqmm": 16,
        "insulation": "PVC",
        "armour": "Unarmoured",
        "standard": "IS 1554",
        "flame_class": "FRLS",
        "application": "Indoor"
    },
    {
        "sku": "XLPE-AL-1C-630-33KV",
        "type": "HT Power Cable",
        "voltage_kv": 33.0,
        "cores": 1,
        "conductor_material": "Aluminium",
        "area_sqmm": 630,
        "insulation": "XLPE",
        "armour": "Corrugated Aluminium Sheath",
        "standard": "IS 7098",
        "flame_class": "FR",
        "application": "Outdoor"
    }
]

# ---- 3. Product pricing table ----
product_prices = [
    {
        "sku": "XLPE-AL-3C-240-1_1KV",
        "unit": "km",
        "currency": "INR",
        "unit_price": 85000  # price per km
    },
    {
        "sku": "XLPE-AL-3C-185-1_1KV",
        "unit": "km",
        "currency": "INR",
        "unit_price": 72000
    },
    {
        "sku": "PVC-CU-4C-16-1_1KV",
        "unit": "km",
        "currency": "INR",
        "unit_price": 38000
    },
    {
        "sku": "XLPE-AL-1C-630-33KV",
        "unit": "km",
        "currency": "INR",
        "unit_price": 210000
    }
]

# ---- 4. Test / services pricing table ----
test_prices = [
    {
        "test_code": "ROUTINE_TEST_IS_7098",
        "description": "Routine tests as per IS 7098",
        "pricing_model": "per_batch",
        "currency": "INR",
        "price": 15000
    },
    {
        "test_code": "TYPE_TEST_IS_7098",
        "description": "Type test as per IS 7098 in NABL-accredited lab",
        "pricing_model": "per_project",
        "currency": "INR",
        "price": 50000
    },
    {
        "test_code": "THIRD_PARTY_INSPECTION",
        "description": "Third-party inspection at factory (e.g., TUV/BV)",
        "pricing_model": "per_visit",
        "currency": "INR",
        "price": 30000
    },
    {
        "test_code": "FAT_AT_FACTORY",
        "description": "Factory Acceptance Test in presence of client",
        "pricing_model": "per_batch",
        "currency": "INR",
        "price": 25000
    }
]

# ---- Write JSON files ----
def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(f"Wrote {path}")

def main():
    write_json(DATA_DIR / "rfp_index.json", rfp_index)
    write_json(CATALOG_DIR / "catalog.json", catalog)
    write_json(PRICING_DIR / "product_prices.json", product_prices)
    write_json(PRICING_DIR / "test_prices.json", test_prices)

if __name__ == "__main__":
    main()
