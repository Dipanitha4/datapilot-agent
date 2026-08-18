"""
data/generate_policy_pdfs.py
Generates realistic travel insurance policy PDF documents.
Run with: python -m data.generate_policy_pdfs
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "policy_documents")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3c5e"),
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontSize=12,
        fontName="Helvetica",
        textColor=colors.HexColor("#4a6fa5"),
        alignment=TA_CENTER,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3c5e"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2c5282"),
        spaceBefore=10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="PolicyBody",
        fontSize=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#333333"),
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        )) 
    styles.add(ParagraphStyle(
        name="BulletItem",
        fontSize=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#333333"),
        leading=15,
        leftIndent=20,
        spaceAfter=3,
        bulletIndent=10,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontSize=8,
        fontName="Helvetica",
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
    ))
    return styles


def generate_comprehensive_policy():
    """Generate travel_insurance_comprehensive_policy.pdf"""
    filename = os.path.join(OUTPUT_DIR, "travel_insurance_comprehensive_policy.pdf")
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = build_styles()
    story = []

    # ── Header ──────────────────────────────────────────────────────────
    story.append(Paragraph("TravelAI Insurance Group", styles["DocTitle"]))
    story.append(Paragraph("Comprehensive Travel Insurance Policy", styles["DocSubtitle"]))
    story.append(Paragraph("Policy Document Reference: TAIG-COMP-2024-v3.1", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3c5e")))
    story.append(Spacer(1, 0.3*cm))

    # ── Summary Table ────────────────────────────────────────────────────
    summary_data = [
        ["Coverage Type", "Maximum Benefit"],
        ["Trip Cancellation", "Up to $10,000 per person"],
        ["Emergency Medical", "Up to $500,000 per person"],
        ["Medical Evacuation", "Up to $1,000,000 per person"],
        ["Baggage Loss/Theft", "Up to $2,500 per person"],
        ["Baggage Delay (12+ hrs)", "Up to $300"],
        ["Travel Delay (6+ hrs)", "Up to $200/day, max $1,000"],
        ["Missed Connection", "Up to $500 per incident"],
        ["Accidental Death", "Up to $100,000"],
    ]
    table = Table(summary_data, colWidths=[9*cm, 8*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4*cm))

    # ── Section 1: Trip Cancellation ────────────────────────────────────
    story.append(Paragraph("1. TRIP CANCELLATION COVERAGE", styles["SectionHeader"]))
    story.append(Paragraph(
        "Trip Cancellation Coverage provides reimbursement for prepaid, non-refundable trip costs "
        "if you must cancel your trip due to a covered reason before your scheduled departure date.",
        styles["BodyText"]
    ))

    story.append(Paragraph("1.1 Covered Reasons for Cancellation", styles["SubHeader"]))
    covered_reasons = [
        "Illness, injury, or death of you, a traveling companion, or an immediate family member",
        "Severe weather conditions making your destination uninhabitable or inaccessible",
        "Natural disasters including earthquakes, hurricanes, floods, or wildfires at destination",
        "Terrorist attack or civil unrest at the destination occurring within 30 days of departure",
        "Involuntary job loss (not voluntary resignation) requiring you to cancel travel",
        "Employer requiring you to work on trip dates due to unforeseen business emergency",
        "Jury duty or mandatory court-ordered appearance during trip dates",
        "Your primary residence becomes uninhabitable due to fire, flood, or natural disaster",
        "Theft of passport or travel documents within 72 hours of departure",
        "Traffic accident on the way to departure point causing you to miss departure",
    ]
    for reason in covered_reasons:
        story.append(Paragraph(f"• {reason}", styles["BulletItem"]))

    story.append(Paragraph("1.2 Exclusions — Not Covered for Trip Cancellation", styles["SubHeader"]))
    exclusions = [
        "Pre-existing medical conditions diagnosed or treated within 180 days of policy purchase "
        "(unless Pre-Existing Condition Waiver is purchased within 14 days of initial trip deposit)",
        "Change of mind, personal preference, or failure to obtain required travel documents (visa, passport)",
        "Financial default of a travel supplier unless the supplier is on our approved list",
        "Acts of war, declared or undeclared, between two or more nations",
        "Travel to destinations under a government-issued Level 4 Travel Advisory (Do Not Travel)",
        "Business or contractual obligations known at time of policy purchase",
        "Pregnancy — routine prenatal care, normal delivery, or elective procedures",
    ]
    for excl in exclusions:
        story.append(Paragraph(f"• {excl}", styles["BulletItem"]))

    story.append(Paragraph("1.3 How to File a Trip Cancellation Claim", styles["SubHeader"]))
    story.append(Paragraph(
        "You must notify us within 72 hours of the event causing cancellation. "
        "Submit the claim form along with: (a) proof of payment for non-refundable trip costs, "
        "(b) documentation of the covered reason (e.g., physician statement, death certificate, "
        "employer letter), and (c) cancellation confirmations from all travel suppliers showing "
        "amounts forfeited. Claims must be submitted within 90 days of the cancellation date.",
        styles["BodyText"]
    ))

    # ── Section 2: Emergency Medical ───────────────────────────────────
    story.append(Paragraph("2. EMERGENCY MEDICAL AND DENTAL COVERAGE", styles["SectionHeader"]))
    story.append(Paragraph(
        "Emergency Medical Coverage pays for necessary medical treatment received while "
        "traveling outside your home country when the treatment is required due to a sudden, "
        "unexpected illness or accidental injury occurring during your covered trip.",
        styles["BodyText"]
    ))

    story.append(Paragraph("2.1 Covered Medical Expenses", styles["SubHeader"]))
    medical_covered = [
        "Emergency hospitalization, surgery, and intensive care unit stays",
        "Physician and specialist consultation fees",
        "Prescription medications required for covered emergency condition",
        "Diagnostic tests including X-rays, MRI, CT scans, and laboratory work",
        "Emergency dental treatment for sudden onset of pain or accidental damage (up to $500)",
        "Ambulance transportation to nearest adequate medical facility",
        "Emergency medical evacuation to your home country hospital when medically necessary",
        "Repatriation of mortal remains to your home country in the event of death",
        "Return of dependent children to home country if you are hospitalized",
        "One round-trip economy airfare for a relative to accompany you if hospitalized 7+ days",
    ]
    for item in medical_covered:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Paragraph("2.2 Coverage Limits", styles["SubHeader"]))
    limits_data = [
        ["Benefit", "Limit"],
        ["Emergency Medical Expenses", "$500,000 per person per trip"],
        ["Emergency Medical Evacuation", "$1,000,000 per person per trip"],
        ["Emergency Dental", "$500 per person per trip"],
        ["Return of Dependent Children", "$10,000 per trip"],
        ["Bedside Companion Travel", "$1,500 round-trip economy"],
        ["Repatriation of Remains", "$25,000"],
    ]
    limits_table = Table(limits_data, colWidths=[10*cm, 7*cm])
    limits_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ebf4ff"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(limits_table)

    story.append(Paragraph("2.3 Important Requirements", styles["SubHeader"]))
    story.append(Paragraph(
        "You MUST contact our 24/7 Emergency Assistance line at +1-800-TRAVEL-1 before "
        "seeking non-emergency treatment abroad. For life-threatening emergencies, seek "
        "treatment immediately and notify us within 48 hours. Failure to contact us may "
        "result in reduced or denied benefits. All treatment must be medically necessary "
        "as determined by a licensed physician.",
        styles["BodyText"]
    ))

    # ── Section 3: Baggage ──────────────────────────────────────────────
    story.append(Paragraph("3. BAGGAGE LOSS, DAMAGE AND DELAY COVERAGE", styles["SectionHeader"]))

    story.append(Paragraph("3.1 Baggage Loss and Theft", styles["SubHeader"]))
    story.append(Paragraph(
        "Provides reimbursement for the actual cash value (original price minus depreciation) "
        "of baggage and personal effects that are lost, stolen, or damaged during your covered trip.",
        styles["BodyText"]
    ))
    baggage_limits = [
        "Total baggage coverage: $2,500 per person",
        "Single item limit: $500 per item (applies to each individual item)",
        "Electronics sub-limit: $1,000 total (cameras, laptops, tablets, phones)",
        "Jewelry and watches sub-limit: $500 total",
        "Sporting equipment: Requires separate Sports Equipment Rider",
        "Business equipment and samples: Not covered under this policy",
    ]
    for item in baggage_limits:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Paragraph("3.2 Baggage Delay", styles["SubHeader"]))
    story.append(Paragraph(
        "If your checked baggage is delayed by a common carrier (airline, ship, train) for "
        "more than 12 hours from your scheduled arrival time, we will reimburse you up to "
        "$300 for the emergency purchase of essential clothing and toiletries. You must "
        "keep all receipts and obtain a written Property Irregularity Report from the carrier.",
        styles["BodyText"]
    ))

    story.append(Paragraph("3.3 Items Excluded from Baggage Coverage", styles["SubHeader"]))
    baggage_exclusions = [
        "Cash, currency, credit cards, debit cards, or prepaid cards",
        "Passports, visas, and other travel or identity documents",
        "Tickets, vouchers, or other travel documents",
        "Contact lenses, eyeglasses, or hearing aids",
        "Perishable goods, food, or beverages",
        "Animals or living plants",
        "Motor vehicles or watercraft",
        "Items shipped separately from your person",
        "Contraband or illegal items",
    ]
    for item in baggage_exclusions:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    # ── Section 4: Travel Delay ─────────────────────────────────────────
    story.append(Paragraph("4. TRAVEL DELAY AND MISSED CONNECTION", styles["SectionHeader"]))

    story.append(Paragraph("4.1 Travel Delay Coverage", styles["SubHeader"]))
    story.append(Paragraph(
        "If your trip is delayed for 6 or more hours due to a covered reason, we will "
        "reimburse your reasonable additional expenses for meals, accommodation, and "
        "local transportation up to $200 per day with a maximum benefit of $1,000.",
        styles["BodyText"]
    ))
    delay_reasons = [
        "Common carrier delay (airline equipment failure, crew shortage, air traffic control)",
        "Severe weather conditions preventing safe travel",
        "Natural disaster causing closure of airport or transportation hub",
        "Security breach or evacuation at airport or transportation facility",
        "Hijacking or terrorist act affecting your common carrier",
    ]
    for reason in delay_reasons:
        story.append(Paragraph(f"• {reason}", styles["BulletItem"]))

    story.append(Paragraph("4.2 Missed Connection", styles["SubHeader"]))
    story.append(Paragraph(
        "If you miss a connecting flight, train, or cruise departure due to a covered "
        "travel delay, we will pay for additional transportation costs to reach your "
        "destination, and necessary hotel accommodation. Maximum benefit is $500 per "
        "incident. Delays must be documented in writing by the common carrier.",
        styles["BodyText"]
    ))

    # ── Section 5: General Terms ────────────────────────────────────────
    story.append(Paragraph("5. GENERAL POLICY TERMS AND CONDITIONS", styles["SectionHeader"]))

    story.append(Paragraph("5.1 Policy Eligibility", styles["SubHeader"]))
    eligibility = [
        "Policy must be purchased prior to departure from your home country",
        "Coverage is available to residents of the United States and Canada",
        "Travelers must be under 85 years of age at time of purchase",
        "Maximum trip length covered under this policy: 180 consecutive days",
        "Coverage begins at midnight on the day after the purchase date",
        "Pre-existing condition waiver must be purchased within 14 days of first trip deposit",
    ]
    for item in eligibility:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Paragraph("5.2 Universal Exclusions (All Coverage Sections)", styles["SubHeader"]))
    universal_exclusions = [
        "Intentional self-injury, suicide, or attempted suicide",
        "Mental health disorders, anxiety, or emotional conditions",
        "Participation in extreme or adventure sports without the Adventure Sports Rider",
        "Travel to countries under U.S. State Department Level 4 Travel Advisory",
        "Pregnancy complications occurring after the 26th week of pregnancy",
        "Incidents related to alcohol or drug intoxication",
        "Nuclear, chemical, biological, or radiological events",
        "Participation in professional or semi-professional athletic competition",
        "Loss or damage caused by gradual deterioration, wear and tear",
        "Acts of war, military conflict, or insurrection",
    ]
    for excl in universal_exclusions:
        story.append(Paragraph(f"• {excl}", styles["BulletItem"]))

    story.append(Paragraph("5.3 Free Look Period and Cancellation", styles["SubHeader"]))
    story.append(Paragraph(
        "You have a 10-day free look period from the date of policy purchase. If you are not "
        "satisfied for any reason, you may cancel the policy for a full refund provided no "
        "claims have been filed and your trip departure date has not occurred. After the free "
        "look period, the policy premium is non-refundable.",
        styles["BodyText"]
    ))

    story.append(Paragraph("5.4 Claims Process", styles["SubHeader"]))
    claims_steps = [
        "Step 1: Notify TravelAI Insurance within 72 hours of any incident",
        "Step 2: Download and complete the claim form at claims.travelai-insurance.com",
        "Step 3: Gather all supporting documentation (receipts, reports, statements)",
        "Step 4: Submit claim form and documentation via email, online portal, or mail",
        "Step 5: Claims are reviewed and processed within 10 business days of complete submission",
        "Step 6: Approved payments are issued via bank transfer or check within 5 business days",
    ]
    for step in claims_steps:
        story.append(Paragraph(f"• {step}", styles["BulletItem"]))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3*cm))

    # ── Contact Information ──────────────────────────────────────────────
    contact_data = [
        ["24/7 Emergency Assistance", "+1-800-TRAVEL-1 (+1-800-872-8351)"],
        ["Claims Portal", "claims.travelai-insurance.com"],
        ["Claims Email", "claims@travelai-insurance.com"],
        ["Customer Service", "+1-888-555-0199 (Mon-Fri 8am-8pm EST)"],
        ["Mailing Address", "TravelAI Insurance Group, 1 Insurance Plaza, New York, NY 10001"],
    ]
    contact_table = Table(contact_data, colWidths=[7*cm, 10*cm])
    contact_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a3c5e")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(contact_table)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "This policy document is issued by TravelAI Insurance Group, a fictional company "
        "created for demonstration purposes. Policy TAIG-COMP-2024-v3.1 © 2024 TravelAI Insurance Group.",
        styles["Footer"]
    ))

    doc.build(story)
    print(f"✅ Generated: {filename}")
    return filename


def generate_claims_guide():
    """Generate travel_insurance_claims_guide.pdf"""
    filename = os.path.join(OUTPUT_DIR, "travel_insurance_claims_guide.pdf")
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = build_styles()
    story = []

    story.append(Paragraph("TravelAI Insurance Group", styles["DocTitle"]))
    story.append(Paragraph("Complete Claims Guide & FAQ", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3c5e")))
    story.append(Spacer(1, 0.4*cm))

    # ── How to File Each Type of Claim ──────────────────────────────────
    story.append(Paragraph("HOW TO FILE YOUR CLAIM", styles["SectionHeader"]))
    story.append(Paragraph(
        "This guide explains exactly what documentation you need and the steps to follow "
        "for each type of insurance claim. Following these steps carefully will ensure your "
        "claim is processed as quickly as possible.",
        styles["BodyText"]
    ))

    story.append(Paragraph("Trip Cancellation Claim — Required Documents", styles["SubHeader"]))
    trip_cancel_docs = [
        "Completed TravelAI Claim Form (download at claims.travelai-insurance.com)",
        "Copy of your travel insurance policy or booking confirmation",
        "Proof of all prepaid, non-refundable trip costs (hotel invoices, flight tickets, tour receipts)",
        "Cancellation confirmations from each travel supplier showing amounts forfeited",
        "Documentation of covered reason:",
        "  — Medical: Attending physician's statement on letterhead confirming diagnosis and inability to travel",
        "  — Death: Certified death certificate",
        "  — Job loss: Termination letter from employer on company letterhead",
        "  — Jury duty: Copy of jury summons",
        "  — Weather/disaster: Official news report or government declaration",
        "Bank statement showing original payment for trip costs",
    ]
    for item in trip_cancel_docs:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Paragraph("Medical Claim — Required Documents", styles["SubHeader"]))
    medical_docs = [
        "Completed TravelAI Claim Form",
        "All original itemized medical bills and receipts (not copies)",
        "Attending physician's diagnosis, treatment notes, and discharge summary",
        "Proof of payment for all medical expenses claimed",
        "Prescription receipts with physician name and medication details",
        "Emergency Assistance case number (if you called +1-800-TRAVEL-1)",
        "Your primary health insurance Explanation of Benefits (EOB) if applicable",
        "Completed Medical Authorization form allowing release of medical records",
    ]
    for item in medical_docs:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))


    story.append(Paragraph("Baggage Loss/Theft Claim — Required Documents", styles["SubHeader"]))
    baggage_docs = [
        "Completed TravelAI Claim Form",
        "Property Irregularity Report (PIR) from airline for lost checked baggage",
        "Police report filed within 24 hours for stolen items (required for all theft claims)",
        "Proof of ownership for claimed items (purchase receipts, credit card statements, photos)",
        "Airline's written confirmation of the amount they compensated you",
        "List of all lost or stolen items with estimated value and date of purchase",
        "For damaged items: photographs clearly showing the damage",
    ]
    for item in baggage_docs:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    story.append(Paragraph("Travel Delay Claim — Required Documents", styles["SubHeader"]))
    delay_docs = [
        "Completed TravelAI Claim Form",
        "Written confirmation from carrier (airline, train company) stating delay reason and duration",
        "Original receipts for all claimed expenses (meals, hotel, transportation)",
        "Your original travel itinerary showing scheduled vs. actual departure/arrival times",
        "Hotel invoice if overnight accommodation was required due to delay",
    ]
    for item in delay_docs:
        story.append(Paragraph(f"• {item}", styles["BulletItem"]))

    # ── Claims Timeline ──────────────────────────────────────────────────
    story.append(Paragraph("CLAIMS TIMELINE", styles["SectionHeader"]))
    timeline_data = [
        ["Step", "Action", "Timeframe"],
        ["1", "Incident occurs — notify TravelAI Insurance", "Within 72 hours"],
        ["2", "Gather all required documentation", "1-7 days"],
        ["3", "Submit complete claim via portal or email", "Within 90 days of incident"],
        ["4", "TravelAI reviews your claim", "Within 10 business days"],
        ["5", "TravelAI may request additional documents", "If needed"],
        ["6", "Claim decision issued", "Within 15 business days"],
        ["7", "Approved payment processed", "Within 5 business days of approval"],
    ]
    timeline_table = Table(timeline_data, colWidths=[1.5*cm, 11*cm, 5*cm])
    timeline_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(timeline_table)

    # ── Frequently Asked Questions ───────────────────────────────────────
    story.append(Paragraph("FREQUENTLY ASKED QUESTIONS", styles["SectionHeader"]))

    faqs = [
        (
            "Q: What is considered a pre-existing condition?",
            "A pre-existing condition is any illness, injury, or medical condition for which you "
            "received medical advice, diagnosis, care, or treatment within 180 days before the "
            "effective date of your policy. Common examples include: diabetes, heart disease, "
            "asthma, cancer (in treatment or remission), back problems, and high blood pressure "
            "that required medication adjustment in the past 180 days."
        ),
        (
            "Q: Am I covered if I travel while pregnant?",
            "Yes, but with limitations. Routine prenatal care and normal delivery are not covered. "
            "Unexpected pregnancy complications are covered up to the 26th week of pregnancy. "
            "We strongly recommend consulting your physician before traveling while pregnant and "
            "confirming your specific coverage with our customer service team."
        ),
        (
            "Q: Does my policy cover adventure sports like skiing or scuba diving?",
            "Standard policies do not cover injuries from extreme or adventure sports. If you plan "
            "to participate in skiing, snowboarding, scuba diving, bungee jumping, rock climbing, "
            "white-water rafting, or similar activities, you must purchase the Adventure Sports "
            "Rider as an add-on to your base policy. This rider must be purchased before departure."
        ),
        (
            "Q: What happens if I need medical treatment in a country with very high costs?",
            "Contact our Emergency Assistance line (+1-800-TRAVEL-1) before seeking non-emergency "
            "treatment. We can pre-authorize treatment, arrange direct billing with hospitals in "
            "many countries, and organize medical evacuation if the local facilities are inadequate. "
            "We have a global network of preferred medical providers in over 150 countries."
        ),
        (
            "Q: My airline lost my luggage. What should I do?",
            "Immediately before leaving the baggage claim area: (1) Report the loss to the airline "
            "baggage desk and obtain a written Property Irregularity Report (PIR) with a reference "
            "number. (2) Keep the PIR — you cannot file a claim without it. (3) If your bag is "
            "delayed 12+ hours, keep receipts for essential purchases (clothing, toiletries) up to "
            "$300. (4) If your bag is permanently lost, file a claim with both the airline and "
            "TravelAI Insurance, providing the PIR and a list of items with estimated values."
        ),
        (
            "Q: My flight was cancelled. Can I claim for my hotel that night?",
            "Yes, if the cancellation was caused by a covered reason (mechanical failure, severe "
            "weather, etc.) and resulted in a delay of 6+ hours. Keep your hotel receipt, and get "
            "written confirmation from the airline stating the reason and duration of the delay. "
            "Note: if the airline provides complimentary hotel accommodation, you cannot claim "
            "additionally from TravelAI Insurance for the same expense."
        ),
        (
            "Q: How long does it take to get paid after I submit a claim?",
            "Once we receive your complete claim with all required documentation, we review it "
            "within 10 business days. If additional information is needed, we will contact you "
            "within 5 business days of submission. After approval, payment is issued within 5 "
            "business days via bank transfer (ACH) or check."
        ),
        (
            "Q: Can I extend my policy if my trip is longer than expected?",
            "Yes, you can request a policy extension if your trip is extended due to circumstances "
            "beyond your control (medical emergency, natural disaster, carrier delay). Contact our "
            "customer service team before your original policy expiry date. Extensions are granted "
            "at our discretion and may require additional premium payment."
        ),
    ]

    for question, answer in faqs:
        story.append(Paragraph(question, styles["SubHeader"]))
        story.append(Paragraph(answer, styles["BodyText"]))
        story.append(Spacer(1, 0.2*cm))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "For assistance: Emergency +1-800-TRAVEL-1 | Customer Service +1-888-555-0199 | "
        "claims.travelai-insurance.com | TravelAI Insurance Group © 2024",
        styles["Footer"]
    ))

    doc.build(story)
    print(f"✅ Generated: {filename}")
    return filename


if __name__ == "__main__":
    print("Generating travel insurance policy PDFs...")
    f1 = generate_comprehensive_policy()
    f2 = generate_claims_guide()
    print(f"\n✅ PDFs saved to: {os.path.dirname(f1)}")
    print("   1. travel_insurance_comprehensive_policy.pdf")
    print("   2. travel_insurance_claims_guide.pdf")