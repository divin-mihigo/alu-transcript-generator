#!/usr/bin/env python3
"""ALU Transcript Generator.

Reads a CSV of course grades, validates it, and prints the student's
GPA, final status (PASSED/FAILED) and any assignment eligible for resubmission.

Expected CSV header: assignment,group,grade,weight
"""

import csv
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

REQUIRED_COLUMNS = ("assignment", "group", "grade", "weight")
PASS_MARK = Decimal("50")
TOTAL_WEIGHT = Decimal("100")
CATEGORY_WEIGHTS = {"Formative": Decimal("60"), "Summative": Decimal("40")}
MAX_GPA = Decimal("5.0")


def load_csv_data():
    """Prompt for a CSV filename (or take it from argv) and parse it.

    Returns a list of assignment dictionaries, or exits on failure.
    """
    if len(sys.argv) > 1:
        filename = sys.argv[1].strip()
    else:
        filename = input("Enter the name of the CSV file to process (e.g., grades.csv): ").strip()

    if not filename:
        print("Error: no filename provided.")
        sys.exit(1)

    assignments = []
    try:
        with open(filename, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                print(f"Error: '{filename}' is empty.")
                sys.exit(1)

            # Normalise headers so " Grade" / "GRADE" still work.
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
            missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing:
                print(f"Error: '{filename}' is missing column(s): {', '.join(missing)}")
                sys.exit(1)

            for line_no, row in enumerate(reader, start=2):
                if not any((value or "").strip() for value in row.values()):
                    continue  # skip blank lines

                name = (row["assignment"] or "").strip()
                group = (row["group"] or "").strip().capitalize()
                try:
                    grade = Decimal((row["grade"] or "").strip())
                    weight = Decimal((row["weight"] or "").strip())
                    if not (grade.is_finite() and weight.is_finite()):
                        raise InvalidOperation
                except InvalidOperation:
                    print(f"Error (line {line_no}): grade and weight must be numbers "
                          f"for assignment '{name}'.")
                    sys.exit(1)

                assignments.append({
                    "assignment": name,
                    "group": group,
                    "grade": grade,
                    "weight": weight,
                    "line": line_no,
                })
    except FileNotFoundError:
        print(f"Error: the file '{filename}' was not found.")
        sys.exit(1)
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        print(f"Error: could not read '{filename}': {exc}")
        sys.exit(1)

    if not assignments:
        print(f"Error: '{filename}' contains no assignments.")
        sys.exit(1)

    return assignments


def validate_grades(assignments):
    """Every grade must be between 0 and 100 (inclusive)."""
    errors = []
    for a in assignments:
        if not (Decimal("0") <= a["grade"] <= Decimal("100")):
            errors.append(f"Invalid grade for '{a['assignment']}': {a['grade']} "
                          "(must be between 0 and 100).")
    return errors


def validate_weights(assignments):
    """Check group names, per-category weights and the overall weight total."""
    errors = []

    for a in assignments:
        if a["group"] not in CATEGORY_WEIGHTS:
            errors.append(f"Unknown group '{a['group']}' for '{a['assignment']}' "
                          "(must be Formative or Summative).")
        if a["weight"] < 0:
            errors.append(f"Negative weight for '{a['assignment']}': {a['weight']}.")

    if errors:
        return errors

    total = sum(a["weight"] for a in assignments)
    if total != TOTAL_WEIGHT:
        errors.append(f"Total weight is {total}, but it must be exactly {TOTAL_WEIGHT}.")

    for group, expected in CATEGORY_WEIGHTS.items():
        group_total = sum(a["weight"] for a in assignments if a["group"] == group)
        if group_total != expected:
            errors.append(f"{group} weights add up to {group_total}, "
                          f"but they must be exactly {expected}.")
    return errors


def category_percentage(assignments, group):
    """Weighted score of a category as a percentage of that category's weight."""
    items = [a for a in assignments if a["group"] == group]
    weight = sum(a["weight"] for a in items)
    earned = sum(a["grade"] * a["weight"] / Decimal("100") for a in items)
    return earned / weight * Decimal("100")


def calculate_results(assignments):
    """Return total grade, GPA, per-category percentages and pass/fail status."""
    total_grade = sum(a["grade"] * a["weight"] / Decimal("100") for a in assignments)
    gpa = total_grade / Decimal("100") * MAX_GPA
    formative_pct = category_percentage(assignments, "Formative")
    summative_pct = category_percentage(assignments, "Summative")
    passed = formative_pct >= PASS_MARK and summative_pct >= PASS_MARK
    return total_grade, gpa, formative_pct, summative_pct, passed


def find_resubmissions(assignments):
    """Failed formative assignment(s) carrying the highest weight (ties included)."""
    failed = [a for a in assignments
              if a["group"] == "Formative" and a["grade"] < PASS_MARK]
    if not failed:
        return []
    highest = max(a["weight"] for a in failed)
    return [a for a in failed if a["weight"] == highest]


def fmt(value, places="0.01"):
    return str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def main():
    assignments = load_csv_data()

    errors = validate_grades(assignments) + validate_weights(assignments)
    if errors:
        print("\nValidation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    total_grade, gpa, formative_pct, summative_pct, passed = calculate_results(assignments)

    print("\n" + "=" * 50)
    print("ALU TRANSCRIPT")
    print("=" * 50)
    print(f"{'Assignment':<25}{'Group':<12}{'Grade':>6}{'Weight':>8}")
    print("-" * 51)
    for a in assignments:
        print(f"{a['assignment']:<25}{a['group']:<12}{fmt(a['grade'], '0.1'):>6}"
              f"{fmt(a['weight'], '0.1'):>8}")
    print("-" * 51)
    print(f"Formative score : {fmt(formative_pct)}%")
    print(f"Summative score : {fmt(summative_pct)}%")
    print(f"Total grade     : {fmt(total_grade)} / 100")
    print(f"Final GPA       : {fmt(gpa)} / 5.0")
    print(f"Final status    : {'PASSED' if passed else 'FAILED'}")

    resubmit = find_resubmissions(assignments)
    print("\nResubmission eligibility:")
    if resubmit:
        for a in resubmit:
            print(f"  - {a['assignment']} (weight {fmt(a['weight'], '0.1')}, "
                  f"grade {fmt(a['grade'], '0.1')})")
    else:
        print("  None - no failed formative assignments.")


if __name__ == "__main__":
    main()
