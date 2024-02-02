import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import create_dict_sedDocment, add_peTask2dict, write_sedml, validate_sedml
from src.sedEditor import create_sedDocment

# This is a template for creating a sedml file for parameter estimation task
# Create a dictionary for the sedml file
dict_sedDocument=create_dict_sedDocment()
# This is the sedml file (relative) path and name
sedFilename='./csv/Boron_HCO3_BG_pe.sedml' 

# ********** The following is to add the task information to the dictionary **********

# Note: the following is an example, you can modify it to add more tasks
# Note: the valid sedml id should start with a letter, and only contain letters, numbers, and underscores

# This is the model id in the sedml file, which is also the task id and output id
model_names=['Boron_HCO3_BG']
# This is the model file name, assuming in the same folder with the sedml file
model_sources=['Boron_HCO3_BG.cellml']
# This is to set optimization algorithm
dict_algorithmParameter_opt={'kisaoID':'KISAO:0000597','name':'tol','value':'1e-6'}
dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}
dict_algorithm_opt={'kisaoID':'KISAO:0000472','name':'global optimization algorithm', 'listOfAlgorithmParameters':[]}
#dict_algorithm_opt={'kisaoID':'KISAO:0000471','name':'local optimization algorithm', 'listOfAlgorithmParameters':[]}
#dict_algorithm_opt={'kisaoID':'KISAO:0000471','name':'local optimization algorithm', 'listOfAlgorithmParameters':[]}

# This is to set simulation algorithm
dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
dict_algorithm_sim={'kisaoID':'KISAO:0000030','name':'Euler forward method', 'listOfAlgorithmParameters':[]}
dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[]}

# This is to modify the model parameters if needed
changes={}

# Specify the data source file for the experiment (conditions and expected observables)
data_source_file1='Boron_HCO3.csv'
fileId1='conditions'
data_summary_1='conditions'

data_source_file2='report_task_Boron_HCO3.csv'
fileId2='expected_observables'
data_summary_2='expected_observables'

# time
# format: [dataSourceId,column_name,startIndex,endIndex,component,name]
dataSourceId_0='time'
time={dataSourceId_0:{'column_name':'t','startIndex':None,'endIndex':None,'component':'main','name':'t'}} 

# observables
# format: [dataSourceId,column_name,startIndex,endIndex,component,name,weight]
dataSourceId_1='v_HCO3_m'
obs1=[dataSourceId_1,'J_HCO3',None,None,'main','v_HCO3_m',1]
observables=[obs1]

# experimentalConditions
# format: [dataSourceId,column_name,startIndex,endIndex,index_value,component,name]
#dataSourceId_2='q_HCO3_i'
#exp1=[dataSourceId_2,'q_Ao_init',None,None,None,'main','q_HCO3_i']

exps=[]
# fitExperiments
# format: [fitId, type, model_variance, algorithm, experimentalConditions, observables,time]
# experimentalConditions=[(fileId,dataSourceId)] to map the data source file and the data source
# observables=[(fileId,dataSourceId,'function for observable output, default is the var with '', abs(var), or-(var),')] to map the data source file and the data source
# time=(fileId,dataSourceId) to map the data source file and the data source
fitId_1='fit1'
fit1=[fitId_1,'timeCourse', '',  dict_algorithm_sim,
      [],
      [(fileId2,dataSourceId_1,'')],
      (fileId1,dataSourceId_0)
    ]

fits=[fit1]

# adjustableParameters
# format: [parameterId, component, name, lowerBound, upperBound, initialValue, scale, experimentReferences]
#experimentReferences: list of fitId

parameterId_1='K_HCO3_s'
adjustable1=[parameterId_1,'main','K_HCO3_s',0.0001,100,0.1,'linear',[fitId_1]]
parameterId_2='kappa_HCO3_m'
adjustable2=[parameterId_2,'main','kappa_HCO3_m',1e-9,1e6,1e-8,'linear',[fitId_1]]

adjustables=[adjustable2]

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
   
# May need to modify the following to map the data source file and the data source
experimentData_files={
        fileId1:{
            'data_summary':data_summary_1,
            'data_file':data_source_file1,
            'time':time,                                                                                         
        },
        fileId2:{
            'data_summary':data_summary_2,
            'data_file':data_source_file2,
            'observables':dict_obs,                                                                                                    
        }    
    }  
# No need to modify the following
fitExperiments={}
for fit in fits:
    fitId=fit[0]
    type=fit[1]
    model_variance=fit[2]
    algorithm=fit[3]
    experimentalConditions=fit[4]
    observables=fit[5]
    if len(fit)==7:
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
            
add_peTask2dict(dict_sedDocument, model_names, model_sources,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )

# You can repeat the above steps to add more tasks with DIFFERENT model names.

# ********** The following is to create the sedml file, no need to modify **********

try:
    doc=create_sedDocment(dict_sedDocument)
except ValueError as err:
    print(err)
write_sedml(doc,sedFilename)
print(validate_sedml(sedFilename))
   
