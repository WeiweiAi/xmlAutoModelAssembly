import os
csv_files = []
model_name = 'GLUT1_BG'
path_='C:/Users/wai484/temp/b65/Facilitated transporter/CellMLV2/'
for model_id in range(25):
    sed_model_id = model_name+f'_{model_id}_io'
    csv_files.append(path_+'report_task_'+f'{sed_model_id}'+'.csv')
# only remove the first line of the second and subsequent files
# if the file exists, delete it first
io_csv = path_+f'{model_name}_ss_io.csv'
if os.path.exists(io_csv):
    os.remove(io_csv)
with open(io_csv, 'w') as file:
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            if csv_file == csv_files[0]:
                file.write(f.read())
            else:
                f.readline()
                file.write(f.read())

csv_files = []
for model_id in range(25):
    sed_model_id = model_name+f'_{model_id}_oi'
    csv_files.append(path_+'report_task_'+f'{sed_model_id}'+'.csv')
# only remove the first line of the second and subsequent files
oi_csv = path_+f'{model_name}_ss_oi.csv'
if os.path.exists(oi_csv):
    os.remove(oi_csv)
with open(oi_csv, 'w') as file:
    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            if csv_file == csv_files[0]:
                file.write(f.read())
            else:
                f.readline()
                file.write(f.read())