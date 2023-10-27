from libcellml import Generator, GeneratorProfile, Printer

def writeCellML(model, full_path):  
    """ 
    Write a CellML model to a CellML file.
    Args:
        model (:obj:`Model`): the CellML model to be written
        full_path (:obj:`str`): the full path of the CellML file (including the file name and extension)
    """  
    printer = Printer()
    serialised_model = printer.printModel(model)    
    write_file = open(full_path, "w")
    write_file.write(serialised_model)
    write_file.close()
    print('CellML model saved to:',full_path)

def writePythonCode(analyser, full_path):
    """ 
    Write a CellML model to a python file.
    Args:
        full_path (:obj:`str`): the full path of the python file (including the file name and extension)
        analyser (:obj:`Analyser`): the Analyser instance of the CellML model
    """
    generator = Generator()
    generator.setModel(analyser.model())
    profile = GeneratorProfile(GeneratorProfile.Profile.PYTHON)
    generator.setProfile(profile)
    implementation_code_python = generator.implementationCode()                   
    with open(full_path, "w") as f:
        f.write(implementation_code_python)