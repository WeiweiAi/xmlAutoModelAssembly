
import numpy
import copy
import sys
import datetime

from .reporter import pad_arrays_to_consistent_shapes, writeReport
from.solver import load_module,get_observables,get_externals
from.analyser import analyse_model_full,parse_model, get_mtype
from.coder import writePythonCode
from.simulator import sim_UniformTimeCourse,getSimSettingFromDict,sim_TimeCourse,SimSettings,get_KISAO_parameters
from .optimiser import get_KISAO_parameters_opt
from .sedEditor import get_dict_simulation, get_dict_algorithm
from scipy.optimize import minimize, Bounds



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
        external_variable=get_externals(mtype,analyser, cellml_model, external_variables_info, external_variables_values)
    except ValueError as exception:
        print(exception)
        raise RuntimeError(exception)
    # execute simulation    
    if dict_simulation['type']=='UniformTimeCourse':
        if current_state:
            try:
                task_variable_results=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_variable,current_state)[-1]
            except Exception as exception:
                print(exception)
                raise RuntimeError(exception)
        else:
            try:
                task_variable_results=sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_variable)[-1]
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


    





 

