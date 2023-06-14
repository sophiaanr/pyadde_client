'''
Converted to python from c
based on mcidas file ncdfaput.c
Converts AREAnnn file to netCDF4 file
Only works for Area files with 1 band
'''

import netCDF4 as nc
import datetime
import numpy as np
import math

'''
HEADER_FIELDS = (
    # words 1-8
    ('relative_position_within_dataset', C.c_int32),
    ('image_type', C.c_int32),
    ('sensor_source_number', C.c_int32),
    ('yyyddd', C.c_int32),
    ('hhmmss', C.c_int32),
    ('line_ul', C.c_int32),
    ('element_ul', C.c_int32),
    ('_reserved1', C.c_int32),

    # 9-16
    ('lines', C.c_int32),
    ('elements', C.c_int32),
    ('bytes_per_element', C.c_int32),
    ('line_res', C.c_int32),
    ('element_res', C.c_int32),
    ('spectral_band_count', C.c_int32),
    ('line_prefix_length', C.c_int32),
    ('project', C.c_int32),

    # 17-24
    ('file_yyyddd', C.c_int32),
    ('file_hhmmss', C.c_int32),
    ('spectral_band_map_1_32', C.c_int32),
    ('spectral_band_map_33_64', C.c_int32),
    ('sensor_specific', C.c_int32 * 4),

    # 25-32
    ('memo', C.c_char * 32),

    # 33-36
    ('_reserved2', C.c_int32),
    ('data_block_offset', C.c_int32),
    ('nav_block_offset', C.c_int32),
    ('validity_code', C.c_int32),

    # 37-44
    ('program_data_load', C.c_int32 * 8),

    # 45-48
    ('band8_source_goesaa', C.c_int32),
    ('image_yyyddd', C.c_int32),
    ('image_hhmmss_or_ms', C.c_int32),
    ('start_scan', C.c_int32),

    # 49-56
    ('prefix_doc_length', C.c_int32),
    ('prefix_cal_length', C.c_int32),
    ('prefix_band_length', C.c_int32),
    ('source_type', C.c_char * 4),
    ('cal_type', C.c_char * 4),
    ('_reserved3', C.c_int32 * 3),

    # 57-64
    ('original_source_type', C.c_char*4),
    ('units', C.c_char*4), # changed from int to char
    ('scaling', C.c_int32),
    ('aux_block_offset', C.c_int32),
    ('aux_block_length', C.c_int32),
    ('_reserved4', C.c_int32),
    ('cal_block_offset', C.c_int32),
    ('comment_count', C.c_int32)
)
'''


def write(area_file, latdata, londata, filename='NCDFxxxx.nc', audit_str=''):
    '''Write netCDF file from AreaFile'''

    adir = area_file.directory
    with nc.Dataset(filename, 'w', format='NETCDF4') as f:
        f.createDimension('xc', adir.elements)
        f.createDimension('yc', adir.lines)
        f.createDimension('time', 1)

        num_chunks = 1
        if len(audit_str) > 0:
            num_chunks = math.ceil(len(audit_str) / 80)

        f.createDimension('auditCount', adir.comment_count + num_chunks)
        f.createDimension('auditSize', 80) # length of single comment card

        version = f.createVariable('version', 'i4') # 'i4' is signed 4 bit integer
        version.longname = 'McIDAS area file version' # add attribute

        sensor = f.createVariable('sensorID', 'i4')
        sensor.long_name = 'McIDAS sensor number'

        imgdate = f.createVariable('imageDate', 'i4')
        imgdate.long_name = 'image year and day of year (in ccyyddd format)'

        imgtime = f.createVariable('imageTime', 'i4')
        imgtime.long_name = 'image time in UTC (hours/minutes/seconds, in HHMMSS format)'

        srtline = f.createVariable('startLine', 'i4')
        srtline.long_name = 'starting image line (in satellite coordinates)'

        srtelem = f.createVariable('startElem', 'i4')
        srtelem.long_name = 'starting image element (in satellite coordintes)'

        time = f.createVariable('time', 'i4', dimensions=('time'))
        time.long_name = 'seconds since 1970-1-1 0:0:0'
        time.units = 'seconds since 1970-1-1 0:0:0'

        datawid = f.createVariable('dataWidth', 'i4')
        datawid.long_name = 'number of 8-bit bytes per source data point'

        lineres = f.createVariable('lineRes', 'i4')
        lineres.long_name = 'resolution of each pixel in line direction'
        lineres.units = 'km'

        elemres = f.createVariable('elemRes', 'i4')
        elemres.long_name = 'resolution of each pixel in element direction'
        elemres.units = 'km'

        prefix = f.createVariable('prefixSize', 'i4')
        prefix.long_name = 'line prefix size in 8-bit bytes'

        createdate = f.createVariable('crDate', 'i4')
        createdate.long_name = 'image creation year and day of year in ccyyddd format'

        createtime = f.createVariable('crTime', 'i4')
        createtime.long_name = 'image creation time in UTC in hhmmss format'

        band = f.createVariable('bands', 'i4')
        band.long_name = 'satellite channel number'

        audittrail = f.createVariable('auditTrail', 'S1', dimensions=('auditCount', 'auditSize'))
        audittrail.long_name = 'audit trail'

        data = f.createVariable('data', 'f4', ('time', 'yc', 'xc'))

        cal_type = adir.cal_type
        match cal_type:
            case b'RAD' | 'RAD':
                data.long_name = 'Radiance'
            case b'BRIT' |'BRIT':
                data.long_name = '0-255 Brightness Temperature'
            case b'TEMP' | 'TEMP':
                data.long_name = 'Temperature' 
            case b'ALB' | 'ALB':
                data.long_name = 'Albedo'
            case b'RAW' | 'RAW':
                data.long_name = 'Raw Satellite Counts'
            case _:
                data.long_name = 'data'
        
        data.type = adir.source_type.decode() # decode bytes into utf-8 encoded string
        data.coordinates = 'lon lat'

        # lines 806 to line 841: units for RAD cal type
        # not tested, wouldn't be surprised if it didn't work
        if cal_type == 'RAD' or cal_type == b'RAD':
            cal_unit = adir.units  # should be a byte string
            if isinstance(cal_type, bytes):
                cal_unit = cal_unit.decode(encoding='utf-8')
            if isinstance(cal_type, str):
                if cal_unit.startswith('wP') | cal_unit.startswith('Wp') | cal_unit.startswith('wp') | cal_unit.startswith('WP'):
                    data.units = 'Watts/meter2/steradian'
                elif cal_unit.startswith('mP') | cal_unit.startswith('Mp') | cal_unit.startswith('mp') | cal_unit.startswith('MP'):
                    data.units = 'Milliwatts/meter2/steradian/(cm-1)'
                elif cal_unit.startswith('wM') | cal_unit.startswith('Wm') | cal_unit.startswith('wm') | cal_unit.startswith('WM'):
                    data.units = 'Watts/meter2/steradian/micron'
                else:
                    data.units = 'Unknown'
            else:
                data.units = 'Unknown'

        lat = f.createVariable('lat', 'f4', dimensions=('yc', 'xc'))
        lat.long_name = 'lat'
        lat.units = 'degrees_north'

        lon = f.createVariable('lon', 'f4', dimensions=('yc', 'xc'))
        lon.long_name = 'lon'
        lon.units = 'degrees_east'

        f.Conventions = 'CF-1.10' # newest version of cf compliance
        f.Source = 'McIDAS Area File'
        f.SatelliteSensor = adir.sensors[adir.sensor_source_number]

        version[:] = adir.image_type
        sensor[:] = adir.sensor_source_number
        yyyddd = adir.yyyddd
        year = ((yyyddd // 1000) % 1900) + 1900
        imgdate[:] = int(f'{year}{yyyddd % 1000:03}')
        imgtime[:] = adir.hhmmss
        srtline[:] = adir.line_ul
        srtelem[:] = adir.element_ul
        datawid[:] = adir.bytes_per_element
        lineres[:] = adir.line_res
        elemres[:] = adir.element_res
        prefix[:] = adir.line_prefix_length
        createdate[:] = adir.file_yyyddd
        createtime[:] = adir.file_hhmmss
        time[:] = (adir.nominal_time - datetime.datetime(1970, 1, 1)).total_seconds() # timestamp() uses local time not UTC ??
        band[:] = adir.bands[0]
        data[:] = area_file.data

        lat[:] = latdata
        lon[:] = londata

        audit_chunks = [audit_str[i:i+80] for i in range(0, num_chunks * 80, 80)]
        if adir.comment_cards :
            audit_chunks = adir.comment_cards + audit_chunks
        audittrail[:] = nc.stringtochar(np.array([audit_chunks], 'S80'))


def nav_transform(area):
    '''Use AreaFile navigation and directory to transform lines/elems to lat/lon'''
    from nvxgoes import nvxgoes as nvx

    navsrt = datetime.datetime.now()
    nav = area.nav

    # initialize nvxgoes module
    nvx.nvxini(1, nav)

    lat = []
    lon = []

    curr_line = area.directory.line_ul
    srt_elem = area.directory.element_ul
    num_lines = area.directory.lines
    num_elems = area.directory.elements
    line_res = area.directory.line_res
    elem_res = area.directory.element_res
    for i in range(num_lines):
        curr_elem = srt_elem
        lat_row = []
        lon_row = []
        for j in range(num_elems):
            nvxsae, xpar, ypar, zpar = nvx.nvxsae(curr_line, curr_elem, 0.0)
            if nvxsae == -1:
                lat_row.append(0x7FC00000) # value for missing data ( off the earth )
                lon_row.append(0x7FC00000)
            else:
                lat_row.append(xpar)
                lon_row.append(-ypar)
            curr_elem += elem_res
        lat.append(lat_row)
        lon.append(lon_row)
        curr_line += line_res


    # calculate satellite height and projection_longitude
    x, y, z = nvx.satpos(0, nav[2])
    height = np.sqrt(x**2 + y**2 + z**2) * 1000 # height in meters
    proj_lat, proj_lon = nvx.nxyzll(x, y, z)
    proj_lon = -proj_lon

    navstop = datetime.datetime.now()
    return lat, lon, proj_lat, proj_lon


#if __name__ == '__main__':
#    from pyarea.file import AreaFile
#    with open('../AREA9998', 'rb') as f:
#        c = f.read()   
#    audit = './fetchfile.py host=geoarc.ssec.wisc.edu user=DAS project=6999 group=AGOES02 descriptor=A-VIS file=AREA9998  unit=BRIT nlines=700 nelems=700 lmag=-22 emag=-22 stime=17.5 etime=17.5 position=0 band=1 day=1978055'
#    a = AreaFile(c)
#    latdata, londata, _, _ = nav_transform(a)
#    write(a, latdata, londata, 'test9998.nc', audit)
