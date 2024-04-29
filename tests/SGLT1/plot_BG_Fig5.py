import sys
import os
sys.path.append('../')
from data_plot import subplots_ajdust, plot_data
path_='C:/Users/wai484/temp/b65/Electrogenic cotransporter/CellMLV2/'
data_path='C:/Users/wai484/temp/b65/Electrogenic cotransporter/data/'

save_fig = {'save_fig': True, 'fig_format': 'png', 'file_path': path_, 'filename': 'BG_fit_fig5'}
filename = data_path+'Fig5_Parent1992.csv'
filename_BG= path_+'fig5.csv'
filename_ss= path_+'fig5_ss.csv'
filename_BG_fast= path_+'fig5_BG_fast.csv'
filename_ss_fast= path_+'fig5_ss_fast.csv'


subtitle_kwargs={}
fig_cfg = {'num_rows': 1, 'num_cols': 2, 'width':8, 'height':4, 'fig_title': None, 'title_y': 0.98, 'fontsize': 10, 
           'left': 0.1, 'bottom': 0.15, 'right': 0.95, 'top': 0.9, 'wspace': 0.28, 'hspace': 0.2}
fig, axs= subplots_ajdust(fig_cfg, **subtitle_kwargs)

plot_cfg = {}
line_cfg = {}

line_cfg[1] = { 'xdata': (filename,'x'), 'ydata':(filename,'Curve1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'Parent et al. (1992a)'}
line_cfg[2] = { 'xdata': (filename_BG,'V_E'), 'ydata':(filename_BG,'Ii'),
                'color': 'r', 'linestyle': '-.',  'legend_label': 'Bond graph'}
line_cfg[3] = { 'xdata': (filename_ss,'V0_Vm'), 'ydata':(filename_ss,'Ii'),
                'color': 'm', 'linestyle': '-.',  'legend_label': 'Steady state (37) from bond graph'}
line_cfg[4] = { 'xdata': (filename_BG_fast,'V_E'), 'ydata':(filename_BG_fast,'Ii'),
                'color': 'g', 'linestyle': '-.',  'legend_label': 'Bond graph-fast binding '}
line_cfg[5] = { 'xdata': (filename_ss_fast,'V0_Vm'), 'ydata':(filename_ss_fast,'Ii'),
                'color': 'b', 'linestyle': '-.',  'legend_label': 'Steady-state Eqs 37 and 38' }


plot_cfg[1] = {'ylabel': 'i (nA)', 'xlabel': 'V (mV)','show_grid': 'both', 'grid_axis': 'both', 
                'line': [1,2], 'legend': [1,2]}
plot_cfg[2] = {'ylabel': 'i (nA)', 'xlabel': 'V (mV)','show_grid': 'both', 'grid_axis': 'both', 
                'line': [4,5], 'legend': [4,5]}

plot_data(fig, axs, plot_cfg, line_cfg, save_fig)