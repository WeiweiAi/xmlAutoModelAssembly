import sys
import os
sys.path.append('../../')
from src.buildBG import buildBG, to_cellmlV1_params, to_cellmlV1_models

file_path='C:/Users/wai484/temp/b65/Facilitated transporter/'
fmatrix='SLC2_f.csv'
rmatrix='SLC2_r.csv'
comp_dict=buildBG(fmatrix,rmatrix,file_path)
to_cellmlV1_params(comp_dict, model_name='params_BG',model_file='params_BG.txt',file_path=file_path)
to_cellmlV1_models(comp_dict, model_name='GLUT1_BG',model_file='GLUT1_BG.txt',params_file='params_BG.cellml',file_path=file_path)