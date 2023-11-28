import requests
import os
import pandas
import tempfile
import re
from .sedModel_changes import get_variable_info_CellML,resolve_model_and_apply_xml_changes
from .simulator import  get_observables,get_KISAO_parameters,SimSettings,load_module
from .sedEditor import get_dict_algorithm
from .analyser import parse_model,analyse_model_full,get_mtype
from .coder import writePythonCode
import copy
import numpy as np


def get_variables_for_task(doc, task):
    """ Get the variables that a task must record

    Args:
        doc (:obj:`SedDocument`): SED document
        task (:obj:`SedTask`): task

    Returns:
        :obj:`list` of :obj:`SedVariable`: variables that task must record
    """
    data_generators = set()
    for i in range(doc.getNumOutputs()):
        output=doc.getOutput(i)
        data_generators.update(get_data_generators_for_output(output))

    sedDataGenerators = [output.getSedDocument().getDataGenerator(data_generator_name) for data_generator_name in data_generators]
    if None in sedDataGenerators:
        sedDataGenerators.remove(None)

    variables = get_variables_for_data_generators(sedDataGenerators)
    for variable in variables:
        task_name = variable.getTaskReference ()
        if task_name != task.getId ():
            variables.remove (variable)
    return variables

def get_data_generators_for_output(output):
    """ Get the data generators involved in an output, TODO: only SED reports are supported

    Args:
        output (:obj:`SedOutput`): report or plot

    Returns:
        :obj:`set` of :obj:`string`: data generator ids involved in the output
    """
    data_generators = set()
    if output.isSedReport ():
        for sedDataSet in output.getListOfDataSets ():
            data_generator_name=sedDataSet.getDataReference()
            data_generators.add(data_generator_name)
    else:
        print("Only SED reports are supported.")

    return data_generators

def get_variables_for_data_generators(data_generators):
    """ Get the variables involved in a collection of generators

    Args:
        data_generators (:obj:`list` of :obj:`SedDataGenerator`): data generators

    Returns:
        :obj:`set` of :obj:`SedVariables`: variables id involved in the data generators
    """
    variables = set()
    sedVariables=[]    
    for data_gen in data_generators:
        for sedVariable in data_gen.getListOfVariables ():
            if sedVariable.getId () not in variables:
                sedVariables.append(sedVariable)
            variables.add(sedVariable.getId ())
    return sedVariables

def get_variables_for_data_generator(data_generator):
    """ Get the variables involved in a collection of generators

    Args:
        data_generators (:obj:`SedDataGenerator`): data generator

    Returns:
        :obj:`set` of :obj:`SedVariables`: variables id involved in the data generators
    """
    variables = set()
    sedVariables=[]    
    for sedVariable in data_generator.getListOfVariables ():
        if sedVariable.getId () not in variables:
            sedVariables.append(sedVariable)
        variables.add(sedVariable.getId ())
    return sedVariables 

def get_model_changes_for_task(task):
    """ Get the changes to models for a task

    Args:
        task (:obj:`Task`): task

    Returns:
        :obj:`list` of :obj:`ModelChange`: changes to the model
    """
    doc=task.getSedDocument()
    if task.isSedTask():
        return []
    elif task.isSedRepeatedTask():
        changes = [task.getTaskChange(i) for i in range(task.getNumTaskChanges())]

        for sub_task in [task.getSubTask(i) for i in range(task.getNumSubTasks())]:
            itask = sub_task.getTask()           
            changes.extend(get_model_changes_for_task(doc.getTask(itask)))
        return changes
    else:
        print("Only SED tasks are supported.")
        return []   

def get_models_referenced_by_task(doc,task):
    """ Get the models referenced from a task
    
    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    task: :obj:`SedTask`
        An instance of SedTask
    
    Raises
    ------
    ValueError
        If the task is not of type SedTask or SedRepeatedTask or SedParameterEstimationTask
        
    Returns
    -------
    :obj:`list` of :obj:`SedModel`
        A list of SedModel objects
    """
 
    if task.isSedTask ():
        models = set()
        if task.isSetModelReference ():
            models.add(task.getModelReference ())
        sedModels=[doc.getModel(modelReference) for modelReference in models]
        return sedModels

    elif task.isSedRepeatedTask () :
        models = set()
        for change in task.getListOfTaskChanges ():
            models.update(get_models_referenced_by_setValue(change))

        for sub_task in task.getListOfSubTasks ():
            itask = doc.getTask(sub_task.getTask ())
            models.update(get_models_referenced_by_task(doc,itask))
            for change in sub_task.getListOfTaskChanges (): # newly added in Level 4
                models.update(get_models_referenced_by_setValue(change)) 

        if task.isSetRangeId (): # TODO: check if this is already covered by getListOfRanges
            irange = task.getRange(task.getRangeId ())
            models.update(get_models_referenced_by_range(task,irange))

        for range in  task.getListOfRanges ():
            models.update(get_models_referenced_by_range(task,range))
        
        sedModels=[doc.getModel(modelReference) for modelReference in models]
        return sedModels
    
    elif task.isSedParameterEstimationTask ():
        models = set()
        for adjustableParameter in task.getListOfAdjustableParameters ():
            models.update(get_models_referenced_by_adjustableParameter(adjustableParameter)) 

        sedModels=[doc.getModel(modelReference) for modelReference in models]
        return sedModels        
    else:
        raise ValueError('Tasks of type `{}` are not supported.'.format(task.getTypeCode ()))
    
def get_models_referenced_by_range(task,range):
    """ Get the models referenced by a range

    Args:
        range (:obj:`SedRange`): range

    Returns:
        :obj:`set` of :obj:`SedModel`: models
    """
    models = set()
    if range.isSedFunctionalRange () and range.getListOfVariables ():
        models.update(get_models_referenced_by_listOfVariables(range.getListOfVariables ()))
    if range.isSetRange ():
        irange=task.getRange(range.getRange ())
        models.update(get_models_referenced_by_range(task,irange))
    return models

def get_models_referenced_by_setValue(task,setValue):
    
    models = set()
    models.add(setValue.getModelReference ())
    if setValue.isSetRange ():
        irange=task.getRange(setValue.getRange ())
        models.update(get_models_referenced_by_range(irange))
    if setValue.getListOfVariables ():
        models.update(get_models_referenced_by_listOfVariables(setValue.getListOfVariables))
    return models

def get_models_referenced_by_computedChange(change):
    models = set()  
    if change.getListOfVariables ():
        models.update(get_models_referenced_by_listOfVariables(change.getListOfVariables))
    return models

def get_models_referenced_by_listOfVariables(listOfVariables):
    models = set()
    for variable in listOfVariables:
        if variable.isSetModelReference ():
            models.add(variable.getModelReference ())
    return models

def get_models_referenced_by_adjustableParameter(adjustableParameter):
    """
    Note: will depreciate in future versions once the issue https://github.com/fbergmann/libSEDML/issues/172 is fixed
    """
    models = set()
    if adjustableParameter.isSetModelReference ():
        models.add(adjustableParameter.getModelReference ())
    return models

def get_df_from_dataDescription(dataDescription, working_dir):
    """
    Return a pandas.DataFrame from a dataDescription.
    Assume the data source file is a csv file.

    Parameters
    ----------
    dataDescription: :obj:`SedDataDescription`
        An instance of SedDataDescription
    working_dir: :obj:`str`
        working directory of the SED document (path relative to which data source files are located)

    Raises
    ------
    FileNotFoundError
        If the data source file does not exist

    Returns
    -------
    :obj:`pandas.DataFrame`
        A pandas.DataFrame object
    
    """

    source = dataDescription.getSource ()
    if re.match(r'^http(s)?://', source, re.IGNORECASE):
        response = requests.get(source)
        try:
            response.raise_for_status()
        except Exception:
            raise FileNotFoundError('Model could not be downloaded from `{}`.'.format(source))

        temp_file, temp_data_source = tempfile.mkstemp()
        os.close(temp_file)
        with open(temp_data_source, 'wb') as file:
            file.write(response.content)
        filename = temp_data_source
    else:
        if os.path.isabs(source):
            filename = source
        else:
            filename = os.path.join(working_dir, source)

        if not os.path.isfile(os.path.join(working_dir, source)):
            raise FileNotFoundError('Data source file `{}` does not exist.'.format(source))
    
    df = pandas.read_csv(filename, skipinitialspace=True,encoding='utf-8')

    return df

def get_value_of_dataSource(doc, dataSourceID,dfDict):
    """
    Return a numpy.ndarray from a data source.
    Assume 2D dimensionDescription and 2D data source.

    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    dataSourceID: :obj:`str`
        The id of the data source
    dfDict: :obj:`dict` of :obj:`pandas.DataFrame`
        A dictionary of pandas.DataFrame objects
        The format is {dataDescription.getId(): pandas.DataFrame}

    Raises
    ------
    ValueError

    Returns
    -------
    :obj:`numpy.ndarray`
        A numpy.ndarray object
    """
    
    dim1_value=None
    dim2_value=None
    dim1_present=False
    dim2_present=False
    dim1_startIndex=None
    dim1_endIndex=None
    dim2_startIndex=None
    dim2_endIndex=None
    for dataDescription in doc.getListOfDataDescriptions ():
        for dataSource in dataDescription.getListOfDataSources ():
            if dataSource.getId () == dataSourceID: # expect only one data source
                df=dfDict[dataDescription.getId()]
                dimensionDescription=dataDescription.getDimensionDescription ()
                dim1_Description=dimensionDescription.get(0)
                dim1_index=dim1_Description.getId() 
                dim2_Description=dim1_Description.get(0)
                dim2_index=dim2_Description.getId()             
                if dataSource.isSetIndexSet ():# expect only using slice
                    raise ValueError('IndexSet is not supported.')
                else:
                    for sedSlice in dataSource.getListOfSlices (): # up to two slices supported
                        if sedSlice.getReference ()==dim1_index:
                            dim1_present=True
                            if sedSlice.isSetValue ():
                                dim1_value=sedSlice.getValue ()
                            if sedSlice.isSetStartIndex ():
                                dim1_startIndex=sedSlice.getStartIndex ()
                            if sedSlice.isSetEndIndex ():
                                dim1_endIndex=sedSlice.getEndIndex ()
                        elif sedSlice.getReference ()==dim2_index:
                            dim2_present=True
                            if sedSlice.isSetValue (): 
                                dim2_value=sedSlice.getValue ()
                            if sedSlice.isSetStartIndex ():
                                dim2_startIndex=sedSlice.getStartIndex ()
                            if sedSlice.isSetEndIndex ():
                                dim2_endIndex=sedSlice.getEndIndex ()
                        else:
                            raise ValueError('up to two slices supported')

                    if dim1_present and (not dim2_present): 
                        # get the value(s) at index=dim1_value or all values if dim1_value is not set then subdivide the values according to startIndex and endIndex
                        # TODO: need to check if the understanding of the slice is correct   
                        if dim1_value is not None:
                            value=df.iloc[[dim1_value]]
                        elif dim1_startIndex is not None and dim1_endIndex is not None:
                            value=df.iloc[dim1_startIndex:(dim1_endIndex+1)]
                        elif dim1_startIndex is not None and (dim1_endIndex is None):
                            value=df.iloc[dim1_startIndex:]
                        elif (dim1_startIndex is None) and dim1_endIndex is not None:
                            value=df.iloc[:(dim1_endIndex+1)]
                        else:
                            value=df
                        return value.to_numpy()
                    
                    elif dim2_present and (not dim1_present):
                        # get the value(s) of the column and then subdivide the values according to startIndex and endIndex
                        if dim2_value:
                            columnName=dim2_value
                            df_selected=df[columnName]
                            if dim2_startIndex is not None and dim2_endIndex is not None:
                                value=df_selected.iloc[dim2_startIndex:(dim2_endIndex+1)]
                            elif dim2_startIndex is not None and (dim2_endIndex is None):
                                value=df_selected.iloc[dim2_startIndex:]
                            elif (dim2_startIndex is None) and dim2_endIndex is not None:
                                value=df_selected.iloc[:(dim2_endIndex+1)]
                            else:
                                value=df_selected
                            return value.to_numpy()
                        
                    elif dim1_present and dim2_present:
                        # get a single value at index=dim1_value and column=dim2_value
                        columnName=dim2_value
                        df_selected=df[columnName]
                        if dim1_value is not None:
                            df_selected=df_selected.iloc[[float(dim1_value)]]
                        return df_selected.to_numpy()
                    else:
                        raise ValueError('Data source `{}` is not defined.'.format(dataSourceID))

def get_adjustableParameters(model_etree,task):
    """
    Return a tuple containing adjustable parameter information.
    Assume the model is a CellML model.
    
    Parameters
    ----------
    model_etree: :obj:`lxml.etree._ElementTree`
        An instance of lxml.etree._ElementTree
    task: :obj:`SedParameterEstimationTask`

    Raises
    ------
    ValueError

    Returns
    -------
    tuple
        A tuple containing adjustable parameter information
        adjustableParameters_info: dict, {index: {'component':component,'name':name}}
        experimentReferences: dict, {index: [experimentId]}
        lowerBound: list, [lowerBound]
        upperBound: list, [upperBound]
        initial_value: list, [initial_value]  
    """
    adjustableParameters_info={}
    experimentReferences={}
    lowerBound=[]
    upperBound=[]
    initial_value=[]
    for i in range(len(task.getListOfAdjustableParameters())):
        adjustableParameter=task.getAdjustableParameter(i)
        try:
            variables_info = get_variable_info_CellML([adjustableParameter],model_etree)
        except ValueError as exception:
            raise exception
        for key,variable_info in variables_info.items(): # should be only one variable
            adjustableParameters_info[i]={'component':variable_info['component'],'name': variable_info['name']}

        bonds=adjustableParameter.getBounds()
        lowerBound.append(bonds.getLowerBound ())
        upperBound.append(bonds.getUpperBound ())
        if adjustableParameter.isSetInitialValue ():
            initial_value.append(adjustableParameter.getInitialValue())
        else:
            initial_value.append(bonds.getLowerBound ())
        experimentReferences[i]=[]
        if adjustableParameter.getNumExperimentReferences()>0:
            for experiment in adjustableParameter.getListOfExperimentReferences ():
                experimentReferences[i].append(experiment.getExperimentId () )
        else:
            for experiment in task.getListOfExperiments():
                experimentReferences[i].append(experiment.getId())
        
    return adjustableParameters_info,experimentReferences,lowerBound,upperBound,initial_value


def get_fit_experiments(doc,task,analyser, cellml_model,model_etree,dfDict):
    """
    Return a dictionary containing fit experiment information.
    Assume the model is a CellML model.
    The variables in experiment conditions are set to be parameters.

    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    task: :obj:`SedParameterEstimationTask`
    analyser: Analyser
        The Analyser instance of the cellml model
    cellml_model: Model
        The CellML model
    model_etree: :obj:`lxml.etree._ElementTree`
        An instance of lxml.etree._ElementTree
    dfDict: :obj:`dict` of :obj:`pandas.DataFrame`

    Raises
    ------
    ValueError

    Returns
    -------
    dict
        A dictionary containing fit experiment information
        fitExperiments: dict, {experimentId: {'type':type,'algorithm':algorithm,'tspan':tspan,'parameters':parameters,'fitness_info':fitness_info}}
        type: str, 'steadyState' or 'timeCourse'
        algorithm: {'kisaoID': , 'name': , 'listOfAlgorithmParameters': [{'kisaoID': , 'name': , 'value': }]}
        tspan: list, [t0,t1]
        parameters: dict, The format is {id:{'name':'variable name','component':'component name',
        'type':'state','value':value,'index':index}}
        fitness_info: tuple, (observables_info,observables_weight,observables_exp)
        observables_info: dict, {dataGeneratorId: {'component':component,'name':name,'index':index,'type':type}}
        observables_weight: dict, {dataGeneratorId: weight}, where weight is numpy.ndarray.
        observables_exp: dict, {dataGeneratorId: observable_exp}, where observable_exp is numpy.ndarray.

    """
    fitExperiments={}
    for fitExperiment in task.getListOfFitExperiments():
        if fitExperiment.getTypeAsString ()=='steadyState':
            simulation_type='steadyState'
        elif fitExperiment.getTypeAsString ()=='timeCourse':
            simulation_type='timeCourse'
        else:
            raise ValueError('Experiment type {} is not supported!'.format(fitExperiment.getTypeAsString ()))
        fitExperiments[fitExperiment.getId()]={}
        fitExperiments[fitExperiment.getId()]['type']=simulation_type
        sed_algorithm = fitExperiment.getAlgorithm()
        try:
            fitExperiments[fitExperiment.getId()]['algorithm']=get_dict_algorithm(sed_algorithm)
        except ValueError as exception:
            raise exception
        fitExperiments[fitExperiment.getId()]['tspan']=[]
        fitExperiments[fitExperiment.getId()]['parameters']={}
        observables_exp={}
        observables_weight={}
        observables_info={}

        for fitMapping in fitExperiment.getListOfFitMappings ():
            if fitMapping.getTypeAsString ()=='time':
                try:
                    tspan=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                # should be 1D array
                if tspan.ndim>1:
                    raise ValueError('The time course {} is not 1D array!'.format(fitMapping.getDataSource()))
                else:
                    fitExperiments[fitExperiment.getId()]['tspan']=tspan

            elif fitMapping.getTypeAsString ()=='experimentalCondition':
                try:
                    initial_value_=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                if initial_value_.ndim>1:
                    raise ValueError('The experimental condition {} is not 1D array!'.format(fitMapping.getDataSource()))
                elif len(initial_value_)==1:
                    initial_value=initial_value_[0]
                else:
                    raise ValueError('The experimental condition {} is not a scalar!'.format(fitMapping.getDataSource()))
                a=fitMapping.getTarget()
                dataGenerator=doc.getDataGenerator(fitMapping.getTarget())
                sedVars=get_variables_for_data_generator(dataGenerator)
                if len(sedVars)>1:
                    raise ValueError('The data generator {} has more than one variable!'.format(fitMapping.getTarget()))
                else:
                    try:
                        parameter_info = get_variable_info_CellML(sedVars,model_etree)
                        parameter=get_observables(analyser, cellml_model, parameter_info)
                    except ValueError as exception:
                        raise exception                    
                    fitExperiments[fitExperiment.getId()]['parameters'].update(parameter)
                    for sedVar in sedVars:
                        fitExperiments[fitExperiment.getId()]['parameters'][sedVar.getId()]['value']=initial_value                                       

            elif fitMapping.getTypeAsString ()=='observable':
                try:
                    observable_exp=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                if observable_exp.ndim>1:
                    raise ValueError('The observable {} is not 1D array!'.format(fitMapping.getDataSource()))
                
                a=fitMapping.getTarget()
                dataGenerator=doc.getDataGenerator(fitMapping.getTarget())
                sedVars=get_variables_for_data_generator(dataGenerator)
                try:
                    observable_info = get_variable_info_CellML(sedVars,model_etree)
                    observable=get_observables(analyser, cellml_model, observable_info)
                except ValueError as exception:
                    raise exception                                   
                observables_info.update(observable)
                key=dataGenerator.getId()

                if fitMapping.isSetWeight():
                    weight=fitMapping.getWeight()
                    observables_weight.update({key:weight})
                elif fitMapping.isSetPointWeight ():
                    try:
                        pointWeight=get_value_of_dataSource(doc, fitMapping.getPointWeight(),dfDict)
                    except ValueError as exception:
                        raise exception
                    if pointWeight.ndim>1:
                        raise ValueError('The point weight {} is not 1D array!'.format(fitMapping.getPointWeight()))
                    else:
                        # observable_exp and pointWeight should have the same length
                        if len(observable_exp)!=len(pointWeight):
                            raise ValueError('The observable {} and point weight {} do not have the same length!'.format(fitMapping.getDataSource(),fitMapping.getPointWeight()))
                        else:
                            observables_weight.update({key:pointWeight})
                else:
                    raise ValueError('Fit mapping {} does not have a weight!'.format(fitMapping.getId()))
                      
                observables_exp.update({key:observable_exp})

            else:
                raise ValueError('Fit mapping type {} is not supported!'.format(fitMapping.getTypeAsString ()))
            
        fitExperiments[fitExperiment.getId()]['fitness_info']=(observables_info,observables_weight,observables_exp) 

    return fitExperiments

def get_fit_experiments_1(doc,task,working_dir,dfDict,external_variables_info={}):
    """
    Return a dictionary containing fit experiment information.
    Assume the model is a CellML model.
    The variables in experiment conditions are set to be parameters.

    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    task: :obj:`SedParameterEstimationTask`
    working_dir: :obj:`str`
        working directory of the SED document (path relative to which models are located)
    dfDict: :obj:`dict` of :obj:`pandas.DataFrame`
    external_variables_info: dict, optional
        The external variables to be specified, in the format of {id:{'component': , 'name': }}

    Raises
    ------
    ValueError

    Returns
    -------
    dict
        A dictionary containing fit experiment information
        fitExperiments: dict,
        {experimentId: {'type':type,'algorithm':algorithm,'tspan':tspan,'parameters':parameters,'fitness_info':fitness_info,
        'model':model,'cellml_model':cellml_model,'analyser':analyser, 'module':module, 'mtype':mtype,
        'external_variables_info':external_variables_info,'param_indices':param_indices
        },
        'adjustableParameters_info':adjustableParameters_info,'experimentReferences':experimentReferences,	
        'lowerBound':lowerBound,'upperBound':upperBound,'initial_value':initial_value}

    """
    fitExperiments={}
    original_models = get_models_referenced_by_task(doc,task)
    model=original_models[0] # parameter estimation task should have only one model
    try:
        temp_model, temp_model_source, model_etree = resolve_model_and_apply_xml_changes(model, doc, working_dir) # must set save_to_file=True
        cellml_model,parse_issues=parse_model(temp_model_source, True)
        if not cellml_model:
            raise RuntimeError('Model parsing failed!')
        adjustableParameters_info,experimentReferences,lowerBound,upperBound,initial_value=get_adjustableParameters(model_etree,task)
        adjustables=(lowerBound,upperBound,initial_value)
    except ValueError as exception:
        raise exception
    for fitExperiment in task.getListOfFitExperiments():
        external_variables_info_new=copy.deepcopy(external_variables_info)
        fitExperiments[fitExperiment.getId()]={}
        if fitExperiment.getTypeAsString ()=='steadyState':
            fitExperiments[fitExperiment.getId()]['type']='steadyState'
        elif fitExperiment.getTypeAsString ()=='timeCourse':
            fitExperiments[fitExperiment.getId()]['type']='timeCourse'
        else:
            raise ValueError('Experiment type {} is not supported!'.format(fitExperiment.getTypeAsString ()))
        sim_setting=SimSettings()
        sim_setting.number_of_steps=0
        sed_algorithm = fitExperiment.getAlgorithm()
        try:
            dict_algorithm=get_dict_algorithm(sed_algorithm)
            sim_setting.method, sim_setting.integrator_parameters=get_KISAO_parameters(dict_algorithm)
        except ValueError as exception:
            raise exception
        if fitExperiment.isSetName (): # temporary solution for the case that a variant model is used for this fit experiment
            modelReference=fitExperiment.getName ()
            model=doc.getModel(modelReference)
        fitExperiments[fitExperiment.getId()]['model']=model
        try:
            temp_model, temp_model_source, model_etree = resolve_model_and_apply_xml_changes(model, doc, working_dir) # must set save_to_file=True
            cellml_model,parse_issues=parse_model(temp_model_source, True)
            if not cellml_model:
                raise RuntimeError('Model parsing failed!')
        except ValueError as exception:
            raise exception   
        sub_adjustableParameters_info={}
        adj_param_indices=[]
        for i in range(len(experimentReferences)):         
            if fitExperiment.getId() in experimentReferences[i]:
                sub_adjustableParameters_info.update({i:adjustableParameters_info[i]})
                adj_param_indices.append(i)
        
        external_variables_info_new.update(sub_adjustableParameters_info) 
        observables_exp={}
        observables_weight={}
        observables_info={}
        fitExperiments[fitExperiment.getId()]['parameters']={} 
        parameters_values=[]       
        for fitMapping in fitExperiment.getListOfFitMappings ():
            if fitMapping.getTypeAsString ()=='time':
                try:
                    tspan=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                # should be 1D array
                if tspan.ndim>1:
                    raise ValueError('The time course {} is not 1D array!'.format(fitMapping.getDataSource()))
                else:
                    sim_setting.tspan=tspan

            elif fitMapping.getTypeAsString ()=='experimentalCondition':
                try:
                    initial_value_=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                if initial_value_.ndim>1:
                    raise ValueError('The experimental condition {} is not 1D array!'.format(fitMapping.getDataSource()))
                elif len(initial_value_)==1:
                    initial_value=initial_value_[0]
                else:
                    #raise ValueError('The experimental condition {} is not a scalar!'.format(fitMapping.getDataSource()))
                    initial_value=initial_value_
                dataGenerator=doc.getDataGenerator(fitMapping.getTarget())
                sedVars=get_variables_for_data_generator(dataGenerator)
                if len(sedVars)>1:
                    raise ValueError('The data generator {} has more than one variable!'.format(fitMapping.getTarget()))
                else:
                    try:
                        parameter_info = get_variable_info_CellML(sedVars,model_etree)
                        if isinstance (initial_value, np.ndarray):
                            external_variables_info_new.update(parameter_info)
                            parameters_values.append(initial_value)
                        else:
                            fitExperiments[fitExperiment.getId()]['parameters'].update(parameter_info)
                            fitExperiments[fitExperiment.getId()]['parameters'][sedVars[0].getId()]['value']=initial_value                       
                    except ValueError as exception:
                        raise exception                          
            elif fitMapping.getTypeAsString ()=='observable':
                try:
                    observable_exp=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                except ValueError as exception:
                    raise exception
                if observable_exp.ndim>1:
                    raise ValueError('The observable {} is not 1D array!'.format(fitMapping.getDataSource()))             
                dataGenerator=doc.getDataGenerator(fitMapping.getTarget())
                sedVars=get_variables_for_data_generator(dataGenerator)
                try:
                    observable_info = get_variable_info_CellML(sedVars,model_etree)
                except ValueError as exception:
                    raise exception                                   
                observables_info.update(observable_info)
                key=dataGenerator.getId()                                                
                if fitMapping.isSetWeight():
                    weight=fitMapping.getWeight()
                    observables_weight.update({key:weight})
                elif fitMapping.isSetPointWeight ():
                    try:
                        pointWeight=get_value_of_dataSource(doc, fitMapping.getPointWeight(),dfDict)
                    except ValueError as exception:
                        raise exception
                    if pointWeight.ndim>1:
                        raise ValueError('The point weight {} is not 1D array!'.format(fitMapping.getPointWeight()))
                    else:
                        # observable_exp and pointWeight should have the same length
                        if len(observable_exp)!=len(pointWeight):
                            raise ValueError('The observable {} and point weight {} do not have the same length!'.format(fitMapping.getDataSource(),fitMapping.getPointWeight()))
                        else:
                            observables_weight.update({key:pointWeight})
                else:
                    raise ValueError('Fit mapping {} does not have a weight!'.format(fitMapping.getId()))
                      
                observables_exp.update({key:observable_exp})

            else:
                raise ValueError('Fit mapping type {} is not supported!'.format(fitMapping.getTypeAsString ()))
        
        model_base_dir=os.path.dirname(temp_model.getSource())
                         
        analyser, issues =analyse_model_full(cellml_model,model_base_dir,external_variables_info_new)       
        if analyser:
            mtype=get_mtype(analyser)
            # write Python code to a temporary file
            tempfile_py, full_path = tempfile.mkstemp(suffix='.py', prefix=temp_model.getId()+"_", text=True,dir=model_base_dir)
            writePythonCode(analyser, full_path)
            module=load_module(full_path)
            os.close(tempfile_py)
            # and delete temporary file
          #  os.remove(full_path)

        fitExperiments[fitExperiment.getId()]['fitness_info']=(observables_info,observables_weight,observables_exp)
        fitExperiments[fitExperiment.getId()]['sim_setting']=sim_setting
        fitExperiments[fitExperiment.getId()].update({'cellml_model':cellml_model,'analyser':analyser, 'module':module, 'mtype':mtype,
                                                                            'external_variables_info':external_variables_info_new,
                                                                'adj_param_indices':adj_param_indices,'parameters_values':parameters_values})      
    return fitExperiments,adjustables 