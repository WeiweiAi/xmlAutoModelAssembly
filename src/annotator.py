from .utilities import findCellComp, findCellVar
from libcellml import cellmlElementTypeAsString
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, FOAF,  DCitemS, XSD

def getEntityID(model, componentName=None, varName=None):
    """ Get the entity ID of a variable or component in a model
    
    Parameters
    ----------
    model: libcellml Model instance
        The model to search in
    componentName: string
        The name of the component to search for
    varName: string
        The name of the variable to search for
    
    Raises
    ------
    ValueError
        If the component or variable is not found in the model
        
    Returns
    -------
    entityID: string
        The entity ID of the variable or component found (an empty string if ID has not been set)
    """
    if componentName:
        comp=findCellComp(model, componentName)
        if comp:
            if varName:
                var=findCellVar(comp, varName)
                if var:
                    return var.id()
                else:
                    raise ValueError('Variable not found in component: '+varName)
            return comp.id()
        else:
            raise ValueError('Component not found in model: '+componentName)
    else:
        return model.id()

def getElementByID(annotator, elementID):
    """ Get a CellML element by ID in a annotator
    
    Parameters
    ----------
    model: libcellml Annotator instance
        The annotator to search in
    elementID: string
        The ID of the element to search for
    
    Raises
    ------
    ValueError
        If the element is not found in the model
        or if the element type is not supported
        
    Returns
    -------
    tuple
        (string, CellML element)
        The type of the element and the element found
    """
    cellElement=annotator.item(elementID)
    if cellElement:
        if cellmlElementTypeAsString(cellElement.type())== 'MODEL':
            return 'MODEL', cellElement.model()
        elif cellmlElementTypeAsString(cellElement.type())== 'COMPONENT':
            return 'COMPONENT', cellElement.component()
        elif cellmlElementTypeAsString(cellElement.type())== 'VARIABLE':
            return 'VARIABLE', cellElement.variable()
        elif cellmlElementTypeAsString(cellElement.type())== 'RESET':
            return 'RESET', cellElement.reset()
        elif cellmlElementTypeAsString(cellElement.type())== 'IMPORT':
            return 'IMPORT', cellElement.importSource()
        elif cellmlElementTypeAsString(cellElement.type())== 'UNITS':
            return 'UNITS', cellElement.units()
        elif cellmlElementTypeAsString(cellElement.type())== 'UNIT':
            return 'UNIT', cellElement.unitsItem()
        elif cellmlElementTypeAsString(cellElement.type())== 'CONNECTION' or cellmlElementTypeAsString(cellElement.type())== 'MAP_VARIABLES':
            return 'CONNECTION', cellElement.variablePair()
        else:
            raise ValueError('Element type not supported: '+cellmlElementTypeAsString(cellElement.type()))
    else:
        raise ValueError('Element not found in annotator: '+elementID)


class Bio_RDF(Graph):
    """ A class to store RDF triples for a Biological models

    Defines the namespaces (https://doi.org/10.1515/jib-2021-0020) 
    and the RDF graph object.

    Attributes
    ----------
    ORCID: Namespace
        The ORCID namespace
    BQMODEL: Namespace
        The BioModels model qualifiers namespace
    BQBIOL: Namespace
        The BioModels biology qualifiers namespace
    PUBMED: Namespace
        The PubMed namespace
    NCBI_TAXONOMY: Namespace
        The NCBI Taxonomy namespace
    BIOMOD: Namespace
        The BioModels database namespace
    CHEBI: Namespace
        The ChEBI namespace
    UNIPROT: Namespace
        The UniProt namespace
    OPB: Namespace
        The Ontology of Physics for Biology namespace
    FMA: Namespace
        The Foundational Model of Anatomy namespace
    GO: Namespace
        The Gene Ontology namespace, https://geneontology.org/docs/ontology-documentation/
    SEMSIM: Namespace
        The SemSim namespace
    prefix_NAMESPACE_: dict
        The dictionary of namespace bindings

    Inherits
    --------
    rdflib.Graph

    Initialization
    --------------
    Bio_RDF(LOCAL, MODEL_BASE)

    Parameters
    ----------
    LOCAL: string
        The local namespace is the namespace of the RDF file
        e.g., Namespace('./'+file_withoutSuffix + '.ttl#') 
    MODEL_BASE: string
        The model base namespace,
        e.g., Namespace('./'+file_withoutSuffix + '.cellml#')
    
    Returns 
    -------
    Bio_RDF
        The Bio_RDF instance

    """
    ORCID = Namespace('http://orcid.org/')   
    BQMODEL = Namespace('http://biomodels.net/model-qualifiers/')
    BQBIOL = Namespace('http://biomodels.net/biology-qualifiers/')
    PUBMED = Namespace('http://identifiers.org/pubmed:')
    NCBI_TAXONOMY = Namespace('http://identifiers.org/taxonomy:')
    BIOMOD = Namespace('http://identifiers.org/biomodels.db:')
    CHEBI = Namespace('http://identifiers.org/CHEBI:')
    UNIPROT = Namespace('http://identifiers.org/uniprot:')
    OPB = Namespace('http://identifiers.org/opb:')
    FMA = Namespace('http://identifiers.org/FMA:')
    GO = Namespace('http://identifiers.org/GO:')
    SEMSIM = Namespace('http://bime.uw.edu/semsim/')
    prefix_NAMESPACE_ = {'rdf':RDF,'foaf':FOAF,'dcitems':DCitemS, 'orcid':ORCID, 'bqmodel':BQMODEL,'bqbiol':BQBIOL, 'pubmed':PUBMED,'NCBI_Taxon':NCBI_TAXONOMY,
                        'biomod':BIOMOD, 'chebi':CHEBI,'uniprot':UNIPROT,'opb':OPB,'fma':FMA,'go':GO, 'semsim':SEMSIM}
    
    # The ontology items that could be used in the FAIR DOs project
    OPB_items={'OPB_00340':'Concentration of chemical', 'OPB_00425':'Molar amount of chemical', 'OPB_00411':'Charge amount',
                'OPB_00592':'Chemical amount flow rate', 'OPB_00593':'Chemical amount density flow_rate',
                'OPB_00318':'Charge flow rate (current)', 'OPB_00299':'Fluid flow rate',  'OPB_00563':'Energy flow rate (power)',
                'OPB_00378':'Chemical potential', 'OPB_01058':'Membrane potential', 'OPB_00506':'Electrical potential (voltage)',
                'OPB_01238':'Charge areal density', 'OPB_01338':'Transducer modulus', 'OPB_00099':'Transformer modulus',
                'OPB_01296':'Reaction rate constant', 'OPB_00151':'Electrical resistance', 'OPB_00446':'Electrical capacitance',
                'OPB_01625':'Boltzmann constant', 'OPB_00293':'Temperature'
                }
    
    GO_items={'0005623':'Cell', '0005634':'Nucleus', '0005886':'Plasma membrane', '0005737':'Cytoplasm', '0005615':'Extracellular space',
    }
    CHEBI_items={'29101':'Sodium ion', '29103':'Potassium ion', '29108':'Calcium ion', '15378':'Hydrogen ion', '29985':'L-glutamate','4167': 'D-glucose',
                 '17996': 'chloride','17544':'hydrogencarbonate',}
    UNIPROT_items={'P43005':'SLC1A1, Excitatory amino acid transporter 3', 'P43004':'SLC1A2, Excitatory amino acid transporter 2',    
              }
           
    def __init__(self, LOCAL, MODEL_BASE):
        # output: a RDF graph object 
        super().__init__()
        self.prefix_NAMESPACE = Bio_RDF.prefix_NAMESPACE_|{'local':LOCAL,'model_base':MODEL_BASE}
        # Defined Namespace bindings.
        for prefix, namespace in self.prefix_NAMESPACE.items():
            self.bind(prefix, namespace)
        self.isVersionOf = self.prefix_NAMESPACE['bqbiol']['isVersionOf']
        self.isPropertyOf = self.prefix_NAMESPACE['bqbiol']['isPropertyOf']
        self.isPartOf = self.prefix_NAMESPACE['bqbiol']['isPartOf']
        self.hasMediatorParticipant=self.prefix_NAMESPACE['semsim']['hasMediatorParticipant']
        self.hasSourceParticipant=self.prefix_NAMESPACE['semsim']['hasSourceParticipant']
        self.hasSinkParticipant=self.prefix_NAMESPACE['semsim']['hasSinkParticipant']
        self.hasMultiplier=self.prefix_NAMESPACE['semsim']['hasMultiplier']

    
    def localNode(self, localitem):
        """ Get the local node of a RDF triple

        Parameters
        ----------
        localitem: string
            The local item of a RDF triple

        Returns
        -------
        URIRef
            The local source of a RDF triple
        """
        return self.prefix_NAMESPACE['local'][localitem]
    
    def modelBaseNode(self, model, componentName=None, varName=None):
        """ Get the model base node of a RDF triple

        Parameters
        ----------
        modelBaseitem: string
            The model base item of a RDF triple

        Returns
        -------
        URIRef
            The model base source of a RDF triple
        """
        try:
            modelBaseitem = getEntityID(model, componentName, varName)
            if modelBaseitem != '':
                return self.prefix_NAMESPACE['model_base'][modelBaseitem]
            else:
                raise ValueError('The model base item is empty')
        except ValueError:
            raise
    
    def literalNode(self, literalitem, literalType=float):
        """ Get the literal node of a RDF triple

        Parameters
        ----------
        literalitem: string
            The literal item of a RDF triple
        literalType: type
            The type of the literal item

        Returns
        -------
        Literal
            The literal source of a RDF triple
        """
        return Literal(literalitem, datatype=XSD[literalType])
    
    def ontologyNode(self, namespace_prefix, item):
        """ Get the ontology node of a RDF triple

        Parameters
        ----------
        namespace_prefix: string
            The prefix of an ontology namespace or the local namespace
        item: string
            The ontology item or the local item

        Raises
        ------
        ValueError
            If the namespace prefix is not found in the Bio_RDF instance
        
        Returns
        -------
        URIRef
            The ontology source of a RDF triple
        """
        if namespace_prefix in self.prefix_NAMESPACE:
            return self.prefix_NAMESPACE[namespace_prefix][item]
        else:
            raise ValueError('Namespace prefix not found: '+namespace_prefix)  


def annotate_bioProc(model, bio_rdf, dict_bioProcess):
    """ Annotate a model with biological information
    
    Parameters
    ----------
    model: libcellml Model instance
        The model to be annotated
    bio_rdf: Bio_RDF instance
        The Bio_RDF instance to store the RDF triples
    dict_bioProcess: dict
        The dictionary of biological process information
        in the format of {id:{'mediators':[dict_bioEntity1,...],'sources':[dict_bioEntity1,...],'sinks':[dict_bioEntity1,...],'properties':[dict_property1, ...]}}
        bioEntity is the local entity of a biological entity, could be a protein, a chemical species, charge, etc.
        The dictionary of biological entity information is in the format of
        {'stoichiometry':1, 'chemical items':[('uniprot','P11166')],'anatomy items': [('go','0005886')],'properties':[dict_property1, ...]}
        stoichiometry is the stoichiometry of the biological entity in the process
        chemical items are used to specify the chemical species of the biological entity
        anatomy items are used to specify the location of the biological entity
        properties are used to specify the properties of the biological entity
        The dictionary of property information is in the format of
        dict_property={'component':'name of the component', 'variable':'name of the variable', 'physics property':('namespace_prefix','term')}              

    """
    
    def _annotate_property(model, bio_rdf, dict_property, local_node):
        """ Annotate a model with a property
        
        Parameters
        ----------
        model: libcellml Model instance
            The model to be annotated
        bio_rdf: Bio_RDF instance
            The Bio_RDF instance to store the RDF triples
        dict_property: dict
            The dictionary of property information
            in the format of {'component':'name of the component', 'variable':'name of the variable', 'physics property':('namespace_prefix','term')}
        local_node: URIRef
            The local node of the property

        """
        model_subj=bio_rdf.modelBaseNode(model, dict_property['component'], dict_property['variable'])
        physics_obj=bio_rdf.ontologyNode(dict_property['physics property'][0], dict_property['physics property'][1])
        bio_rdf.add((model_subj, bio_rdf.isVersionOf, physics_obj))
        bio_rdf.add((model_subj, bio_rdf.isPropertyOf, local_node))

    def _annotate_bioEntity(model, bio_rdf, dict_bioEntity, local_node):
        """ Annotate a model with biological entity information
        
        Parameters
        ----------
        model: libcellml Model instance
            The model to be annotated
        bio_rdf: Bio_RDF instance
            The Bio_RDF instance to store the RDF triples
        dict_bioEntity: dict
            The dictionary of biological entity information
            in the format of {'stoichiometry':1, 'chemical items':[('uniprot','P11166')],'anatomy items': [('go','0005886')],'properties':[dict_property1, ...]}
            dict_property={'component':'name of the component', 'variable':'name of the variable', 'physics property':('namespace_prefix','item')}
        local_node: URIRef
            The local node of the biological entity

        """
        if 'stoichiometry' in dict_bioEntity:
            bio_rdf.add((local_node, bio_rdf.hasMultiplier, bio_rdf.literalNode(dict_bioEntity['stoichiometry'])))

        for item in dict_bioEntity['chemical items']:
            chemical_obj=bio_rdf.ontologyNode(item[0], item[1])
            bio_rdf.add((local_node, bio_rdf.isVersionOf, chemical_obj))
        for item in dict_bioEntity['anatomy items']:
            anatomy_obj=bio_rdf.ontologyNode(item[0], item[1])
            bio_rdf.add((local_node, bio_rdf.isPartOf, anatomy_obj))
        for dict_property in dict_bioEntity['properties']:
            _annotate_property(model, bio_rdf, dict_property, local_node)

    for id, bioProcess in dict_bioProcess.items():
        local_process=bio_rdf.localNode('process_'+id)
        for j in range(len(bioProcess['mediators'])):
            local_mediator=bio_rdf.localNode('mediator_'+ id + '_' + str(j))            
            bio_rdf.add((local_process, bio_rdf.hasMediatorParticipant, local_mediator))
            dict_bioEntity=bioProcess['mediators'][j]
            _annotate_bioEntity(model, bio_rdf, dict_bioEntity, local_mediator)
        for j in range(len(bioProcess['sources'])):
            local_source=bio_rdf.localNode('source_'+ id + '_' + str(j))            
            bio_rdf.add((local_process, bio_rdf.hasSourceParticipant, local_source))
            dict_bioEntity=bioProcess['sources'][j]
            _annotate_bioEntity(model, bio_rdf, dict_bioEntity, local_source)
        for j in range(len(bioProcess['sinks'])):
            local_sink=bio_rdf.localNode('sink_'+ id + '_' + str(j))            
            bio_rdf.add((local_process, bio_rdf.hasSinkParticipant, local_sink))
            dict_bioEntity=bioProcess['sinks'][j]
            _annotate_bioEntity(model, bio_rdf, dict_bioEntity, local_sink)

        for j in range(len(bioProcess['properties'])):
            dict_property=bioProcess['properties'][j]
            _annotate_property(model, bio_rdf, dict_property, local_process)

