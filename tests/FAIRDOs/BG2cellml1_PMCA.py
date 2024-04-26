import sys
import os
sys.path.append('../../')
from src.buildBG import buildBG, to_cellmlV1_params, to_cellmlV1_models,update_params
from src.readBG import kinetic2BGparams,load_matrix
import numpy as np
import math
file_path='./'
fmatrix='PMCA_f.csv'
rmatrix='PMCA_r.csv'
comp_dict=buildBG(fmatrix,rmatrix,file_path)
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
n_zeros=len(CompName)
csv_file=file_path+'PMCA_BG.csv'
fmatrix='PMCA_f.csv'
rmatrix='PMCA_r.csv'
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
deltaG_ATP=-11.9e3 # J/mol
R=8.314 # J/(K*mol)
T=293 # K
AVO=6.022e23
q_tot=6.022e10 # 6.022e10 molecules per cell 100 fmol/cell
q_init = q_tot/AVO/6*1e15 # fmol 100 fmol/cell
V1=1e-3
k_1f=1e6*V1
k_1r=0.1
k_2f=25900
k_2r=2
k_3f=2540
k_3r=67200
k_4f=50
k_4r=2e-3*V1
k_5f=20.5
k_5r=149
k_6f=911
k_6r=k_1f*k_2f*k_3f*k_4f*k_5f*k_6f/(k_1r*k_2r*k_3r*k_4r*k_5r*math.exp(-deltaG_ATP/(R*T)))

print('q_tot=',q_init*6)
print('k_6r=',k_6r)

kf=np.array([[k_1f,k_2f,k_3f,k_4f,k_5f,k_6f]]).transpose()
kr=np.array([[k_1r,k_2r,k_3r,k_4r,k_5r,k_6r ]]).transpose()
K_c=np.array([[1]]).transpose()
N_c=np.array([[0,0,0,0,0,0,1,0,0,0,-1]]).transpose()

V_E=1
V_o=1 # pL
V_i=1 # pL
Ws=np.array([[V_E,V_E,V_E,V_E,V_E,V_E,V_i,V_i,V_i,V_i,V_o]]).transpose()
kappa, K, K_eq, diff,  zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)

q_init_all=np.array([[q_init]*6]).transpose()

update_params(comp_dict,n_zeros, kappa, K, q_init_all, csv_file)

import json
with open('data.json', 'w') as f:
    json.dump(comp_dict, f,indent=4)

to_cellmlV1_params(comp_dict, model_name='params_BG',model_file='params_BG_PMCA.txt',file_path=file_path)
to_cellmlV1_models(comp_dict, model_name='PMCA_BG',model_file='PMCA_BG.txt',params_file='params_BG_PMCA.cellml',file_path=file_path)