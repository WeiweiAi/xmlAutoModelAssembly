import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import create_dict_sedDocment, add_sedTask2dict, write_sedml, validate_sedml
from src.sedEditor import create_sedDocment

# This is a template for creating a sedml file
# Create a dictionary for the sedml file
dict_sedDocument=create_dict_sedDocment()

# ********** The following is to add the task information to the dictionary **********

# This is the model id in the sedml file, which is also the task id and output id
model_name='SLCT3_BG_test'
# This is the model file name, assuming in the same folder with the sedml file
model_source='SLCT3_BG_test.cellml' 
# This is the sedml file (relative) path and name
sedFilename='./csv/SLCT3_BG_test.sedml' 
# This is to modify the model parameters if needed
changes={'id':{'component':'SLCT3_BG_io','name':'q_Ai','newValue':'200'}
         } 
# This is the output of the simulation
outputs={'v_Ai':{'component':'SLCT3_BG_test','name':'v_Ai','scale':1.0}, 
         'v_Ao':{'component':'SLCT3_BG_test','name':'v_Ao'},
         't':{'component':'SLCT3_BG','name':'t'}
         }

# The following is the simulation setting
# This is the algorithm parameter if needed
dict_algorithmParameter={'kisaoID':'KISAO:0000467', 'name':'max_step','value':'1'} 
# This is the ODE solver
dict_algorithm={'kisaoID':'KISAO:0000535','name':'VODE','listOfAlgorithmParameters':[dict_algorithmParameter]} 
# This is the simulation setting
simSetting={'type':'UniformTimeCourse','algorithm':dict_algorithm,'initialTime':0,'outputStartTime':2.3,'outputEndTime':1000,'numberOfSteps':1000}
# simSetting={'type':'OneStep','algorithm':dict_algorithm,'step':0.1}
# simSetting={'type':'SteadyState','algorithm':dict_algorithm}

# The following is to add the task information to the dictionary
add_sedTask2dict(dict_sedDocument, model_name, model_source,changes,simSetting,outputs)

# You can repeat the above steps to add more tasks with DIFFERENT model names.

# ********** The following is to create the sedml file, no need to modify **********

try:
    doc=create_sedDocment(dict_sedDocument)
except ValueError as err:
    print(err)
write_sedml(doc,sedFilename)
print(validate_sedml(sedFilename))
   
