import os

def delete_cpg(path):
    '''Deletes the CPG with a corresponding SHP. ArcGIS sometimes incorrectly
    encodes a shapefile and incorrectly saves the CPG. Before running most
    of the scripts, it is beneficially to ensure an encoding error does throw
    an error
    
    Argument:
        path: path to a file that has the same name as the .cpg file. Usually
        the shapefile
    '''
    
    cpg_path = '.'.join(path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)