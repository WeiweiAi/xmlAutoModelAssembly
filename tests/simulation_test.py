import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.simulator import sim_UniformTimeCourse,SimulationSettings,External_module,load_module,get_observables,get_mtype
from src.analyser import parse_model,analyse_model_full
from src.coder import writePythonCode

model_path='./csv/test_model_noExt.cellml'
external_variable_name='P_3'
external_variable_component='SLC_template3_ss'
external_variables_info=[(external_variable_component,external_variable_name)]
observable_name='v'
observable_component='SLC_template3_ss'
observables_info={'v':(observable_component,observable_name)}
sim_setting=SimulationSettings()

model,issues=parse_model(model_path, True)
base_dir='./csv'
if model:    
    analyser, issues=analyse_model_full(model,base_dir,external_variables_info)
    if analyser:
        mtype=get_mtype(analyser)
        full_path='./csv/test_model.py'
        writePythonCode(analyser, full_path)
        module=load_module(full_path)
        external_module=External_module(analyser, model, external_variables_info,[100])
        observables=get_observables(analyser,observables_info)
        sed_results=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module)[-1]        
        if sed_results:
            print(sed_results)
        else:
            print('simulation failed!')
