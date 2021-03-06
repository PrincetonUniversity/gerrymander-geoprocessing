"""
Helper methods for image based calculations
"""
from PIL import Image
import shapely as shp
import numpy as np
import operator
import helper_tools.shp_calculations as sc


def cropped_bordered_image(img_path):
    ''' Given an image with a border of one color, returns an image with the
    border cropped off.  Works with images in numpy array form.

    Argument:
        img_arr:
            numpy array generated by np.asarray(image)

    Output:
        file path to the cropped image
        modified image array with border cropped off
    '''
    img = Image.open(img_path)
    img_arr = np.asarray(img)

    # calcluate extents of image
    xlen = len(img_arr[0])
    ylen = len(img_arr)

    # calculate border color as top-left pixel
    top_left = img_arr[0][0]
    bot_left = (img_arr[0][xlen - 1] == top_left).all()
    top_right = (img_arr[ylen - 1][0] == top_left).all()
    bot_right = (img_arr[ylen - 1][xlen - 1] == top_left).all()

    # if other corners are not the same color, throw an error
    if not (bot_left and top_right and bot_right):
        raise ValueError('Image does not have same color in all corners')

    # find inner border extents (left, top, right, bottom)
    color = top_left
    top = 0
    while (img_arr[top] == color).all():
        top += 1
    bottom = ylen - 1
    while (img_arr[bottom] == color).all():
        bottom -= 1
    left = 0
    while (img_arr[:, left] == color).all():
        left += 1
    right = xlen - 1
    while (img_arr[:, right] == color).all():
        right -= 1

    # Save new image as 'oldname cropped'
    ext = img_path.split('.')[-1]
    filename = '.'.join(img_path.split('.')[:-1]) + '_cropped'
    new_name = filename + '.' + ext
    # cropped_img = Image.fromarray(img_arr[top+1:bottom, left+1:right])
    cropped_img = Image.fromarray(img_arr[top:bottom, left:right])
    cropped_img.save(new_name)

    # crop and return array
    return new_name


def reduce_colors(img, num_colors):
    ''' Generates an image reducing the number of colors to a number
    specified by the user. Uses Image.convert from PIL.

    Arguments:
        img:
            original image in PIL Image format

        num_colors:
            number of distinct colors in output file

    Output:
        Modified image with reduced number of distinct RGB values
    '''

    conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=num_colors)
    return conv_img.convert('RGB')


def isBlack(color):
    ''' Returns True iff all 3 RGB values are less than 25.

    Arguments:
        color: a list whose first 3 elements are RGB.

    Output:
        True if black, false otherwise
    '''

    return (color[0] < 25 and color[1] < 25 and color[2] < 25)


def most_common_color(poly, img_arr, xmin, xlen, ymin, ylen, sample_limit):
    ''' This function uses pixel sampling to calculate (with high probability)
    the most common RGB value in the section of an image corresponding to
    a Shapely polygon within the reference geometry.

    Arguments:
        poly:
            Shapely polygon within reference geometry

        img_arr:
            numpy array generated by np.asarray(image)

        xmin:
            x coordinate (in geometry coordinate system) of leftmost point
            in georeferenced image

        xlen:
            maximum - minimum x coordinate in georeferenced image

        ymin:
            minimum y coordinate in georeferenced image

        ylen:
            maximum - minimum y coordinate in georeferenced image

        sample_limit:
            maximum number of pixels to sample before guessing

    Output:
        integer corresponding to 256^2 R + 256 G + B
    '''

    # triangulate polygon
    triangles = shp.ops.triangulate(poly)

    # in very rare cases, the polygon is so small that this shapely operation
    # fails to triangulate it, so we return 0 (black)
    if len(triangles) == 0:
        return 0

    # make list of partial sums of areas so we can pick a random triangle
    # weighted by area
    areas = np.asarray([0])
    for triangle in triangles:
        areas = np.append(areas, areas[-1] + triangle.area)

    # scale so last sum is 1
    areas = areas / areas[-1]

    # initialize data to monitor throughout the sampling process
    # colors is a dictionary to store the number of pixels of each color
    colors = {}
    sampled = 0
    used = 0
    color_to_return = None
    stop_sampling = False
    # sample as long as none of the stop criteria have been reached
    while not stop_sampling:

        # update sample count
        sampled += 1

        # select a random triangle (weighted by area) in the triangulation
        r = np.random.random_sample()
        triangle = triangles[np.searchsorted(areas, r) - 1]

        # select a point uniformly at random from this triangle
        pt = sc.random_pt_in_triangle(triangle)

        # gets size of img_arr to align it with poly
        img_xlen = len(img_arr[0])
        img_ylen = len(img_arr)

        # get color of pixel that corresponds to pt
        color = sc.pt_to_pixel_color(pt, img_arr, xmin, xlen, ymin, ylen,
                                     0, img_xlen, 0, img_ylen)

        # in case all are black, return black
        colors[0] = 1

        # if not black, add color to dictionary
        if not isBlack(color):

            used += 1

            # for hashing
            color_int = 256 * 256 * color[0] + 256 * color[1] + color[2]

            # update dictionary
            if color_int not in colors:
                colors[color_int] = 0
            colors[color_int] += 1

        # decide if we are done sampling (every 10 samples)
        if (sampled % 10 == 0):

            # find the most common color and its frequency
            common = max(colors.items(), key=operator.itemgetter(1))[0]
            common_count = colors[common]

            # calculate z-score based on proportion test
            # trying to get evidence that this color is over 50% frequent
            # among all pixels
            if used > 0:
                z_score = (2 * common_count / used - 1) * np.sqrt(used)
            else:
                z_score = 0

            # stop sampling if we have convincing evidence or we hit our limit
            if (z_score > 4 or sampled >= sample_limit):
                color_to_return = common
                stop_sampling = True

    return color_to_return
