from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path
from datetime import date, timedelta

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "rfps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today()

RFPS = [
    {
        "filename": "rfp_lnt_epc_001.pdf",
        "title": "Supply of HT & LT Power Cables for EPC Infra Project",
        "buyer": "Larsen & Toubro – EPC Division",
        "due_days": 45,
        "scope": [
            "3C x 240 sqmm Aluminium XLPE HT Cable – 11 kV – 12 km",
            "1C x 630 sqmm Copper XLPE HT Cable – 11 kV – 4 km",
            "3C x 50 sqmm Aluminium XLPE Cable – LT – 6 km",
        ],
    },
    {
        "filename": "rfp_reliance_industrial_001.pdf",
        "title": "Supply of Control & Instrumentation Cables for Petrochemical Plant",
        "buyer": "Reliance Industries Ltd.",
        "due_days": 60,
        "scope": [
            "25C x 1.5 sqmm Copper Control Cable – Armoured – 18 km",
            "12 Pair Copper Instrumentation Cable – Armoured – 10 km",
            "Cat6 STP Armoured Cable – 8 km",
        ],
    },
    {
        "filename": "rfp_mseb_utility_001.pdf",
        "title": "Procurement of 11 kV HT XLPE Cables for Distribution Network",
        "buyer": "Maharashtra State Electricity Board (MSEB)",
        "due_days": 30,
        "scope": [
            "1C x 1000 sqmm Aluminium XLPE HT Cable – 11 kV – 15 km",
            "3C x 185 sqmm Aluminium XLPE HT Cable – 11 kV – 22 km",
        ],
    },
    {
        "filename": "rfp_siemens_global_001.pdf",
        "title": "Supply of Specialized PTFE & Control Cables for Automation Systems",
        "buyer": "Siemens Global Infrastructure & Industry",
        "due_days": 75,
        "scope": [
            "PTFE Insulated Equipment Wire – 16 AWG – 5 km",
            "PTFE Insulated Equipment Wire – 20 AWG – 8 km",
            "18 Pair Copper Control Cable – Armoured – 6 km",
        ],
    },
]

def generate_pdf(rfp):
    path = OUTPUT_DIR / rfp["filename"]
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, rfp["title"])

    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Buyer: {rfp['buyer']}")

    y -= 20
    due_date = TODAY + timedelta(days=rfp["due_days"])
    c.drawString(50, y, f"Bid Submission Due Date: {due_date.isoformat()}")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Scope of Supply:")

    y -= 20
    c.setFont("Helvetica", 10)
    for item in rfp["scope"]:
        c.drawString(60, y, f"- {item}")
        y -= 15

    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Note: Technical specifications, testing, and acceptance criteria as per applicable IEC / IS standards.")

    c.showPage()
    c.save()
    print(f"Generated {path.name}")

if __name__ == "__main__":
    for rfp in RFPS:
        generate_pdf(rfp)
