subtitle_kwargs = None  # Define subtitle_kwargs here. https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.suptitle.html
import pandas as pd

import matplotlib.pyplot as plt

fig_cfg = {'num_rows': 1, 'num_cols': 1, 'width':6, 'height':6, 'fig_title': None, 'title_y': 0.98, 'fontsize': 10, 
           'left': 0.125, 'bottom': 0.1, 'right': 0.9, 'top': 0.9, 'wspace': 0.2, 'hspace': 0.2}

plot_cfg = {1: {'xlabel': 'X Label', 'ylabel': 'Y Label', 'xlim': None, 'ylim': None, 
                'xscale': 'linear', 'yscale': 'linear', 'xticks': None, 'yticks': None,
                'legends_position': 'loc', 'lgdncol': 1, 'bbox_to_anchor': None,
                'show_grid': False, 'grid_axis': 'both', 'grid_properties': {},
                'line': [1, 2, 3], 'legend': [1,2]}}

line_cfg = {1: { 'xdata': ('file.csv','var1'), 'ydata':('file.csv','var2'), 'rightYAxis': 'Y Label2', 'ylim_right': None,
                'color': 'b', 'linestyle': '-', 'marker': None, 'markevery':1,  'scale': False, 'legend_label': None, 'line_kwargs': {}}}

save_fig = {'save_fig': False, 'fig_format': 'png', 'file_path': './', 'filename': 'fig'}

def subplots_ajdust(fig_cfg, **subtitle_kwargs):
    # maxH=8.75 inches, width 2.63-7.5
    left = fig_cfg.get('left', 0.125)  # the left side of the subplots of the figure,0.125,as a fraction of the figure width.
    right = fig_cfg.get('right', 0.9)   # the right side of the subplots of the figure,0.9, as a fraction of the figure width.
    bottom = fig_cfg.get('bottom', 0.05)  # the bottom of the subplots of the figure, 0.1, as a fraction of the figure width.
    top = fig_cfg.get('top', 0.9)     # the top of the subplots of the figure 0.9, as a fraction of the figure width.
    wspace = fig_cfg.get('wspace', 0.2)  # the amount of width reserved for space between subplots,
    # expressed as a fraction of the average axis width, 0.2
    hspace = fig_cfg.get('hspace', 0.2)  # the amount of height reserved for space between subplots,
    # expressed as a fraction of the average axis height, 0.2
    rows, cols = fig_cfg.get('num_rows', 1), fig_cfg.get('num_cols', 1)
    width, height = fig_cfg.get('width', 6), fig_cfg.get('height', 9)    
    plt.rcParams['font.size'] = fig_cfg.get('fontsize', 10)
    fig, axs = plt.subplots(rows,cols,figsize=(width, height),squeeze=False)
    y=fig_cfg.get('title_y', 0.98) # The y location of the text in figure coordinates.
    fig.suptitle(fig_cfg.get('fig_title', ''), y=fig_cfg.get('title_y', 0.98),  **subtitle_kwargs)
    fig.subplots_adjust(left=left, bottom=bottom, right=right, top=top, wspace=wspace, hspace=hspace)

    return fig, axs

def plot_data(fig, axs, plot_cfg, line_cfg, save_fig):

    # Read data from the files first to avoid reading the same file multiple times
    # If the same file is used for multiple lines, read the file once and use the data for all the lines
    data_files = {}
    data_file_names = {}
    nfiles = 0
    for line_id, line_data in line_cfg.items():
        if line_data['xdata'][0] not in data_file_names:
            # add the file to the data_files dictionary
            nfiles += 1
            data_files[nfiles] = pd.read_csv(line_data['xdata'][0])
            data_file_names[nfiles] = line_data['xdata'][0]
            line_data['xdata_array'] = data_files[nfiles][line_data['xdata'][1]]
        else:
            # find the file in the data_files dictionary and use the data
            for k, v in data_file_names.items():
                if v == line_data['xdata'][0]:
                    line_data['xdata_array'] = data_files[k][line_data['xdata'][1]]
                    break
        if line_data['ydata'][0] not in data_file_names:
            # add the file to the data_files dictionary
            nfiles += 1
            data_file_names[nfiles] = line_data['ydata'][0]
            data_files[nfiles] = pd.read_csv(line_data['ydata'][0])
            line_data['ydata_array'] = data_files[nfiles][line_data['ydata'][1]]
        else:
            # find the file in the data_files dictionary and use the data
            for k, v in data_file_names.items():
                if v == line_data['ydata'][0]:
                    line_data['ydata_array'] = data_files[k][line_data['ydata'][1]]
                    break

    for plot_id, plot_data in plot_cfg.items():
        ax = axs.flatten()[plot_id-1]
        if 'xlabel' in plot_data and plot_data['xlabel'] is not None:
            ax.set_xlabel(plot_data['xlabel'])
        if 'ylabel' in plot_data and plot_data['ylabel'] is not None:
            ax.set_ylabel(plot_data['ylabel'])
        if 'xlim' in plot_data and plot_data['xlim'] is not None:
            ax.set_xlim(plot_data['xlim'])
        if 'ylim' in plot_data and plot_data['ylim'] is not None:
            ax.set_ylim(plot_data['ylim'])
        ax.set_xscale(plot_data.get('xscale', 'linear'))
        ax.set_yscale(plot_data.get('yscale', 'linear'))
        if plot_data.get('xticks', None):
            ax.set_xticks(plot_data['xticks'])
        if plot_data.get('yticks', None):
            ax.set_yticks(plot_data['yticks'])
        if 'title' in plot_data and plot_data['title'] is not None:
            ax.set_title(plot_data['title'],y=plot_data.get('title_y', 1.0))                    
        if plot_data.get('show_grid', False):
            ax.grid(visible=True, which=plot_data['show_grid'], axis=plot_data.get('grid_axis', 'both'), **plot_data.get('grid_properties', {}))
        if 'xticklabel' in plot_data:
            ax.set_xticklabels(plot_data['xticklabel'])
        handles = {}
        for i, line_id in enumerate(plot_data.get('line', [])):
            xdata = line_cfg[line_id]['xdata_array']
            ydata = line_cfg[line_id]['ydata_array']    
            if line_cfg[line_id].get('rightYAxis', False):
                ax2 = ax.twinx()
                ax2.set_ylabel(line_cfg[line_id]['rightYAxis'])
                if line_cfg[line_id].get('ylim_right', False):
                    ax2.set_ylim(line_cfg[line_id]['ylim_right'])
                handles[line_id],=ax2.plot(xdata, ydata, color=line_cfg[line_id].get('color', 'b'), linestyle=line_cfg[line_id].get('linestyle', '-'),
                    marker=line_cfg[line_id].get('marker'), markevery=line_cfg[line_id].get('markevery', 1),
                    label=line_cfg[line_id].get('legend_label'))
            else:
                handles[line_id],=ax.plot(xdata, ydata, color=line_cfg[line_id].get('color', 'b'), linestyle=line_cfg[line_id].get('linestyle', '-'),
                    marker=line_cfg[line_id].get('marker'), markevery=line_cfg[line_id].get('markevery', 1),
                    label=line_cfg[line_id].get('legend_label'))
        # Only show the legend specified in the plot_cfg
        if 'legend' in plot_data and plot_data['legend']:
            handles_list = [handles[i] for i in plot_data['legend']]
            ax.legend(handles=handles_list,loc=plot_data.get('legends_position', 'best'), ncol=plot_data.get('lgdncol', 1))
            if 'bbox_to_anchor' in plot_data and plot_data['bbox_to_anchor'] is not None:
                ax.legend( bbox_to_anchor=plot_data.get('bbox_to_anchor'))
    
    if save_fig.get('save_fig', False):
        full_path = save_fig.get('file_path', './') + save_fig.get('filename', 'new_fig') + '.' + save_fig.get('fig_format', 'png')
        plt.savefig(full_path)
    
    plt.show()
