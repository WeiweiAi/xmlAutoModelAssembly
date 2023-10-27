from .solver import solve_euler, solve_scipy, algebra_evaluation,initialize_module
from pathlib import PurePath
import importlib.util
from libcellml import AnalyserModel, AnalyserVariable

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.ode.html
SCIPY_SOLVERS = ['dopri5', 'dop853', 'VODE', 'LSODA']
KISAO_ALGORITHMS = {'KISAO:0000030': 'Euler forward method',
                    'KISAO:0000535': 'VODE',
                    'KISAO:0000536': 'ZVODE',
                    'KISAO:0000088': 'LSODA',
                    'KISAO:0000087': 'dopri5',
                    'KISAO:0000436': 'dop853',
                    }

def get_KISAO_parameters(algorithm):
    """Get the parameters of the KISAO algorithm.
    Args:
        algorithm (:obj:`dict`): the algorithm of the simulation, the format is {'kisaoID': , 'name': 'optional,Euler forward method' , 'listOfAlgorithmParameters':[dict_algorithmParameter] }
         dict_algorithmParameter={'kisaoID':'KISAO:0000483','value':'0.001'}
    Returns:
        :obj:`tuple`:
            * :obj:`str`: the method of the simulation
            * :obj:`dict`: the parameters of the integrator, the format is {parameter: value}
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
        return None, None
    
    return method, integrator_parameters

class SimulationSettings():
    """ Dictionary that stores the simulation settings 
    items:
    * initial_time (:obj:`float`): the initial time of the simulation
    * output_start_time (:obj:`float`): the start time of the output
    * output_end_time (:obj:`float`): the end time of the output
    * number_of_steps (:obj:`int`): the number of steps of the output
    * step (:obj:`float`): the step size of when the type is OneStep
    * method (:obj:`str`): the method of the ode solver
    * integrator_parameters (:obj:`dict`): the parameters of the integrator, the format is {parameter: value}
    """    
    def __init__(self):
        self.type='UniformTimeCourse'
        self.initial_time = 0
        self.output_start_time = 0
        self.output_end_time = 10
        self.number_of_steps = 1000
        self.step=0.1
        self.method='Euler forward method' 
        self.integrator_parameters={}       

def getSimSettingFromDict(dict_simulation):
    simSetting=SimulationSettings()
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
    else:
        print('The simulation type {} is not supported!'.format(simSetting.type))
        return None    
    method, integrator_parameters=get_KISAO_parameters(dict_simulation['algorithm'])
    if method is None:
        return None
    simSetting.method=method
    simSetting.integrator_parameters=integrator_parameters
    return simSetting

class External_module:
    """ Class to define the external module.
    Args:
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
        param_vars_info (:obj:`list` of :obj:`tuple`): the list of variables, each variable is a tuple of (component_name, variable_name)
        param_vals (:obj:`list`): the list of values of the variables
    """
    def __init__(self,analyser, model,param_vars_info,param_vals):
        self.param_vars = param_vars_info
        self.param_vals = param_vals
        self.param_indices = get_variable_indices(analyser, model, param_vars_info) # the indices of the variables, or False if a required variable is not found, or [] if no variable is specified

    def initialise(self, variables,index):
        if index in self.param_indices:
            return self.param_vals[self.param_indices.index(index)]
        else:
            return None           
    def update(self, variables,index):
        if index in self.param_indices:
            return self.param_vals[self.param_indices.index(index)]
        else:
            return None

def get_externals(external_module):

    if not external_module.param_indices:
        external_variable=None
        external_update=None
    else:
        external_variable=external_module.initialise
        external_update=external_module.update

    return external_variable,external_update

def get_mtype(analyser):
    """ Get the type of the model."""
    return AnalyserModel.typeAsString(analyser.model().type())

def _get_index_type_for_variable(analyser, variable):
    """Get the index and type of a variable in a module.
    Args:
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
        variable_info (:obj:`tuple`): the variable, a tuple of (component_name, variable_name)
    Returns:
        :obj:`tuple`:
            * :obj:`int`: the index of the variable
            * :obj:`str`: the type of the variable
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

def get_index_type_for_equivalent_variable(analyser, variable):
    """Get the index and type of a variable in a module by searching through equivalent variables.
    Args:
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
        variable (:obj:`Variable`): the variable
    Returns:
        :obj:`tuple`:
            * :obj:`int`: the index of the variable
            * :obj:`str`: the type of the variable
    """
    index, vtype = _get_index_type_for_variable(analyser,variable)
    if vtype != 'unknown':
        return index, vtype
    else:
        for i in range(variable.equivalentVariableCount()):
            eqv = variable.equivalentVariable(i)
            # print("Checking equivalent variable: {} / {}".format(cname, vname))
            index, vtype = _get_index_type_for_variable(analyser, eqv)
            if vtype != 'unknown':
                return index, vtype
    return -1, 'unknown'

def get_variable_indices(analyser, model,variables_info):
    """Get the indices of a list of variables in a model.
    Args:
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
        model (:obj:`Model`): the CellML model
        variables_info (:obj:`list` of :obj:`tuple`): the list of variables, each variable is a tuple of (component_name, variable_name)
    Returns:
        :obj:`list` of :obj:`int`: the indices of the variables
    """
    indices = []
    for variable_info in variables_info:
       variable=_find_variable(model, variable_info[0],variable_info[1])
       index, vtype = get_index_type_for_equivalent_variable(analyser,variable)
       if vtype != 'unknown':
           indices.append(index)
       else:
           return False        
    return indices

def load_module(full_path):
    """Take the Python code generated by libCellML and load it into a module that can be executed.
    Args:
        full_path (:obj:`str`): the full path of the Python file (including the file name and extension)
    Returns:
        :obj:`module`: the module containing the Python code"""
    module_name = PurePath(full_path).stem
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _find_variable(model, component_name,variable_name):
    """ Find a variable in a CellML model.
    Args:
        model (:obj:`Model`): the CellML model
        component_name (:obj:`str`): the name of the component
        variable_name (:obj:`str`): the name of the variable
    Returns:
        :obj:`Variable`: the Variable instance of the variable found, None if the variable is not found
    """
    for c in range(model.componentCount()):
        if model.component(c).name()==component_name:
            for v in range(model.component(c).variableCount()):
                if model.component(c).variable(v).name()==variable_name:
                    return model.component(c).variable(v)
    return None

def get_observables(analyser, model, variables_info):
    """
    Get the observables of the simulation.
    Args:
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
        model (:obj:`Model`): the CellML model
        variables_info (:obj:`dict` ): {'v':(observable_component,observable_name)}
    Returns:
        :obj:`dict`: the observables of the simulation, the format is {id:{'name': , 'component': , 'index': , 'type': }}; False if a required variable is not found
    """
    observables = {}
    for key,variable_info in variables_info.items():
        variable=_find_variable(model, variable_info[0],variable_info[1])
        index, vtype=get_index_type_for_equivalent_variable(analyser,variable)
        if vtype != 'unknown':
            observables[key]={'name':variable_info[1],'component':variable_info[0],'index':index,'type':vtype}
        else:
            print("Unable to find a required variable in the generated code")
            return False
    return observables

def sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module,current_state=None):
    """Simulate the model using the UniformTimeCourse algorithm.
    Args:
        mtype (:obj:`str`): the type of the model
        module (:obj:`module`): the module containing the Python code
        sim_setting (:obj:`SimulationSettings`): the simulation settings
        observables (:obj:`dict`): the observables of the simulation, the format is {id:{'name': , 'component': , 'index': , 'type': }}
        external_module (:obj:`External_module`): the external module
    Returns:
        :obj:`dict`: the results of the simulation, the format is {id:numpy.ndarray}
    """

    external_variable,external_update = get_externals(external_module)
    if current_state is None:
        current_state=initialize_module(module,external_variable,mtype,observables,sim_setting.initial_time,sim_setting.number_of_steps)

    output_step_size=(sim_setting.output_end_time-sim_setting.output_start_time)/sim_setting.number_of_steps

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=output_step_size  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            current_state=solve_euler(module, external_update, observables, current_state, sim_setting.output_start_time,sim_setting.output_end_time,sim_setting.number_of_steps,step_size)            
        
        elif sim_setting.method in SCIPY_SOLVERS:
            current_state=solve_scipy(module, external_update, observables, current_state, sim_setting.output_start_time,sim_setting.output_end_time,sim_setting.number_of_steps,sim_setting.method,sim_setting.integrator_parameters)
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            return False
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module, external_update, observables,current_state, sim_setting.number_of_steps)
    else:
        print('The model type {} is not supported!'.format(mtype))
        return False
    
    return current_state






