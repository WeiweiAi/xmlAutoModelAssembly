from .BG_components import e_components_units, biochem_components_units
from .readBG import load_matrix
import os
import copy
print(os.getcwd())
defUnit=["ampere","becquerel","candela","celsius","coulomb","dimensionless","farad","gram","gray","henry",
    "hertz","joule","katal","kelvin","kilogram","liter","litre","lumen","lux","meter","metre","mole",
    "newton","ohm","pascal","radian","second","siemens","sievert","steradian","tesla","volt","watt","weber"]
params_common=['R','T','F']
def buildBG(fmatrix,rmatrix,file_path='./'):
    e_components=e_components_units()['components']
    biochem_components=biochem_components_units()['components']
    CompName,CompType,ReName,ReType,N_f,N_r=load_matrix(file_path+fmatrix,file_path+rmatrix)
    compNames=CompName+ReName
    compTypes=CompType+ReType
    # Use the CompType and ReType to look up the corresponding components in the e_components and biochem_components
    # Get the parameters for components and declare the parameters in the format: "var varName: varUnits {init: 1, pub: out}}"
    # Save the parameters in a dictionary with the key as the variable name and the value as the cellml code
    comp_dict={}    
    for i in range(len(compNames)):
        compType=compTypes[i]
        compName=compNames[i]
        if compType in e_components.keys():
            comp_dict[compName]=copy.deepcopy(e_components[compType])
            comp_dict[compName]['type']=compType
            # Instantiate the parameters, variables and constitutive relations for the component
            for param in comp_dict[compName]['params'].keys():
                if param not in params_common:
                    comp_dict[compName]['params'][param]['symbol']=comp_dict[compName]['params'][param]['symbol']+ '_' + compName
            for var in comp_dict[compName]['vars'].keys():
                comp_dict[compName]['vars'][var]['symbol']=comp_dict[compName]['vars'][var]['symbol']+ '_' + compName
            if 'state_vars' in e_components[compType].keys():                  
                for state_var in e_components[compType]['state_vars'].keys():
                    comp_dict[compName]['state_vars'][state_var]['symbol']=comp_dict[compName]['state_vars'][state_var]['symbol']+ '_' + compName                  
        elif compType in biochem_components.keys():
            comp_dict[compName]=copy.deepcopy(biochem_components[compType])
            comp_dict[compName]['type']=compType
            # Instantiate the parameters, variables and constitutive relations for the component
            for param in comp_dict[compName]['params'].keys():
                if param not in params_common:
                    comp_dict[compName]['params'][param]['symbol']=comp_dict[compName]['params'][param]['symbol']+ '_' + compName
            for var in comp_dict[compName]['vars'].keys():
                comp_dict[compName]['vars'][var]['symbol']=comp_dict[compName]['vars'][var]['symbol']+ '_' + compName
            if 'state_vars' in biochem_components[compType].keys():                    
                for state_var in biochem_components[compType]['state_vars'].keys():
                    comp_dict[compName]['state_vars'][state_var]['symbol']=comp_dict[compName]['state_vars'][state_var]['symbol']+ '_' + compName
        else:
            print('The component type is not found in the e_components and biochem_components')

    for j in range(len(ReName)):
        # The e_0 of the R component is the sum of the e_0 of each C component in the column of N_f[i,:]
        # The e_1 of the R component is the sum of the e_0 of each C component in the column of N_r[i,:]
        reName=ReName[j]
        for i in range(len(CompName)):
            if N_f[i,j]>0:
                comp_dict[reName]['ports']['0']['in']+=[CompName[i]+f':{N_f[i,j]}']
                comp_dict[CompName[i]]['ports']['0']['out']+=[reName+f':{N_f[i,j]}']
            if N_r[i,j]>0:
                if '1' in  comp_dict[reName]['ports'].keys():
                    comp_dict[reName]['ports']['1']['out']+=[CompName[i]+f':{N_r[i,j]}']
                else:
                    comp_dict[reName]['ports']['0']['out']+=[CompName[i]+f':{N_r[i,j]}']
                comp_dict[CompName[i]]['ports']['0']['in']+=[reName+f':{N_r[i,j]}']               
    update_eqn(comp_dict)
    return comp_dict

def update_eqn(comp_dict):
    def get_flow_outputs(sub_comps):
        flow_outputs=[]
        for comp in sub_comps:
            comp_name=comp.split(':')[0]
            stochoimetry=comp.split(':')[1]
            for var in comp_dict[comp_name]['vars']:
                if 'Flow' in comp_dict[comp_name]['vars'][var]['description'] and comp_dict[comp_name]['vars'][var]['IOType']=='out':
                    if stochoimetry=='1':
                        flow_outputs+=[comp_dict[comp_name]['vars'][var]['symbol']]
                    else:
                        flow_outputs+=[comp_dict[comp_name]['vars'][var]['symbol']+f"*{stochoimetry}{{dimensionless}}"]
        return flow_outputs 
    def get_efforts_outputs(sub_comps):
        efforts_outputs=[]
        for comp in sub_comps:
            comp_name=comp.split(':')[0]
            stochoimetry=comp.split(':')[1]
            for var in comp_dict[comp_name]['vars']:
                if 'Potential' in comp_dict[comp_name]['vars'][var]['description'] and comp_dict[comp_name]['vars'][var]['IOType']=='out':
                    if stochoimetry=='1':
                        efforts_outputs+=[comp_dict[comp_name]['vars'][var]['symbol']]
                    else:
                        efforts_outputs+=[comp_dict[comp_name]['vars'][var]['symbol']+f"*{stochoimetry}{{dimensionless}}"]
        return efforts_outputs
    
    for key, comp in comp_dict.items():
        if comp['type']=='Ce':
            comp['constitutive_relations']=[f"{comp['vars']['e_0']['symbol']} = R*T*log({comp['params']['K']['symbol']}*{comp['state_vars']['q_0']['symbol']})",
            f"ode({comp['state_vars']['q_0']['symbol']},t) = {comp['vars']['f_0']['symbol']}"]
            # Get all in flows
            in_flows_=comp['ports']['0']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            # Get all out flows
            out_flows_=comp['ports']['0']['out']
            out_flows_vars=get_flow_outputs(out_flows_)
            if len(out_flows_vars)>0:              
                comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {'+'.join(in_flows_vars)} - {'+'.join(out_flows_vars)}",
                ]
            else:
                comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {'+'.join(in_flows_vars)}",
                ]
        elif comp['type']=='Re':
            comp['constitutive_relations']=[
            f"{comp['vars']['f_0']['symbol']} = {comp['params']['kappa']['symbol']}*(exp({comp['vars']['e_0']['symbol']}/(R*T)) - exp({comp['vars']['e_1']['symbol']}/(R*T)))"
          ]
             # Get all in effors
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            # Get all out effors
            out_efforts_=comp['ports']['0']['out']
            if '1' in comp['ports'].keys():
                out_efforts_=comp['ports']['1']['out']
            out_efforts_vars=get_efforts_outputs(out_efforts_)              
            comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {'+'.join(in_efforts_vars)}",
                f"{comp['vars']['e_1']['symbol']} = {'+'.join(out_efforts_vars)}",
            ]
        elif comp['type']=='C':
            comp['constitutive_relations']=[
            f" {comp['vars']['e_0']['symbol']}={comp['state_vars']['q_0']['symbol']}/{comp['params']['C']['symbol']}",
            f"ode({comp['state_vars']['q_0']['symbol']},t) = {comp['vars']['f_0']['symbol']}"
          ]
             # Get all in flows
            in_flows_=comp['ports']['0']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            # Get all out flows
            out_flows_=comp['ports']['0']['out']
            out_flows_vars=get_flow_outputs(out_flows_)
            if len(out_flows_vars)>0:              
                comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {'+'.join(in_flows_vars)} - {'+'.join(out_flows_vars)}",
                ]              
            else:
                comp['conservation_relations']=[
                f"{comp['vars']['f_0']['symbol']} = {'+'.join(in_flows_vars)}",
                ]
            
        elif comp['type']=='R':
            comp['constitutive_relations']=[
                f"{comp['vars']['f_0']['symbol']}={comp['vars']['e_0']['symbol']}/{comp['params']['r']['symbol']}",
            ]
            # Get all in effors
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            # Get all out effors
            out_efforts_=comp['ports']['0']['out']
            out_efforts_vars=get_efforts_outputs(out_efforts_)
            if len(out_efforts_vars)>0:              
                comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {'+'.join(in_efforts_vars)}-{'+'.join(out_efforts_vars)}",
                ]
            else:
                comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {'+'.join(in_efforts_vars)}",
                ]
        elif comp['type']=='Se':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_0']['symbol']}={comp['params']['e']['symbol']}"
            ]
        elif comp['type']=='Sf':
            comp['constitutive_relations']=[
                f"{comp['vars']['f_0']['symbol']}={comp['params']['f']['symbol']}"
            ]
        elif comp['type']=='TF':
            comp['constitutive_relations']=[
                f"{comp['vars']['e_1']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['e_0']['symbol']}",
                f"{comp['vars']['f_0']['symbol']}={comp['params']['r']['symbol']}*{comp['vars']['f_1']['symbol']}"
            ]
            # Get all in flows
            in_flows_=comp['ports']['0']['in']
            in_flows_vars=get_flow_outputs(in_flows_)
            # Get all out flows
            out_flows_=comp['ports']['0']['out']
            out_flows_vars=get_flow_outputs(out_flows_)              
            comp['conservation_relations']=[
                f"{comp['vars']['f_1']['symbol']} = {'+'.join(in_flows_vars)} - {'+'.join(out_flows_vars)}",
            ]
            # Get all in effors
            in_efforts_=comp['ports']['0']['in']
            in_efforts_vars=get_efforts_outputs(in_efforts_)
            # Get all out effors
            out_efforts_=comp['ports']['0']['out']
            out_efforts_vars=get_efforts_outputs(out_efforts_)
            if len(out_efforts_vars)>0:              
                comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {'+'.join(in_efforts_vars)}-{'+'.join(out_efforts_vars)}",
                ]
            else:
                comp['conservation_relations']=[
                f"{comp['vars']['e_0']['symbol']} = {'+'.join(in_efforts_vars)},"
                ]
            if len(out_flows_vars)>0:
                comp['conservation_relations']+=[
                f"{comp['vars']['f_1']['symbol']} = {'+'.join(in_flows_vars)} - {'+'.join(out_flows_vars)}",
            ]
            else:
                comp['conservation_relations']+=[
                f"{comp['vars']['f_1']['symbol']} = {'+'.join(in_flows_vars)}",
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
    fmatrix='./tests/SLCT4_f.csv'
    rmatrix='./tests/SLCT4_r.csv'
    comp_dict=buildBG(fmatrix,rmatrix) 
    cellml_code=to_cellmlV1_params(comp_dict) 
    print(cellml_code)
    cellml_code=to_cellmlV1_models(comp_dict)
    print(cellml_code)

        

        
