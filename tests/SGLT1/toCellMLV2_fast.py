import sys
import os
sys.path.append('../../')
from src.coder import toCellML2

# This is a template for converting a CellML 1.X model to CellML 2.0

# Specify the path to the model and the model name
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/'
for model_name in ['params_ss_fast','params_BG_step_ss_fast','SGLT1_ss_fast','SGLT1_BG_step_ss_fast']:
    modelfile= model_name + '.cellml'
    oldPath=path_+ modelfile

    # create a new directory for the new model if it does not exist
    if not os.path.exists(path_+'CellMLV2'):
        os.makedirs(path_+'CellMLV2')
    newPath=path_+'CellMLV2/'+ modelfile
    if model_name == 'SGLT1_ss_fast' or model_name == 'SGLT1_BG_step_ss_fast':
        py_full_path=newPath.replace('.cellml','.py')
    else:
        py_full_path=None

    # convert the model to CellML 2.0
    toCellML2(oldPath, newPath, external_variables_info={},strict_mode=True, py_full_path=py_full_path)

"""
The following error message is expected and you can ignore it:
The method "parse_model" found 1 issues:<br>Given model is a CellML 1.1 model, 
the parser will try to represent this model in CellML 2.0.<br>The element type is: model<br>The reference rule is: <br>

If the following error message is shown, you need to fix the model by removing the initial value of the variable of integration.:

"validate_model: No issues found!<br>resolve_imports: No issues found!<br>The method \"analyse_model\" found 2 issues:
<br>Variable 't' in component 'main' cannot be both a variable of integration and initialised.
<br>The element type is: variable<br>The reference rule is: <br>Variable 't' in component 'main' cannot be both a variable of integration and initialised.<br>The 
element type is: variable<br>The reference rule is: <br>"

"""