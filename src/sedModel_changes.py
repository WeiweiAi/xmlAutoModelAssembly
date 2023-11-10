import requests
import tempfile
import os
import re
from lxml import etree
import enum
from .math4sedml import calc_compute_model_change_new_value


CELLML2NAMESPACE ={"cellml":"http://www.cellml.org/cellml/2.0#"}
BIOMODELS_DOWNLOAD_ENDPOINT = 'https://www.ebi.ac.uk/biomodels/model/download/{}?filename={}_url.xml'


class ModelLanguagePattern(str, enum.Enum):
    """ Model language """
    CellML = r'^urn:sedml:language:cellml(\.\d+_\d+)?$'
    SBML = r'^urn:sedml:language:sbml(\.level\-\d+\.version\-\d+)?$'

def is_model_language_encoded_in_xml(language):
    """ Determine if the model language is encoded in XML. Note: only CellML and SBML are supported.

    Args:
        language (:obj:`str`): language

    Returns:
        :obj:`bool`: :obj:`True`, if the model language is encoded in XML
    """
    return (
        language and (
            re.match(ModelLanguagePattern.CellML, language)
            or re.match(ModelLanguagePattern.SBML, language)
        )
    )

def get_namespaces_with_prefixes(namespaces):
    """ Get a dictionary of namespaces less namespaces that have no prefix

    Args:
        namespaces (:obj:`dict`): dictionary that maps prefixes of namespaces their URIs

    Returns:
        :obj:`dict`: dictionary that maps prefixes of namespaces their URIs
    """
    if None in namespaces:
        namespaces = dict(namespaces)
        namespaces.pop(None)
    return namespaces

def eval_xpath(element, xpath, namespaces):
    """ Get the object(s) at an XPath

    Args:
        element (:obj:`etree._ElementTree`): element tree
        xpath (:obj:`str`): XPath
        namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs

    Returns:
        :obj:`list` of :obj:`etree._ElementTree`: object(s) at the XPath
    """
    try:
        return element.xpath(xpath, namespaces=get_namespaces_with_prefixes(namespaces))
    except etree.XPathEvalError as exception:
        if namespaces:
            msg = 'XPath `{}` is invalid with these namespaces:\n  {}\n\n  {}'.format(
                xpath,
                '\n  '.join(' - {}: {}'.format(prefix, uri) for prefix, uri in namespaces.items()),
                exception.args[0].replace('\n', '\n  ')),
        else:
            msg = 'XPath `{}` is invalid without namespaces:\n\n  {}'.format(
                xpath, exception.args[0].replace('\n', '\n  ')),

        exception.args = (msg)
        raise

def get_value_of_variable_model_xml_targets(variable, model_etrees):

    """ Get the value of a variable of a model

    Args:
        variable (:obj:`Variable`): variable
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): dictionary that maps the
            ids of models to paths to files which contain their XML definitions

    Returns:
        :obj:`float`: value
    Note: only support explicit model elements and concept references
    """
    if variable.unsetTarget (): # 
        raise NotImplementedError('Compute model change variable `{}` must have a target'.format(variable.getId()))

    if variable.getTarget ().startswith('#'):
        raise NotImplementedError('Variable references to data descriptions are not supported.')

    obj_xpath, sep, attr = variable.getTarget ().rpartition('/@')
    if sep != '/@':
        raise NotImplementedError('the value of target ' + variable.getTarget() +
                                  ' cannot be obtained by examining the XML, as the target is not an attribute of a model element')

    et = model_etrees[variable.getModelReference()]
    obj = eval_xpath(et, obj_xpath, CELLML2NAMESPACE)
    if len(obj) != 1:
        raise ValueError('xpath {} must match a single object in model {}'.format(obj_xpath, variable.getModelReference()))

    ns, _, attr = attr.rpartition(':')
    if ns:
        attr = '{{{}}}{}'.format(CELLML2NAMESPACE[ns], attr)

    value = obj[0].get(attr)
    if value is None:
        raise ValueError('Target `{}` is not defined in model `{}`.'.format(variable.getTarget (), variable.getModelReference()))
    try:
        value = float(value)
    except ValueError:
        raise ValueError('Target `{}` in model `{}` must be a float.'.format(variable.getTarget (), variable.getModelReference()))

    return value

def get_variable_info_CellML(task_variables,model_etree):
    """ Get information about the variables of a task
    Args:
        task_variables (:obj:`list` of :obj:`SedVariable`): variables of a task
        model_etree (:obj:`etree._Element`): model encoded in XML
    Returns:
        :obj:`dict`: information about the variables in the format {variable.id: {'name': variable name, 'component': component name}}
    """
    variable_info={}
    for v in task_variables:
        if v.getTarget().rpartition('/@')[-1]=='initial_value': # target initial value instead of variable
            vtemp=v.getTarget().rpartition('/@')
            variable_element = model_etree.xpath(vtemp[0],namespaces=CELLML2NAMESPACE)[0]
        else:
            variable_element = model_etree.xpath(v.getTarget (),namespaces=CELLML2NAMESPACE)[0]
        if variable_element is False:
            raise ValueError('The variable {} is not found!'.format(v.getTarget ()))
        else:
            variable_info[v.getId()] = {
                'name': variable_element.attrib['name'],
                'component': variable_element.getparent().attrib['name']
            }
    return variable_info

def resolve_model(model, sed_doc, working_dir):
    """ Resolve the source of a model

    Side effects:
        * Modifies the source of the model, 
          if the model needed to be resolved from a remote source

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`str` or None: temporary path to the source of the modified model, if the model needed to be resolved from
            a remote source.
            None, if the model did not need to be resolved from a remote source.

    """
    source = model.getSource () 

    if source.lower().startswith('urn:'):
        if source.lower().startswith('urn:miriam:biomodels.db:'):
            biomodels_id = source.lower().replace('urn:miriam:biomodels.db:', '')
            url = BIOMODELS_DOWNLOAD_ENDPOINT.format(biomodels_id, biomodels_id)
            response = requests.get(url)
            try:
                response.raise_for_status()
            except Exception:
                raise ValueError('Model `{}` could not be downloaded from BioModels.'.format(biomodels_id))

            temp_file, temp_model_source = tempfile.mkstemp()
            model.setSource(temp_model_source)
            os.close(temp_file)
            with open(temp_model_source, 'wb') as file:
                file.write(response.content)
        else:
            raise NotImplementedError('URN model source `{}` could be resolved.'.format(source))

        return model.getSource ()

    elif re.match(r'^http(s)?://', source, re.IGNORECASE):
        response = requests.get(source)
        try:
            response.raise_for_status()
        except Exception:
            raise ValueError('Model could not be downloaded from `{}`.'.format(source))

        temp_file, temp_model_source = tempfile.mkstemp()
        model.setSource(temp_model_source)
        os.close(temp_file)
        with open(temp_model_source, 'wb') as file:
            file.write(response.content)

        return model.getSource ()

    elif source.startswith('#'):
        other_model_id = source[1:]
        models=[sed_doc.getModel(i) for i in range(sed_doc.getNumModels())]
        other_model = next((m for m in models if m.getId() == other_model_id), None)
        if other_model is None:
            raise ValueError('Relative model source `{}` does not exist.'.format(source))
        
        model.setSource(other_model.getSource())
        for change in other_model.getListOfChanges ():
            model.addChange(change)

        return resolve_model(model, sed_doc, working_dir)

    else:
        if os.path.isabs(source):
            model.setSource(source)
        else:
            model.setSource(os.path.join(working_dir, source)) 

        if not os.path.isfile(model.getSource()):
            raise FileNotFoundError('Model source file `{}` does not exist.'.format(source))

        return None
    
def resolve_model_and_apply_xml_changes(orig_model, sed_doc, working_dir,
                                        apply_xml_model_changes=True, save_to_file=True,
                                        ):
    """ Resolve the source of a model and, optionally, apply XML changes to the model.

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        save_to_file (:obj:`bool`): whether to save the resolved/modified model to a file       

    Returns:
        :obj:`tuple`:

            * :obj:`Model`: modified model (changes are removed, and the source is set to the path to the modified temporary model)
            * :obj:`str`: temporary path to the source of the modified model, if the model needed to be resolved from
              a remote source of modified
            * :obj:`etree._Element`: element tree for the resolved/modified model
    """
    model = orig_model.clone()

    # resolve model
    temp_model_source = resolve_model(model, sed_doc, working_dir)

    # apply changes to model
    if apply_xml_model_changes and model.isSetLanguage() and is_model_language_encoded_in_xml(model.getLanguage ()):
        # read model from file
        try:
            model_etree = etree.parse(model.getSource())
        except Exception as exception:
            raise ValueError('The model could not be parsed because the model is not a valid XML document: {}'.format(str(exception)))

        if model.getListOfChanges () :
            # apply changes
            apply_changes_to_xml_model(model, model_etree, sed_doc, working_dir)
            model.getListOfChanges ().clear()

            # write model to file
            if save_to_file:
                if temp_model_source is None:
                    modified_model_file, temp_model_source = tempfile.mkstemp(suffix='.xml', dir=os.path.dirname(model.getSource()))
                    os.close(modified_model_file)
                    model.setSource(temp_model_source)

                model_etree.write(model.getSource(),
                                  xml_declaration=True,
                                  encoding="utf-8",
                                  standalone=False,
                                  )
    else:
        model_etree = None

    return model, model.getSource(), model_etree

def apply_changes_to_xml_model(model, model_etree,sed_doc=None, working_dir=None,
                               variable_values=None, range_values=None, validate_unique_xml_targets=True):
    """ Modify an XML-encoded model according to a model change

    Side effects:
        * Modifies the model_etree

    Args:
        model (:obj:`Model`): model
        model_etree (:obj:`etree._ElementTree`): element tree for model
        sed_doc (:obj:`SedDocument`, optional): parent SED document; used to resolve sources defined by reference to other models;
            required for compute changes
        working_dir (:obj:`str`, optional): working directory of the SED document (path relative to which models are located);
            required for compute changes
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change
        range_values (:obj:`dict`, optional): dictionary which contains the value of each range of each
            set value compute model change
        validate_unique_xml_targets (:obj:`bool`, optional): whether to validate the XML targets match
            uniue objects

    """

    # First pass:  Must-be-XML changes:
    non_xml_changes = []
    for change in model.getListOfChanges ():
        if change.isSedChangeAttribute():
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                # change.setModelReference(model.getId())
                non_xml_changes.append(change)
                continue
            # get object to change
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                raise NotImplementedError('target ' + change.getTarget () + ' cannot be changed by XML manipulation, as the target '
                                          'is not an attribute of a model element')
            objs = eval_xpath(model_etree, obj_xpath, CELLML2NAMESPACE)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            ns_prefix, _, attr = attr.rpartition(':')
            if ns_prefix:
                ns = CELLML2NAMESPACE.get(ns_prefix, None)
                if ns is None:
                    raise ValueError('No namespace is defined with prefix `{}`'.format(ns_prefix))
                attr = '{{{}}}{}'.format(ns, attr)

            # change value
            for obj in objs:
                obj.set(attr, change.getNewValue () )

        elif change.isSedComputeChange ():
            if variable_values is None:
                model_etrees = {model.getId(): model_etree}
                iter_variable_values = get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir)
            else:
                iter_variable_values = variable_values

            # calculate new value
            new_value = calc_compute_model_change_new_value(change, variable_values=iter_variable_values, range_values=range_values)
            if new_value == int(new_value):
                new_value = str(int(new_value))
            else:
                new_value = str(new_value)

            # get object to change
            obj_xpath, sep, attr = change.getTarget ().rpartition('/@')
            if sep != '/@':
                # Save this for the next pass:
                # change.setModelReference(model.getId())
                change.setNewValue (new_value)
                non_xml_changes.append(change)
                continue
            objs = eval_xpath(model_etree, obj_xpath, CELLML2NAMESPACE)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            ns_prefix, _, attr = attr.rpartition(':')
            if ns_prefix:
                ns = CELLML2NAMESPACE.get(ns_prefix, None)
                if ns is None:
                    raise ValueError('No namespace is defined with prefix `{}`'.format(ns_prefix))
                attr = '{{{}}}{}'.format(ns, attr)

            # change value
            for obj in objs:
                obj.set(attr, new_value)
        else:
            raise NotImplementedError('Change{} of type {} is not supported.'.format(
                ' ' + change.getId() if change.getId() else '', change.getTypeCode ()))

    return None

def get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir):
    """ Get the values of the model variables of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): compute model change
        sed_doc (:obj:`SedDocument`): SED document
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): map from the ids of models to element
            trees of their sources
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`dict`: dictionary which contains the value of each variable of each
            compute model change
    """
    variable_values = {}
    for variable in change.getListOfVariables():
        variable_model = variable.model
        if variable_model.getId() not in model_etrees:
            copy_variable_model, temp_model_source, variable_model_etree= resolve_model_and_apply_xml_changes(
                variable_model, sed_doc, working_dir,
                apply_xml_model_changes=True,
                save_to_file=False)
            model_etrees[variable_model.getId()] = variable_model_etree

            if temp_model_source:
                os.remove(temp_model_source)

        variable_values[variable.getId()] = get_value_of_variable_model_xml_targets(variable, model_etrees)

    return variable_values
