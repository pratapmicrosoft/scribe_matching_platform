from dash import dcc, html
import dash_bootstrap_components as dbc

def create_layout():
    return dbc.Container(
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
