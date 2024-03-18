# Read stoichiometric matrices
import csv
import sys
import numpy as np
import os
print(os.getcwd())
def load_matrix(fmatrix,rmatrix):
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
    
    # Check duplicate component names and empty stoichiometry before return
    if len(list(set(CompName)))<len(CompName) or len(list(set(ReName)))<len(ReName) or any(cell == '' for row in N_f for cell in row) or any(cell == '' for row in N_r for cell in row):
        sys.exit('There are duplicate components or empty stoichiometry') 
    else:
        return CompName, CompType, ReName, ReType, np.array(N_f).astype(int), np.array(N_r).astype(int)

if __name__ == "__main__":
    CompName,CompType,ReName,ReType,N_f,N_r=load_matrix('../tests/SLCT4_f.csv','../tests/SLCT4_r.csv')
    
    print(CompName,CompType,ReName,ReType,N_f,N_r)
