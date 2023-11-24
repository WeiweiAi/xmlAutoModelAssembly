import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import create_dict_sedDocment, add_peTask2dict, write_sedml,validate_sedml
from src.sedEditor import create_sedDocment

# write a function to make test_task_pe() concise please
  

def test_task_pe():  
    dict_sedDocument=create_dict_sedDocment()
    model_name='SLCT3_ss_test'  
    model_source='SLCT3_ss_test.cellml'
    #

    dict_algorithmParameter_opt={'kisaoID':'KISAO:0000597','name':'tol','value':'1e-6'}
    dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
    dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}
    
    dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
    dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[]}

    changes={}

    data_source_file1='data_points.csv'
    fileId1='file1'
    data_summary_1='experimental data'
       
    # observables
    # format: [dataSourceId,column_name,startIndex,endIndex,component,name,weight]
    dataSourceId_1='v_ss_io_1'
    obs1=[dataSourceId_1,'vss',0,0,'SLCT3_ss_test','v_ss',1]
    dataSourceId_2='v_ss_io_2'
    obs2=[dataSourceId_2,'vss',1,1,'SLCT3_ss_test','v_ss',1]
    dataSourceId_3='v_ss_oi_1'
    obs3=[dataSourceId_3,'vss',2,2,'SLCT3_ss_test','v_ss',1]
    dataSourceId_4='v_ss_oi_2'
    obs4=[dataSourceId_4,'vss',3,3,'SLCT3_ss_test','v_ss',1]
    observables=[obs1,obs2,obs3,obs4]
    # experimentalConditions
    # format: [dataSourceId,column_name,startIndex,endIndex,index_value,component,name]
    dataSourceId_5='q_Ao_init_0'
    exp1=[dataSourceId_5,'q_Ao_init',None,None,'0','SLCT3_ss_test','q_Ao']
    dataSourceId_6='q_Ao_init_1'
    exp2=[dataSourceId_6,'q_Ao_init',None,None,'1','SLCT3_ss_test','q_Ao']
    dataSourceId_7='q_Ao_init_2'
    exp3=[dataSourceId_7,'q_Ao_init',None,None,'2','SLCT3_ss_test','q_Ao']
    dataSourceId_8='q_Ai_init_0'
    exp4=[dataSourceId_8,'q_Ai_init',None,None,'0','SLCT3_ss_test','q_Ai']
    dataSourceId_9='q_Ai_init_1'
    exp5=[dataSourceId_9,'q_Ai_init',None,None,'1','SLCT3_ss_test','q_Ai']
    dataSourceId_10='q_Ai_init_2'
    exp6=[dataSourceId_10,'q_Ai_init',None,None,'2','SLCT3_ss_test','q_Ai']

    # fitExperiments
    # format: [fitId, type, algorithm, experimentalConditions, observables]
    fitId_1='fit1'
    fit1=[fitId_1,'steadyState',dict_algorithm_sim,[(fileId1,dataSourceId_5),(fileId1,dataSourceId_9)],[(fileId1,dataSourceId_1)]]
    fitId_2='fit2'
    fit2=[fitId_2,'steadyState',dict_algorithm_sim,[(fileId1,dataSourceId_5),(fileId1,dataSourceId_10)],[(fileId1,dataSourceId_2)]]
    fitId_3='fit3'
    fit3=[fitId_3,'steadyState',dict_algorithm_sim,[(fileId1,dataSourceId_6),(fileId1,dataSourceId_7)],[(fileId1,dataSourceId_3)]]
    fitId_4='fit4'
    fit4=[fitId_4,'steadyState',dict_algorithm_sim,[(fileId1,dataSourceId_6),(fileId1,dataSourceId_8)],[(fileId1,dataSourceId_4)]]

    # adjustableParameters
    # format: [parameterId, component, name, lowerBound, upperBound, initialValue, scale, experimentReferences]
    #experimentReferences: list of fitId
    parameterId_1='P_0'
    adjustable1=[parameterId_1,'SLCT3_ss_test','P_0',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]
    parameterId_2='P_1'
    adjustable2=[parameterId_2,'SLCT3_ss_test','P_1',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]
    parameterId_3='P_2'
    adjustable3=[parameterId_3,'SLCT3_ss_test','P_2',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]
    parameterId_4='P_3'
    adjustable4=[parameterId_4,'SLCT3_ss_test','P_3',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]
    parameterId_5='P_4'
    adjustable5=[parameterId_5,'SLCT3_ss_test','P_4',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]
    parameterId_6='P_5'
    adjustable6=[parameterId_6,'SLCT3_ss_test','P_5',0.0001,100000,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4]]


    dict_obs={}
    for obs in observables:
        dataSourceId=obs[0]
        column_name=obs[1]
        startIndex=obs[2]
        endIndex=obs[3]
        component=obs[4]
        name=obs[5]
        weight=obs[6]
        dict_obs[dataSourceId]={'column_name':column_name,'startIndex':startIndex,'endIndex':endIndex,'component':component,'name':name, 'weight':weight}

    dict_exp={}
    for exp in [exp1,exp2,exp3,exp4,exp5,exp6]:
        dataSourceId=exp[0]
        column_name=exp[1]
        startIndex=exp[2]
        endIndex=exp[3]
        index_value=exp[4]
        component=exp[5]
        name=exp[6]
        dict_exp[dataSourceId]={'column_name':column_name,'startIndex':startIndex,'endIndex':endIndex,'index_value':index_value,'component':component,'name':name}
  
    experimentData_files={
        fileId1:{
            'data_summary':data_summary_1,
            'data_file':data_source_file1,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,                                                                                         
        }   
    }  

    fitExperiments={}

    for fit in [fit1,fit2,fit3,fit4]:
        fitId=fit[0]
        type=fit[1]
        algorithm=fit[2]
        experimentalConditions=fit[3]
        observables=fit[4]
        fitExperiments[fitId]={'type':type,'algorithm':algorithm,'experimentalConditions':experimentalConditions,'observables':observables}
    
    adjustableParameters={}
    for adjustable in [adjustable1,adjustable2,adjustable3,adjustable4,adjustable5,adjustable6]:
        parameterId=adjustable[0]
        component=adjustable[1]
        name=adjustable[2]
        lowerBound=adjustable[3]
        upperBound=adjustable[4]
        initialValue=adjustable[5]
        scale=adjustable[6]
        experimentReferences=adjustable[7]
        adjustableParameters[parameterId]={'component':component,'name':name,'lowerBound':lowerBound,'upperBound':upperBound,'initialValue':initialValue,'scale':scale,'experimentReferences':experimentReferences}
                
    add_peTask2dict(dict_sedDocument, model_name, model_source,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )
    try:
        doc=create_sedDocment(dict_sedDocument)
    except ValueError as err:
        print(err)
    filename='./csv/SLC3_SS_pe.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))

test_task_pe()