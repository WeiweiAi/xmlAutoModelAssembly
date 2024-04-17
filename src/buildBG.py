from .BG_components import e_components_units, biochem_components_units,m_components_units
from .readBG import load_matrix,kinetic2BGparams
import pandas as pd
import copy
import numpy as np

defUnit=["ampere","becquerel","candela","celsius","coulomb","dimensionless","farad","gram","gray","henry",
    "hertz","joule","katal","kelvin","kilogram","liter","litre","lumen","lux","meter","metre","mole",
    "newton","ohm","pascal","radian","second","siemens","sievert","steradian","tesla","volt","watt","weber"]
params_common=['R','T','F']
def buildBG(fmatrix,rmatrix,file_path='./'):
    e_components=e_components_units()['components']
    biochem_components=biochem_components_units()['components']
    m_components=m_components_units()['components']
    CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
    compNames=CompName+ReName
    compTypes=CompType+ReType
    n_zeros=len(CompName)
    n_ones=len(ReName)
    # Use the CompType and ReType to look up the corresponding components in the e_components and biochem_components
    # Get the parameters for components and declare the parameters in the format: "var varName: varUnits {init: 1, pub: out}}"
    # Save the parameters in a dictionary with the key as the variable name and the value as the cellml code
    comp_dict={}    
    for i in range(len(compNames)):
        compType=compTypes[i]
        compName=compNames[i]
        compIndex=compName # compName is the key for the dictionary, make it unique; the ReName and CompName may have overlap;
        if compType in e_components.keys():
            comp_dict[compIndex]=copy.deepcopy(e_components[compType])
            comp_dict[compIndex]['type']=compType
            # Instantiate the parameters, variables and constitutive relations for the component
            for param in comp_dict[compIndex]['params'].keys():
                if param not in params_common:
                    comp_dict[compIndex]['params'][param]['symbol']=comp_dict[compIndex]['params'][param]['symbol']+ '_' + compName
            for var in comp_dict[compIndex]['vars'].keys():
                comp_dict[compIndex]['vars'][var]['symbol']=comp_dict[compIndex]['vars'][var]['symbol']+ '_' + compName
            if 'state_vars' in e_components[compType].keys():                  
                for state_var in e_components[compType]['state_vars'].keys():
                    comp_dict[compIndex]['state_vars'][state_var]['symbol']=comp_dict[compIndex]['state_vars'][state_var]['symbol']+ '_' + compName                  
        elif compType in biochem_components.keys():
            comp_dict[compIndex]=copy.deepcopy(biochem_components[compType])
            comp_dict[compIndex]['type']=compType
            # Instantiate the parameters, variables and constitutive relations for the component
            for param in comp_dict[compIndex]['params'].keys():
                if param not in params_common:
                    comp_dict[compIndex]['params'][param]['symbol']=comp_dict[compIndex]['params'][param]['symbol']+ '_' + compName
            for var in comp_dict[compIndex]['vars'].keys():
                comp_dict[compIndex]['vars'][var]['symbol']=comp_dict[compIndex]['vars'][var]['symbol']+ '_' + compName
            if 'state_vars' in biochem_components[compType].keys():                    
                for state_var in biochem_components[compType]['state_vars'].keys():
                    comp_dict[compIndex]['state_vars'][state_var]['symbol']=comp_dict[compIndex]['state_vars'][state_var]['symbol']+ '_' + compName
        elif compType in m_components.keys():
            comp_dict[compIndex]=copy.deepcopy(m_components[compType])
            comp_dict[compIndex]['type']=compType
            # Instantiate the parameters, variables and constitutive relations for the component
            for param in comp_dict[compIndex]['params'].keys():
                if param not in params_common:
                    comp_dict[compIndex]['params'][param]['symbol']=comp_dict[compIndex]['params'][param]['symbol']+ '_' + compName
            for var in comp_dict[compIndex]['vars'].keys():
                comp_dict[compIndex]['vars'][var]['symbol']=comp_dict[compIndex]['vars'][var]['symbol']+ '_' + compName
            if 'state_vars' in m_components[compType].keys():                    
                for state_var in m_components[compType]['state_vars'].keys():
                    comp_dict[compIndex]['state_vars'][state_var]['symbol']=comp_dict[compIndex]['state_vars'][state_var]['symbol']+ '_' + compName
        else:
            print('The component type is not found in the e_components or biochem_components or m_components')

    for j in range(len(ReName)):
        # The e_0 of the R component is the sum of the e_0 of each C component in the column of N_f[i,:]
        # The e_1 of the R component is the sum of the e_0 of each C component in the column of N_r[i,:]
        reIndex=ReName[j]
        for i in range(len(CompName)):
            compIndex=CompName[i]
            # 0 node to 1 node on port 0; 
            if N_f[i,j]!=0:
                comp_dict[reIndex]['ports']['0']['in']+=[compIndex+f':{N_f[i,j]}']
            # 0 node to 1 node on port 1; 
            if N_r[i,j]!=0:
                comp_dict[reIndex]['ports']['1']['in']+=[compIndex+f':{-N_r[i,j]}']
            # 1 node to 0 node on port 0; 
            if  'f_0' in comp_dict[compIndex]['vars'].keys() and comp_dict[compIndex]['vars']['f_0']['IOType']=='in':
                if N_f[i,j]!=0:
                    comp_dict[compIndex]['ports']['0']['in']+=[reIndex+f':{-N_f[i,j]}']

                if N_r[i,j]!=0:
                    comp_dict[compIndex]['ports']['0']['in']+=[reIndex+f':{N_r[i,j]}']
            # 1 node to 0 node on port 1;
            if 'f_1' in comp_dict[compIndex]['vars'].keys() and comp_dict[compIndex]['vars']['f_1']['IOType']=='in':
                if N_f[i,j]!=0:
                    comp_dict[compIndex]['ports']['1']['in']+=[reIndex+f':{-N_f[i,j]}']

                if N_r[i,j]!=0:
                    comp_dict[compIndex]['ports']['1']['in']+=[reIndex+f':{N_r[i,j]}']

    update_eqn(comp_dict)
    return comp_dict

def update_params(comp_dict,n_zeros, kappa, K, q_init_all, csv='params_BG.csv'):
    # assume that the kappa and K are in the same order as the components in the comp_dict
    # Create a pd frame with the columns: Parameter, Value, and Unit
    csv_pd=pd.DataFrame(columns=['Parameter','Value','Unit'])
    if K.size>0:
        j=0
        for i in range(len(K)):
            compIndex=list(comp_dict)[i]
            if abs(K[i][0])<1e-2 or abs(K[i][0])>1e2:
                K_="{:.3e}".format(K[i][0])
            else:
                K_="{:.3f}".format(K[i][0])
            comp_dict[compIndex]['params']['K']['value']=K_
            if 'q_init' in comp_dict[compIndex]['params'].keys() and comp_dict[compIndex]['type']=='Ce':
                comp_dict[compIndex]['params']['q_init']['value']=q_init_all[j][0]
                j+=1
            str_var=comp_dict[compIndex]['params']['K']['symbol']
            # split the string with the underscore and get the first element
            sub_str_1=str_var.split('_')[0]
            if len(str_var.split('_'))>1:
                sub_str_2=str_var.split('_')[1]
                latex_str='$'+sub_str_1+'_{'+sub_str_2+'}$'
            else:
                sub_str_2=''
                latex_str='$'+sub_str_1+'$'

            units=comp_dict[compIndex]['params']['K']['units']
            # split the string with the underscore and 'per'
            unit_latex_str=''
            if 'per' in units:
                unit_latex_str+=str.join('.',units.split('per')[0].split('_'))
                units_per=units.split('per')[1]
                for j in range(len(units_per.split('_'))-1):
                    unit_latex_str+=units_per.split('_')[j+1]+'$^{-1}$'
            else:
                unit_latex_str+=str.join('.',units.split('_'))

            csv_pd.loc[i]=[latex_str,K_,unit_latex_str]
    if kappa.size>0:
        for i in range(len(kappa)):
            compIndex=list(comp_dict)[i+n_zeros]
            if abs(kappa[i][0])<1e-2 or abs(kappa[i][0])>1e2:
                kappa_="{:.3e}".format(kappa[i][0])
            else:
                kappa_="{:.3f}".format(kappa[i][0])
            comp_dict[compIndex]['params']['kappa']['value']=kappa_
            str_var=comp_dict[compIndex]['params']['kappa']['symbol']
            # split the string with the underscore and get the first element
            sub_str_1=str_var.split('_')[0]
            if len(str_var.split('_'))>1:
                sub_str_2=str_var.split('_')[1]
                latex_str='$\\'+sub_str_1+'_{'+sub_str_2+'}$'
            else:
                sub_str_2=''
                latex_str='$\\'+sub_str_1+'$'
            units=comp_dict[compIndex]['params']['kappa']['units']
            # split the string with the underscore and 'per'
            unit_latex_str=''
            if 'per' in units:
                unit_latex_str+=str.join('.',units.split('per')[0].split('_'))
                units_per=units.split('per')[1]
                for j in range(len(units_per.split('_'))-1):
                    unit_latex_str+=units_per.split('_')[j+1]+'$^{-1}$'
            else:
                unit_latex_str+=str.join('.',units.split('_'))
           
            csv_pd.loc[i+len(K)]=[latex_str,kappa_,unit_latex_str]

    csv_pd.to_csv(csv,index=False)        

def update_eqn(comp_dict):
    def get_flow_outputs(sub_comps):
        flow_outputs=[]
        for comp in sub_comps:
            comp_name=comp.split(':')[0]
            stochoimetry=comp.split(':')[1]
            try:
                num_stochoimetry=int(stochoimetry)
            except:
                try:
                    num_stochoimetry=float(stochoimetry)
                except:
                    raise ValueError('The stochoimetry is not an integer or a float')

            for var in comp_dict[comp_name]['vars']:
                if 'Flow' in comp_dict[comp_name]['vars'][var]['description'] and comp_dict[comp_name]['vars'][var]['IOType']=='out':
                    if stochoimetry=='1':
                        flow_outputs+=[f"+{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    elif stochoimetry=='-1':
                        flow_outputs+=[f"-{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    elif num_stochoimetry>0:
                        flow_outputs+=[f"+{num_stochoimetry}{{dimensionless}}*{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    else:
                        flow_outputs+=[f"-{-num_stochoimetry}{{dimensionless}}*{comp_dict[comp_name]['vars'][var]['symbol']}"]
                        
        return flow_outputs 
    def get_efforts_outputs(sub_comps):
        efforts_outputs=[]
        for comp in sub_comps:
            comp_name=comp.split(':')[0]
            stochoimetry=comp.split(':')[1]
            try:
                num_stochoimetry=int(stochoimetry)
            except:
                try:
                    num_stochoimetry=float(stochoimetry)
                except:
                    raise ValueError('The stochoimetry is not an integer or a float')
            for var in comp_dict[comp_name]['vars']:
                if 'Potential' in comp_dict[comp_name]['vars'][var]['description'] and comp_dict[comp_name]['vars'][var]['IOType']=='out':
                    if stochoimetry=='1':
                        efforts_outputs+=[f"+{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    elif stochoimetry=='-1':
                        efforts_outputs+=[f"-{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    elif num_stochoimetry>0:
                        efforts_outputs+=[f"+{num_stochoimetry}{{dimensionless}}*{comp_dict[comp_name]['vars'][var]['symbol']}"]
                    else:
                        efforts_outputs+=[f"-{-num_stochoimetry}{{dimensionless}}*{comp_dict[comp_name]['vars'][var]['symbol']}"]
        return efforts_outputs
    
    for key, comp in comp_dict.items():
        if comp['type']=='Ce':
            comp['constitutive_relations']=[f"{comp['vars']['e_0']['symbol']} = R*T*ln({comp['params']['K']['symbol']}*{comp['state_vars']['q_0']['symbol']})",
            f"ode({comp['state_vars']['q_0']['symbol']},t) = {comp['vars']['f_0']['symbol']}"]
            # Get all in flows
            in_flows_=comp['ports']['0']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            sum_in_flows=' '.join(in_flows_vars)
            sum_in_flows= sum_in_flows[1:] if sum_in_flows[0]=='+' else sum_in_flows
            comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {sum_in_flows}",
                ]               
        elif comp['type']=='ch_Se':
            comp['constitutive_relations']=[f"{comp['vars']['e_0']['symbol']} = R*T*ln({comp['params']['K']['symbol']}*{comp['params']['q_init']['symbol']})"]            
        elif comp['type']=='Re':
            comp['constitutive_relations']=[
            f"{comp['vars']['f_0']['symbol']} = {comp['params']['kappa']['symbol']}*(exp({comp['vars']['e_0']['symbol']}/(R*T)) - exp({comp['vars']['e_1']['symbol']}/(R*T)))"
          ]
             # Get all in effors
            in_efforts_port0_=comp['ports']['0']['in']
            in_efforts_port0_vars=get_efforts_outputs(in_efforts_port0_)
            sum_in_efforts_port0=' '.join(in_efforts_port0_vars)
            sum_in_efforts_port0= sum_in_efforts_port0[1:] if sum_in_efforts_port0[0]=='+' else sum_in_efforts_port0

            in_efforts_port1_=comp['ports']['1']['in']
            in_efforts_port1_vars=get_efforts_outputs(in_efforts_port1_)
            sum_in_efforts_port1=' '.join(in_efforts_port1_vars)
            sum_out_efforts_port1 = sum_in_efforts_port1.replace('+','plus').replace('-','+').replace('plus','-')
            sum_out_efforts_port1= sum_out_efforts_port1[1:] if sum_out_efforts_port1[0]=='+' else sum_out_efforts_port1
            
            comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {sum_in_efforts_port0}",
                f"{comp['vars']['e_1']['symbol']} = {sum_out_efforts_port1}",
            ]
        elif comp['type']=='C' or comp['type']=='m_C':
            comp['constitutive_relations']=[
            f" {comp['vars']['e_0']['symbol']}={comp['state_vars']['q_0']['symbol']}/{comp['params']['C']['symbol']}",
            f"ode({comp['state_vars']['q_0']['symbol']},t) = {comp['vars']['f_0']['symbol']}"
          ]
             # Get all in flows
            in_flows_=comp['ports']['0']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            sum_in_flows=' '.join(in_flows_vars)
            sum_in_flows= sum_in_flows[1:] if sum_in_flows[0]=='+' else sum_in_flows
            comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {sum_in_flows}",
                ]

        elif comp['type']=='R' or comp['type']=='m_R':
            comp['constitutive_relations']=[
                f"{comp['vars']['f_0']['symbol']}={comp['vars']['e_0']['symbol']}/{comp['params']['r']['symbol']}",
            ]
            # Get all in effors
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            sum_in_efforts=' '.join(in_efforts_vars)
            sum_in_efforts= sum_in_efforts[1:] if sum_in_efforts[0]=='+' else sum_in_efforts
            comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {sum_in_efforts}",
                ]             
        elif comp['type']=='Se' or comp['type']=='e_Se' or comp['type']=='m_Se':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_0']['symbol']}={comp['params']['e']['symbol']}"
            ]
        elif comp['type']=='Sf' or comp['type']=='e_Sf' or comp['type']=='m_Sf':
            comp['constitutive_relations']=[
                f"{comp['vars']['f_0']['symbol']}={comp['params']['f']['symbol']}"
            ]
        elif comp['type']=='TF':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_1']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['e_0']['symbol']}",
                f"{comp['vars']['f_0']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['f_1']['symbol']}"
            ]
            # Get all in flows on port 1
            in_flows_=comp['ports']['1']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            sum_in_flows=' '.join(in_flows_vars)
            sum_in_flows= sum_in_flows[1:] if sum_in_flows[0]=='+' else sum_in_flows
            comp['conservation_relations']=[
                f"{comp['vars']['f_1']['symbol']} = {sum_in_flows}",
            ]                      
            # Get all in effors on port 0
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            sum_in_efforts=' '.join(in_efforts_vars)
            sum_out_efforts=sum_in_efforts.replace('+','plus').replace('-','+').replace('plus','-')
            sum_out_efforts= sum_out_efforts[1:] if sum_out_efforts[0]=='+' else sum_out_efforts
            comp['conservation_relations']+=[
                f"{comp['vars']['e_0']['symbol']} = {sum_out_efforts}"
                ]
        elif comp['type']=='zF':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_1']['symbol']}={comp['params']['r']['symbol']}*F*{comp['vars']['e_0']['symbol']}",
                f"{comp['vars']['f_0']['symbol']}={comp['params']['r']['symbol']}*F*{comp['vars']['f_1']['symbol']}"
            ]
             # Get all in flows on port 1
            in_flows_=comp['ports']['1']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            sum_in_flows=' '.join(in_flows_vars)
            sum_in_flows= sum_in_flows[1:] if sum_in_flows[0]=='+' else sum_in_flows
            comp['conservation_relations']=[
                f"{comp['vars']['f_1']['symbol']} = {sum_in_flows}",
            ]                      
            # Get all in effors on port 0
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            sum_in_efforts=' '.join(in_efforts_vars)
            sum_out_efforts=sum_in_efforts.replace('+','plus').replace('-','+').replace('plus','-')
            sum_out_efforts= sum_out_efforts[1:] if sum_out_efforts[0]=='+' else sum_out_efforts
            comp['conservation_relations']+=[
                f"{comp['vars']['e_0']['symbol']} = {sum_out_efforts}"
                ]

        elif comp['type']=='GY':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_1']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['f_0']['symbol']}",
                f"{comp['vars']['e_0']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['f_1']['symbol']}"
            ]
    return comp_dict

def to_cellmlV1_params(comp_dict, model_name='params_BG',model_file='params_BG.txt',file_path='./'):
    indent=' '*4
    cellml_code=f'def model {model_name} as\n'
    cellml_code+=indent+'def import using "./units.cellml" for\n'
    param_units=set()
    params_common_set=set()
    # Get all the units used in the parameters
    for comp in comp_dict:
        for param in comp_dict[comp]['params']:
            if param in params_common:
                params_common_set.add(param)
            if comp_dict[comp]['params'][param]['units'] not in defUnit:
                param_units.add(comp_dict[comp]['params'][param]['units'])
    for unit in param_units:
        cellml_code+=indent*2+f"unit {unit} using unit {unit};\n"
    cellml_code+=indent+'enddef;\n'

    cellml_code+=indent+f'def comp {model_name} as\n'
    if 'R' in params_common_set:
        cellml_code+=indent*2+f"var R: J_per_K_mol"+f"{{ init: 8.31, pub: out}};\n"
    if 'T' in params_common_set:
        cellml_code+=indent*2+f"var T: kelvin"+f"{{ init: 293, pub: out}};\n"
    if 'F' in params_common_set:
        cellml_code+=indent*2+f'var F: C_per_mol'+f"{{ init: 96485, pub: out}};\n"
    for comp in comp_dict:
        for param in comp_dict[comp]['params']:
            if param not in ['R','T','F']:
                if (comp_dict[comp]['type']=="ch_Se" and param=='q_init') or (comp_dict[comp]['type']=='e_Se' and param =='e') or (comp_dict[comp]['type']=="m_Se" and param=='e'): 
                    cellml_code+=indent*2+f"var {comp_dict[comp]['params'][param]['symbol']}: {comp_dict[comp]['params'][param]['units']}" + f"{{ pub: out}};\n"
                else:
                    cellml_code+=indent*2+f"var {comp_dict[comp]['params'][param]['symbol']}: {comp_dict[comp]['params'][param]['units']}" + f"{{ init: {comp_dict[comp]['params'][param]['value']}, pub: out}};\n"
                    
        
    cellml_code+=indent+'enddef;\n'
    cellml_code+='enddef;\n'
    # Save the model to a file
    with open(file_path+model_file, 'w') as f:
        f.write(cellml_code)
    return cellml_code

def to_cellmlV1_models(comp_dict, model_name='BG',model_file='BG.txt',params_file='params_BG.cellml',file_path='./'):
    indent=' '*4
    # Apart from parameters, add vairables, state variables, constitutive relations and conservation relations
    param_units=set()
    cellml_code_p=''
    cellml_code_vars=''
    cellml_code_state_vars=''
    cellml_code_constitutive_relations=''
    cellml_code_conservation_relations=''
    params_common_set=set()
    for comp in comp_dict:
        for param in comp_dict[comp]['params']:
            if param in params_common:
                params_common_set.add(param)
            if comp_dict[comp]['params'][param]['units'] not in defUnit:
                param_units.add(comp_dict[comp]['params'][param]['units'])
        for var in comp_dict[comp]['vars']:
            if comp_dict[comp]['vars'][var]['units'] not in defUnit:
                param_units.add(comp_dict[comp]['vars'][var]['units'])
        if 'state_vars' in comp_dict[comp].keys():
            for state_var in comp_dict[comp]['state_vars']:
                param_units.add(comp_dict[comp]['state_vars'][state_var]['units'])
    
    cellml_code=f'def model {model_name} as\n'
    cellml_code+=indent+'def import using "./units.cellml" for\n'
    for unit in param_units:
        cellml_code+=indent*2+f"unit {unit} using unit {unit};\n"
    cellml_code+=indent+'enddef;\n'
    
    cellml_code+=indent+f'def import using "{params_file}" for\n'
    params_model_name=params_file.split('.')[0]
    cellml_code+=indent*2+f'comp {params_model_name} using comp {params_model_name};\n'
    cellml_code+=indent+'enddef;\n'
    
    cellml_code+=indent+f'def comp {model_name} as\n'
    cellml_code+=indent*2+f"var t: second;\n"
    if 'R' in params_common_set:
        cellml_code+=indent*2+f"var R: J_per_K_mol"+f"{{ pub: in}};\n"
    if 'T' in params_common_set:
        cellml_code+=indent*2+f"var T: kelvin"+f"{{ pub: in}};\n" 
    if 'F' in params_common_set:
        cellml_code+=indent*2+f'var F: C_per_mol'+f"{{ pub: in}};\n"
    for comp in comp_dict:
        for param in comp_dict[comp]['params']:
            if param not in params_common:
                cellml_code_p+=indent*2+f"var {comp_dict[comp]['params'][param]['symbol']}: {comp_dict[comp]['params'][param]['units']}" + f"{{ pub: in}};\n"
        for var in comp_dict[comp]['vars']:
            cellml_code_vars+=indent*2+f"var {comp_dict[comp]['vars'][var]['symbol']}: {comp_dict[comp]['vars'][var]['units']};\n" 
        if 'state_vars' in comp_dict[comp].keys():
            for state_var in comp_dict[comp]['state_vars']:
                q_init=comp_dict[comp]['state_vars'][state_var]['value']
                cellml_code_state_vars+=indent*2+f"var {comp_dict[comp]['state_vars'][state_var]['symbol']}: {comp_dict[comp]['state_vars'][state_var]['units']}" + f"{{ init: {comp_dict[comp]['params'][q_init]['symbol']}}};\n"
        for enq in comp_dict[comp]['constitutive_relations']:
            cellml_code_constitutive_relations+=indent*2+enq+';\n'
        if 'conservation_relations' in comp_dict[comp].keys():
            for enq in comp_dict[comp]['conservation_relations']:
                cellml_code_conservation_relations+=indent*2+enq+';\n'
    cellml_code+=cellml_code_p
    cellml_code+=cellml_code_vars
    cellml_code+=cellml_code_state_vars
    cellml_code+=cellml_code_constitutive_relations
    cellml_code+=cellml_code_conservation_relations
    cellml_code+=indent+f"enddef;\n"
    cellml_code+=indent+f'def map between {params_model_name} and {model_name} for\n'
    if 'R' in params_common_set:
        cellml_code+=indent*2+'vars R and R;\n'
    if 'T' in params_common_set:
        cellml_code+=indent*2+'vars T and T;\n'
    if 'F' in params_common_set:
        cellml_code+=indent*2+'vars F and F;\n'
    for comp in comp_dict:
        for param in comp_dict[comp]['params']:
            if param not in params_common:
                cellml_code+=indent*2+f"vars {comp_dict[comp]['params'][param]['symbol']} and {comp_dict[comp]['params'][param]['symbol']};\n"
    cellml_code+=indent+'enddef;\n'

    cellml_code+='enddef;\n'
    # Save the model to a file
    with open(file_path+model_file, 'w') as f:
        f.write(cellml_code)
    return cellml_code



def print_comp_dict(comp_dict):
    for comp in comp_dict:
        print(comp)
        for var in comp_dict[comp]['vars']:
            print(var, comp_dict[comp]['vars'][var])
        for param in comp_dict[comp]['params']:
            print(param, comp_dict[comp]['params'][param])
        for port in comp_dict[comp]['ports']:
            print(port, comp_dict[comp]['ports'][port])
        if 'state_vars' in comp_dict[comp].keys():
            for state_var in comp_dict[comp]['state_vars']:
                print(state_var, comp_dict[comp]['state_vars'][state_var])
        print(comp_dict[comp]['constitutive_relations'])
        if 'conservation_relations' in comp_dict[comp].keys():
            print(comp_dict[comp]['conservation_relations'])
    return comp_dict
            
if __name__ == "__main__": 
    fmatrix='../tests/SLC2_f.csv'
    rmatrix='../tests/SLC2_r.csv'
    comp_dict=buildBG(fmatrix,rmatrix) 
    CompName,CompType,ReName,ReType,N_f,N_r=load_matrix('../tests/SLC2_f.csv','../tests/SLC2_r.csv')
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
    kappa, K, diff, zero_est= kinetic2BGparams(N_f,N_r,kf,kr,K_c,N_c,Ws)
    n_zeros=len(CompName)
    update_params(comp_dict,n_zeros, kappa, K)
    cellml_code=to_cellmlV1_params(comp_dict) 
    print(cellml_code)
    cellml_code=to_cellmlV1_models(comp_dict)
    print(cellml_code)

        

        
