from scipy.integrate import ode
import numpy as np
from pathlib import PurePath
import importlib.util
import os
from libcellml import AnalyserVariable

"""
======
Solver
======
The solver module provides the functionality to solve a system.
The system is given as a python module generated from a CellML model.
The python module is assumed to be generated using libCellML (version 0.5.0).
The system can be either ODE or algebraic equations.
The system can be solved using Euler method or scipy supported solvers.
The code is modified from
https://github.com/hsorby/cellsolver.git, which is licensed under Apache License 2.0.

The solver module provides the following functions:
    * load_module - load a module from a file.
    * create_sed_results - create a dictionary to hold the simulation results for each observable.
    * initialize_module - initialize a module based on the given model type and parameters.
    * solve_euler - Euler method solver.
    * solve_scipy - scipy supported solvers.
    * algebra_evaluation - algebraic evaluation.
    * get_externals - get the external variable function for the model.
    * get_observables - get the observables information for the simulation.

"""

def load_module(full_path):
    """ Load a module from a file.

    Parameters
    ----------
    full_path : str
        The full path to the file containing the module.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
        If the module cannot be loaded.

    Returns
    -------
    object
        The loaded module.    
    """

    if not os.path.isfile(full_path):
        raise FileNotFoundError('Model source file `{}` does not exist.'.format(full_path))
    
    module_name = PurePath(full_path).stem
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec is None:
        raise FileNotFoundError('Unable to load module `{}`.'.format(module_name))    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def create_sed_results(observables, N):
    """
    Create a dictionary to hold the simulation results for each observable.

    Parameters
    ----------
    observables : dict
        A dictionary containing the observables to be recorded.
    N : int
        The number of time points to simulate.

    Returns
    -------
    dict
        A dictionary to hold the simulation results for each observable.
        The dictionary is of the form {id: numpy.ndarray} where id is the
        identifier of the observable and the numpy.ndarray is of size N+1.
    """
    
    sed_results = {}
    for id in observables.keys():
        sed_results.update({id: np.empty(N+1)})
    return sed_results

def _initialize_module_ode(module, external_variable=None, parameters={}):
    """
    Initialize the module with ODEs.

    Parameters
    ----------
    module : object
        The module to be initialized.
    external_variable : object, optional
        The function to specify external variable.
    parameters : dict, optional
        The information to modify the parameters. 
        The format is {id:{'name':'variable name','component':'component name',
        'vtype':'state','value':value,'index':index}}
    
    Raises
    ------
    ValueError
        If the initial value of voi or external variable is specified in the parameters, 
        a ValueError will be raised.
        
    Returns
    -------
    tuple
        A tuple containing the initialized states, rates, and variables.

    Notes
    -----
    If the initial value of a state variable is specified in the parameters, 
    the initial value may not be modified accordingly.
    """
    rates = module.create_states_array()
    states = module.create_states_array()
    variables = module.create_variables_array()

    if external_variable:
        module.initialise_variables(states, rates, variables,external_variable)
    else:    
       module.initialise_variables(states, rates, variables)
    
    for id, v in parameters.items():
        if v['type'] == 'state':
            states[v['index']]=v['value']
        elif v['type'] == 'constant' or v['type'] == 'computed_constant' and v['type'] == 'algebraic':
           variables[v['index']]=v['value']
        elif v['type'] == 'variable_of_integration' or v['type'] == 'external':
            raise ValueError('The initial value of voi or external variable cannot be modified!')
        else:
            raise ValueError('The parameter type {} of is not supported!'.format(v['type']))
    
    module.compute_computed_constants(variables)

    return states, rates, variables

def _initialize_module_algebraic(module,external_variable=None,parameters={}):
    """
    Initialize the module with only algebraic equations.

    Parameters
    ----------
    module : object
        The module to be initialized.
    external_variable : object, optional
        The function to specify external variable.
    parameters : dict, optional
        The information to modify the parameters. 
        The format is {id:{'name':'variable name','component':'component name',
        'vtype':'state','value':value,'index':index}}
    
    Raises
    ------
    ValueError
        If other types of variables are specified in the parameters, 
        a ValueError will be raised.
    
    Returns
    -------
    list
        A list containing the initialized variables.
    """       
    variables = module.create_variables_array()

    if external_variable:
        module.initialise_variables(variables,external_variable)
    else:
        module.initialise_variables(variables)
    
    for id, v in parameters.items():
        if v['type'] == 'constant' or v['type'] == 'computed_constant' and v['type'] == 'algebraic':
           variables[v['index']]=v['value']
        else:
            raise ValueError('The parameter type {} is not supported!'.format(v['type']))
           
    module.compute_computed_constants(variables) 

    return variables

def initialize_module(mtype, observables, N, module, voi=0, external_variable=None, parameters={}):
    """
    Initializes a module based on the given model type and parameters.

    Parameters
    ----------
    mtype : str
        The type of model to initialize ('ode' or 'algebraic').
    observables : dict
        A dictionary containing the observables to be recorded.
    N : int
        The number of simulation steps.
    module : object
        The module to initialize.
    voi : float, optional
        The initial value of the variable of integration. Defaults to 0.
    external_variable : object, optional
        The function to specify external variable.
    parameters : dict, optional
        The information to modify the parameters. 
        The format is {id:{'name':'variable name','component':'component name',
        'vtype':'state','value':value,'index':index}}
    
    Raises
    ------
    ValueError
        If the initial value of voi or external variable is specified in the parameters, 
        a ValueError will be raised.

    Returns
    -------
    tuple
        A tuple containing the current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    """
    sed_results=create_sed_results(observables, N)

    if mtype=='ode':
        try:
            states, rates, variables=_initialize_module_ode(module,external_variable,parameters)
        except ValueError as e:
            raise ValueError(e)         
        current_state = (voi, states, rates, variables, 0,sed_results)

    elif mtype=='algebraic':
        try:
            variables=_initialize_module_algebraic(module,external_variable,parameters)
        except ValueError as e:
            raise ValueError(e)
        current_state = (voi, None, None, variables, 0, sed_results)
    else:
        raise ValueError('The model type {} is not supported!'.format(mtype))
    
    return current_state

def _update_rates(voi, states, rates, variables, module, external_variable=None):
    """ Update the rates of the module.
    Parameters
    ----------
    voi : float
        The current value of the independent variable.
    states : list
        The current state of the system.
    rates : list
        The current rates of change of the system.
    variables : list
        The current variables of the system.
    module : object
        The module to update.
    external_variable : object, optional
        The function to specify external variable.

    Returns
    -------
    list
        The updated rates of change of the system.
    """
    if external_variable:
       module.compute_rates(voi, states, rates, variables,external_variable)
    else:
        module.compute_rates(voi, states, rates, variables)
    return rates    

def _update_variables(voi, states, rates, variables, module, external_variable=None):
    """ Update the variables of the module.
    
    Parameters
    ----------
    voi : float
        The current value of the independent variable.
    states : list
        The current state of the system.
    rates : list
        The current rates of change of the system.
    variables : list
        The current variables of the system.
    module : object
        The module to update.    
    external_variable : object, optional
        The function to specify external variable.

    Side effects
    ------------
    The variables of the module are updated.
    
    """
    if external_variable:
       if states is None and rates is None: # algebraic
           module.compute_variables(variables,external_variable)
       else:
           module.compute_variables(voi, states, rates, variables,external_variable)
    else:
        if states is None and rates is None:
            module.compute_variables(variables)
        else:
            module.compute_variables(voi, states, rates, variables)

def _append_current_results(sed_results, index, observables, voi, states, variables):
    """ Append the current results to the results.
    
    Parameters
    ----------
    sed_results : dict
        The dictionary of the simulation results.
    index : int
        The current index of the results.
    observables : dict
        The dictionary of the observables.
    voi : float
        The current value of the independent variable.
    states : list
        The current state of the system.
    variables : list
        The current variables of the system.

    Side effects
    ------------
    The current results are appended to the results.    
    """

    for id, v in observables.items():
        if v['type'] == 'variable_of_integration':
            sed_results[id][index] = voi
        elif v['type'] == 'state':
            sed_results[id][index] = states[v['index']]
        else:
            sed_results[id][index] = variables[v['index']]

def solve_euler(module, current_state, observables, output_start_time, output_end_time,
                number_of_steps, step_size=None, external_variable=None):
    """ Euler method solver.	
    
    Parameters
    ----------
    module : object
        The module to solve.
    current_state : tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    observables : dict
        The dictionary of the observables.
    output_start_time : float
        The start time of the output.
    output_end_time : float
        The end time of the output.
    number_of_steps : int
        The number of steps.
    step_size : float, optional
        The step size. Default is None.
        When step_size is None, the step size is calculated based on the 
        output_start_time, output_end_time, and number_of_steps.
    external_variable : object, optional
        The function to specify external variable. Default is None.

    Returns
    -------
    tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    """	

    output_step_size = (output_end_time - output_start_time) / number_of_steps
    if step_size is None:
        step_size = output_step_size
        
    voi, states, rates, variables, current_index, sed_results = current_state
    # integrate to the output start point
    n=abs((output_start_time-voi)/step_size)
    for i in range(int(n)):
        rates=_update_rates(voi, states,  rates, variables, module, external_variable)
        delta = list(map(lambda var: var * step_size, rates))
        states = [sum(x) for x in zip(states, delta)]
        voi += step_size
    
    _update_variables( voi, states, rates, variables, module, external_variable)
    # save observables
    _append_current_results(sed_results, current_index, observables, voi, states, variables)
    
    # integrate to the output end point
    if output_step_size > step_size:
        n = output_step_size/step_size
    else:
        n=1
    for i in range(int(number_of_steps)):
        for j in range(int(n)):
            rates=_update_rates( voi, states,  rates, variables, module, external_variable)
            delta = list(map(lambda var: var * step_size, rates))
            states = [sum(x) for x in zip(states, delta)]
            voi += step_size
        
        _update_variables(voi, states, rates, variables, module, external_variable)
        # save observables
        current_index = current_index+1
        _append_current_results(sed_results, current_index, observables, voi, states, variables)

    current_state = (voi, states, rates, variables, current_index, sed_results)

    return current_state

def solve_scipy(module, current_state, observables, output_start_time, output_end_time,
                number_of_steps, method, integrator_parameters, external_variable=None):
    """ Scipy supported solvers.

    Parameters
    ----------
    module : object
        The module to solve.
    current_state : tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    observables : dict
        The dictionary of the observables.
    output_start_time : float
        The start time of the output.
    output_end_time : float
        The end time of the output.
    number_of_steps : int
        The number of steps.
    method : str
        The name of the integrator.
    integrator_parameters : dict
        The parameters of the integrator.
    external_variable : object, optional
        The function to specify external variable. Default is None.

    Raises
    ------
    RuntimeError
        If the scipy.integrate.ode failed, a RuntimeError will be raised.

    Returns
    -------
    tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).    
    """

    voi, states, rates, variables, current_index, sed_results = current_state
    output_step_size = (output_end_time - output_start_time) / number_of_steps
    # Set the initial conditions and parameters
    solver = ode(_update_rates)
    solver.set_initial_value(states, voi)
    solver.set_f_params(rates, variables, module, external_variable)
    solver.set_integrator(method, **integrator_parameters)
    
    # integrate to the output start point
    n = abs((voi - output_start_time) / output_step_size)
    for i in range(int(n)):
        solver.integrate(solver.t + output_step_size)
        if not solver.successful():
            raise RuntimeError('scipy.integrate.ode failed.') 
               
    _update_variables(solver.t, solver.y, rates, variables, module, external_variable)
    # save observables
    _append_current_results(sed_results, current_index, observables, solver.t, solver.y, variables)
    # integrate to the output end point
    for i in range(number_of_steps):
       solver.integrate(solver.t + output_step_size)
       if not solver.successful():
           raise RuntimeError('scipy.integrate.ode failed.')
       _update_variables(solver.t, solver.y, rates, variables, module, external_variable)
       # save observables
       current_index = current_index + 1
       _append_current_results(sed_results, current_index, observables, solver.t, solver.y, variables)
    
    current_state = (solver.t, solver.y, rates, variables, current_index, sed_results)
    return current_state

def algebra_evaluation(module, current_state, observables, number_of_steps, external_variable=None):
    """ Algebraic evaluation.
    
    Parameters
    ----------
    module : object
        The module to solve.
    current_state : tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    observables : dict
        The dictionary of the observables.
    number_of_steps : int
        The number of steps.
    external_variable : object, optional
        The function to specify external variable. Default is None.

    Returns
    -------
    tuple
        The current state of the module.
        The format is (voi, states, rates, variables, current_index, sed_results).
    """

    voi, states, rates, variables, current_index, sed_results = current_state

    _update_variables(0, None, None, variables, module, external_variable)
    _append_current_results(sed_results, current_index, observables, 0, None, variables)

    for i in range(number_of_steps):
        current_index = current_index + 1
        _append_current_results(sed_results, current_index, observables, 0, None, variables)

    current_state = (voi, states, rates, variables, current_index, sed_results)
   
    return current_state

class External_module:
    """ Class to define the external module.

    Attributes
    ----------
    param_indices: list
        The indices of the variable in the generated python module.
    param_vals: list
        The values of the variables given by the external module .

    Methods
    -------
    external_variable_algebraic(variables,index)
        Define the external variable function for algebraic type model.
    external_variable_ode(voi, states, rates, variables,index)
        Define the external variable function for ode type model.  
    
    Notes
    -----
    This class only allows the model to take inputs, 
    while the inputs do not depend on the model variables.
        
    """
    def __init__(self, param_indices, param_vals):
        """

         Parameters
         ----------
         param_indices: list
             The indices of the variable in the generated python module.
         param_vals: list
             The values of the variables given by the external module .
             
        """
        self.param_vals = param_vals
        self.param_indices = param_indices 

    def external_variable_algebraic(self, variables,index):
        return self.param_vals[self.param_indices.index(index)]

    def external_variable_ode(self,voi, states, rates, variables,index):
        return self.param_vals[self.param_indices.index(index)]
          
def get_externals(mtype,analyser, cellml_model, external_variables_info, external_variables_values):
    """ Get the external variable function for the model.

    Parameters
    ----------
    mtype: str
        The type of the model.
    analyser: Analyser
        The Analyser instance of the CellML model.
    cellml_model: Model
        The CellML model.
    external_variables_info: dict
        The external variables to be specified, in the format of {id:{'component': , 'name': }}.
    external_variables_values: list
        The values of the external variables.
    
    Raises
    ------
    ValueError
        If the number of external variables does not match the number of external variables values.
        If the model type is not supported.
        If a variable is not found in the model.

    Returns
    -------
    function
        The external variable function for the model.
    """
    # specify external variables
    try:
        param_indices=_get_variable_indices(analyser, cellml_model,external_variables_info)
    except ValueError as exception:
        print(exception)
        raise ValueError(exception)
    
    if len(param_indices)!=len(external_variables_values):
        raise ValueError("The number of external variables does not match the number of external variables values!")

    if len(param_indices)==0:
        external_variable= None
    else:
        external_module=External_module(param_indices,external_variables_values)
        if mtype=='algebraic':
            external_variable=external_module.external_variable_algebraic
        elif mtype=='ode':
            external_variable=external_module.external_variable_ode
        else:
            raise ValueError("The model type {} is not supported!".format(mtype))
       
    return external_variable

def get_observables(analyser, model, variables_info):
    """
    Get the observables information for the simulation
    based on variables_info {id:{'component': , 'name': }}.
    
    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.
    model: Model
        The CellML model.
    variables_info: dict
        The variables to be observed, 
        in the format of {id:{'component': , 'name': }}.

    Raises
    ------
    ValueError
        If a variable is not found in the model.

    Returns
    -------
    dict
        The observables of the simulation, 
        in the format of {id:{'name': , 'component': , 'index': , 'type': }}.
    """
    observables = {}
    for key,variable_info in variables_info.items():
        try:
            variable=_find_variable(model, variable_info['component'],variable_info['name'])
        except ValueError as err:
            print(str(err))
            raise
        
        index, vtype=_get_index_type_for_equivalent_variable(analyser,variable)
        if vtype != 'unknown':
            observables[key]={'name':variable_info['name'],'component':variable_info['component'],'index':index,'type':vtype}
        else:
            print("Unable to find a required variable in the generated code")
            raise ValueError("Unable to find a required variable in the generated code")
        
    return observables

def _get_index_type_for_variable(analyser, variable):
    """Get the index and type of a variable in the python module.
    
    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.
    variable: Variable
        The CellML variable.

    Returns
    -------
    tuple
        (int, str)
        The index and type of the variable.
        If the variable is not found, the index is -1 and the type is 'unknown'.
        The type can be 'algebraic', 'constant', 'computed_constant', 'external',
        'state' or 'variable_of_integration'.
    
    """
    analysedModel=analyser.model()
    for i in range(analysedModel.variableCount()):
        avar=analysedModel.variable(i)
        var=avar.variable()
        var_name=var.name()
        component_name=var.parent().name()
        if component_name==variable.parent().name() and var_name==variable.name():
            return avar.index(), AnalyserVariable.typeAsString(avar.type())
        
    for i in range(analysedModel.stateCount()):
        avar=analysedModel.state(i)
        var=avar.variable()
        var_name=var.name()
        component_name=var.parent().name()
        if component_name==variable.parent().name() and var_name==variable.name():
            return avar.index(), AnalyserVariable.typeAsString(avar.type())
        
    avar=analysedModel.voi()
    if avar:
        var=avar.variable()
        var_name=var.name()
        component_name=var.parent().name()
        if component_name==variable.parent().name() and var_name==variable.name():
            return avar.index(), AnalyserVariable.typeAsString(avar.type())  
          
    return -1, 'unknown'

def _get_index_type_for_equivalent_variable(analyser, variable):
    """Get the index and type of a variable in a module 
    by searching through equivalent variables.
    
    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.
    variable: Variable
        The CellML variable.

    Returns
    -------
    tuple
        (int, str)
        The index and type of the variable.
        If the variable is not found, the index is -1 and the type is 'unknown'.        
    """

    index, vtype = _get_index_type_for_variable(analyser,variable)
    if vtype != 'unknown':
        return index, vtype
    else:
        for i in range(variable.equivalentVariableCount()):
            eqv = variable.equivalentVariable(i)
            index, vtype = _get_index_type_for_variable(analyser, eqv)
            if vtype != 'unknown':
                return index, vtype
    return -1, 'unknown'

def _get_variable_indices(analyser, model, variables_info):
    """Get the indices of a list of variables in a model.
    
    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.
    model: Model
        The CellML model.
    variables_info: dict
        The variables information in the format of {id:{'component': , 'name': }}.

    Raises
    ------
    ValueError
        If a variable is not found in the model.

    Returns
    -------
    list
        The indices of the variables in the generated python module.

    Notes
    -----
    The indices should be in the same order as the variables in the dictionary.
    Hence, Python 3.6+ is required.
    """
    try:
        observables=get_observables(analyser, model, variables_info)
    except ValueError as err:
        print(str(err))
        raise 
    indices=[]
    for _,observable in observables.items():
        indices.append(observable['index'])

    return indices

def _find_variable(model, component_name, variable_name):
    """ Find a variable in a CellML model based on component name and variable name.
    
    Parameters
    ----------
    model: Model
        The CellML model.
    component_name: str
        The name of the component.
    variable_name: str
        The name of the variable.
    
    Raises
    ------
    ValueError
        If the variable is not found in the model.

    Returns
    -------
    Variable
        The CellML variable found in the model.
    """

    def _find_variable_component(component):
        if component.name()==component_name:
            for v in range(component.variableCount()):
                if component.variable(v).name()==variable_name:
                    return component.variable(v)            
        if component.componentCount()>0:
            for c in range(component.componentCount()):
                variable=_find_variable_component(component.component(c))
                if variable:
                    return variable
        return None
    
    for c in range(model.componentCount()):
        variable=_find_variable_component(model.component(c))
        if variable:
            return variable
        
    raise ValueError("Unable to find the variable {} in the component {} of the model".format(variable_name,component_name))