import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocExecutor import exec_sed_doc
from src.sedDocEditor import read_sedml
import pandas

# This is a template for executing a sedml file

sed_filename='./csv/Boron_HCO3.sedml'
doc=read_sedml(sed_filename)
working_dir='./csv'
base_out_path='./csv'

external_variables_info = {'HCO3_i':{'component': 'main', 'name':'HCO3_i' }}
# if the external variable value changes for each simulation step, then the value should be a list of values, with the same length as the number of time points +1
external_filename = './csv/Boron_HCO3.csv'
df = pandas.read_csv(external_filename, skipinitialspace=True,encoding='utf-8')
HCO3_i = df['HCO3_i'].to_numpy() 
# if the external variable value does not change, then the value should be a single value

exec_sed_doc(doc, working_dir,base_out_path, rel_out_path=None, external_variables_info=external_variables_info, external_variables_values=[HCO3_i],ss_time={})
