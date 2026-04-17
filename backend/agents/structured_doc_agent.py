"""
Agent 8 — Structured Document Semantic Validator

Detects text-level forgeries in French payslips (Bulletins de Paie)
that image forensic agents cannot catch:

  1. Field Extraction:  Parses key fields from OCR text using regex
  2. Format Validation: APE, SIRET, SS number format + checksum
  3. Character Class:   Letters in numeric/currency fields = instant flag
  4. Arithmetic Check:  Row-level and document-level math verification

Targets NaviDoMass-style forgery patterns: same-font character
replacement, number inflation, identity field swaps.

Scope: French payslips only. Offline checksums only (no API calls).
Arithmetic tolerance: ±0.05 EUR.
"""

import re
from typing import Optional

from loguru import logger

# ═══════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════

ARITHMETIC_TOLERANCE = 0.05  # EUR

# OCR confusion map: characters commonly misread in numeric fields
_OCR_DIGIT_FIXES = {
    "O": "0", "o": "0",
    "l": "1", "I": "1", "|": "1",
    "S": "5", "s": "5",
    "B": "8",
    "Z": "2", "z": "2",
    "G": "6",
    "T": "7",
    "g": "9",
}

# Characters that are NEVER valid in a pure numeric/currency field
_ALPHA_IN_NUMERIC = re.compile(r"[A-Za-z]")
# Valid characters in French currency: digits, spaces, comma, dot, €, -
_VALID_CURRENCY_CHARS = re.compile(r"^[\d\s,.\-€]+$")
# Valid characters in percentage fields
_VALID_PERCENT_CHARS = re.compile(r"^[\d\s,.%]+$")


# ═══════════════════════════════════════════════════════════
#  French Number Parsing
# ═══════════════════════════════════════════════════════════

def _parse_french_number(raw: str) -> tuple[Optional[float], list[str]]:
    """
    Parse a French-format number string to float.

    French format: 2 341,78  (space=thousands, comma=decimal)

    Returns:
        (parsed_float_or_None, list_of_character_anomalies)
    """
    anomalies = []
    if not raw or not raw.strip():
        return None, []

    cleaned = raw.strip().replace("€", "").replace("%", "").strip()

    if not cleaned:
        return None, []

    # Check for alphabetic characters in the numeric field
    alpha_matches = list(_ALPHA_IN_NUMERIC.finditer(cleaned))
    if alpha_matches:
        for m in alpha_matches:
            anomalies.append(
                f"Character '{m.group()}' at position {m.start()} "
                f"in numeric field '{raw.strip()}'"
            )

    # Try to normalize OCR confusions for arithmetic
    normalized = cleaned
    for bad_char, good_char in _OCR_DIGIT_FIXES.items():
        normalized = normalized.replace(bad_char, good_char)

    # Remove thousands separators (spaces), convert comma to dot
    normalized = normalized.replace(" ", "")
    normalized = normalized.replace(",", ".")

    # Remove any remaining non-numeric chars (except dot and minus)
    normalized = re.sub(r"[^\d.\-]", "", normalized)

    try:
        value = float(normalized)
        return value, anomalies
    except (ValueError, TypeError):
        anomalies.append(f"Cannot parse '{raw.strip()}' as number")
        return None, anomalies


def _parse_french_percent(raw: str) -> tuple[Optional[float], list[str]]:
    """Parse a French percentage like '6,55%' to 0.0655."""
    value, anomalies = _parse_french_number(raw)
    if value is not None:
        return value / 100.0, anomalies
    return None, anomalies


# ═══════════════════════════════════════════════════════════
#  Field Extraction — French Payslip
# ═══════════════════════════════════════════════════════════

def _extract_payslip_fields(ocr_text: str) -> dict:
    """
    Extract structured fields from French payslip OCR text.

    Uses tiered regex: strict patterns first, then OCR-noise-tolerant
    fallbacks with flexible whitespace and character substitution.

    Returns dict with extracted fields and raw values for validation.
    """
    text = ocr_text
    fields = {
        "ape_code": None,
        "siret": None,
        "ss_number": None,
        "postal_code": None,
        "salaire_brut_raw": None,
        "net_a_payer_raw": None,
        "net_imposable_raw": None,
        "total_cotisations_raw": None,
        "cotisation_rows": [],
        "salaire_base_raw": None,
        "salaire_base_heures": None,
        "salaire_base_taux": None,
        "salaire_base_montant": None,
    }

    # ── APE code ──
    # Try strict pattern first, then broader fallback
    ape_patterns = [
        r"(?:num[eé]ro\s*)?ape\s*[:.]?\s*([A-Za-z0-9]{3,6})",
        r"(?:code\s*)?(?:ape|naf)\s*[:./\-]?\s*([A-Za-z0-9]{3,6})",
        r"ape\s*([A-Za-z0-9]{4,5})",  # minimal context
    ]
    for pat in ape_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fields["ape_code"] = m.group(1).strip()
            break

    # ── SIRET ──
    # Strict: label + digits; Fallback: any standalone 14-digit sequence
    siret_patterns = [
        r"siret\s*[:.]?\s*([\d\s]{14,20})",
        r"siret\s*[:/\-.]?\s*([\d\s]{14,22})",
    ]
    for pat in siret_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fields["siret"] = re.sub(r"\s+", "", m.group(1).strip())
            break
    # Fallback: naked 14-digit sequence near "siret" keyword
    if not fields["siret"]:
        m = re.search(r"(\d{14})", text)
        if m:
            # Only accept if near the word "siret" (within 100 chars)
            pos = m.start()
            context = text[max(0, pos - 100):pos + 100].lower()
            if "siret" in context:
                fields["siret"] = m.group(1)

    # ── SS Number (Numéro SS / Sécurité Sociale) ──
    ss_patterns = [
        r"(?:num[eé]ro\s*)?(?:ss|s\.s\.|s[eé]curit[eé]\s*sociale)\s*[:.]?\s*([0-9A-Za-z][\d\s]{12,18})",
        r"(?:n[°o]?\s*)?(?:ss|s\.?s\.?)\s*[:.]?\s*([12][\d\s]{12,18})",  # starts with 1 or 2
    ]
    for pat in ss_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fields["ss_number"] = re.sub(r"\s+", "", m.group(1).strip())
            break

    # ── Postal Code (CP et Ville) ──
    cp_match = re.search(
        r"cp\s*(?:et\s*ville)?\s*[:.]?\s*(\d{5})",
        text, re.IGNORECASE
    )
    if cp_match:
        fields["postal_code"] = cp_match.group(1)

    # ── SALAIRE BRUT ──
    # Tiered: strict → flexible whitespace → broad fallback
    brut_patterns = [
        r"salaire\s*brut\s*[^\d]*([\d\s,.]+?)(?:\s*€|\s*$)",
        r"sal(?:aire)?\s*brut\s*[:.]?\s*([\d][\d\s,.]{2,12})(?:\s*€|\s|$)",
        r"brut\s*[:=]?\s*([\d][\d\s,.]{2,12})(?:\s*€|\s|$)",
    ]
    for pat in brut_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            # Sanity: must have at least 1 digit
            if re.search(r"\d", val):
                fields["salaire_brut_raw"] = val
                break

    # ── Salaire de base (heures, taux, montant) ──
    base_patterns = [
        (r"salaire\s*de\s*base\s+"
         r"([\d\s,.A-Za-z]+?)\s+"
         r"([\d\s,.A-Za-z]+?)\s*€?\s+"
         r"([\d\s,.A-Za-z]+?)(?:\s*€|\s*$)"),
        (r"sal(?:aire)?\s*(?:de\s*)?base\s*"
         r"([\d][\d\s,.]{0,8})\s+"
         r"([\d][\d\s,.]{0,8})\s*€?\s+"
         r"([\d][\d\s,.]{0,10})(?:\s*€|\s|$)"),
    ]
    for pat in base_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            fields["salaire_base_heures"] = m.group(1).strip()
            fields["salaire_base_taux"] = m.group(2).strip()
            fields["salaire_base_montant"] = m.group(3).strip()
            break

    # ── Net à payer ──
    net_patterns = [
        r"net\s*[àaÀ]\s*payer\s*[^\dA-Za-z]*([\dA-Za-z][\d\s,.A-Za-z]*?)(?:\s*€|\s*$)",
        r"net\s*[àaÀ]?\s*pay[eé]r?\s*[:=]?\s*([\d][\d\s,.]{2,12})(?:\s*€|\s|$)",
        r"net\s*(?:[àaÀ]\s*)?pay(?:er)?\s*[:./]?\s*([\d][\d\s,.]{2,12})",
    ]
    for pat in net_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if re.search(r"\d", val):
                fields["net_a_payer_raw"] = val
                break

    # ── Net imposable ──
    netimp_patterns = [
        r"net\s*imposable\s*[^\dA-Za-z]*([\dA-Za-z][\d\s,.A-Za-z]*?)(?:\s*€|\s*$)",
        r"net\s*impos(?:able)?\s*[:=]?\s*([\d][\d\s,.]{2,12})(?:\s*€|\s|$)",
    ]
    for pat in netimp_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if re.search(r"\d", val):
                fields["net_imposable_raw"] = val
                break

    # ── TOTAL des cotisations ──
    total_patterns = [
        r"total\s*(?:des\s*)?cotisations\s*[^\d]*([\d\s,.]+?)(?:\s*€|\s*$)",
        r"total\s*(?:des\s*)?cot(?:isations)?\s*[:=]?\s*([\d][\d\s,.]{2,12})",
    ]
    for pat in total_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            if re.search(r"\d", val):
                fields["total_cotisations_raw"] = val
                break

    # ── Cotisation rows ──
    # Pattern: label  base_amount €?  taux%  montant €?
    cot_pattern = re.compile(
        r"([A-Za-zéèêëàâôûùîïç\s./-]+?)\s+"       # label
        r"([\d\s,.]+?)\s*€?\s+"                      # base
        r"([\d\s,.]+?)\s*%\s+"                        # taux
        r"([\d\s,.A-Za-z]+?)(?:\s*€|\s*$)",           # montant (€ optional)
        re.IGNORECASE | re.MULTILINE
    )
    for m in cot_pattern.finditer(text):
        label = m.group(1).strip()
        # Skip headers and irrelevant lines
        if any(skip in label.lower() for skip in ["cotisations", "base", "taux", "montant", "part"]):
            continue
        fields["cotisation_rows"].append({
            "label": label,
            "base_raw": m.group(2).strip(),
            "taux_raw": m.group(3).strip(),
            "montant_raw": m.group(4).strip(),
        })

    return fields


# ═══════════════════════════════════════════════════════════
#  Format Validators
# ═══════════════════════════════════════════════════════════

def _validate_ape(ape_code: str) -> list[str]:
    """Validate French APE/NAF code format: 4 digits + 1 letter."""
    violations = []
    if not ape_code:
        return violations

    pattern = re.compile(r"^\d{4}[A-Za-z]$")
    if not pattern.match(ape_code):
        violations.append(
            f"APE code '{ape_code}' is INVALID — must be 4 digits + 1 letter "
            f"(e.g. '2229A'). This is a definitive format violation."
        )
    return violations


def _luhn_check(number_str: str) -> bool:
    """Standard Luhn checksum validation."""
    try:
        digits = [int(d) for d in number_str]
    except ValueError:
        return False

    # Reverse digits
    digits = digits[::-1]
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:  # double every second digit from the right
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _validate_siret(siret: str) -> list[str]:
    """Validate French SIRET number: 14 digits + Luhn checksum."""
    violations = []
    if not siret:
        return violations

    # Strip non-digits
    digits_only = re.sub(r"\D", "", siret)

    if len(digits_only) != 14:
        violations.append(
            f"SIRET '{siret}' has {len(digits_only)} digits — must be exactly 14"
        )
        return violations

    if not _luhn_check(digits_only):
        violations.append(
            f"SIRET '{siret}' FAILS Luhn checksum — "
            f"the number has been modified and is mathematically invalid"
        )

    return violations


def _validate_ss_number(ss: str) -> list[str]:
    """
    Validate French SS number (NIR).

    Format: G YY MM DD CCC NNN KK (15 digits total)
    - G: gender (1=male, 2=female)
    - YY: birth year (00-99)
    - MM: birth month (01-12, or 20+ for special)
    - DD: department (01-95, 99 for overseas, or 2A/2B for Corsica)
    - CCC: commune (001-999)
    - NNN: order number (001-999)
    - KK: control key = 97 - (first 13 digits mod 97)
    """
    violations = []
    if not ss:
        return violations

    digits_only = re.sub(r"\D", "", ss)

    if len(digits_only) < 13:
        violations.append(
            f"SS number '{ss}' is too short ({len(digits_only)} digits, need 13+2)"
        )
        return violations

    # Gender check
    gender = digits_only[0]
    if gender not in ("1", "2"):
        violations.append(
            f"SS number '{ss}' has invalid gender digit '{gender}' — must be 1 (male) or 2 (female)"
        )

    # Month check
    try:
        month = int(digits_only[3:5])
        if month < 1 or (month > 12 and month < 20) or month > 42:
            violations.append(
                f"SS number '{ss}' has invalid birth month '{month:02d}'"
            )
    except ValueError:
        pass

    # Control key check (if we have 15 digits)
    if len(digits_only) >= 15:
        try:
            base_13 = int(digits_only[:13])
            key = int(digits_only[13:15])
            expected_key = 97 - (base_13 % 97)
            if key != expected_key:
                violations.append(
                    f"SS number '{ss}' FAILS control key check — "
                    f"key is {key:02d}, expected {expected_key:02d}. "
                    f"The number has been modified."
                )
        except ValueError:
            pass

    return violations


# ═══════════════════════════════════════════════════════════
#  Character Class Checker
# ═══════════════════════════════════════════════════════════

def _check_character_classes(fields: dict) -> list[str]:
    """
    Scan all numeric/currency fields for alphabetic characters.

    This is the highest-confidence check: letters like 'B' or 'AS'
    in a monetary field is DEFINITIVE proof of tampering.
    """
    anomalies = []

    # Fields that must be purely numeric/currency
    currency_fields = [
        ("salaire_brut_raw", "SALAIRE BRUT"),
        ("net_a_payer_raw", "Net à payer"),
        ("net_imposable_raw", "Net imposable"),
        ("total_cotisations_raw", "TOTAL cotisations"),
        ("salaire_base_heures", "Salaire de base (heures)"),
        ("salaire_base_taux", "Salaire de base (taux)"),
        ("salaire_base_montant", "Salaire de base (montant)"),
    ]

    for field_key, field_label in currency_fields:
        raw = fields.get(field_key)
        if not raw:
            continue

        cleaned = raw.replace("€", "").replace("%", "").strip()
        if not cleaned:
            continue

        if not _VALID_CURRENCY_CHARS.match(cleaned):
            # Find the offending characters
            offending = [
                c for c in cleaned
                if c.isalpha()
            ]
            if offending:
                anomalies.append(
                    f"CRITICAL: '{field_label}' contains alphabetic character(s) "
                    f"{offending} in value '{raw}' — "
                    f"letters in a monetary field are definitive proof of tampering"
                )

    # Check cotisation rows
    for i, row in enumerate(fields.get("cotisation_rows", [])):
        for col_key, col_label in [("base_raw", "Base"), ("taux_raw", "Taux"), ("montant_raw", "Montant")]:
            raw = row.get(col_key, "")
            if not raw:
                continue
            cleaned = raw.replace("€", "").replace("%", "").strip()
            if cleaned and not _VALID_CURRENCY_CHARS.match(cleaned):
                offending = [c for c in cleaned if c.isalpha()]
                if offending:
                    anomalies.append(
                        f"CRITICAL: Cotisation row '{row.get('label', i)}' "
                        f"{col_label} contains '{offending}' in '{raw}'"
                    )

    return anomalies


# ═══════════════════════════════════════════════════════════
#  Arithmetic Consistency Checker
# ═══════════════════════════════════════════════════════════

def _check_arithmetic(fields: dict) -> list[str]:
    """
    Verify mathematical relationships in French payslip.

    Tolerance: ±0.05 EUR (handles rounding + OCR noise).
    """
    errors = []
    tol = ARITHMETIC_TOLERANCE

    # ── Check 1: Salaire de base = heures × taux ──
    if fields.get("salaire_base_heures") and fields.get("salaire_base_taux") and fields.get("salaire_base_montant"):
        heures, _ = _parse_french_number(fields["salaire_base_heures"])
        taux, _ = _parse_french_number(fields["salaire_base_taux"])
        montant, _ = _parse_french_number(fields["salaire_base_montant"])

        if heures is not None and taux is not None and montant is not None:
            expected = round(heures * taux, 2)
            if abs(expected - montant) > tol:
                errors.append(
                    f"Salaire de base arithmetic error: "
                    f"{heures} × {taux} = {expected:.2f}, "
                    f"but document shows {montant:.2f} "
                    f"(difference: {abs(expected - montant):.2f}€)"
                )

    # ── Check 2: Per-row cotisation: Base × Taux% ≈ Montant ──
    for row in fields.get("cotisation_rows", []):
        base_val, _ = _parse_french_number(row.get("base_raw", ""))
        taux_val, _ = _parse_french_percent(row.get("taux_raw", ""))
        montant_val, _ = _parse_french_number(row.get("montant_raw", ""))

        if base_val is not None and taux_val is not None and montant_val is not None:
            expected = round(base_val * taux_val, 2)
            if abs(expected - montant_val) > tol:
                errors.append(
                    f"Cotisation '{row.get('label', '?')}' arithmetic error: "
                    f"{base_val:.2f} × {taux_val*100:.2f}% = {expected:.2f}€, "
                    f"but document shows {montant_val:.2f}€ "
                    f"(difference: {abs(expected - montant_val):.2f}€)"
                )

    # ── Check 3: SALAIRE BRUT - TOTAL cotisations ≈ Net à payer ──
    brut_val, _ = _parse_french_number(fields.get("salaire_brut_raw", ""))
    total_cot, _ = _parse_french_number(fields.get("total_cotisations_raw", ""))
    net_val, _ = _parse_french_number(fields.get("net_a_payer_raw", ""))

    if brut_val is not None and total_cot is not None and net_val is not None:
        expected_net = round(brut_val - total_cot, 2)
        if abs(expected_net - net_val) > tol:
            errors.append(
                f"Net pay arithmetic error: "
                f"BRUT ({brut_val:.2f}) - Cotisations ({total_cot:.2f}) = {expected_net:.2f}, "
                f"but Net à payer shows {net_val:.2f} "
                f"(difference: {abs(expected_net - net_val):.2f}€)"
            )

    return errors


# ═══════════════════════════════════════════════════════════
#  Main Entry Point
# ═══════════════════════════════════════════════════════════

def analyze_structured_document(ocr_text: str, doc_type: str = "other") -> dict:
    """
    Run structured semantic validation on a document's OCR text.

    Currently supports French payslips (salary_slip).
    Returns a score and detailed anomaly list.

    Args:
        ocr_text: Raw OCR text from the document
        doc_type: Classification result from classifier

    Returns:
        dict with: structured_validation_score, fields_extracted,
                   format_violations, character_anomalies,
                   arithmetic_errors, anomaly_count, details
    """
    result = {
        "structured_validation_score": 0.0,
        "fields_extracted": {},
        "format_violations": [],
        "character_anomalies": [],
        "arithmetic_errors": [],
        "anomaly_count": 0,
        "details": [],
        "skipped": False,
        "doc_family": "unsupported",
    }

    # Only run for supported document families
    if doc_type not in ("salary_slip",):
        result["skipped"] = True
        result["details"].append(
            f"Structured validation skipped — doc_type '{doc_type}' not yet supported. "
            f"Currently supports: salary_slip (French payslips)."
        )
        logger.info(f"StructuredDoc Agent: Skipped — doc_type '{doc_type}' not supported")
        return result

    result["doc_family"] = "french_payslip"

    # ── Step 1: Extract fields ──
    logger.info("StructuredDoc Agent: Extracting French payslip fields...")
    fields = _extract_payslip_fields(ocr_text)
    result["fields_extracted"] = {
        k: v for k, v in fields.items()
        if k != "cotisation_rows"  # summarize rows separately
    }
    result["fields_extracted"]["cotisation_row_count"] = len(fields.get("cotisation_rows", []))

    logger.info(
        f"StructuredDoc Agent: Extracted — "
        f"APE={fields.get('ape_code')} "
        f"SIRET={fields.get('siret')} "
        f"SS={fields.get('ss_number')} "
        f"brut={fields.get('salaire_brut_raw')} "
        f"net={fields.get('net_a_payer_raw')} "
        f"cotisation_rows={len(fields.get('cotisation_rows', []))}"
    )

    # ── Step 2: Format validation ──
    format_violations = []
    format_violations.extend(_validate_ape(fields.get("ape_code")))
    format_violations.extend(_validate_siret(fields.get("siret")))
    format_violations.extend(_validate_ss_number(fields.get("ss_number")))
    result["format_violations"] = format_violations

    for v in format_violations:
        logger.warning(f"StructuredDoc Agent: FORMAT VIOLATION — {v}")

    # ── Step 3: Character class check ──
    char_anomalies = _check_character_classes(fields)
    result["character_anomalies"] = char_anomalies

    for a in char_anomalies:
        logger.warning(f"StructuredDoc Agent: CHAR ANOMALY — {a}")

    # ── Step 4: Arithmetic consistency ──
    arith_errors = _check_arithmetic(fields)
    result["arithmetic_errors"] = arith_errors

    for e in arith_errors:
        logger.warning(f"StructuredDoc Agent: ARITHMETIC ERROR — {e}")

    # ── Compute score ──
    total_anomalies = len(format_violations) + len(char_anomalies) + len(arith_errors)
    result["anomaly_count"] = total_anomalies

    # Weighted scoring (increased weights — each finding is HIGH confidence):
    #   - Character anomaly (letter in currency): +0.30 each (definitive tampering)
    #   - Arithmetic error: +0.25 each (strong evidence)
    #   - Format violation: +0.30 each (definitive — e.g. invalid APE checksum)
    score = 0.0
    score += len(char_anomalies) * 0.30
    score += len(arith_errors) * 0.25
    score += len(format_violations) * 0.30

    # ── Field coverage penalty ──
    # If the document is classified as a payslip but key financial fields
    # cannot be extracted, that's suspicious — legitimate payslips always
    # have clearly printed amounts. OCR failure on key fields suggests
    # obfuscation, unusual formatting, or non-standard layout.
    key_fields = ["salaire_brut_raw", "net_a_payer_raw"]
    extracted_count = sum(1 for f in key_fields if fields.get(f))
    if extracted_count == 0:
        score += 0.10
        result["details"].append(
            "Field coverage warning: Could not extract salaire_brut or net_a_payer "
            "from OCR text — key financial fields are missing or unreadable."
        )
        logger.warning(
            "StructuredDoc Agent: FIELD COVERAGE — 0/2 key financial fields extracted"
        )

    score = min(1.0, score)

    result["structured_validation_score"] = round(score, 3)

    # Build human-readable summary
    all_details = format_violations + char_anomalies + arith_errors
    # Prepend any existing details (field coverage warnings)
    result["details"] = result["details"] + all_details

    if total_anomalies == 0 and extracted_count > 0:
        result["details"].append(
            "Structured validation passed — all format checks, character classes, "
            "and arithmetic consistency verified."
        )

    logger.info(
        f"StructuredDoc Agent: score={result['structured_validation_score']} "
        f"anomalies={total_anomalies} "
        f"(format={len(format_violations)}, "
        f"char={len(char_anomalies)}, "
        f"arith={len(arith_errors)}) "
        f"fields_extracted={extracted_count}/{len(key_fields)}"
    )

    return result
