from libcellml import  Parser, Validator, Analyser, AnalyserExternalVariable, Importer, cellmlElementTypeAsString
import json

def _dump_issues(source_method_name, logger):
    """"
    Args:
        source_method_name (:obj:`str`): the name of the method that calls the logger
        logger (:obj:`Logger`): the logger instance
    Returns:
        :obj:`tuple`:
            * :obj:`str`: the issue description found by the logger, html format
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
    Args:
        filename (:obj:`str`): the path of the CellML file (including the file name and extension)
        strict_mode (:obj:`bool`): whether to use strict mode to parse the CellML file
    Returns:
        :obj:`tuple`:
            * :obj:`Model`: the CellML model parsed from the CellML file, None if the parser found issues
            * :obj:`str`: the issue description found by the parser
    """
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
    Args:
        model (:obj:`Model`): the CellML model to be validated
    Returns:
        :obj:`tuple`:
            * :obj:`bool`: whether the model is valid
            * :obj:`str`: the issue description found by the validator
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
    Args:
        model (:obj:`Model`): the CellML model to be validated
        base_dir (:obj:`str`): the full path to the directory that import URLs are relative to
        strict_mode (:obj:`bool`): whether to use strict mode to resolve the imports
    Returns:
        :obj:`tuple`:
            * :obj:`Importer`: the Importer instance, None if the importer found issues
            * :obj:`str`: the issue description found by the importer
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
    Args:
        model (:obj:`Model`): the CellML model to be validated
        importer (:obj:`Importer`): the Importer instance
    Returns:
        :obj:`Model`: the flattened CellML model"""
    flatModel=importer.flattenModel(model)
    return flatModel

def ext_var_dic(flatModel,external_variables_info):
    """
    Create a dictionary of external variables in the flattened model.
    Args:
        flatModel (:obj:`Model`): the flattened CellML model
        external_variables (:obj:`list`): the list of external variables to be specified, each variable is a tuple of (component_name, variable_name)
    Returns:
        :obj:`dict`: the dictionary of external variables in the flattened model, the format is {external_variable:[]}
    """
    external_variables_dic={}
    for ext_var in external_variables_info:
        flat_ext_var=flatModel.component(ext_var[0]).variable(ext_var[1])
        if flat_ext_var:
           external_variables_dic[flat_ext_var]=[]
        else:
            print("The external variable {} in component {} is not found in the flattened model!".format(ext_var[1],ext_var[0]))
            return {}
    return external_variables_dic

def analyse_model(flatModel,external_variables_dic={}):
    """ 
    Analyse a flattened CellML model.
    Args:
        model (:obj:`Model`): the flattened CellML model to be analysed
        external_variables (:obj:`dict`): the external variables to be specified, in the format of {external_variable:[dependency1,dependency2,...]}
    Returns:
        :obj:`tuple`:
            * :obj:`Analyser`: the Analyser instance, None if the analyser found issues
            * :obj:`str`: the issue description found by the analyser
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
    Args:
        model (:obj:`Model`): the CellML model to be validated
        base_dir (:obj:`str`): the path to the directory that import URLs are relative to
        strict_mode (:obj:`bool`): whether to use strict mode to resolve the imports
    Returns:
        :obj:`tuple`:
            * :obj:`Analyser`: the Analyser instance, False if issues are found
            * :obj:`flatModel`: the flattened CellML model, None if issues are found
            * :obj:`str`: the issue description in json format
    """
    modelIsValid,issues_validate=validate_model(model)
    if modelIsValid:
        importer,issues_import=resolve_imports(model, base_dir,strict_mode)
        if importer:
            flatModel=importer.flattenModel(model)
            external_variables_dic=ext_var_dic(flatModel,external_variables_info)
            analyser,issues_analyse=analyse_model(flatModel,external_variables_dic)
            issues=issues_validate+issues_import+issues_analyse
            if analyser:
                return analyser, json.dumps(issues)
        else:
            issues=issues_validate+issues_import
    else:
        issues=issues_validate
    return False, json.dumps(issues)


    
