import json
from textwrap import dedent as d
import datetime

import base64
import io

import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html

import plotly.graph_objects as go

import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)
server = app.server

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
        print(e)
        return html.Div([
            'There was an error processing this file.'
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
                  ], style={'display': 'flex', 'column-gap': '10px'})
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
        if analysis_chosen in x_columns:
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
        print(data_analiza)
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
        print(data_analiza)

    data_inverted = []
    for x in data_analiza[data_analiza.columns[0]]:
        data_x_inverted = x.split('.')[2] + '.' + x.split('.')[1] + '.' + x.split('.')[0]
        data_inverted.append(data_x_inverted)

    data_analiza[data_analiza.columns[0]] = data_inverted
    print(data_inverted)
    data_analiza = data_analiza.sort_values(data.columns[0])
    print(data_analiza)

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

    fig.add_trace(go.Scatter(
        x=[data_analiza.iat[0, 0], data_analiza.iat[len(data_analiza) - 1, 0],
           data_analiza.iat[len(data_analiza) - 1, 0],
           data_analiza.iat[0, 0], data_analiza.iat[0, 0]],
        y=[medie_minus3ds, medie_minus3ds, medie_plus3ds, medie_plus3ds, medie_minus3ds],
        fill='toself',
        mode='none',
        name='background',
        opacity=0.1,
        showlegend=False,
    ))
    if data_input == '':
        nr_ds = 3
        while nr_ds != (-4):
            medie = data_analiza[array_of_analysis_chosen[1]].mean() + \
                    (nr_ds * data_analiza[array_of_analysis_chosen[1]].std())
            if nr_ds == 3 or nr_ds == -3:
                fig.add_hline(y=medie, line_color="red", layer="below")
                nr_ds = nr_ds - 1
            else:
                fig.add_hline(y=medie, line_color="lightgrey", layer="below")
                nr_ds = nr_ds - 1
    else:
        nr_ds = 3
        while nr_ds != (-4):
            medie = data_analiza[array_of_analysis_chosen[1]].mean() + \
                    (nr_ds * data_analiza[array_of_analysis_chosen[1]].std())
            medie_annotation = data_analiza[data_input].mean() + (nr_ds * data_analiza[data_input].std())
            if nr_ds == 3 or nr_ds == -3:
                fig.add_hline(y=medie, line_color="red", annotation_text=round(medie_annotation, 2),
                              annotation_position="top right",
                              layer="below")
                nr_ds = nr_ds - 1
            else:
                fig.add_hline(y=medie, line_color="lightgrey", annotation_text=round(medie_annotation, 2),
                              annotation_position="top right",
                              layer="below")
                nr_ds = nr_ds - 1

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

    return [
        html.Div([
            html.Div([
                html.Div([dcc.Graph(id='basic-interactions', figure=fig)], id='graph-div', className="twelve columns"),
            ], className="row"),
        ])
    ]

if __name__ == '__main__':
    app.run_server(debug=False)