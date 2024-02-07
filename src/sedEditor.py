import libsedml
from libsedml import SedOperationReturnValue_toString
import json

"""
====================
SED-ML Editor
====================

This module provides functions to create and get the information of SED-ML elements.
The SED-ML elements are defined in the libSEDML library.

The validation could be overlapped with the libSEDML library.

"""

# Create a lookup table for the SED-ML type codes
SEDML_TYPE_CODES = [libsedml.SEDML_SIMULATION_UNIFORMTIMECOURSE,
                    libsedml.SEDML_SIMULATION_ONESTEP,
                    libsedml.SEDML_SIMULATION_STEADYSTATE,
                    libsedml.SEDML_RANGE_UNIFORMRANGE,
                    libsedml.SEDML_RANGE_VECTORRANGE,
                    libsedml.SEDML_RANGE_FUNCTIONALRANGE,
                    libsedml.SEDML_DATA_RANGE,
                    libsedml.SEDML_TASK,
                    libsedml.SEDML_TASK_REPEATEDTASK,
                    libsedml.SEDML_TASK_PARAMETER_ESTIMATION                                    
]

SEDML_TYPE_CODES_TABLE = dict(zip(SEDML_TYPE_CODES, [libsedml.SedTypeCode_toString(i) for i in SEDML_TYPE_CODES]))

# save the SED-ML type codes to a json file
def save_sedml_type_codes():
    with open('sedml_type_codes.json', 'w') as outfile:
        json.dump(SEDML_TYPE_CODES_TABLE, outfile)

# Get the TypeCode from a string
def SEDML_TYPE_CODE_FROM_STR(type_str):
    for key, value in SEDML_TYPE_CODES_TABLE.items():
        if value == type_str:
            return key
    return None
    

def _operation_flag_check(operation_flag, operation_name):
    if operation_flag<0:
        raise ValueError('{operation_name} returned an error: {flag}'.format(operation_name=operation_name,flag=SedOperationReturnValue_toString(operation_flag)))
    else:
        return

def _setDimensionDescription(sed_dimDescription, dimDict):
    """Set the dimensions and data types of the external data.

    Parameters
    ----------
    sed_dimDescription: SedDimensionDescription
        An instance of SedDimensionDescription.
    dimDict: dict
        The dictionary format: 
        {'id':'Index','name':'Index','indexType':'integer',
         'dim2':{'id':'ColumnIds','name':'ColumnIds','indexType':'string','valueType':'double'}
         }
        The required attributes are 'id','indexType'.
        If dim2 is defined, the required attributes are 'id','indexType','valueType'.        
        The valueType is the data type of the external data.
        The valueType is defined on the atomicDescription.
    
    Raises
    ------
    ValueError
        If the required attributes are not set.
        If the any operation returns an error.
        
    Side effects
    ------------
    sed_dimDescription: SedDimensionDescription
        The dimension description is set.

    Notes
    -----
    Only two dimensions are supported.

    Returns
    -------
    bool
        Whether the dimension description is set successfully.
    """

    dim1_Description=libsedml.CompositeDescription()
    if 'indexType' not in dimDict or 'id' not in dimDict:
        raise ValueError('The indexType and id attributes of a dimension 1 description are required.')
    try:
        _operation_flag_check(dim1_Description.setIndexType(dimDict['indexType']), 'Set the indexType attribute of a dimension description')
        _operation_flag_check(dim1_Description.setId(dimDict['id']), 'Set the id attribute of a dimension description')
        if 'name' in dimDict:
            _operation_flag_check(dim1_Description.setName(dimDict['name']), 'Set the name attribute of a dimension description')
        if 'dim2' in dimDict:
            dim2_Description=dim1_Description.createCompositeDescription()
            if 'indexType' not in dimDict['dim2'] or 'id' not in dimDict['dim2'] or 'valueType' not in dimDict['dim2']:
                raise ValueError('The indexType, id and valueType attributes of a dimension 2 description are required')
            _operation_flag_check(dim2_Description.setIndexType(dimDict['dim2']['indexType']), 'Set the indexType attribute of a dimension description')
            _operation_flag_check(dim2_Description.setId(dimDict['dim2']['id']), 'Set the id attribute of a dimension description')
            atomic_Desc=dim2_Description.createAtomicDescription()
            _operation_flag_check(atomic_Desc.setValueType(dimDict['dim2']['valueType']), 'Set the valueType attribute of a dimension description')
            if 'name' in dimDict['dim2']:
                _operation_flag_check(dim2_Description.setName(dimDict['dim2']['name']), 'Set the name attribute of a dimension description')
    except ValueError as e:
        raise            
    sed_dimDescription.append(dim1_Description)
    return True 

def _get_dict_dimDescription(sed_dimDescription):
    """Get the information of a dimension description
    
    Parameters
    ----------
    sed_dimDescription: SedDimensionDescription
        An instance of SedDimensionDescription.

    Notes
    -----
    Only two dimensions are supported.
    
    Raises
    ------
    ValueError
        If the valueType attribute of a dimension 2 description is not set.

    Returns
    -------
    dict
        The dictionary format: 
        {'id':'Index','name':'Index','indexType':'integer',
         'dim2':{'id':'ColumnIds','name':'ColumnIds','indexType':'string','valueType':'double'}
         }
        Only the attributes that are set will be returned.
    """
    dict_dimDescription = {}
    dim1_Description = sed_dimDescription.get(0)
    dict_dimDescription['id'] = dim1_Description.getId()
    if dim1_Description.isSetName():
        dict_dimDescription['name'] = dim1_Description.getName()
    dict_dimDescription['indexType'] = dim1_Description.getIndexType()    
    if 'dim2' in dict_dimDescription:
        dict_dimDescription['dim2'] = {}
        dim2_Description = dim1_Description.getCompositeDescription(0)
        dict_dimDescription['dim2']['id'] = dim2_Description.getId()
        if dim2_Description.isSetName():
            dict_dimDescription['dim2']['name'] = dim2_Description.getName()
        dict_dimDescription['dim2']['indexType'] = dim2_Description.getIndexType()
        if dim2_Description.get(0).isSetValueType():
            dict_dimDescription['dim2']['valueType'] = dim2_Description.get(0).getValueType()
        else:
            raise ValueError('The valueType attribute of a dimension 2 description is required.')
    return dict_dimDescription

def _setSlice(sed_slice, reference,value=None,index=None,startIndex=None,endIndex=None):
    """Create a slice for a data source. Each slice removes one dimension from the data hypercube

    Parameters
    ----------
    sed_slice: SedSlice
        An instance of SedSlice.
    reference: str
        The reference attribute references one of the indices 
        described in the dimensionDescription of the data source.
    value: str, optional
        The value attribute takes the value of a specific index in the referenced set of indices.
    index: str, optional
        The index attribute is an SIdRef to a RepeatedTask. 
        This is for cases where the Slice refers to data generated by potentially-nested RepeatedTask elements. 
    startIndex: integer, optional
        The startIndex attribute is an integer that specifies the first index in the referenced set of indices to be used.
    endIndex: integer, optional
        The endIndex attribute is an integer that specifies the last index in the referenced set of indices to be used.   
    
    Raises
    ------
    ValueError
        If the any operation returns an error.

    Side effects
    ------------
    sed_slice: SedSlice
        The slice is set.

    Returns
    -------
    bool
        Whether the slice is set successfully.
    """
    try:
        _operation_flag_check(sed_slice.setReference(reference), 'Set the reference attribute of a slice')
        if value:
            _operation_flag_check(sed_slice.setValue(value), 'Set the value attribute of a slice')
        if index:
            _operation_flag_check(sed_slice.setIndex(index), 'Set the index attribute of a slice')
        if startIndex is not None:
            _operation_flag_check(sed_slice.setStartIndex(startIndex), 'Set the startIndex attribute of a slice')
        if endIndex is not None:
            _operation_flag_check(sed_slice.setEndIndex(endIndex), 'Set the endIndex attribute of a slice')
    except ValueError as e:
        raise
    return True

def _get_dict_slice(sed_slice):
    """Get the information of a slice
    
    Parameters
    ----------
    sed_slice: SedSlice
        An instance of SedSlice.
    
    Raises
    ------
    ValueError
        If the reference attribute of a slice is not set.

    Returns
    -------
    dict
        The dictionary format: {'reference':'ColumnIds','value':'csv_column_time','index':'str','startIndex':int,'endIndex':int}
        Only the attributes that are set will be returned.
        'reference' is the only required attribute.
    """
    dict_slice = {}
    if sed_slice.isSetReference():
        dict_slice['reference'] = sed_slice.getReference()
    else:
        raise ValueError('The reference attribute of a slice is required.')
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
    
    Parameters
    ----------
    sed_dataSource: SedDataSource
        An instance of SedDataSource.
    dict_dataSource: dict
        The dictionary format: {'id':'data_source_1','name':'data_source_1','indexSet':''str,'listOfSlices':[dict_slice]}
        id is a required attribute.
        The indexSet attribute references the id of index provided by NuML elements with indexType.
        When the data format is csv, the indexSet attribute is not defined.
        If a DataSource does not define the indexSet attribute, it must contain Slice elements.
        If neither the indexSet attribute nor the listOfSlices attribute is defined, return False.
    
    Raises
    ------
    ValueError
        If the id attribute of a data source is not set.
        If the indexSet attribute and the slice elements of a data source are defined at the same time.
        If neither the indexSet attribute nor the slice elements of a data source are defined.
        If any operation returns an error.

    Side effects
    ------------
    sed_dataSource: SedDataSource
        The data source is set.

    Returns
    -------
    bool
        Whether the data source is set successfully.
    """
    
    if 'id' not in dict_dataSource:
        raise ValueError('The id attribute of a data source is required.')
    if 'indexSet' in dict_dataSource and 'listOfSlices' in dict_dataSource:
        raise ValueError('The indexSet attribute and the slice elements of a data source cannot be defined at the same time.')
    if 'indexSet' not in dict_dataSource and 'listOfSlices' not in dict_dataSource:
        raise ValueError('The indexSet attribute or the slice elements of a data source is required.')
    try:
        _operation_flag_check(sed_dataSource.setId(dict_dataSource['id']), 'Set the id attribute of a data source')
        if 'name' in dict_dataSource:
            _operation_flag_check(sed_dataSource.setName(dict_dataSource['name']), 'Set the name attribute of a data source')
        if 'indexSet' in dict_dataSource: # when the data format is NuML
            _operation_flag_check(sed_dataSource.setIndexSet(dict_dataSource['indexSet']), 'Set the indexSet attribute of a data source')
        elif 'listOfSlices' in dict_dataSource:
            for dict_slice in dict_dataSource['listOfSlices']:
                sed_slice = sed_dataSource.createSlice()
                if 'value' not in dict_slice:
                    value=None
                else:
                    value=dict_slice['value']
                if 'index' not in dict_slice:
                    index=None
                else:
                    index=dict_slice['index']
                if 'startIndex' not in dict_slice:
                    startIndex=None
                else:
                    startIndex=dict_slice['startIndex']
                if 'endIndex' not in dict_slice:
                    endIndex=None
                else:
                    endIndex=dict_slice['endIndex']
                _setSlice(sed_slice, dict_slice['reference'],value,index,startIndex,endIndex)
    except ValueError as e:
        raise

    return True

def _get_dict_dataSource(sed_dataSource):
    """Get the information of a data source

    Parameters
    ----------
    sed_dataSource: SedDataSource
        An instance of SedDataSource.
    
    Raises
    ------
    ValueError
        If the id attribute of a data source is not set.
        If the indexSet attribute and the slice elements of a data source are defined at the same time.
        If neither the indexSet attribute nor the slice elements of a data source are defined.
        If _get_dict_slice(sed_slice) failed.

    Returns
    -------
    dict
        The dictionary format: {'id':'data_source_1','name':'data_source_1','indexSet':'str','listOfSlices':[dict_slice]}
        Only the attributes that are set will be returned.
        'id' is a required attribute.
    """

    dict_dataSource = {}
    if sed_dataSource.isSetId():
        dict_dataSource['id'] = sed_dataSource.getId()
    else:
        raise ValueError('The id attribute of a data source is required.')
    if sed_dataSource.isSetIndexSet() and sed_dataSource.getNumSlices()>0:
        raise ValueError('The indexSet attribute and the slice elements of a data source cannot be defined at the same time.')
    if sed_dataSource.isSetName():
        dict_dataSource['name'] = sed_dataSource.getName()
    if sed_dataSource.isSetIndexSet():
        dict_dataSource['indexSet'] = sed_dataSource.getIndexSet()
    elif sed_dataSource.getNumSlices()>0:
        dict_dataSource['listOfSlices'] = []
        for sed_slice in sed_dataSource.getListOfSlices():
            try:
                dict_slice = _get_dict_slice(sed_slice)
            except ValueError as e:
                raise
            dict_dataSource['listOfSlices'].append(dict_slice)
    else:
        raise ValueError('The indexSet attribute or the slice elements of a data source is required.')
    return dict_dataSource

def create_dataDescription(doc, dict_dataDescription):
    """
    Create a data description

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_dataDescription: dict
        The dictionary format: 
        {'id':'data_description_1','name':'data_description_1', 'source':'file.csv','format':URN string,
         'dimensionDescription':dict_dimDescription,'listOfDataSources':[dict_dataSource]
         }. 
        id and source are required attributes.
        The format attribute is optional. 
        The default is NuML.
        The dimensionDescription attribute is optional.
        The listOfDataSources attribute is optional.
    
    Raises
    ------
    ValueError
        If the id or source attributes of a data description are not set.
        If any operation returns an error.

    Returns
    -------
    SedDataDescription
        An instance of SedDataDescription.
       
    """
    
    sed_dataDescription = doc.createDataDescription()

    if 'id' not in dict_dataDescription or 'source' not in dict_dataDescription:
        raise ValueError('The id and source attributes of a data description are required.')

    try:
        _operation_flag_check(sed_dataDescription.setId(dict_dataDescription['id']), 'Set the id attribute of a data description')
        _operation_flag_check(sed_dataDescription.setSource(dict_dataDescription['source']), 'Set the source attribute of a data description')
        if 'format' in dict_dataDescription:
            _operation_flag_check(sed_dataDescription.setFormat(dict_dataDescription['format']), 'Set the format attribute of a data description')
        else: # the default is NuML
            _operation_flag_check(sed_dataDescription.setFormat('urn:sedml:format:numl)'), 'Set the format attribute of a data description')
        if 'name' in dict_dataDescription:
            _operation_flag_check(sed_dataDescription.setName(dict_dataDescription['name']), 'Set the name attribute of a data description')
        if 'dimensionDescription' in dict_dataDescription:
            sed_dimDescription = sed_dataDescription.createDimensionDescription()
            dict_dimDescription=dict_dataDescription['dimensionDescription']
            _setDimensionDescription(sed_dimDescription, dict_dimDescription)
        if 'listOfDataSources' in dict_dataDescription:
            for dict_dataSource in dict_dataDescription['listOfDataSources']:
                sed_dataSource = sed_dataDescription.createDataSource()
                _setDataSource(sed_dataSource, dict_dataSource)
    except ValueError as e:
        raise  

    return sed_dataDescription

def get_dict_dataDescription(sed_dataDescription):
    """
    Get the information of a data description
    
    Parameters
    ----------
    sed_dataDescription: SedDataDescription
        An instance of SedDataDescription.
    
    Raises
    ------
    ValueError
        If the id or source attributes of a data description are not set.
        If _get_dict_dimDescription(sed_dimDescription) failed.
        If _get_dict_dataSource(sed_dataSource) failed.

    Returns
    -------
    dict
        The dictionary format: 
        {'id':'data_description_1','name':'data_description_1', 'source':'file.csv','format':URN string,
         'dimensionDescription':dict_dimDescription,'listOfDataSources':[dict_dataSource]
         }. 
        Only the attributes that are set will be returned.
        'id' and 'source' are required attributes.
    """

    dict_dataDescription = {}
    if not sed_dataDescription.isSetId() or not sed_dataDescription.isSetSource():
        raise ValueError('The id and source attributes of a data description are required.')
  
    dict_dataDescription['id'] = sed_dataDescription.getId()
    dict_dataDescription['source'] = sed_dataDescription.getSource()

    if sed_dataDescription.isSetFormat():
        dict_dataDescription['format'] = sed_dataDescription.getFormat()
    if sed_dataDescription.isSetName():
        dict_dataDescription['name'] = sed_dataDescription.getName()
    if sed_dataDescription.isSetDimensionDescription():
        dict_dataDescription['dimensionDescription'] = {}
        sed_dimDescription = sed_dataDescription.getDimensionDescription()
        try:
            dict_dimDescription = _get_dict_dimDescription(sed_dimDescription)
        except ValueError as e:
            raise
        dict_dataDescription['dimensionDescription'] = dict_dimDescription
    if sed_dataDescription.getNumDataSources()>0:
        dict_dataDescription['listOfDataSources'] = []
    for sed_dataSource in sed_dataDescription.getListOfDataSources():
        try:
            dict_dataSource = _get_dict_dataSource(sed_dataSource)
        except ValueError as e:
            raise
        dict_dataDescription['listOfDataSources'].append(dict_dataSource)
    return dict_dataDescription

def change_init(sedModel, dict_change_Attribute):
    """"
    Define updates on the attribute values of the corresponding model.

    Parameters
    ----------
    sedModel: SedModel
        An instance of SedModel.
    dict_change_Attribute: dict
        The dictionary format: {'target': target_component_variable,'newValue':'1.0'}
        The target and newValue attributes are required.
    
    Raises
    ------
    ValueError
        If the target and newValue attributes of a change are not set.
        If any operation returns an error.

    Side effects
    ------------
    sedModel: SedModel
        The change is set.

    Returns
    -------
    bool
        Whether the change is set successfully.
    """  
    change = sedModel.createChangeAttribute()
    if 'target' not in dict_change_Attribute or 'newValue' not in dict_change_Attribute:
        raise ValueError('The target and newValue attributes of a change are required.')
    try:
        _operation_flag_check(change.setTarget(dict_change_Attribute['target']), 'Set the target attribute of a change')
        _operation_flag_check(change.setNewValue(dict_change_Attribute['newValue']), 'Set the newValue attribute of a change')
    except ValueError as e:
        raise
    return True   

def create_sedModel(doc,dict_model):
    """
    Create the models used in a simulation experiment

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_model: dict
        The dictionary format: {'id':'model1','source':'model.cellml','language':CELLML_URN,'listOfChanges':[dict_change_Attribute]}
        The id, source and language attributes of a model are required.
        The listOfChanges attribute is optional.
   
    Raises
    ------
    ValueError
        If the id, source and language attributes of a model are not set.
        If any operation returns an error.

    Notes
    -----
    Only ChangeAttribute is supported.
    Only CellML is supported. 

    Returns
    -------
    SedModel
        An instance of SedModel.
    """

    sedModel = doc.createModel()
    if 'id' not in dict_model or 'source' not in dict_model or 'language' not in dict_model:
        raise ValueError('The id, source and language attributes of a model are required.')
    try:
        _operation_flag_check(sedModel.setId(dict_model['id']), 'Set the id attribute of a model')
        _operation_flag_check(sedModel.setSource(dict_model['source']), 'Set the source attribute of a model')
        _operation_flag_check(sedModel.setLanguage(dict_model['language']), 'Set the language attribute of a model')
        if 'listOfChanges' in dict_model:
            for dict_change_Attribute in dict_model['listOfChanges']:
                change_init(sedModel, dict_change_Attribute)
    except ValueError as e:
        raise

    return sedModel

def get_dict_model(sedModel):
    """
    Get the information of a model
   
    Parameters
    ----------
    sedModel: SedModel
        An instance of SedModel.
    
    Notes
    -----
    Only ChangeAttribute is supported.

    Returns
    -------
    dict
        The dictionary format: {'id':'model1','source':'model.cellml','language':CELLML_URN,'listOfChanges':[dict_change_Attribute]}
        Only the attributes that are set will be returned.
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
            raise ValueError('The change type is not SedChangeAttribute.')
               
    return dict_model

def _setAlgorithmParameter(sed_algorithm, dict_algorithmParameter):
    """Parameterize a particular simulation algorithm.

    Parameters
    ----------
    sed_algorithm: SedAlgorithm
        An instance of SedAlgorithm.
    dict_algorithmParameter: dict
        The dictionary format: {'kisaoID':'KISAO:0000019','value':'1.0','name':'optional, describe the meaning of the param'}
        The kisaoID and value attributes are required.
        If the KiSAO term is a value, the string should contain a number; 
        If the KiSAO term is a Boolean, the string should contain the string \true" or \false", etc. 
        The string must be non-empty; 
        to explicitly state that a value is not set, 
        this should be encoded in the string as a KISAO:0000629, 
        which indicates that the value is Null.
    
    Raises
    ------
    ValueError
        If the kisaoID and value attributes of an algorithm parameter are not set.
        If any operation returns an error.

    Side effects
    ------------
    sed_algorithm: SedAlgorithm
        The algorithm parameter is set.

    Returns
    -------
    bool
        Whether the algorithm parameter is set successfully.
    """

    sed_algorithmParameter = sed_algorithm.createAlgorithmParameter()
    if 'kisaoID' not in dict_algorithmParameter or 'value' not in dict_algorithmParameter or dict_algorithmParameter['value']=='':
        raise ValueError('The kisaoID and value are required.')
    try:
        _operation_flag_check(sed_algorithmParameter.setKisaoID(dict_algorithmParameter['kisaoID']), 'Set the kisaoID attribute of an algorithm parameter')
        _operation_flag_check(sed_algorithmParameter.setValue(dict_algorithmParameter['value']), 'Set the value attribute of an algorithm parameter')
        if 'name' in dict_algorithmParameter:
            _operation_flag_check(sed_algorithmParameter.setName(dict_algorithmParameter['name']), 'Set the name attribute of an algorithm parameter')
    except ValueError as e:
        raise
    return True

def _get_dict_algorithmParameter(sed_algorithmParameter):
    """Get the information of an algorithm parameter

    Parameters
    ----------
    sed_algorithmParameter: SedAlgorithmParameter
        An instance of SedAlgorithmParameter.
    
    Raises
    ------
    ValueError
        If the kisaoID and value attributes of an algorithm parameter are not set.

    Returns
    -------
    dict
        The dictionary format: {'kisaoID':'KISAO:0000019','value':'1.0','name':'optional, describe the meaning of the param',}
        Only the attributes that are set will be returned.
    """
    dict_algorithmParameter = {}
    if sed_algorithmParameter.isSetName():
        dict_algorithmParameter['name'] = sed_algorithmParameter.getName()
    if sed_algorithmParameter.isSetKisaoID() and sed_algorithmParameter.isSetValue():
        dict_algorithmParameter['kisaoID'] = sed_algorithmParameter.getKisaoID()
        dict_algorithmParameter['value'] = sed_algorithmParameter.getValue()
    else:
        raise ValueError('The kisaoID and value attributes of an algorithm parameter are required.')
    return dict_algorithmParameter

def _setAlgorithm(sed_algorithm, dict_algorithm):
    """Defines the simulation algorithms used for the execution of the simulation

    Parameters
    ----------
    sed_algorithm: SedAlgorithm
        An instance of SedAlgorithm.
    dict_algorithm: dict
        The dictionary format: {'kisaoID':'KISAO:0000030','name':'optional,e.g,time course simulation over 100 minutes', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
    
    Raises
    ------
    ValueError
        If the kisaoID attribute of an algorithm is not set.
        If any operation returns an error.

    Side effects
    ------------
    sed_algorithm: SedAlgorithm
        The algorithm is set.

    Returns
    -------
    bool
        Whether the algorithm is set successfully.
    """
   
    if 'kisaoID' not in dict_algorithm:
        raise ValueError('The kisaoID attribute of an algorithm is required.')
    try:
        _operation_flag_check(sed_algorithm.setKisaoID(dict_algorithm['kisaoID']), 'Set the kisaoID attribute of an algorithm')
        if 'name' in dict_algorithm:
            _operation_flag_check(sed_algorithm.setName(dict_algorithm['name']), 'Set the name attribute of an algorithm')
        if 'listOfAlgorithmParameters' in dict_algorithm:
            for dict_algorithmParameter in dict_algorithm['listOfAlgorithmParameters']:
                _setAlgorithmParameter(sed_algorithm, dict_algorithmParameter)
    except ValueError as e:
        raise
    return True
    
def get_dict_algorithm(sed_algorithm):
    """Get the information of an algorithm
    
    Parameters
    ----------
    sed_algorithm: SedAlgorithm
        An instance of SedAlgorithm.
    
    Raises
    ------
    ValueError
        If the kisaoID attribute of an algorithm is not set.
        If _get_dict_algorithmParameter(sed_algorithmParameter) failed.

    Notes
    -----
    Assume that the algorithm parameters do not have any algorithm parameters.

    Returns
    -------
    dict
        The dictionary format: {'kisaoID':'KISAO:0000030','name':'optional,e.g,time course simulation over 100 minutes', 'listOfAlgorithmParameters':[dict_algorithmParameter]}
        Only the attributes that are set will be returned.
    """
    dict_algorithm = {}
    if not sed_algorithm.isSetKisaoID():
        raise ValueError('The kisaoID attribute of an algorithm is required.')
    dict_algorithm['kisaoID'] = sed_algorithm.getKisaoID()
    if sed_algorithm.isSetName():
        dict_algorithm['name'] = sed_algorithm.getName()
    if sed_algorithm.getNumAlgorithmParameters()>0:
        dict_algorithm['listOfAlgorithmParameters'] = []
        for sed_algorithmParameter in sed_algorithm.getListOfAlgorithmParameters():
            try:
                dict_algorithmParameter = _get_dict_algorithmParameter(sed_algorithmParameter)
            except ValueError as e:
                raise
            dict_algorithm['listOfAlgorithmParameters'].append(dict_algorithmParameter)
    return dict_algorithm

def create_sim_UniformTimeCourse(doc,dict_uniformTimeCourse):
    """
    Create a uniform time course simulation that calculates a time course output with equidistant time points.

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_uniformTimeCourse: dict
        The dictionary format: 
        {'id':'timeCourse1', 'type': 'UniformTimeCourse','algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
        The id, initialTime, outputStartTime, outputEndTime, numberOfSteps and algorithm of a simulation are required.
    
    Raises
    ------
    ValueError
        If the id, initialTime, outputStartTime, outputEndTime, numberOfSteps and algorithm of a simulation are not set.
        If any operation returns an error.

    Returns
    -------
    SedUniformTimeCourse
        An instance of SedUniformTimeCourse.
    """
    if 'id' not in dict_uniformTimeCourse or 'initialTime' not in dict_uniformTimeCourse or 'outputStartTime' not in dict_uniformTimeCourse or 'outputEndTime' not in dict_uniformTimeCourse or 'numberOfSteps' not in dict_uniformTimeCourse or 'algorithm' not in dict_uniformTimeCourse:
        raise ValueError('The id, initialTime, outputStartTime, outputEndTime, numberOfSteps and algorithm of a simulation are required.')
    sim = doc.createUniformTimeCourse() 
    try:
        _operation_flag_check(sim.setId(dict_uniformTimeCourse['id']), 'Set the id attribute of a simulation')
        _operation_flag_check(sim.setInitialTime(dict_uniformTimeCourse['initialTime']), 'Set the initialTime attribute of a simulation')
        _operation_flag_check(sim.setOutputStartTime(dict_uniformTimeCourse['outputStartTime']), 'Set the outputStartTime attribute of a simulation')
        _operation_flag_check(sim.setOutputEndTime(dict_uniformTimeCourse['outputEndTime']), 'Set the outputEndTime attribute of a simulation')
        _operation_flag_check(sim.setNumberOfPoints(dict_uniformTimeCourse['numberOfSteps']), 'Set the numberOfPoints attribute of a simulation')
        alg = sim.createAlgorithm()
        _setAlgorithm(alg, dict_uniformTimeCourse['algorithm'])
    except ValueError as e:
        raise
    return sim

def get_dict_uniformTimeCourse(sim):
    """
    Get the information of a uniform time course simulation

    Parameters
    ----------
    sim: SedUniformTimeCourse
        An instance of SedUniformTimeCourse.
    
    Raises
    ------
    ValueError
        If get_dict_algorithm(sed_algorithm) failed.

    Notes
    -----
    Assume the simulation has been created successfully.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'timeCourse1', 'type': 'UniformTimeCourse','algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}.
   
    """
    dict_uniformTimeCourse = {}
    dict_uniformTimeCourse['id'] = sim.getId()
    dict_uniformTimeCourse['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    dict_uniformTimeCourse['initialTime'] = sim.getInitialTime()
    dict_uniformTimeCourse['outputStartTime'] = sim.getOutputStartTime()
    dict_uniformTimeCourse['outputEndTime'] = sim.getOutputEndTime()
    dict_uniformTimeCourse['numberOfSteps'] = sim.getNumberOfPoints()
    sed_algorithm = sim.getAlgorithm()
    try:
        dict_algorithm = get_dict_algorithm(sed_algorithm)
    except ValueError as e:
        raise
    dict_uniformTimeCourse['algorithm']=dict_algorithm
    return dict_uniformTimeCourse

def create_sim_OneStep(doc,dict_oneStep):
    """
    Create a one step simulation that calculates one further output step for the model from its current state.
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_oneStep: dict
        The dictionary format: {'id':'oneStep1','type':'OneStep', 'step':0.1,'algorithm':dict_algorithm}
        The id, step and algorithm attributes of a simulation are required.
    
    Raises
    ------
    ValueError
        If the id, step and algorithm attributes of a simulation are not set.
        If any operation returns an error.

    Returns
    -------
    SedOneStep
        An instance of SedOneStep.
    """
    if 'id' not in dict_oneStep or 'step' not in dict_oneStep or 'algorithm' not in dict_oneStep:
        raise ValueError('The id, step and algorithm attributes of a simulation are required.')
    sim = doc.createOneStep() 
    try:
        _operation_flag_check(sim.setId(dict_oneStep['id']), 'Set the id attribute of a simulation')
        _operation_flag_check(sim.setStep(dict_oneStep['step']), 'Set the step attribute of a simulation')
        alg = sim.createAlgorithm()
        _setAlgorithm(alg, dict_oneStep['algorithm'])
    except ValueError as e:
        raise
    return sim   
    

def get_dict_oneStep(sim):
    """
    Get the information of a one step simulation
    
    Parameters
    ----------
    sim: SedOneStep
        An instance of SedOneStep.
    
    Raises
    ------
    ValueError
        If get_dict_algorithm(sed_algorithm) failed.

    Notes
    -----
    Assume the simulation has been created successfully.

    Returns
    -------
    dict or bool
        The dictionary format: {'id':'oneStep1','type':'OneStep', 'step':0.1,'algorithm':dict_algorithm}
        If the required attributes are not set, return False.    
    """

    dict_oneStep = {}
    dict_oneStep['id'] = sim.getId()
    dict_oneStep['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    dict_oneStep['step'] = sim.getStep()
    sed_algorithm = sim.getAlgorithm()
    try:
        dict_algorithm = get_dict_algorithm(sed_algorithm)
    except ValueError as e:
        raise  
    dict_oneStep['algorithm']=dict_algorithm
    return dict_oneStep

def create_sim_SteadyState(doc,dict_steadyState):
    """
    Create a steady state simulation that calculates a steady state output for the model.
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_steadyState: dict
        The dictionary format: {'id':'steadyState1','type':'SteadyState', 'algorithm':dict_algorithm}
        The id and algorithm attributes of a simulation are required.
    
    Raises
    ------
    ValueError
        If the id and algorithm attributes of a simulation are not set.
        If any operation returns an error.

    Returns
    -------
    SedSteadyState
        An instance of SedSteadyState.
    """

    if 'id' not in dict_steadyState or 'algorithm' not in dict_steadyState:
       raise ValueError('The id and algorithm attributes of a simulation are required.')
    sim = doc.createSteadyState()
    try:
        _operation_flag_check(sim.setId(dict_steadyState['id']), 'Set the id attribute of a simulation')
        alg = sim.createAlgorithm()
        _setAlgorithm(alg, dict_steadyState['algorithm'])
    except ValueError as e:
        raise
    return sim

def get_dict_steadyState(sim):
    """
    Get the information of a steady state simulation
    
    Parameters
    ----------
    sim: SedSteadyState
        An instance of SedSteadyState.
    
    Raises
    ------
    ValueError
        If get_dict_algorithm(sed_algorithm) failed.

    Notes
    -----
    Assume the simulation has been created successfully.

    Returns
    -------
    dict
        The dictionary format: {'id':'steadyState1','type':'SteadyState', 'algorithm':dict_algorithm}
    """
    dict_steadyState = {}
    dict_steadyState['id'] = sim.getId()
    dict_steadyState['type'] = libsedml.SedTypeCode_toString(sim.getTypeCode())
    sed_algorithm = sim.getAlgorithm()
    try:     
        dict_algorithm = get_dict_algorithm(sed_algorithm)
    except ValueError as e:
        raise
    dict_steadyState['algorithm'] = dict_algorithm
    return dict_steadyState

def create_simulation(doc,dict_simulation):
    """
    Create a simulation
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_simulation: dict
        If the simulation type is UniformTimeCourse, the dictionary format:
        {'id':'timeCourse1', 'type': 'UniformTimeCourse','algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
        If the simulation type is OneStep, the dictionary format:
        {'id':'oneStep1','type':'OneStep', 'step':0.1,'algorithm':dict_algorithm}
        If the simulation type is SteadyState, the dictionary format:
        {'id':'steadyState1','type':'SteadyState', 'algorithm':dict_algorithm}
    
    Raises
    ------
    ValueError
        If the simulation type is not defined.
        If any operation returns an error.

    Returns
    -------
    SedSimulation
        An instance of SedSimulation.
    """
    
    if dict_simulation['type'] != 'UniformTimeCourse' and dict_simulation['type'] != 'OneStep' and dict_simulation['type'] != 'SteadyState':
        raise ValueError('The simulation type is not defined.')
    try:
        if dict_simulation['type'] == 'UniformTimeCourse':
            sim = create_sim_UniformTimeCourse(doc,dict_simulation)
        elif dict_simulation['type'] == 'OneStep':
            sim = create_sim_OneStep(doc,dict_simulation)
        elif dict_simulation['type'] == 'SteadyState':
            sim = create_sim_SteadyState(doc,dict_simulation)
    except ValueError as e:
        raise
    return sim

def get_dict_simulation(sim):
    """
    Get the information of a simulation

    Parameters
    ----------
    sim: SedSimulation
        An instance of SedSimulation.
    
    Raises
    ------
    ValueError
        If the simulation type is not defined.
        If get_dict_uniformTimeCourse(sim), get_dict_oneStep(sim) or get_dict_steadyState(sim) failed.
    
    Notes
    -----
    Assume the simulation has been created successfully.

    Returns
    -------
    dict
        If the simulation type is UniformTimeCourse, the dictionary format:
        {'id':'timeCourse1', 'type': 'UniformTimeCourse','algorithm':dict_algorithm, 'initialTime':0.0,'outputStartTime':0.0,'outputEndTime':10.0,'numberOfSteps':1000}
        If the simulation type is OneStep, the dictionary format:
        {'id':'oneStep1','type':'OneStep', 'step':0.1,'algorithm':dict_algorithm}
        If the simulation type is SteadyState, the dictionary format:
        {'id':'steadyState1','type':'SteadyState', 'algorithm':dict_algorithm}
    """
    
    if not sim.isSedUniformTimeCourse() and not sim.isSedOneStep() and not sim.isSedSteadyState():
        raise ValueError('The simulation type is not defined.')
    try:
        if sim.isSedUniformTimeCourse():
            dict_simulation = get_dict_uniformTimeCourse(sim)
        elif sim.isSedOneStep():
            dict_simulation = get_dict_oneStep(sim)
        elif sim.isSedSteadyState():
            dict_simulation = get_dict_steadyState(sim)
    except ValueError as e:
        raise
    return dict_simulation

def create_task(doc,dict_task):
    """
    Create a task
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_task: dict
        The dictionary format: {'id':'task1','type':'Task','modelReference':'model1','simulationReference':'timeCourse1'}
        The id, modelReference and simulationReference attributes of a task are required.
    
    Raises
    ------
    ValueError
        If the id, modelReference and simulationReference attributes of a task are not set.
        If any operation returns an error.

    Side effects
    ------------
    doc: SedDocument
        The task is set.

    Returns
    -------
    SedTask
        An instance of SedTask.

    """
    if 'id' not in dict_task or 'modelReference' not in dict_task or 'simulationReference' not in dict_task:
        raise ValueError('The id, modelReference and simulationReference attributes of a task are required.')
    task = doc.createTask()
    try:
        _operation_flag_check(task.setId(dict_task['id']), 'Set the id attribute of a task')
        _operation_flag_check(task.setModelReference(dict_task['modelReference']), 'Set the modelReference attribute of a task')
        _operation_flag_check(task.setSimulationReference(dict_task['simulationReference']), 'Set the simulationReference attribute of a task')
    except ValueError as e:
        raise
    return task

def get_dict_task(task):
    """
    Get the information of a task
    
    Parameters
    ----------
    task: SedTask
        An instance of SedTask.
    
    Notes
    -----
    Assume the task has been created successfully.

    Returns
    -------
    dict
        The dictionary format: {'id':'task1','type':'Task','modelReference':'model1','simulationReference':'timeCourse1'}
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

    Parameters
    ----------
    repeatedTask: SedRepeatedTask
        An instance of SedRepeatedTask.
    dict_range: dict
        The dictionary format could be one of the following:
        UniformRange: {'id':'range1','type':'UniformRange', 'start':0.0,'end':10.0,
        'numberOfPoints':100,'type':'linear or log'}
        VectorRange: {'id':'range1','type':'VectorRange','values':[0.0,0.1,0.2,0.3,0.4,0.5]}
        DataRange: {'id':'range1','type':'DataRange','sourceReference':'data_source_1'}
        to construct a range by reference to external data
    
    Raises
    ------
    ValueError
        If the id, start, end, numberOfPoints and type attributes of a UniformRange are not set.
        If the id and values attributes of a VectorRange are not set.
        If the id and sourceReference attributes of a DataRange are not set.
        If any operation returns an error.

    Notes
    -----
    FunctionalRange is not supported.

    Side effects
    ------------
    repeatedTask: SedRepeatedTask
        The range is set.
   
    Returns
    -------
    bool
        Whether the range is set successfully.
    """
    if dict_range['type'] == 'UniformRange':
        if 'id' not in dict_range or 'start' not in dict_range or 'end' not in dict_range or 'numberOfPoints' not in dict_range or 'type' not in dict_range:
            raise ValueError('The id, start, end, numberOfPoints and type attributes of a UniformRange are required.')
    elif dict_range['type'] == 'VectorRange':
        if 'id' not in dict_range or 'values' not in dict_range:
            raise ValueError('The id and values attributes of a VectorRange are required.')
    elif dict_range['type'] == 'DataRange':
        if 'id' not in dict_range or 'sourceReference' not in dict_range:
            raise ValueError('The id and sourceReference attributes of a DataRange are required.')
    else:
        raise ValueError('The range is not defined.')
    try:
        if dict_range['type'] == 'UniformRange':
            sed_range = repeatedTask.createUniformRange()
            _operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range')
            _operation_flag_check(sed_range.setStart(dict_range['start']), 'Set the start attribute of a range')
            _operation_flag_check(sed_range.setEnd(dict_range['end']), 'Set the end attribute of a range')
            _operation_flag_check(sed_range.setNumberOfPoints(dict_range['numberOfPoints']), 'Set the numberOfPoints attribute of a range')
            _operation_flag_check(sed_range.setType(dict_range['type']), 'Set the type attribute of a range')
        elif dict_range['type'] == 'VectorRange':
            sed_range = repeatedTask.createVectorRange()
            _operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range')
            _operation_flag_check(sed_range.setValues(dict_range['values']), 'Set the values attribute of a range')
        elif dict_range['type'] == 'DataRange':
            sed_range = repeatedTask.createDataRange()
            _operation_flag_check(sed_range.setId(dict_range['id']), 'Set the id attribute of a range')
            _operation_flag_check(sed_range.setSourceReference(dict_range['sourceReference']), 'Set the sourceReference attribute of a range')
    except ValueError as e:
        raise
    return True

def _get_dict_range(sed_range):
    """
    Get the information of a range
    
    Parameters
    ----------
    sed_range: SedRange
        An instance of SedRange.
    
    Raises
    ------
    ValueError
        If the range is not defined.

    Notes
    -----
    Assume the range has been created successfully.
    FunctionalRange is not supported.

    Returns
    -------
    dict
        The dictionary format could be one of the following:
        UniformRange: {'id':'range1','type':'UniformRange', 'start':0.0,'end':10.0,
        'numberOfPoints':100,'type':'linear or log'}
        VectorRange: {'id':'range1','type':'VectorRange','values':[0.0,0.1,0.2,0.3,0.4,0.5]}
        DataRange: {'id':'range1','type':'DataRange','sourceReference':'data_source_1'} 
        to construct a range by reference to external data
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
        raise ValueError('The range is not defined.')
    return dict_range

def _setChange4Task(task,dict_setValue):
    """
    Set change (SedSetValue) to modify the model for a repeatedTask
    
    Parameters
    ----------
    task: SedRepeatedTask
        An instance of SedRepeatedTask.
    dict_setValue: dict
        The dictionary format: {'target':target_component_variable,'modelReference':'model1',
        'symbol':None,'range':None,'math':None}
        The target and modelReference attributes of a set value are required.
    
    Raises
    ------
    ValueError
        If the target and modelReference attributes of a set value are not set.
        If any operation returns an error.

    Side effects
    ------------
    task: SedRepeatedTask
        The change (SedSetValue) is added to the task.

    Returns
    -------
    bool
        Whether the change (SedSetValue) is set successfully.
    """
    if 'target' not in dict_setValue or 'modelReference' not in dict_setValue:
       raise ValueError('The target and modelReference attributes of a set value are required.')
    setValue = task.createTaskChange()
    try:
        _operation_flag_check(setValue.setTarget(dict_setValue['target']), 'Set the target attribute of a set value')
        _operation_flag_check(setValue.setModelReference(dict_setValue['modelReference']), 'Set the modelReference attribute of a set value')
        if 'symbol' in dict_setValue:
            _operation_flag_check(setValue.setSymbol(dict_setValue['symbol']), 'Set the symbol attribute of a set value')
        if 'range' in dict_setValue:
            _operation_flag_check(setValue.setRange(dict_setValue['range']), 'Set the range attribute of a set value')
        if 'math' in dict_setValue:
            _operation_flag_check(setValue.setMath(libsedml.parseL3Formula(dict_setValue['math'])), 'Set the math attribute of a set value')
    except ValueError as e:
        raise
    return True

def _get_dict_setValue(setValue):
    """
    Get the information of a set value
   
    Parameters
    ----------
    setValue: SedSetValue
        An instance of SedSetValue.

    Returns
    -------
    dict
        The dictionary format: {'target':target_component_variable,'modelReference':'model1',
        'symbol':None,'range':None,'math':None}
        Only the attributes that are set will be returned.
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
    
    Parameters
    ----------
    subTask: SedSubTask
        An instance of SedSubTask.
    dict_subTask: dict
        The dictionary format: {'order':1,'task':'task1','listOfChanges':[dict_setValue]}
        The order and task attributes of a sub task are required.
    
    Raises
    ------
    ValueError
        If the order and task attributes of a sub task are not set.
        If any operation returns an error.

    Side effects
    ------------
    subTask: SedSubTask
        The subtask is set.

    Returns
    -------
    SedSubTask
        An instance of SedSubTask.
    """
    if 'order' not in dict_subTask or 'task' not in dict_subTask:
       raise ValueError('The order and task attributes of a sub task are required.')
    try:
        _operation_flag_check(subTask.setOrder(dict_subTask['order']), 'Set the order attribute of a sub task')
        _operation_flag_check(subTask.setTask(dict_subTask['task']), 'Set the task attribute of a sub task')
        if 'listOfChanges' in dict_subTask:
            for dict_setValue in dict_subTask['listOfChanges']:
                _setChange4Task(subTask,dict_setValue)
    except ValueError as e:
        raise
    return subTask

def _get_dict_subTask(subTask):
    """
    Get the information of a subtask
    
    Parameters
    ----------
    subTask: SedSubTask
        An instance of SedSubTask.

    Returns
    -------
    dict
        The dictionary format: {'order':1,'task':'task1','listOfChanges':[dict_setValue]}
        Only the attributes that are set will be returned.
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
    Create a repeated task that provides a looping construct, 
    allowing complex tasks to be composed from individual tasks. 
    The RepeatedTask performs a specfied task 
    (or sequence of tasks as defined in the listOfSubTasks) multiple times 
    (where the exact number is specified through a Range construct as defined in range), 
    while allowing specific quantities in the model or models to be altered at each iteration
    (as defined in the listOfChanges).

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_repeatedTask: dict
        The dictionary format: 
        {'id':'repeatedTask1','type':'RepeatedTask','resetModel':bool,'range':'range1','concatenate':bool,
        'listOfChanges':[dict_setValue],'listOfRanges':[dict_uniformRange,dict_vectorRange,dict_dataRange], 'listOfSubTasks':[dict_subTask]}
        resetModel: specifies whether the model or models should be reset to the initial state
        before processing an iteration of the defined subTasks.
        range: specifies which range defined in the listOfRanges this repeated task iterates over.
        concatenate: optional but strongly suggest to be defined,specifies whether the output of the subtasks
        should be appended to the results of the previous outputs (True), 
        or whether it should be added in parallel, as a new dimension of the output (False).
    
    Raises
    ------
    ValueError
        If the id, resetModel, range, concatenate, listOfRanges and listOfSubTasks attributes of a repeated task are not set.
        If any operation returns an error.

    Returns
    -------
    SedRepeatedTask
        An instance of SedRepeatedTask.       
    """

    if 'id' not in dict_repeatedTask or 'resetModel' not in dict_repeatedTask or 'range' not in dict_repeatedTask or 'concatenate' not in dict_repeatedTask or 'listOfRanges' not in dict_repeatedTask or 'listOfSubTasks' not in dict_repeatedTask:
       raise ValueError('The id, resetModel, range, concatenate, listOfRanges and listOfSubTasks attributes of a repeated task are required.')
    repeatedTask=doc.createRepeatedTask()
    try:
        _operation_flag_check(repeatedTask.setId(dict_repeatedTask['id']), 'Set the id attribute of a repeated task')
        _operation_flag_check(repeatedTask.setResetModel(dict_repeatedTask['resetModel']), 'Set the resetModel attribute of a repeated task')
        _operation_flag_check(repeatedTask.setRangeId(dict_repeatedTask['range']), 'Set the range attribute of a repeated task')
        _operation_flag_check(repeatedTask.setConcatenate(dict_repeatedTask['concatenate']), 'Set the concatenate attribute of a repeated task')
        if 'listOfChanges' in dict_repeatedTask:
            for dict_setValue in dict_repeatedTask['listOfChanges']:
                _setChange4Task(repeatedTask,dict_setValue)
        for dict_range in dict_repeatedTask['listOfRanges']:
            _setRange(repeatedTask,dict_range)
        for dict_subTask in dict_repeatedTask['listOfSubTasks']:
            subTask = repeatedTask.createSubTask()
            _setSubTask(subTask,dict_subTask)
    except ValueError as e:
        raise
    return repeatedTask    

def get_dict_repeatedTask(repeatedTask):
    """
    Get the information of a repeated task
    
    Parameters
    ----------
    repeatedTask: SedRepeatedTask
        An instance of SedRepeatedTask.
    
    Raises
    ------
    ValueError.
        If _get_dict_range(sed_range) failed.

    Notes
    -----
    Assume the repeated task has been created successfully.

    Returns
    -------
    dict 
        The dictionary format: 
        {'id':'repeatedTask1','type':'RepeatedTask','resetModel':bool,'range':'range1','concatenate':bool,
        'listOfChanges':[dict_setValue],'listOfRanges':[dict_uniformRange,dict_vectorRange,dict_dataRange], 'listOfSubTasks':[dict_subTask]}
        Only the attributes that are set will be returned.
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
        try:
            dict_sedRange = _get_dict_range(sedRange)
        except ValueError as e:
            raise
        dict_repeatedTask['listOfRanges'].append(dict_sedRange)
    dict_repeatedTask['listOfSubTasks'] = []
    for subTask in repeatedTask.getListOfSubTasks():
        dict_repeatedTask['listOfSubTasks'].append(_get_dict_subTask(subTask))
    return dict_repeatedTask

def _setAdjustableParameter(task_pe,dict_adjustableParameter):
    """
    Set the adjustable parameter for a parameter estimation task

    Parameters
    ----------
    task_pe: SedParameterEstimationTask
        An instance of SedParameterEstimationTask.
    dict_adjustableParameter: dict
        The dictionary format:
        {'id':'parameter1','modelReference':'model1','target':target_component_variable,
        'initialValue':None or double,'bounds':dict_bounds,'listOfExperimentReferences':[dict_experimentReference]}
        dict_bounds format: {'lowerBound':0.0,'upperBound':10.0,'scale':'linear or log or log10''}
        The target must point to an adjustable element of the Model referenced by the parent ParameterEstimationTask.
        This element is one of the elements whose value can be changed by the task in order to optimize the fit experiments.
        Note: If an AdjustableParameter has no ExperimentReference children, it is adjusted for every FitExperiment.
        The id, modelReference, target and bounds attributes of an adjustable parameter are required.
        Notes: 
        The modelReference is not required in the SED-ML L1V4.
        The modelReference is required in the current version of libSEDML.
    
    Raises
    ------
    ValueError
        If the id, modelReference, target and bounds attributes of an adjustable parameter are not set.
        If the upperBound, lowerBound and scale attributes of bounds are not set.
        If any operation returns an error.

    Side effects
    ------------
    task_pe: SedParameterEstimationTask
        The adjustable parameter is added to the task.

    Returns
    -------
    bool
        Whether the adjustable parameter is set successfully.
    """

    if 'id' not in dict_adjustableParameter or 'modelReference' not in dict_adjustableParameter or 'target' not in dict_adjustableParameter or 'bounds' not in dict_adjustableParameter:
        raise ValueError('The id, modelReference, target and bounds attributes of an adjustable parameter are required.')
    if 'upperBound' not in dict_adjustableParameter['bounds'] or 'lowerBound' not in dict_adjustableParameter['bounds'] or 'scale' not in dict_adjustableParameter['bounds']:
        raise ValueError('The upperBound, lowerBound and scale attributes of bounds are required.')
    p=task_pe.createAdjustableParameter()
    try:
        _operation_flag_check(p.setId(dict_adjustableParameter['id']), 'Set the id attribute of an adjustable parameter')
        _operation_flag_check(p.setModelReference(dict_adjustableParameter['modelReference']), 'Set the modelReference attribute of an adjustable parameter')
        _operation_flag_check(p.setTarget(dict_adjustableParameter['target']), 'Set the target attribute of an adjustable parameter')
        if 'initialValue' in dict_adjustableParameter:
            _operation_flag_check(p.setInitialValue(dict_adjustableParameter['initialValue']), 'Set the initialValue attribute of an adjustable parameter')
        bounds=p.createBounds()
        _operation_flag_check(bounds.setLowerBound(dict_adjustableParameter['bounds']['lowerBound']), 'Set the lowerBound attribute of an adjustable parameter')
        _operation_flag_check(bounds.setUpperBound(dict_adjustableParameter['bounds']['upperBound']), 'Set the upperBound attribute of an adjustable parameter')
        _operation_flag_check(bounds.setScale(dict_adjustableParameter['bounds']['scale']), 'Set the scale attribute of an adjustable parameter')
        if 'listOfExperimentReferences' in dict_adjustableParameter:
            for dict_experimentReference in dict_adjustableParameter['listOfExperimentReferences']:
                _operation_flag_check(p.createExperimentReference().setExperimentId(dict_experimentReference), 'Set the experimentReference attribute of an adjustable parameter')
    except ValueError as e:
        raise
    return True

def _get_dict_adjustableParameter(p):
    """
    Get the information of an adjustable parameter
    
    Parameters
    ----------
    p: SedAdjustableParameter
        An instance of SedAdjustableParameter.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'parameter1','modelReference':'model1','target':target_component_variable,
        'initialValue':None or double,'bounds':dict_bounds,'listOfExperimentReferences':[dict_experimentReference]}
        dict_bounds format: {'lowerBound':0.0,'upperBound':10.0,'scale':'linear or log or log10''}
        Only the attributes that are set will be returned.
    """
    dict_adjustableParameter = {}
    dict_adjustableParameter['id'] = p.getId()
    dict_adjustableParameter['modelReference'] = p.getModelReference() # The modelReference is not required in the SED-ML L1V4.
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
    Set the fitExperiment describing an experiment 
    for which there are known experimental conditions, and expected experimental output. 
    The differences between the expected experimental output 
    and the simulated output is used by the Objective to determine
    the optimal values to use for the AdjustableParameters.
    
    Parameters
    ----------
    task_pe: SedParameterEstimationTask
        An instance of SedParameterEstimationTask.
    dict_fitExperiment: dict
        The dictionary format:
        {'id':'fitExperimen1','type':'timeCourse or steadyState or invalid ExperimentType value',
        'algorithm':dict_algorithm,'listOfFitMappings':[dict_fitMapping]}
        fitMapping is used to correlate elements of a model with data for that simulation,
        whether time, inputs (experimental conditions) or outputs (observables).
        dict_fitMapping format:
        {'type':'time or observable or experimentalCondition','dataSource':'data_source_1',
        'target':'is an SIdRef to a DataGenerator','weight':None,'pointWeight':None}
        time: Used only in time course simulations, maps the time points of the observables to the time points of the simulated output;
        declare what time points must be output by the simulation.
        experimentalCondition: maps a single value to a model element.
        The model element must be set to the value as part of the model's initial condition.
        observable: maps the output of the simulation to a set of data.
        dataSource is a pointer to the expected values;
        target is a pointer to the simulated values;
        The weight or pointWeight attributes are used for observable only.
        The id, type and algorithm attributes of a fit experiment are required.
    
    Raises
    ------
    ValueError
        If the id, type, algorithm and listOfFitMappings attributes of a fit experiment are not set.
        If both weight and pointWeight attributes of a fit mapping (observable) are set.
        If the weight or pointWeight attributes of a fit mapping (observable) are not set.
        If any operation returns an error.

    Side effects
    ------------
    task_pe: SedParameterEstimationTask
        The fit experiment is added to the task.

    Returns
    -------
    bool
        Whether the fit experiment is set successfully.
    """

    if 'id' not in dict_fitExperiment or 'type' not in dict_fitExperiment or 'algorithm' not in dict_fitExperiment or 'listOfFitMappings' not in dict_fitExperiment:
        raise ValueError('The id, type, algorithm and listOfFitMappings attributes of a fit experiment are required.')
    fe=task_pe.createFitExperiment()
    try:
        _operation_flag_check(fe.setId(dict_fitExperiment['id']), 'Set the id attribute of a fit experiment')
        _operation_flag_check(fe.setType(dict_fitExperiment['type']), 'Set the type attribute of a fit experiment')
        if 'name' in dict_fitExperiment:
            _operation_flag_check(fe.setName(dict_fitExperiment['name']), 'Set the name attribute of a fit experiment')
        alg=fe.createAlgorithm()
        _setAlgorithm(alg, dict_fitExperiment['algorithm'])
    except ValueError as e:
        raise

    for dict_fitMapping in dict_fitExperiment['listOfFitMappings']:
        if dict_fitMapping['type']=='observable':
            if 'weight' in dict_fitMapping and 'pointWeight' in dict_fitMapping:
                raise ValueError('The weight and pointWeight attributes of a fit mapping (observable) are mutually exclusive.')
            if 'weight' not in dict_fitMapping and 'pointWeight' not in dict_fitMapping:
                raise ValueError('The weight or pointWeight attributes of a fit mapping (observable) are required.')
        fitMapping=fe.createFitMapping()
        try:
            _operation_flag_check(fitMapping.setType(dict_fitMapping['type']), 'Set the type attribute of a fit mapping')
            _operation_flag_check(fitMapping.setDataSource(dict_fitMapping['dataSource']), 'Set the dataSource attribute of a fit mapping')
            _operation_flag_check(fitMapping.setTarget(dict_fitMapping['target']), 'Set the target attribute of a fit mapping')
            if 'weight' in dict_fitMapping and dict_fitMapping['weight'] is not None:
                _operation_flag_check(fitMapping.setWeight(dict_fitMapping['weight']), 'Set the weight attribute of a fit mapping')
            if 'pointWeight' in dict_fitMapping and dict_fitMapping['pointWeight'] is not None:
                _operation_flag_check(fitMapping.setPointWeight(dict_fitMapping['pointWeight']), 'Set the pointWeight attribute of a fit mapping')
        except ValueError as e:
            raise
    return True
   
def _get_dict_fitExperiment(fe):
    """
    Get the information of a fit experiment

    Parameters
    ----------
    fe: SedFitExperiment
        An instance of SedFitExperiment.
    
    Raises
    ------
    ValueError
        If get_dict_algorithm(sed_algorithm) failed.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'fitExperimen1','type':'timeCourse or steadyState or invalid ExperimentType value',
        'algorithm':dict_algorithm,'listOfFitMappings':[dict_fitMapping]}
        Only the attributes that are set will be returned.
    """

    dict_fitExperiment = {}
    dict_fitExperiment['id'] = fe.getId()
    dict_fitExperiment['type'] = fe.getTypeAsString()
    if fe.isSetName():
        dict_fitExperiment['name'] = fe.getName()
    sed_algorithm = fe.getAlgorithm()
    try:
        dict_fitExperiment['algorithm'] = get_dict_algorithm(sed_algorithm)
    except ValueError as e:
        raise    
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
            else:
                raise ValueError('The weight or pointWeight attributes of a fit mapping (observable) are required.')
        dict_fitExperiment['listOfFitMappings'].append(dict_fitMapping)
    return dict_fitExperiment

def create_parameterEstimationTask(doc,dict_parameterEstimationTask):
    """
    Create a parameter estimation task that defines a parameter estimation problem to be solved.

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_parameterEstimationTask: dict
        The dictionary format: 
        {'id':'parameterEstimationTask1','type':'ParameterEstimationTask','algorithm':dict_algorithm,'objective':{'type':'leastSquare'},
        'listOfAdjustableParameters':[dict_adjustableParameter],'listOfFitExperiments':[dict_fitExperiment]}
        The id, algorithm, objective, listOfAdjustableParameters and listOfFitExperiments attributes of a parameter estimation task are required.
        Notes: The modelReference attribute should be required according to SED-ML L1V4,
        but the current libSEDML does not support it.
        Instead, the modelReference attribute is required in the adjustableParameter.
    
    Raises
    ------
    ValueError
        If the id, algorithm, objective, listOfAdjustableParameters and listOfFitExperiments attributes of a parameter estimation task are not set.
        If the objective type is not leastSquare.
        If any operation returns an error.

    Side effects
    ------------
    doc: SedDocument
        The parameter estimation task is set.

    Returns:
    --------
    SedParameterEstimationTask
        An instance of SedParameterEstimationTask.  
    """

    if 'id' not in dict_parameterEstimationTask or 'algorithm' not in dict_parameterEstimationTask or 'objective' not in dict_parameterEstimationTask or 'listOfAdjustableParameters' not in dict_parameterEstimationTask or 'listOfFitExperiments' not in dict_parameterEstimationTask:
        raise ValueError('The id, algorithm, objective, listOfAdjustableParameters and listOfFitExperiments attributes of a parameter estimation task are required.')
    if dict_parameterEstimationTask['objective']['type'] != 'leastSquare':
        raise ValueError('In Level 1 Version 4, there is only a single Objective option: theLeastSquareObjectiveFunction (called \leastSquareObjectiveFunction" instead of \objective")')
    task_pe = doc.createParameterEstimationTask()
    
    try:
        _operation_flag_check(task_pe.setId(dict_parameterEstimationTask['id']), 'Set the id attribute of a parameter estimation task')
        alg = task_pe.createAlgorithm()
        _setAlgorithm(alg, dict_parameterEstimationTask['algorithm'])
        task_pe.createLeastSquareObjectiveFunction()
        for dict_adjustableParameter in dict_parameterEstimationTask['listOfAdjustableParameters']:
            _setAdjustableParameter(task_pe,dict_adjustableParameter)
        for dict_fitExperiment in dict_parameterEstimationTask['listOfFitExperiments']:
            _setFitExperiment(task_pe,dict_fitExperiment)
    except ValueError as e:
        raise
    return task_pe

def get_dict_parameterEstimationTask(task_pe):
    """
    Get the information of a parameter estimation task
    
    Parameters
    ----------
    task_pe: SedParameterEstimationTask
        An instance of SedParameterEstimationTask.
    
    Raises
    ------
    ValueError
        If get_dict_algorithm(opt_algorithm) failed.
        If get_dict_fitExperiment(fitExperiment) failed.

    Notes
    -----
    Assume the parameter estimation task has been created successfully.

    Returns
    -------
    dict
        The dictionary format: 
        {'id':'parameterEstimationTask1','type':'ParameterEstimationTask','algorithm':dict_algorithm,'objective':{'type':'leastSquare'},
        'listOfAdjustableParameters':[dict_adjustableParameter],'listOfFitExperiments':[dict_fitExperiment]}
        Only the attributes that are set will be returned.
    """
    dict_parameterEstimationTask = {}
    dict_parameterEstimationTask['id'] = task_pe.getId()
    dict_parameterEstimationTask['type']=libsedml.SedTypeCode_toString(task_pe.getTypeCode())
    # dict_parameterEstimationTask['modelReference'] = task_pe.getModelReference()
    opt_algorithm = task_pe.getAlgorithm()
    try:
        dict_parameterEstimationTask['algorithm'] = get_dict_algorithm(opt_algorithm)
    except ValueError as e:
        raise
    dict_parameterEstimationTask['objective'] = 'leastSquare' 
    dict_parameterEstimationTask['listOfAdjustableParameters'] = []
    for adjustableParameter in task_pe.getListOfAdjustableParameters():
        dict_parameterEstimationTask['listOfAdjustableParameters'].append(_get_dict_adjustableParameter(adjustableParameter))
    dict_parameterEstimationTask['listOfFitExperiments'] = []
    for fitExperiment in task_pe.getListOfFitExperiments():
        try: 
            dict_fitExperiment = _get_dict_fitExperiment(fitExperiment)
        except ValueError as e:
            raise
        dict_parameterEstimationTask['listOfFitExperiments'].append(dict_fitExperiment)
    return dict_parameterEstimationTask

def create_abstractTask(doc,dict_Task):
    """
    Create an abstract task that provides a base class for all tasks in SED-ML.

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_Task: dict
        The dictionary format:
        if the type is RepeatedTask: dict_repeatedTask
        if the type is Task: dict_task
        if the type is ParameterEstimationTask: dict_parameterEstimationTask
    
    Raises
    ------
    ValueError
        If the typeCode is not defined.
        If any operation returns an error.

    Side effects
    ------------
    doc: SedDocument
        The abstract task is set.

    Returns:
    --------
    SedAbstractTask
        An instance of SedAbstractTask.
    """       
   
    if dict_Task['type'] == 'RepeatedTask':
        try:
            task=create_repeatedTask(doc,dict_Task)
        except ValueError as e:
            raise
    elif dict_Task['type'] == 'Task':
        try:
            task=create_task(doc,dict_Task)
        except ValueError as e:
            raise
    elif dict_Task['type'] == 'ParameterEstimationTask'	:
        try:
            task=create_parameterEstimationTask(doc,dict_Task)
        except ValueError as e:
            raise
    else:
        raise ValueError('The typeCode is not defined.')
    return task

def get_dict_abstractTask(task):
    """
    Get the information of an abstract task

    Parameters
    ----------
    task: SedAbstractTask
        An instance of SedAbstractTask.
    
    Raises
    ------
    ValueError
        If the type of the abstract task is not supported.
        If get_dict_repeatedTask(task) failed.
        If get_dict_parameterEstimationTask(task) failed.
    Notes
    -----
    Assume the abstract task has been created successfully.

    Returns
    -------
    dict
        The dictionary format:
        if the type is RepeatedTask: dict_repeatedTask
        if the type is Task: dict_task
        if the type is ParameterEstimationTask: dict_parameterEstimationTask
        Only the attributes that are set will be returned.
    """

    if task.isSedRepeatedTask():
        try:
            dict_task = get_dict_repeatedTask(task)
        except ValueError as e:
            raise
    elif task.isSedTask():
        dict_task = get_dict_task(task)
    elif task.isSedParameterEstimationTask():
        try:
            dict_task = get_dict_parameterEstimationTask(task)
        except ValueError as e:
            raise
    else:
       raise ValueError('The type of the abstract task is not supported.')
    return dict_task

def _setVariable(sedVariable,dict_variable):
    """
    Set the attributes of a variable

    Parameters
    ----------
    sedVariable: SedVariable
        An instance of SedVariable.
    dict_variable: dict
        The dictionary format:
        {'id':'variable1','name':None,'target':None,'symbol':None,'target2':None,'symbol2':None,
        'term':None,'modelReference':None,'taskReference':None,
        'dimensionTerm':None,'listOfAppliedDimensions':[dict_appliedDimension],'metaid':None
        }
        - 'id' is required.
        - 'target' could be XPath expressions to an explicit element of a model (e.g.,an SBML Species or a CellML Variable),
        the id of a DataGenerator or DataSource (e.g., #dataSource1") in the same document.
        - 'symbol' is a kisaoID, to refer either to a predefined, implicit variable 
        or to a predefined implicit function to be performed on the target.
        - 'target2' or 'symbol2' refers to a second mathematical element, and is always used in conjunction with a term.
        -'term' is a kisaoID, referring to a function or an analysis dependent on the model.
        - 'dimensionTerm' attribute has exactly the same constraints as the term attribute,
        but must refer to a KiSAO term that reduces the dimensionality of multidimensional data.
        Currently, all such KiSAO terms inherit from "KISAO:0000824" (`aggregation function') 
        and includes functions such as mean ("KISAO:0000825"), standard deviation ("KISAO:0000826"), and maximum ("KISAO:0000828").
        dict_appliedDimension format: {'target':None,'dimensionTarget':None}
        - 'appliedDimension' is used only when dimensionTerm of the Variable is defined
        * target is used when the applied dimension is a Task or RepeatedTask, possible values are:
        the id of a repeatedTask, the id of a task referenced by a repeatedTask, or the id of a subtask child of a repeatedTask
        * dimensionTarget is used when the Variable references an external data source.
        The NuMLIdRef must reference a dimension of the referenced data.
   
    Raises
    ------
    ValueError
        If the id attribute of a variable is not set.
        If the dimensionTerm attribute is defined but the listOfAppliedDimensions attribute of a variable is empty.
        If any operation returns an error.

    Side effects
    ------------
    sedVariable: SedVariable
        The variable is set.

    Returns
    -------
    bool
        Whether the variable is set successfully.
    """
    if 'id' not in dict_variable:
        raise ValueError('The id attribute of a variable is required.')
    if 'dimensionTerm' in dict_variable:
        if 'listOfAppliedDimensions' not in dict_variable or len(dict_variable['listOfAppliedDimensions'])==0:
            raise ValueError('The dimensionTerm attribute is defined but the listOfAppliedDimensions attribute of a variable is empty.')
    try:
        _operation_flag_check(sedVariable.setId(dict_variable['id']), 'Set the id attribute of a variable')
        if 'name' in dict_variable:
            _operation_flag_check(sedVariable.setName(dict_variable['name']), 'Set the name attribute of a variable')
        if 'target' in dict_variable:
            _operation_flag_check(sedVariable.setTarget(dict_variable['target']), 'Set the target attribute of a variable')
        if 'symbol' in dict_variable:
            _operation_flag_check(sedVariable.setSymbol(dict_variable['symbol']), 'Set the symbol attribute of a variable')
        if 'target2' in dict_variable:
            _operation_flag_check(sedVariable.setTarget2(dict_variable['target2']), 'Set the target2 attribute of a variable')
        if 'symbol2' in dict_variable:
            _operation_flag_check(sedVariable.setSymbol2(dict_variable['symbol2']), 'Set the symbol2 attribute of a variable')
        if 'term' in dict_variable:
            _operation_flag_check(sedVariable.setTerm(dict_variable['term']), 'Set the term attribute of a variable')
        if 'modelReference' in dict_variable:
            _operation_flag_check(sedVariable.setModelReference(dict_variable['modelReference']), 'Set the modelReference attribute of a variable')
        if 'taskReference' in dict_variable:
            _operation_flag_check(sedVariable.setTaskReference(dict_variable['taskReference']), 'Set the taskReference attribute of a variable')
        if 'dimensionTerm' in dict_variable:
            _operation_flag_check(sedVariable.setDimensionTerm(dict_variable['dimensionTerm']), 'Set the dimensionTerm attribute of a variable')
            for dict_appliedDimension in dict_variable['listOfAppliedDimensions']:
                appliedDimension=sedVariable.createAppliedDimension()
                if 'target' in dict_appliedDimension:
                    _operation_flag_check(appliedDimension.setTarget(dict_appliedDimension['target']), 'Set the target attribute of an applied dimension')
                elif 'dimensionTarget' in dict_appliedDimension:
                    _operation_flag_check(appliedDimension.setDimensionTarget(dict_appliedDimension['dimensionTarget']), 'Set the dimensionTarget attribute of an applied dimension')
        if 'metaid' in dict_variable:
            _operation_flag_check(sedVariable.setMetaId(dict_variable['metaid']), 'Set the metaid attribute of a variable')       
    except ValueError as e:
        raise

    return True

def _get_dict_variable(sedVariable):
    """
    Get the information of a variable
    
    Parameters
    ----------
    sedVariable: SedVariable
        An instance of SedVariable.
    
    Raises
    ------
    ValueError
        If the id attribute of a variable is required.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'variable1','name':None,'target':None,'symbol':None,'target2':None,'symbol2':None,
        'term':None,'modelReference':None,'taskReference':None,
        'dimensionTerm':None,'listOfAppliedDimensions':[dict_appliedDimension],'metaid':None
        }
        Only the attributes that are set will be returned.                              
    """

    if  not sedVariable.isSetId ():
        raise ValueError('The id attribute of a variable is required.')
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

    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_dataGenerator: dict
        The dictionary format:
        {'id':'dataGenerator1','name':'dataGenerator1','math':'varId or complex math infix ','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
        dict_parameter format: {'id':'param1','name':None,'value':float,'metaid':None}
        The id, and math attributes of a data generator are required.

    Raises
    ------
    ValueError
        If the id and math attributes of a data generator are not set.
        If the id and value attributes of a parameter are not set.
        If any operation returns an error.

    Side effects
    ------------
    doc: SedDocument
        The data generator is set.

    Returns
    -------
    SedDataGenerator
        An instance of SedDataGenerator.
    """

    if 'id' not in dict_dataGenerator or 'math' not in dict_dataGenerator:
        raise ValueError('The id and math attributes of a data generator are required.')
    dataGenerator=doc.createDataGenerator()
    try:
        _operation_flag_check(dataGenerator.setId(dict_dataGenerator['id']), 'Set the id attribute of a data generator')
        if 'name' in dict_dataGenerator:
            _operation_flag_check(dataGenerator.setName(dict_dataGenerator['name']), 'Set the name attribute of a data generator')
        _operation_flag_check(dataGenerator.setMath(libsedml.parseFormula(dict_dataGenerator['math'])), 'Set the math attribute of a data generator')
        if 'listOfVariables' in dict_dataGenerator:
            for dict_variable in dict_dataGenerator['listOfVariables']:
                sedVariable=dataGenerator.createVariable()
                _setVariable(sedVariable,dict_variable)
    except ValueError as e:
        raise
    if 'listOfParameters' in dict_dataGenerator:
        for dict_parameter in dict_dataGenerator['listOfParameters']:
            if 'id' not in dict_parameter or 'value' not in dict_parameter:
                raise ValueError('The id and value attributes of a parameter are required.')
            sedParameter=dataGenerator.createParameter()
            try:
                _operation_flag_check(sedParameter.setId(dict_parameter['id']), 'Set the id attribute of a parameter')
                if 'name' in dict_parameter:
                    _operation_flag_check(sedParameter.setName(dict_parameter['name']), 'Set the name attribute of a parameter')
                _operation_flag_check(sedParameter.setValue(dict_parameter['value']), 'Set the value attribute of a parameter')
                if 'metaid' in dict_parameter:
                    _operation_flag_check(sedParameter.setMetaId(dict_parameter['metaid']), 'Set the metaid attribute of a parameter')
            except ValueError as e:
                raise
    return dataGenerator

def get_dict_dataGenerator(dataGenerator):
    """
    Get the information of a data generator

    Parameters
    ----------
    dataGenerator: SedDataGenerator
        An instance of SedDataGenerator.
    
    Raises
    ------
    ValueError
        If _get_dict_variable(sedVariable) failed.
        If the id and value attributes of a parameter are not set.
        If the id and math attributes of a data generator are not set.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'dataGenerator1','name':'dataGenerator1','math':'varId or complex math infix ','listOfVariables':[dict_variable],'listOfParameters':[dict_parameter]}
        dict_parameter format: {'id':'param1','name':None,'value':float,'metaid':None}
        Only the attributes that are set will be returned.
    """

    if not dataGenerator.isSetId() or not dataGenerator.isSetMath():
        raise ValueError('The id and math attributes of a data generator are required.')
    dict_dataGenerator = {}
    dict_dataGenerator['id'] = dataGenerator.getId()
    if dataGenerator.isSetName():
        dict_dataGenerator['name'] = dataGenerator.getName()
    dict_dataGenerator['math'] = libsedml.formulaToL3String(dataGenerator.getMath())  
    if dataGenerator.getNumVariables()>0:
        dict_dataGenerator['listOfVariables'] = []
    for sedVariable in dataGenerator.getListOfVariables():
        try:
            dict_variable = _get_dict_variable(sedVariable)
        except ValueError as e:
            raise
        dict_dataGenerator['listOfVariables'].append(dict_variable)   
    if dataGenerator.getNumParameters()>0:
        dict_dataGenerator['listOfParameters'] = []
    for sedParameter in dataGenerator.getListOfParameters():
        if not sedParameter.isSetId() and not sedParameter.isSetValue():
            raise ValueError('The id and value attributes of a parameter are required.')
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

    Parameters
    ----------
    dataSet: SedDataSet
        An instance of SedDataSet.
    dict_dataSet: dict
        The dictionary format:
        {'id':'dataSet1','name':'optional,a human readable descriptor of a data set','label':'a unique label','dataReference':'must be the ID of a DataGenerator element'}
        The id, label and dataReference attributes of a data set are required.
        The label can be used as column headers if 2D output is exported as CSV files.
    
    Raises
    ------
    ValueError
        If the id, label and dataReference attributes of a data set are not set.
        If any operation returns an error.

    Side effects
    ------------
    dataSet: SedDataSet
        The data set is set.

    Returns
    -------
    bool
        Whether the data set is set successfully.  
    """
   
    if 'id' not in dict_dataSet or 'label' not in dict_dataSet or 'dataReference' not in dict_dataSet:
        raise ValueError('The id, label and dataReference attributes of a data set are required.')
    try:
        _operation_flag_check(dataSet.setId(dict_dataSet['id']), 'Set the id attribute of a data set')
        if 'name' in dict_dataSet:
            _operation_flag_check(dataSet.setName(dict_dataSet['name']), 'Set the name attribute of a data set')
        _operation_flag_check(dataSet.setLabel(dict_dataSet['label']), 'Set the label attribute of a data set')
        _operation_flag_check(dataSet.setDataReference(dict_dataSet['dataReference']), 'Set the dataReference attribute of a data set')
    except ValueError as e:
        raise

    return True

def _get_dict_dataSet(dataSet):
    """
    Get the information of a data set
    
    Parameters
    ----------
    dataSet: SedDataSet
        An instance of SedDataSet.

    Notes
    -----
    Assume the data set has been created successfully.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'dataSet1','name':'optional,a human readable descriptor of a data set','label':'a unique label','dataReference':'must be the ID of a DataGenerator element'}
        Only the attributes that are set will be returned.
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
   
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    dict_report: dict
        The dictionary format:
        {'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
        The id and listOfDataSets attributes of a report are required.
        The name attribute is optional.
    
    Raises
    ------
    ValueError
        If the id and listOfDataSets attributes of a report are not set.
        If any operation returns an error.

    Side effects
    ------------
    doc: SedDocument
        The report is set.

    Returns
    -------
    SedReport
        An instance of SedReport.
    """

    if 'id' not in dict_report or 'listOfDataSets' not in dict_report:
        raise ValueError('The id and listOfDataSets attributes of a report are required.')
    sedReport=doc.createReport()
    try:
        _operation_flag_check(sedReport.setId(dict_report['id']), 'Set the id attribute of a report')
        if 'name' in dict_report:
            _operation_flag_check(sedReport.setName(dict_report['name']), 'Set the name attribute of a report')
        for dict_dataSet in dict_report['listOfDataSets']:
            dataSet=sedReport.createDataSet()
            setDataSet(dataSet,dict_dataSet)
    except ValueError as e:
        raise
    return sedReport

def get_dict_report(sedReport):
    """
    Get the information of a report
    
    Parameters
    ----------
    sedReport: SedReport
        An instance of SedReport.

    Notes
    -----
    Assume the report has been created successfully.

    Returns
    -------
    dict
        The dictionary format:
        {'id':'report1','name':'report1','listOfDataSets':[dict_dataSet]}
        Only the attributes that are set will be returned.
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
    
    Parameters
    ----------
    dict_sedDocument: dict
        The dictionary format:
        {'listOfDataDescriptions':[dict_dataDescription],'listOfModels':[dict_model],'listOfSimulations':[dict_simulation],
        'listOfTasks':[dict_task],'listOfDataGenerators':[dict_dataGenerator],'listOfReports':[dict_report]}

    Returns
    -------
    SedDocument
        An instance of SedDocument.
        The version and level of the SED-ML document are set to 1 and 4, respectively.    
    """

    doc = libsedml.SedDocument(1,4)
    try:
        if 'listOfDataDescriptions' in dict_sedDocument:
            for dict_dataDescription in dict_sedDocument['listOfDataDescriptions']:
                create_dataDescription(doc,dict_dataDescription)
        if 'listOfModels' in dict_sedDocument:
            for dict_model in dict_sedDocument['listOfModels']:
                create_sedModel(doc,dict_model)
        if 'listOfSimulations' in dict_sedDocument:
            for dict_simulation in dict_sedDocument['listOfSimulations']:
                create_simulation(doc,dict_simulation)
        if 'listOfTasks' in dict_sedDocument:
            for dict_task in dict_sedDocument['listOfTasks']:
                create_abstractTask(doc,dict_task)
        if 'listOfDataGenerators' in dict_sedDocument:
            for dict_dataGenerator in dict_sedDocument['listOfDataGenerators']:
                create_dataGenerator(doc,dict_dataGenerator)
        if 'listOfReports' in dict_sedDocument:
            for dict_report in dict_sedDocument['listOfReports']:
                create_sedReport(doc,dict_report)
    except ValueError as e:
        print(e)
        return
    return doc
   
def get_dict_sedDocument(doc):
    """
    Get the information of a SED-ML document
    
    Parameters
    ----------
    doc: SedDocument
        An instance of SedDocument.
    
    Notes
    -----
    Assume the SED-ML document has been created successfully.

    Returns
    -------
    dict
        The dictionary format:
        {'listOfDataDescriptions':[dict_dataDescription],'listOfModels':[dict_model],'listOfSimulations':[dict_simulation],
        'listOfTasks':[dict_task],'listOfDataGenerators':[dict_dataGenerator],'listOfReports':[dict_report]}
        Only the attributes that are set will be returned.
    """
    dict_sedDocument = {}

    try:
        dict_sedDocument['listOfDataDescriptions'] = []
        for dataDescription in doc.getListOfDataDescriptions():
            dict_sedDocument['listOfDataDescriptions'].append(get_dict_dataDescription(dataDescription))
        dict_sedDocument['listOfModels'] = []
        for sedModel in doc.getListOfModels():
            dict_sedDocument['listOfModels'].append(get_dict_model(sedModel))
        dict_sedDocument['listOfSimulations'] = []
        for sedSimulation in doc.getListOfSimulations():
            dict_sedDocument['listOfSimulations'].append(get_dict_simulation(sedSimulation))
        dict_sedDocument['listOfTasks'] = []
        for task in doc.getListOfTasks():
            dict_sedDocument['listOfTasks'].append(get_dict_abstractTask(task))
        dict_sedDocument['listOfDataGenerators'] = []
        for dataGenerator in doc.getListOfDataGenerators():
            dict_sedDocument['listOfDataGenerators'].append(get_dict_dataGenerator(dataGenerator))
        dict_sedDocument['listOfReports'] = []
        for output in doc.getListOfOutputs():
            if output.isSedReport():
                dict_sedDocument['listOfReports'].append(get_dict_report(output))
    except ValueError as e:
        print(e)
        return
    return dict_sedDocument

# Test
if __name__ == '__main__':

    save_sedml_type_codes()
    
    
    
    