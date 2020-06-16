"""
Author: Shamith Pasula
Date: 6/11/2020

Hatchways.io software assessment

This program encodes a report card from 4 different csv files to one json file.
"""

# imports
import csv
import json
import sys
import pandas as pd
import argparse
parser = argparse.ArgumentParser()

# handles errors
def error_handler(message):
    json.dump({'error': message}, OUTPUT_JSON, indent=4)
    sys.exit() # exit script

# calculates weighted average
def weighted_average(mark, weight):
    course[0]['courseAverage'] += round(mark * weight / 100, 2)

# parsing the cmd line args (default values are shown)
# default FILES are tests downloaded from the assessment instructions
parser.add_argument('courses', nargs='?', default='./courses.csv')
parser.add_argument('students', nargs='?', default='./students.csv')
parser.add_argument('tests', nargs='?', default='./tests.csv')
parser.add_argument('marks', nargs='?', default='./marks.csv')
parser.add_argument('output', nargs='?', default='./output.json')

# parse args into a dict
ARGS = parser.parse_args()
FILES = vars(ARGS)

# opening the csv FILES (read-only) and output.json file (write)
for key in FILES:
    if key == 'output':
        OUTPUT_JSON = open(FILES[key], 'w')
    else:
        FILES[key] = open(FILES[key], 'r')

# reading marks.csv and tests.csv into pandas DataFrames for easier manipulation
MARKS_DF = pd.read_csv(FILES['marks'])
TESTS_DF = pd.read_csv(FILES['tests'])
COURSES_DF = pd.read_csv(FILES['courses'])

# dict of error messages for ease of access
ERROR_MESSAGES = {
    'weights': 'Invalid course weights',
    'percentages': 'Marks must be between 0 and 100 (percentage)',
    'id': 'IDs must be integers'
}

# checking for invalid weights error
sum_weights = 0
last_course = TESTS_DF['course_id'][0]

for i in range(len(TESTS_DF)):
    if TESTS_DF['course_id'][i] == last_course:
        sum_weights += TESTS_DF['weight'][i]
    else:
        if sum_weights != 100:
            error_handler(ERROR_MESSAGES['weights'])
        sum_weights = TESTS_DF['weight'][i]
        last_course = TESTS_DF['course_id'][i]
# for off-by-one error in above loop
if sum_weights != 100:
    error_handler(ERROR_MESSAGES['weights'])

# initialize the dict that will be output.json's only contents
json_dict = {
    'students': []
}

# initialize all students in json_dict with id and name
CSV_READER = csv.DictReader(FILES['students'])
for row in CSV_READER:
    json_dict['students'].append(row)

# convert student ids into ints
for student in json_dict['students']:
    try:
        student['id'] = int(student['id'])
    except ValueError:
        error_handler(ERROR_MESSAGES['id'])

# determine which courses each student took and add them to the student
for student in json_dict['students']:
    courses = []
    for i in range(len(COURSES_DF)):
        took = False
        course_id = COURSES_DF['id'][i]
        idx = list(TESTS_DF['course_id']).index(course_id)
        test_id = TESTS_DF['id'][idx]

        for j in range(len(MARKS_DF)):
            if test_id == MARKS_DF['test_id'][j] and student['id'] == MARKS_DF['student_id'][j]:
                try:
                    course_id = int(course_id)
                except ValueError:
                    error_handler(ERROR_MESSAGES['id'])
                courses.append({
                    'id': course_id,
                    'name': COURSES_DF['name'][i],
                    'teacher': COURSES_DF['teacher'][i]
                })
    student['courses'] = courses

# calculate courseAverages
for i in range(len(MARKS_DF)):
    student_id = MARKS_DF['student_id'][i]
    test_id = MARKS_DF['test_id'][i]
    mark = MARKS_DF['mark'][i]
    if mark > 100 or mark < 0:
        error_handler(ERROR_MESSAGES['percentages'])

    idx = list(TESTS_DF['id']).index(test_id)
    course_id = TESTS_DF['course_id'][idx]
    weight = TESTS_DF['weight'][idx]

    student = [s for s in json_dict['students'] if s['id'] == student_id]
    course = [c for c in student[0]['courses'] if c['id'] == course_id]

    try:
        weighted_average(mark, weight)
    except KeyError:
        course[0]['courseAverage'] = 0
        weighted_average(mark, weight)

# calculate totalAverages
for student in json_dict['students']:
    student['totalAverage'] = 0
    num_courses = 0
    for course in student['courses']:
        student['totalAverage'] += course['courseAverage']
        num_courses += 1
    try:
        student['totalAverage'] = round(
            student['totalAverage'] / num_courses, 2)
    except ZeroDivisionError:
        student['totalAverage'] = 'N/A'

# dump the dict to output.json
json.dump(json_dict, OUTPUT_JSON, indent=4)