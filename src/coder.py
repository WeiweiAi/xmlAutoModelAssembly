from libcellml import Generator, GeneratorProfile, Printer
"""
=================
Code generation
=================
This module contains functions for generating code from a CellML model.

The following functions are defined:
    * writeCellML: write a CellML model to a CellML file.
    * writePythonCode: generate python file from a CellML model.
"""

def writeCellML(model, full_path):  
    """ 
    Write a CellML model to a CellML file.

    Parameters
    ----------
    model: Model
        The CellML model to be written.
    full_path: str
        The full path of the CellML file (including the file name and extension).

    Side effect
    -----------
    The CellML model is written to the specified file.
    """
    
    printer = Printer()
    serialised_model = printer.printModel(model) 
    with open(full_path, "w") as f:
        f.write(serialised_model)   

    print('CellML model saved to:',full_path)

def writePythonCode(analyser, full_path):
    """ 
    Generate Python code from a CellML model
    and write the code to the specified file.

    Parameters
    ----------
    analyser: Analyser
        The Analyser instance of the CellML model.
    full_path: str
        The full path of the python file (including the file name and extension).

    Side effect
    -----------
    The python code is written to the specified file.
    """

    generator = Generator()
    generator.setModel(analyser.model())
    profile = GeneratorProfile(GeneratorProfile.Profile.PYTHON)
    generator.setProfile(profile)
    implementation_code_python = generator.implementationCode()                   
    with open(full_path, "w") as f:
        f.write(implementation_code_python)