import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedEditor import read_sedml
from src.sedInterpreter import exec_sed_doc
"""
filename='./csv/test.sedml'
doc=read_sedml(filename)
working_dir='./csv'
model_base_dir='./csv'
base_out_path='./csv'
external_variable_name='P_3'
external_variable_component='SLC_template3_ss'
external_variables_info=[(external_variable_component,external_variable_name)]
exec_sed_doc(doc, working_dir,model_base_dir, base_out_path, rel_out_path=None, external_variables_info=[],external_variables_values=[], indent=0)
"""
filename='./csv/SLCT3_BG_test.sedml'
doc=read_sedml(filename)
working_dir='./csv'
model_base_dir='./csv'
base_out_path='./csv'

exec_sed_doc(doc, working_dir,model_base_dir, base_out_path, rel_out_path=None, external_variables_info=[],external_variables_values=[], indent=0)
