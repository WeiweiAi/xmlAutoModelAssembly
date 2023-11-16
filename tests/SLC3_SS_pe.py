import sys
    # caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(0, '..')
from src.sedDocEditor import create_dict_sedDocment, add_peTask2dict, write_sedml,validate_sedml
from src.sedEditor import create_sedDocment
  

def test_task_pe():  
    dict_sedDocument=create_dict_sedDocment()
    model_name='SLCT3_ss_test'  
    model_source='SLCT3_ss_test.cellml'
    #
    changes={}

    data_source_file1='data_points.csv'
    fileId1='file1'
    data_summary_1='experimental data'
       
    # observables
    dataSourceId_1='v_ss_io_1'
    column_name_1='vss'
    startIndex_1=0
    endIndex_1=0
    component_1='SLCT3_ss_test'
    name_1='v_ss'
    weight_1=1

    dataSourceId_2='v_ss_io_2'
    column_name_2='vss'
    startIndex_2=1
    endIndex_2=1
    component_2='SLCT3_ss_test'
    name_2='v_ss'
    weight_2=1

    dataSourceId_3='v_ss_oi_1'
    column_name_3='vss'
    startIndex_3=2
    endIndex_3=2
    component_3='SLCT3_ss_test'
    name_3='v_ss'
    weight_3=1

    dataSourceId_4='v_ss_oi_2'
    column_name_4='vss'
    startIndex_4=3
    endIndex_4=3
    component_4='SLCT3_ss_test'
    name_4='v_ss'
    weight_4=1

    # experimentalConditions
    dataSourceId_5='q_Ao_init_0'
    column_name_5='q_Ao_init'
    startIndex_5=None
    endIndex_5=None
    index_value_5='0' # must be string
    component_5='SLCT3_ss_test'
    name_5='q_Ao'

    dataSourceId_6='q_Ai_init_0'
    column_name_6='q_Ai_init'
    startIndex_6=None
    endIndex_6=None
    index_value_6='3' # must be string
    component_6='SLCT3_ss_test'
    name_6='q_Ai'

    dataSourceId_7='q_Ao_init_1'
    column_name_7='q_Ao_init'
    startIndex_7=None
    endIndex_7=None
    index_value_7='2' # must be string
    component_7='SLCT3_ss_test'
    name_7='q_Ao'

    dataSourceId_8='q_Ao_init_2'
    column_name_8='q_Ao_init'
    startIndex_8=None
    endIndex_8=None
    index_value_8='3' # must be string
    component_8='SLCT3_ss_test'
    name_8='q_Ao'

    dataSourceId_9='q_Ai_init_1'
    column_name_9='q_Ai_init'
    startIndex_9=None
    endIndex_9=None
    index_value_9='0' # must be string
    component_9='SLCT3_ss_test'
    name_9='q_Ai'

    dataSourceId_10='q_Ai_init_2'
    column_name_10='q_Ai_init'
    startIndex_10=None
    endIndex_10=None
    index_value_10='1' # must be string
    component_10='SLCT3_ss_test'
    name_10='q_Ai'

    dict_algorithmParameter_opt={'kisaoID':'KISAO:0000597','name':'tol','value':'1e-6'}
    dict_algorithmParameter_opt2={'kisaoID':'KISAO:0000486','name':'maxiter','value':'1e4'}
    dict_algorithm_opt={'kisaoID':'KISAO:0000514','name':'Nelder-Mead', 'listOfAlgorithmParameters':[dict_algorithmParameter_opt,dict_algorithmParameter_opt2]}
    
     
    experimentData_files={fileId1:{
        'data_summary':data_summary_1,'data_file':data_source_file1,

        'observables':{
        dataSourceId_1:{'column_name':column_name_1,'startIndex':startIndex_1,'endIndex':endIndex_1,'component':component_1,'name':name_1, 'weight':weight_1},
        dataSourceId_2:{'column_name':column_name_2,'startIndex':startIndex_2,'endIndex':endIndex_2,'component':component_2,'name':name_2, 'weight':weight_2},
        dataSourceId_4:{'column_name':column_name_4,'startIndex':startIndex_4,'endIndex':endIndex_4,'component':component_4,'name':name_4, 'weight':weight_4},
        dataSourceId_3:{'column_name':column_name_3,'startIndex':startIndex_3,'endIndex':endIndex_3,'component':component_3,'name':name_3, 'weight':weight_3},
                                },
        'experimentalConditions':{
        dataSourceId_5:{'column_name':column_name_5,'startIndex':startIndex_5,'endIndex':endIndex_5, 'index_value':index_value_5,'component':component_5,  'name':name_5},
        dataSourceId_6:{'column_name':column_name_6,'startIndex':startIndex_6,'endIndex':endIndex_6, 'index_value':index_value_6,'component':component_6,'name':name_6},
        dataSourceId_7:{'column_name':column_name_7,'startIndex':startIndex_7,'endIndex':endIndex_7, 'index_value':index_value_7,'component':component_7,'name':name_7},
        dataSourceId_8:{'column_name':column_name_8,'startIndex':startIndex_8,'endIndex':endIndex_8, 'index_value':index_value_8,'component':component_8,'name':name_8},
        dataSourceId_9:{'column_name':column_name_9,'startIndex':startIndex_9,'endIndex':endIndex_9, 'index_value':index_value_9,'component':component_9,'name':name_9},
        dataSourceId_10:{'column_name':column_name_10,'startIndex':startIndex_10,'endIndex':endIndex_10, 'index_value':index_value_10,'component':component_10,'name':name_10}
                                   },                                                                                         
                                   } 
                            }                         
    fitId_1='fit1'
    fitId_2='fit2'
    fitId_3='fit3'
    fitId_4='fit4'

    dict_algorithm_sim_parameter={'kisaoID':'KISAO:0000467','name':'max_step','value':'0.001'}
    dict_algorithm_sim={'kisaoID':'KISAO:0000535','name':'VODE', 'listOfAlgorithmParameters':[]}
    fitExperiments={fitId_1: {'type':'steadyState','algorithm':dict_algorithm_sim, 
                            'experimentalConditions':[(fileId1,dataSourceId_5),(fileId1,dataSourceId_9)],
                            'observables':[(fileId1,dataSourceId_1)]
                            },
                    fitId_2: {'type':'steadyState','algorithm':dict_algorithm_sim,
                            'experimentalConditions':[(fileId1,dataSourceId_5),(fileId1,dataSourceId_10)],
                            'observables':[(fileId1,dataSourceId_2)]
                            },
                    fitId_3: {'type':'steadyState','algorithm':dict_algorithm_sim,
                            'experimentalConditions':[(fileId1,dataSourceId_6),(fileId1,dataSourceId_7)],
                            'observables':[(fileId1,dataSourceId_3)]
                            },
                    fitId_4: {'type':'steadyState','algorithm':dict_algorithm_sim,
                            'experimentalConditions':[(fileId1,dataSourceId_6),(fileId1,dataSourceId_8)],
                            'observables':[(fileId1,dataSourceId_4)]
                            }
                    } 

    adjustableParameters={'parameter1':{'component':'SLCT3_ss','name':'P_0','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},
                          'parameter2':{'component':'SLCT3_ss','name':'P_1','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},
                          'parameter3':{'component':'SLCT3_ss','name':'P_2','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},
                          'parameter4':{'component':'SLCT3_ss','name':'P_3','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},
                          'parameter5':{'component':'SLCT3_ss','name':'P_4','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},
                          'parameter6':{'component':'SLCT3_ss','name':'P_5','lowerBound':0.0001,'upperBound':100000,'initialValue':0.1,'scale':'linear','experimentReferences':[fitId_1,fitId_2,fitId_3,fitId_4]},                                                                     
                        }         

    add_peTask2dict(dict_sedDocument, model_name, model_source,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt )
    try:
        doc=create_sedDocment(dict_sedDocument)
    except ValueError as err:
        print(err)
    filename='./csv/SLC3_SS_pe.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))

test_task_pe()