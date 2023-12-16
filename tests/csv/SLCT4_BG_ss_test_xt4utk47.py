# The content of this file was generated using the Python profile of libCellML 0.5.0.

from enum import Enum
from math import *


__version__ = "0.4.0"
LIBCELLML_VERSION = "0.5.0"

VARIABLE_COUNT = 41


class VariableType(Enum):
    CONSTANT = 0
    COMPUTED_CONSTANT = 1
    ALGEBRAIC = 2
    EXTERNAL = 3


VARIABLE_INFO = [
    {"name": "v_ss", "units": "fmol_per_sec", "component": "SLCT4_ss", "type": VariableType.ALGEBRAIC},
    {"name": "q_Ao", "units": "fmol", "component": "SLCT4_BG_ss_io", "type": VariableType.CONSTANT},
    {"name": "q_Bi", "units": "fmol", "component": "SLCT4_BG_ss_io", "type": VariableType.CONSTANT},
    {"name": "q_Ai", "units": "fmol", "component": "SLCT4_BG_ss_io", "type": VariableType.CONSTANT},
    {"name": "q_Bo", "units": "fmol", "component": "SLCT4_BG_ss_io", "type": VariableType.CONSTANT},
    {"name": "E", "units": "fmol", "component": "SLCT4_BG_ss", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "P_0", "units": "per_fmol2_sec6", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_1", "units": "per_fmol2_sec6", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_2", "units": "per_fmol_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_9", "units": "per_fmol2_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_8", "units": "per_fmol2_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_7", "units": "per_fmol2_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_6", "units": "per_fmol2_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_5", "units": "per_fmol_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_4", "units": "per_fmol_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "P_3", "units": "per_fmol_sec5", "component": "SLCT4_BG_ss", "type": VariableType.ALGEBRAIC},
    {"name": "K_Ao", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.COMPUTED_CONSTANT},
    {"name": "K_Ai", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_Bo", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.ALGEBRAIC},
    {"name": "K_Bi", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.EXTERNAL},
    {"name": "K_5", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.EXTERNAL},
    {"name": "q_5_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_6", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "q_6_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_7", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "q_7_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_8", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "q_8_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_9", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "q_9_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "K_10", "units": "per_fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "q_10_init", "units": "fmol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "kappa_re1", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "kappa_re2", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "kappa_re3", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.EXTERNAL},
    {"name": "kappa_re4", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "kappa_re5", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "kappa_re6", "units": "fmol_per_sec", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "F", "units": "C_per_mol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "R", "units": "J_per_K_per_mol", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT},
    {"name": "T", "units": "kelvin", "component": "SLCT4_BG_param", "type": VariableType.CONSTANT}
]


def create_variables_array():
    return [nan]*VARIABLE_COUNT


def initialise_variables(variables, external_variable):
    variables[1] = 1.0
    variables[2] = 1.0
    variables[3] = 1.0
    variables[4] = 1.0
    variables[17] = 1.0
    variables[21] = 1.0
    variables[22] = 1.0
    variables[23] = 1.0
    variables[24] = 1.0
    variables[25] = 1.0
    variables[26] = 1.0
    variables[27] = 1.0
    variables[28] = 1.0
    variables[29] = 1.0
    variables[30] = 1.0
    variables[31] = 1.0
    variables[32] = 1.0
    variables[33] = 1.0
    variables[35] = 1.0
    variables[36] = 1.0
    variables[37] = 1.0
    variables[38] = 96485.0
    variables[39] = 8.31
    variables[40] = 293.0
    variables[19] = external_variable(variables, 19)
    variables[20] = external_variable(variables, 20)
    variables[34] = external_variable(variables, 34)


def compute_computed_constants(variables):
    variables[16] = variables[17]
    variables[5] = variables[31]+variables[21]+variables[23]+variables[25]+variables[27]+variables[29]


def compute_variables(variables, external_variable):
    variables[34] = external_variable(variables, 34)
    variables[19] = external_variable(variables, 19)
    variables[20] = external_variable(variables, 20)
    variables[6] = variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[16]*variables[19]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]
    variables[18] = variables[19]
    variables[7] = variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[17]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]
    variables[8] = variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[16]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[16]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]+variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[16]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]
    variables[9] = variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[17]*variables[16]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]
    variables[10] = variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[19]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[19]*variables[18]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[19]*variables[18]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[18]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[18]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]
    variables[11] = variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[16]*variables[19]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[16]*variables[19]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[16]*variables[19]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[16]*variables[19]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[16]*variables[19]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[16]*variables[19]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]
    variables[12] = variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[17]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[26]*variables[17]*variables[18]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[17]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[30]*variables[20]*variables[22]*variables[24]*variables[28]*variables[17]*variables[18]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[22]*variables[26]*variables[28]*variables[17]*variables[18]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]+variables[20]*variables[22]*variables[24]*variables[26]*variables[28]*variables[17]*variables[18]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]
    variables[13] = variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[19]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]
    variables[14] = variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[17]*variables[32]*variables[33]*variables[34]*variables[35]*variables[37]+variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[17]*variables[32]*variables[33]*variables[34]*variables[36]*variables[37]+variables[30]*variables[22]*variables[24]*variables[26]*variables[28]*variables[17]*variables[32]*variables[33]*variables[35]*variables[36]*variables[37]
    variables[15] = variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[18]*variables[32]*variables[33]*variables[34]*variables[35]*variables[36]+variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[18]*variables[32]*variables[34]*variables[35]*variables[36]*variables[37]+variables[30]*variables[20]*variables[24]*variables[26]*variables[28]*variables[18]*variables[33]*variables[34]*variables[35]*variables[36]*variables[37]
    variables[0] = variables[5]*(variables[6]*variables[1]*variables[2]-variables[7]*variables[3]*variables[4])/(variables[8]*variables[1]+variables[15]*variables[4]+variables[14]*variables[3]+variables[13]*variables[2]+variables[12]*variables[3]*variables[4]+variables[11]*variables[1]*variables[2]+variables[10]*variables[2]*variables[4]+variables[9]*variables[3]*variables[1])
