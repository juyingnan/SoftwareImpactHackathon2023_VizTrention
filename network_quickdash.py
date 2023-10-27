import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import json
import numpy as np
import igraph as ig

app = dash.Dash(__name__)

# Read the precomputed Sankey data
with open('sankey_data.json', 'r') as f:
    sankey_data = json.load(f)

min_year = min(map(int, sankey_data.keys()))
max_year = max(map(int, sankey_data.keys()))

def create_network(connections_df, selected_N, year_range):
    # Ensure the 'Count' column is of numeric type
    connections_df['Count'] = pd.to_numeric(connections_df['Count'], errors='coerce')
    
    # Drop rows with non-numeric 'Count' values
    connections_df = connections_df.dropna(subset=['Count'])
    
    top_connections = connections_df.nlargest(selected_N, 'Count')
    
    # Create a directed graph
    G = ig.Graph(directed=True)
    
    all_nodes = pd.concat([top_connections['Source'], top_connections['Target']]).unique()
    G.add_vertices(all_nodes)
    
    for index, row in top_connections.iterrows():
        G.add_edge(row['Source'], row['Target'], weight=row['Count'])
   
    # Compute the layout of the graph
    layout = G.layout('auto') # Kamada-Kawai layout
    
    # Extract node positions from the layout
    node_x = [pos[0] for pos in layout.coords]
    node_y = [pos[1] for pos in layout.coords]
    
    # Compute the size of nodes based on the total connection count
    node_sizes = []
    node_labels = []
    limit = 75 # Set a limit on the number of nodes to label
    for node in G.vs:
        in_edges = G.es.select(_target_in=[node.index])
        out_edges = G.es.select(_source_in=[node.index])
        total_weight = sum(in_edges['weight']) + sum(out_edges['weight'])
        node_sizes.append(np.sqrt(total_weight) * 0.2)  # Adjust size multiplier as needed
        if len(node_labels) < limit:
            node_labels.append(node['name'])
        else:
            node_labels.append('')

    label_trace = go.Scatter(
        x=node_x, y=node_y,
        text=node_labels,
        textposition="top center",
        mode='text',
        hoverinfo='none'
    )
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Burg',
            size=node_sizes,  # Set node sizes based on total connection count
            colorbar=dict(
                thickness=15,
                title='Connections',
                xanchor='left',
                titleside='right'
            )
        )
    )

    # Calculate the degree of each node
    node_degrees = np.array(G.degree())

    node_trace.marker.color = node_degrees
    node_trace.marker.cmin = min(node_degrees)
    node_trace.marker.cmax = max(node_degrees)
    node_trace.marker.colorbar.title = 'Connections'
    node_trace.marker.colorbar.tickvals = [min(node_degrees), max(node_degrees)]
    node_trace.marker.colorbar.ticktext = [min(node_degrees), max(node_degrees)]
    
    node_text = []
    for node in G.vs:
        node_text.append(f'{node["name"]}<br># of connections: {G.degree(node.index)}<br>Total connections: {sum(G.es.select(_source_in=[node.index])["weight"]) + sum(G.es.select(_target_in=[node.index])["weight"])}')
    
    node_trace.text = node_text
    
    # Normalize edge weights to range [0, 1]
    edge_weights = np.array(G.es['weight'])
    edge_weight_range = max(edge_weights) - min(edge_weights)
    normalized_weights = (edge_weights - min(edge_weights)) / (edge_weight_range if edge_weight_range != 0 else 1)

    min_alpha = 0.1  # Set minimum alpha for visibility
    alpha_range = 0.7  # Set the range of alpha values, min 0.1 / max 0.8
    
    traces = []  # List to store all the traces
    
    for edge, weight in zip(G.es, normalized_weights):
        source_idx, target_idx = edge.tuple
        edge_x = [layout.coords[source_idx][0], layout.coords[target_idx][0]]
        edge_y = [layout.coords[source_idx][1], layout.coords[target_idx][1]]
        
        alpha = min_alpha + alpha_range * weight  # Ensure a minimum alpha for visibility
        thickness = 1 + 9 * weight  # Adjust thickness based on weight, e.g., from 1 to 10
        
        # Create a trace for each edge
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=thickness, color=f'rgba(0, 0, 0, {alpha})'),
            hoverinfo='text',
            text=f'Connections: {edge["weight"]}',  # Hover text
            mode='lines'
        )
        
        traces.append(edge_trace)

    hover_x = []
    hover_y = []
    hover_text = []
    for edge, weight in zip(G.es, edge_weights):
        source_idx, target_idx = edge.tuple
        x0, y0 = layout.coords[source_idx]
        x1, y1 = layout.coords[target_idx]
        hover_x.append((x0 + x1) / 2)
        hover_y.append((y0 + y1) / 2)
        hover_text.append(f'Connections: {edge["weight"]}')

    # Creating a trace for edge hover points
    hover_trace = go.Scatter(
        x=hover_x, y=hover_y,
        text=hover_text,
        mode='markers',
        hoverinfo='text',
        marker=dict(color='rgba(0,0,0,0)', size=5),
    )

    # Create a Plotly figure
    fig = go.Figure(data=traces + [node_trace, label_trace, hover_trace],  # Add all edge traces and the node trace
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0,l=0,r=0,t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                annotations=[
                            dict(
                                x=0.025,
                                y=0.025,
                                xref='paper',
                                yref='paper',
                                showarrow=False,
                                text=f'Year Range: {year_range[0]} - {year_range[1]}',
                                font=dict(size=20),
                                align='center',
                            )
                        ]
                    )
                )
    return fig

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
    return create_network(combined_connections, selected_N, year_range)

# Play/pause animation callback
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('play-button', 'children')],
    Input('play-button', 'n_clicks'),
    State('interval-component', 'disabled'),
)
def play_pause_animation(n_clicks, is_disabled):
    if n_clicks is None or n_clicks == 0:
        # On initial load, don't update anything
        raise dash.exceptions.PreventUpdate
    # Toggle the 'disabled' property of the interval component
    new_disabled_state = not is_disabled
    # Set button label to "Play" if the animation will be stopped, and "Stop" if it will be running
    button_label = "Play" if new_disabled_state else "Stop"
    return new_disabled_state, button_label

@app.callback(
    Output('year-slider', 'value'),
    Input('interval-component', 'n_intervals'),
    State('year-slider', 'value'),
)
def update_slider(n_intervals, current_year_range):
    max_year = 2021  # Replace with your max year
    if current_year_range[1] < max_year:
        return [current_year_range[0], current_year_range[1] + 1]
    else:
        return [current_year_range[0], max_year]

# Dash app layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.H6('Most Mentioned Software:', style={'marginBottom': 5, 'marginTop': 0}),
            dcc.Dropdown(
                id='n-selector',
                options=[
                    {'label': 'Top 5', 'value': 5},
                    {'label': 'Top 10', 'value': 10},
                    {'label': 'Top 25', 'value': 25},
                    {'label': 'Top 50', 'value': 50},
                    {'label': 'Top 100', 'value': 100},
                    {'label': 'Top 250', 'value': 250},
                ],
                value=100  # default value
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px'}),
    ], style={'marginBottom': '10px'}),

    html.Div([
        dcc.RangeSlider(
            id='year-slider',
            min=1990,
            max=2021,
            step=1,
            marks={i: str(i) for i in range(1990, 2021 + 1, 5)},
            value=[1995, max_year]  # default value
        )
    ], style={'padding': '10px', 'boxShadow': '0px 0px 5px #ccc', 'borderRadius': '5px', 'marginBottom': '20px'}),

    html.Button('Play', id='play-button', n_clicks=0),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0,
        disabled=True,  # disabled on start
    ),

    dcc.Graph(
        id='software-connections',
        style={'height': '70vh'}  # Set the height of the graph
    ),
], style={'padding': '10px', 'height': '100vh', 'margin': '0'})

if __name__ == '__main__':
    app.run_server(debug=False, port=8052)
