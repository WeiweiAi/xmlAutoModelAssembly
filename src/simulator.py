from .solver import solve_euler, solve_scipy, algebra_evaluation, initialize_module



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
        The type of the simulation, the value can be 'OneStep', 'UniformTimeCourse', 'SteadyState' or 'timeCourse'
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
    else:
        print('The simulation type {} is not supported!'.format(simSetting.type))
        return None    
    method, integrator_parameters=get_KISAO_parameters(dict_simulation['algorithm'])
    if method is None:
        return None
    simSetting.method=method
    simSetting.integrator_parameters=integrator_parameters
    return simSetting


def sim_UniformTimeCourse(mtype, module, sim_setting, observables, external_module,current_state=None,parameters={}):
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

    external_variable,external_update = get_externals(mtype,external_module)
    if current_state is None:
        current_state=initialize_module(module,external_variable,mtype,observables,sim_setting.initial_time,sim_setting.number_of_steps,parameters)

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

def sim_TimeCourse(mtype, module, sim_setting, observables, external_module,current_state=None,parameters={}):
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
    
    number_of_steps=len(sim_setting.tspan)-1
    
    external_variable,external_update = get_externals(mtype,external_module)
    if current_state is None:
        current_state=initialize_module(module,external_variable,mtype,observables,0,number_of_steps,parameters)

    output_step_size=(sim_setting.tspan[-1]-sim_setting.tspan[0])/number_of_steps

    if 'step_size' in sim_setting.integrator_parameters:
        step_size=sim_setting.integrator_parameters['step_size']
    else:
        step_size=output_step_size  
    
    if mtype=='ode':
        if sim_setting.method=='Euler forward method':
            for i in range(number_of_steps):
                current_state=solve_euler(module, external_update, observables, current_state, sim_setting.tspan[i],sim_setting.tspan[i+1],1,step_size)                   
        elif sim_setting.method in SCIPY_SOLVERS:
            for i in range(number_of_steps):   
                current_state=solve_scipy(module, external_update, observables, current_state, sim_setting.tspan[i],sim_setting.tspan[i+1],1,sim_setting.method,sim_setting.integrator_parameters)
        else:
            print('The method {} is not supported!'.format(sim_setting.method))
            return False
    elif mtype=='algebraic':
        current_state=algebra_evaluation(module, external_update, observables,current_state, number_of_steps)
    else:
        print('The model type {} is not supported!'.format(mtype))
        return False
    
    return current_state


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


