import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.analyser import parse_model
from src.coder import writeCellML,writePythonCode
from libcellml import Annotator

# create model
"""
model = create_model('test_model')
file_path='./csv/SLC_template3_ss.csv'
flag, external_variables=csv2model(file_path,model)
model_path='./csv/test_model.cellml'
full_path_imported_model='./csv/units_BG.cellml'
importSource, import_model=import_setup(model_path,full_path_imported_model, strict_mode=True)
units_to_define=importUnits(model,importSource)
"""
full_path='./csv/SLCT3_ss_test.cellml'
#writeCellML(full_path, model)
model_parse, issues=parse_model(full_path, strict_mode=True)
annotator = Annotator()
annotator.setModel(model_parse)
annotator.clearAllIds()
writeCellML(model_parse,full_path)

