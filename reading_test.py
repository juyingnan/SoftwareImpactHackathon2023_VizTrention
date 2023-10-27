import pandas as pd
import json

# force print all
pd.set_option('display.max_seq_items', None)

# Data processing
ROOT_DATA_DIR = r'C:\Users\bunny\Desktop\doi_10.5061_dryad.6wwpzgn2c__v8'

using_sample = 7
file_name = '/disambiguated/comm_disambiguated.tsv'
if using_sample != 1:
    file_name = file_name[:-4] + f'_sample{using_sample}.tsv'
file_path = ROOT_DATA_DIR + file_name

disambiguated_df = pd.read_csv(
    file_path,
    sep='\t',
    engine='python'
)
# for 4 possible values of 'curated_label', see unique values of 'mapped_to_software' of each type
for label in disambiguated_df['curation_label'].unique():
    print(label)
    print(list(disambiguated_df[disambiguated_df['curation_label'] == label]['mapped_to_software'].unique()))
    print()