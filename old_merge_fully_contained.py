def merge_fully_contained(df, geo_id = 'geometry',
                          nbr_id='neighbors', cols_to_add=['area']):
    '''If any geometry is contained entirely within another geometry, this
    function merges it into the larger geometry.  Slightly distinct from the
    'donut and donut-hole' analogy because if multiple precincts are completely
    surrounded by a ring-shaped precinct, then they will all be consumed.
    
    Arguments:
        df: geodataframe to apply rook contiguity to
        geo_id = column name for geometries in dataframe
        nbr_id = column name for neighbor list (to be generated) in dataframe
        cols_to_add = which attributes (column names) should be added when 
            precincts are merged (i.e. area or population). For all other 
            columns, the data from the consuming precinct is preserved.
        
    Output:
        dataframe with neighbors list for each attribute in a new column
        called nbr_id (default name is 'neighbors')
    '''
    
    # create neighbor list if it does not exist
    if (nbr_id not in df.columns):
        df = real_rook_contiguity(df)
    
    # Create list of rows to drop at the end of the multiple contained check
    ids_to_drop = []
    
    # Iterate over all attributes
    for i,_ in df.iterrows():
        
        # Create polygon Poly from its exterior coordinates. This
        # polygon will be filled without an interior. The purpose of filling
        # the interior is to allow for an intersection to see if a neighbor is
        # fully contained
        geometry = df.at[i, geo_id]
        poly_coords = list(geometry.exterior.coords)
        poly = Polygon(poly_coords)
        
        # Assuming no overlaps in the geometries, if poly contains the 
        # geometry then no neighbors can be contained in the geometry.
        # So we can go quickly through the loop in most cases.
        if geometry.contains(poly):
            continue
        
        # Create list of contained neighbor id's to delete
        nb_ix_del = []
    
        # Define a list of "possibly contained" precincts. If a precinct
        # is nested witin other contained precincts, we will need to add it to
        # this list
        possibly_contained = df.at[i, nbr_id]
        for j in possibly_contained:        
            
            # Check if the intersection of Poly (precint i's full polygon) and the
            # current neighbor is equal to the current neighbor. This demonstrates
            # that the current neighbor is fully contained within precinct i
            j_geom = df.at[j, geo_id]
            
            if j_geom == j_geom.intersection(poly):
                # j is fully contained within i. To account for nested precincts
                # we append any neighbor of j that is not already in possibly_
                # contained not including i
                for j_nb in df.at[j, nbr_id]:
                    if j_nb not in possibly_contained and j_nb != i:
                        possibly_contained.append(j_nb)
                        
                # Add geometry of j to geometry of i
                polys = [df.at[i, 'geometry'], 
                         df.at[j, 'geometry']]
                df.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
    
                # Add capture columns from neighbor to precinct i
                for col in cols_to_add:
                    if col in df.columns:
                        df.at[i, col] = df.at[i, col] + df.at[j, col]
                            
                # add neighbor reference from precinct i to delete if a neighbor
                if j in df.at[i, nbr_id]:
                    nb_ix = df.at[i, nbr_id].index(j)
                    nb_ix_del.append(nb_ix)
                
                # add neighbor precinct to the ID's to be dropped
                ids_to_drop.append(j)
                
        # Delete neighbor references from precinct i
        if len(nb_ix_del) > 0:
            # iterate through indexes in reverse to prevent errors through deletion
            for nb_ix in reversed(nb_ix_del):
                del(df.at[i, nbr_id][nb_ix])
    
    # Drop contained precincts from the dataframe and return
    df = df.drop(ids_to_drop)
    return df