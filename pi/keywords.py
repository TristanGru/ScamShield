"""
keywords.py — Scam keyword list used as fallback detection when Gemini API is unavailable.
Matching is case-insensitive and whole-word only (BL-002).
"""

SCAM_KEYWORDS = [
    # Government impersonation
    "IRS", "internal revenue", "social security", "medicare", "medicaid",
    "social security administration", "SSA", "CRA",

    # Payment methods scammers demand
    "gift card", "gift cards", "wire transfer", "bitcoin", "cryptocurrency",
    "crypto", "zelle", "western union", "money order", "prepaid card",

    # Legal threats
    "warrant", "arrest warrant", "arrest", "lawsuit", "sued",
    "deportation", "deported", "federal agent", "police officer",

    # Secrecy / urgency tactics
    "don't tell anyone", "do not tell anyone", "keep this confidential",
    "keep this secret", "act now", "act immediately", "immediately",
    "right now", "today only", "limited time", "urgent",

    # Prize / lottery scams
    "prize", "lottery", "you've won", "you have won", "claim your reward",
    "congratulations you", "selected winner", "jackpot",

    # Tech support scams
    "tech support", "technical support", "virus", "infected",
    "remote access", "your computer", "microsoft", "apple support",
    "windows defender",

    # Grandparent / family emergency scams
    "grandchild", "grandson", "granddaughter", "bail", "jail",
    "accident", "hospital", "lawyer calling on behalf",

    # Refund / overpayment scams
    "refund", "overpaid", "send money", "send the money",
    "processing fee", "transfer fee", "release fee",

    # Generic high-pressure
    "do not hang up", "don't hang up", "stay on the line",
    "this is your final notice", "final notice", "last warning",
]
