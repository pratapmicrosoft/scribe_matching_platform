from app import db

# Define database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(50), nullable=False)  # 'child', 'scribe', 'mentor'
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    location = db.Column(db.String(100))
    age_or_school = db.Column(db.String(50))  # Age for child, School info for scribes and mentors
    subject = db.Column(db.String(200))  # Subject expertise or needs
    class_level = db.Column(db.Integer, nullable=False)  # Class level for both child and scribe
    category_of_disability = db.Column(db.String(50), nullable=True)  # Only for children
    disabilities = db.Column(db.String(200), nullable=True)  # Only for children
    assistance_needed = db.Column(db.String(200), nullable=True)  # Only for children
    certificate = db.Column(db.LargeBinary, nullable=True)  # To store uploaded certificate

    def __repr__(self):
        return f"<User {self.name}, {self.user_type}>"

# Ensure tables are created
def create_tables():
    with server.app_context():
        db.create_all()

# Sample data to be added on app creation if database is empty
def add_sample_data():
    with server.app_context():
        if User.query.first() is None:  # Check if the database is empty
            # Sample data for children and scribes
            children_data = [...]
            scribes_data = [...]

            for data in children_data + scribes_data:
                user = User(
                    user_type=data["user_type"],
                    name=data["name"],
                    email=data["email"],
                    location=data["location"],
                    age_or_school=data["age_or_school"],
                    subject=data["subject"],
                    class_level=data["class_level"],
                    category_of_disability=data.get("category_of_disability"),
                    disabilities=data.get("disabilities"),
                    assistance_needed=data.get("assistance_needed"),
                    certificate=data.get("certificate"),
                )
                db.session.add(user)
            db.session.commit()
