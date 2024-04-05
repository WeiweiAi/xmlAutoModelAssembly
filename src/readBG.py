# Read stoichiometric matrices
import csv
import sys
import numpy as np
import os
import sympy
print(os.getcwd())
def load_matrix(fmatrix,rmatrix):
    """
    Load stoichiometric matrices from csv files

    Parameters
    ----------
    fmatrix : str
        The file path of the forward stoichiometric matrix
    rmatrix : str
        The file path of the reverse stoichiometric matrix

    Returns
    -------
    CompName : list
        A list of component names
    CompType : list
        A list of component types
    ReName : list
        A list of reaction names
    ReType : list
        A list of reaction types
    N_f : numpy.ndarray
        The forward stoichiometric matrix
    N_r : numpy.ndarray
        The reverse stoichiometric matrix
    """
    # * * ReType ReType
    # * * ReName ReName
    # CompType CompName 0 1 
    # CompType CompName 1 0
    startR=2
    startC=2
    N_f = []
    N_r = []
    CompName=[]
    CompType=[]
    with open(fmatrix,'r') as f:
        reader = csv.reader(f,delimiter=',')
        line_count = 0
        for row in reader:
            if line_count ==startR-2:
                ReType=row[startC:]
                line_count += 1
            elif line_count ==startR-1:
                ReName=[s for s in row[startC:]]
                line_count += 1
            else:
                N_f.append(row[startC:])
                CompName.append(row[startC-1])
                CompType.append(row[startC-2])
        f.close()
    with open(rmatrix,'r') as f:
        reader = csv.reader(f,delimiter=',')
        line_count = 0
        for row in reader:
            if line_count <startR:                
                line_count += 1            
            else:
                N_r.append(row[startC:])
        f.close()
    
    return CompName, CompType, ReName, ReType, np.array(N_f).astype(int), np.array(N_r).astype(int)

def kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws):
    """
    Convert kinetic parameters to BG parameters

    Parameters
    ----------
    N_f : numpy.ndarray
        The forward stoichiometry matrix
    N_r : numpy.ndarray
        The reverse stoichiometry matrix
    kf : numpy.ndarray
        The forward rate constants,
        a column vector with the same number of rows as the number of reactions
        and the same order as the reactions in N_f  
    kr : numpy.ndarray
        The reverse rate constants,
        a column vector with the same number of rows as the number of reactions
        and the same order as the reactions in N_r
    K_c : numpy.ndarray
        The constraints vector,
        a column vector
    N_c : numpy.ndarray
        The constraints matrix,
        the columns of N_c is the same as the number of the K_c
        the rows of N_c is the same as the number of the species
    Ws : numpy.ndarray
        The volume vector,
        a column vector with the size of number of reactions nr + number of species ns,
        the first nr elements are 1 for reactions, the last ns elements are the volume of species

    Returns
    -------
    kappa : numpy.ndarray
        The reaction rate constants
    K : numpy.ndarray
        The thermodynamic constants
    K_eq : numpy.ndarray
        The equilibrium constants
    diff : float
        The difference between the estimated and the input kinetic parameters
    zero_est : numpy.ndarray
        The estimated zero values of the detailed balance constraints

    """
    
    N_fT=np.transpose(N_f)
    N_rT=np.transpose(N_r)
    N = N_r - N_f
    num_cols = N_f.shape[1] # number of reactions, the same as the number of columns in N_f
    num_rows = N_f.shape[0] # number of species, the same as the number of rows in N_f
    I=np.identity(num_cols)
    N_cT=np.transpose(N_c)
    num_contraints = K_c.shape[0]
    zerofill=np.zeros((num_contraints,num_cols))
    K_eq = np.divide(kf,kr)
    if len(K_c)!=0:
        M=np.block([
            [I, N_fT],
            [I, N_rT],
            [zerofill, N_cT]
        ])
        k= np.block([
            [kf],
            [kr],
            [K_c]
        ]) 
        N_b =np.hstack([-N, N_c])
        K_contraints = np.block([
            [K_eq],
            [K_c]
        ])
    else:
        M=np.block([
            [I, N_fT],
            [I, N_rT]
        ])
        k= np.block([
            [kf],
            [kr]
        ])
        N_b = -N
        K_contraints = K_eq
    # construct W matrix
    W=np.vstack([np.ones((num_cols,1)),Ws])   
    # convert kinetic parameters to BG parameters
    lambdaW= np.exp(np.matmul(np.linalg.pinv(M),np.log(k)))
    lambda_ = np.divide(lambdaW,W)
    kappa=lambda_[:num_cols]
    K = lambda_[num_cols:]
    
    # check if the solution is valid
    N_rref, _ = sympy.Matrix(N).rref()
    zero_est = None
    R_mat = np.array(sympy. nsimplify(sympy.Matrix(N), rational=True).nullspace())
    if R_mat.size>0:
        R_mat = np.transpose(np.array(R_mat).astype(np.float64))[0]
        zero_est = np.matmul(R_mat.T,K_eq)
    # Check that there is a detailed balance constraint
    Z = sympy.nsimplify(sympy.Matrix(N_b), rational=True).nullspace() #rational_nullspace(M, 2)
    if Z:
        Z = np.transpose(np.array(Z).astype(np.float64))[0]
        zero_est = np.matmul(Z.T,np.log(K_contraints))

    k_est = np.exp(np.matmul(M,np.log(lambdaW)))
    diff = np.sum(np.abs(np.divide(k_est - k,k)))

    return kappa, K, K_eq, diff, zero_est

if __name__ == "__main__":
    CompName,CompType,ReName,ReType,N_f,N_r=load_matrix('../tests/SLC2_f.csv','../tests/SLC2_r.csv')
    
    print(CompName,CompType,ReName,ReType,N_f,N_r)
    kf=np.array([[0.726, 1113, 50, 128.456]]).transpose()
    kr=np.array([[12.1, 90.3, 50*9.5,10]]).transpose()
    K_c=np.array([[1]]).transpose()
    N_c=np.array([[1,-1,0,0,0,0]]).transpose()
   # K_c=np.array([[]]).transpose()
   # N_c=np.array([[]]).transpose()
    V_i=90
    V_o=90
    V_E=90
    Ws=np.array([[V_i,V_o,V_E,V_E,V_E,V_E]]).transpose()
 #   Ws=np.array([[1, 1, 1, 1, 1, 1]]).transpose()
    kappa, K,   K_eq, diff, zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)
