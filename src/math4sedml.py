import evalidate
import math
import mpmath
import numpy
import numpy.random
import re
import libsedml
from sedModel_changes import get_value_of_variable_model_xml_targets


def log(*args):
    """ Evaluate a logarithm

    Args:
        *args (:obj:`list` of :obj:`float`): value optional proceeded by a base; otherwise the logarithm
            is calculated in base 10

    Returns:
        :obj:`float`
    """
    value = args[-1]
    if len(args) > 1:
        base = args[0]
    else:
        base = 10.

    return math.log(value, base)


def piecewise(*args):
    """ Evaluate a MathML piecewise function

    Args:
        *args (:obj:`list` of :obj:`float`): pairs of value and conditions followed by a default value

    Returns:
        :obj:`float`
    """
    if len(args) % 2 == 0:
        pieces = args
        otherwise = math.nan

    else:
        pieces = args[0:-1]
        otherwise = args[-1]

    for i_piece in range(0, len(pieces), 2):
        value = pieces[i_piece]
        condition = pieces[i_piece + 1]
        if condition:
            return value

    return otherwise


MATHEMATICAL_FUNCTIONS = {
    'root': lambda x, n: x**(1 / float(n)),
    'abs': abs,
    'exp': math.exp,
    'ln': math.log,
    'log': log,
    'floor': math.floor,
    'ceiling': math.ceil,
    'factorial': math.factorial,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sec': mpmath.sec,
    'csc': mpmath.csc,
    'cot': mpmath.cot,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'sech': mpmath.sech,
    'csch': mpmath.csch,
    'coth': mpmath.coth,
    'arcsin': math.asin,
    'arccos': math.acos,
    'arctan': math.atan,
    'arcsec': mpmath.asec,
    'arccsc': mpmath.acsc,
    'arccot': mpmath.acot,
    'arcsinh': math.asinh,
    'arccosh': math.acosh,
    'arctanh': math.atanh,
    'arcsech': mpmath.asech,
    'arccsch': mpmath.acsch,
    'arccoth': mpmath.acoth,
    'min': numpy.min,
    'max': numpy.max,
    'sum': numpy.sum,
    'product': numpy.product,
    'count': len,
    'mean': numpy.mean,
    'stdev': numpy.std,
    'variance': numpy.var,
    'uniform': numpy.random.uniform,
    'normal': numpy.random.normal,
    'lognormal': numpy.random.lognormal,
    'poisson': numpy.random.poisson,
    'gamma': numpy.random.gamma,
    'piecewise': piecewise,
}

RESERVED_MATHEMATICAL_SYMBOLS = {
    'true': True,
    'false': False,
    'notanumber': math.nan,
    'pi': math.pi,
    'infinity': math.inf,
    'exponentiale': math.e,
}

AGGREGATE_MATH_FUNCTIONS = (
    'min',
    'max',
    'sum',
    'product',
    'count',
    'mean',
    'stdev',
    'variance',
)


VALID_MATH_EXPRESSION_NODES = [
    'Eq',
    'NotEq',
    'Gt',
    'Lt',
    'GtE',
    'LtE',
    'Sub',
    'USub',
    'Mult',
    'Div',
    'Pow',
    'And',
    'Or',
    'Not',
    'BitAnd',
    'BitOr',
    'BitXor',
    'Call',
    'Constant',
]


def compile_math(math):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression

    Returns:
        :obj:`_ast.Expression`: compiled expression
    """
    if isinstance(math, str):
        math = (
            math
            .replace('&&', 'and')
            .replace('||', 'or')
            .replace('^', '**')
        )

    model = evalidate.base_eval_model.clone()
    model.nodes.extend(VALID_MATH_EXPRESSION_NODES)
    model.allowed_functions.extend(MATHEMATICAL_FUNCTIONS.keys())

    math_node = evalidate.Expr(math, model=model)
    compiled_math = compile(math_node.node, '<math>', 'eval')
    return compiled_math


def eval_math(math, compiled_math, workspace):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression
        compiled_math (:obj:`_ast.Expression`): compiled expression
        workspace (:obj:`dict`): values to use for the symbols in the expression

    Returns:
        :obj:`object`: result of the expression

    Raises:
        :obj:`ValueError`: if the expression could not be evaluated
    """
    invalid_symbols = set(RESERVED_MATHEMATICAL_SYMBOLS.keys()).intersection(set(workspace.keys()))
    if invalid_symbols:
        raise ValueError('Variables for mathematical expressions cannot have ids equal to the following reserved symbols:\n  - {}'.format(
            '\n  - '.join('`' + symbol + '`' for symbol in sorted(invalid_symbols))))

    try:
        return eval(compiled_math, MATHEMATICAL_FUNCTIONS, dict(**RESERVED_MATHEMATICAL_SYMBOLS, **workspace))
    except Exception as exception:
        raise ValueError('Expression `{}` could not be evaluated:\n\n  {}\n\n  workspace:\n    {}'.format(
            math, str(exception), '\n    '.join('{}: {}'.format(key, value) for key, value in workspace.items())))

def calc_compute_model_change_new_value(setValue, variable_values=None, range_values=None):
    """ Calculate the new value of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): change
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change
        range_values (:obj:`dict`, optional): dictionary which contains the value of each range of each
            set value compute model change

    Returns:
        :obj:`float`: new value
    """
    compiled_math = compile_math(libsedml.formulaToString(setValue.getMath()))

    workspace = {}

    if setValue.isSetRange ():
        workspace[setValue.getRange ()] = range_values.get(setValue.getRange (), None)
        if workspace[setValue.getRange ()] is None:
            raise ValueError('Value of range `{}` is not defined.'.format(setValue.getRange ()))

    for param in setValue.getListOfParameters ():
        workspace[param.getId()] = param.getValue()

    for var in setValue.getListOfVariables ():
        workspace[var.getId()] = variable_values.get(var.getId(), None)
        if workspace[var.getId()] is None:
            raise ValueError('Value of variable `{}` is not defined.'.format(var.getId()))

    return eval_math(libsedml.formulaToString(setValue.getMath()), compiled_math, workspace)

def calc_data_generator_results(data_generator, variable_results):
    """ Calculate the results of a data generator from the results of its variables

    Args:
        data_generator (:obj:`DataGenerator`): data generator
        variable_results (:obj:`VariableResults`): results for the variables of the data generator

    Returns:
        :obj:`numpy.ndarray`: result of data generator
    """
    var_shapes = set()
    max_shape = []
    for var in data_generator.getListOfVariables():
        var_res = variable_results[var.getId()]
        var_shape = var_res.shape
        if not var_shape and var_res.size:
            var_shape = (1,)
        var_shapes.add(var_shape)

        max_shape = max_shape + [1 if max_shape else 0] * (var_res.ndim - len(max_shape))
        for i_dim in range(var_res.ndim):
            max_shape[i_dim] = max(max_shape[i_dim], var_res.shape[i_dim])

    if len(var_shapes) > 1:
        print('Variables for data generator {} do not have consistent shapes'.format(data_generator.getId()),
             )

    compiled_math = compile_math(libsedml.formulaToString(data_generator.getMath()))

    workspace = {}
    for param in data_generator.getListOfParameters():
        workspace[param.getId()] = param.getValue()

    if not var_shapes:
        value = eval_math(libsedml.formulaToString(data_generator.getMath()), compiled_math, workspace)
        result = numpy.array(value)

    else:
        for aggregate_func in AGGREGATE_MATH_FUNCTIONS:
            if re.search(aggregate_func + r' *\(', libsedml.formulaToString(data_generator.getMath())):
                msg = 'Evaluation of aggregate mathematical functions such as `{}` is not supported.'.format(aggregate_func)
                raise NotImplementedError(msg)

        padded_var_shapes = []
        for var in data_generator.getListOfVariables():
            var_res = variable_results[var.getId()]
            padded_var_shapes.append(
                list(var_res.shape)
                + [1 if var_res.size else 0] * (len(max_shape) - var_res.ndim)
            )

        result = numpy.full(max_shape, numpy.nan)
        n_dims = result.ndim
        for i_el in range(result.size):
            el_indices = numpy.unravel_index(i_el, result.shape)

            vars_available = True
            for var, padded_shape in zip(data_generator.getListOfVariables(), padded_var_shapes):
                var_res = variable_results[var.getId()]
                if var_res.ndim == 0:
                    if i_el == 0 and var_res.size:
                        workspace[var.getId()] = var_res.tolist()
                    else:
                        vars_available = False
                        break

                else:
                    for x, y in zip(padded_shape, el_indices):
                        if (y + 1) > x:
                            vars_available = False
                            break
                    if not vars_available:
                        break

                    workspace[var.getId()] = var_res[el_indices[0:var_res.ndim]]

            if not vars_available:
                continue

            result_el = eval_math(libsedml.formulaToString(data_generator.getMath()), compiled_math, workspace)

            if n_dims == 0:
                result = numpy.array(result_el)
            else:
                result.flat[i_el] = result_el

    return result

def resolve_range(range, model_etrees=None):
    """ Resolve the values of a range

    Args:
        range (:obj:`Range`): range
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): map from the ids of models to element
            trees of their sources; required to resolve variables of functional ranges

    Returns:
        :obj:`list` of :obj:`float`: values of the range

    Raises:
        :obj:`NotImplementedError`: if range isn't an instance of :obj:`UniformRange`, :obj:`VectorRange`,
            or :obj:`FunctionalRange`.
    """
    if range.isSedUniformRange ():
        if range.getType() == 'linear':
            return numpy.linspace(range.getStart(), range.getEnd(), range.getNumberofSteps() + 1).tolist()

        elif range.getType() == 'log':
            return numpy.logspace(numpy.log10(range.getStart()), numpy.log10(range.getEnd()), range.getNumberofSteps() + 1).tolist()

        else:
            raise NotImplementedError('UniformRanges of type `{}` are not supported.'.format(range.getType()))

    elif range.isSedVectorRange ():
        return range.getValues()

    elif range.isSedFunctionalRange ():
        # compile math
        compiled_math = compile_math(libsedml.formulaToString(range.getMath()))

        # setup workspace to evaluate math
        workspace = {}
        for param in range.getListOfParameters ():
            workspace[param.getId()] = param.getValue()

        for var in range.getListOfVariables ():
            if var.isSetSymbol ():
                raise NotImplementedError('Symbols are not supported for variables of functional ranges')
            if model_etrees[var.getModelReference()] is None:
                raise NotImplementedError('Functional ranges that involve variables of non-XML-encoded models are not supported.')
            workspace[var.getId()] = get_value_of_variable_model_xml_targets(var, model_etrees)

        # calculate the values of the range
        values = []
        for child_range_value in resolve_range(range.getRange(), model_etrees=model_etrees):
            workspace[range.getRange().getId()] = child_range_value

            value = eval_math(libsedml.formulaToString(range.getMath()), compiled_math, workspace)
            values.append(value)

        # return values
        return values

    else:
        raise NotImplementedError('Ranges of type `{}` are not supported.'.format(range.getTypeCode()))
    
