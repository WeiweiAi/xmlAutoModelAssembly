import libsedml
from libsedml import SedOperationReturnValue_toString


# Create a lookup table for the SED-ML type codes
SEDML_TYPE_CODES = [libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,
                    libsedml.SEDML_SIMULATION_ONESTEP,
                    libsedml.SEDML_SIMULATION_STEADYSTATE,
                    libsedml.SEDML_RANGE_UNIFORMRANGE,
                    libsedml.SEDML_RANGE_VECTORRANGE,
                    libsedml.SEDML_RANGE_FUNCTIONALRANGE,
                    libsedml.SEDML_TASK,
                    libsedml.SEDML_TASK_REPEATEDTASK,
                    libsedml.SEDML_TASK_PARAMETER_ESTIMATION,
                    libsedml.SEDML_DATA_RANGE                    

]

SEDML_TYPE_CODES_TABLE = dict(zip(SEDML_TYPE_CODES, [libsedml.SedTypeCode_toString(i) for i in SEDML_TYPE_CODES]))

# Get the TypeCode from a string
def SEDML_TYPE_CODE_FROM_STR(type_str):
    for key, value in SEDML_TYPE_CODES_TABLE.items():
        if value == type_str:
            return key
    return None
    

def operation_flag_check(operation_flag, operation_name):
    if operation_flag<0:
        print('{operation_name} returned an error: {flag}'.format(operation_name=operation_name,flag=SedOperationReturnValue_toString(operation_flag)))
        return False
    else:
        return True

def validate_sedml(file_name):
    doc = libsedml.readSedMLFromFile(file_name)
    num_errors = doc.getNumErrors(libsedml.LIBSEDML_SEV_ERROR)
    num_warnings = doc.getNumErrors(libsedml.LIBSEDML_SEV_WARNING)

    print ('file: {0} has {1} warning(s) and {2} error(s)'
        .format(file_name, num_warnings, num_errors))

    log = doc.getErrorLog()
    for i in range(log.getNumErrors()):
        err = log.getError(i)
        print('{0} L{1} C{2}: {3}'.format(err.getSeverityAsString(), err.getLine(), err.getColumn(), err.getMessage()))

    return num_errors

def target_component_variable(component, variable):
    """
    Create a target for a variable in a CellML model.
    """
    return "/cellml:model/cellml:component[@name=&quot;{component}&quot;]/cellml:variable[@name=&quot;{variable}&quot;]".format(component=component, variable=variable)

def target_component_variable_initial(component, variable):
    """
    Create a target for a variable in a CellML model.
    """
    return "/cellml:model/cellml:component[@name=&quot;{component}&quot;]/cellml:variable[@name=&quot;{variable}&quot;]/@initial_value".format(component=component, variable=variable)

def get_component_variable(target):
    """
    Get the component and variable from a target.
    """
    component = target.split('/')[2].split('"')[1]
    variable = target.split('/')[4].split('"')[1]
    return component, variable

def _setDimensionDescription(sed_dimDescription, dimDict):
    """Set the dimensions and data types of the external data.
    Args:
        sed_dimDescription (:obj:`SedDimensionDescription`): an instance of :obj:`SedDimensionDescription`
        dimDict (:obj:`dict`): The dictionary format: 
                               {'id':'time','name':None,'indexType':'double',
                                   'dim2':{'id':'columnName','name':None,'indexType':'string','valueType':'double','atomicName':'concentration'}
                                   }
    Returns:
        :obj:`bool`: whether the dimension description is set successfully
    """
    dim1_Description=libsedml.CompositeDescription()
    if not operation_flag_check(dim1_Description.setIndexType(dimDict['indexType']), 'Set the indexType attribute of a dimension description'):
        return False
    if not operation_flag_check(dim1_Description.setId(dimDict['id']), 'Set the id attribute of a dimension description'):
        return False
    if not operation_flag_check(dim1_Description.setName(dimDict['name']), 'Set the name attribute of a dimension description'):
        return False
    if 'dim2' in dimDict:
        dim2_Description=dim1_Description.createCompositeDescription()
        if not operation_flag_check(dim2_Description.setIndexType(dimDict['dim2']['indexType']), 'Set the indexType attribute of a dimension description'):
            return False
        if not operation_flag_check(dim2_Description.setId(dimDict['dim2']['id']), 'Set the id attribute of a dimension description'):
            return False
        if not operation_flag_check(dim2_Description.setName(dimDict['dim2']['name']), 'Set the name attribute of a dimension description'):
            return False
        
        atomic_Desc=dim2_Description.createAtomicDescription()
        if not operation_flag_check(atomic_Desc.setValueType(dimDict['dim2']['valueType']), 'Set the valueType attribute of a dimension description'):
            return False
      #  if not operation_flag_check(dim2_Description.setAtomicName(dimDict['dim2']['atomicName']), 'Set the atomicName attribute of a dimension description'):
      #      return False
    sed_dimDescription.append(dim1_Description)
    return True 

def _get_dict_dimDescription(sed_dimDescription):
    """Get the information of a dimension description
    Args:
        sed_dimDescription (:obj:`SedDimensionDescription`): an instance of :obj:`SedDimensionDescription`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'time','name':None,'indexType':'double',
                       'dim2':{'id':'columnName','name':None,'indexType':'string','valueType':'double','atomicName':'concentration'}
                       }
    """
    dict_dimDescription = {}
    dim1_Description = sed_dimDescription.get(0)
    dict_dimDescription['id'] = dim1_Description.getId()
    dict_dimDescription['name'] = dim1_Description.getName()
    dict_dimDescription['indexType'] = dim1_Description.getIndexType()
    dict_dimDescription['dim2'] = {}
    dim2_Description = dim1_Description.getCompositeDescription(0)
    dict_dimDescription['dim2']['id'] = dim2_Description.getId()
    dict_dimDescription['dim2']['name'] = dim2_Description.getName()
    dict_dimDescription['dim2']['indexType'] = dim2_Description.getIndexType()
    dict_dimDescription['dim2']['valueType'] = dim2_Description.get(0).getValueType()
    dict_dimDescription['dim2']['atomicName'] = dim2_Description.get(0).getName()
    return dict_dimDescription

def _setSlice(sed_slice, reference,value=None,index=None,startIndex=None,endIndex=None):
    """Create a slice for a data source. Each slice removes one dimension from the data hypercube
    Args:
        sed_slice (:obj:`SedSlice`): an instance of :obj:`SedSlice`
        reference (:obj:`str`): The reference attribute references one of the indices described in the dimensionDescription of the data source.
        value (:obj:`str`, optional): The value attribute takes the value of a specific index in the referenced set of indices
        index (:obj:`int`, optional): index, The index attribute is an SIdRef to a RepeatedTask. This is for cases where the Slice refers to data
                                      generated by potentially-nested RepeatedTask elements.
        startIndex (:obj:`int`, optional): start index
        endIndex (:obj:`int`, optional): end index
    Returns:
        :obj:`bool`: whether the slice is set successfully
    """
    if not operation_flag_check(sed_slice.setReference(reference), 'Set the reference attribute of a slice'):
        return False
    if value:
        if not operation_flag_check(sed_slice.setValue(value), 'Set the value attribute of a slice'):
            return False          
    if index:
        if not operation_flag_check(sed_slice.setIndex(index), 'Set the index attribute of a slice'):
            return False
    if startIndex:
        if not operation_flag_check(sed_slice.setStartIndex(startIndex), 'Set the startIndex attribute of a slice'):
            return False
    if endIndex:
        if not operation_flag_check(sed_slice.setEndIndex(endIndex), 'Set the endIndex attribute of a slice'):
            return False
    return True

def _get_dict_slice(sed_slice):
    """Get the information of a slice
    Args:
        sed_slice (:obj:`SedSlice`): an instance of :obj:`SedSlice`
    Returns:
        :obj:`dict`: The dictionary format: {'reference':'time','value':None,'index':None,'startIndex':None,'endIndex':None}
    """
    dict_slice = {}
    dict_slice['reference'] = sed_slice.getReference()
    if sed_slice.isSetValue():
        dict_slice['value'] = sed_slice.getValue()
    if sed_slice.isSetIndex():
        dict_slice['index'] = sed_slice.getIndex()
    if sed_slice.isSetStartIndex():
        dict_slice['startIndex'] = sed_slice.getStartIndex()
    if sed_slice.isSetEndIndex():
        dict_slice['endIndex'] = sed_slice.getEndIndex()
    return dict_slice

def _setDataSource(sed_dataSource,dict_dataSource):
    """DataSource extracts chunks out of the dataset provided by the outer DataDescription element, can be used anywhere in the SED-ML document.
    Args:
        sed_dataSource (:obj:`SedDataSource`): an instance of :obj:`SedDataSource`
        dict_dataSource (:obj:`dict`): The indexSet attribute references the id of index provided by NuML elements with indexType.
                                       If a DataSource does not defined the indexSet attribute, it will contain Slice elements.
                                       The dictionary format: {'id':'data_source_1','name':None,'indexSet':None,'listOfSlices':[dict_slice]}                                                
    Returns:
        :obj:`bool`: whether the data source is set successfully                                                
  
    """
    if not operation_flag_check(sed_dataSource.setId(dict_dataSource['id']), 'Set the id attribute of a data source'):
        return False
    if 'name' in dict_dataSource:
        if not operation_flag_check(sed_dataSource.setName(dict_dataSource['name']), 'Set the name attribute of a data source'):
            return False
    if 'indexSet' in dict_dataSource:
        if not operation_flag_check(sed_dataSource.setIndexSet(dict_dataSource['indexSet']), 'Set the indexSet attribute of a data source'):
            return False
    elif 'listOfSlices' in dict_dataSource:
        for dict_slice in dict_dataSource['listOfSlices']:
            sed_slice = sed_dataSource.createSlice()
            if not _setSlice(sed_slice, dict_slice['reference'],dict_slice['value'],dict_slice['index'],dict_slice['startIndex'],dict_slice['endIndex']):
                return False 
    else:        
        print('The indexSet attribute is not defined nor the slice elements of a data source are defined.')
        return False
       
    return True

def _get_dict_dataSource(sed_dataSource):
    """Get the information of a data source
    Args:
        sed_dataSource (:obj:`SedDataSource`): an instance of :obj:`SedDataSource`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'data_source_1','name':None,'indexSet':None,'listOfSlices':[dict_slice]} 
    """
    dict_dataSource = {}
    dict_dataSource['id'] = sed_dataSource.getId()
    if sed_dataSource.isSetName():
        dict_dataSource['name'] = sed_dataSource.getName()
    if sed_dataSource.isSetIndexSet():
        dict_dataSource['indexSet'] = sed_dataSource.getIndexSet()
    if sed_dataSource.getNumSlices()>0:
        dict_dataSource['listOfSlices'] = []
    for sed_slice in sed_dataSource.getListOfSlices():
        dict_dataSource['listOfSlices'].append(_get_dict_slice(sed_slice))
    return dict_dataSource

def create_dataDescription(doc, dict_dataDescription):
    """
    Create a data description
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_dataDescription (:obj:`dict`): The dictionary format: 
                                            {'id':'data_description_1','name':None, 'source':'file.xml','format':None,
                                             'dimensionDescription':dict_dimDescription,'listOfDataSources':[dict_dataSource]
                                             }. 
    Returns:
        :obj:`bool` or `SedDataDescription`: If the data description is created successfully, return the instance of :obj:`SedDataDescription`; otherwise, return False
    """	
    sed_dataDescription = doc.createDataDescription()
    if not operation_flag_check(sed_dataDescription.setId(dict_dataDescription['id']), 'Set the id attribute of a data description'):
        return False
    if not operation_flag_check(sed_dataDescription.setSource(dict_dataDescription['source']), 'Set the source attribute of a data description'):
        return False
    if 'format' in dict_dataDescription:
        if not operation_flag_check(sed_dataDescription.setFormat(dict_dataDescription['format']), 'Set the format attribute of a data description'):
            return False
    if 'name' in dict_dataDescription:
        if not operation_flag_check(sed_dataDescription.setName(dict_dataDescription['name']), 'Set the name attribute of a data description'):
            return False
    if 'dimensionDescription' in dict_dataDescription:
        sed_dimDescription = sed_dataDescription.createDimensionDescription()
        dict_dimDescription=dict_dataDescription['dimensionDescription']
        if not _setDimensionDescription(sed_dimDescription, dict_dimDescription):
            return False
    if 'listOfDataSources' in dict_dataDescription:
        for dict_dataSource in dict_dataDescription['listOfDataSources']:
            sed_dataSource = sed_dataDescription.createDataSource()
            if not _setDataSource(sed_dataSource, dict_dataSource):
                return False
    return sed_dataDescription

def get_dict_dataDescription(sed_dataDescription):
    """
    Get the information of a data description
    Args:
        sed_dataDescription (:obj:`SedDataDescription`): an instance of :obj:`SedDataDescription`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'data_description_1','name':None, 'source':'file.xml','format':None,
                       'dimensionDescription':dict_dimDescription,'listOfDataSources':[dict_dataSource]
                       }. 
    """
    dict_dataDescription = {}
    dict_dataDescription['id'] = sed_dataDescription.getId()
    dict_dataDescription['source'] = sed_dataDescription.getSource()
    if sed_dataDescription.isSetFormat():
        dict_dataDescription['format'] = sed_dataDescription.getFormat()
    if sed_dataDescription.isSetName():
        dict_dataDescription['name'] = sed_dataDescription.getName()
    if sed_dataDescription.isSetDimensionDescription():
        dict_dataDescription['dimensionDescription'] = {}
        sed_dimDescription = sed_dataDescription.getDimensionDescription()
        dict_dataDescription['dimensionDescription'] = _get_dict_dimDescription(sed_dimDescription)
    if sed_dataDescription.getNumDataSources()>0:
        dict_dataDescription['listOfDataSources'] = []
    for sed_dataSource in sed_dataDescription.getListOfDataSources():
        dict_dataDescription['listOfDataSources'].append(_get_dict_dataSource(sed_dataSource))
    return dict_dataDescription

def change_init(sedModel, dict_change_Attribute):
    """"
    Define updates on the attribute values of the corresponding model.
    Args:
        sedModel (:obj:`SedModel`): an instance of :obj:`SedModel`
        dict_change_Attribute (:obj:`dict`): The dictionary format: {'target': target_component_variable,'newValue':'1.0'}
    Returns:
        :obj:`bool`: whether the change attribute is created successfully
    """	
    change = sedModel.createChangeAttribute()
    if not operation_flag_check(change.setTarget(dict_change_Attribute['target']), 'Set the target attribute of a change'):
        return False
    if not operation_flag_check(change.setNewValue(dict_change_Attribute['newValue']), 'Set the newValue attribute of a change'):
        return False
    return True
    
doc = libsedml.SedDocument(1, 4)

def create_sedModel(doc,dict_model):
    """
    Create the models used in a simulation experiment
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_model (:obj:`dict`): The dictionary format: {'id':'model1','source':'model.cellml','language':'urn:sedml:language:cellml','listOfChanges':[dict_change_Attribute]}
    Returns:
        :obj:`bool` or `SedModel`: If the model is created successfully, return the instance of :obj:`SedModel`; otherwise, return False"""
    sedModel = doc.createModel()
    if not operation_flag_check(sedModel.setId(dict_model['id']), 'Set the id attribute of a model'):
        return False
    if not operation_flag_check(sedModel.setSource(dict_model['source']), 'Set the source attribute of a model'):
        return False
    if not operation_flag_check(sedModel.setLanguage(dict_model['language']), 'Set the language attribute of a model'):
        return False
    if 'listOfChanges' in dict_model:
        for dict_change_Attribute in dict_model['listOfChanges']:
            if not change_init(sedModel, dict_change_Attribute):
                return False
    return sedModel

def get_dict_model(sedModel):
    """
    Get the information of a model
    Args:
        sedModel (:obj:`SedModel`): an instance of :obj:`SedModel`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'model1','source':'model.cellml','language':'urn:sedml:language:cellml','listOfChanges':[dict_change_Attribute]}
    """
    dict_model = {}
    dict_model['id'] = sedModel.getId()
    dict_model['source'] = sedModel.getSource()
    dict_model['language'] = sedModel.getLanguage()
    if sedModel.getNumChanges()>0:
        dict_model['listOfChanges'] = []
    for change in sedModel.getListOfChanges():
        dict_change_Attribute = {}
        if change.isSedChangeAttribute():
            dict_change_Attribute['target'] = change.getTarget()
            dict_change_Attribute['newValue'] = change.getNewValue()
            dict_model['listOfChanges'].append(dict_change_Attribute)
        else:
            print('The change is not an attribute change.')
            return False        
    return dict_model

def _setAlgorithmParameter(sed_algorithm, dict_algorithmParameter):
    """Parameterize a particular simulation algorithm.
    Args:
        sed_algorithm (:obj:`SedAlgorithm`): an instance of :obj:`SedAlgorithm`
        dict_algorithmParameter (:obj:`dict`): The dictionary format: {'kisaoID':'KISAO:0000019','value':'1.0','name':'optional, describe the meaning of the param'}
                                               if the KiSAO term is a value, the string should contain a number; 
                                               if the KiSAO term is a Boolean, the string should contain the string \true" or \false", etc. 
                                               The string must be non-empty; to explicitly state that a value is not set, this should be encoded in the string as a KISAO:0000629, which indicates that the value is Null.
    Returns:
        :obj:`bool`: whether the algorithm parameter is set successfully
    """
    sed_algorithmParameter = sed_algorithm.createAlgorithmParameter()
    if 'name' in dict_algorithmParameter:
        if not operation_flag_check(sed_algorithmParameter.setName(dict_algorithmParameter['name']), 'Set the name attribute of an algorithm parameter'):
            return False
    if not operation_flag_check(sed_algorithmParameter.setKisaoID(dict_algorithmParameter['kisaoID']), 'Set the kisaoID attribute of an algorithm parameter'):
        return False
    if not operation_flag_check(sed_algorithmParameter.setValue(dict_algorithmParameter['value']), 'Set the value attribute of an algorithm parameter'):
        return False
    return True  

def _get_dict_algorithmParameter(sed_algorithmParameter):
    """Get the information of an algorithm parameter
    Args:
        sed_algorithmParameter (:obj:`SedAlgorithmParameter`): an instance of :obj:`SedAlgorithmParameter`
    Returns:
        :obj:`dict`: The dictionary format: {'kisaoID':'KISAO:0000019','value':'1.0','name':'optional, describe the meaning of the param',}
    """
    dict_algorithmParameter = {}
    if sed_algorithmParameter.isSetName():
        dict_algorithmParameter['name'] = sed_algorithmParameter.getName()
    dict_algorithmParameter['kisaoID'] = sed_algorithmParameter.getKisaoID()
    dict_algorithmParameter['value'] = sed_algorithmParameter.getValue()
    return dict_algorithmParameter

def _setAlgorithm(sed_algorithm, dict_algorithm):
    """Defines the simulation algorithms used for the execution of the simulation
    Args:
        sed_algorithm (:obj:`SedAlgorithm`): an instance of :obj:`SedAlgorithm`
        dict_algorithm (:obj:`dict`, optional): the dictionary format: {'kisaoID':'KISAO:0000030','name':'optional,e.g,time course simulation over 100 minutes', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
    """
    if not operation_flag_check(sed_algorithm.setKisaoID(dict_algorithm['kisaoID']), 'Set the kisaoID attribute of an algorithm'):
        return False
    if 'name' in dict_algorithm:
        if not operation_flag_check(sed_algorithm.setName(dict_algorithm['name']), 'Set the name attribute of an algorithm'):
            return False
    if 'listOfAlgorithmParameters' in dict_algorithm:
        for dict_algorithmParameter in dict_algorithm['listOfAlgorithmParameters']:
            if not _setAlgorithmParameter(sed_algorithm, dict_algorithmParameter):
                return False
    return True

def get_dict_algorithm(sed_algorithm):
    """Get the information of an algorithm
    Args:
        sed_algorithm (:obj:`SedAlgorithm`): an instance of :obj:`SedAlgorithm`
    Returns:
        :obj:`dict`: The dictionary format: {'kisaoID':'KISAO:0000030','name':'optional,e.g,time course simulation over 100 minutes', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
    """
    dict_algorithm = {}
    dict_algorithm['kisaoID'] = sed_algorithm.getKisaoID()
    if sed_algorithm.isSetName():
        dict_algorithm['name'] = sed_algorithm.getName()
    if sed_algorithm.getNumAlgorithmParameters()>0:
        dict_algorithm['listOfAlgorithmParameters'] = []
    for sed_algorithmParameter in sed_algorithm.getListOfAlgorithmParameters():
        dict_algorithm['listOfAlgorithmParameters'].append(_get_dict_algorithmParameter(sed_algorithmParameter))
    return dict_algorithm

def create_sim_UniformTimeCourse(doc,dict_uniformTimeCourse):
    """
    Create a uniform time course simulation that calculates a time course output with equidistant time points.
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_uniformTimeCourse (:obj:`dict`): The dictionary format: 
                                              {'id':'timeCourse1', 'type':libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,'algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
    Returns:
        :obj:`bool` or `SedUniformTimeCourse`: If the simulation is created successfully, return the instance of :obj:`SedUniformTimeCourse`; otherwise, return False
    """
    sim = doc.createUniformTimeCourse()
    if not operation_flag_check(sim.setId(dict_uniformTimeCourse['id']), 'Set the id attribute of a simulation'):
        return False
    if not operation_flag_check(sim.setInitialTime(dict_uniformTimeCourse['initialTime']), 'Set the initialTime attribute of a simulation'):
        return False
    if not operation_flag_check(sim.setOutputStartTime(dict_uniformTimeCourse['outputStartTime']), 'Set the outputStartTime attribute of a simulation'):
        return False
    if not operation_flag_check(sim.setOutputEndTime(dict_uniformTimeCourse['outputEndTime']), 'Set the outputEndTime attribute of a simulation'):
        return False
    if not operation_flag_check(sim.setNumberOfPoints(dict_uniformTimeCourse['numberOfSteps']), 'Set the numberOfPoints attribute of a simulation'):
        return False
    alg = sim.createAlgorithm()
    if not _setAlgorithm(alg, dict_uniformTimeCourse['algorithm']):
        return False     
    return sim

def get_dict_uniformTimeCourse(sim):
    """
    Get the information of a uniform time course simulation
    Args:
        sim (:obj:`SedUniformTimeCourse`): an instance of :obj:`SedUniformTimeCourse`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'timeCourse1', 'type':libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE, 'algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
    """
    dict_uniformTimeCourse = {}
    dict_uniformTimeCourse['id'] = sim.getId()
    dict_uniformTimeCourse['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    dict_uniformTimeCourse['initialTime'] = sim.getInitialTime()
    dict_uniformTimeCourse['outputStartTime'] = sim.getOutputStartTime()
    dict_uniformTimeCourse['outputEndTime'] = sim.getOutputEndTime()
    dict_uniformTimeCourse['numberOfSteps'] = sim.getNumberOfPoints()
    sed_algorithm = sim.getAlgorithm()
    dict_uniformTimeCourse['algorithm']=get_dict_algorithm(sed_algorithm)
    return dict_uniformTimeCourse

def create_sim_OneStep(doc,dict_oneStep):
    """
    Create a one step simulation that calculates one further output step for the model from its current state.
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_oneStep (:obj:`dict`): The dictionary format: {'id':'oneStep1','type':libsedml.SEDML_SIMULATION_ONESTEP, 'algorithm':dict_algorithm, 'step':0.1}
    Returns:
        :obj:`bool` or `SedOneStep`: If the simulation is created successfully, return the instance of :obj:`SedOneStep`; otherwise, return False
    """
    
    sim = doc.createOneStep()
    if not operation_flag_check(sim.setId(dict_oneStep['id']), 'Set the id attribute of a simulation'):
        return False
    if not operation_flag_check(sim.setStep(dict_oneStep['step']), 'Set the step attribute of a simulation'):
        return False
    alg = sim.createAlgorithm()
    if not _setAlgorithm(alg, dict_oneStep['algorithm']):
        return False 
    return sim

def get_dict_oneStep(sim):
    """
    Get the information of a one step simulation
    Args:
        sim (:obj:`SedOneStep`): an instance of :obj:`SedOneStep`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'oneStep1','type':libsedml.SEDML_SIMULATION_ONESTEP, 'algorithm':dict_algorithm, 'step':0.1}
    """
    dict_oneStep = {}
    dict_oneStep['id'] = sim.getId()
    dict_oneStep['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    dict_oneStep['step'] = sim.getStep()
    sed_algorithm = sim.getAlgorithm()
    dict_oneStep['algorithm']=get_dict_algorithm(sed_algorithm)
    return dict_oneStep

def create_sim_SteadyState(doc,dict_steadyState):
    """
    Create a steady state simulation that calculates a steady state output for the model.
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_steadyState (:obj:`dict`): The dictionary format: {'id':'steadyState1', 'type':libsedml.SEDML_SIMULATION_STEADYSTATE ,'algorithm':dict_algorithm}
    Returns:
        :obj:`bool` or `SedSteadyState`: If the simulation is created successfully, return the instance of :obj:`SedSteadyState`; otherwise, return False
    """
    sim = doc.createSteadyState()
    if not operation_flag_check(sim.setId(dict_steadyState['id']), 'Set the id attribute of a simulation'):
        return False
    alg = sim.createAlgorithm()
    if not _setAlgorithm(alg, dict_steadyState['algorithm']):
        return False 
    return sim

def get_dict_steadyState(sim):
    """
    Get the information of a steady state simulation
    Args:
        sim (:obj:`SedSteadyState`): an instance of :obj:`SedSteadyState`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'steadyState1','type':libsedml.SEDML_SIMULATION_STEADYSTATE , 'algorithm':dict_algorithm}
    """
    dict_steadyState = {}
    dict_steadyState['id'] = sim.getId()
    dict_steadyState['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    sed_algorithm = sim.getAlgorithm()
    dict_steadyState['algorithm']=get_dict_algorithm(sed_algorithm)
    return dict_steadyState

def create_simulation(doc,dict_simulation):
    if dict_simulation['type'] == 'UniformTimeCourse':
        sim = create_sim_UniformTimeCourse(doc,dict_simulation)
    elif dict_simulation['type'] == 'OneStep':
        sim = create_sim_OneStep(doc,dict_simulation)
    elif dict_simulation['type'] == 'SteadyState':
        sim = create_sim_SteadyState(doc,dict_simulation)
    else:
        print('The simulation is not defined.')
        return False
    return sim

def get_dict_simulation(sim):
    if sim.isSedUniformTimeCourse():
        dict_simulation = get_dict_uniformTimeCourse(sim)
    elif sim.isSedOneStep():
        dict_simulation = get_dict_oneStep(sim)
    elif sim.isSedSteadyState():
        dict_simulation = get_dict_steadyState(sim)
    else:
        print('The simulation is not defined.')
        return False
    return dict_simulation

def create_task(doc,dict_task):
    """
    Create a task
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_task (:obj:`dict`): The dictionary format: {'id':'task1','type':libsedml.SEDML_TASK,'modelReference':'model1','simulationReference':'timeCourse1'}
    Returns:
        :obj:`bool` or `SedTask`: If the task is created successfully, return the instance of :obj:`SedTask`; otherwise, return False
    """
    task = doc.createTask()
    if not operation_flag_check(task.setId(dict_task['id']), 'Set the id attribute of a task'):
        return False
    if not operation_flag_check(task.setModelReference(dict_task['modelReference']), 'Set the modelReference attribute of a task'):
        return False
    if not operation_flag_check(task.setSimulationReference(dict_task['simulationReference']), 'Set the simulationReference attribute of a task'):
        return False
    return task

def get_dict_task(task):
    """
    Get the information of a task
    Args:
        task (:obj:`SedTask`): an instance of :obj:`SedTask`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'task1','type':libsedml.SEDML_TASK,'modelReference':'model1','simulationReference':'timeCourse1'}
    """
    dict_task = {}
    dict_task['id'] = task.getId()
    dict_task['type'] = libsedml.SedTypeCode_toString(task.getTypeCode())
    dict_task['modelReference'] = task.getModelReference()
    dict_task['simulationReference'] = task.getSimulationReference()
    return dict_task

def _setRange(repeatedTask,dict_range):
    """
    Set the range for a repeatedTask
    Args:
        repeatedTask (:obj:`SedRepeatedTask`): an instance of :obj:`SedRepeatedTask`
        dict_range (:obj:`dict`): The dictionary format could be one of the following:
                                    UniformRange: {'id':'range1','type':libsedml.SEDML_RANGE_UNIFORMRANGE, 'start':0.0,'end':10.0,'numberOfPoints':100,'type':'linear or log'}
                                    VectorRange: {'id':'range1','type':libsedml.SEDML_RANGE_VECTORRANGE,'values':[0.0,0.1,0.2,0.3,0.4,0.5]}
                                    DataRange: {'id':'range1','type':libsedml.SEDML_DATA_RANGE,'sourceReference':'data_source_1'} to construct a range by reference to external data
    Returns:
        :obj:`bool`: whether the range is set successfully
    """
    if dict_range['type'] == 'UniformRange':
        sed_range = repeatedTask.createUniformRange()
        if not operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setStart(dict_range['start']), 'Set the start attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setEnd(dict_range['end']), 'Set the end attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setNumberOfPoints(dict_range['numberOfPoints']), 'Set the numberOfPoints attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setType(dict_range['type']), 'Set the type attribute of a range'):
            return False
    elif dict_range['type'] == 'VectorRange':	
        sed_range = repeatedTask.createVectorRange()
        if not operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setValues(dict_range['values']), 'Set the values attribute of a range'):
            return False
    elif dict_range['type'] == 'DataRange':
        sed_range = repeatedTask.createDataRange()
        if not operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range'):
            return False
        if not operation_flag_check(sed_range.setSourceReference(dict_range['sourceReference']), 'Set the sourceReference attribute of a range'):
            return False
    else:
        print('The range is not defined.')
        return False
    return True

def _get_dict_range(sed_range):
    """
    Get the information of a range
    Args:
        sed_range (:obj:`SedRange`): an instance of :obj:`SedRange`
    Returns:
        :obj:`dict`: The dictionary format could be one of the following:
                      UniformRange: {'id':'range1','type':libsedml.SEDML_RANGE_UNIFORMRANGE, 'start':0.0,'end':10.0,'numberOfPoints':100,'type':'linear or log'}
                      VectorRange: {'id':'range1','type':libsedml.SEDML_RANGE_VECTORRANGE,'values':[0.0,0.1,0.2,0.3,0.4,0.5]}
                      DataRange: {'id':'range1','type':libsedml.SEDML_DATA_RANGE,'sourceReference':'data_source_1'} to construct a range by reference to external data
    """
    dict_range = {}
    dict_range['id'] = sed_range.getId()
    dict_range['type'] = libsedml.SedTypeCode_toString(sed_range.getTypeCode())
    if sed_range.isSedUniformRange():
        dict_range['start'] = sed_range.getStart()
        dict_range['end'] = sed_range.getEnd()
        dict_range['numberOfPoints'] = sed_range.getNumberOfPoints()
        dict_range['type'] = sed_range.getType()
    elif sed_range.isSedVectorRange():
        dict_range['values'] = sed_range.getValues()
    elif sed_range.isSedDataRange():
        dict_range['sourceReference'] = sed_range.getSourceReference()
    else:
        print('The range is not defined.')
        return False
    return dict_range

def _modifyModel4Task(task,dict_setValue):
    """
    Modify the model for a subTask or repeatedTask
    Args:
        task (:obj:`SedRepeatedTask` or `SedSubTask` ): an instance of :obj:`SedRepeatedTask` or `SedSubTask`
        dict_setValue (:obj:`dict`): The dictionary format: {'target':target_component_variable,'modelReference':'model1','symbol':None,'range':None,'math':None}
    Returns:
        :obj:`bool`: whether the model is modified successfully
    """
    setValue = task.createTaskChange()
    if not operation_flag_check(setValue.setTarget(dict_setValue['target']), 'Set the target attribute of a set value'):
        return False
    if not operation_flag_check(setValue.setModelReference(dict_setValue['modelReference']), 'Set the modelReference attribute of a set value'):
        return False
    if 'symbol' in dict_setValue:
        if not operation_flag_check(setValue.setSymbol(dict_setValue['symbol']), 'Set the symbol attribute of a set value'):
            return False
    if 'range' in dict_setValue:
        if not operation_flag_check(setValue.setRange(dict_setValue['range']), 'Set the range attribute of a set value'):
            return False
    if 'math' in dict_setValue:
        if not operation_flag_check(setValue.setMath(libsedml.parseL3Formula(dict_setValue['math'])), 'Set the math attribute of a set value'):
            return False
    return True

def _get_dict_setValue(setValue):
    """
    Get the information of a set value
    Args:
        setValue (:obj:`SedSetValue`): an instance of :obj:`SedSetValue`
    Returns:
        :obj:`dict`: The dictionary format: {'target':target_component_variable,'modelReference':'model1','symbol':None,'range':None,'math':None}
    """
    dict_setValue = {}
    dict_setValue['target'] = setValue.getTarget()
    dict_setValue['modelReference'] = setValue.getModelReference()
    if setValue.isSetSymbol():
        dict_setValue['symbol'] = setValue.getSymbol()
    if setValue.isSetRange():
        dict_setValue['range'] = setValue.getRange()
    if setValue.isSetMath():
        dict_setValue['math'] = libsedml.formulaToL3String(setValue.getMath())
    return dict_setValue

def _setSubTask(subTask,dict_subTask):
    """
    Set the subtask which is executed in every iteration of the enclosing RepeatedTask
    Args:
        subTask (:obj:`SedSubTask`): an instance of :obj:`SedSubTask`
        dict_subTask (:obj:`dict`): The dictionary format: {'order':1,'task':'task1','listOfChanges':[dict_setValue]}
    Returns:
        :obj:`bool` or `SedSubTask`: If the subTask is created successfully, return the instance of :obj:`SedSubTask`; otherwise, return False
    """
    if not operation_flag_check(subTask.setOrder(dict_subTask['order']), 'Set the order attribute of a sub task'):
        return False
    if not operation_flag_check(subTask.setTask(dict_subTask['task']), 'Set the task attribute of a sub task'):
        return False
    if 'listOfChanges' in dict_subTask:
        for dict_setValue in dict_subTask['listOfChanges']:
            if not _modifyModel4Task(subTask,dict_setValue):
                return False
    return subTask	

def _get_dict_subTask(subTask):
    """
    Get the information of a subtask
    Args:
        subTask (:obj:`SedSubTask`): an instance of :obj:`SedSubTask`
    Returns:
        :obj:`dict`: The dictionary format: {'order':1,'task':'task1','listOfChanges':[dict_setValue]}
    """
    dict_subTask = {}
    dict_subTask['order'] = subTask.getOrder()
    dict_subTask['task'] = subTask.getTask()
    if subTask.getNumTaskChanges()>0:
        dict_subTask['listOfChanges'] = []
    for taskChange in subTask.getListOfTaskChanges():
        dict_subTask['listOfChanges'].append(_get_dict_setValue(taskChange))
    return dict_subTask

def create_repeatedTask(doc,dict_repeatedTask):
    """
    Create a repeated task that provides a looping construct, allowing complex tasks to be composed from individual tasks. 
    The RepeatedTask performs a specfied task (or sequence of tasks as defined in the listOfSubTasks) multiple times (where the exact number is specified through a Range
    construct as defined in range), while allowing specific quantities in the model or models to be altered at each iteration (as defined in the listOfChanges).
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_repeatedTask (:obj:`dict`): The dictionary format: {'id':'repeatedTask1','type':libsedml.SEDML_TASK_REPEATEDTASK,'resetModel':False,'range':'range1','concatenate':bool,
                   'listOfChanges':[dict_setValue],'listOfRanges':[dict_uniformRange,dict_vectorRange,dict_dataRange], 'listOfSubTasks':[dict_subTask]}
                    resetModel: specifies whether the model or models should be reset to the initial state before processing an iteration of the defined subTasks.
                    range: specifies which range defined in the listOfRanges this repeated task iterates over.
                    concatenate: optional but strongly suggest to be defined,specifies whether the output of the subtasks should be appended to the results of the previous outputs (\true"), 
                                 or whether it should be added in parallel, as a new dimension of the output (\false").
    Returns:
        :obj:`bool` or `SedRepeatedTask`: If the repeatedTask is created successfully, return the instance of :obj:`SedRepeatedTask`; otherwise, return False
    """
    repeatedTask=doc.createRepeatedTask()
    if not operation_flag_check(repeatedTask.setId(dict_repeatedTask['id']), 'Set the id attribute of a repeated task'):
        return False
    if not operation_flag_check(repeatedTask.setResetModel(dict_repeatedTask['resetModel']), 'Set the resetModel attribute of a repeated task'):
        return False
    if not operation_flag_check(repeatedTask.setRangeId(dict_repeatedTask['range']), 'Set the range attribute of a repeated task'):
        return False
    if not operation_flag_check(repeatedTask.setConcatenate(dict_repeatedTask['concatenate']), 'Set the concatenate attribute of a repeated task'):
        return False
    if 'listOfChanges' in dict_repeatedTask:
        for dict_setValue in dict_repeatedTask['listOfChanges']:
            if not _modifyModel4Task(repeatedTask,dict_setValue):
                return False
    for dict_range in dict_repeatedTask['listOfRanges']:
        if not _setRange(repeatedTask,dict_range):
            return False
    if 'listOfSubTasks' in dict_repeatedTask:
        for dict_subTask in dict_repeatedTask['listOfSubTasks']:
            subTask = repeatedTask.createSubTask()
            if not _setSubTask(subTask,dict_subTask):
                return False
    return repeatedTask       

def get_dict_repeatedTask(repeatedTask):
    """
    Get the information of a repeated task
    Args:
        repeatedTask (:obj:`SedRepeatedTask`): an instance of :obj:`SedRepeatedTask`
    Returns:
        :obj:`dict`: The dictionary format: {'id':'repeatedTask1','type':libsedml.SEDML_TASK_REPEATEDTASK,'resetModel':False,'range':'range1','concatenate':bool,
                   'listOfChanges':[dict_setValue],'listOfRanges':[dict_uniformRange,dict_vectorRange,dict_dataRange], 'listOfSubTasks':[dict_subTask]}
    """
    dict_repeatedTask = {}
    dict_repeatedTask['id'] = repeatedTask.getId()
    dict_repeatedTask['type'] = libsedml.SedTypeCode_toString(repeatedTask.getTypeCode())
    dict_repeatedTask['resetModel'] = repeatedTask.getResetModel()
    dict_repeatedTask['range'] = repeatedTask.getRangeId()
    if repeatedTask.isSetConcatenate():
        dict_repeatedTask['concatenate'] = repeatedTask.getConcatenate()
    if repeatedTask.getNumTaskChanges()>0:
        dict_repeatedTask['listOfChanges'] = []
    for taskChange in repeatedTask.getListOfTaskChanges():
        dict_repeatedTask['listOfChanges'].append(_get_dict_setValue(taskChange))
    dict_repeatedTask['listOfRanges'] = []
    for sedRange in repeatedTask.getListOfRanges():
        dict_repeatedTask['listOfRanges'].append(_get_dict_range(sedRange))
    if repeatedTask.getNumSubTasks()>0:
        dict_repeatedTask['listOfSubTasks'] = []
    for subTask in repeatedTask.getListOfSubTasks():
        dict_repeatedTask['listOfSubTasks'].append(_get_dict_subTask(subTask))
    return dict_repeatedTask

def _setAdjustableParameter(task_pe,dict_adjustableParameter):
    """
    Set the adjustable parameter for a parameter estimation task
    Args:
        task_pe (:obj:`SedParameterEstimationTask`): an instance of :obj:`SedParameterEstimationTask`
        dict_adjustableParameter (:obj:`dict`): The dictionary format: 
                                                {'id':'parameter1','modelReference':'model1','target':target_component_variable,
                                                 'initialValue':None,'bounds':dict_bounds,'listOfExperimentReferences':[dict_experimentReference]}
                                                 dict_bounds format: {'lowerBound':'0.0','upperBound':'10.0','scale':'linear or log or log10''}
                                                 The target must point to an adjustable element of the Model referenced by the parent ParameterEstimationTask. 
                                                 This element is one of the elements whose value can be changed by the task in order to optimize the fit experiments.
                                                 Note: If an AdjustableParameter has no ExperimentReference children, it is adjusted for every FitExperiment.
    Returns:
        :obj:`bool`: whether the adjustable parameter is set successfully
    """
    p=task_pe.createAdjustableParameter()
    if not operation_flag_check(p.setId(dict_adjustableParameter['id']), 'Set the id attribute of an adjustable parameter'):
        return False
    if not operation_flag_check(p.setModelReference(dict_adjustableParameter['modelReference']), 'Set the modelReference attribute of an adjustable parameter'):
        return False
    if not operation_flag_check(p.setTarget(dict_adjustableParameter['target']), 'Set the target attribute of an adjustable parameter'):
        return False
    if 'initialValue' in dict_adjustableParameter:
        if not operation_flag_check(p.setInitialValue(dict_adjustableParameter['initialValue']), 'Set the initialValue attribute of an adjustable parameter'):
            return False
    bounds=p.createBounds()
    if not operation_flag_check(bounds.setLowerBound(dict_adjustableParameter['bounds']['lowerBound']), 'Set the lowerBound attribute of an adjustable parameter'):
        return False
    if not operation_flag_check(bounds.setUpperBound(dict_adjustableParameter['bounds']['upperBound']), 'Set the upperBound attribute of an adjustable parameter'):
        return False
    if not operation_flag_check(bounds.setScale(dict_adjustableParameter['bounds']['scale']), 'Set the scale attribute of an adjustable parameter'):
        return False
    if 'listOfExperimentReferences' in dict_adjustableParameter:
        for dict_experimentReference in dict_adjustableParameter['listOfExperimentReferences']:
            if not operation_flag_check(p.createExperimentReference().setExperimentId(dict_experimentReference['experiment']), 'Set the experimentReference attribute of an adjustable parameter'):
                return False
    return True

def _get_dict_adjustableParameter(p):
    """
    Get the information of an adjustable parameter
    Args:
        p (:obj:`SedAdjustableParameter`): an instance of :obj:`SedAdjustableParameter`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'parameter1','modelReference':'model1','target':target_component_variable,
                       'initialValue':None,'bounds':dict_bounds,'listOfExperimentReferences':[dict_experimentReference]}
                       dict_bounds format: {'lowerBound':'0.0','upperBound':'10.0','scale':'linear or log or log10''}
    """
    dict_adjustableParameter = {}
    dict_adjustableParameter['id'] = p.getId()
    dict_adjustableParameter['modelReference'] = p.getModelReference()
    dict_adjustableParameter['target'] = p.getTarget()
    if p.isSetInitialValue():
        dict_adjustableParameter['initialValue'] = p.getInitialValue()
    dict_adjustableParameter['bounds'] = {}
    bounds = p.getBounds()
    dict_adjustableParameter['bounds']['lowerBound'] = bounds.getLowerBound()
    dict_adjustableParameter['bounds']['upperBound'] = bounds.getUpperBound()
    dict_adjustableParameter['bounds']['scale'] = bounds.getScale()
    if p.getNumExperimentReferences()>0:
        dict_adjustableParameter['listOfExperimentReferences'] = []
    for experimentReference in p.getListOfExperimentReferences():
        dict_adjustableParameter['listOfExperimentReferences'].append(experimentReference.getExperimentId())
    return dict_adjustableParameter

def _setFitExperiment(task_pe,dict_fitExperiment):
    """
    Set the fitExperiment describing an experiment for which there are known experimental conditions, and expected experimental output. 
    The differences between the expected experimental output and the simulated output is used by the Objective to determine the optimal values to use for the AdjustableParameters.
    Args:
        task_pe (:obj:`SedParameterEstimationTask`): an instance of :obj:`SedParameterEstimationTask`
        dict_fitExperiment (:obj:`dict`): The dictionary format: 
                                          {'id':'fitExperimen1','type':'timeCourse or steadyState or invalid ExperimentType value','algorithm':dict_algorithm,'listOfFitMappings':[dict_fitMapping]}
                                          fitMapping is used to correlate elements of a model simulation with data for that simulation, whether time, inputs (experimental conditions) or outputs (observables).
                                          dict_fitMapping format: 
                                          {'type':'time or observable or experimentalCondition','dataSource':'data_source_1','target':'is an SIdRef to a DataGenerator','weight':None,'pointWeight':None}                                   
                                              time: Used only in time course simulations, maps the time points of the observables to the time points of the simulated output;
                                                    declare what time points must be output by the simulation.
                                              experimentalCondition: maps a single value to a model element. The model element must be set to the value as part of the model's initial condition.
                                              observable: maps the output of the simulation to a set of data.
                                              dataSource is a pointer to the expected values;
                                              target is a pointer to the simulated values;
                                              The weight or pointWeight attributes are used for observable only.
    Returns: 
        :obj:`bool`: whether the fit experiment is set successfully
    """
    fe=task_pe.createFitExperiment()
    if not operation_flag_check(fe.setId(dict_fitExperiment['id']), 'Set the id attribute of a fit experiment'):
        return False
    if not operation_flag_check(fe.setType(dict_fitExperiment['type']), 'Set the type attribute of a fit experiment'):
        return False
    alg=fe.createAlgorithm()
    if not _setAlgorithm(alg, dict_fitExperiment['algorithm']):
        return False
    for dict_fitMapping in dict_fitExperiment['listOfFitMappings']:
        fitMapping=fe.createFitMapping()
        if not operation_flag_check(fitMapping.setType(dict_fitMapping['type']), 'Set the type attribute of a fit mapping'):
            return False
        if not operation_flag_check(fitMapping.setDataSource(dict_fitMapping['dataSource']), 'Set the dataSource attribute of a fit mapping'):
            return False
        if not operation_flag_check(fitMapping.setTarget(dict_fitMapping['target']), 'Set the target attribute of a fit mapping'):
            return False
        if dict_fitMapping['type']=='observable':
            if 'weight' in dict_fitMapping:
                if dict_fitMapping['weight'] is not None:
                    if not operation_flag_check(fitMapping.setWeight(dict_fitMapping['weight']), 'Set the weight attribute of a fit mapping'):
                        return False
            elif 'pointWeight' in dict_fitMapping:
                if dict_fitMapping['pointWeight'] is not None:
                    if not operation_flag_check(fitMapping.setPointWeight(dict_fitMapping['pointWeight']), 'Set the pointWeight attribute of a fit mapping'):
                        return False
    return True

def _get_dict_fitExperiment(fe):
    """
    Get the information of a fit experiment
    Args:
        fe (:obj:`SedFitExperiment`): an instance of :obj:`SedFitExperiment`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'fitExperimen1','type':'TimeCourse or SteadyState or invalid ExperimentType value','algorithm':dict_algorithm,'listOfFitMappings':[dict_fitMapping]}
                      dict_fitMapping format: 
                      {'type':'time or observable or experimentalCondition or invalid MappingType value','dataSource':'data_source_1','target':'is an SIdRef to a DataGenerator','weight':None,'pointWeight':None}                                   
    """
    dict_fitExperiment = {}
    dict_fitExperiment['id'] = fe.getId()
    dict_fitExperiment['type'] = fe.getTypeAsString()
    sed_algorithm = fe.getAlgorithm()
    dict_fitExperiment['algorithm'] = get_dict_algorithm(sed_algorithm)    
    dict_fitExperiment['listOfFitMappings'] = []
    for fitMapping in fe.getListOfFitMappings():
        dict_fitMapping = {}
        dict_fitMapping['type'] = fitMapping.getTypeAsString()
        dict_fitMapping['dataSource'] = fitMapping.getDataSource()
        dict_fitMapping['target'] = fitMapping.getTarget()
        if fitMapping.getTypeAsString()== 'observable':
            if fitMapping.isSetWeight():
                dict_fitMapping['weight'] = fitMapping.getWeight()
            elif fitMapping.isSetPointWeight():
                dict_fitMapping['pointWeight'] = fitMapping.getPointWeight()
        dict_fitExperiment['listOfFitMappings'].append(dict_fitMapping)
    return dict_fitExperiment

def create_parameterEstimationTask(doc,dict_parameterEstimationTask):
    """
    Create a parameter estimation task that defines a parameter estimation problem to be solved.
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_parameterEstimationTask (:obj:`dict`): The dictionary format: 
                                                    {'id':'parameterEstimationTask1','type':libsedml.SEDML_TASK_PARAMETER_ESTIMATION,'algorithm':dict_algorithm,'objective':{'type':'leastSquare'},
                                                     'listOfAdjustableParameters':[dict_adjustableParameter],'listOfFitExperiments':[dict_fitExperiment]}
    Returns:
        :obj:`bool` or `SedParameterEstimationTask`: If the parameter estimation task is created successfully, return the instance of :obj:`SedParameterEstimationTask`; otherwise, return False
    """
    task_pe = doc.createParameterEstimationTask()
    if not operation_flag_check(task_pe.setId(dict_parameterEstimationTask['id']), 'Set the id attribute of a parameter estimation task'):
        return False
    #if not operation_flag_check(task_pe.setModelReference(dict_parameterEstimationTask['modelReference']), 'Set the modelReference attribute of a parameter estimation task'):
        #return False
    alg = task_pe.createAlgorithm()
    if not _setAlgorithm(alg, dict_parameterEstimationTask['algorithm']):
        return False
    if dict_parameterEstimationTask['objective']['type'] == 'leastSquare':
        task_pe.createLeastSquareObjectiveFunction()
    else:
        print('In Level 1 Version 4, there is only a single Objective option: theLeastSquareObjectiveFunction (called \leastSquareObjectiveFunction" instead of \objective")')
        return None
    for dict_adjustableParameter in dict_parameterEstimationTask['listOfAdjustableParameters']:
        if not _setAdjustableParameter(task_pe,dict_adjustableParameter):
            return False
    for dict_fitExperiment in dict_parameterEstimationTask['listOfFitExperiments']:
        if not _setFitExperiment(task_pe,dict_fitExperiment):
            return False
    return task_pe

def get_dict_parameterEstimationTask(task_pe):
    """
    Get the information of a parameter estimation task
    Args:
        task_pe (:obj:`SedParameterEstimationTask`): an instance of :obj:`SedParameterEstimationTask`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'parameterEstimationTask1','type':libsedml.SEDML_TASK_PARAMETER_ESTIMATION,'algorithm':dict_algorithm,'objective':'leastSquare',
                       'listOfAdjustableParameters':[dict_adjustableParameter],'listOfFitExperiments':[dict_fitExperiment]}
    """
    dict_parameterEstimationTask = {}
    dict_parameterEstimationTask['id'] = task_pe.getId()
    dict_parameterEstimationTask['type']=libsedml.SedTypeCode_toString(task_pe.getTypeCode())
    # dict_parameterEstimationTask['modelReference'] = task_pe.getModelReference()
    opt_algorithm = task_pe.getAlgorithm()
    dict_parameterEstimationTask['algorithm'] = get_dict_algorithm(opt_algorithm)
    dict_parameterEstimationTask['objective'] = 'leastSquare' 
    dict_parameterEstimationTask['listOfAdjustableParameters'] = []
    for adjustableParameter in task_pe.getListOfAdjustableParameters():
        dict_parameterEstimationTask['listOfAdjustableParameters'].append(_get_dict_adjustableParameter(adjustableParameter))
    dict_parameterEstimationTask['listOfFitExperiments'] = []
    for fitExperiment in task_pe.getListOfFitExperiments():
        dict_parameterEstimationTask['listOfFitExperiments'].append(_get_dict_fitExperiment(fitExperiment))
    return dict_parameterEstimationTask

def create_abstractTask(doc,dict_Task):
    if dict_Task['type'] == 'RepeatedTask':
        return create_repeatedTask(doc,dict_Task)
    elif dict_Task['type'] == 'Task':
        return create_task(doc,dict_Task)
    elif dict_Task['type'] == 'ParameterEstimationTask'	:
        return create_parameterEstimationTask(doc,dict_Task)
    else:
        print('The typeCode is not defined.')
        return False

def get_dict_abstractTask(task):
    if task.isSedRepeatedTask():
        return get_dict_repeatedTask(task)
    elif task.isSedTask():
        return get_dict_task(task)
    elif task.isSedParameterEstimationTask():
        return get_dict_parameterEstimationTask(task)
    else:
        print('The typeCode is not defined.')
        return False

def _setVariable(sedVariable,dict_variable):
    """
    Set the attributes of a variable
    Args:
        sedVariable (:obj:`SedVariable`): an instance of :obj:`SedVariable`
        dict_variable (:obj:`dict`): The dictionary format: 
                                     {'id':'variable1','name':None,'target':None,'symbol':None,'target2':None,'symbol2':None,
                                      'term':None,'modelReference':None,'taskReference':None,
                                      'dimensionTerm':None,'listOfAppliedDimensions':[dict_appliedDimension],'metaid':None
                                      }
                                      target could be XPath expressions to an explicit element of a model (e.g.,an SBML Species or a CellML Variable), 
                                      the id of a DataGenerator or DataSource (e.g., \#dataSource1") in the same document.
                                      symbol is a kisaoID, to refer either to a predefined, implicit variable or to a predefined implicit function to be performed on the target.
                                      target2 or symbol2 refers to a second mathematical element, and is always used in conjunction with a term
                                      term is a kisaoID, referring to a function or an analysis dependent on the model.
                                      A dimensionTerm attribute has exactly the same constraints as the term attribute, but must refer to a KiSAO term that reduces the dimensionality of multidimensional data.
                                      Currently, all such KiSAO terms inherit from \KISAO:0000824" (`aggregation function') and includes functions such as mean (\KISAO:0000825"), standard deviation (\KISAO:0000826"), and maximum (\KISAO:0000828").
                                      dict_appliedDimension format: {'target':None,'dimensionTarget':None}
                                         appliedDimension is used only when dimensionTerm of the Variable is defined
                                         target is used when the applied dimension is a Task or RepeatedTask, possible values are: the id of a repeatedTask, the id of a task referenced by a repeatedTask, or the id of a subtask child of a repeatedTask
                                         dimensionTarget is used when the Variable references an external data source. The NuMLIdRef must reference a dimension of the referenced data.
    Returns:
        :obj:`bool`: whether the variable is set successfully
    """
    if not operation_flag_check(sedVariable.setId(dict_variable['id']), 'Set the id attribute of a variable'):
        return False
    if 'name' in dict_variable:
        if not operation_flag_check(sedVariable.setName(dict_variable['name']), 'Set the name attribute of a variable'):
            return False
    if 'target' in dict_variable:
        if not operation_flag_check(sedVariable.setTarget(dict_variable['target']), 'Set the target attribute of a variable'):
            return False
    if 'symbol' in dict_variable:
        if not operation_flag_check(sedVariable.setSymbol(dict_variable['symbol']), 'Set the symbol attribute of a variable'):
            return False
    if 'target2' in dict_variable:
        if not operation_flag_check(sedVariable.setTarget2(dict_variable['target2']), 'Set the target2 attribute of a variable'):
            return False
    if 'symbol2' in dict_variable:
        if not operation_flag_check(sedVariable.setSymbol2(dict_variable['symbol2']), 'Set the symbol2 attribute of a variable'):
            return False
    if 'term' in dict_variable:
        if not operation_flag_check(sedVariable.setTerm(dict_variable['term']), 'Set the term attribute of a variable'):
            return False
    if 'modelReference' in dict_variable:
        if not operation_flag_check(sedVariable.setModelReference(dict_variable['modelReference']), 'Set the modelReference attribute of a variable'):
            return False
    if 'taskReference' in dict_variable:
        if not operation_flag_check(sedVariable.setTaskReference(dict_variable['taskReference']), 'Set the taskReference attribute of a variable'):
            return False
    if 'dimensionTerm' in dict_variable:
        if not operation_flag_check(sedVariable.setDimensionTerm(dict_variable['dimensionTerm']), 'Set the dimensionTerm attribute of a variable'):
            return False
        elif 'listOfAppliedDimensions' in dict_variable and dict_variable['listOfAppliedDimensions']:
            for dict_appliedDimension in dict_variable['listOfAppliedDimensions']:
                appliedDimension=sedVariable.createAppliedDimension()
                if 'target' in dict_appliedDimension:
                    if not operation_flag_check(appliedDimension.setTarget(dict_appliedDimension['target']), 'Set the target attribute of an applied dimension'):
                        return False
                elif 'dimensionTarget' in dict_appliedDimension:
                    if not operation_flag_check(appliedDimension.setDimensionTarget(dict_appliedDimension['dimensionTarget']), 'Set the dimensionTarget attribute of an applied dimension'):
                        return False
                else:
                    print('The dimensionTerm attribute is defined but the listOfAppliedDimensions attribute of a variable is empty.')
                    return False
        else:
            print('The dimensionTerm attribute is defined but the listOfAppliedDimensions attribute of a variable is empty.')
            return False  
    if 'metaid' in dict_variable:
        if not operation_flag_check(sedVariable.setMetaId(dict_variable['metaid']), 'Set the metaid attribute of a variable'):
            return False       
    return True

def _get_dict_variable(sedVariable):
    """
    Get the information of a variable
    Args:
        sedVariable (:obj:`SedVariable`): an instance of :obj:`SedVariable`
    Returns:
        :obj:`dict`: The dictionary format: 
                      {'id':'variable1','name':None,'target':None,'symbol':None,'target2':None,'symbol2':None,
                       'term':None,'modelReference':None,'taskReference':None,
                       'dimensionTerm':None,'listOfAppliedDimensions':[dict_appliedDimension],'metaid':None
                       }
                       dict_appliedDimension format: {'target':None,'dimensionTarget':None}                       
    """
    dict_variable = {}
    dict_variable['id'] = sedVariable.getId()
    if sedVariable.isSetName():
        dict_variable['name'] = sedVariable.getName()
    if sedVariable.isSetTarget():
        dict_variable['target'] = sedVariable.getTarget()
    if sedVariable.isSetSymbol():
        dict_variable['symbol'] = sedVariable.getSymbol()
    if sedVariable.isSetTarget2():
        dict_variable['target2'] = sedVariable.getTarget2()
    if sedVariable.isSetSymbol2():
        dict_variable['symbol2'] = sedVariable.getSymbol2()
    if sedVariable.isSetTerm():
        dict_variable['term'] = sedVariable.getTerm()
    if sedVariable.isSetModelReference():
        dict_variable['modelReference'] = sedVariable.getModelReference()
    if sedVariable.isSetTaskReference():
        dict_variable['taskReference'] = sedVariable.getTaskReference()
    if sedVariable.isSetDimensionTerm():
        dict_variable['dimensionTerm'] = sedVariable.getDimensionTerm()
        dict_variable['listOfAppliedDimensions'] = []
        for appliedDimension in sedVariable.getListOfAppliedDimensions():
            dict_appliedDimension = {}
            if appliedDimension.isSetTarget():
                dict_appliedDimension['target'] = appliedDimension.getTarget()
            if appliedDimension.isSetDimensionTarget():
                dict_appliedDimension['dimensionTarget'] = appliedDimension.getDimensionTarget()
            dict_variable['listOfAppliedDimensions'].append(dict_appliedDimension)
    if sedVariable.isSetMetaId():
        dict_variable['metaid'] = sedVariable.getMetaId()
    return dict_variable

def create_dataGenerator(doc,dict_dataGenerator):
    """
    Set the attributes of a data generator to prepare the raw simulation results for later output
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_dataGenerator (:obj:`dict`): The dictionary format:
                                            {'id':'dataGenerator1','name':'dataGenerator1','math':'varId or complex math infix ','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
                                            dict_parameter format: {'id':'param1','name':None,'value':float,'metaid':None}                                            
    Returns:
        :obj:`bool`: whether the data generator is set successfully  
    """
    dataGenerator=doc.createDataGenerator()
    if not operation_flag_check(dataGenerator.setId(dict_dataGenerator['id']), 'Set the id attribute of a data generator'):
        return False
    if 'name' in dict_dataGenerator:
        if not operation_flag_check(dataGenerator.setName(dict_dataGenerator['name']), 'Set the name attribute of a data generator'):
            return False
    if 'math' in dict_dataGenerator:
        if not operation_flag_check(dataGenerator.setMath(libsedml.parseFormula(dict_dataGenerator['math'])), 'Set the math attribute of a data generator'):
            return False
    if 'listOfVariables' in dict_dataGenerator:
        for dict_variable in dict_dataGenerator['listOfVariables']:
            sedVariable=dataGenerator.createVariable()
            if not _setVariable(sedVariable,dict_variable):
                return False
    if 'listOfParameters' in dict_dataGenerator:
        for dict_parameter in dict_dataGenerator['listOfParameters']:
            sedParameter=dataGenerator.createParameter()
            if not operation_flag_check(sedParameter.setId(dict_parameter['id']), 'Set the id attribute of a parameter'):
                return False
            if 'name' in dict_parameter:
                if not operation_flag_check(sedParameter.setName(dict_parameter['name']), 'Set the name attribute of a parameter'):
                    return False
            if not operation_flag_check(sedParameter.setValue(dict_parameter['value']), 'Set the value attribute of a parameter'):
                return False
            if 'metaid' in dict_parameter:
                if not operation_flag_check(sedParameter.setMetaId(dict_parameter['metaid']), 'Set the metaid attribute of a parameter'):
                    return False
    return True

def get_dict_dataGenerator(dataGenerator):
    """
    Get the information of a data generator
    Args:
        dataGenerator (:obj:`SedDataGenerator`): an instance of :obj:`SedDataGenerator`
    Returns:
        :obj:`dict`: The dictionary format:
                      {'id':'dataGenerator1','name':'dataGenerator1','math':'varId or complex math infix ','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
                      dict_parameter format: {'id':'param1','name':None,'value':float,'metaid':None} 
    """
    dict_dataGenerator = {}
    dict_dataGenerator['id'] = dataGenerator.getId()
    if dataGenerator.isSetName():
        dict_dataGenerator['name'] = dataGenerator.getName()
    if dataGenerator.isSetMath():
        dict_dataGenerator['math'] = libsedml.formulaToL3String(dataGenerator.getMath())
    if dataGenerator.getNumVariables()>0:
        dict_dataGenerator['listOfVariables'] = []
    for sedVariable in dataGenerator.getListOfVariables():
        dict_dataGenerator['listOfVariables'].append(_get_dict_variable(sedVariable))
    if dataGenerator.getNumParameters()>0:
        dict_dataGenerator['listOfParameters'] = []
    for sedParameter in dataGenerator.getListOfParameters():
        dict_parameter = {}
        dict_parameter['id'] = sedParameter.getId()
        if sedParameter.isSetName():
            dict_parameter['name'] = sedParameter.getName()
        dict_parameter['value'] = sedParameter.getValue()
        if sedParameter.isSetMetaId():
            dict_parameter['metaid'] = sedParameter.getMetaId()
        dict_dataGenerator['listOfParameters'].append(dict_parameter)
    return dict_dataGenerator

def setDataSet(dataSet,dict_dataSet):
    """
    The DataSet class holds definitions of data to be used in the Report class
    Args:
        dataSet (:obj:`SedDataSet`): an instance of :obj:`SedDataSet`
        dict_dataSet (:obj:`dict`): The dictionary format:
                                    {'id':'dataSet1','name':'optional,a human readable descriptor of a data set','label':'a unique label','dataReference':'must be the ID of a DataGenerator element'}
    Returns:
        :obj:`bool`: whether the data set is set successfully  
    """
    if not operation_flag_check(dataSet.setId(dict_dataSet['id']), 'Set the id attribute of a data set'):
        return False
    if 'name' in dict_dataSet:
        if not operation_flag_check(dataSet.setName(dict_dataSet['name']), 'Set the name attribute of a data set'):
            return False
    if not operation_flag_check(dataSet.setLabel(dict_dataSet['label']), 'Set the label attribute of a data set'):
        return False
    if not operation_flag_check(dataSet.setDataReference(dict_dataSet['dataReference']), 'Set the dataReference attribute of a data set'):
        return False
    return True

def _get_dict_dataSet(dataSet):
    """
    Get the information of a data set
    Args:
        dataSet (:obj:`SedDataSet`): an instance of :obj:`SedDataSet`
    Returns:
        :obj:`dict`: The dictionary format:
                      {'id':'dataSet1','name':'optional,a human readable descriptor of a data set','label':'a unique label','dataReference':'must be the ID of a DataGenerator element'}
    """
    dict_dataSet = {}
    dict_dataSet['id'] = dataSet.getId()
    if dataSet.isSetName():
        dict_dataSet['name'] = dataSet.getName()
    dict_dataSet['label'] = dataSet.getLabel()
    dict_dataSet['dataReference'] = dataSet.getDataReference()
    return dict_dataSet

def create_sedReport(doc,dict_report):
    """
    Create a report that how the results of a simulation are presented
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        dict_report (:obj:`dict`): The dictionary format:
                                    {'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
    Returns:
        :obj:`bool` or `SedReport`: If the report is created successfully, return the instance of :obj:`SedReport`; otherwise, return False
    """
    sedReport=doc.createReport()
    if not operation_flag_check(sedReport.setId(dict_report['id']), 'Set the id attribute of a report'):
        return False
    if 'name' in dict_report:
        if not operation_flag_check(sedReport.setName(dict_report['name']), 'Set the name attribute of a report'):
            return False
    for dict_dataSet in dict_report['listOfDataSets']:
        dataSet=sedReport.createDataSet()
        if not setDataSet(dataSet,dict_dataSet):
            return False
    return sedReport

def get_dict_report(sedReport):
    """
    Get the information of a report
    Args:
        sedReport (:obj:`SedReport`): an instance of :obj:`SedReport`
    Returns:
        :obj:`dict`: The dictionary format:
                      {'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
    """
    dict_report = {}
    dict_report['id'] = sedReport.getId()
    if sedReport.isSetName():
        dict_report['name'] = sedReport.getName()
    dict_report['listOfDataSets'] = []
    for dataSet in sedReport.getListOfDataSets():
        dict_report['listOfDataSets'].append(_get_dict_dataSet(dataSet))
    return dict_report

def create_sedDocment(dict_sedDocument):
    """
    Create a SED-ML document
    Args:
        dict_sedDocument (:obj:`dict`): The dictionary format:
                                        {'listOfDataDescriptions':[dict_dataDescription],'listOfModels':[dict_model],'listOfSimulations':[dict_simulation],
                                         'listOfTasks':[dict_task],'listOfDataGenerators':[dict_dataGenerator],'listOfReports':[dict_report]}
    Returns:
        :obj:`SedDocument`: the instance of :obj:`SedDocument`
    """
    doc = libsedml.SedDocument(1,4)
    if 'listOfDataDescriptions' in dict_sedDocument:
        for dict_dataDescription in dict_sedDocument['listOfDataDescriptions']:
            if not create_dataDescription(doc,dict_dataDescription):
                return False
    if 'listOfModels' in dict_sedDocument:
        for dict_model in dict_sedDocument['listOfModels']:
            if not create_sedModel(doc,dict_model):
                return False
    if 'listOfSimulations' in dict_sedDocument:
        for dict_simulation in dict_sedDocument['listOfSimulations']:
            if not create_simulation(doc,dict_simulation):
                return False
    if 'listOfTasks' in dict_sedDocument:
        for dict_task in dict_sedDocument['listOfTasks']:
            if not create_abstractTask(doc,dict_task):
                return False
    if 'listOfDataGenerators' in dict_sedDocument:
        for dict_dataGenerator in dict_sedDocument['listOfDataGenerators']:
            if not create_dataGenerator(doc,dict_dataGenerator):
                return False
    if 'listOfReports' in dict_sedDocument:
        for dict_report in dict_sedDocument['listOfReports']:
            if not create_sedReport(doc,dict_report):
                return False
    return doc

def get_dict_sedDocument(doc):
    """
    Get the information of a SED-ML document
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
    Returns:
        :obj:`dict`: The dictionary format:
                      {'listOfDataDescriptions':[dict_dataDescription],'listOfModels':[dict_model],'listOfSimulations':[dict_simulation],
                       'listOfTasks':[dict_task],'listOfDataGenerators':[dict_dataGenerator],'listOfReports':[dict_report]}
    """
    dict_sedDocument = {}
    if doc.getNumDataDescriptions()>0:
        dict_sedDocument['listOfDataDescriptions'] = []
        for dataDescription in doc.getListOfDataDescriptions():
            dict_sedDocument['listOfDataDescriptions'].append(get_dict_dataDescription(dataDescription))
    if doc.getNumModels()>0:
        dict_sedDocument['listOfModels'] = []
        for sedModel in doc.getListOfModels():
            dict_sedDocument['listOfModels'].append(get_dict_model(sedModel))
    if doc.getNumSimulations()>0:
        dict_sedDocument['listOfSimulations'] = []
        for sedSimulation in doc.getListOfSimulations():
            dict_sedDocument['listOfSimulations'].append(get_dict_simulation(sedSimulation))
    if doc.getNumTasks()>0:
        dict_sedDocument['listOfTasks'] = []
        for task in doc.getListOfTasks():
            dict_sedDocument['listOfTasks'].append(get_dict_abstractTask(task))
    if doc.getNumDataGenerators()>0:
        dict_sedDocument['listOfDataGenerators'] = []
        for dataGenerator in doc.getListOfDataGenerators():
            dict_sedDocument['listOfDataGenerators'].append(get_dict_dataGenerator(dataGenerator))
    if doc.getNumOutputs()>0:
        dict_sedDocument['listOfReports'] = []
        for output in doc.getListOfOutputs():
            if output.isSedReport():
                dict_sedDocument['listOfReports'].append(get_dict_report(output))
    return dict_sedDocument

def write_sedml(doc,file_name):
    """
    Write the SED-ML document to a file
    Args:
        doc (:obj:`SedDocument`): an instance of :obj:`SedDocument`
        file_name (:obj:`str`): the file name
    """
    libsedml.writeSedMLToFile(doc,file_name)

def read_sedml(file_name):
    """
    Read the SED-ML document from a file
    Args:
        file_name (:obj:`str`): the file name
    Returns:
        :obj:`SedDocument`: the instance of :obj:`SedDocument`
    """
    doc = libsedml.readSedMLFromFile(file_name)
    return doc

def validate_sedml(file_name):
    doc = libsedml.readSedMLFromFile(file_name)
    num_errors = doc.getNumErrors(libsedml.LIBSEDML_SEV_ERROR)
    num_warnings = doc.getNumErrors(libsedml.LIBSEDML_SEV_WARNING)

    print ('file: {0} has {1} warning(s) and {2} error(s)'
        .format(file_name, num_warnings, num_errors))

    log = doc.getErrorLog()
    for i in range(log.getNumErrors()):
        err = log.getError(i)
        print('{0} L{1} C{2}: {3}'.format(err.getSeverityAsString(), err.getLine(), err.getColumn(), err.getMessage()))

    return num_errors


# Test
if __name__ == '__main__':
    
    print(SEDML_TYPE_CODES_TABLE)
    dict_sedDocument={}

    dict_model={'id':'model1','source':'../tests/csv/test_model_noExt.cellml','language':'urn:sedml:language:cellml','listOfChanges':[]}
    dict_sedDocument['listOfModels']=[dict_model]

    dict_algorithmParameter={'kisaoID':'KISAO:0000483','name':'step size','value':'0.001'}
    dict_algorithm={'kisaoID':'KISAO:0000030','name':'Euler forward method', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
    dict_simulation={'id':'timeCourse1', 'type':'UniformTimeCourse', 'algorithm':dict_algorithm, 
                     'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
    dict_sedDocument['listOfSimulations']= [dict_simulation]

    dict_task={'id':'task1','type':'Task', 'modelReference':'model1','simulationReference':'timeCourse1'}
    dict_sedDocument['listOfTasks']= [dict_task]

    dict_variable={'id':'v','target':target_component_variable('SLC_template3_ss', 'v'),'modelReference':'model1','taskReference':'task1'}
    dict_parameter={'id':'scale','value':10.0}
    dict_dataGenerator={'id':'output','name':'dataGenerator1','math':'v*scale','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
    dict_sedDocument['listOfDataGenerators']= [dict_dataGenerator]

    dict_dataSet={'id':'dataSet1','label':'output','dataReference':'output'}
    dict_report={'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
    dict_sedDocument['listOfReports']= [dict_report]

    doc=create_sedDocment(dict_sedDocument)
    filename='../tests/csv/test.sedml'
    write_sedml(doc,filename)
    print(validate_sedml(filename))
    print(get_dict_sedDocument(doc))
    
    