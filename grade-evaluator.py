import csv
import math
import sys
import os

VALID_GROUPS = ('Formative', 'Summative')
REQUIRED_COLUMNS = ('assignment', 'group', 'score', 'weight')
PASS_MARK = 50
EXPECTED_WEIGHTS = {'Formative': 60, 'Summative': 40}
TOTAL_WEIGHT = 100


def load_csv_data():
    """
    Prompts the user for a filename, checks if it exists,
    and extracts all fields into a list of dictionaries.
    Empty rows are skipped; invalid rows are reported with their line number.
    """
    try:
        filename = input("Enter the name of the CSV file to process (e.g., grades.csv): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nError: no filename was provided.")
        sys.exit(1)

    if not filename:
        print("Error: no filename was provided.")
        sys.exit(1)

    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' was not found.")
        sys.exit(1)

    if not os.path.isfile(filename):
        print(f"Error: '{filename}' is not a file.")
        sys.exit(1)

    assignments = []
    row_errors = []
    empty_rows = 0

    try:
        # utf-8-sig also copes with files saved by Excel (which add a BOM)
        with open(filename, mode='r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                print(f"Error: The file '{filename}' is empty.")
                sys.exit(1)

            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
            missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
            if missing:
                print(f"Error: The file '{filename}' is missing the required column(s): "
                      f"{', '.join(missing)}.")
                print(f"Expected header: {','.join(REQUIRED_COLUMNS)}")
                sys.exit(1)

            for row in reader:
                line = reader.line_num
                values = [(row.get(col) or '').strip() for col in REQUIRED_COLUMNS]

                if not any(values):
                    empty_rows += 1
                    continue

                name, group, raw_score, raw_weight = values
                problems = []

                if not name:
                    problems.append("assignment name is missing")
                if not group:
                    problems.append("group is missing")

                score = weight = None
                try:
                    score = float(raw_score)
                except ValueError:
                    problems.append(f"score '{raw_score}' is not a number" if raw_score
                                    else "score is missing")
                try:
                    weight = float(raw_weight)
                except ValueError:
                    problems.append(f"weight '{raw_weight}' is not a number" if raw_weight
                                    else "weight is missing")

                if problems:
                    row_errors.append(f"Line {line}: " + "; ".join(problems) + ".")
                    continue

                assignments.append({
                    'assignment': name,
                    'group': group,
                    'score': score,
                    'weight': weight
                })
    except UnicodeDecodeError:
        print(f"Error: '{filename}' is not a readable text/CSV file.")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error: '{filename}' is not valid CSV: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"Error: could not read '{filename}': {e.strerror or e}")
        sys.exit(1)

    if row_errors:
        print(f"Invalid data found in '{filename}':")
        for error in row_errors:
            print(f"  - {error}")
        sys.exit(1)

    if empty_rows:
        print(f"Note: skipped {empty_rows} empty row(s).")

    return assignments


def validate_scores(data):
    """Every score must be a number between 0 and 100. Returns a list of errors."""
    errors = []
    for item in data:
        score = item['score']
        if not math.isfinite(score) or score < 0 or score > 100:
            errors.append(f"Invalid score for '{item['assignment']}': {item['score']:g} "
                          "(must be between 0 and 100).")
    return errors


def validate_weights(data):
    """
    Total weight must be exactly 100, with Formative = 60 and Summative = 40.
    Returns a list of errors.
    """
    errors = []

    for item in data:
        if item['group'] not in VALID_GROUPS:
            errors.append(f"Unknown group '{item['group']}' for '{item['assignment']}' "
                          "(must be Formative or Summative).")
        if not math.isfinite(item['weight']) or item['weight'] < 0:
            errors.append(f"Invalid weight for '{item['assignment']}': {item['weight']:g} "
                          "(must be zero or more).")

    if errors:
        return errors

    # rounding avoids floating point noise such as 59.99999999999999
    total = round(sum(item['weight'] for item in data), 6)
    if total != TOTAL_WEIGHT:
        errors.append(f"Total weight is {total:g}, but it must be exactly {TOTAL_WEIGHT}.")

    for group, expected in EXPECTED_WEIGHTS.items():
        group_total = round(sum(i['weight'] for i in data if i['group'] == group), 6)
        if group_total != expected:
            errors.append(f"{group} weight is {group_total:g}, but it must be exactly {expected}.")

    return errors


def find_resubmissions(formative):
    """
    Returns the failed formative assignment(s) (score < 50) that carry the highest
    weight. If several share that weight, all of them are returned.
    """
    failed = [item for item in formative if item['score'] < PASS_MARK]
    if not failed:
        return []

    highest_weight = failed[0]['weight']
    for item in failed:
        if item['weight'] > highest_weight:
            highest_weight = item['weight']

    return [item for item in failed if item['weight'] == highest_weight]


def evaluate_grades(data):
    """
    Validates the assignment records, calculates the GPA, decides
    PASSED/FAILED and finds the assignment(s) eligible for resubmission.
    'data' is a list of dictionaries containing the assignment records.
    """
    print("\n--- Processing Grades ---")

    if not data:
        print("Error: the CSV file contains no assignments.")
        sys.exit(1)

    # Normalise group names so "formative" / "FORMATIVE " are treated the same
    for item in data:
        item['group'] = item['group'].strip().capitalize()

    # a) Check that all scores are percentage based (0-100)
    # b) Validate total weights (Total=100, Summative=40, Formative=60)
    score_errors = validate_scores(data)
    weight_errors = validate_weights(data)

    if score_errors or weight_errors:
        print("Validation failed:")
        for error in score_errors + weight_errors:
            print(f"  - {error}")
        sys.exit(1)

    formative = [item for item in data if item['group'] == 'Formative']
    summative = [item for item in data if item['group'] == 'Summative']

    # c) Calculate the Final Grade and GPA
    formative_points = sum(i['score'] * i['weight'] / 100 for i in formative)
    summative_points = sum(i['score'] * i['weight'] / 100 for i in summative)
    total_grade = formative_points + summative_points
    gpa = (total_grade / 100) * 5.0

    # Category percentages: points earned out of the points available in that category
    formative_pct = formative_points / EXPECTED_WEIGHTS['Formative'] * 100
    summative_pct = summative_points / EXPECTED_WEIGHTS['Summative'] * 100

    # d) Determine Pass/Fail status (>= 50% in BOTH categories)
    passed = round(formative_pct, 6) >= PASS_MARK and round(summative_pct, 6) >= PASS_MARK

    # e) Failed formative assignments (< 50%) with the highest weight
    resubmit = find_resubmissions(formative)

    # f) Print the final decision (PASSED / FAILED) and resubmission options
    print(f"\n{'Assignment':<40}{'Group':<12}{'Score':>7}{'Weight':>8}")
    print("-" * 67)
    for item in data:
        print(f"{item['assignment']:<40}{item['group']:<12}"
              f"{item['score']:>7.1f}{item['weight']:>8.1f}")
    print("-" * 67)

    print(f"\nFormative Score : {formative_pct:.2f}%")
    print(f"Summative Score : {summative_pct:.2f}%")
    print(f"Total Grade     : {total_grade:.2f} / 100")
    print(f"GPA             : {gpa:.2f} / 5.0")
    print(f"Final Status    : {'PASSED' if passed else 'FAILED'}")

    print("\nResubmission Eligibility:")
    if resubmit:
        for item in resubmit:
            print(f"  - {item['assignment']} (score: {item['score']:.1f}, "
                  f"weight: {item['weight']:g})")
    else:
        print("  None - no failed formative assignments.")


if __name__ == "__main__":
    # 1. Load the data
    course_data = load_csv_data()

    # 2. Process the features
    evaluate_grades(course_data)
