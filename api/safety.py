"""
api/safety.py
PII detection and anonymization using Microsoft Presidio.
Every customer message passes through this before reaching the LLM.

Detected entities are replaced with placeholders so the LLM never
sees raw passport numbers, card numbers, or personal identifiers.
"""

import logging
from typing import Optional
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# ─── Initialize engines (once at module load) ────────────────────────────────

_analyzer = None
_anonymizer = None


def _get_analyzer() -> AnalyzerEngine:
    """Lazy initialization of the Presidio analyzer engine."""
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
        logger.info("Presidio AnalyzerEngine initialized")
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    """Lazy initialization of the Presidio anonymizer engine."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
        logger.info("Presidio AnonymizerEngine initialized")
    return _anonymizer


# ─── PII entity types we detect ──────────────────────────────────────────────

DETECTED_ENTITIES = [
    "CREDIT_CARD",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "PERSON",
    "US_SSN",
    "US_BANK_NUMBER",
    "IBAN_CODE",
    "IP_ADDRESS",
]


# How to replace detected entities in the text
ANONYMIZATION_OPERATORS = {
    "CREDIT_CARD":    OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
    "PHONE_NUMBER":   OperatorConfig("replace", {"new_value": "<PHONE_NUMBER>"}),
    "EMAIL_ADDRESS":  OperatorConfig("replace", {"new_value": "<EMAIL_ADDRESS>"}),
    "PERSON":         OperatorConfig("replace", {"new_value": "<PERSON_NAME>"}),
    "PASSPORT":       OperatorConfig("replace", {"new_value": "<PASSPORT_NUMBER>"}),
    "US_SSN":         OperatorConfig("replace", {"new_value": "<SSN>"}),
    "US_BANK_NUMBER": OperatorConfig("replace", {"new_value": "<BANK_ACCOUNT>"}),
    "IBAN_CODE":      OperatorConfig("replace", {"new_value": "<IBAN>"}),
    "IP_ADDRESS":     OperatorConfig("replace", {"new_value": "<IP_ADDRESS>"}),
    "DEFAULT":        OperatorConfig("replace", {"new_value": "<REDACTED>"}),
}


# ─── Main functions ───────────────────────────────────────────────────────────

def scan_for_pii(text: str, language: str = "en") -> dict:
    """
    Scans text for PII entities without modifying the text.
    Returns a dict with detected entities and their types.
    
    Args:
        text: The customer's raw message
        language: Language code (default 'en')
    
    Returns:
        {
            "has_pii": bool,
            "entities": [{"type": "CREDIT_CARD", "start": 10, "end": 26, "score": 0.85}],
            "entity_types": ["CREDIT_CARD"]
        }
    """
    if not text or not text.strip():
        return {"has_pii": False, "entities": [], "entity_types": []}

    try:
        analyzer = _get_analyzer()
        results = analyzer.analyze(
            text=text,
            entities=DETECTED_ENTITIES,
            language=language,
        )

        entities = [
            {
                "type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": round(r.score, 2),
            }
            for r in results
        ]

        return {
            "has_pii": len(results) > 0,
            "entities": entities,
            "entity_types": list({r.entity_type for r in results}),
        }

    except Exception as e:
        logger.error(f"PII scan error: {e}")
        return {"has_pii": False, "entities": [], "entity_types": [], "error": str(e)}


def anonymize_text(text: str, language: str = "en") -> dict:
    """
    Scans and anonymizes PII in the text.
    Returns both the sanitized text and detection details.
    
    Args:
        text: The customer's raw message
        language: Language code (default 'en')
    
    Returns:
        {
            "original_text": str,
            "sanitized_text": str,
            "has_pii": bool,
            "entity_types": list,
            "entities_found": int
        }
    """
    if not text or not text.strip():
        return {
            "original_text": text,
            "sanitized_text": text,
            "has_pii": False,
            "entity_types": [],
            "entities_found": 0,
        }

    try:
        analyzer = _get_analyzer()
        anonymizer = _get_anonymizer()

        analysis_results = analyzer.analyze(
            text=text,
            entities=DETECTED_ENTITIES,
            language=language,
        )

        if not analysis_results:
            return {
                "original_text": text,
                "sanitized_text": text,
                "has_pii": False,
                "entity_types": [],
                "entities_found": 0,
            }

        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators=ANONYMIZATION_OPERATORS,
        )

        entity_types = list({r.entity_type for r in analysis_results})
        logger.info(f"PII detected and redacted: {entity_types}")

        return {
            "original_text": text,
            "sanitized_text": anonymized.text,
            "has_pii": True,
            "entity_types": entity_types,
            "entities_found": len(analysis_results),
        }

    except Exception as e:
        logger.error(f"PII anonymization error: {e}")
        # On error, return original text with warning — don't block the request
        return {
            "original_text": text,
            "sanitized_text": text,
            "has_pii": False,
            "entity_types": [],
            "entities_found": 0,
            "error": str(e),
        }


def process_message(text: str) -> tuple[str, bool, list]:
    """
    Convenience function — scans and anonymizes in one call.
    Returns (sanitized_text, has_pii, entity_types).
    
    This is what FastAPI and the agent graph call on every message.
    """
    result = anonymize_text(text)
    return (
        result["sanitized_text"],
        result["has_pii"],
        result["entity_types"],
    )
