from app import app, db
from app.models import Student, Faculty, Room, Section, Schedule

def add_test_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Schedule).delete()
        db.session.query(Student).delete()
        db.session.query(Faculty).delete()
        db.session.query(Room).delete()
        db.session.query(Section).delete()
        db.session.commit()

        # Create test sections
        section1 = Section(section_name="3-B", course="BSCS", year_level="3")
        section2 = Section(section_name="3-C", course="BSCS", year_level="3")
        db.session.add_all([section1, section2])
        db.session.commit()

        # Create test students
        students = [
            Student(
                student_number="S224-12536M",
                name="Adrian Kurt P. Nacu",
                course="BSCS",
                year_level=3,
                section_id=section1.id
            ),
            Student(
                student_number="S224-12537M",
                name="Emman Seron",
                course="BSCS",
                year_level=3,
                section_id=section1.id
            ),
            Student(
                student_number="S224-12538M",
                name="Charlie Magne Aranez",
                course="BSCS",
                year_level=3,
                section_id=section1.id
            )
        ]
        db.session.add_all(students)
        db.session.commit()

        # Create test faculty
        faculty = Faculty(
            faculty_id="F1",
            name="Merita Latip",
            department="Computer Science"
        )
        db.session.add(faculty)
        db.session.commit()

        # Create test room
        room = Room(room_name="Room 201")
        db.session.add(room)
        db.session.commit()

        # Create test schedules
        schedules = [
            Schedule(
                time="2PM-3PM",
                day="TUESDAY",
                subject="PROGLEC",
                section_id=section1.id,
                faculty_id=faculty.id,
                room_id=room.id
            ),
            Schedule(
                time="3PM-4PM",
                day="TUESDAY",
                subject="PROGLAB",
                section_id=section1.id,
                faculty_id=faculty.id,
                room_id=room.id
            )
        ]
        db.session.add_all(schedules)
        db.session.commit()

if __name__ == "__main__":
    add_test_data()
    print("Test data has been added successfully!")
