from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from db import User
import base64
import dash_cytoscape as cyto

cyto.load_extra_layouts()

# Register all the callbacks
def register_callbacks(app, server):

    # Callback to handle both Child and Scribe Registration
    @app.callback(
        Output({"type": "registration_confirmation", "user_type": "child"}, "children"),
        Output({"type": "registration_confirmation", "user_type": "scribe"}, "children"),
        [
            Input({"type": "registration_submit", "user_type": "child"}, "n_clicks"),
            Input({"type": "registration_submit", "user_type": "scribe"}, "n_clicks")
        ],
        [
            State({"type": "registration_name", "user_type": "child"}, "value"),
            State({"type": "registration_email", "user_type": "child"}, "value"),
            State({"type": "registration_location", "user_type": "child"}, "value"),
            State({"type": "registration_extra", "user_type": "child"}, "value"),
            State({"type": "registration_subject", "user_type": "child"}, "value"),
            State({"type": "registration_class_level", "user_type": "child"}, "value"),
            State({"type": "registration_category_of_disability", "user_type": "child"}, "value"),
            State({"type": "registration_disabilities", "user_type": "child"}, "value"),
            State({"type": "registration_assistance", "user_type": "child"}, "value"),
            State({"type": "registration_certificate", "user_type": "child"}, "contents"),
            State({"type": "registration_name", "user_type": "scribe"}, "value"),
            State({"type": "registration_email", "user_type": "scribe"}, "value"),
            State({"type": "registration_location", "user_type": "scribe"}, "value"),
            State({"type": "registration_extra", "user_type": "scribe"}, "value"),
            State({"type": "registration_subject", "user_type": "scribe"}, "value"),
            State({"type": "registration_class_level", "user_type": "scribe"}, "value")
        ],
        prevent_initial_call=True,
    )
    def handle_registration(
        child_click, scribe_click,
        child_name, child_email, child_location, child_extra, child_subject, child_class_level,
        child_category, child_disabilities, child_assistance, child_certificate,
        scribe_name, scribe_email, scribe_location, scribe_extra, scribe_subject, scribe_class_level
    ):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        button_id = eval(triggered_id)  # Convert string dict to actual dict
        user_type = button_id["user_type"]

        if user_type == "child":
            # Decode the uploaded certificate file (if any)
            if child_certificate:
                try:
                    content_type, content_string = child_certificate.split(',')
                    decoded = base64.b64decode(content_string)
                except Exception:
                    decoded = None
            else:
                return dbc.Alert("Please upload your Disability Certificate.", color="danger"), ""

            # Register user for child
            return register_user(
                "child", child_name, child_email, child_location, child_extra, child_subject, child_class_level,
                child_category, child_disabilities, child_assistance, decoded
            ), ""

        elif user_type == "scribe":
            # Register user for scribe
            return "", register_user(
                "scribe", scribe_name, scribe_email, scribe_location, scribe_extra, scribe_subject, scribe_class_level,
                None, None, None, None
            )

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
            return "", populate_update_form(user, user_type)

    # Callback to handle updating user details
    @app.callback(
        Output("update_confirmation", "children"),
        Input("update_button", "n_clicks"),
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
            State("update_certificate", "contents"),
        ],
        prevent_initial_call=True,
    )
    def update_user(
        n_clicks, user_type, email, name, location, extra, subject, class_level,
        category_of_disability, disabilities, assistance, certificate_content
    ):
        if n_clicks:
            # Validate required fields
            if user_type == "child" and not certificate_content:
                return dbc.Alert("Please upload your Disability Certificate.", color="danger")

            # Update the user
            return update_user_in_db(user_type, email, name, location, extra, subject, class_level,
                                     category_of_disability, disabilities, assistance, certificate_content)

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
        return get_matching_elements(selected_locations, selected_subjects, selected_user_types)

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
            return display_modal(edge_data)

        return is_open, ""


# Helper functions

def register_user(user_type, name, email, location, extra, subject, class_level,
                  category_of_disability, disabilities, assistance, certificate):
    # Add your logic to register the user in the database
    # Returns a confirmation message or error
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


def populate_update_form(user, user_type):
    # Populate and return the update form based on user details
    # This will use the `user` data to pre-fill the update form
    # ...
    pass


def update_user_in_db(user_type, email, name, location, extra, subject, class_level,
                      category_of_disability, disabilities, assistance, certificate_content):
    # Logic to update the user in the database
    # ...
    pass


def get_matching_elements(selected_locations, selected_subjects, selected_user_types):
    elements = []

    # Query users based on filters
    with server.app_context():
        filtered_users = User.query.filter(
            User.location.in_(selected_locations),
            User.user_type.in_(selected_user_types),
        ).all()

    # Further filter by subjects and create nodes and edges
    for user in filtered_users:
        short_name = user.name[:6] + "..." if len(user.name) > 6 else user.name
        elements.append({
            "data": {
                "id": f"user_{user.id}",
                "name": user.name,
                "short_name": short_name,
                "type": user.user_type,
                "tooltip": f"Name: {user.name}\nLocation: {user.location}",
            }
        })

    # Add logic to create edges between children and scribes
    # ...

    return elements


def display_modal(edge_data):
    # Display modal content based on the edge data (child-scribe relationship)
    try:
        child_id = int(edge_data['source'].split("_")[1])
        scribe_id = int(edge_data['target'].split("_")[1])
    except (IndexError, ValueError):
        return False, ""

    with server.app_context():
        child = User.query.get(child_id)
        scribe = User.query.get(scribe_id)

    if not child or not scribe:
        return False, ""

    modal_content = html.Div([
        html.H5("Child Details"),
        html.P(f"Name: {child.name}"),
        # Add more fields from child and scribe details
        html.Hr(),
        html.H5("Scribe Details"),
        html.P(f"Name: {scribe.name}"),
        # Add more fields...
    ])

    return True, modal_content
