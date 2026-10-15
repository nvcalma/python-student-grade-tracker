import mysql.connector
import hashlib
import secrets
import time
import re


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="test@dummy", 
    database="schooldb"
)

cursor = db.cursor()


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(8)

    hashed = hashlib.sha256(
        (salt + password).encode()
    ).hexdigest()

    return salt, hashed


def log_action(username, action):
    sql = """
    INSERT INTO activity_logs (username, action)
    VALUES (%s, %s)
    """
    cursor.execute(sql, (username, action))
    db.commit()



def input_password(prompt):
    while True:
        password = input(prompt)
        if len(password) < 8:
            print("Password is too short. Use at least 8 characters. Try again.")
        elif len(password) > 12:
            print("Password is too long. Use at most 12 characters. Try again.")
        else:
            return password


def input_name():
    while True:
        name = input("Enter student full name: ").strip()
        if len(name) < 3 or len(name) > 60:
            print("Name must contain 3 to 60 characters. Try again.")
        elif len(name.split()) < 2:
            print("Enter both first name and last name. Try again.")
        else:
            valid = True
            for character in name:
                if not character.isalpha() and character not in " '-’":
                    valid = False
            for part in name.split():
                if not any(character.isalpha() for character in part):
                    valid = False
            if not valid:
                print("Name allows letters, spaces, apostrophes and hyphens only. Try again.")
            else:
                return name


def input_username(prompt):
    while True:
        username = input(prompt).strip()
        if "@" in username:
            # Emails can be used as usernames; special characters are allowed before @.
            pattern = r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
            local = username.split("@")[0]
            domain = username.split("@")[-1]
            if len(username) > 100 or len(local) > 64:
                print("Email is too long. Maximum 100 characters (64 before @). Try again.")
            elif (not re.fullmatch(pattern, username) or local.startswith(".")
                  or local.endswith(".") or ".." in local):
                print("Invalid email format. Example: juan+school@example.com. Try again.")
            else:
                valid = True
                for part in domain.split("."):
                    if part.startswith("-") or part.endswith("-") or len(part) > 63:
                        valid = False
                if valid:
                    return username
                print("Invalid email domain. Try again.")
        elif len(username) < 3 or len(username) > 30:
            print("Username must contain 3 to 30 characters. Try again.")
        elif not username[0].isalpha():
            print("Username must start with a letter. Try again.")
        else:
            valid = True
            for character in username:
                if not character.isalnum() and character not in "_.-":
                    valid = False
            if valid:
                return username
            print("Username allows letters, numbers, underscore, dot and hyphen. Try again.")


def input_student_id():
    while True:
        student_id = input("Enter student ID: ").strip()
        if len(student_id) < 1 or len(student_id) > 20:
            print("Student ID must contain 1 to 20 characters. Try again.")
        else:
            valid = True
            for part in student_id.split("-"):
                if not part.isalnum():
                    valid = False
            if valid:
                return student_id
            print("Use letters/numbers separated by hyphens, for example 2026-001. Try again.")


def input_subject():
    while True:
        subject = input("Enter subject: ").strip()
        if len(subject) < 2 or len(subject) > 60:
            print("Subject must contain 2 to 60 characters. Try again.")
        else:
            valid = False
            for character in subject:
                if character.isalpha():
                    valid = True
            for character in subject:
                if not character.isalnum() and character not in " .,'&()/+-":
                    valid = False
                    break
            if valid:
                return subject
            print("Enter a subject with letters and ordinary punctuation. Try again.")


def input_grade(prompt):
    while True:
        grade = input(prompt).strip()
        if len(grade) < 1 or len(grade) > 6:
            print("Grade must contain 1 to 6 characters. Try again.")
            continue
        try:
            number = float(grade)
            if not 0 <= number <= 100:
                print("Grade must be from 0 to 100. Try again.")
            else:
                return grade
        except ValueError:
            print("Grade must be a number. Try again.")


def input_grade_id():
    while True:
        grade_id = input("Enter grade ID to update: ").strip()
        if not grade_id.isascii() or not grade_id.isdigit() or len(grade_id) > 10:
            print("Grade ID must contain 1 to 10 digits. Try again.")
        elif int(grade_id) < 1:
            print("Grade ID must be greater than zero. Try again.")
        else:
            return grade_id


def setup_teacher():
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'teacher'"
    )
    count = cursor.fetchone()[0]

    if count == 0:
        print("\nNo teacher account found.")
        print("Create the first teacher account.")

        username = input_username("Teacher username (or email): ")
        password = input_password("Teacher password: ")

        salt, hashed_password = hash_password(password)

        sql = """
        INSERT INTO users
        (username, password_hash, salt, role, student_id)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (username, hashed_password, salt, "teacher", None)
        )

        db.commit()

        print("Teacher account created!")



def login():
    failed_attempts = 0

    while failed_attempts < 3:
        username = input("\nUsername: ")
        password = input("Password: ")

        sql = """
        SELECT username, password_hash, salt, role, student_id
        FROM users
        WHERE username = %s
        """

        cursor.execute(sql, (username,))
        user = cursor.fetchone()

        if user:
            stored_hash = user[1]
            salt = user[2]

            _, hashed_password = hash_password(password, salt)

            if hashed_password == stored_hash:
                print("Login successful!")
                log_action(username, "Successful login")
                return user

        failed_attempts += 1
        log_action(username, "Failed login attempt")

        print("Invalid username or password.")
        print("Attempts left:", 3 - failed_attempts)

    print("Too many failed login attempts.")
    print("Login is temporarily blocked.")
    time.sleep(5)

    return None


def add_student(username):
    student_id = input_student_id()
    name = input_name()

    student_username = input_username("Create student username (or email): ")
    student_password = input_password("Create student password: ")

    try:
        sql = """
        INSERT INTO students (student_id, name)
        VALUES (%s, %s)
        """
        cursor.execute(sql, (student_id, name))

        salt, hashed_password = hash_password(student_password)

        sql = """
        INSERT INTO users
        (username, password_hash, salt, role, student_id)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                student_username,
                hashed_password,
                salt,
                "student",
                student_id
            )
        )

        db.commit()

        log_action(username, "Added student " + student_id)
        print("Student added successfully!")

    except mysql.connector.Error as error:
        db.rollback()
        print("Could not add student.")
        print("Error:", error)


def add_grade(username):
    student_id = input_student_id()

    cursor.execute(
        "SELECT student_id FROM students WHERE student_id = %s",
        (student_id,)
    )

    if cursor.fetchone() is None:
        print("Student not found.")
        return

    subject = input_subject()
    grade = input_grade("Enter grade: ")

    try:
        grade = float(grade)

        if grade < 0 or grade > 100:
            print("Grade must be from 0 to 100.")
            return

        sql = """
        INSERT INTO grades (student_id, subject, grade)
        VALUES (%s, %s, %s)
        """

        cursor.execute(sql, (student_id, subject, grade))
        db.commit()

        log_action(username, "Added grade for " + student_id)
        print("Grade added successfully!")

    except ValueError:
        print("Grade must be a number.")



def update_grade(username):
    grade_id = input_grade_id()
    new_grade = input_grade("Enter new grade: ")

    try:
        new_grade = float(new_grade)

        if new_grade < 0 or new_grade > 100:
            print("Grade must be from 0 to 100.")
            return

        sql = """
        UPDATE grades
        SET grade = %s
        WHERE id = %s
        """

        cursor.execute(sql, (new_grade, grade_id))

        if cursor.rowcount == 0:
            print("Grade record not found.")
            return

        db.commit()

        log_action(username, "Updated grade ID " + grade_id)
        print("Grade updated successfully!")

    except ValueError:
        print("Grade must be a number.")


def view_student_grades():
    student_id = input_student_id()

    sql = """
    SELECT students.name, grades.id, grades.subject, grades.grade
    FROM students
    JOIN grades
    ON students.student_id = grades.student_id
    WHERE students.student_id = %s
    """

    cursor.execute(sql, (student_id,))
    results = cursor.fetchall()

    if results:
        print("\nStudent:", results[0][0])
        print("------------------------------")

        total = 0

        for row in results:
            print(
                "Grade ID:", row[1],
                "|", row[2],
                ":", row[3]
            )
            total += float(row[3])

        average = total / len(results)

        print("------------------------------")
        print("Average:", round(average, 2))

    else:
        print("Student not found / No grades to display.")



def view_my_grades(student_id):
    sql = """
    SELECT students.name, grades.subject, grades.grade
    FROM students
    JOIN grades
    ON students.student_id = grades.student_id
    WHERE students.student_id = %s
    """

    cursor.execute(sql, (student_id,))
    results = cursor.fetchall()

    if results:
        print("\nStudent:", results[0][0])
        print("------------------------------")

        total = 0

        for row in results:
            print(row[1], ":", row[2])
            total += float(row[2])

        average = total / len(results)

        print("------------------------------")
        print("Average:", round(average, 2))

    else:
        print("No grades to display.")



def view_logs():
    sql = """
    SELECT username, action, log_time
    FROM activity_logs
    ORDER BY log_time DESC
    """

    cursor.execute(sql)
    results = cursor.fetchall()

    print("\n========== ACTIVITY LOGS ==========")

    for row in results:
        print(row[2], "|", row[0], "|", row[1])



def view_all_grades():
    sql = """
    SELECT students.student_id, students.name, grades.id, grades.subject, grades.grade
    FROM students
    JOIN grades ON students.student_id = grades.student_id
    ORDER BY students.name, students.student_id, grades.subject, grades.id
    """
    cursor.execute(sql)
    results = cursor.fetchall()
    print("\n========== ALL GRADES ==========")
    if not results:
        print("No grades to display.")
    for row in results:
        print("Student ID:", row[0], "|", row[1],
              "| Grade ID:", row[2], "|", row[3], ":", row[4])


def reset_teacher_password(username):
    current_password = input("Enter current teacher password: ")
    sql = """
    SELECT password_hash, salt FROM users
    WHERE username = %s AND role = 'teacher'
    """
    cursor.execute(sql, (username,))
    teacher = cursor.fetchone()
    if teacher is None:
        print("Teacher account not found.")
        return
    _, current_hash = hash_password(current_password, teacher[1])
    if current_hash != teacher[0]:
        print("Current password is incorrect.")
        return

    while True:
        new_password = input_password("Enter new password: ")
        confirm_password = input("Confirm new password: ")
        if new_password != confirm_password:
            print("Passwords do not match. Try again.")
        else:
            break

    salt, hashed_password = hash_password(new_password)
    try:
        sql = """
        UPDATE users SET password_hash = %s, salt = %s
        WHERE username = %s AND role = 'teacher'
        """
        cursor.execute(sql, (hashed_password, salt, username))
        db.commit()
        log_action(username, "Reset teacher password")
        print("Teacher password reset successfully!")
    except mysql.connector.Error as error:
        db.rollback()
        print("Could not reset password.")
        print("Error:", error)


def teacher_menu(username):
    while True:
        print("\n==============================")
        print("       TEACHER MENU")
        print("==============================")
        print("1. Add Student")
        print("2. Add Grade")
        print("3. Update Grade")
        print("4. View Student Grades")
        print("5. View Activity Logs")
        print("6. Exit")
        print("7. View All Grades")
        print("8. Reset Teacher Password")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_student(username)

        elif choice == "2":
            add_grade(username)

        elif choice == "3":
            update_grade(username)

        elif choice == "4":
            view_student_grades()

        elif choice == "5":
            view_logs()

        elif choice == "6":
            print("Goodbye!")
            break

        elif choice == "7":
            view_all_grades()

        elif choice == "8":
            reset_teacher_password(username)

        else:
            print("Invalid choice.")


def student_menu(username, student_id):
    while True:
        print("\n==============================")
        print("       STUDENT MENU")
        print("==============================")
        print("1. View My Grades")
        print("2. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            view_my_grades(student_id)

        elif choice == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")



setup_teacher()

user = login()

if user:
    username = user[0]
    role = user[3]
    student_id = user[4]

    if role == "teacher":
        teacher_menu(username)

    elif role == "student":
        student_menu(username, student_id)

    else:
        print("Unknown user role.")

cursor.close()
db.close()
