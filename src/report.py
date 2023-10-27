import os
import numpy
import pandas

def writeReport(report, results, base_path, rel_path, format='csv'):
    rel_path = os.path.relpath(rel_path, '.')
    results_array = []
    data_set_ids = []
    data_set_labels = []
    data_set_names = []
    data_set_data_types = []
    data_set_shapes = []
    for data_set in report.getListOfDataSets ():
        if data_set.getId() in results:
            data_set_result = results[data_set.getId()]
            results_array.append(data_set_result)
            data_set_ids.append(data_set.getId())
            data_set_labels.append(data_set.getLabel () )
            data_set_names.append(data_set.getName() or '')
            if data_set_result is None:
                data_set_data_types.append('__None__')
                data_set_shapes.append('')
            else:
                data_set_dtype = data_set_result.dtype
                if data_set_dtype in [numpy.dtype('object'), numpy.dtype('void'), numpy.dtype('S'), numpy.dtype('a')]:
                    msg = 'NumPy dtype should be a specific type such as `float64` or `int64` not `{}`.'.format(data_set_dtype.name)
                    raise TypeError(msg)
                data_set_data_types.append(data_set_dtype.name)
                data_set_shapes.append(','.join(str(dim_len) for dim_len in data_set_result.shape))
    results_array = pad_arrays_to_consistent_shapes(results_array)
    results_array = numpy.array(results_array)
    if format in ['csv','tsv','xlsx']:
        if results_array.ndim > 2:
            msg = 'Report has {} dimensions. Multidimensional reports cannot be exported to {}.'.format(
                results_array.ndim, format.upper())
            print(msg)
            return
        if len(set(data_set.getLabel () for data_set in report.getListOfDataSets ())) < len(report.getListOfDataSets ()):
            print('To facilitate machine interpretation, data sets should have unique labels.')
        msg = 'Reports exported to {} do not contain information about the data type or size of each data set.'.format(
            format.upper())
        print(msg)
        results_df = pandas.DataFrame(results_array, index=data_set_labels)
        if format in ['csv','tsv']:
            filename = os.path.join(base_path, rel_path + '.' + format)
            out_dir = os.path.dirname(filename)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            results_df.to_csv(filename, header=False, sep=',' if format == 'csv' else '\t')
        else:
            filename = os.path.join(base_path, os.path.dirname(rel_path) + '.' + format)
            out_dir = os.path.dirname(filename)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with pandas.ExcelWriter(filename, mode='a' if os.path.isfile(filename) else 'w', engine='openpyxl') as writer:
                results_df.to_excel(writer, sheet_name=os.path.basename(rel_path), header=False)
    else:
        raise NotImplementedError('Report format {} is not supported'.format(format))

def readReport(report, base_path, rel_path, format='csv'):
    rel_path = os.path.relpath(rel_path, '.')

    if format in ['csv','tsv','xlsx']:
        print('Reports exported to {} do not contain information about the data type or size of each data set.'.format(
            format.upper()))
        if format in ['csv','tsv']:
            filename = os.path.join(base_path, rel_path + '.' + format)
            df = pandas.read_csv(filename,
                                 index_col=0,
                                 header=None,
                                 sep=',' if format == 'csv' else '\t')
        else:
            filename = os.path.join(base_path, os.path.dirname(rel_path) + '.' + format)
            df = pandas.read_excel(filename,
                                   sheet_name=os.path.basename(rel_path),
                                   index_col=0,
                                   header=None,
                                   engine='openpyxl')
        df.columns = pandas.RangeIndex(start=0, stop=df.shape[1], step=1)
        results = {}
        data_set_labels = [data_set.getLabel () for data_set in report.getListOfDataSets ()]
        if df.index.tolist() == data_set_labels:
            data = df.to_numpy()
            for i_data_set, data_set in enumerate(report.getListOfDataSets ()):
                results[data_set.id] = data[i_data_set, :]
            extra_data_sets = set()
        else:
            data_set_label_to_index = {}
            for i_data_set, data_set_label in enumerate(df.index):
                if data_set_label not in data_set_label_to_index:
                    data_set_label_to_index[data_set_label] = i_data_set
                else:
                    data_set_label_to_index[data_set_label] = None
            unreadable_data_sets = []
            for data_set in report.getListOfDataSets ():
                i_data_set = data_set_label_to_index.get(data_set.getLabel (), None)
                if i_data_set is None:
                    # results[data_set.id] = None
                    unreadable_data_sets.append(data_set.getId())
                else:
                    results[data_set.id] = df.loc[data_set.getLabel (), :].to_numpy()
            if unreadable_data_sets:
                print('Some data sets could not be read because their labels are not unique:\n  - {}'.format(
                    '\n'.join('`' + id + '`' for id in sorted(unreadable_data_sets))))
            data_set_id_to_label = {data_set.id: data_set.getLabel () for data_set in report.getListOfDataSets ()}
            extra_data_sets = set(df.index) - set(data_set_id_to_label[id] for id in results.keys()) - set(unreadable_data_sets)
        file_data_set_ids = set(results.keys()) | extra_data_sets
    else:
        raise NotImplementedError('Report format {} is not supported'.format(format))
    report_data_set_ids = set(data_set.id for data_set in report.getListOfDataSets ())
    missing_data_set_ids = report_data_set_ids.difference(file_data_set_ids)
    extra_data_set_ids = file_data_set_ids.difference(report_data_set_ids)
    if missing_data_set_ids:
        print('File does not contain data for the following data sets of the report:\n  - {}'.format(
            '\n'.join('`' + id + '`' for id in sorted(missing_data_set_ids))))
    if extra_data_set_ids:
        print('File contains additional data that could not be mapped to data sets of the report:\n  - {}'.format(
            '\n'.join('`' + id + '`' for id in sorted(extra_data_set_ids))))
    return results

def pad_arrays_to_consistent_shapes(arrays):
    """ Pad a list of NumPy arrays to a consistent shape

    Args:
        arrays (:obj:`list` of :obj:`numpy.ndarray`): list of NumPy arrays

    Returns:
        :obj:`list` of :obj:`numpy.ndarray`: list of padded arrays
    """
    shapes = set()
    for array in arrays:
        if array is not None:
            shape = array.shape
            if not shape and array.size:
                shape = (1,)
            shapes.add(shape)

    if len(shapes) > 1:
        print('Arrays do not have consistent shapes', UserWarning)

    max_shape = []
    for shape in shapes:
        max_shape = max_shape + [1 if max_shape else 0] * (len(shape) - len(max_shape))
        shape = list(shape) + [1 if shape else 0] * (len(max_shape) - len(shape))
        max_shape = [max(x, y) for x, y in zip(max_shape, shape)]

    padded_arrays = []
    for array in arrays:
        if array is None:
            array = numpy.full(max_shape, numpy.nan)

        shape = tuple(list(array.shape)
                      + [1 if array.size else 0]
                      * (len(max_shape) - array.ndim))
        array = array.astype('float64').reshape(shape)

        pad_width = tuple((0, x - y) for x, y in zip(max_shape, shape))

        if pad_width:
            array = numpy.pad(array,
                              pad_width,
                              mode='constant',
                              constant_values=numpy.nan)

        padded_arrays.append(array)

    return padded_arrays
