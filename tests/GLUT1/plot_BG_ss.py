import sys
import os
sys.path.append('../')
from data_plot import subplots_ajdust, plot_data
path_='C:/Users/wai484/temp/b65/Facilitated transporter/CellMLV2/'

save_fig = {'save_fig': True, 'fig_format': 'png', 'file_path': path_, 'filename': 'BG_fit_ss'}
filename = path_+'report_task_GLUT1_kinetic.csv'
filename_BG_io = path_+'GLUT1_BG_0_ss_io.csv'
filename_BG_oi = path_+'GLUT1_BG_0_ss_oi.csv'
filename_ss_io_free = path_+'report_task_GLUT1_ss_io_no_constraint.csv'
filename_ss_oi_free = path_+'report_task_GLUT1_ss_oi_no_constraint.csv'


outputs={'glu':{'component':'main','name':'glu','scale':1},
         'v_io_ss':{'component':'main','name':'v_io_ss','scale':1},         
         'v_oi_ss':{'component':'main','name':'v_oi_ss','scale':1},         
         }

outputs_oi={'t':{'component':'GLUT1_BG','name':'t','scale':1},
             'v_r1':{'component':'GLUT1_BG','name':'v_r1','scale':1/90},         
             'q_init_Ao':{'component':'GLUT1_BG','name':'q_init_Ai','scale':1/90},
             }

outputs_io={'t':{'component':'GLUT1_BG','name':'t','scale':1},
             'v_r1':{'component':'GLUT1_BG','name':'v_r1','scale':1/90},         
             'q_init_Ai':{'component':'GLUT1_BG','name':'q_init_Ai','scale':1/90},
             }
outputs_ss_oi={'t':{'component':'GLUT1_BG','name':'t','scale':1},
         'v_free':{'component':'GLUT1_BG','name':'v_free','scale':1/90},         
         'q_Ao':{'component':'GLUT1_BG','name':'q_Ao','scale':1/90},
         }
outputs_ss_io={'t':{'component':'GLUT1_BG','name':'t','scale':1},
         'v_free':{'component':'GLUT1_BG','name':'v_free','scale':-1/90},         
         'q_Ai':{'component':'GLUT1_BG','name':'q_Ai','scale':1/90},
         }
subtitle_kwargs={}
fig_cfg = {'num_rows': 2, 'num_cols': 1, 'width':6, 'height':6, 'fig_title': None, 'title_y': 0.98, 'fontsize': 10, 
           'left': 0.145, 'bottom': 0.1, 'right': 0.9, 'top': 0.9, 'wspace': 0.2, 'hspace': 0.2}
fig, axs= subplots_ajdust(fig_cfg, **subtitle_kwargs)

plot_cfg = {}
line_cfg = {}

N=len(outputs)
for i, output in enumerate(outputs):
    if i>0:
        line_cfg[i] = { 'xdata': (filename,'glu'), 'ydata':(filename,output), 
                'color': 'b', 'linestyle': '-',  'legend_label': 'kinetic'}

line_cfg[3] = { 'xdata': (filename_BG_io,'q_init_Ai'), 'ydata':(filename_BG_io,'v_r1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'BG_io_ss'}
line_cfg[4] = { 'xdata': (filename_BG_oi,'q_init_Ao'), 'ydata':(filename_BG_oi,'v_r1'),
                'color': 'k', 'linestyle': '-',  'legend_label': 'BG_oi_ss'}
line_cfg[5] = { 'xdata': (filename_ss_io_free,'q_Ai'), 'ydata':(filename_ss_io_free,'v_free'),
                'color': 'r', 'linestyle': '--',  'legend_label': 'io_ss_free'}
line_cfg[6] = { 'xdata': (filename_ss_oi_free,'q_Ao'), 'ydata':(filename_ss_oi_free,'v_free'),
                'color': 'r', 'linestyle': '--',  'legend_label': 'oi_ss_free'}
line_cfg[7] = { 'xdata': (filename_ss_io_free,'q_Ai'), 'ydata':(filename_ss_io_free,'v'),
                'color': 'r', 'linestyle': '-.',  'legend_label': 'io_ss'}
line_cfg[8] = { 'xdata': (filename_ss_oi_free,'q_Ao'), 'ydata':(filename_ss_oi_free,'v'),
                'color': 'r', 'linestyle': '-.',  'legend_label': 'oi_ss'}

plot_cfg[1] = {'ylabel': 'v_io_ss', 'xlabel': 'q_Ai (mM)','show_grid': 'both', 'grid_axis': 'both',
                'line': [1,3,5,7], 'legend': [1,3,5,7]}

plot_cfg[2] = {'ylabel': 'v_oi_ss', 'xlabel': 'q_Ao (mM)','show_grid': 'both', 'grid_axis': 'both',
                'line': [2,4,6,8], 'legend': [2,4,6,8]}


plot_data(fig, axs, plot_cfg, line_cfg, save_fig)