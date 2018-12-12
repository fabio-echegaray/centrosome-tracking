import logging

import seaborn as sns
import pandas as pd
import numpy as np
# noinspection PyUnresolvedReferences
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.ticker as ticker
import matplotlib.lines as mlines
import mechanics as m

from imagej_pandas import ImagejPandas
import plot_special_tools as sp

log = logging.getLogger(__name__)

pt_color = sns.light_palette(sp.SUSSEX_COBALT_BLUE, n_colors=10, reverse=True)[3]
_fig_size_A3 = (11.7, 16.5)
_err_kws = {'alpha': 0.5, 'lw': 0.1}


class Tracks():
    def __init__(self, data):
        self.data = data

    @staticmethod
    def _plot_dist_tracks(df, ax, color='k'):
        sns.lineplot(data=df,
                     x='Time', y='DistCentr',
                     estimator=np.nanmean, err_style=None,
                     lw=2, alpha=1, c=color, ax=ax)
        sns.lineplot(data=df,
                     x='Time', y='DistCentr',
                     units='indiv', estimator=None,
                     lw=0.2, alpha=1, c=color, ax=ax)
        ax.axvline(linewidth=1, linestyle='--', color='k', zorder=50)

    @staticmethod
    def _plot_dist_mean(df, ax, color='k'):
        sns.lineplot(data=df,
                     x='Time', y='DistCentr',
                     estimator=np.nanmean, err_style=None,
                     lw=2, alpha=1, c=color, ax=ax)

    @staticmethod
    def format_axes(ax):
        ax.legend(title=None, loc='upper left')
        ax.xaxis.set_major_locator(ticker.MultipleLocator(60))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(30))
        ax.set_xlabel('time [min]')
        ax.set_ylabel('distance [um]')

    def pSTLC(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of +STLC')

    def nocodazole(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_No10+'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[1])
        df, _ = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_mean(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of Nocodazole (10ng)')
        self.format_axes(ax)

        lbls = [cond[0], '+STLC']
        dhandles = [mlines.Line2D([], [], color=sns.color_palette()[1], linestyle='-', marker=None, label=lbls[0])]
        dhandles.append(mlines.Line2D([], [], color=sns.color_palette()[0], linestyle='-', marker=None, label=lbls[1]))
        ax.legend(dhandles, lbls, loc='upper right')

    def cytochalsinD(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_CyDT'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[1])
        df, _ = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_mean(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of Cytochalsin D')
        self.format_axes(ax)

        lbls = [cond[0], '+STLC']
        dhandles = [mlines.Line2D([], [], color=sns.color_palette()[1], linestyle='-', marker=None, label=lbls[0])]
        dhandles.append(mlines.Line2D([], [], color=sns.color_palette()[0], linestyle='-', marker=None, label=lbls[1]))
        ax.legend(dhandles, lbls, loc='upper right')

    def blebbistatin(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_Bleb'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[1])
        df, _ = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_mean(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of Blebbistatin')
        self.format_axes(ax)

        lbls = [cond[0], '+STLC']
        dhandles = [mlines.Line2D([], [], color=sns.color_palette()[1], linestyle='-', marker=None, label=lbls[0])]
        dhandles.append(mlines.Line2D([], [], color=sns.color_palette()[0], linestyle='-', marker=None, label=lbls[1]))
        ax.legend(dhandles, lbls, loc='upper right')

    def chTog(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_chTOG'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[1])
        df, _ = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_mean(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of ChTog siRNA')
        self.format_axes(ax)

        lbls = [cond[0], '+STLC']
        dhandles = [mlines.Line2D([], [], color=sns.color_palette()[1], linestyle='-', marker=None, label=lbls[0])]
        dhandles.append(mlines.Line2D([], [], color=sns.color_palette()[0], linestyle='-', marker=None, label=lbls[1]))
        ax.legend(dhandles, lbls, loc='upper right')

    def faki(self, ax, centered=False):
        df, cond = self.data.get_condition(['1_FAKI'], centered=centered)
        self._plot_dist_tracks(df, ax, color=sns.color_palette()[1])
        df, _ = self.data.get_condition(['1_P.C.'], centered=centered)
        self._plot_dist_mean(df, ax, color=sns.color_palette()[0])
        ax.set_title('Tracks of FAKi')
        self.format_axes(ax)

        lbls = [cond[0], '+STLC']
        dhandles = [mlines.Line2D([], [], color=sns.color_palette()[1], linestyle='-', marker=None, label=lbls[0])]
        dhandles.append(mlines.Line2D([], [], color=sns.color_palette()[0], linestyle='-', marker=None, label=lbls[1]))
        ax.legend(dhandles, lbls, loc='upper right')


class MSD():
    msd_ylim = [0, 420]

    def __init__(self, data):
        self.data = data

    @staticmethod
    def format_axes(ax, time_minor=5, time_major=15, msd_minor=50, msd_major=100):
        ax.legend(loc='upper left')
        # ax.get_legend().remove()

        ax.set_ylim([0, 600])
        ax.set_xlim([-60, 120])
        ax.xaxis.set_major_locator(ticker.MultipleLocator(time_major))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(time_minor))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(msd_major))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(msd_minor))

        ax.set_ylabel('MSD')
        ax.set_xlabel('time [min]')

    def pSTLC(self, ax):
        df, cond = self.data.get_condition(['1_P.C.'], centered=True)
        df = m.get_msd(df, group='trk', frame='Frame', time='Time', x='CentX', y='CentY')
        df = df.loc[df['msd'].notna(), :]
        df = m._msd_tag(df, time='Time', centrosome_label='CentrLabel')

        sp.set_axis_size(4, 2, ax=ax)
        sns.lineplot(x='Time', y='msd', data=df,
                     style='msd_cat', style_order=['displacing more', 'displacing less'],
                     hue='msd_cat', hue_order=['displacing more', 'displacing less'],
                     estimator=np.nanmean)
        # ax.axvline(x=0, linewidth=1, linestyle='--', color='k', zorder=50)
        ax.set_title('MSD of +STLC')

    def pSTLC_mother_dauther(self, ax):
        df, cond = self.data.get_condition(['mother-daughter'], centered=True)

        msd = m.get_msd(df, group='trk', frame='Frame', time='Time', x='CentX', y='CentY')
        msd = msd.loc[msd['msd'].notna(), :]

        msd.loc[msd['CentrLabel'] == 'A', 'mother'] = 'mother'
        msd.loc[msd['CentrLabel'] == 'B', 'mother'] = 'daugther'

        sns.lineplot(x='Time', y='msd', data=msd,
                     style='mother', style_order=['mother', 'daughter'],
                     hue='mother', hue_order=['mother', 'daughter'], ax=ax)

        sp.set_axis_size(4, 2, ax=ax)
        # ax.axvline(x=0, linewidth=1, linestyle='--', color='k', zorder=50)
        ax.set_title('MSD of +STLC')

    def msd_vs_congression(self, ax):
        _conds = ['1_N.C.', '1_P.C.',
                  '2_CDK1_DA', '2_CDK1_DC', '1_Bleb', 'hset', 'kif25', 'hset+kif25',
                  '2_Kines1', '2_CDK1_DK', '1_DIC', '1_Dynei', '1_CENPF', '1_BICD2',
                  '1_No10+', '1_MCAK', '1_chTOG',
                  '1_CyDT', '1_FAKI', '1_ASUND']

        markers = ['o', 'o',
                   '^', '<', '>', 's', 'X', 'v',
                   's', 'X', 'v', '^', '<', '>',
                   'p', 'P', 'X',
                   'p', 'P', 'X']

        df, conds = self.data.get_condition(_conds)
        colors = [sp.SUSSEX_CORAL_RED, sp.SUSSEX_COBALT_BLUE]
        colors.extend([sp.SUSSEX_GRAPE] * 6)
        colors.extend([sp.SUSSEX_FLINT] * 6)
        colors.extend([sp.SUSSEX_FUSCHIA_PINK] * 3)
        colors.extend([sp.SUSSEX_TURQUOISE] * 3)
        # colortuple = dict(zip(conds, colors))

        df_ = df[df['Time'] <= 100]
        df_msd = ImagejPandas.msd_particles(df_).set_index('Frame').sort_index()
        dfcg = sp._compute_congression(df).set_index('Time').sort_index()
        df_msd_final = pd.DataFrame()
        for _, dfmsd in df_msd.groupby(ImagejPandas.CENTROSOME_INDIV_INDEX):
            cnd = dfmsd.iloc[0]['condition']
            cgr = dfcg[dfcg['condition'] == cnd].iloc[-1]['congress']
            df_it = pd.DataFrame([[dfmsd.iloc[-1]['msd'], cgr, cnd]],
                                 columns=['msd', 'cgr', 'condition'])
            df_msd_final = df_msd_final.append(df_it)

        # inneficient as cgr is repeated for every sample
        df_msd_final = df_msd_final.groupby('condition').mean().reset_index()
        for cnd, m, _color in zip(conds, markers, colors):
            p = df_msd_final[df_msd_final['condition'] == cnd]
            ax.scatter(p['cgr'], p['msd'], c=_color, s=200, label=cnd, marker=m, zorder=1000)

        ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(50))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))
