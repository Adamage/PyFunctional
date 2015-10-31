# pylint: disable=redefined-builtin,too-many-arguments

import future.builtins as builtins
import re
import csv as csvapi
import json as jsonapi
import six

from .pipeline import Sequence
from .util import is_primitive, LazyFile


def seq(*args):
    """
    Primary entrypoint for the functional package. Returns a functional.pipeline.Sequence wrapping
    the original sequence.

    Additionally it parses various types of input to a Sequence as best it can.

    >>> type(seq([1, 2]))
    functional.pipeline.Sequence

    >>> type(Sequence([1, 2]))
    functional.pipeline.Sequence

    >>> seq([1, 2, 3])
    [1, 2, 3]

    >>> seq(1, 2, 3)
    [1, 2, 3]

    >>> seq(1)
    [1]

    >>> seq(range(4))
    [0, 1, 2, 3]

    :param args: Three types of arguments are valid.
        1) Iterable which is then directly wrapped as a Sequence
        2) A list of arguments is converted to a Sequence
        3) A single non-iterable is converted to a single element Sequence
    :return: wrapped sequence

    """
    if len(args) == 0:
        raise TypeError("seq() takes at least 1 argument ({0} given)".format(len(args)))
    elif len(args) > 1:
        return Sequence(list(args))
    elif is_primitive(args[0]):
        return Sequence([args[0]])
    else:
        return Sequence(args[0])


def open(path, delimiter=None, mode='r', buffering=-1, encoding=None,
         errors=None, newline=None):
    """
    Additional entry point to Sequence which parses input files as defined by options. Path
    specifies what file to parse. If delimiter is not None, then the file is read in bulk then
    split on it. If it is None (the default), then the file is parsed as sequence of lines. The
    rest of the options are passed directly to builtins.open with the exception that write/append
    file modes is not allowed.

    :param path: path to file
    :param delimiter: delimiter to split joined text on. if None, defaults to file.readlines()
    :param mode: file open mode
    :param buffering: passed to builtins.open
    :param encoding: passed to builtins.open
    :param errors: passed to builtins.open
    :param newline: passed to builtins.open
    :return: output of file depending on options wrapped in a Sequence via seq
    """
    if not re.match('^[rbt]{1,3}$', mode):
        raise ValueError('mode argument must be only have r, b, and t')
    if delimiter is None:
        return seq(LazyFile(path, mode=mode, buffering=buffering, encoding=encoding, errors=errors,
                            newline=newline))
    else:
        with builtins.open(path, mode=mode, buffering=buffering, encoding=encoding, errors=errors,
                           newline=newline) as data:
            return seq(''.join(data.readlines()).split(delimiter))


def range(*args):
    """
    Additional entry point to Sequence which wraps the builtin range generator.
    seq.range(args) is equivalent to seq(range(args)).
    """
    rng = builtins.range(*args)
    return seq(rng)


def csv(csv_file, dialect='excel', **fmt_params):
    """
    Additional entry point to Sequence which parses the input of a csv stream or file according
    to the defined options. csv_file can be a filepath or an object that implements the iterator
    interface (defines next() or __next__() depending on python version).

    >>> f = seq.csv('functional/test/data/test.csv').to_list()
    [['1', '2', '3', '4'], ['a', 'b', 'c', 'd']]

    :param csv_file: path to file or iterator object
    :param dialect: dialect of csv, passed to csv.reader
    :param fmt_params: options passed to csv.reader
    :return: Sequence wrapping csv file
    """
    if isinstance(csv_file, str):
        input_file = LazyFile(csv_file, mode='r')
    elif hasattr(csv_file, 'next') or hasattr(csv_file, '__next__'):
        input_file = csv_file
    else:
        raise ValueError('csv_file must be a file path or implement the iterator interface')

    csv_input = csvapi.reader(input_file, dialect=dialect, **fmt_params)
    return seq(csv_input)


def jsonl(jsonl_file):
    """
    Additional entry point to Sequence which parses the input of a jsonl file stream or file from
    the given path. Jsonl formatted files have a single valid json value on each line which is
    parsed by the python json module.

    :param jsonl_file: path or file containing jsonl content
    :return: Sequence wrapping jsonl file
    """
    if isinstance(jsonl_file, str):
        input_file = LazyFile(jsonl_file)
    else:
        input_file = jsonl_file
    return seq(input_file).map(jsonapi.loads).cache(delete_lineage=True)


def json(json_file):
    """
    Additional entry point to Sequence which parses the input of a json file handler or file from
    the given path. Json files are parsed in the following ways depending on if the root is a
    dictionary or array.
    1) If the json's root is a dictionary, these are parsed into a sequence of (Key, Value) pairs
    2) If the json's root is an array, these are parsed into a sequence of entries

    :param json_file: path or file containing json content
    :return: Sequence wrapping jsonl file
    """
    if isinstance(json_file, str):
        input_file = builtins.open(json_file, mode='r')
        json_input = jsonapi.load(input_file)
        input_file.close()
    elif hasattr(json_file, 'read'):
        json_input = jsonapi.load(json_file)
    else:
        raise ValueError('json_file must be a file path or implement the iterator interface')

    if isinstance(json_input, list):
        return seq(json_input)
    else:
        return seq(six.viewitems(json_input))


seq.open = open
seq.range = range
seq.csv = csv
seq.jsonl = jsonl
seq.json = json
