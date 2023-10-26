import pandas as pd
import json

# Data processing
ROOT_DATA_DIR = r'C:\Users\bunny\Desktop\doi_10.5061_dryad.6wwpzgn2c__v8'

using_sample = 3
file_name = '/disambiguated/comm_disambiguated.tsv'
if using_sample != 1:
    file_name = file_name[:-4] + f'_sample{using_sample}.tsv'
file_path = ROOT_DATA_DIR + file_name

disambiguated_df = pd.read_csv(
    file_path,
    sep='\t',
    engine='python'
)

disambiguated_df = disambiguated_df[(disambiguated_df['mapped_to_software'] != 'not_disambiguated') & (disambiguated_df['curation_label'] != 'not_software')]
disambiguated_df['year'] = disambiguated_df['pubdate'].astype(str).str[:4].astype(int, errors='ignore')
disambiguated_df['year'] = disambiguated_df['year'].dropna().astype(int)

min_year = disambiguated_df['year'].min()
max_year = disambiguated_df['year'].max()

sankey_data = {}

for year in range(min_year, max_year + 1):
    print(year)
    year_df = disambiguated_df[disambiguated_df['year'] == year]
    connections = {}
    
    for uid, group in year_df.groupby('doi'):
        softwares = group['mapped_to_software'].unique()
        for i in range(len(softwares)):
            for j in range(i+1, len(softwares)):
                software_pair = tuple(sorted((softwares[i], softwares[j])))
                if software_pair not in connections:
                    connections[software_pair] = 1
                else:
                    connections[software_pair] += 1
    
    connections_df = pd.DataFrame(list(connections.items()), columns=['Connection', 'Count'])
    
    if not connections_df.empty:
        connections_df['Source'], connections_df['Target'] = zip(*connections_df['Connection'])
        connections_df = connections_df.drop('Connection', axis=1)
        sankey_data[year] = connections_df.to_dict(orient='records')
    else:
        sankey_data[year] = []

# Save the data to a JSON file
with open('sankey_data.json', 'w') as f:
    json.dump(sankey_data, f)
