#!/usr/bin/env python3
import logging
from pyadde.client import AddeClient
import asyncio
import traceback
import io
import sys
import getopt
import datetime
from matplotlib import pyplot as plt
import projections
from pyresample import geometry
from write_netcdf import nav_transform, write
import math
import warnings
import typing

warnings.filterwarnings('ignore', category=RuntimeWarning)

MISSING_VALUE = 2143289344 # defined by mcidas

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    x1 = lat2 - lat1
    y1 = lon2 - lon1

    a = math.sin(x1 / 2)**2 + math.cos(lat2) * math.cos(lat1) * math.sin(y1 / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def nn_radius(lat, lon):
    mid = int(len(lat) / 2)
    srt_idx = None
    for i in range(len(lat)):
        if lat[mid][i] != MISSING_VALUE:
            srt_idx = i
            break
    
    if not srt_idx:
        return 50000

    sum = 0
    for i in range(srt_idx, srt_idx + 10):
        sum += haversine(lat[mid][i], lon[mid][i], lat[mid][i+1], lon[mid][i+1])
    return (sum / 10) * 1000


async def process(host=None, project=0, user='XXXX', kwargs=None):
    try:
        async with AddeClient(host=host, project=project, user=user) as c:
            try:
                area_file = await c.aget(**kwargs)
                return area_file
            # except TypeError as err:
            # unexpected key-word arguments
            #    print(err)
            #    asyncio.get_event_loop().stop()
            except Exception as e:
                logger.error(e)
                #efp = io.StringIO()
                traceback.print_exc()
                #message = efp.getvalue()
                #logger.error(message)
                #raise
                return host, e
    except Exception as ee:
        logger.error(ee)
        return host, ee


async def collect(hosts=None, project=0, user='XXXX', kwargs=None):
    tasks = list()
    for h in hosts:
        taks = asyncio.ensure_future(process(host=h, user=user, project=project, kwargs=kwargs))
        tasks.append(taks)
    return await asyncio.gather(*tasks, return_exceptions=True)

    
doc = """
usage: ./fetchfile.py host=<host> group=<grp> descriptor=<desc> band=<band> position=<pos> file=<file>...
  required params: 
    host: adde server
      user: username (4 characters), optional depending on server
      project: project number (4 characters or integers), optional depending on server
    group: 
    descriptor: 
    band: band number or ALL
    position: single position or iter of positions or ALL

  non required (default) params: 
    file: file name binary AREA file data is saved to, default=None
    netcdf: file name netCDF4 data is saved to, default=None
    coord_type: (E)ARTH, (I)mage, or (A)rea, default=A
    coord_pos: (C)entered or (U)pper, default=U
    coord_start_dim1: lat or line number, default=None
    coord_start_dim2: lon or element number, default=None
    nlines: number or images lines to transmit, default=None
    nelems: number or elements to transmit, default=None
    day: day range to search ccyyddd or yyddd or yyyy-mm-dd, default=None
    stime: start time for time range to search hh:mm:ss, default=None
    etime: end time for time range to search hh:mm:ss, default=None
    aux: YES or NO, default=NO
    unit: calibration type requested, default=None
    spac: number of bytes per data point, default=X
    cal: default=X
    lmag: line magnification factor, default=1
    emag: element magnification factor default=1
    doc: YES or NO, default=YES
    aux: YES or NO, default=YES
"""

if __name__ == "__main__":
    logger = logging.getLogger("client")
    logger.setLevel('DEBUG')

    try:
        opts, args = getopt.getopt(sys.argv[1:], ":h", ["help"])
        if opts:
            print(doc)
            sys.exit(1)
    except getopt.GetoptError:
        pass

    args = sys.argv
    if len(args) > 2:
        clargs = dict((s.split('=') + [None])[:2] for s in args[1:])
    else:
        logger.debug("Arguments expected")
        print(doc)
        sys.exit(1)

    if 'host' not in clargs:
        raise KeyError("ADDE host must be specified")
    else:
        adde_server = clargs.pop('host')

    username = 'XXXX'
    prj = 0
    netcdf = None
    if 'user' in clargs:
        username = clargs.pop('user')
    if 'project' in clargs:
        prj = clargs.pop('project')
    if 'netcdf' in clargs:
        netcdf = clargs.pop('netcdf')

    then = datetime.datetime.now()
    loop = asyncio.new_event_loop()
    try:
        f = collect(hosts=[adde_server], user=username, project=prj, kwargs=clargs)
        a = loop.run_until_complete(f)

        for e in a:
            try:
                logger.info('Drawing AreaFile')
                d = e.data[0]
                fig = plt.figure(1, figsize=(10,10))
                plt.title(f'Band {e.directory.bands[0]}')
                plt.xticks([]) 
                plt.yticks([])
                plt.imshow(d, cmap='gist_gray')
                plt.show(block=False)
                plt.pause(0.05)
                
                try:    
                    proj = {'G': 'Geostationary', 'P': 'Plate Carree', 'R': 'Robinson', 'M': 'Mollweide'}
                    logger.debug('Starting nav transform')
                    now = datetime.datetime.now()
                    lat, lon, proj_lat, proj_lon = nav_transform(e)
                    logger.debug(f'{datetime.datetime.now() - now}')
                    
                    radius = nn_radius(lat, lon) 
                    arg_str = ' '.join(args) # turn list of cla's to string
                    if netcdf:
                        logger.debug(f'Writing netCDF file: {netcdf}')
                        arg_str = ' '.join(args) # turn list of cla's to string 
                        write(e, lat, lon, filename=netcdf, audit_str=arg_str) 

                    swath_def = geometry.SwathDefinition(lons=lon, lats=lat)
                    print('Projections: ')
                    print('\t(G)eostationary')
                    print('\t(P)late Carree')
                    print('\t(R)obinson')
                    print('\t(M)ollweide')
                    print()
                    while True:
                        i = input('Specify projection (G, P, R, M) or press Q to quit: ') 
                        match i:
                            case 'G' | 'g':
                                i = i.upper()
                                logger.info(f'Drawing {proj[i]} Projection')
                                data, crs, extent = projections.geostationary(swath_def, e.data[0], proj_lat, proj_lon, radius)
                            case 'P' | 'p':
                                i = i.upper()
                                logger.info(f'Drawing {proj[i]} Projection')
                                data, crs, extent = projections.plate_carree(swath_def, e.data[0], proj_lat, proj_lon, radius)
                            case 'R' | 'r':
                                i = i.upper()
                                logger.info(f'Drawing {proj[i]} Projection')
                                data, crs, extent = projections.robinson(swath_def, e.data[0], proj_lat, proj_lon, radius)
                            case 'M' | 'm':
                                i = i.upper()
                                logger.info(f'Drawing {proj[i]} Projection')
                                data, crs, extent = projections.mollweide(swath_def, e.data[0], proj_lat, proj_lon, radius)
                            case 'Q' | 'q':
                                plt.close()
                                break
                            case _:
                                logger.info('Invalid projection')
                                continue

                        ax = projections.plot(data, crs, extent, figtitle=f'{proj[i]} Projection')
                        plt.tight_layout()
                        plt.show(block=False)

                except Exception as err:
                    traceback.print_exc()
                    logger.error(err)

            except Exception as err:
                if isinstance(err, typing.Iterable):
                    host, em = e
                    logger.info(f'Server {host} says {em}')
                else:
                    print(e)
                    logger.error(err)

    except KeyboardInterrupt as ke:

        logger.info('Attempting graceful shutdown')
        def shutdown_exception_handler(loop, context):
            if "exception" not in context or not isinstance(context["exception"], asyncio.CancelledError):
                loop.default_exception_handler(context)

        loop.set_exception_handler(shutdown_exception_handler)
        tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()
        while not tasks.done() and not loop.is_closed():
            loop.run_forever()

    finally:
        loop.close()
        now = datetime.datetime.now()
        logger.info(f'Total run time {now-then}')
