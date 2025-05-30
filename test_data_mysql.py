from app import app, db
from app.models import Student, Faculty, Room, Section, Schedule, Course, Subject

def add_test_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Schedule).delete()
        db.session.query(Student).delete()
        db.session.query(Faculty).delete()
        db.session.query(Room).delete()
        db.session.query(Section).delete()
        db.session.query(Course).delete()
        db.session.query(Subject).delete()
        db.session.commit()

        # Create courses
        bscs = Course(course_name="BSCS")
        bsit = Course(course_name="BSIT")
        db.session.add_all([bscs, bsit])
        db.session.commit()

        # Create test sections
        section1 = Section(section_name="3-B", course="BSCS", year_level="3", course_id=bscs.course_id)
        section2 = Section(section_name="3-C", course="BSCS", year_level="3", course_id=bscs.course_id)
        db.session.add_all([section1, section2])
        db.session.commit()

        # Create test students
        students = [
            Student(
                student_number="S224-12536M",
                name="Adrian Kurt P. Nacu",
                course="BSCS",
                year_level=3,
                section_id=section1.section_id,  # Changed from id to section_id
                email="adrian.nacu@example.com",
                course_id=bscs.course_id
            ),
            Student(
                student_number="S224-12537M",
                name="Emman Seron",
                course="BSCS",
                year_level=3,
                section_id=section1.section_id,  # Changed from id to section_id
                email="emman.seron@example.com",
                course_id=bscs.course_id
            ),
            Student(
                student_number="S224-12538M",
                name="Charlie Magne Aranez",
                course="BSCS",
                year_level=3,
                section_id=section1.section_id,  # Changed from id to section_id
                email="charlie.aranez@example.com",
                course_id=bscs.course_id
            )
        ]
        db.session.add_all(students)
        db.session.commit()

        # Create test faculty
        faculty = Faculty(
            name="Merita Latip",
            department="Computer Science"
        )
        db.session.add(faculty)
        db.session.commit()

        # Create test room
        room = Room(
            room_name="Room 201",
            floor=2,
            capacity=50
        )
        db.session.add(room)
        db.session.commit()

        # Create subjects
        proglec = Subject(subject_name="PROGLEC")
        proglab = Subject(subject_name="PROGLAB")
        db.session.add_all([proglec, proglab])
        db.session.commit()

        # Create test schedules
        schedules = [
            Schedule(
                time="2PM-3PM",
                day="TUESDAY",
                subject="PROGLEC",
                subject_id=proglec.subject_id,
                section_id=section1.section_id,  # Changed from id to section_id
                faculty_id=faculty.faculty_id,   # Changed from id to faculty_id
                room_id=room.room_id            # Changed from id to room_id
            ),
            Schedule(
                time="3PM-4PM",
                day="TUESDAY",
                subject="PROGLAB",
                subject_id=proglab.subject_id,
                section_id=section1.section_id,  # Changed from id to section_id
                faculty_id=faculty.faculty_id,   # Changed from id to faculty_id
                room_id=room.room_id            # Changed from id to room_id
            )
        ]
        db.session.add_all(schedules)
        db.session.commit()

if __name__ == "__main__":
    add_test_data()
    print("Test data has been added successfully!")