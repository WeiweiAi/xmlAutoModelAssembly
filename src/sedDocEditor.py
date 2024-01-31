from .sedEditor import get_dict_sedDocument
import libsedml
from libsedml import writeSedMLToFile, readSedMLFromFile
import os

"""
This module provides functions to create a SED-ML document with user-defined information.
The model is assumed to be a CellML model.

"""	

CELLML_URN = 'urn:sedml:language:cellml'

def target_component_variable(component, variable):
    """
    Create a target for a variable in a CellML model.

    Parameters
    ----------
    component: str
        The name of the component containing the variable.
    variable: str
        The name of the variable.

    Returns
    -------
    str
        XPath to the variable in the CellML model.
    """
    return "/cellml:model/cellml:component[@name=&quot;{component}&quot;]/cellml:variable[@name=&quot;{variable}&quot;]".format(component=component, variable=variable)

def target_component_variable_initial(component, variable):
    """
    Create a target for a variable in a CellML model.

    Parameters
    ----------
    component: str
        The name of the component containing the variable.
    variable: str
        The name of the variable.

    Returns
    -------
    str
        XPath to the variable initial_value in the CellML model.
    """
    return "/cellml:model/cellml:component[@name=&quot;{component}&quot;]/cellml:variable[@name=&quot;{variable}&quot;]/@initial_value".format(component=component, variable=variable)
def write_sedml(doc,file_name):
    """
    Write the SED-ML document to a file
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    file_name: str
        The full path of the file

    Side effects
    ------------
    A SED-ML file is created.

    """
    writeSedMLToFile(doc,file_name)

def read_sedml(file_name):
    """
    Read the SED-ML document from a file
    
    Parameters
    ----------
    file_name: str
        The full path of the file

    Raises
    ------
    FileNotFoundError
        If the file is not found.

    Returns
    -------
    SedDocument
        An instance of SedDocument.
    """

    if not os.path.exists(file_name):
        raise FileNotFoundError('The file {0} is not found.'.format(file_name))
    doc = readSedMLFromFile(file_name)
    return doc

def validate_sedml(file_name):
    """
    Validate the SED-ML document from a file

    Parameters
    ----------
    file_name: str
        The full path of the file
    
    Raises
    ------
    FileNotFoundError
        If the file is not found.
    ValueError
        If the SED-ML document is not valid (more strict than libsedml).

    Returns
    -------
    int
        The number of errors.
    """
    try:
        doc = read_sedml(file_name)
    except FileNotFoundError as e:
        raise e
    num_errors = doc.getNumErrors(libsedml.LIBSEDML_SEV_ERROR)
    num_warnings = doc.getNumErrors(libsedml.LIBSEDML_SEV_WARNING)

    print ('file: {0} has {1} warning(s) and {2} error(s)'
        .format(file_name, num_warnings, num_errors))

    log = doc.getErrorLog()
    for i in range(log.getNumErrors()):
        err = log.getError(i)
        print('{0} L{1} C{2}: {3}'.format(err.getSeverityAsString(), err.getLine(), err.getColumn(), err.getMessage()))
    try:
        dict_doc = get_dict_sedDocument(doc)
    except ValueError as e:
        raise e

    if dict_doc and num_errors == 0:
        return True
    else:
        return False 

def create_dict_sedDocment():
    """
    Create an empty SED-ML document dictionary.

    Returns
    -------
    dict
        The dictionary format:
        {'listOfDataDescriptions':[],'listOfModels':[],'listOfSimulations':[],'listOfTasks':[],'listOfDataGenerators':[],'listOfReports':[]}
    """

    dict_sedDocument={'listOfDataDescriptions':[],'listOfModels':[],'listOfSimulations':[],'listOfTasks':[],'listOfDataGenerators':[],'listOfReports':[]}
    
    return dict_sedDocument


def add_sedTask2dict(dict_sedDocument, model_name, model_source,changes,simSetting,outputs):
    """
    Add user-defined task information to the SED-ML document dictionary.
    Assume single model, single simulation, single task, single report.
    The task type is 'Task'.
    The output type is 'Report'.
    The report is intended to be exported to a csv file,
    using the label as column headers.
    Each data set refers to a data generator, which contains a single variable.
    The variable can be scaled if the scale attribute is provided.
    Each variable targets a single variable in the model. 
   
    Parameters
    ----------
    dict_sedDocument: dict
        The dictionary format:
        {'listOfDataDescriptions':[],'listOfModels':[],'listOfSimulations':[],'listOfTasks':[],'listOfDataGenerators':[],'listOfReports':[]}
    model_name: str
        The id of the model.
    model_source: str
        The source of the model, e.g., '../tests/csv/test_model_noExt.cellml'
    changes: dict
        The dictionary format:
        {'id':{'component':str,'name':str,'newValue':str}}
        The id, component, name and newValue attributes of a change are required.
    simSetting: dict
        The dictionary format:
        - if 'UniformTimeCourse', {'type':'UniformTimeCourse','algorithm':dict_algorithm,'initialTime':float,'outputStartTime':float,'outputEndTime':float,'numberOfSteps':int}
        - if 'OneStep', {'type':'OneStep','algorithm':dict_algorithm,'step':float}
        - if 'SteadyState', {'type':'SteadyState','algorithm':dict_algorithm}
        dict_algorithm format: {'kisaoID':str,'name':str,'listOfAlgorithmParameters':[dict_algorithmParameter]}
        dict_algorithmParameter format: {'kisaoID':str,'name':str,'value':str}
        The kisaoID, name and value attributes of a algorithmParameter are required.

    outputs: dict
        The dictionary format:
        {'id':{'component':str,'name':str,'scale':float}}
            
    Side effects
    ------------
    The SED-ML document dictionary is updated.
    """

    # model
    dict_model={'id':model_name,'source':model_source,'language':CELLML_URN,'listOfChanges':[]}

    # changes
    for change in changes.values():
        dict_change_Attribute = {'target': target_component_variable_initial(change['component'], change['name']),'newValue': change['newValue']} 
        dict_model['listOfChanges'].append(dict_change_Attribute)
    dict_sedDocument['listOfModels'].append(dict_model)

    # simulation
    sim_id = 'sim_'+ model_name
    if simSetting['type'] == 'UniformTimeCourse':
        dict_simulation={'id':sim_id, 'type':'UniformTimeCourse', 'algorithm':simSetting['algorithm'],'initialTime':simSetting['initialTime'],
                         'outputStartTime':simSetting['outputStartTime'],'outputEndTime':simSetting['outputEndTime'],'numberOfSteps':simSetting['numberOfSteps']}
    elif simSetting['type'] == 'OneStep':
        dict_simulation={'id':sim_id, 'type':'OneStep', 'algorithm':simSetting['algorithm'],'step':simSetting['step']}
    elif simSetting['type'] == 'SteadyState':
        dict_simulation={'id':sim_id, 'type':'SteadyState', 'algorithm':simSetting['algorithm']}

    dict_sedDocument['listOfSimulations'].append(dict_simulation)
    
    # task
    task_id = 'task_'+ model_name
    dict_task={'id':task_id,'type':'Task', 'modelReference':model_name,'simulationReference':sim_id}
    dict_sedDocument['listOfTasks'].append(dict_task)

    # output
    report_id = 'report_'+ task_id
    dict_report={'id':report_id,'name':report_id,'listOfDataSets':[]}

    for id,output in outputs.items():
        var_id = model_name + '_'+ id
        dict_variable={'id':var_id,'target':target_component_variable(output['component'], output['name']),'modelReference':model_name,'taskReference':task_id}
        dataGenerator_id = 'dg_'+ var_id
        if 'scale' in output:
            dict_parameter={'id':'scale','value':output['scale']}           
            dict_dataGenerator={'id':dataGenerator_id,'name':dataGenerator_id,'math':var_id+'*scale','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
        else:
            dict_dataGenerator={'id':dataGenerator_id,'name':dataGenerator_id,'math':var_id,'listOfVariables':[dict_variable]}
        dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator)
        dataSet_id = 'dataset_'+ var_id
        dict_dataSet={'id':dataSet_id,'label':id,'dataReference':dataGenerator_id}
        dict_report['listOfDataSets'].append(dict_dataSet)

    dict_sedDocument['listOfReports'].append(dict_report)
       
    return 

def add_peTask2dict(dict_sedDocument, model_names, model_sources,changes,experimentData_files, adjustableParameters,fitExperiments,dict_algorithm_opt):
    """
    Add user-defined parameterization task information to the SED-ML document dictionary.
    Assume single model, single ParameterEstimationTask, single report.
    The task type is 'ParameterEstimationTask'.
    The output type is 'Report'.

    Parameters
    ----------
    dict_sedDocument: dict
        The dictionary format:
        {'listOfDataDescriptions':[],'listOfModels':[],'listOfSimulations':[],'listOfTasks':[],'listOfDataGenerators':[],'listOfReports':[]}
    model_name: str
        The id of the model.
    model_source: str
        The source of the model, e.g., '../tests/csv/test_model_noExt.cellml'
    changes: dict
        The dictionary format:
        {'id':{'component':str,'name':str,'newValue':str}}
        The id, component, name and newValue attributes of a change are required.

    experimentData_files: dict
        The dictionary format:
        {fileId:{'data_summary':str,'data_file':str,'time':dict,'experimentalConditions':dict,'observables':dict,'pointWeights':dict}}
        The id, data_summary and data_file attributes of a data description are required.
        The time, experimentalConditions, observables and pointWeights attributes are optional.
        The time, experimentalConditions, observables and pointWeights are dictionaries.
        time: {dataSourceId:{'column_name':str,'startIndex':int,'endIndex':int,'component':str,'name':str}}
        experimentalConditions: {dataSourceId:{'column_name':str,'startIndex':int,'endIndex':int,'index_value':str, 'component':str,'name':str}}
        observables: {dataSourceId:{'column_name':str,'startIndex':int,'endIndex':int,'component':str,'name':str,'weight':str or float}}
        pointWeights: {dataSourceId:{'column_name':str,'startIndex':int,'endIndex':int}}

    adjustableParameters: dict
        The dictionary format:
        {'id':{'component':str,'name':str,'lowerBound':float,'upperBound':float,'initialValue':float,'experimentReferences':[str]}}
        The id, component, name, lowerBound, upperBound, initialValue and experimentReferences attributes of a adjustableParameter are required.
        The experimentReferences attribute is a list of fitExperiment ids.
    
    fitExperiments: dict
        The dictionary format:
        {'id':{'type':str,'algorithm':dict,'time':(str,str),'experimentalConditions':[(str,str)],'observables':[(str,str)]}}
        The tuple format: (fileId,dataSourceId) to refer to a data source in the experimentData_files.
        The algorithm dictionary format is {'kisaoID':str,'name':str,'listOfAlgorithmParameters':[dict_algorithmParameter]}.

    dict_algorithm_opt: dict
        The dictionary format:
        {'kisaoID':str,'name':str,'listOfAlgorithmParameters':[dict_algorithmParameter]}

    Side effects
    ------------
    The SED-ML document dictionary is updated.    
    """
    # model
    for model_name,model_source in zip(model_names,model_sources):
        dict_model={'id':model_name,'source':model_source,'language':CELLML_URN,'listOfChanges':[]}
        for change in changes.values():
            dict_change_Attribute = {'target': target_component_variable_initial(change['component'], change['name']),'newValue': change['newValue']} 
            dict_model['listOfChanges'].append(dict_change_Attribute)
        dict_sedDocument['listOfModels'].append(dict_model)   
    # pe task holder
    task_id = 'pe_task_'+ model_name
    dict_parameterEstimationTask= {'id':task_id,'type':'ParameterEstimationTask','algorithm':dict_algorithm_opt,'objective':{'type':'leastSquare'},
                       'listOfAdjustableParameters':[],'listOfFitExperiments':[]}    
    # report holder
    report_id = 'report_'+ task_id
    dict_report={'id':report_id,'name':report_id,'listOfDataSets':[]}
    # adjustableParameters
    for id, adjustableParameter in adjustableParameters.items():
        dict_bounds={'lowerBound':adjustableParameter['lowerBound'],'upperBound':adjustableParameter['upperBound'],'scale':'linear'}
        dict_adjustableParameter = {'id':id,'modelReference':model_name,'target':target_component_variable_initial(adjustableParameter['component'], adjustableParameter['name']),
                                                 'initialValue':adjustableParameter['initialValue'],'bounds':dict_bounds,'listOfExperimentReferences':adjustableParameter['experimentReferences']}
        
        dict_parameterEstimationTask['listOfAdjustableParameters'].append(dict_adjustableParameter)  
    # Describe the experimental data
    # Fixed dimension description: for 2D csv, the column headers are string, the values are double
    dict_dimDescription={'id':'Index','name':'Index','indexType':'integer','dim2':{'id':'ColumnIds','name':'ColumnIds','indexType':'string','valueType':'double'}}

    for fileId, experimentData_file in experimentData_files.items():
        dict_dataDescription={'id':fileId,'name':experimentData_file['data_summary'], 'source':experimentData_file['data_file'],
                              'format':'csv','dimensionDescription':dict_dimDescription, 'listOfDataSources':[]}
        if 'time' in experimentData_file:
            for dataSourceId, time in experimentData_file['time'].items():
                idataSourceId=fileId+'_'+dataSourceId
                dict_slice_time={'reference':'ColumnIds','value':time['column_name'],'startIndex':time['startIndex'],'endIndex':time['endIndex']}
                dict_dataSource_time={'id':idataSourceId,'listOfSlices':[dict_slice_time]}
                dict_dataDescription['listOfDataSources'].append(dict_dataSource_time)
        if 'experimentalConditions' in experimentData_file:
            for dataSourceId, initial in experimentData_file['experimentalConditions'].items():
                idataSourceId=fileId+'_'+dataSourceId
                dict_slice_initial_column={'reference':'ColumnIds','value':initial['column_name'],'startIndex':initial['startIndex'],'endIndex':initial['endIndex']}
                if 'index_value' in initial:
                    if initial['index_value'] is None:                       
                        dict_dataSource_initial={'id':idataSourceId,'listOfSlices':[dict_slice_initial_column]}                   
                    else:                        
                        dict_slice_initial_index={'reference':'Index','value':initial['index_value']}                        
                        dict_dataSource_initial={'id':idataSourceId,'listOfSlices':[dict_slice_initial_index,dict_slice_initial_column]}
                else:
                    dict_dataSource_initial={'id':idataSourceId,'listOfSlices':[dict_slice_initial_column]}  

                dict_dataDescription['listOfDataSources'].append(dict_dataSource_initial)
        if 'observables' in experimentData_file:
            for dataSourceId, observe in experimentData_file['observables'].items():
                dict_slice_observe={'reference':'ColumnIds','value':observe['column_name'],'startIndex':observe['startIndex'],'endIndex':observe['endIndex']}
                idataSourceId=fileId+'_'+dataSourceId
                dict_dataSource_observe={'id':idataSourceId,'listOfSlices':[dict_slice_observe]}
                dict_dataDescription['listOfDataSources'].append(dict_dataSource_observe)     
        if 'pointWeights' in experimentData_file:
            for dataSourceId, pointWeight in experimentData_file['pointWeights'].items():
                dict_slice_pointWeight={'reference':'ColumnIds','value':pointWeight['column_name'],'startIndex':pointWeight['startIndex'],'endIndex':pointWeight['endIndex']}
                idataSourceId=fileId+'_'+dataSourceId
                dict_dataSource_pointWeight={'id':idataSourceId,'listOfSlices':[dict_slice_pointWeight]}
                dict_dataDescription['listOfDataSources'].append(dict_dataSource_pointWeight)
       
        dict_sedDocument['listOfDataDescriptions'].append(dict_dataDescription)
    # fitExperiments
    for id, fitExperiment in fitExperiments.items():
        dict_fitExperiment={'id':id, 'type':fitExperiment['type'],'algorithm':fitExperiment['algorithm'],'listOfFitMappings':[]}
        if 'name' in fitExperiment:
            dict_fitExperiment['name']=fitExperiment['name']
        if fitExperiment['type']=='timeCourse':
            fileId=fitExperiment['time'][0]
            dataSourceId=fitExperiment['time'][1]
            idataSourceId=fileId+'_'+dataSourceId
            dict_variable=experimentData_files[fileId]['time'][dataSourceId]
            var_id = 'var_'+ idataSourceId
            dict_variable_time={'id':var_id,'target':target_component_variable(dict_variable['component'], dict_variable['name']),
                                'modelReference':model_name,'taskReference':task_id}
            dataGenerator_id = 'dg_'+ idataSourceId
            dict_dataGenerator_time={'id':dataGenerator_id,'name':'dataGenerator1','math':var_id,'listOfVariables':[dict_variable_time]}
            dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator_time)

            dict_fitMapping_time= {'type':'time','dataSource':idataSourceId,'target':dataGenerator_id}
            dict_fitExperiment['listOfFitMappings'].append(dict_fitMapping_time)

        for experimentalCondition_des in fitExperiment['experimentalConditions']:
            fileId=experimentalCondition_des[0]
            dataSourceId=experimentalCondition_des[1]
            idataSourceId=fileId+'_'+dataSourceId
            if 'experimentalConditions' in experimentData_files[fileId]:
                experimentalCondition=experimentData_files[fileId]['experimentalConditions'][dataSourceId]
                var_id = 'var_'+ idataSourceId
                dict_variable_init={'id':var_id,'target':target_component_variable_initial(experimentalCondition['component'], experimentalCondition['name']),
                                    'modelReference':model_name,'taskReference':task_id}
                dataGenerator_id = 'dg_'+ idataSourceId
                dict_dataGenerator_init={'id':dataGenerator_id,'name':'dataGenerator1','math':var_id,'listOfVariables':[dict_variable_init]}
                dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator_init)
    
                dict_fitMapping_initial= {'type':'experimentalCondition','dataSource':idataSourceId,'target':dataGenerator_id}
                dict_fitExperiment['listOfFitMappings'].append(dict_fitMapping_initial)

        for observable_des in fitExperiment['observables']:
            fileId=observable_des[0]
            dataSourceId=observable_des[1]
            math_fun=observable_des[2]
            idataSourceId=fileId+'_'+dataSourceId
            if 'observables' in experimentData_files[fileId]:
                observable=experimentData_files[fileId]['observables'][dataSourceId]
                var_id = 'var_'+ idataSourceId
                dict_variable_observe={'id':var_id,'target':target_component_variable(observable['component'], observable['name']),
                                       'modelReference':model_name,'taskReference':task_id}
                dataGenerator_id = 'dg_'+ idataSourceId
                if math_fun=='':
                    math=var_id
                else:
                    math=math_fun+'('+var_id+')'
                dict_dataGenerator_observe={'id':dataGenerator_id,'name':'dataGenerator1','math':math,'listOfVariables':[dict_variable_observe]}
                dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator_observe)

                if isinstance(observable['weight'], str):
                    dict_fitMapping_observe= {'type':'observable','dataSource':idataSourceId,'target':dataGenerator_id,'pointWeight':observable['weight']}
                else:
                    dict_fitMapping_observe= {'type':'observable','dataSource':idataSourceId,'target':dataGenerator_id,'weight':observable['weight']}
    
                dict_fitExperiment['listOfFitMappings'].append(dict_fitMapping_observe)

                dataSet_id = 'dataset_'+ idataSourceId

                dict_dataSet={'id':dataSet_id,'label':idataSourceId,'dataReference':dataGenerator_id}
                dict_report['listOfDataSets'].append(dict_dataSet)     
        
        dict_parameterEstimationTask['listOfFitExperiments'].append(dict_fitExperiment)

    # report the objective value and optimal values of the adjustable parameters
    var_obj='var_obj'
    dg_obj='dg_obj'
    dataSet_obj='dataset_obj' 
    dict_variable_objective_value={'id':var_obj,'taskReference':task_id, 'symbol':'sedml:parameterestimation:objective_value'}
    dict_dataGenerator_objective_value={'id':dg_obj,'math':var_obj,'listOfVariables':[dict_variable_objective_value]}
    dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator_objective_value)
    dict_dataSet_objective_value={'id':dataSet_obj,'label':'OBJ','dataReference':dg_obj}
    dict_report['listOfDataSets'].append(dict_dataSet_objective_value)
    
    var_optimal='var_optimal'
    dg_optimal='dg_optimal'
    dataSet_optimal='dataset_optimal'
    dict_variable_adjustableParameters={'id':var_optimal,'taskReference':task_id, 'symbol':'sedml:parameterestimation:optimal_adjustableParameters'}
    dict_dataGenerator_adjustableParameters={'id':dg_optimal,'math':var_optimal,'listOfVariables':[dict_variable_adjustableParameters]}
    dict_sedDocument['listOfDataGenerators'].append(dict_dataGenerator_adjustableParameters)
    dict_dataSet_adjustableParameters={'id':dataSet_optimal,'label':'ADJ','dataReference':dg_optimal}
    dict_report['listOfDataSets'].append(dict_dataSet_adjustableParameters)

    dict_sedDocument['listOfTasks'].append(dict_parameterEstimationTask)
    dict_sedDocument['listOfReports'].append(dict_report)

    return