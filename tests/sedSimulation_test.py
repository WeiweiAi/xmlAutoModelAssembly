import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import read_sedml,validate_sedml
from src.sedTasker import exec_task,report_task,exec_parameterEstimationTask

"""
filename='./csv/test.sedml'
doc=read_sedml(filename)
working_dir='./csv'
base_out_path='./csv'
external_variable_name='P_3'
external_variable_component='SLC_template3_ss'
external_variables_info=[(external_variable_component,external_variable_name)]
exec_sed_doc(doc, working_dir,model_base_dir, base_out_path, rel_out_path=None, external_variables_info=[],external_variables_values=[], indent=0)
"""
filename='./csv/test_pe.sedml'
doc=read_sedml(filename)
print(validate_sedml(filename))
working_dir='./csv'

base_out_path='./csv'
"""	
for i_task, task in enumerate(doc.getListOfTasks()):
    current_state, variable_results= exec_task(doc,task,working_dir,external_variables_info={},external_variables_values=[],current_state=None)
    report_task(doc,task, variable_results, base_out_path, rel_out_path=None, report_formats =['csv'])
"""
for i_task, task in enumerate(doc.getListOfTasks()):
    res= exec_parameterEstimationTask(doc,task, working_dir,external_variables_info={},external_variables_values=[])
    print(res)
    #report_task(doc,task, variable_results, base_out_path, rel_out_path=None, report_formats =['csv'])
