import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import json

app = dash.Dash(__name__)

# Read the precomputed Sankey data
with open('sankey_data.json', 'r') as f:
    sankey_data = json.load(f)

min_year = min(map(int, sankey_data.keys()))
max_year = max(map(int, sankey_data.keys()))

# Function to create the Sankey diagram
def create_sankey(connections_df, selected_N):
    # Ensure the 'Count' column is of numeric type
    connections_df['Count'] = pd.to_numeric(connections_df['Count'], errors='coerce')
    
    # Drop rows with non-numeric 'Count' values
    connections_df = connections_df.dropna(subset=['Count'])
    
    top_connections = connections_df.nlargest(selected_N, 'Count')
    
    all_software = pd.concat([top_connections['Source'], top_connections['Target']]).unique()
    nodes = [{'name': software} for software in all_software]
    
    links = []
    for index, row in top_connections.iterrows():
        source_index = list(all_software).index(row['Source'])
        target_index = list(all_software).index(row['Target'])
        links.append({'source': source_index, 'target': target_index, 'value': row['Count']})
    
    sankey_figure = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=[node['name'] for node in nodes]
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links]
        )
    ))

    sankey_figure.update_layout(title_text="Software Mentions Connections", font_size=10)
    return sankey_figure

@app.callback(
    Output('software-connections', 'figure'),
    [Input('n-selector', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(selected_N, year_range):
    combined_connections = pd.DataFrame(columns=['Source', 'Target', 'Count'])
    
    for year in range(year_range[0], year_range[1] + 1):
        year_str = str(year)
        if year_str in sankey_data:
            year_connections = pd.DataFrame(sankey_data[year_str])
            combined_connections = pd.concat([combined_connections, year_connections])
    
    combined_connections = combined_connections.groupby(['Source', 'Target'], as_index=False).sum()
    return create_sankey(combined_connections, selected_N)

# Dash app layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.H6('N Most Cited Software:', style={'marginBottom': 5, 'marginTop': 0}),
            dcc.Dropdown(
                id='n-selector',
                options=[
                    {'label': 'Top 5', 'value': 5},
                    {'label': 'Top 10', 'value': 10},
                    {'label': 'Top 25', 'value': 25},
                    {'label': 'Top 50', 'value': 50},
                    {'label': 'Top 100', 'value': 100},
                ],
                value=50  # default value
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px'}),
    ], style={'marginBottom': '10px'}),

    html.Div([
        dcc.RangeSlider(
            id='year-slider',
            min=1970,
            max=2021,
            step=1,
            marks={i: str(i) for i in range(1970, 2021 + 1, 5)},
            value=[1995, max_year]  # default value
        )
    ], style={'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px', 'marginBottom': '20px'}),

    dcc.Graph(
        id='software-connections',
        style={'height': '70vh'}  # Set the height of the graph
    ),
], style={'padding': '10px', 'height': '100vh', 'margin': '0'})


if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
