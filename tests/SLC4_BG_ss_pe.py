import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import create_dict_sedDocment, add_peTask2dict, write_sedml,validate_sedml
from src.sedEditor import create_sedDocment

# write a function to make test_task_pe() concise please
  

def test_task_pe():  
    dict_sedDocument=create_dict_sedDocment()
    model_names=['SLCT4_BG_ss_test']  
    model_sources=['SLCT4_BG_ss_test.cellml']
    #

    dict_algorithmParameter_opt={'kisaoID':'KISAO:0000597','name':'tol','value':'1e-6'}
    dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
   # dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}
    dict_algorithm_opt={'kisaoID':'KISAO:0000472','name':'global optimization algorithm', 'listOfAlgorithmParameters':[]}
    
    dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
    dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[]}

    changes={}

    data_source_file1='data_SLC4_BG_ss_EXPA.csv'
    fileId1='EXPA'
    data_summary_1='experiment A'

    data_source_file2='data_SLC4_BG_ss_EXPB.csv'
    fileId2='EXPB'
    data_summary_2='experiment B'

    data_source_file3='data_SLC4_BG_ss_EXPC.csv'
    fileId3='EXPC'
    data_summary_3='experiment C'

    data_source_file4='data_SLC4_BG_ss_EXPD.csv'
    fileId4='EXPD'
    data_summary_4='experiment D'

    data_source_file5='data_SLC4_BG_ss_EXPE.csv'
    fileId5='EXPE'
    data_summary_5='experiment E'

    data_source_file6='data_SLC4_BG_ss_EXPF.csv'
    fileId6='EXPF'
    data_summary_6='experiment F'

    # time
    # format: [dataSourceId,column_name,startIndex,endIndex,component,name]
    dataSourceId_0='time'
    time={dataSourceId_0:{'column_name':'t','startIndex':None,'endIndex':None,'component':'SLCT4_BG_ss_test','name':'time'}} 
 
    # observables
    # format: [dataSourceId,column_name,startIndex,endIndex,component,name,weight]
    dataSourceId_1='v_ss'
    obs1=[dataSourceId_1,'vss',None,None,'SLCT4_BG_ss_io','v_ss',1]
    observables=[obs1]
    # experimentalConditions
    # format: [dataSourceId,column_name,startIndex,endIndex,index_value,component,name]
    dataSourceId_2='q_Ai'
    exp1=[dataSourceId_2,'q_Ai',None,None,None,'SLCT4_BG_ss_io','q_Ai']
    dataSourceId_3='q_Ao'
    exp2=[dataSourceId_3,'q_Ao',None,None,None,'SLCT4_BG_ss_io','q_Ao']
    dataSourceId_4='q_Bi'
    exp3=[dataSourceId_4,'q_Bi',None,None,None,'SLCT4_BG_ss_io','q_Bi']
    dataSourceId_5='q_Bo'
    exp4=[dataSourceId_5,'q_Bo',None,None,None,'SLCT4_BG_ss_io','q_Bo']
    exps=[exp1,exp2,exp3,exp4]

    # fitExperiments
    # format: [fitId, type, model_variance, algorithm, experimentalConditions, observables,time]
    fitId_1='fit1'
    model_variance_name='SLCT4_BG_ss_test_A'
    model_variance_source='SLCT4_BG_ss_test_A.cellml'
    model_names.append(model_variance_name)
    model_sources.append(model_variance_source)
    fit1=[fitId_1,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId1,dataSourceId_2),(fileId1,dataSourceId_3),(fileId1,dataSourceId_4),(fileId1,dataSourceId_5)],[(fileId1,dataSourceId_1,'abs')],(fileId1,dataSourceId_0)]
    fitId_2='fit2'
    fit2=[fitId_2,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId2,dataSourceId_2),(fileId2,dataSourceId_3),(fileId2,dataSourceId_4),(fileId2,dataSourceId_5)],[(fileId2,dataSourceId_1,'abs')],(fileId2,dataSourceId_0)]
    fitId_4='fit4'
    fit4=[fitId_4,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId4,dataSourceId_2),(fileId4,dataSourceId_3),(fileId4,dataSourceId_4),(fileId4,dataSourceId_5)],[(fileId4,dataSourceId_1,'abs')],(fileId4,dataSourceId_0)]
    fitId_5='fit5'
    fit5=[fitId_5,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId5,dataSourceId_2),(fileId5,dataSourceId_3),(fileId5,dataSourceId_4),(fileId5,dataSourceId_5)],[(fileId5,dataSourceId_1,'abs')],(fileId5,dataSourceId_0)]

    fitId_3='fit3'
    model_variance_name='SLCT4_BG_ss_test_B'
    model_variance_source='SLCT4_BG_ss_test_B.cellml'
    model_names.append(model_variance_name)
    model_sources.append(model_variance_source)
    fit3=[fitId_3,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId3,dataSourceId_2),(fileId3,dataSourceId_3),(fileId3,dataSourceId_4),(fileId3,dataSourceId_5)],[(fileId3,dataSourceId_1,'abs')],(fileId3,dataSourceId_0)]
    fitId_6='fit6'
    fit6=[fitId_6,'timeCourse', model_variance_name,  dict_algorithm_sim,[(fileId6,dataSourceId_2),(fileId6,dataSourceId_3),(fileId6,dataSourceId_4),(fileId6,dataSourceId_5)],[(fileId6,dataSourceId_1,'abs')],(fileId6,dataSourceId_0)]

    # adjustableParameters
    # format: [parameterId, component, name, lowerBound, upperBound, initialValue, scale, experimentReferences]
    #experimentReferences: list of fitId
    parameterId_1='K_Ai'
    adjustable1=[parameterId_1,'SLCT4_BG_param','K_Ai',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_4,fitId_5]]
    parameterId_2='K_Bi'
    adjustable2=[parameterId_2,'SLCT4_BG_param','K_Bi',0.0001,1e12,0.1,'linear',[fitId_3,fitId_6]]
    parameterId_3='K_5'
    adjustable3=[parameterId_3,'SLCT4_BG_param','K_5',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4,fitId_5,fitId_6]]
    parameterId_4='K_6'
    adjustable4=[parameterId_4,'SLCT4_BG_param','K_6',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_3,fitId_4,fitId_5,fitId_6]]
    parameterId_5='K_7'
    adjustable5=[parameterId_5,'SLCT4_BG_param','K_7',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_4,fitId_5]]
    parameterId_6='K_8'
    adjustable6=[parameterId_6,'SLCT4_BG_param','K_8',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_4,fitId_5]]
    parameterId_7='K_9'
    adjustable7=[parameterId_7,'SLCT4_BG_param','K_9',0.0001,1e12,0.1,'linear',[fitId_3,fitId_6]]
    parameterId_8='K_10'
    adjustable8=[parameterId_8,'SLCT4_BG_param','K_10',0.0001,1e12,0.1,'linear',[fitId_3,fitId_6]]
    parameterId_13='kappa_re5'
    adjustable13=[parameterId_13,'SLCT4_BG_param','kappa_re5',0.0001,1e12,0.1,'linear',[fitId_3,fitId_6]]
    parameterId_14='kappa_re6'
    adjustable14=[parameterId_14,'SLCT4_BG_param','kappa_re6',0.0001,1e12,0.1,'linear',[fitId_1,fitId_2,fitId_4,fitId_5]]
    

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
    for exp in exps:
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
            'time':time,                                                                                         
        },
        fileId2:{
            'data_summary':data_summary_2,
            'data_file':data_source_file2,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,
            'time':time,                                                                                         
        },
        fileId3:{
            'data_summary':data_summary_3,
            'data_file':data_source_file3,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,
            'time':time,                                                                                         
        },
        fileId4:{
            'data_summary':data_summary_4,
            'data_file':data_source_file4,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,
            'time':time,                                                                                         
        },
        fileId5:{
            'data_summary':data_summary_5,
            'data_file':data_source_file5,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,
            'time':time,                                                                                         
        },
        fileId6:{
            'data_summary':data_summary_6,
            'data_file':data_source_file6,
            'observables':dict_obs,
            'experimentalConditions':dict_exp,
            'time':time,                                                                                         
        }

    }  

    fitExperiments={}

    for fit in [fit1,fit2,fit3,fit4,fit5,fit6]:
        fitId=fit[0]
        type=fit[1]
        model_variance=fit[2]
        algorithm=fit[3]
        experimentalConditions=fit[4]
        observables=fit[5]
        if len(fit)==7:
            time=fit[6]
            fitExperiments[fitId]={'type':type,'algorithm':algorithm,'experimentalConditions':experimentalConditions,'observables':observables,'time':time}
        else:
            fitExperiments[fitId]={'type':type,'algorithm':algorithm,'experimentalConditions':experimentalConditions,'observables':observables}
        if model_variance!='':
            fitExperiments[fitId]['name']=model_variance
    
    adjustableParameters={}
    for adjustable in [adjustable1,adjustable2,adjustable3,adjustable4,adjustable5,adjustable6,adjustable7,adjustable8,adjustable13,adjustable14]:
        parameterId=adjustable[0]
        component=adjustable[1]
        name=adjustable[2]
        lowerBound=adjustable[3]
        upperBound=adjustable[4]
        initialValue=adjustable[5]
        scale=adjustable[6]
        experimentReferences=adjustable[7]
        adjustableParameters[parameterId]={'component':component,'name':name,'lowerBound':lowerBound,'upperBound':upperBound,'initialValue':initialValue,'scale':scale,'experimentReferences':experimentReferences}
                
    add_peTask2dict(dict_sedDocument, model_names, model_sources,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )
    try:
        doc=create_sedDocment(dict_sedDocument)
    except ValueError as err:
        print(err)
    filename='./csv/SLCT4_BG_ss_test_pe_time_global.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))

test_task_pe()