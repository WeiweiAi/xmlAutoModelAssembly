import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint

# https://docs.scipy.org/doc/scipy/reference/optimize.html
SCIPY_OPTIMIZE_LOCAL = ['Nelder-Mead','Powell','CG','BFGS','Newton-CG','L-BFGS-B','TNC','COBYLA','SLSQP','trust-constr','dogleg','trust-ncg','trust-exact','trust-krylov']
KISAO_ALGORITHMS = {'KISAO:0000514': 'Nelder-Mead',
                    'KISAO:0000472': 'global optimization algorithm',
                    'KISAO:0000471': 'local optimization algorithm',
                    'KISAO:0000503': 'simulated annealing',	
                    'KISAO:0000520': 'evolutionary algorithm',
                    'KISAO:0000504': 'random search',
                    }
def get_KISAO_parameters_opt(algorithm):
    """Get the parameters of the KISAO algorithm.
    Args:
        algorithm (:obj:`dict`): the algorithm of the simulation, the format is {'kisaoID': , 'name': 'optional,Euler forward method' , 'listOfAlgorithmParameters':[dict_algorithmParameter] }
         dict_algorithmParameter={'kisaoID':'KISAO:0000483','value':'0.001'}
    Returns:
        :obj:`tuple`:
            * :obj:`str`: the method of the simulation
            * :obj:`dict`: the parameters of the integrator, the format is {parameter: value}
    """
    method = KISAO_ALGORITHMS[algorithm['kisaoID']]
    opt_parameters = {}
    if algorithm['kisaoID'] == 'KISAO:0000514':        
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000211':
                opt_parameters['xatol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000486':
                opt_parameters['maxiter'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000597':
                opt_parameters['tol'] = float(p['value'])
    elif algorithm['kisaoID'] == 'KISAO:0000472':
        return method, None
    elif algorithm['kisaoID'] == 'KISAO:0000471':
        return method, None
    else:
        print("The algorithm {} is not supported!".format(algorithm['kisaoID']))
        return method, None
    
    return method, opt_parameters
class ExperimentData(dict):
    def __init__(self):
        self.types = [] # list,  ['mean', 'max', 'min','steady-state','series'] Specify the type of the outputs, which could be mean, max, min, steady state or the raw series of the simulation result
        self.observables_info = [] # list, [('component1','variable1'),('component2','variable2'),...] Specify the variables to be observed
        self.exp_const_vec = None # The constant measurements, np.ndarray, np.generic
        self.weight_const_vec = None #The scale vector to differentiate the significance of observed values
        self.std_const_vec = None # The standard deviation of constant measurements
        self.std_series_vec = None # The standard deviation of series measurements
        self.exp_series_vec = None # The series measurements, np.ndarray, np.generic
        self.weight_series_vec = None #"""The scale vector to differentiate the significance of observed series """   
        self.time_vec = None # The time vector of the series measurements        
        self.cost_type = 'MSE'   # The cost calculation formula type, MSE: Mean Square Error, AE: Absolute Error

class OptimisationSettings(dict):   
    def __init__(self):
        self.param_init = None # Specify the initial values of the parameters
        self.param_mins = None # np.ndarray, np.generic
        self.param_maxs = None # np.ndarray, np.generic           
        self.method = 'trust-constr' # The optimization method https://docs.scipy.org/doc/scipy/reference/optimize.html, ['Nelder-Mead','Powell','CG','BFGS','Newton-CG','L-BFGS-B','TNC','COBYLA','SLSQP','trust-','dogleg',        'trust-ncg','trust-exact','trust-krylov']
        self.params = {'jac':None, 'hess':None, 'hessp':None, 'constraints':(), 'tol':None, 'callback':None}# {'args','jac','hess','hessp','bounds','constrains','tol','callback'}, https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize
        self.options={'verbose': 1} # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize   

def preprocess_observations(simulation_results,experimentData):
    nseries = experimentData.types.count('series')
    nconst = len(experimentData.types)-nseries      
    if nseries == 0:
       sim_series_array = None        
    elif len(experimentData.exp_series_vec) != nseries:
        print('The size of simulation series and experiment data do not match')
        return False                      
    else:
        sedID = list(simulation_results.keys())[0] # get the first key
        numOfSteps = len(simulation_results[sedID]) # assume all series have the same length
        sim_series_array = np.zeros((nseries, numOfSteps))
    
    if nconst == 0:
       sim_consts_vec = None 
    elif len(experimentData.exp_const_vec) != nconst:
        print('The size of simulation constants and exp does not match')
        return False 
    else:
        sim_consts_vec = np.zeros((nconst, ))

    const_count = 0
    series_count = 0
    for JJ in range(len(simulation_results)):
        sedID = list(simulation_results.keys())[JJ]
        if  experimentData.types[JJ] == 'mean':
            sim_consts_vec[const_count] = np.mean(simulation_results[sedID])
            const_count += 1
        elif experimentData.types[JJ] == 'max':
            sim_consts_vec[const_count] = np.max(simulation_results[sedID])
            const_count += 1
        elif experimentData.types[JJ] == 'min':
            sim_consts_vec[const_count] = np.min(simulation_results[sedID])
            const_count += 1
        elif experimentData.types[JJ] == 'steady-state':
            sim_consts_vec[const_count] = simulation_results[sedID][-1]
            const_count += 1
        elif experimentData.types[JJ] == 'series':
            sim_series_array[series_count, :] = simulation_results[sedID][:]
            series_count += 1
            pass
    return sim_consts_vec, sim_series_array

def _get_cost_from_obs(simulation_results,experimentData):
    sim_consts_vec, sim_series_array =preprocess_observations(simulation_results,experimentData)
    # calculate error between the observables of this set of parameters
    # and the ground truth
    cost = _cost_calc(sim_consts_vec, sim_series_array,experimentData)
    return cost

def _cost_calc(consts, series,experimentData):
    
    if consts is not None:
       if experimentData.weight_const_vec is None:
              experimentData.weight_const_vec = np.ones(np.shape(consts))
       if experimentData.std_const_vec is None:
                experimentData.std_const_vec = np.ones(np.shape(consts))   
       if experimentData.cost_type == 'MSE':
           cost = np.sum(np.power(experimentData.weight_const_vec*(consts -
                              experimentData.exp_const_vec)/experimentData.std_const_vec, 2))
       elif experimentData.cost_type == 'AE':
           cost = np.sum(np.abs(experimentData.weight_const_vec*(consts -
                                                         experimentData.exp_const_vec)/experimentData.std_const_vec))
    else:
        cost=0
    if series is not None:
        if np.shape(experimentData.exp_series_vec) != np.shape(series):
            print(f'exp:{experimentData.exp_series_vec.shape},sim:{series.shape}')
        else:
           min_len_series = min(np.shape(experimentData.exp_series_vec)[1], np.shape(series)[1])
           if experimentData.weight_series_vec is None:
              experimentData.weight_series_vec = np.ones(np.shape(series))
           if experimentData.std_series_vec is None:
              experimentData.std_series_vec = np.ones(np.shape(series))
           # calculate sum of squares cost and divide by number data points in series data
           # divide by number data points in series data
           if experimentData.cost_type == 'MSE':
               series_cost = np.sum(np.power((series[:, :min_len_series] -
                                              experimentData.exp_series_vec[:,
                                              :min_len_series]) * experimentData.weight_series_vec.reshape(-1, 1) /
                                             experimentData.std_series_vec.reshape(-1, 1), 2)) / min_len_series
           elif experimentData.cost_type == 'AE':
               series_cost = np.sum(np.abs((series[:, :min_len_series] -
                                            experimentData.exp_series_vec[:,
                                            :min_len_series]) * experimentData.weight_series_vec.reshape(-1, 1) /
                                           experimentData.std_series_vec.reshape(-1, 1))) / min_len_series
           cost = (cost + series_cost) / len(experimentData.names)
    else:
        cost = cost / len(experimentData.variables_info)
    return cost


def get_cost_from_params_singleSim(param_vals, param_vars_info, analyser, module, sim_setting,experimentData):
    external_module=External_module(analyser, param_vars_info,param_vals)
    # update the simulation setting according to the experiment data
    sim_setting.obserables=get_observables(analyser,experimentData.variables_info)
    if experimentData.time_vec:
        sim_setting.output_start_time=experimentData.time_vec[0]
        sim_setting.output_end_time=experimentData.time_vec[-1]
        sim_setting.number_of_steps=len(experimentData.time_vec)-1
    sed_results=simulate(analyser, module, sim_setting, external_module)
    if sed_results:
        cost=_get_cost_from_obs(sed_results,experimentData)

    else:
        print('simulation failed with params...')
        print(param_vals)
        cost = np.inf
    return cost

def objective_function(param_vals,param_vars_dic, analysers, modules, sim_settings, experimentDatas):
    cost = 0
    param_vars=param_vars_dic[-1]
    for i in range(len(analysers)):
        sub_param_vars=param_vars_dic[i]
        sub_param_vars_indices=[param_vars.index(item) for item in sub_param_vars]
        sub_param_vals=[param_vals[item] for item in sub_param_vars_indices]
        cost += get_cost_from_params_singleSim(sub_param_vals,sub_param_vars, analysers[i], modules[i], sim_settings[i], experimentDatas[i])
    return cost

def optimiseModel(param_vars_dic, analysers, modules, sim_settings, experimentDatas, opt):
    x0=opt.param_init
    if opt.param_mins is None:
        opt.param_mins=[-np.inf]*len(x0)
    if opt.param_maxs is None:
        opt.param_maxs=[np.inf]*len(x0)
    bounds=Bounds(opt.param_mins,opt.param_maxs)
    res=minimize(objective_function, x0, args=(param_vars_dic, analysers, modules, sim_settings, experimentDatas), method=opt.method,bounds=bounds,
                 jac=opt.params['jac'], hess=opt.params['hess'], hessp=opt.params['hessp'],constraints=opt.params['constraints'],tol=opt.params['tol'],
                 callback=opt.params['callback'], options=opt.options)
    return res
