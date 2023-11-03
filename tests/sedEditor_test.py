import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedEditor import create_sedDocment,write_sedml,validate_sedml,get_dict_sedDocument,target_component_variable,target_component_variable_initial
"""
model_source='SLCT3_BG_test.cellml'
# modify the initial value
component_modified='SLCT3_BG_io'
variable_modified='q_Ai' 
new_initial_value='200'
# output
component_output='SLCT3_BG_test'
variable_output='v_Ai'

component_voi='SLCT3_BG'
variable_voi='t'

dict_sedDocument={}
dict_change_Attribute={'target': target_component_variable_initial(component_modified, variable_modified),'newValue':new_initial_value}
dict_model={'id':'model1','source':model_source,'language':'urn:sedml:language:cellml','listOfChanges':[dict_change_Attribute]}
dict_sedDocument['listOfModels']=[dict_model]

dict_algorithmParameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
dict_algorithm={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
dict_simulation={'id':'timeCourse1', 'type':'UniformTimeCourse', 'algorithm':dict_algorithm, 
                 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':100}
dict_sedDocument['listOfSimulations']= [dict_simulation]

dict_task={'id':'task1','type':'Task', 'modelReference':'model1','simulationReference':'timeCourse1'}
dict_sedDocument['listOfTasks']= [dict_task]

dict_variable={'id':'v','target':target_component_variable(component_output, variable_output),'modelReference':'model1','taskReference':'task1'}
dict_parameter={'id':'scale','value':1.0}
dict_dataGenerator={'id':'output','name':'dataGenerator1','math':'v*scale','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}

dict_variable_voi={'id':'voi','target':target_component_variable(component_voi, variable_voi),'modelReference':'model1','taskReference':'task1'}
dict_dataGenerator_voi={'id':'output_voi','name':'dataGenerator1','math':'voi','listOfVariables':[dict_variable_voi],'listOfParameters':[]}

dict_sedDocument['listOfDataGenerators']= [dict_dataGenerator_voi,dict_dataGenerator]

dict_dataSet={'id':'dataSet1','label':'v_Ai','dataReference':'output'}
dict_dataSet_voi={'id':'dataSet2','label':'time','dataReference':'output_voi'}

dict_report={'id':'report1','name':'report1','listOfDataSets':[dict_dataSet_voi,dict_dataSet]}
dict_sedDocument['listOfReports']= [dict_report]

doc=create_sedDocment(dict_sedDocument)
filename='./csv/SLCT3_BG_test.sedml'
write_sedml(doc,filename)
print(validate_sedml(filename))
print(get_dict_sedDocument(doc))

"""
dict_sedDocument={}
model_source_opt='SLCT3_BG_test.cellml'
opt_model_id='model1'

data_source='data.csv'

component_opt='SLCT3_BG_param'
variable_opt='kappa_re1'
dg_opt='dg_opt'
lowerBound_opt=0.0
upperBound_opt=10.0
initialValue_opt=0.1

component_init='SLCT3_BG_io'
variable_init='q_Ai'
dg_init='dg_init'
datasource_init='data_source_initial'
csv_column_init='q_Ai'

component_observed='SLCT3_BG_test'
variable_observed='v_Ai'
dg_observed='dg_observed'
datasource_observed='data_source_observed'
csv_column_observed='v_Ai'

datasource_pointWeight='data_source_pointWeight'
csv_column_pointWeight='pointWeight'

component_voi='SLCT3_BG'
variable_voi='t'
dg_voi='dg_voi'
datasource_time='data_source_time'
csv_column_time='time'


dict_variable_voi={'id':'voi','target':target_component_variable(component_voi, variable_voi),'modelReference':opt_model_id,'taskReference':'parameterEstimationTask1'}
dict_dataGenerator_voi={'id':dg_voi,'name':'dataGenerator1','math':None,'listOfVariables':[dict_variable_voi],'listOfParameters':[]}

dict_variable_init={'id':'variable_init','target':target_component_variable_initial(component_init, variable_init),'modelReference':opt_model_id,'taskReference':'parameterEstimationTask1'}
dict_dataGenerator_init={'id':dg_init,'name':'dataGenerator1','math':None,'listOfVariables':[dict_variable_init],'listOfParameters':[]}

dict_variable_observed={'id':'variable_observed','target':target_component_variable(component_observed, variable_observed),'modelReference':opt_model_id,'taskReference':'parameterEstimationTask1'}
dict_dataGenerator_observed={'id':dg_observed,'name':'dataGenerator1','math':None,'listOfVariables':[dict_variable_observed],'listOfParameters':[]}

# Describe the experimental data
dict_slice_time={'reference':'ColumnIds','value':csv_column_time,'index':None,'startIndex':None,'endIndex':None}
dict_dataSource_time={'id':datasource_time,'name':datasource_time,'listOfSlices':[dict_slice_time]}

dict_slice_initial_index={'reference':'Index','value':'0','index':None,'startIndex':None,'endIndex':None}
dict_slice_initial_column={'reference':'ColumnIds','value':csv_column_init,'index':None,'startIndex':None,'endIndex':None}
dict_dataSource_initial={'id':datasource_init,'name':datasource_init,'listOfSlices':[dict_slice_initial_index,dict_slice_initial_column]}

dict_slice_observe={'reference':'ColumnIds','value':csv_column_observed,'index':None,'startIndex':None,'endIndex':None}
dict_dataSource_observe={'id':datasource_observed,'name':datasource_observed,'listOfSlices':[dict_slice_observe]}

dict_slice_pointWeight={'reference':'ColumnIds','value':csv_column_pointWeight,'index':None,'startIndex':None,'endIndex':None}
dict_dataSource_pointWeight={'id':datasource_pointWeight,'name':datasource_pointWeight,'listOfSlices':[dict_slice_pointWeight]}

dict_dimDescription={'id':'Index','name':'index','indexType':'integer','dim2':{'id':'ColumnIds','name':'ColumnIds','indexType':'string','valueType':'double','atomicName':'Values'}}
dict_dataDescription={'id':'data_description_1','name':'external data', 'source':data_source,'format':'csv','dimensionDescription':dict_dimDescription,
                      'listOfDataSources':[dict_dataSource_time,dict_dataSource_initial,dict_dataSource_observe,dict_dataSource_pointWeight]}

dict_sedDocument['listOfDataDescriptions']= [dict_dataDescription]

dict_model={'id':opt_model_id,'source':model_source_opt,'language':'urn:sedml:language:cellml','listOfChanges':[]}
dict_sedDocument['listOfModels']=[dict_model]
dict_algorithmParameter_opt={'kisaoID':'KISAO:0000211','name':'xatol','value':'1e-8'}
dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}

dict_fitMapping_time= {'type':'time','dataSource':datasource_time,'target':dg_voi}
dict_fitMapping_observable= {'type':'observable','dataSource':datasource_observed,'target':dg_observed,'pointWeight':datasource_pointWeight}
dict_fitMapping_init= {'type':'experimentalCondition','dataSource':datasource_init,'target':dg_init}


dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[dict_algorithm_sim_parameter]}
dict_fitExperiment={'id':'fitExperimen1','type':'timeCourse','algorithm':dict_algorithm_sim,'listOfFitMappings':[dict_fitMapping_time,dict_fitMapping_observable,dict_fitMapping_init]}

dict_experimentReference={'id':'experiment1','experiment':'fitExperimen1'}

dict_bounds={'lowerBound':lowerBound_opt,'upperBound':upperBound_opt,'scale':'linear'}
dict_adjustableParameter = {'id':'parameter1','modelReference':opt_model_id,'target':target_component_variable(component_opt, variable_opt),
                                                 'initialValue':initialValue_opt,'bounds':dict_bounds,'listOfExperimentReferences':[dict_experimentReference]}

dict_parameterEstimationTask= {'id':'parameterEstimationTask1','type':'ParameterEstimationTask','modelReference':opt_model_id,'algorithm':dict_algorithm_opt,'objective':{'type':'leastSquare'},
                       'listOfAdjustableParameters':[dict_adjustableParameter],'listOfFitExperiments':[dict_fitExperiment]}                                                 

dict_sedDocument['listOfTasks']= [dict_parameterEstimationTask]



dict_variable={'id':'v','target':target_component_variable(component_observed, variable_observed),'modelReference':'model1','taskReference':'parameterEstimationTask1'}
dict_parameter={'id':'scale','value':10.0}
dict_dataGenerator={'id':'output','name':'dataGenerator1','math':'v*scale','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}

dict_sedDocument['listOfDataGenerators']= [dict_dataGenerator_voi,dict_dataGenerator,dict_dataGenerator_init,dict_dataGenerator_observed]

dict_dataSet={'id':'dataSet1','label':'output','dataReference':'output'}
dict_report={'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
dict_sedDocument['listOfReports']= [dict_report]

doc=create_sedDocment(dict_sedDocument)
filename='./csv/test_pe.sedml'
write_sedml(doc,filename)
print(validate_sedml(filename))
print(get_dict_sedDocument(doc))
