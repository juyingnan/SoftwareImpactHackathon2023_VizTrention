import pandas as pd
import os

def estimate_row_count(file_path, sample_size=5000):
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rt', encoding='utf-8', errors='ignore') as file:
        sample_data = file.read(sample_size)
    average_row_size = sample_size / sample_data.count('\n')
    estimated_rows = file_size / average_row_size
    return int(estimated_rows)

ROOT_DATA_DIR = r'C:\Users\bunny\Desktop\doi_10.5061_dryad.6wwpzgn2c__v8'

filename = ROOT_DATA_DIR + '/disambiguated/comm_disambiguated.tsv'
num_rows = 7000000
chunksize = 500000

chunks = pd.read_csv(filename, sep='\t', chunksize=chunksize)

estimated_rows = estimate_row_count(filename)
print(f'Estimated number of rows: {estimated_rows}')

sample_rate = estimated_rows // num_rows
print(f'Sample rate: {sample_rate}')
sample_filename = filename[:-4] + f'_sample{sample_rate}.tsv'

sample_frames = []

for i, chunk in enumerate(chunks):
    sample_frac = num_rows / (estimated_rows - i * chunksize)
    sample = chunk.sample(frac=sample_frac, random_state=1)
    sample_frames.append(sample)
    num_rows -= len(sample)
    print(f'Number of rows remaining: {num_rows}')
    if num_rows <= 0:
        break

sample_df = pd.concat(sample_frames, ignore_index=True)
sample_df.to_csv(sample_filename, sep='\t', index=False)
