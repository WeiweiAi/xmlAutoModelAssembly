from .sedCollector import get_models_referenced_by_task, get_variables_for_task, get_adjustableParameters, get_fit_experiments, get_df_from_dataDescription
from .sedModel_changes import resolve_model_and_apply_xml_changes, get_variable_info_CellML
from .sedEditor import get_dict_algorithm
from .optimiser import get_KISAO_parameters_opt
from .analyser import analyse_model_full, get_mtype,parse_model
from .coder import writePythonCode
from .simulator import getSimSettingFromSedSim, sim_UniformTimeCourse, get_observables, load_module, get_externals, SimSettings, get_KISAO_parameters, sim_TimeCourse
from .sedReporter import exec_report
import tempfile
import os
import sys
from scipy.optimize import minimize, Bounds
import numpy



def exec_task(doc,task,working_dir,model_base_dir,external_variables_info={},external_variables_values=[],current_state=None):
    """ Execute a SedTask.

    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    task: :obj:`SedTask`
        The task to be executed.
    working_dir: str
        working directory of the SED document (path relative to which models are located)
    model_base_dir: str
        The full path to the directory that import URLs (in the xml model) are relative to.
    external_variables_info: dict, optional
        The external variables to be specified, in the format of {id:{'component': , 'name': }}
    external_variables_values: list, optional
        The values of the external variables to be specified [value1, value2, ...]
    current_state: tuple, optional
        The format is (voi, states, rates, variables, current_index, sed_results)

    Returns
    -------
    tuple
        (tuple, dict)
        The current state of the simulation and the variable results of the task. 
        The format of the current state is (voi, states, rates, variables, current_index, sed_results)
        The format of the variable results is {sedVar_id: numpy.ndarray}
        numpy.ndarray is a 1D array of the variable values at each time point.   
    """

    # get the model
    original_models = get_models_referenced_by_task(doc,task)
    if len(original_models) != 1:
        raise RuntimeError('Task must reference exactly one model.')
    
    # get the variables recorded by the task
    task_vars = get_variables_for_task(doc, task)
    if len(task_vars) == 0:
        print('Task does not record any variables.')
        raise RuntimeError('Task does not record any variables.')
    # apply changes to the model if any
    try:
        temp_model, temp_model_source, model_etree = resolve_model_and_apply_xml_changes(original_models[0], doc, working_dir) # must set save_to_file=True
        cellml_model,parse_issues=parse_model(temp_model_source, True)
        # cleanup modified model sources
        os.remove(temp_model_source)
        if cellml_model:
            analyser, issues =analyse_model_full(cellml_model,model_base_dir,external_variables_info)
            if analyser:
                mtype=get_mtype(analyser)
                external_variable=get_externals(mtype,analyser, cellml_model, external_variables_info, external_variables_values)
                # write Python code to a temporary file
                tempfile_py, full_path = tempfile.mkstemp(suffix='.py', prefix=temp_model.getId()+"_", text=True)
                writePythonCode(analyser, full_path)
                module=load_module(full_path)
                os.close(tempfile_py)
                # and delete temporary file
                os.remove(full_path)

    except (ValueError,FileNotFoundError) as exception:
        print(exception)
        raise RuntimeError(exception)
    
    if not cellml_model:
        print('Model parsing failed!',parse_issues)
        raise RuntimeError('Model parsing failed!')
    if not analyser:
        print('Model analysis failed!',issues)
        raise RuntimeError('Model analysis failed!')           
    
    # get observables and simulation settings
    try:
        variables_info = get_variable_info_CellML(task_vars,model_etree)
        observables=get_observables(analyser,cellml_model,variables_info)
        sedSimulation=doc.getSimulation(task.getSimulationReference())
        sim_setting=getSimSettingFromSedSim(sedSimulation) 
    except ValueError as exception:
        print(exception)
        raise RuntimeError(exception) 
    
    if sim_setting.type=='UniformTimeCourse':
        try:
            current_state=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_variable, current_state,parameters={})
        except RuntimeError as exception:
            print(exception)
            raise RuntimeError(exception)
    else:
        raise RuntimeError('Simulation type not supported!')
    
    task_variable_results=current_state[-1]
    # check that the expected variables were recorded
    variable_results = {}
    if len(task_variable_results) > 0:
        for i,ivar in enumerate(task_vars):
            variable_results[ivar.getId()] = task_variable_results.get(ivar.getId(), None)            

    return current_state, variable_results

def report_task(doc,task, variable_results, base_out_path, rel_out_path, report_formats =['csv']):
    """ Generate the outputs of a SedTask.

    Parameters
    ----------
    doc: :obj:`SedDocument`
        An instance of SedDocument
    task: :obj:`SedTask`
        The task to be executed.
    variable_results: dict
        The variable results of the task. 
        The format of the variable results is {sedVar_id: numpy.ndarray}
        numpy.ndarray is a 1D array of the variable values at each time point.
    base_out_path: str
        The base path to the directory that output files are written to.
    rel_out_path: str
        The relative path to the directory that output files are written to.
         * CSV: directory in which to save outputs to files
            ``{base_out_path}/{rel_out_path}/{report.getId()}.csv``

    report_formats: list, optional
        The formats of the reports to be generated. Default: ['csv']
    
    Raises
    ------
    RuntimeError
        If some generators could not be produced.
    NotImplementedError
        If the output is not of type SedReport.

    Returns
    -------
    dict
        The results of the reports. 
        The format of the results is {sedReport_id: numpy.ndarray}
        numpy.ndarray is a 1D array of the report values at each time point.   
    """

    indent = 0
    listOfOutputs = doc.getListOfOutputs()
    report_results = {}

    task_contributes_to_output = False
        
    for i_output, output in enumerate(listOfOutputs):
        print('{}Generating output {}: `{}` ...'.format(' ' * 2 * (indent + 2), i_output + 1, output.getId()), end='')
        sys.stdout.flush()
        if output.isSedReport ():
            output_result, output_status, output_exception, task_contributes_to_report = exec_report(
                output, variable_results, base_out_path, rel_out_path,  report_formats, task)
            
            print(' {}'.format(output_status))
            if output_exception:
                print('{}'.format(output_exception))
                raise RuntimeError(output_exception)
            
            task_contributes_to_output = task_contributes_to_output or task_contributes_to_report   
        else:
            # only reports are supported for now
            raise NotImplementedError('Outputs of type {} are not supported.'.format(output.getTypeCode ()))
        if  output_result is not None:
            report_results[output.getId()] = output_result
    
    if not task_contributes_to_output:
        print('Task {} does not contribute to any outputs.'.format(task.getId()))

    return report_results

def exec_parameterEstimationTask( doc,task, working_dir, model_base_dir,external_variables_info=[],external_variables_values=[]):

    # get the model
    original_models = get_models_referenced_by_task(doc,task)
    if len(original_models) != 1:
        raise RuntimeError('Task must reference exactly one model.')
    
    # get the variables recorded by the task
    task_vars = get_variables_for_task(doc, task)
    if len(task_vars) == 0:
        print('Task does not record any variables.')
        raise RuntimeError('Task does not record any variables.')
    # apply changes to the model if any
    try:
        temp_model, temp_model_source, model_etree = resolve_model_and_apply_xml_changes(original_models[0], doc, working_dir) # must set save_to_file=True
        cellml_model,parse_issues=parse_model(temp_model_source, True)
        # cleanup modified model sources
        os.remove(temp_model_source)
        if cellml_model:
            adjustableParameters_info,experimentReferences,lowerBound,upperBound,initial_value=get_adjustableParameters(doc,model_etree,task)
            for key,adjustableParameter_info in adjustableParameters_info.items():
                external_variables_info.append(adjustableParameter_info)

            analyser, issues =analyse_model_full(cellml_model,model_base_dir,external_variables_info)
            if analyser:
                mtype=get_mtype(analyser)
                # write Python code to a temporary file
                _, full_path = tempfile.mkstemp(suffix='.py', prefix=temp_model.getId()+"_", text=True)
                writePythonCode(analyser, full_path)
                module=load_module(full_path)
                # and delete temporary file
                os.remove(full_path)

    except (ValueError,FileNotFoundError) as exception:
        print(exception)
        raise RuntimeError(exception)
    
    if not cellml_model:
        print('Model parsing failed!',parse_issues)
        raise RuntimeError('Model parsing failed!')
    if not analyser:
        print('Model analysis failed!',issues)
        raise RuntimeError('Model analysis failed!')  
    
    dict_algorithm=get_dict_algorithm(task.getAlgorithm())
    method, opt_parameters=get_KISAO_parameters_opt(dict_algorithm)

    dfDict={}
    for dataDescription in doc.getListOfDataDescriptions() :
        dfDict.update({dataDescription.getId():get_df_from_dataDescription(dataDescription, working_dir)})
    
    fitExperiments=get_fit_experiments(doc,task,analyser, cellml_model,model_etree,dfDict)
    
    bounds=Bounds(lowerBound ,upperBound)

    res=minimize(objective_function, initial_value, args=(analyser, cellml_model, mtype, module, external_variables_info,external_variables_values,experimentReferences,fitExperiments), 
                 method=method,bounds=bounds, options=opt_parameters)

    return res

def objective_function(param_vals, analyser, cellml_model, mtype, module, external_variables_info,external_variables_values,experimentReferences,fitExperiments):
    residuals_sum=0
    try:
        external_variable=get_externals(mtype,analyser, cellml_model, external_variables_info, external_variables_values)
    except ValueError as exception:
        print(exception)
        raise RuntimeError(exception)

    for i in range(len(experimentReferences)):
        for experimentReference in experimentReferences[i]:
            sim_setting=SimSettings()
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
            current_state=sim_TimeCourse(mtype, module, sim_setting, observables, external_variable,current_state=None,parameters=parameters)
            sed_results = current_state[-1]
            residuals={}
            for key, value in sed_results.items():
                residuals[key]=value-observables_exp[key]
                residuals_sum+=numpy.sum(residuals[key]*observables_weight[key])
    
    return residuals_sum

