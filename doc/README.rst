=======================================
About The Project
=======================================

This project includes Python libraries for the following:

- Using libcellml_ to create, manipulate and serialise CellML_ models.
- Using libsedml_ to create, manipulate and serialise SED-ML_ files.
- Simulating CellML models
- Running SED-ML files to simulate CellML models
- Running SED-ML files to perform parameter estimation on CellML models

.. _libcellml: https://libcellml.org/
.. _libsedml: https://github.com/fbergmann/libSEDML
.. _CellML: https://cellml.org/
.. _SED-ML: https://sed-ml.org/

=======================================
Getting Started
=======================================

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

Prerequisites
-------------

- Python 3.7 or later

Installation
------------

1. Clone the repository:
    
    .. code-block:: bash

        git clone https://github.com/WeiweiAi/xmlAutoModelAssembly.git


2. Create a virtual environment for the project
   
3. Activate the virtual environment and install the required packages:

    .. code-block:: bash

        cd xmlAutoModelAssembly
        pip install -r requirements.txt    

=======================================
Usage
=======================================

Parameter estimation
---------------------
To perform parameter estimation on a CellML model, you need to provide a SED-ML file that specifies the parameter estimation task. If the CellML model is version 1.x, you also need to convert it to version 2.0 because libcellml_ only supports version 2.0. The `Boron_CO2_BG_V3_pe.py` in the folder `tests` demonstrates how to perform parameter estimation on a CellML model.

