import os
import json
import shutil
import logging
import unittest
from main import Facade

input_directory = "./fixtures"
output_directory = "./reports"


# Generate a test class for an individual data directory.
def make_test(data_dir):
    class TestClass(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

        @classmethod
        def tearDownClass(cls):
            shutil.rmtree(output_directory)

        def test_parser(self):
            print("\nTesting " + data_dir + "\n")
            courses_path = os.path.join(input_directory, data_dir, "courses.csv")
            students_path = os.path.join(input_directory, data_dir, "students.csv")
            tests_path = os.path.join(input_directory, data_dir, "tests.csv")
            marks_path = os.path.join(input_directory, data_dir, "marks.csv")
            expected_json_path = os.path.join(input_directory, data_dir, "output.json")
            actual_json_path = os.path.join(output_directory, data_dir, "output.json")

            data_dir_path = os.path.join(output_directory, data_dir)

            if os.path.exists(data_dir_path):
                shutil.rmtree(data_dir_path)

            os.mkdir(data_dir_path)

            facade = Facade(
                courses_path, students_path, tests_path, marks_path, actual_json_path
            )

            facade.get_json()

            f_actual = open(
                actual_json_path,
            )
            actual_json = json.load(f_actual)
            f_actual.close()

            f_expected = open(
                expected_json_path,
            )
            expected_json = json.load(f_expected)
            f_expected.close()

            if "error" in actual_json or "error" in expected_json:
                self.assertEqual(actual_json, expected_json)
            else:
                actual_students = actual_json["students"]
                f_actual.close()
                expected_students = expected_json["students"]
                f_expected.close()

                self.assertEqual(len(actual_students), len(expected_students))

                for i in range(len(actual_students)):
                    actual_student = actual_students[i]
                    expected_student = expected_students[i]

                    self.assertEqual(actual_student["id"], expected_student["id"])
                    self.assertEqual(actual_student["name"], expected_student["name"])
                    self.assertEqual(
                        actual_student["totalAverage"], expected_student["totalAverage"]
                    )

                    actual_courses = actual_student["courses"]
                    expected_courses = expected_student["courses"]

                    # sort courses before testing since the courses don’t have to be ordered
                    sorted_actual_courses = actual_courses.sort(
                        key=lambda course: course["id"]
                    )
                    sorted_expected_courses = expected_courses.sort(
                        key=lambda course: course["id"]
                    )

                    self.assertEqual(sorted_actual_courses, sorted_expected_courses)

    return TestClass


for dir_name, sub_dirs, file_names in os.walk("fixtures"):
    for test_data in sub_dirs:
        globals()["Test%s" % test_data] = make_test(test_data)

if __name__ == "__main__":
    unittest.main()
