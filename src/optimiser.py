
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
        algorithm (:obj:`dict`): the algorithm of the optimization, 
        the format is {'kisaoID': , 'name': 'optional,Euler forward method' , 
        'listOfAlgorithmParameters':[dict_algorithmParameter] }
        dict_algorithmParameter={'kisaoID':'KISAO:0000483','value':'0.001'}
    Returns:
        :obj:`tuple`:
            * :obj:`str` or None: the method of the optimization algorithm
            * :obj:`dict` or None: the parameters of the integrator, the format is {parameter: value}
    """
    opt_parameters = {}
    if algorithm['kisaoID'] == 'KISAO:0000514': 
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]       
        for p in algorithm['listOfAlgorithmParameters']:
            if p['kisaoID'] == 'KISAO:0000211':
                opt_parameters['xatol'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000486':
                opt_parameters['maxiter'] = float(p['value'])
            elif p['kisaoID'] == 'KISAO:0000597':
                opt_parameters['tol'] = float(p['value'])

        return method, opt_parameters
    elif algorithm['kisaoID'] in KISAO_ALGORITHMS.keys():
        method = KISAO_ALGORITHMS[algorithm['kisaoID']]
        return method, None
    else:
        print("The algorithm {} is not supported!".format(algorithm['kisaoID']))
        return None, None
