from libcellml import Component, Model, Units,  Variable, ImportSource
import pandas as pd
from lxml import etree
import libsbml
from pathlib import PurePath
import os
from .analyser import parse_model
import re

""" Misc. Constants of CellML construction """
MATH_HEADER = '<math xmlns="http://www.w3.org/1998/Math/MathML" xmlns:cellml="http://www.cellml.org/cellml/2.0#">\n'
MATH_FOOTER = '</math>\n'
BUILTIN_UNITS = {'ampere':Units.StandardUnit.AMPERE, 'becquerel':Units.StandardUnit.BECQUEREL, 'candela':Units.StandardUnit.CANDELA, 'coulomb':Units.StandardUnit.COULOMB, 'dimensionless':Units.StandardUnit.DIMENSIONLESS, 
                 'farad':Units.StandardUnit.FARAD, 'gram':Units.StandardUnit.GRAM, 'gray':Units.StandardUnit.GRAY, 'henry':Units.StandardUnit.HENRY, 'hertz':Units.StandardUnit.HERTZ, 'joule':Units.StandardUnit.JOULE,
                   'katal':Units.StandardUnit.KATAL, 'kelvin':Units.StandardUnit.KELVIN, 'kilogram':Units.StandardUnit.KILOGRAM, 'liter':Units.StandardUnit.LITRE, 'litre':Units.StandardUnit.LITRE, 
                   'lumen':Units.StandardUnit.LUMEN, 'lux':Units.StandardUnit.LUX, 'metre':Units.StandardUnit.METRE, 'meter':Units.StandardUnit.METRE, 'mole':Units.StandardUnit.MOLE, 'newton':Units.StandardUnit.NEWTON, 
                   'ohm':Units.StandardUnit.OHM, 'pascal':Units.StandardUnit.PASCAL, 'radian':Units.StandardUnit.RADIAN, 'second':Units.StandardUnit.SECOND, 'siemens':Units.StandardUnit.SIEMENS, 'sievert':Units.StandardUnit.SIEVERT, 
                   'steradian':Units.StandardUnit.STERADIAN, 'tesla':Units.StandardUnit.TESLA, 'volt':Units.StandardUnit.VOLT, 'watt':Units.StandardUnit.WATT, 'weber':Units.StandardUnit.WEBER}
PREFIX={'yotta':Units.Prefix.YOTTA, 'zetta':Units.Prefix.ZETTA, 'exa':Units.Prefix.EXA, 'peta':Units.Prefix.PETA, 'tera':Units.Prefix.TERA, 
        'giga':Units.Prefix.GIGA, 'mega':Units.Prefix.MEGA, 'kilo':Units.Prefix.KILO, 'hecto':Units.Prefix.HECTO, 'deca':Units.Prefix.DECA, 
        'deci':Units.Prefix.DECI, 'centi':Units.Prefix.CENTI, 'milli':Units.Prefix.MILLI, 'micro':Units.Prefix.MICRO, 'nano':Units.Prefix.NANO, 
        'pico':Units.Prefix.PICO, 'femto':Units.Prefix.FEMTO, 'atto':Units.Prefix.ATTO, 'zepto':Units.Prefix.ZEPTO, 'yocto':Units.Prefix.YOCTO}

INTERFACETYPE={'none':Variable.InterfaceType.NONE, 'public':Variable.InterfaceType.PUBLIC, 'private':Variable.InterfaceType.PRIVATE, 'public_and_private':Variable.InterfaceType.PUBLIC_AND_PRIVATE}


def create_model(name):
    """ 
    Create a CellML model.
    Args:
        name (:obj:`str`): the name of the CellML model
    Returns:
        :obj:`Model`: the CellML model created
    """
    model = Model(name)
    return model

def create_component(name):
    """ 
    Create a component.
    Args:
        name (:obj:`str`): the name of the component
    Returns:
        :obj:`Component`: the Component instance of the component created
    """
    component = Component(name)
    return component

def create_variable(name, units, initial_value=None, interface_type=None):
    """ 
    Create a variable.
    Args:
        name (:obj:`str`): the name of the variable
        units (:obj:`str` or Units): the name of the units, or the Units instance
        initial_value (:obj:`float` or 'str' or Variable): the initial value of the variable (float or string), or the Variable instance of the initial value
        interface_type (:obj:`Variable.InterfaceType`): the interface type of the variable
    Returns:
        :obj:`Variable`: the Variable instance of the variable created
    """
    variable = Variable(name)
    if isinstance(units, str):
        variable.setUnits(Units(units))
    else:
        variable.setUnits(units)
    if initial_value is not None:
       variable.setInitialValue(initial_value)
    if interface_type is not None:
       variable.setInterfaceType(interface_type)
    return variable

def create_units(name):
    """ 
    Create a units.
    Args:
        name (:obj:`str`): the name of the units
    Returns:
        :obj:`Units`: the Units instance of the units created
    """
    units = Units(name)
    return units

def csv2model(model,file_path):    
    """ 
    Read a csv file to create a cellml Model. The csv file should have the following columns:
     component: the name of the component
       variable: the name of the variable
       units: the name of the units of the variable
       initial_value: the initial value of the variable
       param: the type of the variable;
    Rules of interpretation: 
       1. if the initial_value is nan, then the initial_value is None;
       2. if the param column is 'param', then the variable is a parameter and it will be added to the params list;
          The initial_value of the variable will be None;
          The initial_value of the parameter will be the value in the initial_value column;
       3. if the param column is init, then the variable is a state variable, and the variable name + '_init' will be added to the params list;
          The initial_value of the variable will be variable name + '_init';
          The initial_value of the parameter (variable name + '_init') will be the value in the initial_value column;
       4. if the param column is external, then the variable is an external variable, and the variable will be added to the external_variables list;
           Note: the initial_value of the external variable will be None; 
    Args:
        file_path (:obj:`str`): the path of the csv file (including the file name and extension)
        model (:obj:`Model`): the CellML model created from the csv file (without units defined), not completely valid but holds the information of the model 
    Returns:
        :obj:`tuple`:
            * :obj:`bool`: whether the csv information was added to the model successfully
            * :obj:`list`: the list of the external variables of the model
    """
    # Read the csv file
    df = pd.read_csv(file_path, sep=',', header=0, index_col=False,na_values='nan')
    df['component']=df['component'].ffill()
    gdf=df.groupby('component')
    params_comp = Component('param')
    external_variables=[]
    for component_name, groupi in gdf:
        component=Component(component_name)          
        for index, row in groupi.iterrows():
            units_name = row['units']
            var_name = row['variable']
            variable = Variable(var_name)
            units = Units(units_name)
            variable.setUnits(units)
            variable.setInterfaceType(Variable.InterfaceType.PUBLIC)
            if pd.isna(row['initial_value']):
                pass
            elif row["param"]=='param':
                param = variable.clone()
                param.setInitialValue(row['initial_value'])
                if not params_comp.addVariable(param):
                    return False,external_variables                                            
            elif row['param'] == 'init':
                param = Variable(var_name+'_init')
                variable.setInitialValue(param)
                param.setUnits(units)
                param.setInitialValue(row['initial_value'])
                if not params_comp.addVariable(param):
                    return False,external_variables
            else:
                variable.setInitialValue(row['initial_value'])  
            if not component.addVariable(variable):
                return False,external_variables
            elif row['param'] == 'external':
                external_variables.append(component.variable(var_name))  
        if not model.addComponent(component):
            return False,external_variables    
    if params_comp.variableCount()>0:        
        if not model.addComponent(params_comp):
            return False,external_variables
    return True,external_variables  

def csv2unitsModel(unitsModel, file_path):
    """"
    Read a csv file to add units to the model_with_units.
    The csv file should have the following columns:
        units: the name of the units
            unitName: the name of the unit
            prefix: the prefix of the unit
            exponent: the exponent of the unit
    Args:
        file_path (:obj:`str`): the path of the csv file (including the file name and extension)
        unitsModel (:obj:`Model`): the CellML model to hold the units definitions
    Returns:
        :obj:`bool`: whether the units are added successfully
    """
    # Read the csv file
    df = pd.read_csv(file_path, sep=',', header=0, index_col=False,na_values='nan')
    df['units']=df['units'].ffill()
    gdf=df.groupby('units')
    for units_name, groupi in gdf:
        iunits = Units(units_name)
        for index, row in groupi.iterrows():
            if pd.isna(row['unitName']):
               unitName = units_name+'_unit'+str(index)
            else:
                unitName = row['unitName']
            if pd.isna(row['prefix']):
                prefix = 0
            else:
                prefix = row['prefix']
            if pd.isna(row['exponent']):
                exponent = 1
            else:
                exponent = row['exponent']
            if pd.isna(row['multiplier']):
                multiplier = 1
            else:
                multiplier = row['multiplier']
            define_units(iunits, unitName, prefix=prefix, exponent=exponent, multiplier=multiplier)
        if unitsModel.addUnits(iunits):
            pass
        else:
            return False
    return True

def define_units(iunits, unitName, prefix=0, exponent=1, multiplier=1):
    """ 
    Args:
        iunits (:obj:`Units`): the Units instance to which the unit is added
        unitName (:obj:`str`, or StandardUnit standardUnit): the name of the unit or the StandardUnit constant
        prefix (:obj:`int`, 'str', or Units.Prefix constant): the prefix of the unit, the prefix can be an integer, a string or Units.Prefix
        exponent (:obj:`float`): the exponent of the unit
        multiplier (:obj:`float`): the multiplier of the unit
    """
    if unitName in BUILTIN_UNITS.keys():
        iunits.addUnit(BUILTIN_UNITS[unitName], prefix, exponent, multiplier)
    elif unitName in BUILTIN_UNITS.values():
        iunits.addUnit(unitName, prefix, exponent, multiplier)
    else:
        iunits.addUnit(unitName,prefix, exponent, multiplier)

def _checkUndefinedUnits(model):
    """ 
    Check the undefined units of a CellML model.
    Args:
        model (:obj:`Model`): the CellML model
    Returns:
        :obj:`set`: the names of the undefined Units of the CellML model
    """
    units_claimed = set()
    for comp_numb in range(model.componentCount()): # Does it count the import components?
        if not model.component(comp_numb).isImport(): # Check if the component is imported
            for var_numb in range(model.component(comp_numb).variableCount()):
                if model.component(comp_numb).variable(var_numb).units().name() != '':
                    if  not (model.component(comp_numb).variable(var_numb).units().name() in BUILTIN_UNITS.keys()):
                        units_claimed.add(model.component(comp_numb).variable(var_numb).units().name())
    units_defined = set()
    for unit_numb in range(model.unitsCount()):
        units_defined.add(model.units(unit_numb).name()) 
    units_undefined = units_claimed - units_defined
    return units_undefined

def add_component(model, component):
    """ 
    Add a component to a CellML model.
    Args:
        model (:obj:`Model`): the CellML model to which the component is added
        component (:obj:`Component`): the Component instance of the component to be added
    Returns:
        :obj:`bool`: whether the component is added successfully
    """
    if model.containsComponent(component):
        print('The component already exists in the model {}!'.format(model.name()))
        return False
    if model.addComponent(component):
        return True
    else:
        return False

def add_variable(component,variable):
    """ 
    Add a variable to a component.
    Args:
        component (:obj:`Component`): the component to which the variable is added
        variable (:obj:'Variable`): the Variable instance
    Returns:
        :obj:`bool`: whether the variable is added successfully
    """
    if component.hasVariable(variable):
        print('The variable already exists in the component {}!'.format(component.name()))
        return False
    if component.addVariable(variable):
        return True
    else:
        return False

def varmap(var1,var2,connection=True):
    """ 
    Map two variables.
    Args:
        var1 (:obj:`Variable`): the first variable to be mapped
        var2 (:obj:`Variable`): the second variable to be mapped
        connection (:obj:`bool`): whether the variables are connected
    Returns:
        :obj:`bool`: whether the variables are mapped successfully"""
    
    if connection:
        if not Variable.addEquivalence(var1, var2):
            return False
    else:
        if not Variable.removeEquivalence(var1, var2):
            return False
    return True

def equivalent_variables(variable):
    """ 
    Get the equivalent variables of given variable.
    Args:
        variable (:obj:`Variable`): the variable to which the equivalent variables are found
    Returns:
        eqv_set (:obj:`set`): the set of the equivalent variables
    """
    eqv_set=set()
    for i in range(variable.equivalentVariableCount()):
        eqv_set.add(variable.equivalentVariable(i))
    return eqv_set

def encapsulate(component_parent, component_children):
    """ 
    Encapsulate a component.
    Args:
        model (:obj:`Model`): the CellML model that includes the components to be encapsulated, the default value is None
        component_parent (:obj: Component'): the Component instance of the parent component
        component_children (:obj:`list`): the list of the Component instances of the children components
    Returns:
        :obj:`bool`: whether the components are encapsulated successfully
    """
    for component_child in component_children:
        if not component_parent.addComponent(component_child):
            return False
    return True

def add_equations(component, equations):
    """ Add equations to a component.
    Args:
        component (:obj:`Component`): the component to which the equations are added
        equations (:obj:`list`): the equations to be added to the component
    Returns:
        None
    """
    component.setMath(MATH_HEADER)            
    for equation in equations:
        component. appendMath(equation)
    component. appendMath(MATH_FOOTER)

def import_setup(model_path,full_path_imported_model, strict_mode=True):
    """ Import a CellML model to a CellML model.
    Args:
        model_path (:obj:`str`): the path of the CellML model to which the imported model is added excluding the file name and extension
        full_path_imported_model (:obj:`str`): the full path of the CellML model to be imported (including the file name and extension)
        strict_mode (:obj:`bool`): whether to use strict mode to import the CellML model
    Returns:
        :obj:`tuple`:
            * :obj:`ImportSource`: the ImportSource instance, None if the importer found issues
            * :obj:`Model` or 'str': the CellML model imported from the CellML file, issues string if the importer found issues"""
    import_model,issues,issue_details=parse_model(full_path_imported_model, strict_mode)
    if not import_model:
        return None, issues
    else:
        relative_path_os = os.path.relpath(full_path_imported_model,model_path)        
        relative_path=PurePath(relative_path_os).as_posix()
        importSource = ImportSource()
        importSource.setUrl(relative_path)
        importSource.setModel(import_model)
        return importSource, import_model

def importComponents(model,importSource,import_components_dict):
    """ Import components to a CellML model.
    Args:
        model (:obj:`Model`): the CellML model to which the components are imported
        importSource (:obj:`ImportSource`): the ImportSource instance
        import_model (:obj:`Model`): the CellML model to be imported
        import_components_dict (:obj:`dict`): the dictionary of the components to be imported, in the format of {component_name: component_reference}
    Returns:
        :obj:`bool`: whether the components are imported successfully
        """  
    if not importSource.hasModel():
            print('The import source is not valid.')
            return False
    else:
        import_model=importSource.model() 
    for component in list(import_components_dict.keys()):
        c = Component(component)
        c.setImportSource(importSource)
        c.setImportReference(import_components_dict[component])
        if c.isResolved():
            dummy_c = import_model.component(c.importReference()).clone()
            while(dummy_c.variableCount()):
                if not c.addVariable(dummy_c.variable(0)):
                    return False
            if not model.addComponent(c):
                return False
        else:
            print('Component {} is not resolved!'.format(component))
            return False
    return True

def importUnits(model,importSource):
    """" Import units to a CellML model.
    Args:
        model (:obj:`Model`): the CellML model to which the units are imported
        importSource (:obj:`ImportSource`): the ImportSource instance
    Returns:
        :obj:`set`: the name of the units yet to be defined in the CellML model
    """
    units_undefined=_checkUndefinedUnits(model)
    if len(units_undefined)==0:
        print('All the units are defined!')
        return units_undefined
    if not importSource.hasModel():
            print('The import source is not valid.')
            return units_undefined   
    if len(units_undefined)>0:
        # Get the intersection of the units_undefined and the units defined in the import source
            units_model=importSource.model()
            existing_units=set([units_model.units(unit_numb).name() for unit_numb in range(units_model.unitsCount())]) # Get the units names defined in the import source
            units_to_import = units_undefined.intersection(existing_units)
            units_to_define = units_undefined - units_to_import    
    for unit in units_to_import:
        iunit=Units(unit)
        iunit.setImportSource(importSource)
        iunit.setImportReference(unit)
        model.addUnits(iunit)       
    return units_to_define


def infix_to_mathml(infix, yvar, voi=''):
    """ Convert an infix expression to a MathML expression.
    Args:
        infix (:obj:`str`): the infix expression
        yvar (:obj:`str`): the name of the dependent variable
        voi (:obj:`str`): the name of the variable of integration
    Returns:
        :obj:`str`: the MathML expression"""
    
    if voi!='':
        preforumla = '<apply> \n <eq/> <apply> <diff/> <bvar> <ci>'+ voi + '</ci> </bvar> <ci>' + yvar + '</ci> </apply> \n'
    else:
        preforumla = '<apply> \n <eq/> <ci>'+ yvar + '</ci>'    
    postformula = '\n </apply> \n'
    p = libsbml.parseL3Formula (infix)
    mathstr = libsbml.writeMathMLToString (p)
    # remove the <math> tags in the mathML string, and the namespace declaration will be added later according to the CellML specification
    mathstr = mathstr.replace ('<math xmlns="http://www.w3.org/1998/Math/MathML">', '')
    mathstr = mathstr.replace ('</math>', '')
    mathstr = mathstr.replace ('<?xml version="1.0" encoding="UTF-8"?>', '')
    # temporary solution to add cellml units for constant in the mathML string, replace <cn type="integer"> to <cn cellml:units="dimensionless">
    mathstr = mathstr.replace ('<cn type="integer">', '<cn cellml:units="dimensionless">')
    # add left side of the equation       
    mathstr = preforumla + mathstr + postformula
    return mathstr

def get_equations(model):
    """ Get the equations of a CellML model.
    Args:
        model (:obj:`Model`): the CellML model
    Returns:
        :obj:`dict`: the equations of the CellML model, in the format of {component_name: equation}"""
    equations = {}
    def _getEquations(component):
        if component.math()!='':
            equations.update({component.name():component.math()})
        if component.componentCount()>0:
            for c in range(component.componentCount()):                   
                   _getEquations(component.component(c))
    
    for c in range(model.componentCount()):
            _getEquations(model.component(c))
    return equations

def get_equations_present(model):
    """ Get the equations of a CellML model, in the format of MathML presentation.
    Args:
        model (:obj:`Model`): the CellML model
    Returns:
        obj:'list': the list of MathML presentation
    """
    equations = get_equations(model)
    math_json = []
    xslt = etree.parse("ctopff.xsl")
    tran_c2p = etree.XSLT(xslt)
    def m_c2p(math_c):
        #preff = '{http://www.w3.org/1998/Math/MathML}'
        if '<math ' not in math_c:
            math_c = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + math_c + '</math>'
        # separate the math_c according to <math> and </math>
        math_c_reg=math_c.replace('\n','')
        regex = r'(<math[^>]*>)(.*?)(</math>)'
        math_match = re.findall(regex, math_c_reg)
        math_present = []
        for tuple in math_match:
            submath_c = ''.join(tuple)
            if '<math ' not in submath_c:
                submath_c = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + submath_c + '</math>'

            mml_dom = etree.fromstring(submath_c)
            mmldom = tran_c2p(mml_dom)
            math_present.append(str(mmldom).replace('·', '&#xB7;').replace('−', '-').replace('<?xml version="1.0"?>', '<?xml version="1.0" encoding="UTF-8"?>'))  
                    
        return math_present
    
    for key,value in equations.items():
        math_json.append((key,m_c2p(value)))
    return math_json
