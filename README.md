# Multi-Objective Diet Optimization Problem (MODP)

## Team: ZeroDay Squad

## Requirements
- Python 3.12
- MySQL

## Installation

```bash
pip install -r requirements.txt
```

## Database Setup

1. Create the database:
```bash
mysql -u root -p -e "CREATE DATABASE diet;"
```

2. Import the data:
```bash
mysql -u root -p diet < diet.sql
```

3. Update database credentials in `src/database.py`:
```python
password="your_password"
```

## Project Structure
diet-optimization/
├── src/
│   ├── database.py        # Database connection and queries
│   ├── chromosome.py      # Chromosome representation and decoding
│   ├── objectives.py      # Objective functions
│   ├── penalty.py         # Penalty functions
│   ├── menu_table.py      # Sample menu generation
│   └── algorithms/
│       ├── nsga2.py       # NSGA-II algorithm
│       └── spea2.py       # SPEA2 algorithm
├── results/               # Output plots and CSV files
├── main.py                # Run all experiments
└── requirements.txt

## Running

```bash
python main.py
```

## Objectives
1. User Preference → MAX
2. Cost → MIN
3. Preparation Time → MIN

## Users
- User 1: Non-vegetarian
- User 2: Vegetarian