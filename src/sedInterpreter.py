import requests
import tempfile
import os
import re
import numpy
import copy
import enum
import sys
import datetime
import libsedml
from .math4sedml import compile_math,eval_math,AGGREGATE_MATH_FUNCTIONS
from lxml import etree
from .report import pad_arrays_to_consistent_shapes, writeReport
from.solver import load_module
from.analyser import analyse_model_full,parse_model,External_module,get_observables,get_variable_indices, get_mtype
from.coder import writePythonCode
from.simulator import sim_UniformTimeCourse,getSimSettingFromDict,sim_TimeCourse,SimSettings,get_KISAO_parameters
from .optimiser import get_KISAO_parameters_opt
from .sedEditor import get_dict_simulation, get_dict_algorithm
from scipy.optimize import minimize, Bounds
import pandas

CELLML2NAMESPACE ={"cellml":"http://www.cellml.org/cellml/2.0#"}

BIOMODELS_DOWNLOAD_ENDPOINT = 'https://www.ebi.ac.uk/biomodels/model/download/{}?filename={}_url.xml'


def exec_sed_doc(doc, working_dir,model_base_dir, base_out_path, rel_out_path=None, external_variables_info=None, external_variables_values=None,indent=0):
    
    doc = doc.clone() # clone the document to avoid modifying the original document
    listOfTasks = doc.getListOfTasks()
    listOfOutputs = doc.getListOfOutputs()
    # Print information about the SED document
    if len(listOfTasks)==0:
        print('SED document does not describe any tasks.')
    print('{}Found {} tasks and {} outputs:\n{}Tasks:\n{}{}\n{}Outputs:\n{}{}'.format(
        ' ' * 2 * indent,
        len(listOfTasks),
        len(listOfTasks),
        ' ' * 2 * (indent + 1),
        ' ' * 2 * (indent + 2),
        ('\n' + ' ' * 2 * (indent + 2)).join(sorted('`' + task.getId() + '`' for task in listOfTasks)),
        ' ' * 2 * (indent + 1),
        ' ' * 2 * (indent + 2),
        ('\n' + ' ' * 2 * (indent + 2)).join(sorted('`' + output.getId() + '`' for output in listOfOutputs)),
    ))
    # execute tasks
    variable_results = {}
    report_results = {}
    for i_task, task in enumerate(listOfTasks):
        print('{}Executing task {}: `{}`'.format(' ' * 2 * indent, i_task + 1, task.getId()))
        # Execute task
        print('{}Executing simulation ...'.format(' ' * 2 * (indent + 1)), end='')
        sys.stdout.flush()
        start_time = datetime.datetime.now()
        # get model and apply changes
        original_models = get_models_referenced_by_task(doc,task)
        temp_model_sources = []
        model_etrees = {}
        for original_model in original_models:
            temp_model, temp_model_source, model_etree = resolve_model_and_apply_xml_changes(original_model, doc, working_dir)
            
            original_model.setSource(temp_model.getSource())
            original_model.getListOfChanges().clear()
            for change in temp_model.getListOfChanges():
                original_model.addChange(change)
            if temp_model_source:
                temp_model_sources.append(temp_model_source)
            model_etrees[original_model.getId()] = model_etree
        
        # execute task
        if task.isSedTask ():
            try:
                current_state, task_var_results=exec_task(doc,task, original_model,model_etree, model_base_dir,external_variables_info,external_variables_values)
            except Exception as exception:
                print(exception)
                raise RuntimeError(exception)           

        elif task.isSedRepeatedTask ():
            task_var_results = exec_repeated_task(doc,task,model_base_dir,external_variables_info,external_variables_values, model_etrees=model_etrees)
        elif task.isSedParameterEstimationTask ():
            res=exec_parameterEstimationTask( doc,task, original_model,model_etree, working_dir, model_base_dir,external_variables_info,external_variables_values)
            
        else:  # pragma: no cover: already validated by :obj:`get_models_referenced_by_task`
            raise NotImplementedError('Tasks of type {} are not supported.'.format(task.getTypeCode () ))
        
        # append results
        for key, value in task_var_results.items():
            variable_results[key] = value

        # cleanup modified model sources
        for temp_model_source in temp_model_sources:
            os.remove(temp_model_source)

        # generate outputs
        print('{}Generating {} outputs ...'.format(' ' * 2 * (indent + 1), len(listOfOutputs)))
        task_contributes_to_output = False
        report_formats =['csv']
        for i_output, output in enumerate(listOfOutputs):
            print('{}Generating output {}: `{}` ...'.format(' ' * 2 * (indent + 2), i_output + 1, output.getId()), end='')
            sys.stdout.flush()
            if output.isSedReport ():
                output_result, output_status, output_exception, task_contributes_to_report = exec_report(
                    output, variable_results, base_out_path, rel_out_path, report_formats, task)
                
                task_contributes_to_output = task_contributes_to_output or task_contributes_to_report   

            else:
                # only reports are supported for now
                raise NotImplementedError('Outputs of type {} are not supported.'.format(output.getTypeCode ()))
            if  output_result is not None:
                report_results[output.getId()] = output_result


        if not task_contributes_to_output:
            print('Task {} does not contribute to any outputs.'.format(task.getId()))

    # return the results of the reports
    return report_results

def exec_task(doc,task, original_model,model_etree, model_base_dir,external_variables_info=[],external_variables_values=[],current_state=None):
    """ Execute a basic SED task

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document
        task (:obj:`SedTask`): task
        original_model (:obj:`SedModel`): model
        model_etree (:obj:`etree._Element`): model encoded in XML
        model_base_dir (:obj:`str`): the full path to the directory of the base model that import URLs are relative to, used to resolve imports
        external_variables_info (:obj:`list` of :obj:`tuple`): information about the external variables
    Returns:
        :obj:`VariableResults` or `None`: results of the variables or None if the task failed. The format is {variable.id: numpy.ndarray}
    """
    # get the model
    cellml_model,issues=parse_model(original_model.getSource(), True)
    if not cellml_model:
        print('Model parsing failed!',issues)
        raise RuntimeError('Model parsing failed!')
    # analyse the model
    analyser, issues =analyse_model_full(cellml_model,model_base_dir,external_variables_info)
    if not analyser:
        print('Model analysis failed!',issues)
        raise RuntimeError('Model analysis failed!')
    else:
        mtype=get_mtype(analyser)
        if mtype not in ['ode','algebraic']:
            print('Model type is not supported!')
            raise RuntimeError('Model type is not supported!')
                
    task_vars = get_variables_for_task(doc, task)
    if len(task_vars) == 0:
        print('Task does not record any variables.')
        raise RuntimeError('Task does not record any variables.')
    # get observables
    try:
        variables_info = get_variable_info_CellML(task_vars,model_etree)
    except ValueError as exception:
        print(exception)
        raise RuntimeError(exception)
    
    observables=get_observables(analyser,cellml_model,variables_info)
    if not observables:
        print('Not all observables found in the Python module!')
        raise RuntimeError('Not all observables found in the Python module!')
    # get simulation settings
    sedSimulation=doc.getSimulation(task.getSimulationReference())
    dict_simulation=get_dict_simulation(sedSimulation)
    if not dict_simulation:
        print('Simulation settings are not found!')
        raise RuntimeError('Simulation settings are not found!')
    
    sim_setting=getSimSettingFromDict(dict_simulation)
    if not sim_setting:
        print('Simulation settings are not supported!')
        raise RuntimeError('Simulation settings are not supported!')
    
    # write Python code
    full_path = model_base_dir+'/'+original_model.getId()+'.py'
    writePythonCode(analyser, full_path)
    try:
        module=load_module(full_path)
    except Exception as exception:
        print(exception)
        raise RuntimeError(exception)
    # specify external variables
    try:
        param_indices=get_variable_indices(analyser, cellml_model,external_variables_info)
    except ValueError as exception:
        print(exception)
        raise RuntimeError(exception)
    external_module=External_module(param_indices,external_variables_values)
    # execute simulation    
    if dict_simulation['type']=='UniformTimeCourse':
        if current_state:
            try:
                task_variable_results=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module,current_state)[-1]
            except Exception as exception:
                print(exception)
                raise RuntimeError(exception)
        else:
            try:
                task_variable_results=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module)[-1]
            except Exception as exception:
                print(exception)
                raise RuntimeError(exception)
    # check that the expected variables were recorded
    variable_results = {}
    if len(task_variable_results) > 0:
        for i,ivar in enumerate(task_vars):
            variable_results[ivar.getId()] = task_variable_results.get(ivar.getId(), None)
    # return results
    return current_state, variable_results

def get_variable_info_CellML(task_variables,model_etree):
    """ Get information about the variables of a task
    Args:
        task_variables (:obj:`list` of :obj:`SedVariable`): variables of a task
        model_etree (:obj:`etree._Element`): model encoded in XML
    Returns:
        :obj:`dict`: information about the variables in the format {variable.id: {'name': variable name, 'component': component name}}
    """
    variable_info={}
    for v in task_variables:
        if v.getTarget().rpartition('/@')[-1]=='initial_value': # target initial value instead of variable
            vtemp=v.getTarget().rpartition('/@')
            variable_element = model_etree.xpath(vtemp[0],namespaces={"cellml":"http://www.cellml.org/cellml/2.0#"})[0]
        else:
            variable_element = model_etree.xpath(v.getTarget (),namespaces={"cellml":"http://www.cellml.org/cellml/2.0#"})[0]
        if variable_element is False:
            raise ValueError('The variable {} is not found!'.format(v.getTarget () ))
        else:
            variable_info[v.getId()] = {
                'name': variable_element.attrib['name'],
                'component': variable_element.getparent().attrib['name']
            }
    return variable_info


def exec_repeated_task(doc,task,working_dir,external_variables_info,
                                                  model_etrees=None,
                                                  pretty_print_modified_xml_models=True):
    """ Execute a repeated SED task

    Args:
        task (:obj:`RepeatedTask`): task
        task_executer (:obj:`types.FunctionType`): function to execute each task in the SED-ML file.
            The function must implement the following interface::

                def exec_task(task, variables, preprocessed_task=None, log=None, config=None, **simulator_config):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
                       preprocessed_task (:obj:`object`, optional): preprocessed information about the task, including possible
                            model changes and variables. This can be used to avoid repeatedly executing the same initialization
                            for repeated calls to this method.
                       log (:obj:`TaskLog`, optional): log for the task
                       config (:obj:`Config`, optional): BioSimulators common configuration
                       **simulator_config (:obj:`dict`, optional): optional simulator-specific configuration

                    Returns:
                       :obj:`VariableResults`: results of variables
                    '''
                    pass

        task_vars (:obj:`list` of :obj:`Variable`): variables that task must record
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`)
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`VariableResults`: results of the variables
    """
    task_vars = get_variables_for_task(doc, task)
    # hold onto model to be able to reset it
    if task.isSetResetModel ():
        original_doc = doc
        original_task = task
        original_model_etrees = model_etrees

    # resolve the ranges
    main_range_values = resolve_range(task.getRange(task.getRangeId ()), model_etrees=model_etrees)

    range_values = {}
    for range in task.getListOfRanges ():
        range_values[range.getId()] = resolve_range(range, model_etrees=model_etrees)
    for change in task.getListOfChanges():
        if change.isSetRange () :
            range_values[change.getRange ()] = resolve_range(task.getRange(change.getRange ()), model_etrees=model_etrees)

    # initialize the results of the sub-tasks
    variable_results = {}
    for var in task_vars:
        variable_results[var.getId()] = []
        for main_range_value in main_range_values:
            variable_results[var.getId()].append([None] * task.getNumSubTasks ())

    # iterate over the main range, apply the changes to the model(s), execute the sub-tasks, and record the results of the tasks
    for i_main_range, _ in enumerate(main_range_values):
        # reset the models referenced by the task
        if task.isSetResetModel ():
            doc = original_doc.clone()
            task = next(task for task in doc.getListOfTasks () if task.getId() == original_task.getId())
            model_etrees = copy.deepcopy(original_model_etrees)

        # get range values
        current_range_values = {}
        current_range_values[task.getRangeId ()] = range_values[task.getRangeId ()][i_main_range]
        for range in task.getListOfRanges ():
            current_range_values[range.getId()] = range_values[range.getId()][i_main_range]
        for change in task.getListOfChanges():
            if change.isSetRange ():
                current_range_values[change.getRange ()] = range_values[change.getRange ()][i_main_range]

        # apply the changes to the models
        for change in task.getListOfChanges():
            variable_values = {}
            for variable in change.getListOfVariables ():
                variable_values[variable.getId()] = get_value_of_variable_model_xml_targets(variable, model_etrees)
            new_value = calc_compute_model_change_new_value(change, variable_values=variable_values, range_values=current_range_values)
            if new_value == int(new_value):
                new_value = str(int(new_value))
            else:
                new_value = str(new_value)
            if change.isSetSymbol ():
                raise NotImplementedError('Set value changes of symbols is not supported.')
            model = doc.getModel(change.getModelReference()).clone()
            model_language=model.getLanguage ()
            attr_change = change.clone()
            attr_change.setNewValue(new_value)
            model.addChange(attr_change)
            if is_model_language_encoded_in_xml(model_language):
                apply_changes_to_xml_model(model, model_etrees[change.getModelReference()], None, None)
            else:
                model.getListOfChanges().append(attr_change)
        # sort the sub-tasks
        sub_tasks = sorted(task.getListOfSubTasks (), key=lambda sub_task: sub_task.getOrder () )

        # execute the sub-tasks and record their results
        for i_sub_task, sub_task in enumerate(sub_tasks):
            itask=doc.getTask(sub_task.getTask ())

            if itask.isSedTask () :
                model = doc.getModel(itask.getModelReference())
                if is_model_language_encoded_in_xml(model.getLanguage ()):
                    original_model_source = model.getSource()
                    fid, tempSource = tempfile.mkstemp(suffix='.xml', dir=os.path.dirname(original_model_source))
                    model.setSource(tempSource)
                    os.close(fid)

                    model_etrees[model.getId()].write(model.getSource(),
                                                 xml_declaration=True,
                                                 encoding="utf-8",
                                                 standalone=False,
                                                 pretty_print=pretty_print_modified_xml_models)
                
                sub_task_var_results=exec_task(doc,task, model,working_dir,external_variables_info)           

                if is_model_language_encoded_in_xml(model.getLanguage ()):
                    os.remove(model.getSource())
                    model.setSource(original_model_source)

            elif itask.isRepeatedTask ():
                sub_task_var_results = exec_repeated_task(doc,task,working_dir,external_variables_info,
                                                          model_etrees=model_etrees,
                                                          pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                                                          )

            else:  # pragma: no cover: already validated by :obj:`get_first_last_models_executed_by_task`
                raise NotImplementedError('Tasks of type {} are not supported.'.format(sub_task.task.__class__.__name__))

            for var in task_vars:
                variable_results[var.getId()][i_main_range][i_sub_task] = sub_task_var_results.get(var.getId(), None)

    # shape results to consistent size
    arrays = []
    for var in task_vars:
        for i_main_range, _ in enumerate(main_range_values):
            for i_sub_task, sub_task in enumerate(sub_tasks):
                arrays.append(variable_results[var.getId()][i_main_range][i_sub_task])

    padded_arrays = pad_arrays_to_consistent_shapes(arrays)

    i_array = 0
    for var in task_vars:
        for i_main_range, _ in enumerate(main_range_values):
            for i_sub_task, sub_task in enumerate(sub_tasks):
                variable_results[var.getId()][i_main_range][i_sub_task] = padded_arrays[i_array]
                i_array += 1

        variable_results[var.getId()] = numpy.array(variable_results[var.getId()])

    # return the results of the task
    return variable_results

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

def exec_parameterEstimationTask( doc,task, original_model,model_etree, working_dir, model_base_dir,external_variables_info=[],external_variables_values=[]):

    cellml_model,issues=parse_model(original_model.getSource(), True)
    if not cellml_model:
        print('Model parsing failed!',issues)
        return None
    # analyse the model
    adjustableParameters_info,experimentReferences,lowerBound,upperBound,initial_value=get_adjustableParameters(doc,model_etree,task)
    for key,adjustableParameter_info in adjustableParameters_info.items():
        external_variables_info.append(adjustableParameter_info)

    analyser, issues =analyse_model_full(cellml_model,model_base_dir,external_variables_info)
    if not analyser:
        print('Model analysis failed!',issues)
        return None
    else:
        mtype=get_mtype(analyser)
        if mtype not in ['ode','algebraic']:
            print('Model type is not supported!')
            return None
    # write Python code
    full_path = model_base_dir+'/'+original_model.getId()+'.py'
    writePythonCode(analyser, full_path)
    try:
        module=load_module(full_path)
    except Exception as exception:
        print(exception)
        return None
    
    dict_algorithm=get_dict_algorithm(task.getAlgorithm())
    method, opt_parameters=get_KISAO_parameters_opt(dict_algorithm)

    dfDict={}
    for dataDescription in doc.getListOfDataDescriptions() :
        dfDict.update(get_dfDict_from_dataDescription(dataDescription, working_dir))
    
    fitExperiments=get_fit_experiments(doc,task,analyser, cellml_model,model_etree,dfDict)
    
    bounds=Bounds(lowerBound ,upperBound)

    res=minimize(objective_function, initial_value, args=(analyser, cellml_model, mtype, module, external_variables_info,external_variables_values,experimentReferences,fitExperiments), 
                 method=method,bounds=bounds, options=opt_parameters)

    return res

def objective_function(param_vals, analyser, cellml_model, mtype, module, external_variables_info,external_variables_values,experimentReferences,fitExperiments):
    residuals_sum=0
    a=external_variables_values+param_vals.tolist()
    external_module=External_module(analyser, cellml_model, external_variables_info,a)

    for i in range(len(experimentReferences)):
        for experimentReference in experimentReferences[i]:
            sim_setting=SimulationSettings()
            simulation_type=fitExperiments[experimentReference]['type']
            sim_setting.tspan=fitExperiments[experimentReference]['tspan']
            dict_algorithm=fitExperiments[experimentReference]['algorithm']
            sim_setting.method, sim_setting.integrator_parameters=get_KISAO_parameters(dict_algorithm)            
            fitness_info=fitExperiments[experimentReference]['fitness_info']
            parameters=fitExperiments[experimentReference]['parameters']
            observables=fitness_info[0]
            observables_weight=fitness_info[1]
            observables_exp=fitness_info[2]
        
        if simulation_type=='timeCourse':
            current_state=sim_TimeCourse(mtype, module, sim_setting, observables, external_module,current_state=None,parameters=parameters)
            sed_results = current_state[-1]
            residuals={}
            for key, value in sed_results.items():
                residuals[key]=value-observables_exp[key]
                residuals_sum+=numpy.sum(residuals[key]*observables_weight[key])
    
    return residuals_sum

def get_adjustableParameters(doc,model_etree,task):
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
            adjustableParameters_info[i]=(variable_info['component'],variable_info['name'])

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
    fitExperiments={}
    for fitExperiment in task.getListOfFitExperiments():
        if fitExperiment.getTypeAsString ()=='steadyState':
            simulation_type='steadyState'
        elif fitExperiment.getTypeAsString ()=='timeCourse':
            simulation_type='timeCourse'
        else:
            raise NotImplementedError('Experiment type {} is not supported!'.format(fitExperiment.getTypeAsString ()))
        fitExperiments[fitExperiment.getId()]={}
        fitExperiments[fitExperiment.getId()]['type']=simulation_type
        sed_algorithm = fitExperiment.getAlgorithm()
        fitExperiments[fitExperiment.getId()]['algorithm']=get_dict_algorithm(sed_algorithm)
        fitExperiments[fitExperiment.getId()]['tspan']=[]
        fitExperiments[fitExperiment.getId()]['parameters']={}
        observables_exp={}
        observables_weight={}
        observables_info={}

        for fitMapping in fitExperiment.getListOfFitMappings ():
            if fitMapping.getTypeAsString ()=='time':
                tspan=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                # should be 1D array
                if tspan.ndim>1:
                    raise ValueError('The time course {} is not 1D array!'.format(fitMapping.getDataSource()))
                else:
                    fitExperiments[fitExperiment.getId()]['tspan']=tspan

            elif fitMapping.getTypeAsString ()=='experimentalCondition':
                initial_value_=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
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
                        parameters_info = get_variable_info_CellML(sedVars,model_etree)
                    except ValueError as exception:
                        raise exception
                    try:
                        observables=get_observables(analyser, cellml_model, parameters_info)
                    except ValueError as exception:
                        raise exception                    
                    fitExperiments[fitExperiment.getId()]['parameters'].update(observables)
                    for sedVar in sedVars:
                        fitExperiments[fitExperiment.getId()]['parameters'][sedVar.getId()]['value']=initial_value                                       

            elif fitMapping.getTypeAsString ()=='observable':

                observable_exp=get_value_of_dataSource(doc, fitMapping.getDataSource(),dfDict)
                if observable_exp.ndim>1:
                    raise ValueError('The observable {} is not 1D array!'.format(fitMapping.getDataSource()))
                
                a=fitMapping.getTarget()
                dataGenerator=doc.getDataGenerator(fitMapping.getTarget())
                sedVars=get_variables_for_data_generator(dataGenerator)
                if len(sedVars)>1:
                    raise ValueError('The data generator {} has more than one variable!'.format(fitMapping.getTarget()))
                else:
                    try:
                        parameters_info = get_variable_info_CellML(sedVars,model_etree)
                    except ValueError as exception:
                        raise exception
                    try:
                        observables=get_observables(analyser, cellml_model, parameters_info)
                    except ValueError as exception:
                        raise exception  
                                      
                    observables_info.update(observables)
                key=list(observables.keys())[0]

                if fitMapping.isSetWeight():
                    weight=fitMapping.getWeight()
                    observables_weight.update({key:weight})
                elif fitMapping.isSetPointWeight ():
                    pointWeight=get_value_of_dataSource(doc, fitMapping.getPointWeight(),dfDict)
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
                raise NotImplementedError('Fit mapping type {} is not supported!'.format(fitMapping.getTypeAsString ()))
            
        fitExperiments[fitExperiment.getId()]['fitness_info']=(observables_info,observables_weight,observables_exp) 

    return fitExperiments   


def exec_report(report, variable_results, base_out_path, rel_out_path, formats, task):
    """ Execute a report, generating the data sets which are available

    Args:
        report (:obj:`Report`): report
        variable_results (:obj:`VariableResults`): result of each data generator
        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.getId()}.csv``

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv)
        task (:obj:`SedTask`): task

    Returns:
        :obj:`tuple`:

            * :obj:`dict`: results of the data sets, format is {data_set.id: numpy.ndarray}
            * :obj:`Status`: status
            * :obj:`Exception`: exception for failure
            * :obj:`bool`: whether :obj:`task` contribute a variable to the report
    Side effects:
        * writes the results of the report to a file
    """
    # calculate data generators
    data_generators_ids = set()
    doc=report.getSedDocument()
    for data_set in report.getListOfDataSets ():
        data_generators_ids.add(data_set.getDataReference ())
    
    data_generators = [doc.getDataGenerator(data_generator_id) for data_generator_id in data_generators_ids]

    data_gen_results, data_gen_statuses, data_gen_exceptions, task_contributes_to_report = calc_data_generators_results(
        data_generators, variable_results, task, make_shapes_consistent=True)

    # collect data sets
    data_set_results = {}

    running = False
    succeeded = True
    failed = False

    for data_set in report.getListOfDataSets ():
        data_gen_res = data_gen_results[data_set.getDataReference ()]
        data_set_results[data_set.getId()] = data_gen_res

        data_gen_status = data_gen_statuses[data_set.getDataReference ()]
        if data_gen_status == 'FAILED':
            failed = True
        if data_gen_status == 'SUCCEEDED':
            running = True
        else:
            succeeded = False

    for format in formats:
        writeReport(report, data_set_results, base_out_path, os.path.join(rel_out_path, report.getId()) if rel_out_path else report.getId(), format)

    if failed:
        status = 'FAILED'

    elif running:
        if succeeded:
            status = 'SUCCEEDED'
        else:
            status = 'RUNNING'	

    else:
        status = 'QUEUED'

    return data_set_results, status, data_gen_exceptions, task_contributes_to_report

def calc_data_generators_results(data_generators, variable_results,task, make_shapes_consistent=True):
    """ Calculator the values of a list of data generators

    Args:
        data_generators (:obj:`list` of :obj:`SedDataGenerator`): SED task
        variable_results (:obj:`VariableResults`): results of the SED variables involved in the data generators
        task (:obj:`SedTask`): SED task
        make_shapes_consistent (:obj:`bool`, optional): where to make the shapes of the data generators consistent
            (e.g., for concatenation into a table for a report)

    Returns:
        :obj:`tuple`:

            * :obj:`dict`: values of the data generators, format is {data_generator.id: numpy.ndarray}
            * :obj:`dict` of :obj:`str` to :obj:`Status`: dictionary that maps the id of each data generator to its status
            * :obj:`Exception`: exception for failures
            * :obj:`bool`: where the task contributes to any of the data generators
    """
    task_contributes_to_data_generators = False
    statuses = {}
    exceptions = []
    results = {}

    for data_gen in data_generators:
        vars_available = True
        vars_failed = False
        for variable in data_gen.getListOfVariables():
            if variable.getTaskReference () == task.getId():
                task_contributes_to_data_generators = True
            if variable.getId() in variable_results:
                if variable_results.get(variable.getId(), None) is None:
                    vars_available = False
                    vars_failed = True
            else:
                vars_available = False

        if vars_failed:
            status = 'FAILED'
            msg = 'Data generator {} cannot be calculated because its variables were not successfully produced.'.format(data_gen.getId())
            exceptions.append(ValueError(msg))
            result = None

        elif vars_available:
            try:
                result = calc_data_generator_results(data_gen, variable_results)
                status = 'SUCCEEDED'
            except Exception as exception:
                result = None
                exceptions.append(exception)
                status = 'FAILED'

        else:
            status = 'QUEUED'	
            result = None

        statuses[data_gen.getId()] = status
        results[data_gen.getId()] = result

    if make_shapes_consistent:
        arrays = results.values()
        consistent_arrays = pad_arrays_to_consistent_shapes(arrays)
        for data_gen_id, result in zip(results.keys(), consistent_arrays):
            results[data_gen_id] = result

    if exceptions:
        exception = ValueError('Some generators could not be produced:\n  - {}'.format(
            '\n  '.join(str(exception) for exception in exceptions)))
    else:
        exception = None

    return results, statuses, exception, task_contributes_to_data_generators

def calc_data_generator_results(data_generator, variable_results):
    """ Calculate the results of a data generator from the results of its variables

    Args:
        data_generator (:obj:`DataGenerator`): data generator
        variable_results (:obj:`VariableResults`): results for the variables of the data generator

    Returns:
        :obj:`numpy.ndarray`: result of data generator
    """
    var_shapes = set()
    max_shape = []
    for var in data_generator.getListOfVariables():
        var_res = variable_results[var.getId()]
        var_shape = var_res.shape
        if not var_shape and var_res.size:
            var_shape = (1,)
        var_shapes.add(var_shape)

        max_shape = max_shape + [1 if max_shape else 0] * (var_res.ndim - len(max_shape))
        for i_dim in range(var_res.ndim):
            max_shape[i_dim] = max(max_shape[i_dim], var_res.shape[i_dim])

    if len(var_shapes) > 1:
        print('Variables for data generator {} do not have consistent shapes'.format(data_generator.getId()),
             )

    compiled_math = compile_math(libsedml.formulaToString(data_generator.getMath()))

    workspace = {}
    for param in data_generator.getListOfParameters():
        workspace[param.getId()] = param.getValue()

    if not var_shapes:
        value = eval_math(libsedml.formulaToString(data_generator.getMath()), compiled_math, workspace)
        result = numpy.array(value)

    else:
        for aggregate_func in AGGREGATE_MATH_FUNCTIONS:
            if re.search(aggregate_func + r' *\(', libsedml.formulaToString(data_generator.getMath())):
                msg = 'Evaluation of aggregate mathematical functions such as `{}` is not supported.'.format(aggregate_func)
                raise NotImplementedError(msg)

        padded_var_shapes = []
        for var in data_generator.getListOfVariables():
            var_res = variable_results[var.getId()]
            padded_var_shapes.append(
                list(var_res.shape)
                + [1 if var_res.size else 0] * (len(max_shape) - var_res.ndim)
            )

        result = numpy.full(max_shape, numpy.nan)
        n_dims = result.ndim
        for i_el in range(result.size):
            el_indices = numpy.unravel_index(i_el, result.shape)

            vars_available = True
            for var, padded_shape in zip(data_generator.getListOfVariables(), padded_var_shapes):
                var_res = variable_results[var.getId()]
                if var_res.ndim == 0:
                    if i_el == 0 and var_res.size:
                        workspace[var.getId()] = var_res.tolist()
                    else:
                        vars_available = False
                        break

                else:
                    for x, y in zip(padded_shape, el_indices):
                        if (y + 1) > x:
                            vars_available = False
                            break
                    if not vars_available:
                        break

                    workspace[var.getId()] = var_res[el_indices[0:var_res.ndim]]

            if not vars_available:
                continue

            result_el = eval_math(libsedml.formulaToString(data_generator.getMath()), compiled_math, workspace)

            if n_dims == 0:
                result = numpy.array(result_el)
            else:
                result.flat[i_el] = result_el

    return result

class ModelLanguagePattern(str, enum.Enum):
    """ Model language """
    CellML = r'^urn:sedml:language:cellml(\.\d+_\d+)?$'
    SBML = r'^urn:sedml:language:sbml(\.level\-\d+\.version\-\d+)?$'

def is_model_language_encoded_in_xml(language):
    """ Determine if the model language is encoded in XML. Note: only CellML and SBML are supported.

    Args:
        language (:obj:`str`): language

    Returns:
        :obj:`bool`: :obj:`True`, if the model language is encoded in XML
    """
    return (
        language and (
            re.match(ModelLanguagePattern.CellML, language)
            or re.match(ModelLanguagePattern.SBML, language)
        )
    )

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

def resolve_model(model, sed_doc, working_dir):
    """ Resolve the source of a model

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`str`: temporary path to the source of the modified model, if the model needed to be resolved from
    """
    source = model.getSource () 

    if source.lower().startswith('urn:'):
        if source.lower().startswith('urn:miriam:biomodels.db:'):
            biomodels_id = source.lower().replace('urn:miriam:biomodels.db:', '')
            url = BIOMODELS_DOWNLOAD_ENDPOINT.format(biomodels_id, biomodels_id)
            response = requests.get(url)
            try:
                response.raise_for_status()
            except Exception:
                raise ValueError('Model `{}` could not be downloaded from BioModels.'.format(biomodels_id))

            temp_file, temp_model_source = tempfile.mkstemp()
            os.close(temp_file)
            with open(temp_model_source, 'wb') as file:
                file.write(response.content)
        else:
            raise NotImplementedError('URN model source `{}` could be resolved.'.format(source))

        return temp_model_source

    elif re.match(r'^http(s)?://', source, re.IGNORECASE):
        response = requests.get(source)
        try:
            response.raise_for_status()
        except Exception:
            raise ValueError('Model could not be downloaded from `{}`.'.format(source))

        temp_file, temp_model_source = tempfile.mkstemp()
        os.close(temp_file)
        with open(temp_model_source, 'wb') as file:
            file.write(response.content)

        return temp_model_source

    elif source.startswith('#'):
        other_model_id = source[1:]
        models=[sed_doc.getModel(i) for i in range(sed_doc.getNumModels())]
        other_model = next((m for m in models if m.getId() == other_model_id), None)
        if other_model is None:
            raise ValueError('Relative model source `{}` does not exist.'.format(source))
        return resolve_model(other_model, sed_doc, working_dir)

    else:
        if os.path.isabs(source):
            pass
        else:
            model.setSource(os.path.join(working_dir, source)) 

        if not os.path.isfile(model.getSource()):
            raise FileNotFoundError('Model source file `{}` does not exist.'.format(source))

        return None


def resolve_model_and_apply_xml_changes(orig_model, sed_doc, working_dir,
                                        apply_xml_model_changes=True, save_to_file=True,
                                        ):
    """ Resolve the source of a model and, optionally, apply XML changes to the model.

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        save_to_file (:obj:`bool`): whether to save the resolved/modified model to a file       

    Returns:
        :obj:`tuple`:

            * :obj:`Model`: modified model
            * :obj:`str`: temporary path to the source of the modified model, if the model needed to be resolved from
              a remote source of modified
            * :obj:`etree._Element`: element tree for the resolved/modified model
    """
    model = orig_model.clone()
    # resolve model
    temp_model_source = resolve_model(model, sed_doc, working_dir)

    # apply changes to model
    if apply_xml_model_changes and model.isSetLanguage() and is_model_language_encoded_in_xml(model.getLanguage ()):
        # read model from file
        try:
            model_etree = etree.parse(model.getSource())
        except Exception as exception:
            raise ValueError('The model could not be parsed because the model is not a valid XML document: {}'.format(str(exception)))

        if model.getListOfChanges () :
            # Change source here so that tasks point to actual source they can find.
            orig_model.setSource(model.getSource())
            orig_model.getListOfChanges ().clear()
            for change in model.getListOfChanges ():
                orig_model.addChange(change)
            # apply changes
            apply_changes_to_xml_model(model, model_etree, sed_doc, working_dir)
            model.getListOfChanges ().clear()

            # write model to file
            if save_to_file:
                if temp_model_source is None:
                    modified_model_file, temp_model_source = tempfile.mkstemp(suffix='.xml', dir=os.path.dirname(model.getSource()))
                    os.close(modified_model_file)
                    model.setSource(temp_model_source)

                model_etree.write(model.getSource(),
                                  xml_declaration=True,
                                  encoding="utf-8",
                                  standalone=False,
                                  )
    else:
        model_etree = None

    return model, temp_model_source, model_etree

def apply_changes_to_xml_model(model, model_etree,sed_doc=None, working_dir=None,
                               variable_values=None, range_values=None, validate_unique_xml_targets=True):
    """ Modify an XML-encoded model according to a model change
    Args:
        model (:obj:`Model`): model
        model_etree (:obj:`etree._ElementTree`): element tree for model
        sed_doc (:obj:`SedDocument`, optional): parent SED document; used to resolve sources defined by reference to other models;
            required for compute changes
        working_dir (:obj:`str`, optional): working directory of the SED document (path relative to which models are located);
            required for compute changes
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change
        range_values (:obj:`dict`, optional): dictionary which contains the value of each range of each
            set value compute model change
        validate_unique_xml_targets (:obj:`bool`, optional): whether to validate the XML targets match
            uniue objects
    """

    # First pass:  Must-be-XML changes:
    non_xml_changes = []
    for change in model.getListOfChanges ():
        if change.isSedChangeAttribute():
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                # change.setModelReference(model.getId())
                non_xml_changes.append(change)
                continue
            # get object to change
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                raise NotImplementedError('target ' + change.getTarget () + ' cannot be changed by XML manipulation, as the target '
                                          'is not an attribute of a model element')
            objs = eval_xpath(model_etree, obj_xpath, CELLML2NAMESPACE)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            ns_prefix, _, attr = attr.rpartition(':')
            if ns_prefix:
                ns = CELLML2NAMESPACE.get(ns_prefix, None)
                if ns is None:
                    raise ValueError('No namespace is defined with prefix `{}`'.format(ns_prefix))
                attr = '{{{}}}{}'.format(ns, attr)

            # change value
            for obj in objs:
                obj.set(attr, change.getNewValue () )
        elif change.isSedComputeChange ():
            if variable_values is None:
                model_etrees = {model.getId(): model_etree}
                iter_variable_values = get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir)
            else:
                iter_variable_values = variable_values

            # calculate new value
            new_value = calc_compute_model_change_new_value(change, variable_values=iter_variable_values, range_values=range_values)
            if new_value == int(new_value):
                new_value = str(int(new_value))
            else:
                new_value = str(new_value)

            # get object to change
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                # Save this for the next pass:
                # change.setModelReference(model.getId())
                change.setNewValue (new_value)
                non_xml_changes.append(change)
                continue
            objs = eval_xpath(model_etree, obj_xpath, CELLML2NAMESPACE)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            ns_prefix, _, attr = attr.rpartition(':')
            if ns_prefix:
                ns = CELLML2NAMESPACE.get(ns_prefix, None)
                if ns is None:
                    raise ValueError('No namespace is defined with prefix `{}`'.format(ns_prefix))
                attr = '{{{}}}{}'.format(ns, attr)

            # change value
            for obj in objs:
                obj.set(attr, new_value)
        else:
            raise NotImplementedError('Change{} of type {} is not supported.'.format(
                ' ' + change.getId() if change.getId() else '', change.getTypeCode ()))

    # Interlude:  set up the preprocessed task, if there's a set_value_executor
    preprocessed_task = None

    return preprocessed_task

def get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir):
    """ Get the values of the model variables of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): compute model change
        sed_doc (:obj:`SedDocument`): SED document
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): map from the ids of models to element
            trees of their sources
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`dict`: dictionary which contains the value of each variable of each
            compute model change
    """
    variable_values = {}
    for variable in change.getListOfVariables():
        variable_model = variable.model
        if variable_model.getId() not in model_etrees:
            copy_variable_model, temp_model_source, variable_model_etree= resolve_model_and_apply_xml_changes(
                variable_model, sed_doc, working_dir,
                apply_xml_model_changes=True,
                save_to_file=False)
            model_etrees[variable_model.getId()] = variable_model_etree

            if temp_model_source:
                os.remove(temp_model_source)

        variable_values[variable.getId()] = get_value_of_variable_model_xml_targets(variable, model_etrees)

    return variable_values

def get_models_referenced_by_task(doc,task):
    """ Get the models referenced from a task

    Args:
        task (:obj:`SedAbstractTask`): task

    Returns:
        :obj:`list` of :obj:`SedModel`: models
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
        raise NotImplementedError('Tasks of type `{}` are not supported.'.format(task.getTypeCode ()))
    
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

def resolve_range(range, model_etrees=None):
    """ Resolve the values of a range

    Args:
        range (:obj:`Range`): range
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): map from the ids of models to element
            trees of their sources; required to resolve variables of functional ranges

    Returns:
        :obj:`list` of :obj:`float`: values of the range

    Raises:
        :obj:`NotImplementedError`: if range isn't an instance of :obj:`UniformRange`, :obj:`VectorRange`,
            or :obj:`FunctionalRange`.
    """
    if range.isSedUniformRange ():
        if range.getType() == 'linear':
            return numpy.linspace(range.getStart(), range.getEnd(), range.getNumberofSteps() + 1).tolist()

        elif range.getType() == 'log':
            return numpy.logspace(numpy.log10(range.getStart()), numpy.log10(range.getEnd()), range.getNumberofSteps() + 1).tolist()

        else:
            raise NotImplementedError('UniformRanges of type `{}` are not supported.'.format(range.getType()))

    elif range.isSedVectorRange ():
        return range.getValues()

    elif range.isSedFunctionalRange ():
        # compile math
        compiled_math = compile_math(libsedml.formulaToString(range.getMath()))

        # setup workspace to evaluate math
        workspace = {}
        for param in range.getListOfParameters ():
            workspace[param.getId()] = param.getValue()

        for var in range.getListOfVariables ():
            if var.isSetSymbol ():
                raise NotImplementedError('Symbols are not supported for variables of functional ranges')
            if model_etrees[var.getModelReference()] is None:
                raise NotImplementedError('Functional ranges that involve variables of non-XML-encoded models are not supported.')
            workspace[var.getId()] = get_value_of_variable_model_xml_targets(var, model_etrees)

        # calculate the values of the range
        values = []
        for child_range_value in resolve_range(range.getRange(), model_etrees=model_etrees):
            workspace[range.getRange().getId()] = child_range_value

            value = eval_math(libsedml.formulaToString(range.getMath()), compiled_math, workspace)
            values.append(value)

        # return values
        return values

    else:
        raise NotImplementedError('Ranges of type `{}` are not supported.'.format(range.getTypeCode()))

def eval_xpath(element, xpath, namespaces):
    """ Get the object(s) at an XPath

    Args:
        element (:obj:`etree._ElementTree`): element tree
        xpath (:obj:`str`): XPath
        namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs

    Returns:
        :obj:`list` of :obj:`etree._ElementTree`: object(s) at the XPath
    """
    try:
        return element.xpath(xpath, namespaces=get_namespaces_with_prefixes(namespaces))
    except etree.XPathEvalError as exception:
        if namespaces:
            msg = 'XPath `{}` is invalid with these namespaces:\n  {}\n\n  {}'.format(
                xpath,
                '\n  '.join(' - {}: {}'.format(prefix, uri) for prefix, uri in namespaces.items()),
                exception.args[0].replace('\n', '\n  ')),
        else:
            msg = 'XPath `{}` is invalid without namespaces:\n\n  {}'.format(
                xpath, exception.args[0].replace('\n', '\n  ')),

        exception.args = (msg)
        raise

def get_namespaces_with_prefixes(namespaces):
    """ Get a dictionary of namespaces less namespaces that have no prefix

    Args:
        namespaces (:obj:`dict`): dictionary that maps prefixes of namespaces their URIs

    Returns:
        :obj:`dict`: dictionary that maps prefixes of namespaces their URIs
    """
    if None in namespaces:
        namespaces = dict(namespaces)
        namespaces.pop(None)
    return namespaces

def get_value_of_variable_model_xml_targets(variable, model_etrees):

    """ Get the value of a variable of a model

    Args:
        variable (:obj:`Variable`): variable
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): dictionary that maps the
            ids of models to paths to files which contain their XML definitions

    Returns:
        :obj:`float`: value
    Note: only support explicit model elements and concept references
    """
    if variable.unsetTarget (): # 
        raise NotImplementedError('Compute model change variable `{}` must have a target'.format(variable.getId()))

    if variable.getTarget ().startswith('#'):
        raise NotImplementedError('Variable references to data descriptions are not supported.')

    obj_xpath, sep, attr = variable.getTarget ().rpartition('/@')
    if sep != '/@':
        raise NotImplementedError('the value of target ' + variable.getTarget() +
                                  ' cannot be obtained by examining the XML, as the target is not an attribute of a model element')

    et = model_etrees[variable.getModelReference()]
    obj = eval_xpath(et, obj_xpath, CELLML2NAMESPACE)
    if len(obj) != 1:
        raise ValueError('xpath {} must match a single object in model {}'.format(obj_xpath, variable.getModelReference()))

    ns, _, attr = attr.rpartition(':')
    if ns:
        attr = '{{{}}}{}'.format(CELLML2NAMESPACE[ns], attr)

    value = obj[0].get(attr)
    if value is None:
        raise ValueError('Target `{}` is not defined in model `{}`.'.format(variable.getTarget (), variable.getModelReference()))
    try:
        value = float(value)
    except ValueError:
        raise ValueError('Target `{}` in model `{}` must be a float.'.format(variable.getTarget (), variable.getModelReference()))

    return value

def get_dfDict_from_dataDescription(dataDescription, working_dir):
    dfDict={}
    source = dataDescription.getSource ()
    if re.match(r'^http(s)?://', source, re.IGNORECASE):
        response = requests.get(source)
        try:
            response.raise_for_status()
        except Exception:
            raise ValueError('Model could not be downloaded from `{}`.'.format(source))

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
    dfDict[dataDescription.getId()]=df
    return dfDict

def get_value_of_dataSource(doc, dataSourceID,dfDict):
    
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
                    raise NotImplementedError('IndexSet is not supported.')
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
                            raise NotImplementedError('up to two slices supported')

                    if dim1_present and (not dim2_present): 
                        # get the value(s) at index=dim1_value or all values if dim1_value is not set then subdivide the values according to startIndex and endIndex   
                        if dim1_value:
                            value=df.iloc[[dim1_value]]
                        elif dim1_startIndex and dim1_endIndex:
                            value=df.iloc[dim1_startIndex:dim1_endIndex]
                        elif dim1_startIndex and (not dim1_endIndex):
                            value=df.iloc[dim1_startIndex:]
                        elif (not dim1_startIndex) and dim1_endIndex:
                            value=df.iloc[:dim1_endIndex]
                        else:
                            value=df
                        return value.to_numpy()
                    
                    elif dim2_present and (not dim1_present):
                        # get the value(s) of the column and then subdivide the values according to startIndex and endIndex
                        if dim2_value:
                            columnName=dim2_value
                            df_selected=df[columnName]
                            if dim2_startIndex and dim2_endIndex:
                                value=df_selected.iloc[dim2_startIndex:dim2_endIndex]
                            elif dim2_startIndex and (not dim2_endIndex):
                                value=df_selected.iloc[dim2_startIndex:]
                            elif (not dim2_startIndex) and dim2_endIndex:
                                value=df_selected.iloc[:dim2_endIndex]
                            else:
                                value=df_selected
                            return value.to_numpy()
                        
                    elif dim1_present and dim2_present:
                        # get a single value at index=dim1_value and column=dim2_value
                        columnName=dim2_value
                        df_selected=df[columnName]
                        if dim1_value:
                            df_selected=df_selected.iloc[[dim1_value]]
                        return df_selected.to_numpy()
                    else:
                        raise ValueError('Data source `{}` is not defined.'.format(dataSourceID))

                              
                                          
                       
    

                        
                            
                            
                        

                 
    




def calc_compute_model_change_new_value(setValue, variable_values=None, range_values=None):
    """ Calculate the new value of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): change
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change
        range_values (:obj:`dict`, optional): dictionary which contains the value of each range of each
            set value compute model change

    Returns:
        :obj:`float`: new value
    """
    compiled_math = compile_math(libsedml.formulaToString(setValue.getMath()))

    workspace = {}

    if setValue.isSetRange ():
        workspace[setValue.getRange ()] = range_values.get(setValue.getRange (), None)
        if workspace[setValue.getRange ()] is None:
            raise ValueError('Value of range `{}` is not defined.'.format(setValue.getRange ()))

    for param in setValue.getListOfParameters ():
        workspace[param.getId()] = param.getValue()

    for var in setValue.getListOfVariables ():
        workspace[var.getId()] = variable_values.get(var.getId(), None)
        if workspace[var.getId()] is None:
            raise ValueError('Value of variable `{}` is not defined.'.format(var.getId()))

    return eval_math(libsedml.formulaToString(setValue.getMath()), compiled_math, workspace)