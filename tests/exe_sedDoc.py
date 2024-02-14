import sys
sys.path.append('../')
from src.sedDocExecutor import exec_sed_doc
from src.sedDocEditor import read_sedml
import pandas

# This is a template for executing a sedml file
path_='C:/Users/wai484/Documents/BG parameterisation/b61_Intracellular_pH_regulation/models/CellMLV2/'
sedFilename='Boron_NH4_BG_V3_pe.sedml' 
full_path=path_+sedFilename
doc=read_sedml(full_path)
working_dir=path_
base_out_path=path_

external_variables_info = {'q_HCO3_i':{'component': 'main', 'name':'q_HCO3_i' }}
# if the external variable value changes for each simulation step, then the value should be a list of values, with the same length as the number of time points +1
external_filename = './csv/Boron_HCO3.csv'
# df = pandas.read_csv(external_filename, skipinitialspace=True,encoding='utf-8')
# HCO3_i = df['HCO3_i'].to_numpy() 
# if the external variable value does not change, then the value should be a single value

exec_sed_doc(doc, working_dir,base_out_path, rel_out_path=None, external_variables_info={}, external_variables_values=[],ss_time={},cost_type='AE')
