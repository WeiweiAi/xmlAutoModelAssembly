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
filename_50_sugar = data_path+'Fig10_Parent1992_50mV_sugar.csv'
filename_150_sugar = data_path+'Fig10_Parent1992_150mV_sugar.csv'
filename_BG_150_sugar = path_+'report_task_SGLT1_BG_step_fig10_150mV_sugar_post.csv'
filename_BG_50_sugar = path_+'report_task_SGLT1_BG_step_fig10_50mV_sugar_post.csv'


subtitle_kwargs={}
fig_cfg = {'num_rows': 1, 'num_cols': 2, 'width':8, 'height':4, 'fig_title': None, 'title_y': 0.98, 'fontsize': 8, 
           'left': 0.1, 'bottom': 0.25, 'right': 0.95, 'top': 0.95, 'wspace': 0.25, 'hspace': 0.2}
fig, axs= subplots_ajdust(fig_cfg, **subtitle_kwargs)

plot_cfg = {}
line_cfg = {}

line_cfg[1] = { 'xdata': (filename_50,'x'), 'ydata':(filename_50,'Curve1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'Parent et al. (1992a) @50mV'}
line_cfg[2] = { 'xdata': (filename_150,'x'), 'ydata':(filename_150,'Curve1'),
                'color': 'k', 'linestyle': '-.',  'legend_label': 'Parent et al. (1992a) @-150mV'}
line_cfg[3] = { 'xdata': (filename_BG_50,'tms'), 'ydata':(filename_BG_50,'Ii'),
                'color': 'b', 'linestyle': '--',  'legend_label': 'Bond graph @50mV'}
line_cfg[4] = { 'xdata': (filename_BG_150,'tms'), 'ydata':(filename_BG_150,'Ii'),
                'color': 'r', 'linestyle': '--',  'legend_label': 'Bond graph @-150mV'}
line_cfg[5] = { 'xdata': (filename_50_sugar,'x'), 'ydata':(filename_50_sugar,'Curve1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'Parent et al. (1992a) @50mV'}
line_cfg[6] = { 'xdata': (filename_150_sugar,'x'), 'ydata':(filename_150_sugar,'Curve1'),
                'color': 'k', 'linestyle': '-.',  'legend_label': 'Parent et al. (1992a) @-150mV'}
line_cfg[7] = { 'xdata': (filename_BG_50_sugar,'tms'), 'ydata':(filename_BG_50_sugar,'Ii'),
                'color': 'b', 'linestyle': '--',  'legend_label': 'Bond graph @50mV'}
line_cfg[8] = { 'xdata': (filename_BG_150_sugar,'tms'), 'ydata':(filename_BG_150_sugar,'Ii'),
                'color': 'r', 'linestyle': '--',  'legend_label': 'Bond graph @-150mV'}

plot_cfg[1] = {'ylabel': 'i (nA)', 'xlabel': 'Time (ms)','show_grid': 'both', 'grid_axis': 'both',  'ylim': [-500, 1500], 'xlim': [0, 80],
                'line': [1,2,3,4], 'legend': [1,2,3,4], 'title': '(a) Before the addition of sugar','title_y': -0.25}
plot_cfg[2] = {'ylabel': 'i (nA)', 'xlabel': 'Time (ms)','show_grid': 'both', 'grid_axis': 'both',  'ylim': [-500, 400], 'xlim': [0, 80],
                'line': [5,6,7,8], 'legend': [5,6,7,8], 'title': '(b) After the addition of sugar','title_y': -0.25}

plot_data(fig, axs, plot_cfg, line_cfg, save_fig)