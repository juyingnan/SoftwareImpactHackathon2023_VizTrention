import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

app = dash.Dash(__name__)

# data processing
ROOT_DATA_DIR = r'ROOTPATH'

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

# Function to update the figure based on the selected N
def update_figure(selected_N, value_type, year_range):
    # Filter data based on the selected year range
    df_filtered = disambiguated_df[(disambiguated_df['year'] >= year_range[0]) & (disambiguated_df['year'] <= year_range[1])]

    software_counts = df_filtered['mapped_to_software'].value_counts()
    top_software = software_counts.head(selected_N)

    top_software_trends = df_filtered[
        df_filtered['mapped_to_software'].isin(top_software.index)
    ].groupby(['year', 'mapped_to_software']).size().unstack().fillna(0)

    # Calculate the total mentions of all software in each year
    total_mentions_per_year = df_filtered.groupby('year')['mapped_to_software'].size()

    if value_type == 'percentage':
        # Use total mentions for percentage calculation
        top_software_trends = top_software_trends.divide(total_mentions_per_year, axis=0) * 100
        top_software_trends = top_software_trends.fillna(0)  # fill NaN values with 0

    top_software_trends = top_software_trends.reset_index()
    melted_df = pd.melt(top_software_trends, id_vars='year', var_name='Software', value_name='Count')

    y_label = 'Percentage of Mentions' if value_type == 'percentage' else 'Number of Mentions'
    
    fig = px.area(
        melted_df,
        x='year',
        y='Count',
        color='Software',
        title=f'Trend of Software Mentions Over Time (Top {selected_N})',
        labels={'Count': y_label}
    )

    for i in range(len(fig['data'])):
        fig['data'][i]['line']['width'] = 0

    return fig

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
                ],
                value=25,  # default value
            )
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px'}),

        html.Div([
            html.H6('Value Type:', style={'marginBottom': 5, 'marginTop': 0}),
            dcc.Dropdown(
                id='value-type-selector',
                options=[
                    {'label': 'Absolute', 'value': 'absolute'},
                    {'label': 'Percentage', 'value': 'percentage'}
                ],
                value='percentage',  # default value
            )
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px', 'marginLeft': '5px'}),
    ], style={'marginBottom': '10px'}),

    html.Div([
        dcc.RangeSlider(
            id='year-slider',
            min=1970,
            max=2021,
            step=1,
            marks={i: str(i) for i in range(1970, 2022, 5)},
            value=[1995, 2021]  # default value
        )
    ], style={'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px', 'marginBottom': '20px'}),

dcc.Graph(
        id='software-trend',
        figure=update_figure(25, 'percentage', [1995, 2021]),
        style={'height': '70vh'}  # Set the height of the graph
    ),
], style={'padding': '10px', 'height': '100vh', 'margin': '0'})


@app.callback(
    Output('software-trend', 'figure'),
    [Input('n-selector', 'value'),
     Input('value-type-selector', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(selected_N, value_type, year_range):
    return update_figure(selected_N, value_type, year_range)

if __name__ == '__main__':
    app.run_server(debug=False)
