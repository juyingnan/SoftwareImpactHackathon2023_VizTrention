import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go

app = dash.Dash(__name__)

# data processing
ROOT_DATA_DIR = r'C:\Users\bunny\Desktop\doi_10.5061_dryad.6wwpzgn2c__v8'

using_sample = True
file_path = ROOT_DATA_DIR + '/disambiguated/comm_disambiguated.tsv'
if using_sample:
    file_path = file_path[:-4] + '_sample.tsv'

disambiguated_df = pd.read_csv(
    file_path,
    sep='\t',
    engine='python',
    # compression='gzip',
    # nrows=2000000
)

# filter ['mapped_to_software'] != 'not_disambiguated' and ['curation_label'] != 'not_software'
disambiguated_df = disambiguated_df[disambiguated_df['mapped_to_software'] != 'not_disambiguated']
disambiguated_df = disambiguated_df[disambiguated_df['curation_label'] != 'not_software']

disambiguated_df['year'] = disambiguated_df['pubdate'].astype(str).str[:4].astype(int, errors='ignore')
disambiguated_df['year'] = disambiguated_df['year'].dropna().astype(int)

min_year = disambiguated_df['year'].min()
max_year = disambiguated_df['year'].max()

# Function to create the Sankey diagram
def create_sankey(df, selected_N):
    # Calculate the connections between software mentions
    connections = {}
    for uid, group in df.groupby('doi'):
        softwares = group['mapped_to_software'].unique()
        for i in range(len(softwares)):
            for j in range(i+1, len(softwares)):
                # Ensure the smaller software name comes first in the tuple
                software_pair = tuple(sorted((softwares[i], softwares[j])))
                if software_pair not in connections:
                    connections[software_pair] = 1
                else:
                    connections[software_pair] += 1

    # Convert connections to a DataFrame
    connections_df = pd.DataFrame(list(connections.items()), columns=['Connection', 'Count'])
    connections_df[['Source', 'Target']] = pd.DataFrame(connections_df['Connection'].tolist(), index=connections_df.index)
    connections_df = connections_df.drop('Connection', axis=1)
    
    # Select the top N connections
    top_connections = connections_df.nlargest(selected_N, 'Count')
    
    # Create the nodes for the Sankey diagram
    all_software = pd.concat([top_connections['Source'], top_connections['Target']]).unique()
    nodes = [{'name': software} for software in all_software]
    
    # Create the links for the Sankey diagram
    links = []
    for index, row in top_connections.iterrows():
        source_index = list(all_software).index(row['Source'])
        target_index = list(all_software).index(row['Target'])
        links.append({'source': source_index, 'target': target_index, 'value': row['Count']})
    
    # Create the Sankey diagram
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
    # Filter data based on the selected year range
    df_filtered = disambiguated_df[(disambiguated_df['year'] >= year_range[0]) & (disambiguated_df['year'] <= year_range[1])]
    return create_sankey(df_filtered, selected_N)

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
