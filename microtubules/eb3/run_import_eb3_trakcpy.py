import logging
import os
import re
import sys
import warnings

import coloredlogs
import pandas as pd
import trackpy as tp
import trackpy.diag
import trackpy.predict
import matplotlib.pyplot as plt
import numpy as np
import tifffile as tf
from moviepy.video.io.bindings import mplfig_to_npimage
import moviepy.editor as mpy
import skimage.draw as draw
import skimage.filters as filters
import skimage.exposure as exposure
import skimage.morphology as morphology
import skimage.measure as measure
import skimage.color as color
from matplotlib import cm
from scipy import ndimage
from shapely.geometry import Point, Polygon

import parameters as p
import plot_special_tools as sp

warnings.filterwarnings("ignore", category=DeprecationWarning)
coloredlogs.install(fmt='%(levelname)s:%(funcName)s - %(message)s', level=logging.INFO)
tp.diag.performance_report()
logging.basicConfig(stream=sys.stderr, format='%(levelname)s:%(funcName)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)
coloredlogs.install()
trackpy.quiet()
pd.set_option('display.width', 320)


def movie(frames, linked_particles, filename="movie.mp4", pix_per_um=1):
    def make_frame_mpl(t):
        fr = int(t)

        ax.cla()
        im = render[fr]
        # im = exposure.equalize_hist(im)
        # w, h = im.shape[0], im.shape[1]

        tp.annotate(linked_particles[linked_particles['frame'] == fr], im, ax=ax,
                    plot_style={"markersize": 4},
                    # imshow_style={"extent": [0, w / pix_per_um, h / pix_per_um, 0]})
                    )
        # tp.plot_displacements(linked_particles, fr, fr + 1, ax=ax, arrowprops={"color": "blue", "alpha": 0.2})
        # ax.set_xlabel("x[um]")
        # ax.set_ylabel("y[um]")

        return mplfig_to_npimage(fig)  # RGB image of the figure

    # subtract first frame and deal with negative results after the operation
    nobkg = np.int32(frames)
    nobkg -= nobkg[0]
    nobkg = nobkg[1:, :, :]
    nobkg = np.uint16(nobkg.clip(0))

    # path, fim = os.path.split(image_path)
    linked_particles['frame'] += 1
    nobkg = exposure.equalize_hist(nobkg)
    frames = exposure.equalize_hist(frames)
    nobkg = color.gray2rgb(nobkg)
    frames = color.gray2rgb(frames)
    render = frames[1:] * 0.2 + nobkg * sp.colors.hoechst_33342 * 0.4

    logging.info("rendering movie %s" % filename)
    fig = plt.figure(20)
    ax = fig.gca()
    fig.tight_layout()

    animation = mpy.VideoClip(make_frame_mpl, duration=len(render))
    animation.write_videofile(filename, fps=1)
    animation.close()


def vis_detection(image_path, filename="movie.mp4"):
    def make_frame_mpl(t):
        fr = int(t)

        for ax in [ax1, ax2, ax3, ax4]:
            ax.cla()
        # im = _images[fr]
        im = frames[fr]
        # im = exposure.equalize_hist(im)

        # edges = canny(im, 2, 1, 25)
        # median=rank.median(image=im, selem=disk(0.2*pix_per_um))
        median = im
        ax1.imshow(median, cmap=cm.gray)

        thr_lvl = filters.threshold_otsu(median)
        thresh = im >= thr_lvl
        morphology.remove_small_objects(thresh, min_size=2 * pix_per_um, in_place=True)
        ax2.imshow(thresh, cmap=cm.gray)

        # distance=ndimage.distance_transform_edt(thresh)
        # local_maxi = feature.peak_local_max(distance, labels=thresh, min_distance=int(0.5*pix_per_um), indices = False)
        # markers = ndimage.label(local_maxi)[0]
        # labels = segmentation.watershed(-distance, markers, mask=thresh)
        # image_label_overlay = color.label2rgb(labels, image=median)
        # # thr_lvl=filters.threshold_otsu(thresh)
        # # thresh = im >= thr_lvl
        # # morphology.remove_small_objects(thresh,min_size=2*pix_per_um,in_place=True)

        w, h = im.shape
        labels = ndimage.label(thresh)[0]
        image_label_overlay = color.label2rgb(labels, image=median)
        out = np.zeros((w, h, 3), dtype=np.double)

        # ax3.imshow(image_label_overlay, cmap=cm.gray)
        ax3.text(0, 0, '%d' % t)

        for k, region in enumerate(measure.regionprops(labels, coordinates='rc', cache=True)):
            # if k!=100: continue
            if region.eccentricity < 0.8: continue
            rp, cp = draw.polygon(region.coords[:, 0], region.coords[:, 1], im.shape)
            # out[rp, cp, :] = (0,1,0)

            # rotate = transform.SimilarityTransform(rotation=np.pi / 2)
            # rotate = transform.SimilarityTransform(rotation=0)
            # rc,cc=rotate(region.centroid)[0]

            rc, cc = region.centroid
            l = region.major_axis_length / 2
            # l_sint, l_cost = np.sin(region.orientation) * l, np.cos(region.orientation) * l

            if region.orientation > 0:
                out[rp, cp, :] = (0, 1, 0)
                l_sint, l_cost = np.sin(region.orientation) * l, np.cos(region.orientation) * l
                xx1, yy1 = cc + l_sint, rc + l_cost  # don't know why, but i had to interchange sin and cos
                xx2, yy2 = cc - l_sint, rc - l_cost
            if region.orientation == 0:
                # log.warning("orientation was zero!")
                out[rp, cp, :] = (1, 1, 1)
                xx1, yy1 = cc + l, rc
                xx2, yy2 = cc - l, rc
            if region.orientation < 0:
                out[rp, cp, :] = (1, 0, 1)
                l_sint, l_cost = np.sin(np.pi - region.orientation) * l, np.cos(np.pi - region.orientation) * l
                xx1, yy1 = cc + l_sint, rc - l_cost  # don't know why, but i had to interchange sin and cos
                xx2, yy2 = cc - l_sint, rc + l_cost
            ax3.plot(xx1, yy1, marker='o', markersize=2, c='red')
            ax3.plot(xx2, yy2, marker='o', markersize=2, c='blue')

        ax3.imshow(out)
        # ax4.set_xlim([0,w])
        # ax4.set_ylim([0,h])

        # lines = probabilistic_hough_line(thresh, threshold=10, line_length=5, line_gap=3)
        # for line in lines:
        #     p0, p1 = line
        #     ax.plot((p0[0], p1[0]), (p0[1], p1[1]))

        return mplfig_to_npimage(fig)  # RGB image of the figure

    _images, pix_per_um, dt = sp.load_tiff(image_path)
    # subtract first frame and deal with negative results after the operation
    frames = np.int32(_images)
    frames -= frames[0]
    frames = frames[1:, :, :]
    frames = np.uint16(frames.clip(0))

    logging.info("rendering movie %s" % filename)
    fig = plt.figure(20, figsize=(10, 10))
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)
    fig.tight_layout()

    animation = mpy.VideoClip(make_frame_mpl, duration=len(frames))
    animation.write_videofile(filename, fps=1)
    animation.close()
    exit()


def obj_function(_df, x, y, radius=10, n=16, ax=None):
    n = 2 ** int(np.log2(n))
    box = Polygon(
        [(x - radius, y - radius), (x - radius, y + radius), (x + radius, y + radius), (x + radius, y - radius)])
    if min(box.bounds) < 0 or min(box.bounds) > 512: return 0

    in_idx = _df['pt1'].apply(lambda pt: pt.within(box)) & _df['pt2'].apply(lambda pt: pt.within(box))
    df = _df[in_idx]
    if len(df) == 0: return 0

    # fill four cuadrants
    cuadrants = list()
    divs_per_cuadrant = int(n / 4)
    for cuadrant, color in zip(range(4), ['red', 'blue', 'green', 'yellow']):
        o = 0
        pn_idx = df['theta'].apply(lambda t: t < 0 if (cuadrant == 0 or cuadrant == 2) else t > 0)
        dc = df[pn_idx]
        for i in range(divs_per_cuadrant):
            ang_i = 2 * np.pi / n * i
            ang_ii = 2 * np.pi / n * (i + 1)
            # build triangle
            c_ang = cuadrant / 2 * np.pi
            tri = Polygon([(x, y),
                           (x + radius * np.cos(ang_i + c_ang), y + radius * np.sin(ang_i + c_ang)),
                           (x + radius * np.cos(ang_ii + c_ang), y + radius * np.sin(ang_ii + c_ang))
                           ])

            in_idx = dc['pt1'].apply(lambda pt: pt.within(tri)) & dc['pt2'].apply(lambda pt: pt.within(tri))

            ang_avg = (ang_ii + ang_i) / 2
            ang_diff = np.abs(ang_ii - ang_i)
            if (cuadrant == 0 or cuadrant == 2): dc.loc[in_idx, 'theta'] += np.pi / 2
            in_ang = dc.loc[in_idx, 'theta'].apply(lambda t: np.abs(t - ang_avg) < ang_diff)
            # o += dc.loc[in_idx & in_ang, 'theta'].sum()
            o += len(dc[in_idx & in_ang])

            if ax is not None:
                # ax.plot(tri.exterior.xy[0], tri.exterior.xy[1], lw=0.1, c=color)
                ax.plot(tri.exterior.xy[0], tri.exterior.xy[1], lw=0.5, c='white')
                # for ix, row in dc[in_idx & in_ang].iterrows():
                #     ax.plot([row['x1'], row['x2']], [row['y1'], row['y2']], lw=1, c='white', alpha=0.3)
        cuadrants.append(o)

    return min(cuadrants)


def detection(images, pix_per_um=1):
    features = pd.DataFrame()

    # subtract first frame and deal with negative results after the operation
    nobkg = np.int32(images)
    nobkg -= nobkg[0]
    nobkg = nobkg[1:, :, :]
    nobkg = np.uint16(nobkg.clip(0))

    # last_frame=np.zeros(frames[0].shape,dtype=bool)
    for num, im in enumerate(nobkg):

        # median=rank.median(image=im, selem=disk(0.2*pix_per_um))
        # thr_lvl=filters.threshold_otsu(median)

        thr_lvl = filters.threshold_otsu(im)
        thresh = im >= thr_lvl
        morphology.remove_small_objects(thresh, min_size=2 * pix_per_um, in_place=True)

        labels = ndimage.label(thresh)[0]
        w, h = im.shape

        for region in measure.regionprops(labels, coordinates='rc', cache=True):
            if region.eccentricity < 0.8: continue

            rc, cc = region.centroid
            l = region.major_axis_length / 2
            if region.orientation > 0:
                l_sint, l_cost = np.sin(region.orientation) * l, np.cos(region.orientation) * l
                xx1, yy1 = cc + l_sint, rc + l_cost  # don't know why, but i had to interchange sin and cos
                xx2, yy2 = cc - l_sint, rc - l_cost
            elif region.orientation == 0:
                # log.warning("orientation was zero!")
                xx1, yy1 = cc + l, rc
                xx2, yy2 = cc - l, rc
            else:
                l_sint, l_cost = np.sin(np.pi - region.orientation) * l, np.cos(np.pi - region.orientation) * l
                xx1, yy1 = cc + l_sint, rc - l_cost  # don't know why, but i had to interchange sin and cos
                xx2, yy2 = cc - l_sint, rc + l_cost

            features = features.append([{'x': rc, 'y': cc,
                                         'pt1': Point((xx1 / pix_per_um, (h - yy1) / pix_per_um)),
                                         'pt2': Point((xx2 / pix_per_um, (h - yy2) / pix_per_um)),
                                         'x1': xx1 / pix_per_um, 'y1': (h - yy1) / pix_per_um,
                                         'x2': xx2 / pix_per_um, 'y2': (h - yy2) / pix_per_um,
                                         'theta': region.orientation, 'frame': num}])

    features['xum'] = features['x'] / pix_per_um
    features['yum'] = features['y'] / pix_per_um
    return features.reset_index(drop=True)


def do_trackpy(image_path):
    _images, pix_per_um, dt = sp.load_tiff(image_path)
    w, h = _images[0].shape[0], _images[0].shape[1]

    f = detection(_images, pix_per_um=pix_per_um)
    # f.to_pickle('f.pandas')
    # f = pd.read_pickle('f.pandas')
    log.info("detection step completed.")

    divs = 20
    x = np.linspace(0, w / pix_per_um, divs)
    y = np.linspace(0, h / pix_per_um, divs)
    obj = np.zeros((x.size, y.size), dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    for i in range(x.size):
        for j in range(y.size):
            print(j, i, )
            obj[j, i] = obj_function(f, xx[j, i], yy[j, i])
    # np.savetxt('obj.csv', obj)
    # obj = np.loadtxt('obj.csv')

    fig = plt.figure()
    ax = fig.gca()
    # obj_function(f, 60, 65, ax=ax)
    ax.imshow(obj, interpolation='none', extent=[0, w / pix_per_um, h / pix_per_um, 0])
    for ix, row in f.iterrows():
        ax.plot([row['x1'], row['x2']], [row['y1'], row['y2']], lw=1, c='white', alpha=0.3)
    for i in range(obj.shape[0]):
        for j in range(obj.shape[1]):
            if obj[j, i] > 10:
                obj_function(f, xx[j, i], yy[j, i], ax=ax)
            # text = ax.text(xx[j, i], yy[j, i], '%d' % obj[j, i], ha="center", va="center", color="w",
            #                fontsize='xx-small')

    ax.set_aspect('equal')
    fig.savefig('objfn.png')

    # fig = plt.figure()
    # ax = fig.gca()
    # for ix, row in f.iterrows():
    #     ax.plot([row['x1'], row['x2']], [row['y1'], row['y2']], lw=1, c='k', alpha=0.3)
    # fig.savefig('linedens.pdf', format='pdf')
    exit()

    # for search_range in [1.0, 1.5, 2.0, 2.5]:
    #     linked = tp.link_df(f, search_range, pos_columns=['xum', 'yum'])
    #     hist, bins = np.histogram(np.bincount(linked.particle.astype(int)),
    #                               bins=np.arange(30), normed=True)
    #     plt.step(bins[1:], hist, label='range = {} microns'.format(search_range))
    # plt.gca().set(ylabel='relative frequency', xlabel='track length (frames)')
    # plt.legend()
    # plt.show()
    # exit()

    search_range = 0.4
    pred = tp.predict.NearestVelocityPredict(initial_guess_vels=0.1)
    # trackpy.linking.Linker.MAX_SUB_NET_SIZE=50
    linked = pred.link_df(f, search_range, pos_columns=['xum', 'yum'])

    #  filter spurious tracks
    frames_per_particle = linked.groupby('particle')['frame'].nunique()
    particles = frames_per_particle[frames_per_particle > 8].index
    linked = linked[linked['particle'].isin(particles)]
    logging.info('filtered %d particles by track length' % linked['particle'].nunique())

    m = tp.imsd(linked, 1, 1, pos_columns=['xum', 'yum'])
    mt = m.ix[15]
    particles = mt[mt > 1].index
    linked = linked[linked['particle'].isin(particles)]
    logging.info('filtered %d particles msd' % linked['particle'].nunique())

    movie(_images, linked, filename='%s.mp4' % image_path[:-4], pix_per_um=pix_per_um)
    # exit()

    return linked


def process_dir(dir_base):
    logging.info('processing data from folder %s' % dir_base)
    df = pd.DataFrame()
    cal = pd.read_excel(p.experiments_dir + 'eb3/eb3_calibration.xls')
    # Traverse through all subdirs looking for image files. When a file is found, assume folder structure of (cond/date)
    for root, directories, files in os.walk(dir_base):
        for f in files:
            mpath = os.path.join(root, f)
            if os.path.isfile(mpath) and f[-4:] == '.tif':
                logging.info('processing file %s in folder %s' % (f, root))
                try:  # process
                    # vis_detection(mpath, filename='%s.mp4' % mpath[:-4])
                    tdf = do_trackpy(mpath)
                    tdf['condition'] = os.path.basename(os.path.dirname(root))
                    tdf['tag'] = f[:-4]
                    # tdf.drop(['mass', 'size', 'ecc', 'signal', 'raw_mass', 'ep'], axis=1, inplace=True)

                    calp = cal[cal['filename'] == f].iloc[0]
                    tdf['time'] = tdf['frame'] * calp['dt']

                    tdf['particle'] = tdf['particle'].astype('int32')
                    tdf['frame'] = tdf['frame'].astype('int32')
                    tdf[['x', 'y', 'xum', 'yum', 'time']] = tdf[['x', 'y', 'xum', 'yum', 'time']].astype('float64')

                    # consider 1.6X magification of optivar system
                    if calp['optivar'] == 'yes':
                        tdf['xum'] /= 1.6
                        tdf['yum'] /= 1.6

                    df.to_csv(os.path.join(root, '%s.csv' % f[:-4]), index=False)
                    df = df.append(tdf)
                except IOError as ioe:
                    logging.warning('could not import due to IO error: %s' % ioe)
                # except Exception as e:
                #     logging.error('skipped file %s' % f)
                #     logging.error(e)

    return df


def optivar_resolution_to_excel(dir_base):
    logging.info('constructing optivar reference from folder %s' % dir_base)
    df = pd.DataFrame()
    # Traverse through all subdirs looking for image files. When a file is found, assume folder structure of (cond/date)
    for root, directories, files in os.walk(dir_base):
        for f in files:
            mpath = os.path.join(root, f)
            if os.path.isfile(mpath) and f[-4:] == '.tif':
                logging.info('file %s in folder %s' % (f, root))
                # i['tag'] = f[10:-4]  # take "Result of" and extension out of the filename
                condition = os.path.basename(os.path.dirname(root))

                with tf.TiffFile(mpath, fastij=True) as tif:
                    has_image_meta = tif.is_imagej is not None
                    has_meta_in_log = np.any([i[-4:] == '.log' for i in os.listdir(root) if f[:-14] in i])
                    if has_image_meta or has_meta_in_log:
                        res = 'n/a'
                        if tif.pages[0].resolution_unit == 'centimeter':
                            # asuming square pixels
                            xr = tif.pages[0].x_resolution
                            res = float(xr[0]) / float(xr[1])  # pixels per cm
                            res = res / 1e4  # pixels per um
                        elif tif.pages[0].imagej_tags.unit == 'micron':
                            # asuming square pixels
                            xr = tif.pages[0].x_resolution
                            res = float(xr[0]) / float(xr[1])  # pixels per um

                        dt = 'n/a'
                        if has_image_meta:
                            dt = tif.pages[0].imagej_tags.finterval
                        elif has_meta_in_log:
                            file_log = [i for i in os.listdir(root) if f[:-14] in i and i[-4:] == '.log'][0]
                            with open(os.path.join(root, file_log), 'r') as log:
                                for line in log:
                                    search = re.search('^Average Timelapse Interval: ([0-9.]+) ms', line)
                                    if search is not None:
                                        dt = eval(search.group(1)) / 1000.0
                        date = os.path.basename(root)
                        i = pd.DataFrame(data=[[condition, date, f, dt, res, 'no']],
                                         columns=['condition', 'date', 'filename', 'dt', 'resolution', 'optivar'])

                        df = df.append(i)

    excel_file = os.path.join(dir_base, 'eb3_calibration.xls')
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df.to_excel(writer, 'calibration', index=False)
    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    worksheet = writer.sheets['calibration']
    float_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'center'})
    center_format = workbook.add_format({'align': 'center'})

    # Set the column width and format.
    worksheet.set_column('A:A', 13)
    worksheet.set_column('B:B', 8)
    worksheet.set_column('C:C', 75)
    worksheet.set_column('D:D', 10, float_format)
    worksheet.set_column('E:E', 10, float_format)
    worksheet.set_column('F:F', 10, center_format)
    writer.save()

    return df


if __name__ == '__main__':
    _fig_size_A3 = (11.7, 16.5)
    _err_kws = {'alpha': 0.3, 'lw': 1}

    # df = optivar_resolution_to_excel('/Users/Fabio/data/lab/eb3')
    df = process_dir(p.experiments_dir + 'eb3')
    df.to_pickle(p.experiments_dir + 'eb3.pandas')
    # df = pd.read_pickle(p.experiments_dir + 'eb3.pandas')

    # process dataframe and render images
    from microtubules.eb3 import run_plots_eb3

    logging.info('filtering using run_plots_eb3.')
    df, df_avg = run_plots_eb3.batch_filter(df)
    logging.info('rendering images.')
    run_plots_eb3.render_image_tracks(df, folder=p.experiments_dir + 'eb3')
