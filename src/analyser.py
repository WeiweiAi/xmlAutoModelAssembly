from libcellml import  Parser, Validator, Analyser, AnalyserExternalVariable, Importer, cellmlElementTypeAsString, AnalyserModel, AnalyserVariable
import json
import os

def _dump_issues(source_method_name, logger):
    """"
    Dump the issues found by the parser, validator, importer or analyser.

    Parameters
    ----------
    source_method_name: str
        The name of the source method that generated the logger.
    logger: Parser, Validator, Importer or Analyser
        The libcellml logger instance.

    Returns
    -------
    str
        The issues found by the logger.
    """

    issues = ''
    if logger.issueCount() > 0:
        issue_sum = 'The method "{}" found {} issues:'.format(source_method_name, logger.issueCount())
        issues=issues+issue_sum+'<br>'
        for i in range(0, logger.issueCount()):
            issuei=logger.issue(i).description()
            issues=issues+issuei+'<br>'
            issues=issues+'The element type is: '+ cellmlElementTypeAsString(logger.issue(i).item().type())+'<br>'
            issues=issues+'The reference rule is: '+logger.issue(i).referenceHeading( )+'<br>'
    return issues

def parse_model(filename, strict_mode=False):
    """ 
    Parse a CellML file to a CellML model.

    Parameters
    ----------
    filename: str
        The fullpath of the CellML file.
    strict_mode: bool, optional
        Whether to use strict mode to parse the CellML file. Default: False.
        If False, the parser can parse CellML 1.0 and 1.1 files. TODO: check this

    Returns
    -------
    tuple
        The CellML model and the issues found by the parser.
        If issues are found, the model is None.
    """

    if not os.path.isfile(filename):
        raise FileNotFoundError('Model source file `{}` does not exist.'.format(filename))
    
    cellml_file = open(filename)
    parser = Parser(strict_mode)
    model = parser.parseModel(cellml_file.read())
    cellml_file.close() 
    issues = _dump_issues("parse_model", parser)
    if issues !='':
        return None, issues
    else:
        issues="parse_model: No issues found!<br>"
        return model, issues

def validate_model(model):
    """ 
    Validate a CellML model.
    
    Parameters
    ----------
    model: Model
        The CellML model to be validated.

    Returns
    -------
    tuple
        (bool, str)
        Whether the model is valid and the issues found by the validator.
        If issues are found, the model is not valid (False).
    """
    validator = Validator()
    validator.validateModel(model)
    issues = _dump_issues("validate_model", validator)
    if issues=='':
        issues="validate_model: No issues found!<br>"
        return True, issues
    else:
        return False, issues

def resolve_imports(model, base_dir,strict_mode=True):
    """ 
    Resolve the imports of a CellML model.
    
    Parameters
    ----------
    model: Model
        The CellML model for which the import needs to be resolved.
    base_dir: str
        The full path to the directory that import URLs are relative to.
    strict_mode: bool, optional
        Whether to use strict mode to resolve imports. Default: True.

    Returns
    -------
    tuple
        (Importer, str)
        The Importer instance and the issues found by the importer.
        If issues are found, the importer is None.
    """

    importer = Importer(strict_mode)
    importer.resolveImports(model, base_dir)
    issues = _dump_issues("resolve_imports", importer)
    if issues=='' and (not model.hasUnresolvedImports()):
        issues="resolve_imports: No issues found!<br>"
        return importer, issues
    else:
        return None, issues

def flatten_model(model,importer):
    """ 
    Flatten a CellML model. Assume the model has been validated and the imports have been resolved.
    
    Parameters
    ----------
    model: Model
        The CellML model to be flattened.
    importer: Importer
        The Importer instance that has resolved the imports of the model.
    
    Returns
    -------
    Model
        If successful,the flattened CellML model, otherwise None.
    """
    
    flatModel=importer.flattenModel(model)
    return flatModel

def ext_var_dic(flatModel,external_variables_info):
    """
    Create a dictionary of external variables in the flattened model.
    
    Parameters
    ----------
    flatModel: Model
        The flattened CellML model.
    external_variables_info: dict
        The external variables to be specified, in the format of {id:{'component': , 'name': }}

    Raises
    ------
    ValueError
        If an external variable is not found in the flattened model.

    Returns
    -------
    dict
        The dictionary of external variables in the flattened model, in the format of {external_variable:[]}
    
    Notes
    -----
        No dependency is specified for the external variables.
    """

    external_variables_dic={}
    for _, ext_var_info in external_variables_info.items():
        flat_ext_var=flatModel.component(ext_var_info['component']).variable(ext_var_info['name']) # TODO: check if equivalent variables should be considered
        if flat_ext_var:
           external_variables_dic[flat_ext_var]=[]
        else:
            raise ValueError ("The external variable {} in component {} is not found in the flattened model!".format(ext_var_info['component'],ext_var_info['name']))

    return external_variables_dic

def analyse_model(flatModel,external_variables_dic={}):
    """ 
    Analyse a flattened CellML model.
    
    Parameters
    ----------
    flatModel: Model
        The flattened CellML model.
    external_variables_dic: dict, optional
        The dictionary of external variables in the flattened model, in the format of {external_variable:[dependency1,dependency2]}.

    Returns
    -------
    tuple
        (Analyser, str)
        The Analyser instance and the issues found by the analyser.
        If issues are found, the analyser is None.
    """ 

    analyser = Analyser()
    for external_variable in external_variables_dic.keys():
        aev=AnalyserExternalVariable(external_variable)
        for dependency in external_variables_dic[external_variable]:
            aev.addDependency(dependency)
        if not analyser.addExternalVariable(aev):        
            return None, "analyse_model: Unable to add external variable {} to the analyser! <br> ".format(external_variable.name())	
    analyser.analyseModel(flatModel)
    issues = _dump_issues("analyse_model", analyser)
    if issues=='':
        return analyser, issues
    else:
        return None, issues
    
def analyse_model_full(model,base_dir,external_variables_info=[],strict_mode=True):
    """ 
    Fully validate and analyse a cellml model.
   
    Parameters
    ----------
    model: Model
        The CellML model to be analysed.
    base_dir: str
        The full path to the directory that import URLs are relative to.
    external_variables_info: dict, optional
        The external variables to be specified, in the format of {id:{'component': , 'name': }}
    strict_mode: bool, optional
        Whether to use strict mode to resolve imports. Default: True.

    Returns
    -------
    tuple
        (Analyser, str)
        The Analyser instance and the issues found by the analysing process.
        If issues are found, the analyser is None.
    """
    modelIsValid,issues_validate=validate_model(model)
    if modelIsValid:
        importer,issues_import=resolve_imports(model, base_dir,strict_mode)
        if importer:
            flatModel=importer.flattenModel(model)
            if not flatModel:
                return None, json.dumps(issues_import)
            try:
                external_variables_dic=ext_var_dic(flatModel,external_variables_info)
            except ValueError as err:
                return None, json.dumps(str(err))            
            analyser,issues_analyse=analyse_model(flatModel,external_variables_dic)
            issues=issues_validate+issues_import+issues_analyse
            if analyser:
                return analyser, json.dumps(issues)
        else:
            issues=issues_validate+issues_import
    else:
        issues=issues_validate
    return None, json.dumps(issues)

def get_mtype(analyser):
    """ Get the type of the model.
    
    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.

    Returns
    -------
    str
        The type of the model.
        The type can be 'unknown', 'algebraic', 'dae', 'invalid', 'nla', 'ode', 
        'overconstrained', 'underconstrainted' or 'unsuitably_constrained'.
        Refer to https://libcellml.org/documentation/v0.5.0/api/classlibcellml_1_1AnalyserModel
  
    """
    return AnalyserModel.typeAsString(analyser.model().type())
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
          
def get_externals(mtype,external_module):
    """ Get the external variable function for the model.

    Parameters
    ----------
    mtype: str
        The type of the model.
    external_module: External_module
        The external module instance.
    
    Returns
    -------
    function
        The external variable function for the model.
    """

    if mtype=='algebraic':
        external_variable=external_module.external_variable_algebraic
    elif mtype=='ode':
        external_variable=external_module.external_variable_ode
    else:
        raise NotImplementedError("The model type {} is not supported!".format(mtype))

    return external_variable

def _get_index_type_for_variable(analyser, variable):
    """Get the index and type of a variable in a module.
    
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
        The type can be 'algebraic', 'constant', 'computed_constant', 'external',  'state' or 'variable_of_integration'.
    
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

def get_variable_indices(analyser, model,variables_info):
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
        raise ValueError(str(err))
    indices=[]
    for key,observable in observables.items():
        indices.append(observable['index'])

    return indices

def get_observables(analyser, model, variables_info):
    """
    Get the observables of the simulation.
    
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
            raise ValueError(str(err))
        
        index, vtype=get_index_type_for_equivalent_variable(analyser,variable)
        if vtype != 'unknown':
            observables[key]={'name':variable_info['name'],'component':variable_info['component'],'index':index,'type':vtype}
        else:
            print("Unable to find a required variable in the generated code")
            raise ValueError("Unable to find a required variable in the generated code")
        
    return observables

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
