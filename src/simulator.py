from .solver import solve_euler, solve_scipy, algebra_evaluation, initialize_module
from .sedEditor import get_dict_simulation
from libcellml import AnalyserVariable
from pathlib import PurePath
import importlib.util
import os
import types
import numpy

"""
====================
The simulator module
====================
The simulator module provides the functions to simulate the model.

The module defines the following classes:
    * SimSettings - stores the simulation settings
The module defines the following functions:
    * getSimSettingFromDict - get the simulation settings from the dictionary of the simulation
    * getSimSettingFromSedSim - get the simulation settings from the sedSimulation
    * load_module - load a module from a file.
    * sim_UniformTimeCourse - simulate the model with UniformTimeCourse setting
    * sim_TimeCourse - simulate the model with TimeCourse setting
    * get_KISAO_parameters - get the parameters of the KISAO algorithm
    * get_externals - get the external variable function for the model.
    * get_observables - get the observables information for the simulation.
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
    elif simSetting.type=='UniformTimeCourse':
        simSetting.initial_time=dict_simulation['initialTime']
        simSetting.output_start_time=dict_simulation['outputStartTime']
        simSetting.output_end_time=dict_simulation['outputEndTime']
        simSetting.number_of_steps=dict_simulation['numberOfSteps']
    elif simSetting.type=='SteadyState' or simSetting.type=='steadyState':
        pass
    elif simSetting.type=='timeCourse':
        pass
    else:
        print('The simulation type {} is not supported!'.format(simSetting.type))
        raise ValueError('The simulation type {} is not supported!'.format(simSetting.type))    
    simSetting.method, simSetting.integrator_parameters=get_KISAO_parameters(dict_simulation['algorithm'])
    
    return simSetting

def getSimSettingFromSedSim(sedSimulation):
    """Get the simulation settings from the sedSimulation.

    Parameters
    ----------
    sedSimulation : SedSimulation
        The sedSimulation object

    Raises
    ------
    ValueError
        If the dict_simulation is not valid
        If the simulation type is not supported

    Returns
    -------
    :obj:`SimSettings`: the simulation settings
    """

    try:
        dict_simulation = get_dict_simulation(sedSimulation)
        simSetting = getSimSettingFromDict(dict_simulation)
    except ValueError as e:
        raise ValueError(str(e)) from e
    return simSetting
       
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

def sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module, current_state=None,parameters={}):
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
    external_module : object
        The External_module_varies object instance for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model
        {id:{'name': , 'component': , 'index': , 'type': , 'value': }}

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
                                            sim_setting.initial_time, external_module,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e          

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=None  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            try:
                current_state=solve_euler(module, current_state, observables,
                                          sim_setting.output_start_time, sim_setting.output_end_time,sim_setting.number_of_steps,
                                          step_size,external_module)
            except ValueError as e:
                raise RuntimeError(str(e)) from e            
        
        elif sim_setting.method in SCIPY_SOLVERS:
            try:
                current_state=solve_scipy(module, current_state, observables,
                                          sim_setting.output_start_time, sim_setting.output_end_time,sim_setting.number_of_steps,
                                          sim_setting.method,sim_setting.integrator_parameters,external_module)
            except Exception as e:
                raise RuntimeError(str(e)) from e 
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         sim_setting.number_of_steps,external_module)
    else:
        print('The model type {} is not supported!'.format(mtype)) # should not reach here
        raise RuntimeError('The model type {} is not supported!'.format(mtype))
    
    return current_state

def sim_OneStep(mtype, module, sim_setting, observables, external_module, current_state=None,parameters={}):
    """Simulate the model with OneStep setting.
    
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
    external_module : object
        The External_module_varies object instance for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model
        {id:{'name': , 'component': , 'index': , 'type': , 'value': }}

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
            current_state=initialize_module(mtype,observables,0,module,
                                            0, external_module,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e          

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=None  
    
    step=sim_setting.step
    output_start_time=current_state[0]+step
    output_end_time=output_start_time

    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            try:
                current_state=solve_euler(module, current_state, observables,
                                          output_start_time, output_end_time,0,
                                          step_size,external_module)
            except ValueError as e:
                raise RuntimeError(str(e)) from e            
        
        elif sim_setting.method in SCIPY_SOLVERS:
            try:
                current_state=solve_scipy(module, current_state, observables,
                                          output_start_time, output_end_time,0,
                                          sim_setting.method,sim_setting.integrator_parameters,external_module)
            except Exception as e:
                raise RuntimeError(str(e)) from e 
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         0,external_module)
    else:
        print('The model type {} is not supported!'.format(mtype)) # should not reach here
        raise RuntimeError('The model type {} is not supported!'.format(mtype))
    
    return current_state

def sim_TimeCourse(mtype, module, sim_setting, observables, external_module,current_state=None,parameters={}):
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
   external_module : object
       The External_module_varies object instance for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model
        The format is {id:{'name':'variable name','component':'component name',
        'type':'state','value':value,'index':index}}
    
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
    if number_of_steps<0:
        raise RuntimeError('The time points should be greater than 0!')
            
    if current_state is None:
        try:
            current_state=initialize_module(mtype,observables,number_of_steps,module,
                                            0,external_module,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=None  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            for i in range(number_of_steps):
                try:
                    current_state=solve_euler(module,current_state,observables,
                                              sim_setting.tspan[i],sim_setting.tspan[i+1],1,
                                              step_size,external_module)
                except ValueError as e:
                    raise RuntimeError(str(e)) from e
            if number_of_steps==0:
                try:
                    current_state=solve_euler(module,current_state,observables,
                                              sim_setting.tspan[0],sim_setting.tspan[0],0,
                                              step_size,external_module)
                except ValueError as e:
                    raise RuntimeError(str(e)) from e
                                 
        elif sim_setting.method in SCIPY_SOLVERS:
            for i in range(number_of_steps):
                try:                      
                    current_state=solve_scipy(module,current_state,observables,
                                              sim_setting.tspan[i],sim_setting.tspan[i+1],1,
                                              sim_setting.method,sim_setting.integrator_parameters,external_module)
                except Exception as e:
                    raise e from e
            if number_of_steps==0:
                try:
                    current_state=solve_scipy(module,current_state,observables,
                                              sim_setting.tspan[0],sim_setting.tspan[0],0,
                                              sim_setting.method,sim_setting.integrator_parameters,external_module)
                except Exception as e:
                    raise e from e
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         number_of_steps,external_module)
    else:
        print('The model type {} is not supported!'.format(mtype))
        raise RuntimeError('The model type {} is not supported!'.format(mtype))
    
    return current_state

def sim_SteadyState(mtype, module, sim_setting, observables, external_module, current_state=None,parameters={}):
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
    external_module : object
        The External_module_varies object instance for the model
    current_state : tuple
        The current state of the model.
        The format is (voi, states, rates, variables, current_index, sed_results)
    parameters : dict
        The parameters of the model
        {id:{'name': , 'component': , 'index': , 'type': , 'value': }}

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
                                            sim_setting.initial_time, external_module,parameters)
        except ValueError as e:
            raise RuntimeError(str(e)) from e          
    sed_results=current_state[-1]
    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=0.001  
    
    ftol=1    
    t0=sim_setting.initial_time
    tf=100

    if mtype=='ode':
        while ftol>1e-6:
            if sim_setting.method=='Euler forward method':
                current_state=solve_euler(module, current_state, observables,
                                          t0, tf,sim_setting.number_of_steps,
                                          step_size,external_module)            

            elif sim_setting.method in SCIPY_SOLVERS:
                try:
                    current_state=solve_scipy(module, current_state, observables,
                                              t0, tf, sim_setting.number_of_steps,
                                              sim_setting.method,sim_setting.integrator_parameters,external_module)
                except RuntimeError as e:
                    raise e from e
            else:
                print('The method {} is not supported!'.format(sim_setting.method))
                raise RuntimeError('The method {} is not supported!'.format(sim_setting.method))

            ftol=sum(abs((current_state[-1]-sed_results)/sed_results))
            sed_results=current_state[-1]
            t0=tf
            tf=tf+100
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module,current_state,observables,
                                         sim_setting.number_of_steps,external_module)
    else:
        print('The model type {} is not supported!'.format(mtype)) # should not reach here
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
    method = KISAO_ALGORITHMS[algorithm['kisaoID']]
    integrator_parameters = {}
    if algorithm['kisaoID'] == 'KISAO:0000030':
        # Euler forward method
        if 'listOfAlgorithmParameters' in algorithm:
            for p in algorithm['listOfAlgorithmParameters']:
                if p['kisaoID'] == 'KISAO:0000483':
                    integrator_parameters['step_size'] = float(p['value'])

    elif algorithm['kisaoID'] == 'KISAO:0000535':
            # VODE            
            if 'listOfAlgorithmParameters' in algorithm:
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
        if 'listOfAlgorithmParameters' in algorithm:
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
        if 'listOfAlgorithmParameters' in algorithm:
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
        if 'listOfAlgorithmParameters' in algorithm:
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
    The inputs are constant during the simulation.
        
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

class External_module_varies:
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
    This class allows the model to take inputs as constant, 
    inputs as a list or inputs as a function, 
    while the inputs do not depend on the model variables.
    If the inputs are given as a list, 
    the list should have the same length as the numberOfSteps + 1.
    If the inputs are given as a function,
    (1) for algebraic, take the index of the results as the input and return the value;
    (2) for ode, take the voi as the input and return the value.   
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
    
    def external_variable_algebraic(self, variables,index,result_index=0):
        temp=self.param_vals[self.param_indices.index(index)]
        if isinstance(temp, (int, float)):
            return temp
        elif isinstance(temp, list) or isinstance(temp, numpy.ndarray):
            return temp[result_index]
        elif isinstance(temp,types.FunctionType):
            return temp(result_index)

    def external_variable_ode(self,voi, states, rates, variables,index,result_index=0):
        temp=self.param_vals[self.param_indices.index(index)]
        if isinstance(temp, (int, float)):
            return temp
        elif isinstance(temp, list):
            return temp[result_index]
        elif isinstance(temp,types.FunctionType):
            return temp(voi)

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

def get_externals_varies(analyser, cellml_model, external_variables_info, external_variables_values):
    """ Get the external variable function for the model.

    Parameters
    ----------
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
        If a variable is not found in the model.

    Returns
    -------
    object
        The External_module_varies.
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
        external_module= None
    else:
        external_module=External_module_varies(param_indices,external_variables_values)
       
    return external_module

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
        else:
            for i in range(variable.equivalentVariableCount()):
                eqv = variable.equivalentVariable(i)
                if component_name==eqv.parent().name() and var_name==eqv.name():
                    return avar.index(), AnalyserVariable.typeAsString(avar.type())
        
    for i in range(analysedModel.stateCount()):
        avar=analysedModel.state(i)
        var=avar.variable()
        var_name=var.name()
        component_name=var.parent().name()
        if component_name==variable.parent().name() and var_name==variable.name():
            return avar.index(), AnalyserVariable.typeAsString(avar.type())
        else:
            for i in range(variable.equivalentVariableCount()):
                eqv = variable.equivalentVariable(i)
                if component_name==eqv.parent().name() and var_name==eqv.name():
                    return avar.index(), AnalyserVariable.typeAsString(avar.type())
        
    avar=analysedModel.voi()
    if avar:
        var=avar.variable()
        var_name=var.name()
        component_name=var.parent().name()
        if component_name==variable.parent().name() and var_name==variable.name():
            return avar.index(), AnalyserVariable.typeAsString(avar.type())  
        else:
            for i in range(variable.equivalentVariableCount()):
                eqv = variable.equivalentVariable(i)
                if component_name==eqv.parent().name() and var_name==eqv.name():
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
    else: # search through equivalent variables; should not reach here? 
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