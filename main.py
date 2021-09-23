import pandas as pd
from pandas.api.types import is_numeric_dtype
import json
import sys


class Student:
    def __init__(self, student_id, name):
        self.id = student_id
        self.name = name
        self.totalAverage = 0
        self.courses = []


class Course:
    def __init__(self, course_id, name, teacher):
        self.id = course_id
        self.name = name
        self.teacher = teacher
        self.courseAverage = 0


class Parse:
    def __init__(self):
        self.students = []
        self.invalid_input = False
        self.error_message = ""

    def store_csv_info(
        self, path_to_courses, path_to_students, path_to_tests, path_to_marks
    ):
        courses = (
            pd.read_csv(path_to_courses)
            .rename(columns={"id": "course_id"})
            .sort_values(by=["course_id"])
        )
        students = (
            pd.read_csv(path_to_students)
            .rename(columns={"id": "student_id"})
            .sort_values(by=["student_id"])
        )
        tests = pd.read_csv(path_to_tests).rename(columns={"id": "test_id"})
        marks = pd.read_csv(path_to_marks)

        self.check_input_validity(courses, students, tests, marks)

        if self.invalid_input:
            return

        for index, row in students.iterrows():
            student = Student(row[0], row[1])

            student_marks = marks.loc[marks["student_id"] == student.id]

            student_course_marks = pd.merge(student_marks, tests)

            weighted_course_marks = pd.DataFrame(
                student_course_marks["mark"].mul(student_course_marks["weight"]),
                columns=["weighted_mark"],
            ).join(student_course_marks)

            final_marks = weighted_course_marks.groupby(
                ["student_id", "course_id"]
            ).agg({"weighted_mark": "sum", "weight": "sum"})

            mark_sum = 0

            for i, r in final_marks.iterrows():
                course_id = i[1]
                course_avg = r[0] / 100
                mark_sum += course_avg
                course_info = courses.loc[courses["course_id"] == course_id].iloc[0]
                course = Course(
                    course_info["course_id"],
                    course_info["name"],
                    course_info["teacher"],
                )
                course.courseAverage = "{:.2f}".format(course_avg)
                student.courses.append(course)

            if len(final_marks.index) > 0:
                student.totalAverage = "{:.2f}".format(
                    mark_sum / len(final_marks.index)
                )
            else:
                student.totalAverage = 0

            self.students.append(student)

    def check_input_validity(self, courses, students, tests, marks):
        if not is_numeric_dtype(courses["course_id"]):
            self.invalid_input = True
            self.error_message = "Invalid input in courses"
        elif not is_numeric_dtype(students["student_id"]):
            self.invalid_input = True
            self.error_message = "Invalid input in students"
        elif (
            not is_numeric_dtype(tests["test_id"])
            and is_numeric_dtype(tests["course_id"])
            and is_numeric_dtype(tests["weight_id"])
        ):
            self.invalid_input = True
            self.error_message = "Invalid input in tests"
        elif (
            not is_numeric_dtype(marks["test_id"])
            and is_numeric_dtype(marks["student_id"])
            and is_numeric_dtype(marks["mark"])
        ):
            self.invalid_input = True
            self.error_message = "Invalid input in tests"
        elif any(courses["course_id"].duplicated()):
            self.invalid_input = True
            self.error_message = "Course id not unique"
        elif any(students["student_id"].duplicated()):
            self.invalid_input = True
            self.error_message = "Student id not unique"
        elif any(tests["test_id"].duplicated()):
            self.invalid_input = True
            self.error_message = "Test id not unique"
        elif not all(tests.course_id.isin(courses.course_id)):
            self.invalid_input = True
            self.error_message = "Course id doesn't exist"
        elif not all(courses.course_id.isin(tests.course_id)):
            self.invalid_input = True
            self.error_message = "Course has no grade distribution"
        elif not all(marks.mark.between(0, 100)):
            self.invalid_input = True
            self.error_message = "Invalid mark given"
        elif not all(tests.weight.between(0, 100)):
            self.invalid_input = True
            self.error_message = "Invalid test weight"
        elif tests.weight.sum() / len(courses.index) != 100:
            self.invalid_input = True
            self.error_message = "Invalid course grade distribution"
        elif not all(marks.student_id.isin(students.student_id)):
            self.invalid_input = True
            self.error_message = "Student id doesn't exist"
        elif not all(marks.test_id.isin(tests.test_id)):
            self.invalid_input = True
            self.error_message = "Test id doesn't exist"

    def generate_json(self, path_to_output):
        if self.invalid_input:
            report = {"error": self.error_message}
        else:
            report = self.build_report()

        with open(path_to_output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

    def build_report(self):
        report = {"students": []}
        for student in self.students:
            courses = []
            for course in student.courses:
                json_course = {
                    "id": int(course.id),
                    "name": course.name.strip(),
                    "teacher": course.teacher.strip(),
                    "courseAverage": float(course.courseAverage),
                }
                courses.append(json_course)
            json_student = {
                "id": int(student.id),
                "name": student.name.strip(),
                "totalAverage": float(student.totalAverage),
                "courses": courses,
            }
            report["students"].append(json_student)
        return report


class Facade:
    def __init__(
        self,
        courses_path_name,
        students_path_name,
        tests_path_name,
        marks_path_name,
        output_path_name,
    ):
        self.courses_path_name = courses_path_name
        self.students_path_name = students_path_name
        self.tests_path_name = tests_path_name
        self.marks_path_name = marks_path_name
        self.output_path_name = output_path_name
        self.parse = Parse()

    def get_json(self):
        self.parse.store_csv_info(
            self.courses_path_name,
            self.students_path_name,
            self.tests_path_name,
            self.marks_path_name,
        )
        return self.parse.generate_json(self.output_path_name)


# fronted can simply give the output and input data paths to generate a JSON file:
def main(
    courses_path_name,
    students_path_name,
    tests_path_name,
    marks_path_name,
    output_path_name,
):
    facade = Facade(
        courses_path_name,
        students_path_name,
        tests_path_name,
        marks_path_name,
        output_path_name,
    )
    facade.get_json()


if __name__ == "__main__":
    courses_file = sys.argv[1]
    students_file = sys.argv[2]
    tests_file = sys.argv[3]
    marks_file = sys.argv[4]
    output_file = sys.argv[5]

    main(courses_file, students_file, tests_file, marks_file, output_file)
