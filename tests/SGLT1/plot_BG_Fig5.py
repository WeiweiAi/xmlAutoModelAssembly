import sys
import os
sys.path.append('../')
from data_plot import subplots_ajdust, plot_data
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/CellMLV2/'
data_path='C:/Users/wai484/temp/b65/Electrogenic cotransporter/data/'

save_fig = {'save_fig': True, 'fig_format': 'png', 'file_path': path_, 'filename': 'BG_fit_fig5'}
filename = data_path+'Fig5_Parent1992.csv'
filename_BG= path_+'fig5.csv'


subtitle_kwargs={}
fig_cfg = {'num_rows': 1, 'num_cols': 1, 'width':6, 'height':6, 'fig_title': None, 'title_y': 0.98, 'fontsize': 10, 
           'left': 0.145, 'bottom': 0.1, 'right': 0.9, 'top': 0.9, 'wspace': 0.2, 'hspace': 0.2}
fig, axs= subplots_ajdust(fig_cfg, **subtitle_kwargs)

plot_cfg = {}
line_cfg = {}

line_cfg[1] = { 'xdata': (filename,'x'), 'ydata':(filename,'Curve1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'Parent 1992'}
line_cfg[2] = { 'xdata': (filename_BG,'V_E'), 'ydata':(filename_BG,'Ii'),
                'color': 'r', 'linestyle': '-.',  'legend_label': 'BG'}


plot_cfg[1] = {'ylabel': 'i (nA)', 'xlabel': 'V (mV)','show_grid': 'both', 'grid_axis': 'both', 
                'line': [1,2], 'legend': [1,2]}

plot_data(fig, axs, plot_cfg, line_cfg, save_fig)