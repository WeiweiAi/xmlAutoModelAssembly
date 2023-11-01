from scipy.integrate import ode
import numpy as np

# Modified from https://github.com/hsorby/cellsolver.git
# https://github.com/hsorby/cellsolver.git is licensed under Apache License 2.0

def create_sed_results(observables,N):
    """Create the results dictionary to hold the results
    Args:
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index}}
        N(:obj:'int'): the number of steps
    Returns:
        :obj:`dict`: the dictionary of array of results, the format is {id:numpy.ndarray}
    """       
    sed_results={}
    for id in observables.keys():
        sed_results.update({id: np.empty(N+1)})
    return sed_results

def _initialize_module_ode(module,external_variable=None,parameters={}):
    """Initialize the module with odes.
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_variable(:obj:'function'): the function to specify the external variables
        parameters(:obj:'dict'): the dictionary of parameters, the format is {id:{'name':'variable name','component':'component name','vtype':'state','value':value,'index':index}}
    Returns:    
        :obj:`tuple`:
            * :obj:`list`: the list of states
            * :obj:`list`: the list of rates
            * :obj:`list`: the list of variables
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
        else:
           variables[v['index']]=v['value']
    
    module.compute_computed_constants(variables)

    return states, rates, variables 

def _initialize_module_algebraic(module,external_variable=None,parameters={}):
    """Initialize the module with only algebra.
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_variable(:obj:'function'): the function to specify the external variables
        parameters(:obj:'dict'): the dictionary of parameters, the format is {id:{'name':'variable name','component':'component name','vtype':'state','value':value,'index':index}}
    Returns:
        :obj:`list`: the list of variables
    """       
    variables = module.create_variables_array()

    if external_variable:
        module.initialise_variables(variables,external_variable)
    else:
        module.initialise_variables(variables)
    
    for id, v in parameters.items():
        if v['type'] == 'constant' or v['type'] == 'computed_constant' and v['type'] == 'algebraic':
           variables[v['index']]=v['value']
           
    module.compute_computed_constants(variables) 

    return variables

def initialize_module(module,external_variable,mtype,observables,t0,N,parameters={}):
    """Initialize the module.
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_variable(:obj:'function'): the function to specify the external variables
        mtype(:obj:'str'): the type of the model, the value is either 'ode' or 'algebraic'
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index,'value':value}}
        t0(:obj:'float'): the initial time
        N(:obj:'int'): the number of steps
    Returns:
        :obj:`tuple`: the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
    """
    sed_results=create_sed_results(observables,N)
    if mtype=='ode':
        states, rates, variables=_initialize_module_ode(module,external_variable,parameters)
        current_state = (t0, states, rates, variables, 0,sed_results)
    elif mtype=='algebraic':
        variables=_initialize_module_algebraic(module,external_variable,parameters)
        current_state = (t0, None, None, variables, 0, sed_results)
    else:
        print('The model type {} is not supported!'.format(mtype))
        return False
    return current_state

def _update_rates(voi, states, rates, variables, module, external_variable=None):
    """ Update the module.
    Args:
        voi(:obj:'float'): the variable of integration
        states(:obj:'list'): the list of states
        rates(:obj:'list'): the list of rates
        variables(:obj:'list'): the list of variables
        module(:obj:'module'): the module imported from the generated Python code
        external_variable(:obj:'function'): the function to define the external variable
    Returns:
        side effect: the rates and variables are updated
        rates(:obj:'list'): the list of rates
    """
    if external_variable:
       module.compute_rates(voi, states, rates, variables,external_variable)
    else:
        module.compute_rates(voi, states, rates, variables)
    return rates    

def _update_variables(voi, states, rates, variables, module, external_variable=None):
    """ Update the module.
    Args:
        voi(:obj:'float'): the variable of integration
        states(:obj:'list'): the list of states
        rates(:obj:'list'): the list of rates
        variables(:obj:'list'): the list of variables
        module(:obj:'module'): the module imported from the generated Python code
        external_variable(:obj:'function'): the function to define the external variable
    Returns:
        side effect: the variables are updated
    """
    if external_variable:
       if states is None and rates is None:
           module.compute_variables(variables,external_variable)
       else:
           module.compute_variables(voi, states, rates, variables,external_variable)
    else:
        if states is None and rates is None:
            module.compute_variables(variables)
        else:
            module.compute_variables(voi, states, rates, variables)

def _append_current_results(index, voi, states, variables, observables,sed_results):
    """ Append the current results to the results.
    Args:
        index(:obj:'int'): the index of the current result
        voi(:obj:'float'): the variable of integration
        states(:obj:'list'): the list of states
        variables(:obj:'list'): the list of variables
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index}}
        sed_results(:obj:'dict'): the dictionary of array of results, the format is {id:numpy.ndarray}
    Returns:
        side effect: the current results are appended to the results
    """
    for id, v in observables.items():
        if v['type'] == 'variable_of_integration':
            #print("voi = {}".format(voi))
            sed_results[id][index] = voi
        elif v['type'] == 'state':
            sed_results[id][index] = states[v['index']]
        else:
            sed_results[id][index] = variables[v['index']]

def solve_euler(module, external_update, observables, current_state, output_start_time,output_end_time,number_of_steps,step_size=None):
    """ Euler method solver.	
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_update(:obj:'function'): the function to update the external variables
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index}}
        current_state(:obj:'tuple'): the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
        step_size(:obj:'float'): the step size of the integration
    Returns:
        :obj:`tuple`: the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
    """	
    output_step_size = (output_end_time - output_start_time) / number_of_steps
    if step_size is None:
        step_size = output_step_size
        
    voi, states, rates, variables, current_index, sed_results = current_state

    n=abs((output_start_time-voi)/step_size)
    for i in range(int(n)):
        rates=_update_rates(voi, states,  rates, variables, module, external_update)
        delta = list(map(lambda var: var * step_size, rates))
        states = [sum(x) for x in zip(states, delta)]
        voi += step_size
    
    _update_variables(voi, states, rates, variables, module, external_update)
    # save observables
    _append_current_results(current_index, voi, states, variables,  observables, sed_results)
    
    if output_step_size > step_size:
        n = output_step_size/step_size
    else:
        n=1

    for i in range(int(number_of_steps)):
        for j in range(int(n)):
            rates=_update_rates(voi, states,  rates, variables, module, external_update)
            delta = list(map(lambda var: var * step_size, rates))
            states = [sum(x) for x in zip(states, delta)]
            voi += step_size
        
        _update_variables(voi, states, rates, variables, module, external_update)
        # save observables
        current_index = current_index+1
        _append_current_results(current_index, voi, states, variables,  observables, sed_results)

    current_state = (voi, states, rates, variables, current_index, sed_results)

    return current_state

def solve_scipy(module, external_update, observables, current_state, output_start_time,output_end_time,number_of_steps,method,integrator_parameters):
    """ Scipy supported solvers.
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_update(:obj:'function'): the function to update the external variables
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index}}
        current_state(:obj:'tuple'): the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
        integrator_parameters(:obj:'dict'): the dictionary of the parameters of the integrator
    Returns:
        :obj:`tuple`: the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
    """
    voi, states, rates, variables, current_index, sed_results = current_state

    output_step_size = (output_end_time - output_start_time) / number_of_steps
    # Set the initial conditions and parameters
    solver = ode(_update_rates)
    solver.set_initial_value(states, voi)
    solver.set_f_params(rates, variables, module, external_update)
    solver.set_integrator(method, **integrator_parameters)
    
    # integrate to the output start point
    n = abs((voi - output_start_time) / output_step_size)
    for i in range(int(n)):
        solver.integrate(solver.t + output_step_size)
        if not solver.successful():
            raise ValueError('scipy.integrate.ode failed.') 
               
    _update_variables( solver.t, solver.y, rates, variables, module, external_update)
    # save observables
    _append_current_results(current_index, solver.t, solver.y, variables, observables, sed_results)

    for i in range(number_of_steps):
       solver.integrate(solver.t + output_step_size)
       if not solver.successful():
           raise ValueError('scipy.integrate.ode failed.')
       _update_variables( solver.t, solver.y, rates, variables, module, external_update)
       # save observables
       current_index = current_index + 1
       _append_current_results(current_index, solver.t, solver.y, variables, observables, sed_results)
    
    current_state = (solver.t, solver.y, rates, variables, current_index, sed_results)
    return current_state


def algebra_evaluation(module, external_update, observables,current_state, number_of_steps):
    """ Algebraic evaluation.
    Args:
        module(:obj:'module'): the module imported from the generated Python code
        external_update(:obj:'function'): the function to update the external variables
        observables(:obj:'dict'): the dictionary of observables, the format is 
                                  {id:{'name':'variable name','component':'component name','vtype':'state','index':index}}
        current_state(:obj:'tuple'): the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
        number_of_steps(:obj:'int'): the number of steps
    Returns:
        :obj:`tuple`: the tuple of the current state, the format is (voi, states, rates, variables, current_index, sed_results)
    """

    voi, states, rates, variables, current_index, sed_results = current_state

    _update_variables( 0, None, None, variables, module, external_update)
    _append_current_results(current_index, 0, None, variables, observables, sed_results)

    for i in range(number_of_steps):
        current_index = current_index + 1
        _append_current_results(current_index, 0, None, variables, observables, sed_results)

    current_state = (voi, states, rates, variables, current_index, sed_results)
   
    return current_state


