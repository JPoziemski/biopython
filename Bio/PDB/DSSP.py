# make yield compatible with Python 2.2
from __future__ import generators

import os
import tempfile

from Bio.PDB import *



__doc__="""
Use the DSSP program to calculate secondary structure and accessibility.
You need to have a working version of DSSP (and a
license - free for academic use) in order to use this. 

For DSSP, see http://www.cmbi.kun.nl/gv/dssp/.

The DSSP codes for secondary structure used here are:

H        Alpha helix (4-12)
B        Isolated beta-bridge residue
E        Strand ("extended")
G        3-10 helix
I        pi helix
T        Turn
S        Bend
-        None
"""

def dssp_dict_from_pdb_file(in_file, DSSP="dssp"):
    """
    Create a DSSP dictionary from a PDB file.

    Example:
        >>> dssp_dict=dssp_dict_from_pdb_file("1fat.pdb")
        >>> aa, ss, acc=dssp_dict[('A', 1)]

    @param in_file: pdb file
    @type in_file: string

    @param DSSP: DSSP executable (argument to os.system)
    @type DSSP: string

    @return: a dictionary that maps (chainid, resid) to 
        amino acid type, secondary structure code and 
        accessibility.
    @rtype: {}
    """
    out_file=tempfile.mktemp()
    os.system(DSSP+" %s > %s" % (in_file, out_file))
    d=make_dssp_dict(out_file)
    # This can be dangerous...
    #os.system("rm "+out_file)
    return d

def make_dssp_dict(filename):
    """
    Return a DSSP dictionary that maps (chainid, resid) to
    aa, ss and accessibility, from a DSSP file.

    @param filename: the DSSP output file
    @type filename: string
    """
    dssp={}
    fp=open(filename, "r")
    start=0
    for l in fp.readlines():
        sl=l.split()
        if sl[1]=="RESIDUE":
            # start
            start=1
            continue
        if not start:
            continue
        if l[9]==" ":
            # skip -- missing residue
            continue
        resseq=int(l[5:10])
        icode=l[10]
        chainid=l[11]
        aa=l[13]
        ss=l[16]
        if ss==" ":
            ss="-"
        acc=int(l[34:38])
        res_id=(" ", resseq, icode)
        dssp[(chainid, res_id)]=(aa, ss, acc)
    fp.close()
    return dssp


class DSSP:
    """
    Run DSSP on a pdb file, and provide a handle to the 
    DSSP secondary structure and accessibility.

    Note that DSSP can only handle one model.

    Example:
        >>> p=PDBParser()
        >>> structure=parser.get_structure("1fat.pdb")
        >>> model=structure[0]
        >>> dssp=DSSP(model, "1fat.pdb")
        >>> # print dssp data for a residue
        >>> secondary_structure, accessibility=dssp[residue]
    """
    def __init__(self, model, pdb_file, dssp="dssp"):
        """
        @param model: the first model of the structure
        @type model: L{Model}

        @param pdb_file: a PDB file
        @type pdb_file: string

        @param dssp: the dssp executable (ie. the argument to os.system)
        @type dssp: string
        """
        p=PDBParser()
        # create DSSP dictionary
        self.dssp_dict=dssp_dict_from_pdb_file(pdb_file, dssp)
        map={}
        res_list=[]
        # Now create a dictionary that maps Residue objects to 
        # secondary structure and accessibility, and a list of 
        # (residue, (secondary structure, accessibility)) tuples
        for chain in model.get_iterator():
            chain_id=chain.get_id()
            for res in chain.get_iterator():
                res_id=res.get_id()
                if self.dssp_dict.has_key((chain_id, res_id)):
                    aa, ss, acc=self.dssp_dict[(chain_id, res_id)]
                    # Verify if AA in DSSP == AA in Structure
                    resname=res.get_resname()
                    resname=to_one_letter_code[resname]
                    # Something went wrong if this is not true!
                    assert(resname==aa)
                    map[res]=(ss, acc)
                    res_list.append((res, (ss, acc)))
                else:
                    pass
        self.map=map
        self.res_list=res_list
        self.model=model

    def __getitem__(self, res):
        """
        Return (secondary structure, accessibility) tuple for 
        a residue.

        @param res: a residue
        @type res: L{Residue}

        @return: (secondary structure, accessibility) tuple
        @rtype: (char, int)
        """
        return self.map[res]

    def __len__(self):
        """
        Return number of residues for which accessibility & secondary
        structure is available.

        @return: number of residues
        @rtype: int
        """
        return len(self.res_list)

    def has_key(self, res):
        """
        Return 1 if DSSP has calculated accessibility & secondary
        structure for this residue, 0 otherwise.

        Example:
            >>> if dssp.has_key(residue):
            >>>     sec, acc=dssp[residue]
            >>>     print sec, acc

        @param res: a residue
        @type res: L{Residue}
        """
        return self.map.has_key(res)

    def get_keys(self):
        """
        Return the list of residues.

        @return: list of residues for which accessibility & secondary 
            structure was calculated by DSSP.
        @rtype: [L{Residue}, L{Residue},...] 
        """
        return Selection.unfold_entities(self.model, 'R')

    def get_iterator(self):
        """
        Iterate over the (residue, (secondary structure, accessibility))
        list. Handy alternative to the dictionary-like access.

        Example:
            >>> for (res, (sec, acc)) in dssp.get_iterator():
            >>>     print res, sec, acc         

        @return: iterator
        """
        for i in range(0, len(self.res_list)):
            yield self.res_list[i]


if __name__=="__main__":

    import sys

    p=PDBParser()
    s=p.get_structure('X', sys.argv[1])

    model=s[0]

    d=DSSP(model, sys.argv[1])

    for r in d.get_iterator():
        print r


