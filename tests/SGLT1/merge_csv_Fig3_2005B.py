import os
import pandas as pd
csv_files = []
csv_files_sugar = []

model_name = 'SGLT1_BG_ss_2005B'
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/CellMLV2/'
model_ids_=['_fig5_m150mV','_fig5_m120mV','_fig5_m80mV','_fig5_m50mV','_fig5_m30mV','_fig5_0mV','_fig5_30mV','_fig5_50mV',
            '_fig5_m150mV_sugar','_fig5_m120mV_sugar','_fig5_m80mV_sugar','_fig5_m50mV_sugar','_fig5_m30mV_sugar','_fig5_0mV_sugar',
            '_fig5_30mV_sugar','_fig5_50mV_sugar',]
new_csv_file=path_+'fig3_ss_2005B.csv'
new_csv_file_sugar=path_+'fig3_ss_2005B_sugar.csv'

if os.path.exists(new_csv_file):
        os.remove(new_csv_file)
if os.path.exists(new_csv_file_sugar):
        os.remove(new_csv_file_sugar)
for model_id in model_ids_:
    sed_model_id = model_name+model_id
    csv_file=path_+'report_task_'+f'{sed_model_id}'+'.csv'
    if 'sugar' not in model_id:
        csv_files.append(csv_file)
    else:
        csv_files_sugar.append(csv_file)

# keep the first line of the first file, and remove the first line of the second and subsequent files
# add line 12752 of all files to the new file
line_num = 197184
for csv_file in csv_files:
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        with open(new_csv_file, 'a') as file:
            if csv_file == csv_files[0]:
                file.writelines(lines[:1])
                file.writelines(lines[line_num:line_num+1])
            else:
                file.writelines(lines[line_num:line_num+1])
for csv_file in csv_files_sugar:
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        with open(new_csv_file_sugar, 'a') as file:
            if csv_file == csv_files_sugar[0]:
                file.writelines(lines[:1])
                file.writelines(lines[line_num:line_num+1])
            else:
                file.writelines(lines[line_num:line_num+1])                
      
# read the new file to pd dataframe;
# Ii in new_csv_file_sugar is A and in new_csv_file is B, the new value is A-B
# Save the new value to a new file;
# Save the V_E value to the new file as well
# Create a new pd dataframe with the new values
df_new = pd.DataFrame()
df = pd.read_csv(new_csv_file)
df_sugar = pd.read_csv(new_csv_file_sugar)
df_new['Ii'] = df_sugar['Ii']-df['Ii']
df_new['V_E'] = df['V_E']
df_new.to_csv(path_+'fig3_2005B.csv', index=False)
    
    
    
