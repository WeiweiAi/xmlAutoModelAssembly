import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.simulator import SimulationSettings,load_module,get_observables
from src.analyser import parse_model,analyse_model_full
from src.coder import writePythonCode
from src.optimiser import optimiseModel,ExperimentData,OptimisationSettings

model_path='./csv/test_model.cellml'
model,issues=parse_model(model_path, True)
base_dir='./csv'

if model:
    # specify the external variables which are the parameters to be optimised
    external_variable_name='P_3'
    external_variable_component='SLC_template3_ss'
    external_variables_info=[(external_variable_component,external_variable_name)]
    param_vars_dic={-1:external_variables_info,0:external_variables_info}
    # specify the observables
    observable_name='v'
    observable_component='SLC_template3_ss'
    observables_info=[(observable_component,observable_name)]
    # specify the experiment data
    sim_setting=SimulationSettings()
    experimentData=ExperimentData()
    experimentData.types=['mean']
    experimentData.observables_info=observables_info
    experimentData.exp_const_vec=[43.34209999]
    # specify the optimisation settings
    opt=OptimisationSettings()
    opt.param_init=10
    opt.param_mins=0
    opt.param_maxs=100
    # analyse the model
    analyser,flat_model, issues=analyse_model_full(model,base_dir,external_variables_info)
    #
    if analyser:
        full_path='./csv/test_model.py'
        writePythonCode(analyser, full_path)
        module=load_module(full_path)
        sim_setting.observables=get_observables(analyser,observables_info)
        res=optimiseModel(param_vars_dic, [analyser], [module], [sim_setting], [experimentData], opt)
        print(res)
    else:
        print(issues)
else:
    print(issues)
