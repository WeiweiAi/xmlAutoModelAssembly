import sys
import os
sys.path.append('../')
from data_plot import subplots_ajdust, plot_data
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/CellMLV2/'
data_path='C:/Users/wai484/temp/b65/Electrogenic cotransporter/data/'

save_fig = {'save_fig': True, 'fig_format': 'png', 'file_path': path_, 'filename': 'BG_fit_fig10'}
filename_50 = data_path+'Fig10_Parent1992_50mV.csv'
filename_150 = data_path+'Fig10_Parent1992_150mV.csv'
filename_BG_150 = path_+'report_task_SGLT1_BG_step_fig10_150mV_post.csv'
filename_BG_50 = path_+'report_task_SGLT1_BG_step_fig10_50mV_post.csv'


subtitle_kwargs={}
fig_cfg = {'num_rows': 1, 'num_cols': 1, 'width':6, 'height':6, 'fig_title': None, 'title_y': 0.98, 'fontsize': 10, 
           'left': 0.145, 'bottom': 0.1, 'right': 0.9, 'top': 0.9, 'wspace': 0.2, 'hspace': 0.2}
fig, axs= subplots_ajdust(fig_cfg, **subtitle_kwargs)

plot_cfg = {}
line_cfg = {}

line_cfg[1] = { 'xdata': (filename_50,'x'), 'ydata':(filename_50,'Curve1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'Parent 1992 50mV'}
line_cfg[2] = { 'xdata': (filename_150,'x'), 'ydata':(filename_150,'Curve1'),
                'color': 'k', 'linestyle': '-.',  'legend_label': 'Parent 1992 -150mV'}
line_cfg[3] = { 'xdata': (filename_BG_50,'tms'), 'ydata':(filename_BG_50,'Ii'),
                'color': 'b', 'linestyle': '--',  'legend_label': 'BG 50mV'}
line_cfg[4] = { 'xdata': (filename_BG_150,'tms'), 'ydata':(filename_BG_150,'Ii'),
                'color': 'r', 'linestyle': '--',  'legend_label': 'BG -150mV'}

plot_cfg[1] = {'ylabel': 'i (nA)', 'xlabel': 'Time (ms)','show_grid': 'both', 'grid_axis': 'both',  'ylim': [-500, 1500], 'xlim': [0, 80],
                'line': [1,2,3,4], 'legend': [1,2,3,4]}

plot_data(fig, axs, plot_cfg, line_cfg, save_fig)