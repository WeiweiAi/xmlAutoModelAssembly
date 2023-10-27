import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedEditor import create_sedDocment,write_sedml,validate_sedml,get_dict_sedDocument,target_component_variable,target_component_variable_initial

model_source='SLCT3_BG_test.cellml'
# modify the initial value
component_modified='SLCT3_BG_io'
variable_modified='q_Ai' 
new_initial_value='200'
# output
component_output='SLCT3_BG_test'
variable_output='v_Ai'

dict_sedDocument={}
dict_change_Attribute={'target': target_component_variable_initial(component_modified, variable_modified),'newValue':new_initial_value}
dict_model={'id':'model1','source':model_source,'language':'urn:sedml:language:cellml','listOfChanges':[dict_change_Attribute]}
dict_sedDocument['listOfModels']=[dict_model]

dict_algorithmParameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
dict_algorithm={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
dict_simulation={'id':'timeCourse1', 'type':'UniformTimeCourse', 'algorithm':dict_algorithm, 
                 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
dict_sedDocument['listOfSimulations']= [dict_simulation]

dict_task={'id':'task1','type':'Task', 'modelReference':'model1','simulationReference':'timeCourse1'}
dict_sedDocument['listOfTasks']= [dict_task]

dict_variable={'id':'v','target':target_component_variable(component_output, variable_output),'modelReference':'model1','taskReference':'task1'}
dict_parameter={'id':'scale','value':10.0}
dict_dataGenerator={'id':'output','name':'dataGenerator1','math':'v*scale','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
dict_sedDocument['listOfDataGenerators']= [dict_dataGenerator]

dict_dataSet={'id':'dataSet1','label':'output','dataReference':'output'}
dict_report={'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
dict_sedDocument['listOfReports']= [dict_report]

doc=create_sedDocment(dict_sedDocument)
filename='./csv/test.sedml'
write_sedml(doc,filename)
print(validate_sedml(filename))
print(get_dict_sedDocument(doc))