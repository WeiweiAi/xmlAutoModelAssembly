from .solver import solve_euler, solve_scipy, algebra_evaluation, initialize_module

"""
====================
The simulator module
====================
The simulator module provides the functions to simulate the model.

The module defines the following classes:
    * SimSettings - stores the simulation settings
The module defines the following functions:
    * getSimSettingFromDict - get the simulation settings from the dictionary of the simulation
    * sim_UniformTimeCourse - simulate the model with UniformTimeCourse setting
    * sim_TimeCourse - simulate the model with TimeCourse setting
    * get_KISAO_parameters - get the parameters of the KISAO algorithm
"""

# The supported methods of the integration

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.ode.html
SCIPY_SOLVERS = ['dopri5', 'dop853', 'VODE', 'LSODA']
KISAO_ALGORITHMS = {'KISAO:0000030': 'Euler forward method',
                    'KISAO:0000535': 'VODE',
                    'KISAO:0000536': 'ZVODE',
                    'KISAO:0000088': 'LSODA',
                    'KISAO:0000087': 'dopri5',
                    'KISAO:0000436': 'dop853',
                    }
class SimSettings():

    """ Dictionary that stores the simulation settings     
    
    Attributes
    ----------
    type : str
        The type of the simulation, the value can be
        'OneStep','UniformTimeCourse', 'SteadyState' or 'timeCourse'
    initial_time : float
        The initial time of the simulation
    output_start_time : float
        The start time of the output
    output_end_time : float
        The end time of the output
    number_of_steps : int
        The number of steps
    step : float
        The step size
    tspan : list
        The time span of the simulation
    method : str
        The method of the integration
    integrator_parameters : dict
        The parameters of the integrator
    """  

    def __init__(self):
        self.type='UniformTimeCourse'
        self.initial_time = 0
        self.output_start_time = 0
        self.output_end_time = 10
        self.number_of_steps = 1000
        self.step=0.1
        self.tspan=[]
        self.method='Euler forward method' 
        self.integrator_parameters={}       

def getSimSettingFromDict(dict_simulation):
    """Get the simulation settings from the dictionary of the simulation.

    Parameters
    ----------
    dict_simulation : dict
        The dictionary of the simulation
        If the type is 'OneStep', the format is {'type': 'OneStep', 'step': 0.1}
        If the type is 'UniformTimeCourse', the format is {'type': 'UniformTimeCourse',
        'initialTime': 0.0, 'outputStartTime': 0.0, 'outputEndTime': 10.0, 'numberOfSteps': 100}
        If the type is 'SteadyState', the format is {'type': 'SteadyState'}
    
    Raises
    ------
    ValueError
        If the type is not supported
        
    Returns
    -------
    :obj:`SimSettings`: the simulation settings
    """

    simSetting=SimSettings()
    simSetting.type=dict_simulation['type']
    if simSetting.type=='OneStep':
        simSetting.step=dict_simulation['step']
        simSetting.number_of_steps=1
    elif simSetting.type=='UniformTimeCourse':
        simSetting.initial_time=dict_simulation['initialTime']
        simSetting.output_start_time=dict_simulation['outputStartTime']
        simSetting.output_end_time=dict_simulation['outputEndTime']
        simSetting.number_of_steps=dict_simulation['numberOfSteps']
    elif simSetting.type=='SteadyState':
        simSetting.number_of_steps=1
    elif simSetting.type=='timeCourse':
        pass
    else:
        print('The simulation type {} is not supported!'.format(simSetting.type))
        raise ValueError('The simulation type {} is not supported!'.format(simSetting.type))    
    simSetting.method, simSetting.integrator_parameters=get_KISAO_parameters(dict_simulation['algorithm'])
    
    return simSetting


def sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_variable, current_state=None,parameters={}):
    """Simulate the model with UniformTimeCourse setting.
    
    Parameters
    ----------
    mtype : str
        The type of the model ('ode' or 'algebraic')
    module : module
        The module containing the Python code
    sim_setting : SimSettings
        The simulation settings
    observables : dict
        The observables of the simulation, the format is 
        {id:{'name': , 'component': , 'index': , 'type': }}
    external_variable : function
        The external variable function for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model

    Raises
    ------
    RuntimeError
        If the method is not supported
        If initialize_module fails
        If solve_scipy fails

    Returns
    -------
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)

    """

    if current_state is None:
        try:
            current_state=initialize_module(mtype,observables,sim_setting.number_of_steps,module,
                                            sim_setting.initial_time, external_variable,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e          

    output_step_size=(sim_setting.output_end_time-sim_setting.output_start_time)/sim_setting.number_of_steps

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=output_step_size  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            current_state=solve_euler(module, current_state, observables,
                                      sim_setting.output_start_time, sim_setting.output_end_time,sim_setting.number_of_steps,
                                      step_size,external_variable)            
        
        elif sim_setting.method in SCIPY_SOLVERS:
            try:
                current_state=solve_scipy(module, current_state, observables,
                                          sim_setting.output_start_time, sim_setting.output_end_time,sim_setting.number_of_steps,
                                          sim_setting.method,sim_setting.integrator_parameters,external_variable)
            except RuntimeError as e:
                raise e from e
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         sim_setting.number_of_steps,external_variable)
    else:
        print('The model type {} is not supported!'.format(mtype)) # should not reach here
        raise RuntimeError('The model type {} is not supported!'.format(mtype))
    
    return current_state

def sim_TimeCourse(mtype, module, sim_setting, observables, external_variable,current_state=None,parameters={}):
    """Simulate the model with TimeCourse setting.

    Parameters
    ----------
    mtype : str
        The type of the model ('ode' or 'algebraic')
    module : module
        The module containing the Python code
    sim_setting : SimSettings
        The simulation settings
    observables : dict
        The observables of the simulation, the format is {id:{'name': , 'component': , 'index': , 'type': }}
    external_variable : function
        The external variable function for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model
    
    Raises
    ------
    RuntimeError
        If the method is not supported
        If initialize_module fails
        If solve_scipy fails
        
    Returns
    -------
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    """
    
    number_of_steps=len(sim_setting.tspan)-1
            
    if current_state is None:
        try:
            current_state=initialize_module(mtype,observables,number_of_steps,module,
                                            0,external_variable,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e

    output_step_size=(sim_setting.tspan[-1]-sim_setting.tspan[0])/number_of_steps

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=output_step_size  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            for i in range(number_of_steps):
                current_state=solve_euler(module,current_state,observables,
                                          sim_setting.tspan[i],sim_setting.tspan[i+1],1,
                                          step_size,external_variable)                   
        elif sim_setting.method in SCIPY_SOLVERS:
            for i in range(number_of_steps):
                try:                      
                    current_state=solve_scipy(module,current_state,observables,
                                              sim_setting.tspan[i],sim_setting.tspan[i+1],1,
                                              sim_setting.method,sim_setting.integrator_parameters,external_variable)
                except RuntimeError as e:
                    raise e from e
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         number_of_steps,external_variable)
    else:
        print('The model type {} is not supported!'.format(mtype))
        raise RuntimeError('The model type {} is not supported!'.format(mtype))
    
    return current_state


def get_KISAO_parameters(algorithm):
    """Get the parameters of the KISAO algorithm.
    
    Parameters
    ----------
    algorithm : dict
        The dictionary of the KISAO algorithm
        Format: {'kisaoID': , 'name': , 'listOfAlgorithmParameters': [{'kisaoID': , 'name': , 'value': }]}
    
    Raises
    ------
    ValueError
        If the algorithm is not supported
        
    Returns
    -------
    method : str
        The method of the integration. 
        Now the supported methods are 'Euler forward method', 'VODE', 'LSODA', 'dopri5' and 'dop853'.
        None if the method is not supported.
    integrator_parameters : dict
        The parameters of the integrator
        None if the method is not supported.
    """

    if algorithm['kisaoID'] == 'KISAO:0000030':
        # Euler forward method
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]
        integrator_parameters = {}
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000483':
                integrator_parameters['step_size'] = float(p['value'])

    elif algorithm['kisaoID'] == 'KISAO:0000535':
            # VODE
            method = KISAO_ALGORITHMS[algorithm['kisaoID']]
            integrator_parameters = {}
            for p in algorithm['listOfAlgorithmParameters']:
                if p['kisaoID'] == 'KISAO:0000209':
                    integrator_parameters['rtol'] = float(p['value'])
                elif p['kisaoID'] == 'KISAO:0000211':
                    integrator_parameters['atol'] = float(p['value'])
                elif p['kisaoID'] == 'KISAO:0000475':
                    integrator_parameters['method'] = p['value']
                elif p['kisaoID'] == 'KISAO:0000415':
                    integrator_parameters['nsteps'] = int(p['value'])
                elif p['kisaoID'] == 'KISAO:0000467':
                    integrator_parameters['max_step'] = float(p['value'])
                elif p['kisaoID'] == 'KISAO:0000485':
                    integrator_parameters['min_step'] = float(p['value'])
                elif p['kisaoID'] == 'KISAO:0000484':
                    integrator_parameters['order'] = int(p['value'])
    elif algorithm['kisaoID'] == 'KISAO:0000088':
        # LSODA
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]
        integrator_parameters = {}
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000209':
                integrator_parameters['rtol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000211':
                integrator_parameters['atol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000415':
                integrator_parameters['nsteps'] = int(p['value'])
            elif p['kisaoID'] == 'KISAO:0000467':
                integrator_parameters['max_step'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000485':
                integrator_parameters['min_step'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000219':
                integrator_parameters['max_order_ns'] =int(p['value'])
            elif p['kisaoID'] == 'KISAO:0000220':
                integrator_parameters['max_order_s'] = int(p['value'])
    elif algorithm['kisaoID'] == 'KISAO:0000087':
        # dopri5
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]
        integrator_parameters = {}
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000209':
                integrator_parameters['rtol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000211':
                integrator_parameters['atol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000415':
                integrator_parameters['nsteps'] = int(p['value'])
            elif p['kisaoID'] == 'KISAO:0000467':
                integrator_parameters['max_step'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000541':
                integrator_parameters['beta'] = float(p['value'])
    elif algorithm['kisaoID'] == 'KISAO:0000436':
        # dop853
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]
        integrator_parameters = {}
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000209':
                integrator_parameters['rtol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000211':
                integrator_parameters['atol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000415':
                integrator_parameters['nsteps'] = int(p['value'])
            elif p['kisaoID'] == 'KISAO:0000467':
                integrator_parameters['max_step'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000541':
                integrator_parameters['beta'] = float(p['value'])
    else:
        print("The algorithm {} is not supported!".format(algorithm['kisaoID']))
        raise ValueError("The algorithm {} is not supported!".format(algorithm['kisaoID']))
    
    return method, integrator_parameters


