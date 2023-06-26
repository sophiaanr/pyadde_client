# different projections for full disk images
from pyresample import kd_tree, geometry
from matplotlib import pyplot as plt
from pyresample.area_config import create_area_def
import matplotlib as mpl
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import numpy as np


def plate_carree(swath_def, data, proj_lat, proj_lon, radius_nn=50000):
    projection = {'proj': 'eqc', 'ellps':'WGS84', 'lon_0': proj_lon, 'lat_0': proj_lat}
    extent = [-10018754.17, -10018754.17, 10018754.17, 10018754.17]
    area_def = create_area_def('pc_world', projection=projection, description='Plate Carree Proj', units='meters', width=2702, height=2702, area_extent=extent)
    
    res = kd_tree.resample_nearest(swath_def, data, area_def, radius_of_influence=radius_nn, epsilon=0.5)
    crs = area_def.to_cartopy_crs()
    return res, crs, extent


def geostationary(swath_def, data, proj_lat, proj_lon, radius_nn=50000):
    projection = {'proj': 'geos', 'a': '6378169', 'h': '35785831', 'lon_0': proj_lon, 'lat_0': proj_lat, 'rf': 295.488065897001}
    extent = [-5434201.1352, -5415668.5992, 5434201.1352, 5415668.5992]
    area_def = create_area_def('geos_full_disk', projection=projection, description='Geostationary Proj', units='meters', width=2712, height=2702, area_extent=extent)

    res = kd_tree.resample_nearest(swath_def, data, area_def, radius_of_influence=radius_nn, epsilon=0.5)
    crs = area_def.to_cartopy_crs()
    return res, crs, extent


def robinson(swath_def, data, proj_lat, proj_lon, radius_nn=50000):
    projection = {'proj': 'robin', 'ellps': 'WGS84', 'lon_0': proj_lon, 'lat_0': proj_lat}
    extent = [-20037508.34, -10018754.17, 20037508.34, 10018754.17]
    area_def = create_area_def('robin_world', projection=projection, description='Robinson Proj', units='meters', width=2702, height=2702, area_extent=extent)

    res = kd_tree.resample_nearest(swath_def, data, area_def, radius_of_influence=radius_nn, epsilon=0.5)
    crs = area_def.to_cartopy_crs()
    return res, crs, extent


def mollweide(swath_def, data, proj_lat, proj_lon, radius_nn=50000):
    projection = {'proj': 'moll', 'ellps': 'WGS84', 'lon_0': proj_lon, 'lat_0': proj_lat}
    extent = [-20037508.34, -10018754.17, 20037508.34, 10018754.17]
    area_def = create_area_def('mollweide', projection=projection, description='Mollweide projection', units='meters', width=1920, height=1440, area_extent=extent)
    res = kd_tree.resample_nearest(swath_def, data, area_def, radius_of_influence=radius_nn, epsilon=0.5)
    crs = area_def.to_cartopy_crs()
    return res, crs, extent


def plot(img_data, crs, extent, figsize=(8,8), cmap='gist_gray', figtitle=''):
    fig = plt.figure(figsize=figsize)
    ax = plt.axes(projection=crs) 
    ax.set_title(figtitle)
    ax.set_global()
    
    cmap = mpl.colormaps[cmap]
    cmap.set_under(color='white')
    plt.imshow(img_data, transform=crs, extent=crs.bounds, cmap=cmap, vmin=0.5)
    ax.set_frame_on(False)
    ax.coastlines()
    gl = ax.gridlines(draw_labels=True)
    plt.tight_layout()
    return ax

