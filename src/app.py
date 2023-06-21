import base64
import io

import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html

import plotly.graph_objects as go

import pandas as pd

import dash_auth

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)
server = app.server

auth = dash_auth.BasicAuth(
    app,
    {'arnlab': '7271'}
)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

shape_lo = go.Layout(
    clickmode='event',
)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '96%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'solid',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': 'auto',
            'margin-top': '25px'
        },
        multiple=True
    ),
    html.Div(id='output-datatable'),
    html.Div(id="output-div", children=[]),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        return html.Div([
            f'There was an error processing this file. {e}'
        ])

    array_options = []
    for x in df.columns.difference([df.columns[0]]):
        if x.split('-')[0] not in array_options \
                and x.split(':')[0] != "Unnamed":
            array_options.append(x.split('-')[0])

    return html.Div([
        html.P(' '),
        html.Div([html.P("Choose analysis of interest:"),
                  html.Div(html.Div([
                      dcc.Dropdown(id='analysis', clearable=False, value=array_options[0],
                                   options=[{'label': x, 'value': x} for x in array_options]),
                      html.P(' '),
                  ], className="eight columns"), className="row"),
                  html.Div([
                      html.P("Display the dispersion measurements values of the control: "),
                      dcc.Input(id='input', value='', type='text'),
                  ], style={'display': 'flex', 'column-gap': '10px', 'margin-bottom': '10px'})
                  ], className="offset-by-two columns"),

        dcc.Store(id='stored-data', data=df.to_dict('records'))
    ])


@app.callback(Output('output-datatable', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

@app.callback(Output(component_id="output-div", component_property="children"),
              Input(component_id="analysis", component_property="value"),
              Input(component_id="input", component_property="value"),
              State('stored-data', 'data'))
def make_graph(analysis_chosen, data_input, data):
    data = pd.DataFrame(data)
    fig = go.Figure(layout=shape_lo)
    array_of_analysis_chosen = []
    nr_of_controls = 0
    for x_columns in data.columns.difference([data.columns[0]]):
        if analysis_chosen + '-' in x_columns:
            array_of_analysis_chosen.append(x_columns)
            nr_of_controls = nr_of_controls + 1
    data_analiza = []
    nr_analize_fara_null = 0
    index_verificare_null = 0
    if nr_of_controls == 2:
        for x in data[array_of_analysis_chosen[0]]:
            if pd.isnull(x) == 0:
                data_analiza.append({data.columns[0]: data.iat[index_verificare_null, 0]
                                    , array_of_analysis_chosen[0]: x, array_of_analysis_chosen[1]:
                                    data[array_of_analysis_chosen[1]].iloc[index_verificare_null]})
                nr_analize_fara_null = nr_analize_fara_null + 1
            index_verificare_null = index_verificare_null + 1
        data_analiza = pd.DataFrame(data_analiza)
    else:
        for x in data[array_of_analysis_chosen[0]]:
            if pd.isnull(x) == 0:
                data_analiza.append({data.columns[0]: data.iat[index_verificare_null, 0]
                                    , array_of_analysis_chosen[0]: x, array_of_analysis_chosen[1]:
                                    data[array_of_analysis_chosen[1]].iloc[index_verificare_null],
                                    array_of_analysis_chosen[2]:
                                    data[array_of_analysis_chosen[2]].iloc[index_verificare_null]})
                nr_analize_fara_null = nr_analize_fara_null + 1
            index_verificare_null = index_verificare_null + 1
        data_analiza = pd.DataFrame(data_analiza)

    data_inverted = []
    for x in data_analiza[data_analiza.columns[0]]:
        data_x_inverted = x.split('.')[2] + '.' + x.split('.')[1] + '.' + x.split('.')[0]
        data_inverted.append(data_x_inverted)

    data_analiza[data_analiza.columns[0]] = data_inverted
    data_analiza = data_analiza.sort_values(data.columns[0])

    medie_plus3ds = data_analiza[array_of_analysis_chosen[1]].mean() + (
                3 * data_analiza[array_of_analysis_chosen[1]].std())
    medie_plus2ds = data_analiza[array_of_analysis_chosen[1]].mean() + (
                2 * data_analiza[array_of_analysis_chosen[1]].std())
    medie_plus1ds = data_analiza[array_of_analysis_chosen[1]].mean() + (
                1 * data_analiza[array_of_analysis_chosen[1]].std())
    medie_minus1ds = data_analiza[array_of_analysis_chosen[1]].mean() - (
                1 * data_analiza[array_of_analysis_chosen[1]].std())
    medie_minus2ds = data_analiza[array_of_analysis_chosen[1]].mean() - (
                2 * data_analiza[array_of_analysis_chosen[1]].std())
    medie_minus3ds = data_analiza[array_of_analysis_chosen[1]].mean() - (
                3 * data_analiza[array_of_analysis_chosen[1]].std())

    lines = []
    annotations = []

    nr_ds = 3
    while nr_ds != (-4):
        medie = data_analiza[array_of_analysis_chosen[1]].mean() + \
                (nr_ds * data_analiza[array_of_analysis_chosen[1]].std())
        line_color = "red" if nr_ds == 3 or nr_ds == -3 else "lightgrey"
        fig.add_hline(y=medie, line_color=line_color, layer="below")
        lines.append(fig.layout.shapes[-1])
        nr_ds = nr_ds - 1

    if data_input != '':
        nr_ds = 3
        for line in lines:
            medie_annotation = data_analiza[data_input].mean() + (nr_ds * data_analiza[data_input].std())
            annotations.append(
                dict(
                    x=1,
                    y=line['y0'],
                    xref="paper",
                    yref="y",
                    text=str(round(medie_annotation, 2)),
                    showarrow=False,
                    align="right",
                )
            )
            nr_ds = nr_ds - 1

    fig.update_layout(annotations=annotations)

    nr_add_trace = 0
    while nr_add_trace < nr_of_controls:
        fig.add_trace(go.Scatter(x=data_analiza[data.columns[0]], y=data_analiza[array_of_analysis_chosen[1]].mean() + (
                    data_analiza[array_of_analysis_chosen[nr_add_trace]] -
                    data_analiza[array_of_analysis_chosen[nr_add_trace]].mean())
                    * data_analiza[array_of_analysis_chosen[1]].std()
                    / data_analiza[array_of_analysis_chosen[nr_add_trace]].std(),
                    customdata=data_analiza[array_of_analysis_chosen[nr_add_trace]],
                    hovertemplate='(%{x}, %{customdata})',
                    name=array_of_analysis_chosen[nr_add_trace]))
        if nr_add_trace == 0:
            fig.add_trace(go.Scatter(x=data_analiza[data.columns[0]], y=data_analiza[array_of_analysis_chosen[1]],
                                     name=array_of_analysis_chosen[1]))
        nr_add_trace = nr_add_trace + 2

    fig.update_yaxes(ticktext=["-3SD", "-2SD", "-1SD", "X", "1SD", "2SD", "3SD"],
                     tickvals=[medie_minus3ds, medie_minus2ds, medie_minus1ds,
                               data_analiza[array_of_analysis_chosen[1]].mean(),
                               medie_plus1ds, medie_plus2ds, medie_plus3ds])
    fig.update_annotations()
    fig.update_traces(mode="markers+lines")
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(showgrid=False, zeroline=False, categoryorder='category ascending')

    warnings = []

    for date in data_analiza[data.columns[0]]:
        # Get the data for the current date
        data_for_date = data_analiza[data_analiza['Data'] == date]

        for i in range(len(array_of_analysis_chosen)):
            for j in range(i + 1, len(array_of_analysis_chosen)):
                column1 = array_of_analysis_chosen[i]
                column2 = array_of_analysis_chosen[j]

                data1 = data_analiza[array_of_analysis_chosen[1]].mean() + \
                        (data_for_date[column1] - data_analiza[column1].mean()) * data_analiza[array_of_analysis_chosen[1]].std() \
                        / data_analiza[column1].std()

                data2 = data_analiza[array_of_analysis_chosen[1]].mean() + \
                        (data_for_date[column2] - data_analiza[column2].mean()) * data_analiza[array_of_analysis_chosen[1]].std() \
                        / data_analiza[column2].std()

                diff = abs(data1 - data2)

                over_4sd = diff > 4 * data_analiza[array_of_analysis_chosen[1]].std()

                if any(over_4sd):
                    warnings.append(('Red',
                                     f'Warning: The difference between controls {column1} and {column2} is over 4 Standard Deviations on {date}.'))

        over_2sd_counts = 0
        under_2sd_counts = 0
        for column in array_of_analysis_chosen:
            control_data = data_for_date[column]
            over_2sd = control_data > data_analiza[column].mean() + 2 * data_analiza[column].std()
            under_2sd = control_data < data_analiza[column].mean() - 2 * data_analiza[column].std()
            if any(over_2sd):
                over_2sd_counts += 1
            if any(under_2sd):
                under_2sd_counts += 1
        if over_2sd_counts >= 2 or under_2sd_counts >= 2:
            warnings.append(('Red', f'Warning: 2 controls are over 2 Standard Deviations on {date}.'))

    for column in array_of_analysis_chosen:
        medie_analysisPlus3DS = data_analiza[column].mean() + (3 * data_analiza[column].std())
        medie_analysisMinus3DS = data_analiza[column].mean() - (3 * data_analiza[column].std())
        control_data = data_analiza[column]

        if any(control_data > medie_analysisPlus3DS):
            warnings.append(('Red', f'Warning: {column} has a control above 3 Standard Deviations.'))

        if any(control_data < medie_analysisMinus3DS):
            warnings.append(('Red', f'Warning: {column} has a control under 3 Standard Deviations.'))

        over_2sd = control_data > data_analiza[column].mean() + 2 * data_analiza[column].std()
        under_2sd = control_data < data_analiza[column].mean() - 2 * data_analiza[column].std()
        if any(over_2sd[:-1].reset_index(drop=True) & over_2sd[1:].reset_index(drop=True)) or \
                any(under_2sd[:-1].reset_index(drop=True) & under_2sd[1:].reset_index(drop=True)):
            warnings.append(('Red', f'Warning: {column} has 2 consecutive measurements over 2 Standard Deviations.'))

        over_1sd = control_data > data_analiza[column].mean() + data_analiza[column].std()
        under_1sd = control_data < data_analiza[column].mean() - data_analiza[column].std()
        if any(over_1sd[:-3].reset_index(drop=True) & over_1sd[1:-2].reset_index(drop=True) & over_1sd[2:-1].reset_index
                (drop=True) & over_1sd[3:].reset_index(drop=True)) or \
                any(under_1sd[:-3].reset_index(drop=True) & under_1sd[1:-2].reset_index(drop=True)
                    & under_1sd[2:-1].reset_index(drop=True) & under_1sd[3:].reset_index(drop=True)):
            warnings.append(('Yellow',
                             f'Warning: {column} has 4 consecutive measurements on the same side of the mean above or under 1 Standard Deviation.'))

        over_mean = control_data > data_analiza[column].mean()
        under_mean = control_data < data_analiza[column].mean()
        if any((over_mean[:-9].reset_index(drop=True)) & (over_mean[1:-8].reset_index(drop=True)) & (
            over_mean[2:-7].reset_index(drop=True)) & (over_mean[3:-6].reset_index(drop=True)) & (
               over_mean[4:-5].reset_index(drop=True)) & (over_mean[5:-4].reset_index(drop=True))
               & (over_mean[6:-3].reset_index(drop=True)) & (over_mean[7:-2].reset_index(drop=True)) & (
               over_mean[8:-1].reset_index(drop=True)) & (over_mean[9:].reset_index(drop=True))) or \
                any((under_mean[:-9].reset_index(drop=True)) & (under_mean[1:-8].reset_index(drop=True)) & (
                under_mean[2:-7].reset_index(drop=True)) & (under_mean[3:-6].reset_index(drop=True)) & (
                    under_mean[4:-5].reset_index(drop=True))
                    & (under_mean[5:-4].reset_index(drop=True)) & (under_mean[6:-3].reset_index(drop=True)) & (
                    under_mean[7:-2].reset_index(drop=True)) & (under_mean[8:-1].reset_index(drop=True)) & (
                    under_mean[9:].reset_index(drop=True))):
            warnings.append(
                ('Yellow', f'Warning: {column} has 10 consecutive measurements on the same side of the mean.'))

        diff = control_data.diff()
        if any((diff[:-5].reset_index(drop=True) > 0) & (diff[1:-4].reset_index(drop=True) > 0) &
               (diff[2:-3].reset_index(drop=True) > 0) & (diff[3:-2].reset_index(drop=True) > 0) &
               (diff[4:-1].reset_index(drop=True) > 0) & (diff[5:].reset_index(drop=True) > 0)) or \
                any((diff[:-5].reset_index(drop=True) < 0) & (diff[1:-4].reset_index(drop=True) < 0) &
                    (diff[2:-3].reset_index(drop=True) < 0) & (diff[3:-2].reset_index(drop=True) < 0) &
                    (diff[4:-1].reset_index(drop=True) < 0) & (diff[5:].reset_index(drop=True) < 0)):
            warnings.append(('Yellow', f'Warning: {column} has 7 consecutive measurements that increase or decrease.'))

    warning_divs = []
    for color, message in warnings:
        bg_color = []
        if color == 'Red':
            bg_color = 'rgba(255, 0, 0, 0.1)'  # Light red
        elif color == 'Yellow':
            bg_color = 'rgba(255, 165, 0, 0.1)'  # Light yellow
        if color == 'Yellow':
            color = 'rgba(255, 165, 0)'
        warning_divs.append(html.Div(
            message, style={
                'border': f'1px solid {color}',
                'borderRadius': '5px',
                'padding': '10px',
                'textAlign': 'center',
                'color': color,
                'backgroundColor': bg_color,
                'width': '65%',  # Set the width to 80% of the parent div
                'margin': 'auto',  # Center the div
                'margin-bottom': '10px'
            })
        )
    return [
        html.Div([
            html.Div([
                html.Div([dcc.Graph(id='basic-interactions', figure=fig)], id='graph-div', className="twelve columns"),
                html.Div(warning_divs, className="twelve columns",
                             style={'justifyContent': 'center', 'alignItems': 'center'}),
            ], className="row"),
        ])
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
