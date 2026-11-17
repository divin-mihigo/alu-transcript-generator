import csv
import math
import sys
import os

def load_csv_data():
    """
    Prompts the user for a filename, checks if it exists, 
    and extracts all fields into a list of dictionaries.
    """
    filename = input("Enter the name of the CSV file to process (e.g., grades.csv): ")
    
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' was not found.")
        sys.exit(1)
        
    assignments = []
    
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert numeric fields to floats for calculations
                assignments.append({
                    'assignment': row['assignment'],
                    'group': row['group'],
                    'score': float(row['score']),
                    'weight': float(row['weight'])
                })
        return assignments
    except KeyError as e:
        print(f"Error: the CSV file is missing the required column {e}. "
              "Expected columns: assignment, group, score, weight.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

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

    # Normalise group names so "formative " / "FORMATIVE" are treated the same.
    for item in data:
        item['group'] = item['group'].strip().capitalize()

    # a) Check that all scores are percentage based (0-100)
    errors = []
    for item in data:
        score = item['score']
        if not math.isfinite(score) or score < 0 or score > 100:
            errors.append(f"Invalid score for '{item['assignment']}': {item['score']} "
                          "(must be between 0 and 100).")
        if not math.isfinite(item['weight']) or item['weight'] < 0:
            errors.append(f"Invalid weight for '{item['assignment']}': {item['weight']}.")
        if item['group'] not in ('Formative', 'Summative'):
            errors.append(f"Unknown group '{item['group']}' for '{item['assignment']}' "
                          "(must be Formative or Summative).")

    if errors:
        print("Grade validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # b) Validate total weights (Total=100, Summative=40, Formative=60)
    formative = [d for d in data if d['group'] == 'Formative']
    summative = [d for d in data if d['group'] == 'Summative']

    total_weight = round(sum(d['weight'] for d in data), 6)
    formative_weight = round(sum(d['weight'] for d in formative), 6)
    summative_weight = round(sum(d['weight'] for d in summative), 6)

    if total_weight != 100:
        errors.append(f"Total weight is {total_weight:g}, but it must be exactly 100.")
    if formative_weight != 60:
        errors.append(f"Formative weight is {formative_weight:g}, but it must be exactly 60.")
    if summative_weight != 40:
        errors.append(f"Summative weight is {summative_weight:g}, but it must be exactly 40.")

    if errors:
        print("Weight validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # c) Calculate the Final Grade and GPA
    formative_points = sum(d['score'] * d['weight'] / 100 for d in formative)
    summative_points = sum(d['score'] * d['weight'] / 100 for d in summative)
    total_grade = formative_points + summative_points
    gpa = (total_grade / 100) * 5.0

    # Category percentages (points earned out of the category's weight)
    formative_pct = formative_points / formative_weight * 100
    summative_pct = summative_points / summative_weight * 100

    # d) Determine Pass/Fail status (>= 50% in BOTH categories)
    passed = formative_pct >= 50 and summative_pct >= 50

    # e) Failed formative assignments (< 50%) with the highest weight
    failed_formative = [d for d in formative if d['score'] < 50]
    resubmit = []
    if failed_formative:
        highest_weight = max(d['weight'] for d in failed_formative)
        resubmit = [d for d in failed_formative if d['weight'] == highest_weight]

    # f) Print the final decision and resubmission options
    print(f"\n{'Assignment':<40}{'Group':<12}{'Score':>7}{'Weight':>8}")
    print("-" * 67)
    for d in data:
        print(f"{d['assignment']:<40}{d['group']:<12}{d['score']:>7.1f}{d['weight']:>8.1f}")
    print("-" * 67)

    print(f"\nFormative Score : {formative_pct:.2f}%")
    print(f"Summative Score : {summative_pct:.2f}%")
    print(f"Total Grade     : {total_grade:.2f} / 100")
    print(f"GPA             : {gpa:.2f} / 5.0")
    print(f"Final Status    : {'PASSED' if passed else 'FAILED'}")

    print("\nResubmission Eligibility:")
    if resubmit:
        for d in resubmit:
            print(f"  - {d['assignment']} (score: {d['score']:.1f}, weight: {d['weight']:g})")
    else:
        print("  None - no failed formative assignments.")


if __name__ == "__main__":
    # 1. Load the data
    course_data = load_csv_data()
    
    # 2. Process the features
    evaluate_grades(course_data)