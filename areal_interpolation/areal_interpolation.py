import pandas as pd
import operator

def aggregate(source, target, source_columns=None, target_columns=None, method='fractional_area', spatial_index=True):
    """Function to (a) aggregate characteristics of source polygons (e.g., vote totals of election precincts) up into target polygons (e.g., hypothetical district maps) and/or (b) label source polygons by which target polygon they most overlap with.
    """

    Arguments
    ---------
    source: GeoPandas GeoDataFrame
        GeoDataFrame consisting of small polygons with associated columns of data.
    target: GeoPandas GeoDataFrame
        GeoPandas GeoDataFrame consisting of target polygons.
    source_columns: list, default None
        List of the names of columns of source data that should be aggregated up into target. These are values that will be summed, like population or vote total.
    target_columns: list, default None
        List of the names of the columns of the target data that should be used to label source polygons. These should be labels, like Census GEOID. If None, use the index of target.
    method: 'fractional_area', 'greatest_area', or 'first_centroid', default 'fractional_area'
        String indicating how to associate source with target. Options include:
        'fractional_area': Usually recommended, but slowest. Assumes that the data represented in source_columns is distributed uniformly across each soruce polygon, and distributes the data by fractional area across the target polygons in target. Uses the maximum fractional_area to determine which polygons in source get labeled by the labels in target_columns.

        'greatest_area': Recommended if source polygons should not intersect with more than one target polygon. About 1.5x faster than 'fractional_area'. Works like 'fractional_area', but assigns all of the source data to target polygons in a winner-take-all fashion, with the target polygon with the greatest fractional_area taking everything.

        'first_centroid': Like 'greatest_area', assigns data in source polygons to target polygons in a winner-take-all fashion based on the first target polygon to contain the centroid of the source polygon. About 2x faster than 'greatest_area' and 3x faster than 'fractional_area'.

        (Time comparisons are based on rudimentary exploration of a single dataset.)
    spatial_index: bool, default True
        Indicate whether to use a GeoPandas r-tree spatial index to speed up the process by 1.1x to 1.5x or so.

    Outputs
    -------
    source: GeoPandas GeoDataFrame
        Same as the input, but with new label columns as defined by the target_columns argument.
    target: GeoPandas GeoDataFrame
        Same as the input, but with new data columns as defined by the source_columns argument.

    """

    # add empty columns to be filled in
    source = pd.concat([source, pd.DataFrame(columns=target_columns)])
    source = pd.concat([source, pd.DataFrame(columns=target_columns)], sort=False)
    target = pd.concat([target, pd.DataFrame(columns=source_columns)], sort=False)
    
    if source_columns is not None:
        target[source_columns] = 0


    if spatial_index:
        si = target.sindex

    for i, _ in source.iterrows():
        shape = source.loc[i, 'geometry']

        if spatial_index:
            possible_matches = [target.index[m] for m in list(si.intersection(shape.bounds))]
        else:
            possible_matches = target.index

        if len(possible_matches) == 1:
            match = possible_matches[0]
            if method == 'fractional_area':
                frac_area = {match: 1}
        else:
            if method == 'greatest_area' or method == 'fractional_area':
                frac_area = {}
                found_majority = False
                shape_area = shape.area
                for j in possible_matches:
                    if not found_majority:
                        area = target.loc[j, 'geometry'].intersection(shape).area / shape_area
                        if area > .5 and method=='greatest_area':
                            # stop looking for new intersections if you find one above .5; you've already found the polygon with the greatest fractional area.
                            found_majority = True
                        frac_area[j] = area
                match = max(frac_area.items(), key=operator.itemgetter(1))[0]

            elif method == 'first_centroid':
                for j in possible_matches:
                    if target.loc[j, 'geometry'].contains(shape.centroid):
                        match = j
                        break

        if target_columns is not None:
            for col in target_columns:
                source.loc[i, col] = target.loc[match, col]
        else:
            source.loc[i, 'target_index'] = match
        
        if source_columns is not None:
            for col in source_columns:
                if method == 'fractional_area':
                    for j in possible_matches:
                        target.loc[j, col] += source.loc[i, col] * frac_area[j]
                else:
                    target.loc[match, col] += source.loc[i, col]

    return source, target
