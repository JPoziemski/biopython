#!/usr/bin/env python2.3

__version__ = "$Revision: 1.10 $"

import os
import sys

from Bio.SeqIO.FASTA import FastaReader, FastaWriter

try:
    import poly

    _NamedTemporaryFile = poly.NamedTemporaryFile
except ImportError:
    import tempfile
    
    _NamedTemporaryFile = tempfile.NamedTemporaryFile

def _build_align_cmdline(cmdline, pair, output_filename, kbyte=None, force_type=None, quiet=False):
    """
    >>> os.environ["WISE_KBYTE"]="300000"
    >>> _build_align_cmdline(["dnal"], ("seq1.fna", "seq2.fna"), "/tmp/output", kbyte=100000)
    'dnal -kbyte 100000 seq1.fna seq2.fna > /tmp/output'
    >>> _build_align_cmdline(["psw"], ("seq1.faa", "seq2.faa"), "/tmp/output_aa")
    'psw -kbyte 300000 seq1.faa seq2.faa > /tmp/output_aa'

    """
    cmdline = cmdline[:]

    ### XXX: force_type ignored

    if kbyte is None:
        try:
            cmdline.extend(("-kbyte", os.environ["WISE_KBYTE"]))
        except KeyError:
            pass
    else:
        cmdline.extend(("-kbyte", str(kbyte)))

    try:
        import poly
        if poly.jobid:
            cmdline.append("-quiet")
    except ImportError:
        pass

    cmdline.extend(pair)
    cmdline.extend((">", output_filename))
    if quiet:
        cmdline.extend(("2>", "/dev/null"))
    cmdline_str = ' '.join(cmdline)

    return cmdline_str

def align(cmdline, pair, kbyte=None, force_type=None, dry_run=False, quiet=False, debug=False):
    """
    Returns a filehandle
    """
    output_file = _NamedTemporaryFile(mode='r')
    input_files = _NamedTemporaryFile(mode="w"), _NamedTemporaryFile(mode="w")

    if dry_run:
        print _build_align_cmdline(cmdline,
                                   pair,
                                   output_file.name,
                                   kbyte,
                                   force_type,
                                   quiet)
        return

    for filename, input_file in zip(pair, input_files):
        input_file.close()
        FastaWriter(file(input_file.name, "w")).write(FastaReader(file(filename)).next())

    input_file_names = [input_file.name for input_file in input_files]
    
    cmdline_str = _build_align_cmdline(cmdline,
                                       input_file_names,
                                       output_file.name,
                                       kbyte,
                                       force_type,
                                       quiet)

    if debug:
        print >>sys.stderr, cmdline_str
        
    status = os.system(cmdline_str) >> 8

    if status > 1:
        if kbyte != 0: # possible memory problem; could be None
            print >>sys.stderr, "INFO trying again with the linear model"
            return align(cmdline, pair, 0, force_type, dry_run, quiet, debug)
        else:
            raise OSError, "%s returned %s" % (" ".join(cmdline), status)
    
    return output_file

def all_pairs(singles):
    """
    Generate pairs list for all-against-all alignments

    >>> all_pairs(range(4))
    [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    """
    pairs = []

    singles = list(singles)
    while singles:
        suitor = singles.pop(0) # if sorted, stay sorted
        pairs.extend([(suitor, single) for single in singles])

    return pairs

def main():
    pass

def _test(*args, **keywds):
    import doctest, sys
    doctest.testmod(sys.modules[__name__], *args, **keywds)

if __name__ == "__main__":
    if __debug__:
        _test()
    main()