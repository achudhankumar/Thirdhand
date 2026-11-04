"""Module 4: Local Scout & Civic Utilities (Google Places, TNEB Bill Calculator/Status, Generic Medicine Lookup)."""

from services.tools.local_tool import LocalTool

GENERIC_MEDICINES_DB = {
    "dolo 650": {
        "brand_name": "Dolo 650 (Micro Labs)",
        "generic_salt": "Paracetamol IP 650 mg",
        "jan_aushadhi_code": "Janaushadhi Paracetamol 650mg",
        "typical_brand_price_15_tabs_inr": 33.0,
        "jan_aushadhi_price_15_tabs_inr": 9.5,
        "savings_percent": 71,
        "use": "Fever and mild-to-moderate pain relief",
    },
    "augmentin 625": {
        "brand_name": "Augmentin 625 Duo (GSK)",
        "generic_salt": "Amoxycillin 500 mg + Clavulanic Acid 125 mg",
        "jan_aushadhi_code": "Janaushadhi Amoxycillin + Potassium Clavulanate 625mg",
        "typical_brand_price_10_tabs_inr": 223.0,
        "jan_aushadhi_price_10_tabs_inr": 62.0,
        "savings_percent": 72,
        "use": "Bacterial infections (Prescription required - Schedule H)",
    },
    "pan 40": {
        "brand_name": "Pan 40 (Alkem)",
        "generic_salt": "Pantoprazole Gastro-Resistant 40 mg",
        "jan_aushadhi_code": "Janaushadhi Pantoprazole 40mg",
        "typical_brand_price_15_tabs_inr": 165.0,
        "jan_aushadhi_price_15_tabs_inr": 18.0,
        "savings_percent": 89,
        "use": "Acidity, GERD, and gastric ulcer relief",
    },
    "azithral 500": {
        "brand_name": "Azithral 500 (Alembic)",
        "generic_salt": "Azithromycin IP 500 mg",
        "jan_aushadhi_code": "Janaushadhi Azithromycin 500mg",
        "typical_brand_price_5_tabs_inr": 132.0,
        "jan_aushadhi_price_5_tabs_inr": 35.0,
        "savings_percent": 73,
        "use": "Bacterial throat/respiratory infections (Prescription required)",
    },
    "shelcal 500": {
        "brand_name": "Shelcal 500 (Torrent)",
        "generic_salt": "Calcium 500 mg + Vitamin D3 250 IU",
        "jan_aushadhi_code": "Janaushadhi Calcium & Vitamin D3",
        "typical_brand_price_15_tabs_inr": 144.0,
        "jan_aushadhi_price_15_tabs_inr": 22.0,
        "savings_percent": 85,
        "use": "Calcium and Vitamin D3 supplement",
    },
    "ecosprin 75": {
        "brand_name": "Ecosprin 75 (USV)",
        "generic_salt": "Aspirin Gastro-Resistant 75 mg",
        "jan_aushadhi_code": "Janaushadhi Aspirin 75mg",
        "typical_brand_price_14_tabs_inr": 6.0,
        "jan_aushadhi_price_14_tabs_inr": 3.0,
        "savings_percent": 50,
        "use": "Blood thinner / cardiovascular prevention (Consult doctor)",
    },
}

CITY_DEFAULT_COORDS = {
    "trichy": (10.7905, 78.7047),
    "tiruchirappalli": (10.7905, 78.7047),
    "chennai": (13.0827, 80.2707),
    "madurai": (9.9252, 78.1198),
    "coimbatore": (11.0168, 76.9558),
    "salem": (11.6643, 78.1460),
}


def calculate_tneb_domestic_tariff(units: int) -> float:
    """Official TANGEDCO bi-monthly domestic slab calculator (first 100 units free)."""
    if units <= 100:
        return 0.0
    if units <= 200:
        return round((units - 100) * 2.35, 2)
    if units <= 400:
        return round(100 * 2.35 + (units - 200) * 4.70, 2)
    if units <= 500:
        return round(100 * 2.35 + 200 * 4.70 + (units - 400) * 6.30, 2)
    return round(
        300 * 4.70 + 100 * 6.30 + (units - 500) * 8.40,
        2,
    )


class LocalScoutTool(LocalTool):
    """Extended Local Scout & Civic Utilities tool matching Playbook Module 4."""

    async def search_nearby_by_text_or_coords(
        self, category: str, location_text_or_coords: str, radius: int = 3000
    ) -> dict:
        text = location_text_or_coords.strip().lower()
        if "," in text:
            parts = [p.strip() for p in text.split(",", 1)]
            try:
                lat, lng = float(parts[0]), float(parts[1])
                return await self.search_nearby_places(category, lat, lng, radius)
            except ValueError:
                pass
        for city, (lat, lng) in CITY_DEFAULT_COORDS.items():
            if city in text:
                return await self.search_nearby_places(category, lat, lng, radius)
        raise ValueError(
            "Location is unverified; provide a supported city or coordinates"
        )

    async def check_tneb_bill_status(
        self, consumer_number: str, units_consumed: int | None = None
    ) -> dict:
        clean_no = "".join(ch for ch in consumer_number if ch.isdigit())
        if not 9 <= len(clean_no) <= 13:
            raise ValueError(
                "TNEB (TANGEDCO) consumer number must contain 9 to 13 digits (Region code + Section + Distribution + Service No)."
            )
        region_code = clean_no[:2]
        regions = {
            "01": "Chennai North",
            "02": "Chennai South",
            "03": "Coimbatore",
            "04": "Erode",
            "05": "Madurai",
            "06": "Tiruchirappalli (Trichy)",
            "07": "Tirunelveli",
            "08": "Vellore",
            "09": "Villupuram",
        }
        region_name = regions.get(region_code, "Tamil Nadu TANGEDCO Region")
        estimated_bill = (
            calculate_tneb_domestic_tariff(units_consumed)
            if units_consumed is not None and units_consumed >= 0
            else None
        )
        return {
            "source": "TANGEDCO (TNEB) Civic Utility Helper",
            "consumer_number": clean_no,
            "region": region_name,
            "estimated_bi_monthly_charge_inr": estimated_bill,
            "units_evaluated": units_consumed,
            "official_quick_pay_url": "https://www.tnebnet.org/awp/login",
            "whatsapp_helpline": "9498794987",
            "note": "Private consumer ledger requires authentication on tnebnet.org. Bi-monthly slab calculation uses official TANGEDCO LT-IA domestic rates (first 100 units free).",
        }

    async def find_generic_medicine(self, medicine_name: str) -> dict:
        key = medicine_name.strip().lower()
        for name, info in GENERIC_MEDICINES_DB.items():
            if key in name or name in key or key in info["generic_salt"].lower():
                return {
                    "source": "PMBJP Jan Aushadhi Generic Reference",
                    "match": info,
                    "disclaimer": "Informational generic salt lookup only. Always consult a registered doctor or pharmacist before substituting any prescription medicine.",
                }
        return {
            "source": "PMBJP Jan Aushadhi Generic Reference",
            "query": medicine_name,
            "match": None,
            "portal_url": "https://janaushadhi.gov.in/",
            "disclaimer": "Exact salt match not in local cache; verify composition on the strip and consult your doctor or nearest Jan Aushadhi Kendra.",
        }
