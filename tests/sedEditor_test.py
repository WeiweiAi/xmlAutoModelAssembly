import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedEditor import create_sedDocment_user_task,create_sedDocment_user_task_pe, write_sedml,validate_sedml,get_dict_sedDocument,target_component_variable,target_component_variable_initial

def test_task():
    model_source='SLCT3_BG_test.cellml'
    changes={'id':{'component':'SLCT3_BG_io','name':'q_Ai','newValue':'200'}}
    outputs={'v_Ai':{'component':'SLCT3_BG_test','name':'v_Ai','scale':1.0},
            't':{'component':'SLCT3_BG','name':'t'}
            }
    dict_algorithmParameter={'kisaoID':'KISAO:0000467', 'name':'max_step','value':'0.001'}
    dict_algorithm={'kisaoID':'KISAO:0000535','name':'VODE','listOfAlgorithmParameters':[dict_algorithmParameter]}
    simSetting={'type':'UniformTimeCourse','algorithm':dict_algorithm,'initialTime':0,'outputStartTime':2.3,'outputEndTime':1000,'numberOfSteps':1000}
   # simSetting={'type':'OneStep','algorithm':dict_algorithm,'step':0.1}
   # simSetting={'type':'SteadyState','algorithm':dict_algorithm}
    
    doc=create_sedDocment_user_task(model_source,changes,simSetting,outputs)
    filename='./csv/SLCT3_BG_test.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))
   

def test_task_pe():    
    model_source='SLCT3_BG_test.cellml'
    #
    component_change='SLCT3_BG_io'
    variable_change='q_Ao'
    initial_value='200' # must be string
    changes={'id':{'component':component_change,'name':variable_change,'newValue':initial_value}}

    data_source_file1='data_series.csv'
    fileId1='file1'
    data_summary_1='time series'
    # time 
    dataSourceId_1='t'
    column_name_1='t'
    startIndex_1=None
    endIndex_1=None
    component_1='SLCT3_BG'
    name_1='t'
    
    # pointWeights
    dataSourceId_2='pointWeight_v_Ao'
    column_name_2='pointWeight_v_Ao'
    startIndex_2=None
    endIndex_2=None

    # observables
    dataSourceId_4='v_Ao'
    column_name_4='v_Ao'
    startIndex_4=None
    endIndex_4=None
    component_4='SLCT3_BG_test'
    name_4='v_Ao'
    weight_4=dataSourceId_2

    dataSourceId_3='v_Ai'
    column_name_3='v_Ai'
    startIndex_3=None
    endIndex_3=None
    component_3='SLCT3_BG_test'
    name_3='v_Ai'
    weight_3=1 # must be float


    data_source_file2='data_points.csv'
    fileId2='file2'
    data_summary_2='data points'

    # experimentalConditions
    dataSourceId_5='q_Ao_init'
    column_name_5='q_Ao_init'
    startIndex_5=None
    endIndex_5=None
    index_value_5='0' # must be string
    component_5='SLCT3_BG_io'
    name_5='q_Ao'

    dict_algorithmParameter_opt={'kisaoID':'KISAO:0000211','name':'xatol','value':'1e-8'}
    dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
    dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}
    
     
    experimentData_files={fileId1:{'data_summary':data_summary_1,'data_file':data_source_file1,
                                   'time':{dataSourceId_1:{'column_name':column_name_1,'startIndex':startIndex_1,'endIndex':endIndex_1,'component':component_1,'name':name_1}
                                           },
                                   'observables':{dataSourceId_4:{'column_name':column_name_4,'startIndex':startIndex_4,'endIndex':endIndex_4,'component':component_4,'name':name_4, 'weight':weight_4},
                                                  dataSourceId_3:{'column_name':column_name_3,'startIndex':startIndex_3,'endIndex':endIndex_3,'component':component_3,'name':name_3, 'weight':weight_3}
                                                  },
                                   'pointWeights':{dataSourceId_2:{'column_name':column_name_2,'startIndex':startIndex_2,'endIndex':endIndex_2}                                                   
                                                   }
                                   },
                          fileId2:{'data_summary':data_summary_2,'data_file':data_source_file2,
                                   'experimentalConditions':{dataSourceId_5:{'column_name':column_name_5,'startIndex':startIndex_5,'endIndex':endIndex_5, 'index_value':index_value_5,'component':component_5,'name':name_5}
                                                             },                                   
                                   }                          
                        }
    fitId='fit1'
    dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
    dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[dict_algorithm_sim_parameter]}
    fitExperiments={fitId: {'type':'timeCourse','algorithm':dict_algorithm_sim, 
                            'time':(fileId1,dataSourceId_1),
                            'experimentalConditions':[(fileId2,dataSourceId_5)],
                            'observables':[(fileId1,dataSourceId_3),(fileId1,dataSourceId_4)]
                            }
                    } 

    adjustableParameters={'parameter1':{'component':'SLCT3_BG_param','name':'kappa_re1','lowerBound':0.0,'upperBound':10.0,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId]},
                          'parameter2':{'component':'SLCT3_BG_param','name':'kappa_re2','lowerBound':0.0,'upperBound':10.0,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId]}
                          }         

    doc=create_sedDocment_user_task_pe(model_source,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )
    filename='./csv/test_pe.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))

test_task_pe()