import pandas as pd

ROOT_DATA_DIR = r'C:\Users\bunny\Desktop\doi_10.5061_dryad.6wwpzgn2c__v8'

disambiguated_df = pd.read_csv(
    ROOT_DATA_DIR + '/disambiguated/comm_disambiguated.tsv.gz',
    sep='\t',
    engine='python',
    compression='gzip',
    nrows=1000000  # Load only the first 1,000,000 rows for initial testing
)

disambiguated_df['mapped_to_software'] = disambiguated_df.apply(
    lambda x: x['software'] if x['mapped_to_software'] == 'not_disambiguated' else x['mapped_to_software'],
    axis=1
)

disambiguated_df['year'] = disambiguated_df['pubdate'].astype(str).str[:4].astype(int, errors='ignore')

software_counts = disambiguated_df['mapped_to_software'].value_counts()
top_20_software = software_counts.head(20)
print(top_20_software)

top_software_trends = disambiguated_df[
    disambiguated_df['mapped_to_software'].isin(top_20_software.index)
].groupby(['year', 'mapped_to_software']).size().unstack().fillna(0)

# show preview of top_software_trends
print(top_software_trends)


# area chart visualization
import plotly.express as px

# Resetting the index to have 'year' as a column instead of an index
top_software_trends = top_software_trends.reset_index()

# Melting the DataFrame to have a long-form DataFrame which Plotly prefers
melted_df = pd.melt(top_software_trends, id_vars='year', var_name='Software', value_name='Count')

# Creating the area chart
fig = px.area(
    melted_df,
    x='year',
    y='Count',
    color='Software',
    title='Trend of Software Mentions Over Time',
    labels={'Count': 'Number of Mentions'}
)

# remove the borders
for i in range(len(fig['data'])):
  fig['data'][i]['line']['width']=0

# Show the plot
fig.show()

