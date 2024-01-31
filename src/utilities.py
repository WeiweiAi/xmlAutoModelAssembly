def findCellComp(icomponent, compName, searchEncapsulated=True):
    """ Search for a component by name in a libcellml component or model
    
    Parameters
    ----------
    icomponent: CellML Component (or Model) instance in libcellml
        The component to search in
    compName: string
        The name of the component to search for
    searchEncapsulated: bool
        If True, search in encapsulated components as well

    Returns
    -------
    icomp: CellML Component (or Model) instance in libcellml
        The component found or None if not found
    """
    if icomponent.componentCount()>0:
        icomp=icomponent.component(compName,False)
        if icomp:
            return icomp
        elif searchEncapsulated:
            for i in range(icomponent.componentCount()):
                icomp=findCellComp(icomponent.component(i),compName,searchEncapsulated)
        else:
            return None
    else:
        return None 

def findCellVar(icomponent, varName):
    """ Search for a variable by name in a libcellml component or model
    
    Parameters
    ----------
    icomponent: CellML Component (or Model) instance in libcellml
        The component to search in
    varName: string
        The name of the variable to search for

    Returns
    -------
    ivar: CellML Variable instance in libcellml
        The variable found or None if not found
    """
    return icomponent.variable(varName)     