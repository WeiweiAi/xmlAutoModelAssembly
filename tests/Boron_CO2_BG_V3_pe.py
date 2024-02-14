import sys
import os
sys.path.append('../')
from src.sedDocEditor import create_dict_sedDocment, add_peTask2dict, write_sedml, validate_sedml, read_sedml
from src.sedEditor import create_sedDocment
from src.coder import toCellML2
from src.sedDocExecutor import exec_sed_doc

# Convert the model to CellML 2.0 if needed
path_='./models/'
model_name='Boron_CO2_BG_V3'
modelfile= model_name + '.cellml'
oldPath=path_+ modelfile
# create a new directory for the new model if it does not exist
if not os.path.exists(path_+'CellMLV2'):
    os.makedirs(path_+'CellMLV2')

newPath=path_+'CellMLV2/'+ modelfile
# convert the model to CellML 2.0
try:
    toCellML2(oldPath, newPath, external_variables_info={},strict_mode=True, py_full_path=None)
except Exception as err:
    exit()
# ********** TThe above can be commented out if the model is already in CellML 2.0 **********

# ********** The following is to create a dictionary for the sedml file **********
dict_sedDocument=create_dict_sedDocment()
# This is the sedml file (relative) path and name, assuming in the same folder with the CellML model file
path_='./models/CellMLV2/'
model_name='Boron_CO2_BG_V3'
model_id = model_name # This is the model id in the sedml, could be different from the model file name
sedFilename = model_name+'_pe.sedml' 
full_path = path_+ sedFilename 
ss_time={} # The time for the steady state, if not provided, the default value will be used
cost_type='AE' 
# The cost function type, could be 'AE' (absolute error),
# 'MIN-MAX' (normalized by (max(exp_value)-min(exp_value))), 
# 'Z-SCORE' (normalized by std(exp_value), 
# or 'MSE' (mean squared error). 

# ********** The following is to add the task information to the dictionary **********

# Note: the following is an example, you can modify it to add more tasks
# Note: the valid sedml id should start with a letter, and only contain letters, numbers, and underscores

# This is the model id in the sedml file, which is also the task id and output id
model_names=[model_id]
# This is the model file name, assuming in the same folder with the sedml file
model_sources=[model_name+'.cellml']
# This is to set optimization algorithm
# This is to set the tolerance for least square when using local optimization algorithm, default is 1e-8
dict_algorithmParameter_opt={'kisaoID':'KISAO:0000597','name':'tol','value':'1e-9'} 
# This is to set the maximum number of iterations when using local optimization algorithm, default is 1000
dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'} 

# ****************** You can choose one of the following optimization algorithms ******************
# This is to set optimization algorithm as local optimization algorithm, and the scipy.least_square is implemented in the code
dict_algorithm_opt={'kisaoID':'KISAO:0000471','name':'local optimization algorithm', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}

# This is to set optimization algorithm as global optimization algorithm, and scipy.shgo is used to implement the algorithm
# dict_algorithm_opt={'kisaoID':'KISAO:0000472','name':'global optimization algorithm', 'listOfAlgorithmParameters':[]}

# This is to set optimization algorithm as genetic algorithm, and scipy.differential_evolution is used to implement the algorithm
# dict_algorithm_opt={'kisaoID':'KISAO:0000520','name':'evolutionary algorithm', 'listOfAlgorithmParameters':[]}

# This is to set optimization algorithm as simulated annealing, and scipy.dual_annealing is used to implement the algorithm
# dict_algorithm_opt={'kisaoID':'KISAO:0000503','name':'simulated annealing', 'listOfAlgorithmParameters':[]}

# This is to set optimization algorithm as random search, and scipy.basinhopping is used to implement the algorithm
# Note: basinhopping does not support bounds, and the bounds will be ignored
# dict_algorithm_opt={'kisaoID':'KISAO:0000504','name':'random search', 'listOfAlgorithmParameters':[]}

# ***************** This is to set simulation algorithm *****************
# This is to set the maximum step size for the simulation
dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.1'} 
# You can set more algorithm parameters if needed. You can refer to get_KISAO_parameters() in src/simulator.py file to get the parameters for the specific algorithm
# Add the algorithm parameters to listOfAlgorithmParameters
# You can choose one of the simulation algorithms specified by KISAO_ALGORITHMS in src/simulator.py file
dict_algorithm_sim={'kisaoID':'KISAO:0000030','name':'Euler forward method', 'listOfAlgorithmParameters':[dict_algorithm_sim_parameter]}
# dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[dict_algorithm_sim_parameter]}


# ******************** This is to modify the model parameters if needed ********************
changes={} # by default, no changes to the model parameters
# the format is {'id':{'component':str,'name':str,'newValue':str}}
# Example: changes={'v_CO2_max':{'component':'main','name':'v_CO2_max','newValue':'10'}

# ******************** This is to specify the data source files for the fitting experiments ********************
# The data source file should be in the same folder with the sedml file, otherwise, the full path should be provided

# Specify the data source file for the expected observables, which is used for fitting. This is a must.
data_observables_file='report_task_Boron_CO2.csv'
fileId_observables='expected_observables'

experimentData_files={fileId_observables:{'data_summary':'expected_observables','data_file':data_observables_file}}
# time
# format: [dataSourceId,column_name,startIndex,endIndex,component,name]
# column_name: the column name in the data source file corresponding to the time points
# startIndex: the start index of the time points, default is None
# endIndex: the end index of the time points, default is None
# component: the component name in the model where the variable of integration is located
# name: the name of the variable of integration in the model
dataSourceId_0='time'
time={dataSourceId_0:{'column_name':'t','startIndex':None,'endIndex':None,'component':'main','name':'t'}} 
# if the fitting experiment is steady state, the time is not needed. time={}
# if the fitting experiment is steady state, time_map=()
if time !={}:
    time_map=(fileId_observables,dataSourceId_0) # to map the data source file and the data source
    experimentData_files[fileId_observables]['time']=time
else:
    time_map=()
# observables
# format: [dataSourceId,column_name,startIndex,endIndex,component,name,weight]
# column_name: the column name in the data source file corresponding to the measured observable data
# startIndex: the start index of the observable, default is None
# endIndex: the end index of the observable, default is None
# component: the component name in the model where the observable variable is located
# name: the name of the observable variable in the model
# weight: the weight for the observable, default is 1
dataSourceId_1='v_CO2_m'
obs1=[dataSourceId_1,'J_CO2',None,None,'main','v_CO2_m',1]
# You can add more observables if needed
# Add the observables to the list
observables=[obs1]

#observables_map=[(fileId,dataSourceId,'function for observable output, default is the var with '', abs(var), or-(var),')] to map the data source file and the data source
observables_map =[(fileId_observables,dataSourceId_1,'')] 

# Specify the data source file for the experiment conditions if external input is needed. Otherwise, you don't need to specify it.
# data_source_file1='report_task_Boron_CO2.csv'
# fileId1='conditions'
# data_summary_1='conditions'
# experimentalConditions
# format: [dataSourceId,column_name,startIndex,endIndex,index_value,component,name]
# column_name: the column name in the data source file corresponding to the experimental condition
# startIndex: the start index of the experimental condition, default is None
# endIndex: the end index of the experimental condition, default is None
# index_value: the value of the experimental condition, default is None
# component: the component name in the model where the experimental condition variable is located
# name: the name of the experimental condition variable in the model
# You can add more experimental conditions if needed
# e.g.,
# dataSourceId_2='q_CO2_i'
# exp1=[dataSourceId_2,'J_CO2_i',None,None,None,'main','q_CO2_i']

# Add the experimental conditions to the list. If no experimental condition is needed, keep the list empty
exps=[]
# experimentalConditions=[(fileId,dataSourceId)], to map the data source file and the data source, can be empty if no experimental condition is needed
experimentalConditions_map = []
dict_file_conditions={}

# ******************** This is to specify the fitting experiments ********************
# fitExperiments
# format: [fitId, type, model_variance, algorithm, experimentalConditions_map, observables_map,time_map]

# time=(fileId,dataSourceId) to map the data source file and the data source
fitId_1='fit1' # fitId: the id for the fit experiment
fitting_type='timeCourse' #  the type of the fit experiment, which could be 'steadyState', or 'timeCourse'
# model_variance: the model variance, default is ''
# dict_algorithm_sim: the simulation algorithm information for the fit experiment
fit1=[fitId_1,fitting_type, '',  dict_algorithm_sim, experimentalConditions_map, observables_map,time_map ]

# Add the fit experiments to the list
fits=[fit1]

# ******************** This is to specify the adjustable parameters for the fitting experiments ********************
# adjustableParameters
# format: [parameterId, component, name, lowerBound, upperBound, initialValue, scale, experimentReferences]
#experimentReferences: list of fitId

parameterId_1='v_CO2_max'
adjustable1=[parameterId_1,'main','v_CO2_max',1e-12,1e12,1,'linear',[fitId_1]]
parameterId_2='gamma_CO2'
adjustable2=[parameterId_2,'main','gamma_CO2',1e-12,1e12,1,'linear',[fitId_1]]
adjustables=[adjustable1,adjustable2]

# ********** No need to modify the following **********

dict_obs={}
for obs in observables:
    dataSourceId=obs[0]
    column_name=obs[1]
    startIndex=obs[2]
    endIndex=obs[3]
    component=obs[4]
    name=obs[5]
    weight=obs[6]
    dict_obs[dataSourceId]={'column_name':column_name,'startIndex':startIndex,'endIndex':endIndex,'component':component,'name':name, 'weight':weight}
experimentData_files[fileId_observables]['observables']=dict_obs
dict_exp={}
for exp in exps:
    dataSourceId=exp[0]
    column_name=exp[1]
    startIndex=exp[2]
    endIndex=exp[3]
    index_value=exp[4]
    component=exp[5]
    name=exp[6]
    dict_exp[dataSourceId]={'column_name':column_name,'startIndex':startIndex,'endIndex':endIndex,'index_value':index_value,'component':component,'name':name}

fitExperiments={}
for fit in fits:
    fitId=fit[0]
    type=fit[1]
    model_variance=fit[2]
    algorithm=fit[3]
    experimentalConditions=fit[4]
    observables=fit[5]
    if len(fit)==7 and type=='timeCourse':
        time=fit[6]
        fitExperiments[fitId]={'type':type,'algorithm':algorithm,'experimentalConditions':experimentalConditions,'observables':observables,'time':time}
    else:
        fitExperiments[fitId]={'type':type,'algorithm':algorithm,'experimentalConditions':experimentalConditions,'observables':observables}
    if model_variance!='':
        fitExperiments[fitId]['name']=model_variance

adjustableParameters={}
for adjustable in adjustables:
    parameterId=adjustable[0]
    component=adjustable[1]
    name=adjustable[2]
    lowerBound=adjustable[3]
    upperBound=adjustable[4]
    initialValue=adjustable[5]
    scale=adjustable[6]
    experimentReferences=adjustable[7]
    adjustableParameters[parameterId]={'component':component,'name':name,'lowerBound':lowerBound,'upperBound':upperBound,'initialValue':initialValue,'scale':scale,'experimentReferences':experimentReferences}

try:            
    add_peTask2dict(dict_sedDocument, model_names, model_sources,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )
except ValueError as err:
    print(err)
    exit()

# You can repeat the above steps to add more tasks with DIFFERENT model names.

# ********** The following is to create the sedml file, no need to modify **********

try:
    doc=create_sedDocment(dict_sedDocument)
except ValueError as err:
    print(err)
    exit()
write_sedml(doc,full_path)
print(validate_sedml(full_path))

doc=read_sedml(full_path) # Must read the sedml file again to avoid the error in the next step
exec_sed_doc(doc, path_,path_, rel_out_path=None, external_variables_info={},
              external_variables_values=[],ss_time=ss_time,cost_type=cost_type)
# Run the sedml file
