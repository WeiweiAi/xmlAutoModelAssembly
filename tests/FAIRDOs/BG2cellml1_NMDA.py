import sys
import os
sys.path.append('../../')
from src.buildBG import buildBG, to_cellmlV1_params, to_cellmlV1_models,update_params
from src.readBG import kinetic2BGparams,load_matrix
import numpy as np
file_path='./'
fmatrix='NMDA_f.csv'
rmatrix='NMDA_r.csv'
comp_dict=buildBG(fmatrix,rmatrix,file_path)
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
n_zeros=len(CompName)
csv_file=file_path+'NMDA_BG_1.csv'
fmatrix='NMDA_f.csv'
rmatrix='NMDA_r.csv'
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
AVO=6.022e23
q_tot=6.022e10 # 6.022e10 molecules per cell 100 fmol/cell
q_init = q_tot/AVO/6*1e15 # fmol 100 fmol/cell
V1=1e-3
k_1f=2e7*V1
k_1r=8
k_2f=1e7*V1
k_2r=16
k_3f=1e9*V1
k_3r=8
k_4f=1e9*V1
k_4r=8
k_5f=1e9*V1
k_5r=8
k_6f=2e7*V1
k_6r=8
k_7f=1e7*V1
k_7r=16

k_8f=91.6 # 200 µM L-Glutamate
k_8r=46.5 # 200 µM L-Glutamate

k_8f=95.8 # 30 µM L-Cysteate
k_8r=39.1 # 30 µM L-Cysteate

k_8r=250 # 100 µM L-Glutamate 
k_8f=100 # 100 µM L-Glutamate 


print('q_tot=',q_init*6)

balance1=k_1f*k_2f*k_5f*k_7r*k_6r*k_3r/(k_1r*k_2r*k_5r*k_7f*k_6f*k_3f)
balance2=k_1f*k_4f*k_6r*k_3r/(k_1r*k_4r*k_6f*k_3f)
balance3=k_2f*k_5f*k_7r*k_4r/(k_2r*k_5r*k_7f*k_4f)

print(balance1,balance2,balance3)
kf=np.array([[k_1f,k_2f,k_3f,k_4f,k_5f,k_6f,k_7f,k_8f]]).transpose()
kr=np.array([[k_1r,k_2r,k_3r,k_4r,k_5r,k_6r,k_7r,k_8r ]]).transpose()
K_c=np.array([[]]).transpose()
N_c=np.array([[]]).transpose()

V_E=1
V_o=1 # pL
V_i=1 # pL
Ws=np.array([[V_E,V_E,V_E,V_E,V_E,V_E,V_i,V_i,V_i,V_E]]).transpose()
kappa, K, K_eq, diff,  zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)

q_init_all=np.array([[q_init]*6]).transpose()

update_params(comp_dict,n_zeros, kappa, K, q_init_all, csv_file)

import json
with open('data.json', 'w') as f:
    json.dump(comp_dict, f,indent=4)

to_cellmlV1_params(comp_dict, model_name='params_BG',model_file='params_BG_NMDA_1.txt',file_path=file_path)
to_cellmlV1_models(comp_dict, model_name='NMDA_BG',model_file='NMDA_BG.txt',params_file='params_BG_NMDA_1.cellml',file_path=file_path)