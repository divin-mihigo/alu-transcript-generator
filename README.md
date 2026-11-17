# ALU Transcript Generator

Introduction to Python Programming and Databases - Lab 2 (BSE Year 1, Trimester 2)

## Files

- `grade-evaluator.py` - validates scores and weights, computes GPA, pass/fail status and resubmission eligibility.
- `organizer.sh` - archives `grades.csv` with a timestamp, resets it to an empty file and logs the action to `organizer.log`.
- `grades.csv` - course grades (`assignment,group,score,weight`).

## Usage

```bash
python3 grade-evaluator.py grades.csv   # or run without arguments and enter the filename
./organizer.sh
```

## Rules implemented

- Every score must be between 0 and 100.
- Weights must total 100 (Formative = 60, Summative = 40).
- GPA = (total grade / 100) * 5.0.
- PASSED only when both Formative and Summative scores are at least 50%.
- Resubmission: the failed Formative assignment(s) with the highest weight (ties are all listed).
