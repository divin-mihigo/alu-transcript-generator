# ALU Transcript Generator

**Course:** Introduction to Python Programming and Databases - BSE Year 1, Trimester 2
**Assignment:** Individual Coding Lab - ALU Transcript Generator

A Python application that calculates a student's final academic standing from a CSV file of course grades, plus a Bash script that archives the grade file between batches.

## Repository contents

| File | Purpose |
|------|---------|
| `grade-evaluator.py` | Validates the grades, calculates the GPA, decides PASSED/FAILED and lists assignments eligible for resubmission |
| `organizer.sh` | Archives `grades.csv` with a timestamp, creates a fresh empty `grades.csv` and logs the action |
| `grades.csv` | The course grades used as input |
| `README.md` | This file |

## Requirements

- Python 3.6 or newer (standard library only - no packages to install)
- Bash (Linux, macOS or WSL)

## Input format

`grades.csv` must have this header and one row per assignment:

```csv
assignment,group,score,weight
Quiz,Formative,85,20
Group Exercise,Formative,40,20
Functions and Debugging Lab,Formative,45,20
Midterm Project - Simple Calculator,Summative,70,20
Final Project - Text-Based Game,Summative,60,20
```

- `group` is either `Formative` or `Summative` (case-insensitive)
- `score` is a percentage from 0 to 100
- `weight` is the assignment's share of the final grade

## Running the Python application

```bash
python3 grade-evaluator.py
```

Enter the CSV filename when prompted (e.g. `grades.csv`).

### Calculation rules

- **Total grade** = sum of (score x weight / 100) over all assignments
- **GPA** = (Total grade / 100) x 5.0
- **Category score** = points earned in the category as a percentage of that category's weight (Formative out of 60, Summative out of 40)
- **Final status** = `PASSED` only if the student scores **at least 50% in both** Formative and Summative, otherwise `FAILED`
- **Resubmission** = among the failed Formative assignments (score below 50), the one with the highest weight. If several share that highest weight, **all of them** are listed

### Validation

The program checks the data before calculating and prints every problem it finds:

- every score is a number from 0 to 100
- every weight is a non-negative number
- every group is Formative or Summative
- all weights add up to exactly 100, with Formative = 60 and Summative = 40

### Edge cases handled

The program prints a clear message and exits instead of crashing when:

- no filename is entered, the file does not exist, is a directory, is empty or is not a text file
- a required column (`assignment`, `group`, `score`, `weight`) is missing
- a row has a missing or non-numeric score or weight (the line number is reported)
- the file contains only a header and no assignments

Completely empty rows are skipped, and the number skipped is reported.

### Example output (`grades.csv` provided)

```
--- Processing Grades ---

Assignment                              Group          Score  Weight
-------------------------------------------------------------------
Quiz                                    Formative       85.0    20.0
Group Exercise                          Formative       40.0    20.0
Functions and Debugging Lab             Formative       45.0    20.0
Midterm Project - Simple Calculator     Summative       70.0    20.0
Final Project - Text-Based Game         Summative       60.0    20.0
-------------------------------------------------------------------

Formative Score : 56.67%
Summative Score : 65.00%
Total Grade     : 60.00 / 100
GPA             : 3.00 / 5.0
Final Status    : PASSED

Resubmission Eligibility:
  - Group Exercise (score: 40.0, weight: 20)
  - Functions and Debugging Lab (score: 45.0, weight: 20)
```

Hand check: Formative = 17 + 8 + 9 = 34 out of 60 = 56.67%; Summative = 14 + 12 = 26 out of 40 = 65%; total = 60; GPA = 60 / 100 x 5 = 3.00. Both failed Formative assignments carry the same highest weight (20), so both are eligible for resubmission.

## Running the organizer script

```bash
chmod +x organizer.sh   # first time only
./organizer.sh
```

Each run:

1. Creates the `archive/` directory if it does not exist
2. Moves `grades.csv` into `archive/` renamed with a timestamp, e.g. `archive/grades_20251105-170000.csv`
3. Immediately creates a new, empty `grades.csv` so the workspace is ready for the next batch
4. Appends a line to `organizer.log` (the log accumulates across runs):

```
[20251105-170000] original: grades.csv | archived: archive/grades_20251105-170000.csv
```

If `grades.csv` does not exist the script reports an error and exits without changing anything. If two runs happen within the same second, a numeric suffix keeps the earlier archive from being overwritten.

> Note: run `grade-evaluator.py` **before** `organizer.sh`, because the organizer leaves `grades.csv` empty.
