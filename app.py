import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, MATCH, ALL
import dash_cytoscape as cyto
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import base64

# Initialize Flask app and configure SQLAlchemy
server = Flask(__name__)
server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(server)

# Initialize Flask-Migrate
migrate = Migrate(server, db)

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    server=server,
    suppress_callback_exceptions=True,
    title="Scribe Matching Platform",
)

# Load extra layouts for Cytoscape
cyto.load_extra_layouts()

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
with server.app_context():
    db.create_all()

# Sample data to be added on app creation if database is empty
def add_sample_data():
    with server.app_context():
        if User.query.first() is None:  # Check if the database is empty
            # Sample data for children
            children_data = [
                {
                    "user_type": "child",
                    "name": "Alice",
                    "email": "alice@example.com",
                    "location": "New York",
                    "age_or_school": "10",
                    "subject": "Mathematics",
                    "class_level": 10,
                    "category_of_disability": "SLD",
                    "disabilities": "Dyslexia",
                    "assistance_needed": "Writing Assistance",
                    "certificate": None,
                },
                {
                    "user_type": "child",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "location": "San Francisco",
                    "age_or_school": "12",
                    "subject": "Science",
                    "class_level": 12,
                    "category_of_disability": "VI",
                    "disabilities": "Visual Impairment",
                    "assistance_needed": "Reading Aloud",
                    "certificate": None,
                },
                {
                    "user_type": "child",
                    "name": "Charlie",
                    "email": "charlie@example.com",
                    "location": "Chicago",
                    "age_or_school": "11",
                    "subject": "English",
                    "class_level": 11,
                    "category_of_disability": "DF",
                    "disabilities": "Deformed Fingers",
                    "assistance_needed": "Writing Assistance",
                    "certificate": None,
                },
            ]

            # Sample data for scribes
            scribes_data = [
                {
                    "user_type": "scribe",
                    "name": "Eve",
                    "email": "eve@example.com",
                    "location": "New York",
                    "age_or_school": "NYU",
                    "subject": "Mathematics, Physics",
                    "class_level": 9,  # Lower than children's class_level
                    "category_of_disability": None,  # Not applicable
                    "disabilities": None,  # Not applicable
                    "assistance_needed": None,  # Not applicable
                    "certificate": None,
                },
                {
                    "user_type": "scribe",
                    "name": "Frank",
                    "email": "frank@example.com",
                    "location": "San Francisco",
                    "age_or_school": "Stanford",
                    "subject": "Science, Chemistry",
                    "class_level": 10,  # Lower than children's class_level
                    "category_of_disability": None,  # Not applicable
                    "disabilities": None,  # Not applicable
                    "assistance_needed": None,  # Not applicable
                    "certificate": None,
                },
                {
                    "user_type": "scribe",
                    "name": "Grace",
                    "email": "grace@example.com",
                    "location": "Chicago",
                    "age_or_school": "UChicago",
                    "subject": "English, Literature",
                    "class_level": 9,  # Lower than children's class_level
                    "category_of_disability": None,  # Not applicable
                    "disabilities": None,  # Not applicable
                    "assistance_needed": None,  # Not applicable
                    "certificate": None,
                },
            ]

            # Add sample users to the database
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

# Run the function to add the sample data if needed
add_sample_data()

# Helper function to handle user registration
def register_user(
    user_type,
    name,
    email,
    location,
    extra,
    subject,
    class_level,
    category_of_disability,
    disabilities,
    assistance,
    certificate,
):
    # Validate required fields
    if user_type == "scribe":
        required_fields = [
            name,
            email,
            location,
            extra,
            subject,
            class_level,
        ]
        if not all(required_fields):
            return dbc.Alert(
                "Please fill in all required fields for scribe registration.",
                color="danger",
            )
    else:
        required_fields = [
            name,
            email,
            location,
            extra,
            subject,
            class_level,
            category_of_disability,
        ]
        if not all(required_fields):
            return dbc.Alert(
                f"Please fill in all required fields for {user_type} registration.",
                color="danger",
            )

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return dbc.Alert("Email already registered.", color="warning")

    try:
        disabilities_str = ", ".join(disabilities) if disabilities else ""
        assistance_str = ", ".join(assistance) if assistance else ""
        new_user = User(
            user_type=user_type,
            name=name,
            email=email,
            location=location,
            age_or_school=extra,
            subject=subject,
            class_level=class_level,
            category_of_disability=category_of_disability if user_type == "child" else None,
            disabilities=disabilities_str if user_type == "child" else None,
            assistance_needed=assistance_str if user_type == "child" else None,
            certificate=certificate if user_type == "child" else None,
        )
        db.session.add(new_user)
        db.session.commit()
        return dbc.Alert(
            f"{user_type.capitalize()} registration for {name} completed successfully!",
            color="success",
        )
    except Exception as e:
        db.session.rollback()
        return dbc.Alert(f"An error occurred during registration: {str(e)}", color="danger")

# Registration Form for Child or Scribe
def registration_form(user_type):
    extra_label = "Age" if user_type == "child" else "School Information"
    subject_label = "Subject Requirements" if user_type == "child" else "Subject Expertise"

    # Category of Disability options based on Table 8.1 (only for children)
    category_options = [
        {"label": "Blindness (B)", "value": "B"},
        {"label": "Low Vision (LV)", "value": "LV"},
        {"label": "Locomotor Disability (L)", "value": "L"},
        {"label": "Hearing and Speech Impairment (HI)", "value": "HI"},
        {"label": "Leprosy Cured (LC)", "value": "LC"},
        {"label": "Mental Illness (MI)", "value": "MI"},
        {"label": "Mental Retardation (MR)", "value": "MR"},
        {"label": "Autism (Aut)", "value": "Aut"},
        {"label": "Cerebral Palsy (CP)", "value": "CP"},
        {"label": "Multiple Disabilities (MD)", "value": "MD"},
        {"label": "Specific Learning Disabilities (SLD)", "value": "SLD"},
    ]

    # Specific Disabilities options (only for children)
    disabilities_options = [
        {"label": "Autism", "value": "Aut"},
        {"label": "Cerebral Palsy", "value": "CP"},
        {"label": "Intellectual Disability (MR)", "value": "MR"},
        {"label": "Multiple Disabilities", "value": "MD"},
        {"label": "Blindness", "value": "B"},
        {"label": "Low Vision", "value": "LV"},
        {"label": "Hearing Impairment", "value": "HI"},
        {"label": "Leprosy Cured", "value": "LC"},
        {"label": "Specific Learning Disabilities", "value": "SLD"},
        {"label": "Deformed Fingers", "value": "DF"},
        {"label": "Other", "value": "Other"},
    ]

    # Assistance needed options (only for children)
    assistance_options = [
        {"label": "Additional Time", "value": "additional_time"},
        {"label": "Amanuensis/Reader/Lab Assistant", "value": "amanuensis"},
        {"label": "Use of Computer with Adaptations", "value": "computer_use"},
        {"label": "Seating Arrangements", "value": "seating_arrangements"},
        {"label": "Interpreter for Sign Language", "value": "interpreter"},
        {"label": "Care Giver Support", "value": "care_giver"},
        {"label": "Other Assistance", "value": "other_assistance"},
    ]

    # Class Level options (assuming classes 1 to 12)
    class_options = [{"label": f"Class {i}", "value": i} for i in range(1, 13)]

    form_fields = [
        dbc.Row(
            [
                dbc.Col(dbc.Label("Name *"), width=3),
                dbc.Col(
                    dbc.Input(
                        id={"type": "registration_name", "user_type": user_type},
                        type="text",
                        placeholder="Enter your name",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Email *"), width=3),
                dbc.Col(
                    dbc.Input(
                        id={"type": "registration_email", "user_type": user_type},
                        type="email",
                        placeholder="Enter your email",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Location *"), width=3),
                dbc.Col(
                    dbc.Input(
                        id={"type": "registration_location", "user_type": user_type},
                        type="text",
                        placeholder="Enter your location",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Label(extra_label + " *"), width=3
                ),
                dbc.Col(
                    dbc.Input(
                        id={"type": "registration_extra", "user_type": user_type},
                        type="text",
                        placeholder=f"Enter your {extra_label.lower()}",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Label(subject_label + " *"), width=3
                ),
                dbc.Col(
                    dbc.Input(
                        id={"type": "registration_subject", "user_type": user_type},
                        type="text",
                        placeholder="Enter subjects (comma-separated)",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Label("Class Level *"), width=3
                ),
                dbc.Col(
                    dcc.Dropdown(
                        options=class_options,
                        id={"type": "registration_class_level", "user_type": user_type},
                        placeholder="Select your class level",
                    ),
                    width=9,
                ),
            ],
            className="mb-3",
        ),
    ]

    # Additional fields specific to 'child'
    if user_type == "child":
        form_fields += [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Category of Disability *"), width=3
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            options=category_options,
                            id={"type": "registration_category_of_disability", "user_type": user_type},
                            placeholder="Select category of disability",
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Label("Specific Disabilities"), width=3),
                    dbc.Col(
                        dcc.Checklist(
                            options=disabilities_options,
                            id={"type": "registration_disabilities", "user_type": user_type},
                            inline=False,  # Set to False for vertical layout
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Label("Assistance Needed *"), width=3),
                    dbc.Col(
                        dcc.Checklist(
                            options=assistance_options,
                            id={"type": "registration_assistance", "user_type": user_type},
                            inline=False,  # Set to False for vertical layout
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Upload Disability Certificate *"), width=3
                    ),
                    dbc.Col(
                        dcc.Upload(
                            id={"type": "registration_certificate", "user_type": user_type},
                            children=html.Div(
                                [
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]
                            ),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px 0',
                            },
                            multiple=False
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
        ]

    # Submit Button and Confirmation
    form_fields += [
        dbc.Row(
            [
                dbc.Button(
                    "Submit",
                    color="primary",
                    id={"type": "registration_submit", "user_type": user_type},
                    n_clicks=0,
                )
            ],
            justify="center",
        ),
        html.Div(id={"type": "registration_confirmation", "user_type": user_type}, className="mt-3"),
    ]

    return dbc.Form(form_fields)

# Update Form with User Type Filter
def update_form():
    return dbc.Form(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("User Type *"), width=3
                    ),
                    dbc.Col(
                        dcc.RadioItems(
                            options=[
                                {"label": "Child", "value": "child"},
                                {"label": "Scribe", "value": "scribe"},
                            ],
                            id="update_user_type",
                            value="child",
                            inline=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Email *"), width=3
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="update_email",
                            type="email",
                            placeholder="Enter your registered email",
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Fetch Details",
                        color="secondary",
                        id="update_fetch",
                        n_clicks=0,
                    ),
                    width={"size": 6, "offset": 3},
                ),
                className="mb-3",
            ),
            html.Div(id="update_fetch_alert", className="mb-3"),
            html.Div(id="update_form_content"),
        ]
    )

# Callback to handle both Child and Scribe Registration using Pattern-Matching Callbacks
@app.callback(
    Output({"type": "registration_confirmation", "user_type": ALL}, "children"),
    [
        Input({"type": "registration_submit", "user_type": ALL}, "n_clicks")
    ],
    [
        State({"type": "registration_submit", "user_type": ALL}, "id"),
        State({"type": "registration_name", "user_type": ALL}, "value"),
        State({"type": "registration_email", "user_type": ALL}, "value"),
        State({"type": "registration_location", "user_type": ALL}, "value"),
        State({"type": "registration_extra", "user_type": ALL}, "value"),
        State({"type": "registration_subject", "user_type": ALL}, "value"),
        State({"type": "registration_class_level", "user_type": ALL}, "value"),
        State({"type": "registration_category_of_disability", "user_type": ALL}, "value"),
        State({"type": "registration_disabilities", "user_type": ALL}, "value"),
        State({"type": "registration_assistance", "user_type": ALL}, "value"),
        State({"type": "registration_certificate", "user_type": ALL}, "contents"),
    ],
    prevent_initial_call=True,
)
def handle_registration(
    n_clicks,
    button_ids,
    names,
    emails,
    locations,
    extras,
    subjects,
    class_levels,
    categories,
    disabilities_list,
    assistance_list,
    certificates,
):
    ctx = callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_id = eval(triggered_id)  # Convert string dict to actual dict

    user_type = button_id["user_type"]

    # Extract form values based on user_type
    name = names[0]  # Since ALL, it's a list
    email = emails[0]
    location = locations[0]
    extra = extras[0]
    subject = subjects[0]
    class_level = class_levels[0]
    category_of_disability = categories[0]
    disabilities = disabilities_list[0]
    assistance = assistance_list[0]
    certificate_content = certificates[0]

    # Decode the uploaded file (only required for child)
    if user_type == "child":
        if certificate_content:
            try:
                content_type, content_string = certificate_content.split(',')
                decoded = base64.b64decode(content_string)
            except Exception:
                decoded = None
        else:
            return dbc.Alert("Please upload your Disability Certificate.", color="danger")
    else:
        decoded = None  # Not required for scribe

    # Register user
    confirmation = register_user(
        user_type,
        name,
        email,
        location,
        extra,
        subject,
        class_level,
        category_of_disability,
        disabilities,
        assistance,
        decoded,
    )

    return confirmation

# Callback to render tab content based on active tab
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    prevent_initial_call=True,
)
def render_tab_content(active_tab):
    if active_tab == "child_registration":
        return registration_form("child")
    elif active_tab == "scribe_registration":
        return registration_form("scribe")
    elif active_tab == "update_registration":
        return update_form()
    elif active_tab == "matching_network":
        return matching_layout()
    else:
        return html.P("This tab is not available.")

# Callback to fetch and display update form based on user type and email
@app.callback(
    Output("update_fetch_alert", "children"),
    Output("update_form_content", "children"),
    Input("update_fetch", "n_clicks"),
    State("update_user_type", "value"),
    State("update_email", "value"),
    prevent_initial_call=True,
)
def fetch_user_details(n_clicks, user_type, email):
    if n_clicks:
        if not email:
            return dbc.Alert("Please enter your registered email.", color="danger"), ""
        user = User.query.filter_by(email=email, user_type=user_type).first()
        if not user:
            return dbc.Alert(
                f"No {user_type} registration found with this email.", color="warning"
            ), ""
        # Populate the update form with existing data
        category_options = [
            {"label": "Blindness (B)", "value": "B"},
            {"label": "Low Vision (LV)", "value": "LV"},
            {"label": "Locomotor Disability (L)", "value": "L"},
            {"label": "Hearing and Speech Impairment (HI)", "value": "HI"},
            {"label": "Leprosy Cured (LC)", "value": "LC"},
            {"label": "Mental Illness (MI)", "value": "MI"},
            {"label": "Mental Retardation (MR)", "value": "MR"},
            {"label": "Autism (Aut)", "value": "Aut"},
            {"label": "Cerebral Palsy (CP)", "value": "CP"},
            {"label": "Multiple Disabilities (MD)", "value": "MD"},
            {"label": "Specific Learning Disabilities (SLD)", "value": "SLD"},
        ]

        disabilities_options = [
            {"label": "Autism", "value": "Aut"},
            {"label": "Cerebral Palsy", "value": "CP"},
            {"label": "Intellectual Disability (MR)", "value": "MR"},
            {"label": "Multiple Disabilities", "value": "MD"},
            {"label": "Blindness", "value": "B"},
            {"label": "Low Vision", "value": "LV"},
            {"label": "Hearing Impairment", "value": "HI"},
            {"label": "Leprosy Cured", "value": "LC"},
            {"label": "Specific Learning Disabilities", "value": "SLD"},
            {"label": "Deformed Fingers", "value": "DF"},
            {"label": "Other", "value": "Other"},
        ]

        assistance_options = [
            {"label": "Additional Time", "value": "additional_time"},
            {"label": "Amanuensis/Reader/Lab Assistant", "value": "amanuensis"},
            {"label": "Use of Computer with Adaptations", "value": "computer_use"},
            {"label": "Seating Arrangements", "value": "seating_arrangements"},
            {"label": "Interpreter for Sign Language", "value": "interpreter"},
            {"label": "Care Giver Support", "value": "care_giver"},
            {"label": "Other Assistance", "value": "other_assistance"},
        ]

        # Class Level options (assuming classes 1 to 12)
        class_options = [{"label": f"Class {i}", "value": i} for i in range(1, 13)]

        update_form_user = [
            dbc.Row(
                [
                    dbc.Col(dbc.Label("Name *"), width=3),
                    dbc.Col(
                        dbc.Input(
                            id="update_name",
                            type="text",
                            value=user.name,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Label("Location *"), width=3),
                    dbc.Col(
                        dbc.Input(
                            id="update_location",
                            type="text",
                            value=user.location,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Age or School Information *"), width=3
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="update_extra",
                            type="text",
                            value=user.age_or_school,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Subject Expertise/Requirements *"), width=3
                    ),
                    dbc.Col(
                        dbc.Input(
                            id="update_subject",
                            type="text",
                            value=user.subject,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label("Class Level *"), width=3
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            options=class_options,
                            id="update_class_level",
                            value=user.class_level,
                            placeholder="Select your class level",
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
        ]

        # Additional fields specific to 'child'
        if user_type == "child":
            update_form_user += [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Label("Category of Disability *"), width=3
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                options=category_options,
                                id="update_category_of_disability",
                                value=user.category_of_disability,
                                placeholder="Select category of disability",
                            ),
                            width=9,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(dbc.Label("Specific Disabilities"), width=3),
                        dbc.Col(
                            dcc.Checklist(
                                options=disabilities_options,
                                id="update_disabilities",
                                value=[
                                    d.strip()
                                    for d in user.disabilities.split(",")
                                ]
                                if user.disabilities
                                else [],
                                inline=False,  # Set to False for vertical layout
                            ),
                            width=9,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(dbc.Label("Assistance Needed *"), width=3),
                        dbc.Col(
                            dcc.Checklist(
                                options=assistance_options,
                                id="update_assistance",
                                value=[
                                    a.strip()
                                    for a in user.assistance_needed.split(",")
                                ]
                                if user.assistance_needed
                                else [],
                                inline=False,  # Set to False for vertical layout
                            ),
                            width=9,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Label("Upload Disability Certificate *"), width=3
                        ),
                        dbc.Col(
                            dcc.Upload(
                                id="update_certificate",
                                children=html.Div(
                                    [
                                        'Drag and Drop or ',
                                        html.A('Select Files')
                                    ]
                                ),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px 0',
                                },
                                multiple=False
                            ),
                            width=9,
                        ),
                    ],
                    className="mb-3",
                ),
            ]

        # Submit Button and Confirmation
        update_form_user += [
            dbc.Row(
                [
                    dbc.Button(
                        "Update",
                        color="success",
                        id="update_button",
                        n_clicks=0,
                    )
                ],
                justify="center",
            ),
            html.Div(id="update_confirmation", className="mt-3"),
        ]

        return dbc.Form(update_form_user)

# Callback to handle updating user details
@app.callback(
    Output("update_confirmation", "children"),
    [
        Input("update_button", "n_clicks"),
    ],
    [
        State("update_user_type", "value"),
        State("update_email", "value"),
        State("update_name", "value"),
        State("update_location", "value"),
        State("update_extra", "value"),
        State("update_subject", "value"),
        State("update_class_level", "value"),
        State("update_category_of_disability", "value"),
        State("update_disabilities", "value"),
        State("update_assistance", "value"),
        State("update_certificate", "contents"),  # For child
    ],
    prevent_initial_call=True,
)
def update_user(
    n_clicks,
    user_type,
    email,
    name,
    location,
    extra,
    subject,
    class_level,
    category_of_disability,
    disabilities,
    assistance,
    certificate_content,
):
    if n_clicks:
        # Validate required fields
        if user_type == "child":
            required_fields = [
                name,
                email,
                location,
                extra,
                subject,
                class_level,
                category_of_disability,
            ]
            if not all(required_fields):
                return dbc.Alert(
                    "Please fill in all required fields for child registration.",
                    color="danger",
                )
            if not certificate_content:
                return dbc.Alert(
                    "Please upload your Disability Certificate.", color="danger"
                )
        else:
            required_fields = [
                name,
                email,
                location,
                extra,
                subject,
                class_level,
            ]
            if not all(required_fields):
                return dbc.Alert(
                    f"Please fill in all required fields for {user_type} registration.",
                    color="danger",
                )

        user = User.query.filter_by(email=email, user_type=user_type).first()
        if not user:
            return dbc.Alert(
                f"No {user_type} registration found with this email.", color="warning"
            )
        try:
            user.name = name
            user.location = location
            user.age_or_school = extra
            user.subject = subject
            user.class_level = class_level
            if user_type == "child":
                user.category_of_disability = category_of_disability
                user.disabilities = ", ".join(disabilities) if disabilities else ""
                user.assistance_needed = ", ".join(assistance) if assistance else ""

                # Handle certificate upload for child
                if certificate_content:
                    try:
                        content_type, content_string = certificate_content.split(',')
                        decoded = base64.b64decode(content_string)
                        user.certificate = decoded
                    except Exception:
                        return dbc.Alert(
                            "There was an error processing the uploaded certificate.",
                            color="danger",
                        )
                else:
                    return dbc.Alert(
                        "Please upload your Disability Certificate.", color="danger"
                    )
            db.session.commit()
            return dbc.Alert(
                f"{user_type.capitalize()} registration updated successfully!",
                color="success",
            )
        except Exception as e:
            db.session.rollback()
            return dbc.Alert(f"An error occurred while updating: {str(e)}", color="danger")
    return ""

# Matching Layout
def matching_layout():
    # Query data from the database to generate filters for locations and subjects
    with server.app_context():
        all_users = User.query.all()

    locations = sorted(set([user.location for user in all_users if user.location]))
    subjects = sorted(
        set(
            [
                subj.strip()
                for user in all_users
                if user.subject
                for subj in user.subject.split(",")
            ]
        )
    )
    user_types = ["child", "scribe"]

    stylesheet = [
        {
            "selector": '[type = "child"]',
            "style": {"background-color": "#FF4136", "shape": "rectangle"},
        },
        {
            "selector": '[type = "scribe"]',
            "style": {"background-color": "#0074D9", "shape": "ellipse"},
        },
        {
            "selector": "node",
            "style": {
                "label": "data(short_name)",
                "text-valign": "center",
                "text-halign": "center",
                "font-size": "12px",
            },
        },
        {
            "selector": "edge",
            "style": {
                "label": "data(subjects)",
                "text-rotation": "autorotate",  # Rotate text along the edge
                "text-margin-y": -10,  # Slight adjustment to avoid overlap with edge line
                "text-wrap": "wrap",
                "text-max-width": 10,  # Narrow width to make it vertical
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "line-color": "#ccc",
                "target-arrow-color": "#ccc",
                "width": 2,
                "font-size": "10px",
            },
        },
    ]

    return dbc.Container(
        [
            html.H4("Scribe Matching Network"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            id="location_filter",
                            options=[{"label": loc, "value": loc} for loc in locations],
                            value=locations,  # Select all locations by default
                            multi=True,
                            placeholder="Filter by Location",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id="subject_filter",
                            options=[{"label": subj, "value": subj} for subj in subjects],
                            value=subjects,  # Select all subjects by default
                            multi=True,
                            placeholder="Filter by Subject",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Checklist(
                            id="user_type_filter",
                            options=[
                                {"label": user_type.capitalize(), "value": user_type}
                                for user_type in user_types
                            ],
                            value=user_types,  # Select all user types by default
                            inline=True,
                        ),
                        width=4,
                    ),
                ],
                className="mb-3",
            ),
            cyto.Cytoscape(
                id="matching-network",
                elements=[],
                stylesheet=stylesheet,
                style={"width": "100%", "height": "600px"},
                layout={"name": "dagre"},  # Layout type for node positioning
            ),
        ],
        fluid=True,
    )

# Callback to update the matching network based on filters
@app.callback(
    Output("matching-network", "elements"),
    [
        Input("location_filter", "value"),
        Input("subject_filter", "value"),
        Input("user_type_filter", "value"),
    ],
)
def update_matching_network(selected_locations, selected_subjects, selected_user_types):
    elements = []

    with server.app_context():
        if not selected_locations:
            selected_locations = [
                user.location for user in User.query.all() if user.location
            ]
        if not selected_subjects:
            selected_subjects = [
                subj.strip()
                for user in User.query.all()
                if user.subject
                for subj in user.subject.split(",")
            ]
        if not selected_user_types:
            selected_user_types = ["child", "scribe"]

        filtered_users = User.query.filter(
            User.location.in_(selected_locations),
            User.user_type.in_(selected_user_types),
        ).all()

    # Filter users based on subjects
    filtered_users = [
        user
        for user in filtered_users
        if any(
            subj.strip().lower() in [s.lower() for s in user.subject.split(",")]
            for subj in selected_subjects
        )
    ]

    # Create nodes for children and scribes
    for user in filtered_users:
        short_name = (
            user.name[:6] + "..." if len(user.name) > 6 else user.name
        )  # Shorten the name for display
        elements.append(
            {
                "data": {
                    "id": f"user_{user.id}",
                    "name": user.name,
                    "short_name": short_name,  # Shortened name for display
                    "label": user.name,
                    "type": user.user_type,
                    "tooltip": f"Name: {user.name}\nAge/School: {user.age_or_school}\nLocation: {user.location}\nSubjects: {user.subject}\nClass Level: {user.class_level}",
                }
            }
        )

    # Create edges between children and scribes based on shared subjects, location, and class level
    for child in filtered_users:
        if child.user_type != "child":
            continue
        for scribe in filtered_users:
            if scribe.user_type != "scribe":
                continue
            # Check location, subjects, and class level
            if child.location == scribe.location:
                child_subjects = set(
                    [subj.strip().lower() for subj in child.subject.split(",")]
                )
                scribe_subjects = set(
                    [subj.strip().lower() for subj in scribe.subject.split(",")]
                )
                common_subjects = child_subjects.intersection(scribe_subjects)
                if common_subjects:
                    # Ensure scribe's class_level is lower than child's class_level
                    if scribe.class_level < child.class_level:
                        elements.append(
                            {
                                "data": {
                                    "source": f"user_{child.id}",
                                    "target": f"user_{scribe.id}",
                                    "type": "child_scribe",
                                    "subjects": ", ".join(
                                        [subj.capitalize() for subj in common_subjects]
                                    ),
                                }
                            }
                        )

    return elements

# Callback to display a modal when a relationship (edge) is clicked
@app.callback(
    Output("modal", "is_open"),
    Output("modal-content", "children"),
    Input("matching-network", "tapEdgeData"),
    Input("close-modal", "n_clicks"),
    State("modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(edge_data, n_close, is_open):
    ctx = callback_context

    if not ctx.triggered:
        return False, ""

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == "close-modal" and n_close:
        return False, ""

    if edge_data:
        # Extract child and scribe IDs from the edge data
        try:
            child_id = int(edge_data['source'].split("_")[1])
            scribe_id = int(edge_data['target'].split("_")[1])
        except (IndexError, ValueError):
            return is_open, ""

        # Query the database for child and scribe details
        with server.app_context():
            child = User.query.get(child_id)
            scribe = User.query.get(scribe_id)

        if not child or not scribe:
            return is_open, ""

        # Prepare the modal content
        modal_content = html.Div(
            [
                html.H5(
                    "Child Details", style={"text-decoration": "underline"}
                ),
                html.P(f"Name: {child.name}"),
                html.P(f"Age: {child.age_or_school}"),
                html.P(f"Location: {child.location}"),
                html.P(f"Subjects: {child.subject}"),
                html.P(f"Class Level: {child.class_level}"),
                html.P(f"Category of Disability: {child.category_of_disability}"),
                html.P(f"Disabilities: {child.disabilities}"),
                html.P(f"Assistance Needed: {child.assistance_needed}"),
                html.Hr(),
                html.H5(
                    "Scribe Details", style={"text-decoration": "underline"}
                ),
                html.P(f"Name: {scribe.name}"),
                html.P(f"School: {scribe.age_or_school}"),
                html.P(f"Location: {scribe.location}"),
                html.P(f"Subjects: {scribe.subject}"),
                html.P(f"Class Level: {scribe.class_level}"),
                html.Hr(),
                html.H5(
                    "Matching Criteria", style={"text-decoration": "underline"}
                ),
                html.P(
                    f"Matched based on common subjects: {edge_data.get('subjects', '')}, location: {child.location}, and scribe's class level ({scribe.class_level}) is lower than child's class level ({child.class_level})."
                ),
            ]
        )
        return True, modal_content

    return is_open, ""

# Main Layout using Tabs
app.layout = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
        dbc.NavbarSimple(
            brand="Scribe Matching Platform",
            brand_href="/",
            color="primary",
            dark=True,
            className="mb-4",
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="Child Registration", tab_id="child_registration"),
                dbc.Tab(label="Scribe Registration", tab_id="scribe_registration"),
                dbc.Tab(label="Update Registration", tab_id="update_registration"),
                dbc.Tab(label="Scribe Matching Network", tab_id="matching_network"),
            ],
            id="tabs",
            active_tab="child_registration",  # Set a default active tab
        ),
        html.Div(id="tab-content"),
        # Modal for displaying match details
        dbc.Modal(
            [
                dbc.ModalHeader("Scribe Match Details"),
                dbc.ModalBody(id="modal-content"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close-modal", className="ml-auto", n_clicks=0
                    ),
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ],
    fluid=True,
)

# Running the server
if __name__ == "__main__":
    # Run the app with Flask-Migrate support
    # Ensure that you've initialized and applied migrations as per the steps below.
    app.run(use_reloader=False, debug=True, host="0.0.0.0", port=8050)
