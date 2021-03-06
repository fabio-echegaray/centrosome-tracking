import itertools
import logging
import math

import numpy as np
import pandas as pd
import matplotlib.axes
import matplotlib.colors
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.colors as colors
from matplotlib.patches import Arc
from matplotlib.ticker import FormatStrFormatter, LinearLocator
from mpl_toolkits.mplot3d import axes3d
import seaborn as sns
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import scipy.stats

import mechanics as m
from tools import stats
from imagej.imagej_pandas import ImagejPandas

logger = logging.getLogger(__name__)

# sussex colors
SUSSEX_FLINT = colors.to_rgb('#013035')
SUSSEX_COBALT_BLUE = colors.to_rgb('#1E428A')
SUSSEX_MID_GREY = colors.to_rgb('#94A596')
SUSSEX_FUSCHIA_PINK = colors.to_rgb('#EB6BB0')
SUSSEX_CORAL_RED = colors.to_rgb('#DF465A')
SUSSEX_TURQUOISE = colors.to_rgb('#00AFAA')
SUSSEX_WARM_GREY = colors.to_rgb('#D6D2C4')
SUSSEX_SUNSHINE_YELLOW = colors.to_rgb('#FFB81C')
SUSSEX_BURNT_ORANGE = colors.to_rgb('#DC582A')
SUSSEX_SKY_BLUE = colors.to_rgb('#40B4E5')

SUSSEX_NAVY_BLUE = colors.to_rgb('#1B365D')
SUSSEX_CHINA_ROSE = colors.to_rgb('#C284A3')
SUSSEX_POWDER_BLUE = colors.to_rgb('#7DA1C4')
SUSSEX_GRAPE = colors.to_rgb('#5D3754')
SUSSEX_CORN_YELLOW = colors.to_rgb('#F2C75C')
SUSSEX_COOL_GREY = colors.to_rgb('#D0D3D4')
SUSSEX_DEEP_AQUAMARINE = colors.to_rgb('#487A7B')


# SUSSEX_NEON_BLUE=''
# SUSSEX_NEON_BRIGHT_ORANGE=''
# SUSSEX_NEON_GREEN=''
# SUSSEX_NEON_LIGHT_ORANGE=''
# SUSSEX_NEON_YELLOW=''
# SUSSEX_NEON_SALMON=''
# SUSSEX_NEON_PINK=''

class colors():
    alexa_488 = [.29, 1., 0]
    alexa_594 = [1., .61, 0]
    alexa_647 = [.83, .28, .28]
    hoechst_33342 = [0, .57, 1.]
    red = [1, 0, 0]
    green = [0, 1, 0]
    blue = [0, 0, 1]
    sussex_flint = colors.to_rgb('#013035')
    sussex_cobalt_blue = colors.to_rgb('#1e428a')
    sussex_mid_grey = colors.to_rgb('#94a596')
    sussex_fuschia_pink = colors.to_rgb('#eb6bb0')
    sussex_coral_red = colors.to_rgb('#df465a')
    sussex_turquoise = colors.to_rgb('#00afaa')
    sussex_warm_grey = colors.to_rgb('#d6d2c4')
    sussex_sunshine_yellow = colors.to_rgb('#ffb81c')
    sussex_burnt_orange = colors.to_rgb('#dc582a')
    sussex_sky_blue = colors.to_rgb('#40b4e5')

    sussex_navy_blue = colors.to_rgb('#1b365d')
    sussex_china_rose = colors.to_rgb('#c284a3')
    sussex_powder_blue = colors.to_rgb('#7da1c4')
    sussex_grape = colors.to_rgb('#5d3754')
    sussex_corn_yellow = colors.to_rgb('#f2c75c')
    sussex_cool_grey = colors.to_rgb('#d0d3d4')
    sussex_deep_aquamarine = colors.to_rgb('#487a7b')


class MyAxes3D(axes3d.Axes3D):
    def __init__(self, baseObject, sides_to_draw):
        self.__class__ = type(baseObject.__class__.__name__,
                              (self.__class__, baseObject.__class__),
                              {})
        self.__dict__ = baseObject.__dict__
        self.sides_to_draw = list(sides_to_draw)
        self.mouse_init()

    def set_some_features_visibility(self, visible):
        for t in self.w_zaxis.get_ticklines() + self.w_zaxis.get_ticklabels():
            t.set_visible(visible)
        self.w_zaxis.line.set_visible(visible)
        self.w_zaxis.pane.set_visible(visible)
        self.w_zaxis.label.set_visible(visible)

    def draw(self, renderer):
        # set visibility of some features False
        self.set_some_features_visibility(False)
        # draw the axes
        super(MyAxes3D, self).draw(renderer)
        # set visibility of some features True.
        # This could be adapted to set your features to desired visibility,
        # e.g. storing the previous values and restoring the values
        self.set_some_features_visibility(True)

        zaxis = self.zaxis
        draw_grid_old = zaxis.axes._draw_grid
        # disable draw grid
        zaxis.axes._draw_grid = False

        tmp_planes = zaxis._PLANES

        if 'l' in self.sides_to_draw:
            # draw zaxis on the left side
            zaxis._PLANES = (tmp_planes[2], tmp_planes[3],
                             tmp_planes[0], tmp_planes[1],
                             tmp_planes[4], tmp_planes[5])
            zaxis.draw(renderer)
        if 'r' in self.sides_to_draw:
            # draw zaxis on the right side
            zaxis._PLANES = (tmp_planes[3], tmp_planes[2],
                             tmp_planes[1], tmp_planes[0],
                             tmp_planes[4], tmp_planes[5])
            zaxis.draw(renderer)

        zaxis._PLANES = tmp_planes

        # disable draw grid
        zaxis.axes._draw_grid = draw_grid_old


def set_axis_size(w, h, ax=None):
    """ w, h: width, height in inches """
    if not ax: ax = plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w) / (r - l)
    figh = float(h) / (t - b)
    ax.figure.set_size_inches(figw, figh)


def _compute_congression(cg):
    # compute congression signal
    cg['cgr'] = 0
    _cg = pd.DataFrame()
    for id, idf in cg.groupby(ImagejPandas.NUCLEI_INDIV_INDEX):
        time_of_c, frame_of_c, dist_of_c = ImagejPandas.get_contact_time(idf, ImagejPandas.DIST_THRESHOLD)
        if frame_of_c is not None and frame_of_c > 0:
            idf.loc[idf['Frame'] >= frame_of_c, 'cgr'] = 1
        _cg = _cg.append(idf)
    cg = _cg

    cg = cg[cg['CentrLabel'] == 'A']

    dfout = pd.DataFrame()
    for id, cdf in cg.groupby('condition'):
        total_centrosome_pairs = float(len(cdf['indiv'].unique()))
        cdf = cdf.set_index(['indiv', 'Time']).sort_index()
        cgr1_p = cdf['cgr'].unstack('indiv').fillna(method='ffill').sum(axis=1) / total_centrosome_pairs * 100.0
        cgr1_p = cgr1_p.reset_index().rename(index=str, columns={0: 'congress'})
        cgr1_p['condition'] = id
        dfout = dfout.append(cgr1_p)

    return dfout


def congression(cg, ax=None, order=None, linestyles=None):
    # plot centrosome congression as %
    # get congression signal
    cgs = _compute_congression(cg)
    palette = itertools.cycle(sns.color_palette())

    ax = ax if ax is not None else plt.gca()
    order = order if order is not None else cg['condition'].unique()

    dhandles, dlabels = list(), list()
    for id in order:
        cdf = cgs[cgs['condition'] == id]
        # PLOT centrosome congresion
        _color = matplotlib.colors.to_hex(next(palette))
        cgri = cdf.set_index('Time').sort_index()
        ls = linestyles[id] if linestyles is not None else None
        cgri.plot(y='congress', drawstyle='steps-pre', color=_color, linestyle=ls, lw=1, ax=ax)
        dlbl = '%s' % (id)
        dhandles.append(mlines.Line2D([], [], color=_color, linestyle=ls, marker=None, label=dlbl))
        dlabels.append(dlbl)

    _xticks = range(0, int(cgs['Time'].max()), 20)
    ax.set_xticks(_xticks)
    ax.set_xlabel('Time $[min]$')
    ax.set_ylabel('Congression in percentage ($d<%0.2f$ $[\mu m]$)' % ImagejPandas.DIST_THRESHOLD)
    ax.legend(dhandles, dlabels, loc='upper left')


def anotated_boxplot(df, variable, point_size=5, fontsize=None, group='condition', repeat_grp=None,
                     swarm=True, stars=False, order=None, xlabels=None, rotation='horizontal', ax=None):
    sns.boxplot(data=df, y=variable, x=group, linewidth=0.5, width=0.4, fliersize=0, order=order, ax=ax,
                zorder=100)

    plt_kws = {'zorder': 10, 'ax': ax}
    if swarm:
        fn = sns.swarmplot
    else:
        fn = sns.stripplot
        plt_kws['jitter'] = True

    # if repeat_grp is not None:
    #     markers = ['o', 'p', '^', 's', 'v', '<', 'x', ]
    #     for c, f in df.groupby(repeat_grp):
    #         _ax = fn(data=f, y=variable, x=group, size=point_size, order=order, marker=markers[c], **plt_kws)
    # else:
    #     _ax = fn(data=df, y=variable, x=group, size=point_size, order=order, **plt_kws)
    _ax = fn(data=df, y=variable, x=group, hue=repeat_grp, size=point_size, order=order, **plt_kws)

    for i, artist in enumerate(_ax.artists):
        artist.set_facecolor('None')
        artist.set_edgecolor('k')
        artist.set_zorder(5000)
    for i, artist in enumerate(_ax.lines):
        artist.set_color('k')
        artist.set_zorder(5000)

    order = order if order is not None else df[group].unique()
    if fontsize is not None:
        for x, c in enumerate(order):
            d = df[df[group] == c][variable]
            _max_y = _ax.axis()[3]
            count = d.count()
            mean = d.mean()
            median = d.median()
            # _txt = '%0.2f\n%0.2f\n%d' % (mean, median, count)
            _txt = '%0.2f\n%d' % (median, count)
            _ax.text(x, _max_y * -0.7, _txt, rotation=rotation, ha='center', va='bottom', fontsize=fontsize)
    # print [i.get_text() for i in _ax.xaxis.get_ticklabels()]
    if xlabels is not None:
        _ax.set_xticklabels([xlabels[tl.get_text()] for tl in _ax.xaxis.get_ticklabels()],
                            rotation=rotation, multialignment='right')
    else:
        _ax.set_xticklabels(_ax.xaxis.get_ticklabels(), multialignment='right')
    _ax.set_xlabel('')
    # Pad margins so that markers don't get clipped by the axes
    plt.margins(0.1)

    if stars:
        maxy = ax.get_ylim()[1]
        ypos = np.flip(ax.yaxis.get_major_locator().tick_values(maxy, maxy * 0.8))
        dy = -np.diff(ypos)[0]
        k = 0
        for i, s11 in enumerate(order):
            for j, s12 in enumerate(order):
                if i < j:
                    sig1 = df[df[group] == s11][variable]
                    sig2 = df[df[group] == s12][variable]
                    st, p = scipy.stats.ttest_ind(sig1, sig2)
                    # st, p = scipy.stats.mannwhitneyu(sig1, sig2, use_continuity=False, alternative='two-sided')
                    # if p <= 0.05:
                    ypos = maxy - dy * k
                    _ax.plot([i, j], [ypos, ypos], lw=0.75, color='k', zorder=20)
                    _ax.text(j, ypos + dy * 0.25, stats.star_system(p), ha='right', va='bottom',
                             fontsize=fontsize, zorder=20)
                    k += 1

    return _ax


def ribbon(df, ax, ribbon_width=0.75, n_indiv=8, indiv_cols=range(8), z_max=None):
    right_axes_class = (str(type(ax)) == "<class 'matplotlib.axes._subplots.Axes3DSubplot'>") or \
                       (str(type(ax)) == "<class 'plot_special_tools.Axes3DSubplot'>")

    if not right_axes_class:
        raise Exception('Not the right axes class for ribbon plot.')
    if df['condition'].unique().size > 1:
        raise Exception('Ribbon plot needs just one condition.')
    if len(indiv_cols) != n_indiv:
        if len(indiv_cols) != 8:
            raise Exception('Number of individuals and pick must match.')
        else:
            indiv_cols = range(n_indiv)
    # extract data
    df = df[df['CentrLabel'] == 'A']
    time_series = sorted(df['Time'].unique())
    df = df.set_index(['Time', 'indv']).sort_index()
    dmat = df['DistCentr'].unstack('indv').as_matrix()
    x = np.array(time_series)
    y = np.linspace(1, n_indiv, n_indiv)
    z = dmat[:, indiv_cols]

    numPts = x.shape[0]
    numSets = y.shape[0]
    # print x.shape, y.shape, z.shape, np.max(np.nan_to_num(z))

    # create facet color matrix
    _time_color_grad = sns.color_palette('coolwarm', len(time_series))
    _colors = np.empty((len(time_series), len(time_series)), dtype=tuple)
    for cy in range(len(time_series)):
        for cx in range(len(time_series)):
            _colors[cx, cy] = _time_color_grad[cx]

    zmax = z_max if z_max is not None else df['DistCentr'].max()

    # plot each "ribbon" as a surface plot with a certain width
    for i in np.arange(0, numSets):
        X = np.vstack((x, x)).T
        Y = np.ones((numPts, 2)) * i
        Y[:, 1] = Y[:, 0] + ribbon_width
        Z = np.vstack((z[:, i], z[:, i])).T
        surf = ax.plot_surface(X, Y, Z, vmax=zmax, rstride=1, cstride=1, facecolors=_colors,
                               edgecolors='k', alpha=0.8, linewidth=0.25)

    ax.set_facecolor('white')

    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    ax.set_title(df['condition'].unique()[0])

    ax.set_xlabel('Time $[min]$', labelpad=20)
    ax.set_ylabel('Track', labelpad=15)
    ax.set_zlabel('Distance between centrosomes $[\mu m]$', labelpad=10)

    ax.set_ylim((0, numSets + 1))

    xticks = np.arange(0, np.max(time_series), 20)
    ax.set_xticks(xticks)
    ax.set_xticklabels(['%d' % t for t in xticks])

    yticks = np.arange(1, n_indiv, 2)
    ax.set_yticks(yticks)
    ax.set_yticklabels(['%d' % t for t in yticks])

    zticks = np.arange(0, zmax, 10)
    ax.set_zlim3d(0, zmax)
    ax.set_zticks(zticks)
    ax.set_zticklabels(['%d' % t for t in zticks])


def msd_indivs(df, ax, time='Time', ylim=None):
    if df.empty:
        raise Exception('Need non-empty dataframe..')
    if df['condition'].unique().size > 1:
        raise Exception('Need just one condition for using this plotting function.')

    _err_kws = {'alpha': 0.5, 'lw': 0.1}
    cond = df['condition'].unique()[0]
    df_msd = ImagejPandas.msd_particles(df)
    df_msd = m._msd_tag(df_msd)

    sns.tsplot(
        data=df_msd[df_msd['condition'] == cond], lw=3,
        err_style=['unit_traces'], err_kws=_err_kws,
        time=time, value='msd', unit='indv', condition='msd_cat', estimator=np.nanmean, ax=ax)
    ax.set_title(cond)
    ax.set_ylabel('Mean Square Displacement (MSD) $[\mu m^2]$')
    ax.legend(title=None, loc='upper left')
    if time == 'Frame':
        ax.set_xlabel('Time delay $[frames]$')
        ax.set_xticks(range(0, df['Frame'].max(), 5))
        ax.set_xlim([0, df['Frame'].max()])
    else:
        ax.set_xlabel('Time delay $[min]$')
    if ylim is not None:
        ax.set_ylim(ylim)


def msd(df, ax, time='Time', ylim=None, color='k'):
    if df.empty:
        raise Exception('Need non-empty dataframe..')
    if df['condition'].unique().size > 1:
        raise Exception('Need just one condition for using this plotting function.')

    cond = df['condition'].unique()[0]
    df_msd = ImagejPandas.msd_particles(df)
    df_msd = m._msd_tag(df_msd)

    sns.tsplot(data=df_msd[df_msd['msd_cat'] == cond + ' displacing more'],
               color=color, linestyle='-',
               time=time, value='msd', unit='indv', condition='msd_cat', estimator=np.nanmean, ax=ax)
    sns.tsplot(data=df_msd[df_msd['msd_cat'] == cond + ' displacing less'],
               color=color, linestyle='--',
               time=time, value='msd', unit='indv', condition='msd_cat', estimator=np.nanmean, ax=ax)
    ax.set_title(cond)
    ax.set_ylabel('Mean Square Displacement (MSD) $[\mu m^2]$')
    ax.set_xticks(np.arange(0, df_msd['Time'].max(), 20.0))
    ax.legend(title=None, loc='upper left')
    if time == 'Frame':
        ax.set_xlabel('Time delay $[frames]$')
        ax.set_xticks(range(0, df['Frame'].max(), 5))
        ax.set_xlim([0, df['Frame'].max()])
    else:
        ax.set_xlabel('Time delay $[min]$')
    if ylim is not None:
        ax.set_ylim(ylim)


def distance_to_nuclei_center(df, ax, mask=None, time_contact=None, plot_interp=False):
    pal = sns.color_palette()
    nucleus_id = df['Nuclei'].min()

    dhandles, dlabels = list(), list()
    for k, [(centr_lbl), _df] in enumerate(df.groupby(['Centrosome'])):
        track = _df.set_index('Time').sort_index()
        color = pal[k % len(pal)]
        dlbl = 'N%d-C%d' % (nucleus_id, centr_lbl)
        dhandles.append(mlines.Line2D([], [], color=color, marker=None, label=dlbl))
        dlabels.append(dlbl)

        if mask is not None and not mask.empty:
            tmask = mask[mask['Centrosome'] == centr_lbl].set_index('Time').sort_index()
            orig = track.loc[tmask.index, 'Dist'][tmask['Dist']]
            if len(orig) > 0:
                orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
            if plot_interp:
                interp = track['Dist'][~tmask['Dist']]
                if len(interp) > 0:
                    interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
                track['Dist'].plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)
            else:
                orig.plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)
        else:
            print('plotting distance to nuclei with no mask.')
            track['Dist'].plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.legend(dhandles, dlabels, loc='upper right')
    ax.set_ylabel('Distance to\nnuclei center $[\mu m]$')


def distance_to_cell_center(df, ax, mask=None, time_contact=None, plot_interp=False):
    pal = sns.color_palette()
    nucleus_id = df['Nuclei'].min()

    dhandles, dlabels = list(), list()
    for k, [(centr_lbl), _df] in enumerate(df.groupby(['Centrosome'])):
        track = _df.set_index('Time').sort_index()
        color = pal[k % len(pal)]
        dlbl = 'N%d-C%d' % (nucleus_id, centr_lbl)
        dhandles.append(mlines.Line2D([], [], color=color, marker=None, label=dlbl))
        dlabels.append(dlbl)

        if mask is not None and not mask.empty:
            tmask = mask[mask['Centrosome'] == centr_lbl].set_index('Time').sort_index()
            orig = track.loc[tmask.index, 'DistCell'][tmask['DistCell']]
            if len(orig) > 0:
                orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
            if plot_interp:
                interp = track['DistCell'][~tmask['DistCell']]
                if len(interp) > 0:
                    interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
                track['Dist'].plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)
            else:
                orig.plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)
        else:
            print('plotting distance to cell center with no mask.')
            track['DistCell'].plot(ax=ax, label=dlbl, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.legend(dhandles, dlabels, loc='upper right')
    ax.set_ylabel('Distance to\ncell center $[\mu m]$')


def distance_between_centrosomes(df, ax, mask=None, time_contact=None):
    color = sns.color_palette()[0]
    track = df.set_index('Time').sort_index()

    if mask is not None and not mask.empty:
        tmask = mask[mask['CentrLabel'] == 'A'].set_index('Time').sort_index()
        orig = track['DistCentr'][tmask['DistCentr']]
        interp = track['DistCentr'][~tmask['DistCentr']]
        if len(orig) > 0:
            orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
        if len(interp) > 0:
            interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
    else:
        print('plotting distance between centrosomes with no mask.')
    track['DistCentr'].plot(ax=ax, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.set_ylabel('Distance between\ncentrosomes $[\mu m]$')
    ax.set_ylim([0, max(ax.get_ylim())])


def speed_to_nucleus(df, ax, mask=None, time_contact=None):
    pal = sns.color_palette()
    nucleus_id = df['Nuclei'].min()

    dhandles, dlabels = list(), list()
    for k, [(lbl_centr), _df] in enumerate(df.groupby(['Centrosome'])):
        track = _df.set_index('Time').sort_index()
        color = pal[k % len(pal)]
        dlbl = 'N%d-C%d' % (nucleus_id, lbl_centr)
        dhandles.append(mlines.Line2D([], [], color=color, marker=None, label=dlbl))
        dlabels.append(dlbl)

        if mask is not None and not mask.empty:
            tmask = mask[mask['Centrosome'] == lbl_centr].set_index('Time').sort_index()
            orig = track.loc[tmask.index, 'Speed'][tmask['Speed']]
            interp = track['Speed'][~tmask['Speed']]
            if len(orig) > 0:
                orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
            if len(interp) > 0:
                interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
        else:
            print('plotting speed to nuclei with no mask.')
        track['Speed'].plot(ax=ax, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.legend(dhandles, dlabels, loc='upper right')
    ax.set_ylabel('Speed to\nnuclei $\\left[\\frac{\mu m}{min} \\right]$')


def speed_between_centrosomes(df, ax, mask=None, time_contact=None):
    color = sns.color_palette()[0]
    track = df.set_index('Time').sort_index()

    if mask is not None and not mask.empty:
        tmask = mask[mask['CentrLabel'] == 'A'].set_index('Time').sort_index()
        orig = track['SpeedCentr'][tmask['SpeedCentr']]
        interp = track['SpeedCentr'][~tmask['SpeedCentr']]
        if len(orig) > 0:
            orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
        if len(interp) > 0:
            interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
    else:
        print('plotting speed between centrosomes with no mask.')
    track['SpeedCentr'].plot(ax=ax, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.set_ylabel('Speed between\ncentrosomes $\\left[\\frac{\mu m}{min} \\right]$')


def acceleration_to_nucleus(df, ax, mask=None, time_contact=None):
    pal = sns.color_palette()
    nucleus_id = df['Nuclei'].min()

    dhandles, dlabels = list(), list()
    for k, [(lbl_centr), _df] in enumerate(df.groupby(['Centrosome'])):
        track = _df.set_index('Time').sort_index()
        color = pal[k % len(pal)]
        dlbl = 'N%d-C%d' % (nucleus_id, lbl_centr)
        dhandles.append(mlines.Line2D([], [], color=color, marker=None, label=dlbl))
        dlabels.append(dlbl)

        if mask is not None and not mask.empty:
            tmask = mask[mask['Centrosome'] == lbl_centr].set_index('Time').sort_index()
            orig = track.loc[tmask.index, 'Acc'][tmask['Acc']]
            interp = track['Acc'][~tmask['Acc']]
            if len(orig) > 0:
                orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
            if len(interp) > 0:
                interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
        else:
            print('plotting acceleration to nuclei with no mask.')
        track['Acc'].plot(ax=ax, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.legend(dhandles, dlabels, loc='upper right')
    ax.set_ylabel('Acceleration relative\nto nuclei $\\left[\\frac{\mu m}{min^2} \\right]$')


def plot_acceleration_between_centrosomes(df, ax, mask=None, time_contact=None):
    color = sns.color_palette()[0]
    track = df.set_index('Time').sort_index()

    if mask is not None and not mask.empty:
        tmask = mask[mask['CentrLabel'] == 'A'].set_index('Time').sort_index()
        orig = track['AccCentr'][tmask['AccCentr']]
        interp = track['AccCentr'][~tmask['AccCentr']]
        if len(orig) > 0:
            orig.plot(ax=ax, label='Original', marker='o', markersize=3, linewidth=0, c=color)
        if len(interp) > 0:
            interp.plot(ax=ax, label='Interpolated', marker='<', linewidth=0, c=color)
    else:
        print('plotting acceleration between centrosomes with no mask.')
    track['AccCentr'].plot(ax=ax, marker=None, sharex=True, c=color)

    # plot time of contact
    if time_contact is not None:
        ax.axvline(x=time_contact, color='dimgray', linestyle='--')
        ax.axvline(x=time_contact - ImagejPandas.TIME_BEFORE_CONTACT, color='lightgray', linestyle='--')

    ax.set_ylabel('Acceleration between\ncentrosomes $\\left[\\frac{\mu m}{min^2} \\right]$')


def render_cell(df, ax, img=None, res=4.5, w=50, h=50):
    """
    Render an individual cell with all its measured features
    """
    from skimage import exposure

    # plot image
    if img is not None:
        img = exposure.equalize_hist(img)
        img = exposure.adjust_gamma(img, gamma=3)
        ax.imshow(img, cmap='gray', extent=(0, img.shape[0] / res, img.shape[1] / res, 0))
    # if img is not None: ax.imshow(img, cmap='gray')

    _ca = df[df['CentrLabel'] == 'A']
    _cb = df[df['CentrLabel'] == 'B']

    if not _ca['NuclBound'].empty:
        nucleus = Polygon(eval(_ca['NuclBound'].values[0][1:-1]))

        nuc_center = nucleus.centroid
        x, y = nucleus.exterior.xy
        ax.plot(x, y, color=SUSSEX_CORN_YELLOW, linewidth=1, solid_capstyle='round')
        ax.plot(nuc_center.x, nuc_center.y, color=SUSSEX_CORN_YELLOW, marker='+', linewidth=1, solid_capstyle='round',
                zorder=1)

    if not _ca['CellBound'].empty:
        cell = Polygon(eval(_ca['CellBound'].values[0])) if not _ca['CellBound'].empty > 0 else None

        cll_center = cell.centroid
        x, y = cell.exterior.xy
        ax.plot(x, y, color='w', linewidth=1, solid_capstyle='round')
        ax.plot(cll_center.x, cll_center.y, color='w', marker='o', linewidth=1, solid_capstyle='round')

    if not _ca['CentX'].empty:
        c_a = Point(_ca['CentX'], _ca['CentY'])
        ca = plt.Circle((c_a.x, c_a.y), radius=1, edgecolor=SUSSEX_NAVY_BLUE, facecolor='none', linewidth=2, zorder=10)
        ax.add_artist(ca)

        if not _cb['CentX'].empty:
            c_b = Point(_cb['CentX'], _cb['CentY'])
            cb = plt.Circle((c_b.x, c_b.y), radius=1, edgecolor=SUSSEX_CORAL_RED, facecolor='none', linewidth=2,
                            zorder=10)
            ax.plot((c_a.x, c_b.x), (c_a.y, c_b.y), color=SUSSEX_WARM_GREY, linewidth=1, zorder=10)
            ax.add_artist(cb)

    ax.set_xlim(c_a.x - w / 2, c_a.x + w / 2)
    ax.set_ylim(c_a.y - h / 2 + 10, c_a.y + h / 2 + 10)
    # ax.set_xlim(nuc_center.x - w / 2, nuc_center.x + w / 2)
    # ax.set_ylim(nuc_center.y - h / 2, nuc_center.y + h / 2)


# functions for plotting angle in matplotlib
def get_angle_text(angle_plot):
    angle = angle_plot.get_label()[:-1]  # Excluding the degree symbol
    angle = "%0.2f" % float(angle) + u"\u00b0"  # Display angle upto 2 decimal places

    # Get the vertices of the angle arc
    vertices = angle_plot.get_verts()

    # Get the midpoint of the arc extremes
    x_width = (vertices[0][0] + vertices[-1][0]) / 2.0
    y_width = (vertices[0][5] + vertices[-1][6]) / 2.0

    # print x_width, y_width

    separation_radius = max(x_width / 2.0, y_width / 2.0)

    return [x_width + separation_radius, y_width + separation_radius, angle]


def get_angle_plot(line1, line2, offset=1, color=None, origin=[0, 0], len_x_axis=1, len_y_axis=1):
    l1xy = line1.get_xydata()

    # Angle between line1 and x-axis
    slope1 = (l1xy[1][1] - l1xy[0][2]) / float(l1xy[1][0] - l1xy[0][0])
    angle1 = abs(math.degrees(math.atan(slope1)))  # Taking only the positive angle

    l2xy = line2.get_xydata()

    # Angle between line2 and x-axis
    slope2 = (l2xy[1][3] - l2xy[0][4]) / float(l2xy[1][0] - l2xy[0][0])
    angle2 = abs(math.degrees(math.atan(slope2)))

    theta1 = min(angle1, angle2)
    theta2 = max(angle1, angle2)

    angle = theta2 - theta1

    if color is None:
        color = line1.get_color()  # Uses the color of line 1 if color parameter is not passed.

    return Arc(origin, len_x_axis * offset, len_y_axis * offset, 0, theta1, theta2, color=color,
               label=str(angle) + u"\u00b0")
