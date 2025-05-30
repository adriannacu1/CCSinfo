from app import app, db
from app.models import Student, Faculty, Room, Section, Schedule, Course, Subject, Admin
import hashlib

def add_test_data():
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        db.session.query(Schedule).delete()
        db.session.query(Student).delete()
        db.session.query(Section).delete()
        db.session.query(Faculty).delete()
        db.session.query(Room).delete()
        db.session.query(Subject).delete()
        db.session.query(Course).delete()
        db.session.commit()

        # Add courses
        bscs = Course(course_id=1, course_name="BSCS")
        bsit = Course(course_id=2, course_name="BSIT")
        db.session.add_all([bscs, bsit])
        db.session.commit()

        # Add subjects
        prog_lec = Subject(subject_id=1, subject_name="Programming Lecture")
        prog_lab = Subject(subject_id=2, subject_name="Programming Laboratory")
        web_dev = Subject(subject_id=3, subject_name="Web Development")
        db.session.add_all([prog_lec, prog_lab, web_dev])
        db.session.commit()

        # Add faculty
        faculty1 = Faculty(faculty_id=1, name="Merita Latip", department="Computer Science")
        faculty2 = Faculty(faculty_id=2, name="John Smith", department="Information Technology")
        db.session.add_all([faculty1, faculty2])
        db.session.commit()

        # Add rooms
        room201 = Room(room_id=1, room_name="Room 201", floor=2, capacity=40)
        room202 = Room(room_id=2, room_name="Room 202", floor=2, capacity=35)
        computer_lab = Room(room_id=3, room_name="Computer Lab 1", floor=1, capacity=30)
        db.session.add_all([room201, room202, computer_lab])
        db.session.commit()

        # Add sections
        section1 = Section(section_id=1, section_name="3-B", course="BSCS", year_level="3", course_id=bscs.course_id)
        section2 = Section(section_id=2, section_name="3-C", course="BSCS", year_level="3", course_id=bscs.course_id)
        section3 = Section(section_id=3, section_name="2-A", course="BSIT", year_level="2", course_id=bsit.course_id)
        db.session.add_all([section1, section2, section3])
        db.session.commit()

        # Add students
        students = [
            Student(
                student_id=1,
                student_number="S224-12536M",
                name="Adrian Kurt P. Nacu",
                course="BSCS", 
                year_level=3,
                section_id=section1.section_id,
                email="adrian.nacu@example.com",
                status="Active",
                course_id=bscs.course_id
            ),
            Student(
                student_id=2,
                student_number="S224-12537M",
                name="Emman Seron",
                course="BSCS",
                year_level=3, 
                section_id=section1.section_id,
                email="emman.seron@example.com",
                status="Active",
                course_id=bscs.course_id
            ),
            Student(
                student_id=3,
                student_number="S224-12538M",
                name="Charlie Magne Aranez",
                course="BSCS",
                year_level=3,
                section_id=section1.section_id,
                email="charlie.aranez@example.com",
                status="Active",
                course_id=bscs.course_id
            ),
            Student(
                student_id=4,
                student_number="S224-12540M",
                name="Jane Smith",
                course="BSIT",
                year_level=2,
                section_id=section3.section_id,
                email="jane.smith@example.com",
                status="Active",
                course_id=bsit.course_id
            )
        ]
        db.session.add_all(students)
        db.session.commit()

        # Add schedules
        schedules = [
            Schedule(
                schedule_id=1,
                time="8:00 AM - 10:00 AM",
                day="Monday",
                subject="Programming Lecture",
                subject_id=prog_lec.subject_id,
                section_id=section1.section_id,
                faculty_id=faculty1.faculty_id,
                room_id=room201.room_id
            ),
            Schedule(
                schedule_id=2,
                time="10:00 AM - 12:00 PM",
                day="Monday",
                subject="Programming Laboratory",
                subject_id=prog_lab.subject_id,
                section_id=section1.section_id,
                faculty_id=faculty1.faculty_id,
                room_id=computer_lab.room_id
            ),
            Schedule(
                schedule_id=3,
                time="1:00 PM - 3:00 PM",
                day="Wednesday",
                subject="Web Development",
                subject_id=web_dev.subject_id,
                section_id=section3.section_id,
                faculty_id=faculty2.faculty_id,
                room_id=computer_lab.room_id
            )
        ]
        db.session.add_all(schedules)
        db.session.commit()

        print("Test data added successfully!")

if __name__ == "__main__":
    add_test_data()
