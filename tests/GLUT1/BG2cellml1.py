import sys
import os
sys.path.append('../../')
from src.buildBG import buildBG, to_cellmlV1_params, to_cellmlV1_models,update_params
from src.readBG import kinetic2BGparams,load_matrix
import numpy as np

file_path='C:/Users/wai484/temp/b65/Facilitated transporter/'
fmatrix='SLC2_f.csv'
rmatrix='SLC2_r.csv'
comp_dict=buildBG(fmatrix,rmatrix,file_path)
CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
V=1
V_o=90
h=0.726;g=12.1;c=1113;d=90.3;a=500*V_o;b=a*9.5;f=3*V_o;e=12.8459*f
kf=np.array([[h, c, a, e]]).transpose()
kr=np.array([[g, d, b, f]]).transpose()
K_c=np.array([[1]]).transpose()
N_c=np.array([[1,-1,0,0,0,0]]).transpose()
K_c=np.array([[]]).transpose()
N_c=np.array([[]]).transpose()
V_i=90
V_o=90
V_E=1
Ws=np.array([[V_i,V_o,V_E,V_E,V_E,V_E]]).transpose()
kappa, K, K_eq, diff,  zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)
KA=K[0][0]; K1=K[2][0];K2=K[3][0];K3=K[4][0];K4=K[5][0]
kappa1=kappa[0][0];kappa2=kappa[1][0];kappa3=kappa[2][0];kappa4=kappa[3][0]
print (kappa3,kappa4)
print(K, kappa)
assert np.isclose(K4/K1, h/g)
print (K4/K1, h/g)
assert np.isclose(K2/K3, c/d)
print (K2/K3, c/d)
print (K2/(K1*KA*V_o), b/a)
assert np.isclose(K2/(K1*KA*V_o), b/a)
print (K3/(K4*KA*V_o), e/f)
assert np.isclose(K3/(K4*KA*V_o), e/f)
print(kappa1*K4, h)
assert np.isclose(kappa1*K4*V_E, h)
print(kappa1*K1, g)
assert np.isclose(kappa1*K1*V_E, g)
print(kappa2*K2, c)
assert np.isclose(kappa2*K2*V_E, c)
print(kappa2*K3, d)
assert np.isclose(kappa2*K3*V_E, d)
print(kappa3*K1*KA, a)
assert np.isclose(kappa3*K1*V_E*KA*V_o, a)
print(kappa3*K2, b)
assert np.isclose(kappa3*K2*V_E, b)
print(kappa4*K4*KA, f)
assert np.isclose(kappa4*K4*V_E*KA*V_o, f)
print(kappa4*K3*V_E, e)

n_zeros=len(CompName)
update_params(comp_dict,n_zeros, kappa, K,Ws)
to_cellmlV1_params(comp_dict, model_name='params_BG',model_file='params_BG.txt',file_path=file_path)
to_cellmlV1_models(comp_dict, model_name='GLUT1_BG',model_file='GLUT1_BG_0.txt',params_file='params_BG.cellml',file_path=file_path)