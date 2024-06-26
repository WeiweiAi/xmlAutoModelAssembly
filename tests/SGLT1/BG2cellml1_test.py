import sys
import os
sys.path.append('../../')
from src.buildBG import buildBG, to_cellmlV1_params, to_cellmlV1_models,update_params
from src.readBG import kinetic2BGparams,load_matrix
import numpy as np
file_path='C:/Users/wai484/temp/b65/Electrogenic cotransporter/'
fmatrix='SLC5_f.csv'
rmatrix='SLC5_r.csv'
comp_dict=buildBG(fmatrix,rmatrix,file_path)
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
n_zeros=len(CompName)
csv_file=file_path+'SGLT1_BG_fast.csv'
fmatrix='SLC5_f_chem.csv'
rmatrix='SLC5_r_chem.csv'
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
AVO=6.022e23
q_tot=6e10 # 5e10 molecules per cell
q_init = q_tot/AVO/6*1e15 # fmol
V1=1e-3
scale=1e4
k_12=8e4*V1*V1*scale
k_23=1e5*V1*scale
k_34=50
k_45=800*scale
k_56=10*scale
k_61=3
k_25=0.3
k_21=500/0.08*k_12
k_32=20/100*k_23
k_43=50
k_65=50*V1*V1/10*k_56
k_16=35
k_52=k_12*k_25*k_56*k_61/(k_21*k_65*k_16)
k_54=k_23*k_34*k_45*k_52/(k_32*k_43*k_25)

print ('k_52=',k_52)
print ('k_54=',k_54)
print('q_tot=',q_init*6)

balance1=k_12*k_23*k_34*k_45*k_56*k_61/(k_21*k_32*k_43*k_54*k_65*k_16)
balance2=k_12*k_25*k_56*k_61/(k_21*k_52*k_65*k_16)
balance3=k_23*k_34*k_45*k_52/(k_32*k_43*k_54*k_25)
print(balance1,balance2,balance3)
kf=np.array([[k_12, k_23, k_34, k_45, k_56, k_61, k_25]]).transpose()
kr=np.array([[k_21, k_32, k_43, k_54, k_65, k_16, k_52 ]]).transpose()
K_c=np.array([[]]).transpose()
N_c=np.array([[]]).transpose()

V_E=1
V_o=8.5e5
V_i=8.5e5
Ws=np.array([[V_i,V_o,V_i,V_o,V_E,V_E,V_E,V_E,V_E,V_E]]).transpose()
kappa, K, K_eq, diff,  zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)

q_init_all=np.array([[q_init]*6]).transpose()

update_params(comp_dict,n_zeros, kappa, K, q_init_all, csv_file)

import json
with open('data.json', 'w') as f:
    json.dump(comp_dict, f,indent=4)

to_cellmlV1_params(comp_dict, model_name='params_BG_fast',model_file='params_BG_fast.txt',file_path=file_path)
to_cellmlV1_models(comp_dict, model_name='SGLT1_BG_fast',model_file='SGLT1_BG_fast.txt',params_file='params_BG_fast.cellml',file_path=file_path)