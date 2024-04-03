import sys
import os
sys.path.append('../../')
from src.sedDocEditor import create_dict_sedDocment, add_sedTask2dict, write_sedml, validate_sedml,read_sedml
from src.sedEditor import create_sedDocment
from src.coder import toCellML2
from src.sedDocExecutor import exec_sed_doc

# Convert the model to CellML 2.0 if needed
path_='C:/Users/wai484/temp/b65/Facilitated transporter/'
model_name='GLUT1_ss_io_no_constraint'
modelfile= model_name + '.cellml'
oldPath=path_+ modelfile
# create a new directory for the new model if it does not exist
if not os.path.exists(path_+'CellMLV2'):
    os.makedirs(path_+'CellMLV2')

path_='C:/Users/wai484/temp/b65/Facilitated transporter/CellMLV2/'
newPath=path_+ modelfile
# convert the model to CellML 2.0
try:
    toCellML2(oldPath, newPath, external_variables_info={},strict_mode=True, py_full_path=None)
except Exception as err:
    exit()
# ********** TThe above can be commented out if the model is already in CellML 2.0 **********

# ********** The following is to create a dictionary for the sedml file **********
dict_sedDocument=create_dict_sedDocment()
# This is the sedml file (relative) path and name, assuming in the same folder with the CellML model file
path_='C:/Users/wai484/temp/b65/Facilitated transporter/CellMLV2/'
# model_name='Boron_acid_EA'
model_id = model_name # This is the model id in the sedml, could be different from the model file name
sedFilename = model_name+'.sedml' 
full_path = path_+ sedFilename 

# ********** The following is to add the task information to the dictionary **********

# Note: the following is an example, you can modify it to add more tasks
# Note: the valid sedml id should start with a letter, and only contain letters, numbers, and underscores
# This is the model file name, assuming in the same folder with the sedml file
model_source = model_name + '.cellml' 
# This is to modify the model parameters if needed
changes={
         } 
# the format is {'id':{'component':str,'name':str,'newValue':str}}
# Example: changes={'V_m':{'component':'main','name':'V_m','newValue':'-0.055'}

# This is the output of the simulation, and the key is part of the output id
# The value is a dictionary with the following keys: 'component', 'name', 'scale'
# component is the component name in the CellML model where the output variable is defined
# name is the variable name of the outputs
# scale is the scaling factor for the output variable
outputs={'t':{'component':'GLUT1_BG','name':'t','scale':1},
         'v_free':{'component':'GLUT1_BG','name':'v_free','scale':-1/90}, 
         'v':{'component':'GLUT1_BG','name':'v','scale':-1/90},        
         'q_Ai':{'component':'GLUT1_BG','name':'q_Ai','scale':1/90},
         }
# You can add more outputs if needed

# The following is the simulation setting
# This is to set the maximum step size for the simulation
dict_algorithmParameter={'kisaoID':'KISAO:0000467', 'name':'max_step','value':'100'} 
# You can set more algorithm parameters if needed. You can refer to get_KISAO_parameters() in src/simulator.py file to get the parameters for the specific algorithm
# Add the algorithm parameters to listOfAlgorithmParameters
# You can choose one of the simulation algorithms specified by KISAO_ALGORITHMS in src/simulator.py file
dict_algorithm={'kisaoID':'KISAO:0000535','name':'VODE','listOfAlgorithmParameters':[]} 
# This is the simulation setting
# You can choose one of the following simulation types: 'UniformTimeCourse', 'OneStep'
simSetting={'type':'UniformTimeCourse','algorithm':dict_algorithm,'initialTime':0,'outputStartTime':0,'outputEndTime':25,'numberOfSteps':25}
# simSetting={'type':'OneStep','algorithm':dict_algorithm,'step':0.1}


# The following is to add the task information to the dictionary
add_sedTask2dict(dict_sedDocument, model_id, model_source,changes,simSetting,outputs)

# You can repeat the above steps to add more tasks with DIFFERENT model names.

# ********** The following is to create the sedml file, no need to modify **********

try:
    doc=create_sedDocment(dict_sedDocument)
except ValueError as err:
    print(err)
write_sedml(doc,full_path)
print(validate_sedml(full_path))

doc=read_sedml(full_path) # Must read the sedml file again to avoid the error in the next step
exec_sed_doc(doc, path_,path_, rel_out_path=None, external_variables_info={},
              external_variables_values=[],ss_time={},cost_type=None)
# Run the sedml file
   
