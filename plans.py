"""
plans.py
----------
Single source of truth for the pricing catalog, used by both the
/pricing page and the account page. No real payment processor is wired
up yet — selecting a plan here just updates the user's `plan` /
`billing_cycle` fields for demo purposes. Swapping in real billing
(Stripe, Paddle, etc.) later only needs to touch account.py.
"""

PLANS = [
    {
        "id": "free",
        "name": "Free",
        "tagline": "Try the pipeline on your own test targets.",
        "price_monthly": 0,
        "price_annual": 0,
        "scans_per_day": 3,
        "badge": None,
        "highlight": False,
        "features": [
            "3 scans / 24h",
            "All 5 scan modules",
            "Live scan log",
            "7-day scan history",
        ],
    },
    {
        "id": "student",
        "name": "Student",
        "tagline": "Discounted access for coursework and graduation projects.",
        "price_monthly": 4,
        "price_annual": 40,
        "scans_per_day": 15,
        "badge": "Student ID required",
        "highlight": False,
        "features": [
            "15 scans / 24h",
            "All 5 scan modules",
            "Live scan log",
            "30-day scan history",
            "Email support",
        ],
    },
    {
        "id": "pro",
        "name": "Pro",
        "tagline": "For freelancers and small security teams running scans regularly.",
        "price_monthly": 19,
        "price_annual": 190,
        "scans_per_day": 100,
        "badge": "Most popular",
        "highlight": True,
        "features": [
            "100 scans / 24h",
            "All 5 scan modules",
            "Live scan log",
            "Unlimited scan history",
            "Priority email support",
            "JSON report export",
        ],
    },
    {
        "id": "team",
        "name": "Team",
        "tagline": "Shared usage and higher limits for a whole team.",
        "price_monthly": 49,
        "price_annual": 490,
        "scans_per_day": 500,
        "badge": None,
        "highlight": False,
        "features": [
            "500 scans / 24h",
            "All 5 scan modules",
            "Live scan log",
            "Unlimited scan history",
            "Priority support",
            "JSON report export",
            "Shared team scan history",
        ],
    },
]

PLAN_BY_ID = {p["id"]: p for p in PLANS}


def get_plan(plan_id):
    return PLAN_BY_ID.get(plan_id)
