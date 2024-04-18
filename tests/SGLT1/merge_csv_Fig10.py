import os
import pandas as pd
csv_files = []
model_name = 'SGLT1_BG_step'
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/CellMLV2/'
model_ids_=['_fig10_50mV','_fig10_150mV','_fig10_50mV_sugar','_fig10_150mV_sugar']
for model_id in model_ids_:
    sed_model_id = model_name+model_id
    csv_file=path_+'report_task_'+f'{sed_model_id}'+'.csv'
    new_csv_file = path_+'report_task_'+f'{sed_model_id}'+'_post.csv'
    if os.path.exists(new_csv_file):
        os.remove(new_csv_file)
    # remove the lines from line 2  to line 12001 and write to a new file
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        with open(new_csv_file, 'w') as f:
            f.writelines(lines[:1])
            f.writelines(lines[12001:])
    # read the new file to pd dataframe and add a new column 'tms', which is the time in ms; and save to a new file
    # tms = (t-1.2)*1000
    df = pd.read_csv(new_csv_file)
    df['tms'] = (df['t']-1.2)*1000
    df.to_csv(new_csv_file, index=False)
    
