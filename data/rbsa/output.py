import os
import rbsadbmodel as rdb
import util
#import matplotlib as mpl
#mpl.use('Agg') # Turn interactive plotting off
#mpl.use('qt4agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np
import itertools
import pandas as pd
import matplotlib as mpl
from PIL import Image

def trim_white(filename):
    im = Image.open(filename)
    pix = np.asarray(im)

    pix = pix[:,:,0:3] # Drop the alpha channel
    idx = np.where(pix-255)[0:2] # Drop the color when finding edges
    box = map(min,idx)[::-1] + map(max,idx)[::-1]

    region = im.crop(box)
    region_pix = np.asarray(region)
    region.save(filename)

def draw_scatter_plot(df, cols, marker_labels, slicer, weighted_area=True, setlims=None, marker_colors=None, marker_shapes=None, size='medium', axis_titles=None, marker_color_all=None, show_labels=True, leg_label=None):
#     plt.rcParams['figure.figsize'] = 10, 10  # that's default image size for this interactive session
    def get_marker(i):
        return mpl.markers.MarkerStyle.filled_markers[i]

    def add_labels(marker_labels, x, y):
        if not show_labels:
            return
        for label, x, y in zip(marker_labels, x, y):
            if y > x:
                ha = 'right'
                va = 'bottom'
                xytext = (-5, 5)
            else:
                ha = 'left'
                va = 'top'
                xytext = (5, -5)
            plt.annotate(label, xy =(x, y), xytext=xytext,
                textcoords='offset points', ha=ha, va=va, alpha=0.8)

    if marker_color_all is None:
        marker_color_all = 'b'

    title = slicer
    x = df[cols[0]]
    y = df[cols[1]]
    
    if not marker_colors is None:
        if not marker_shapes is None:
            for i, shape in enumerate(set(marker_shapes)):
                this_marker = df.loc[df['level_0'] == shape, :]
                x = this_marker[cols[0]]
                y = this_marker[cols[1]]
                marker_colors = this_marker['level_1']
                marker_colors = [list(set(marker_colors)).index(j) for j in marker_colors.tolist()]
                marker_labels = zip(this_marker['level_0'], this_marker['level_1'])
                if weighted_area:
                    plt.scatter(x, y, c=marker_colors, cmap=plt.cm.Set1, marker='${}$'.format(shape[2:]), s=df['HouseCount'], alpha=0.7, label=leg_label)
                else:
                    plt.scatter(x, y, c=marker_colors, cmap=plt.cm.Set1, marker='${}$'.format(shape[2:]), s=1000, alpha=0.7, label=leg_label)
                add_labels(marker_labels, x, y)
        else:
            if weighted_area:
                plt.scatter(x, y, c=marker_colors, cmap=plt.cm.Set1, s=df['HouseCount'], alpha=0.7, label=leg_label)
            else:
                plt.scatter(x, y, c=marker_colors, cmap=plt.cm.Set1, s=50, alpha=0.7, label=leg_label)
            add_labels(marker_labels, x, y)
    else:
        if weighted_area:
#             plt.scatter(x, y, s=df['HouseCount'], c='k', alpha=1.0) # solid black for superimpoesed shadows
            plt.scatter(x, y, s=df['HouseCount'], c=marker_color_all, alpha=0.5, label=leg_label)
        else:
            plt.scatter(x, y, c=marker_color_all, alpha=0.5, label=leg_label)
        add_labels(marker_labels, x, y)

    # y=x line
    ax = plt.gca()
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]

    if not setlims is None:
        print "Overwriting calculated scale limits ({}) with user-specified limits ({})".format(lims, setlims)
        for i, setlim in enumerate(setlims):
            if not setlim is None:
                lims[i] = setlim

    # now plot both limits against eachother
    ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0)

    # +20% line
    ax.plot(lims, [lims[0], lims[1]*1.2], 'k-', alpha=0.1, zorder=0)

    # +20% line
    ax.plot(lims, [lims[0], lims[1]*0.8], 'k-', alpha=0.1, zorder=0)
    
    ax.set_aspect('equal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    
    if size == 'large':
        title_size = 20
        axis_label_size = 24
        tick_size = 16
    elif size == 'medium':
        title_size = 16
        axis_label_size = 20
        tick_size = 12
    elif size == 'small':
        title_size = 16
        axis_label_size = 16
        tick_size = 12

    if axis_titles is None:
        ax.set_xlabel('RBSA', fontsize=axis_label_size)
        ax.set_ylabel('NREL PNW-Scale Analysis', fontsize=axis_label_size)
    else:
        ax.set_xlabel(axis_titles[0], fontsize=axis_label_size)
        ax.set_ylabel(axis_titles[1], fontsize=axis_label_size)
    plt.tick_params(axis='both', which='major', labelsize=tick_size)
    plt.title(title, fontsize=title_size)
    
def do_plot(slices, fields, size='medium', weighted_area=True, save=False, setlims=None, marker_color=False, marker_shape=False, version=None, marker_color_all=None, show_labels=True, leg_label=None):
    if size == 'large':
        plt.rcParams['figure.figsize'] = 20, 20 #20, 20  # set image size
        max_marker_size = 800
    elif size == 'medium':
        plt.rcParams['figure.figsize'] = 20, 10  # set image size
        max_marker_size = 400
    elif size == 'small':
        plt.rcParams['figure.figsize'] = 10, 5  # set image size
        max_marker_size = 400       
    
    # house_count = 3579529.34
    
    for i, slicer in enumerate(slices):
        plt.subplot(1, len(slices), i+1)
        marker_colors = None
        marker_shapes = None
        marker_labels = None
        if fields == 'weights':
            measured_elec = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['kwh_nrm_total']]
            measured_gas = pd.read_csv('../../analysis_results/outputs/pnw/Natural Gas Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['thm_nrm_total']]
            measured = measured_elec.join(measured_gas)
            measured['Measured Total Site Energy MBtu'] = 3412.0 * 0.000001 * measured['kwh_nrm_total'] + 29.3 * 3412.0 * 0.000001 * measured['thm_nrm_total']
            house_count = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['Weight']].sum().values[0]
            predicted = pd.read_csv('../../analysis_results/resstock_pnw.csv', index_col=['name'])[['building_characteristics_report.{}'.format(slicer), 'simulation_output_report.Total Site Energy MBtu', 'led_lighting_upgrade.run_measure', 'r13_wall_insulation_upgrade_(if_uninsulated).run_measure', 'triple_pane_windows_upgrade_(if_single_pane).run_measure', 'upgrade_package_(all_or_none).run_measure', 'upgrade_package_(allow_individual_options).run_measure']]
            predicted = remove_upgrades(predicted)
            predicted['Weight'] = house_count / len(predicted.index)
            predicted['Predicted Total Site Energy MBtu'] = predicted['simulation_output_report.Total Site Energy MBtu'] * predicted['Weight']
            predicted = predicted.groupby('building_characteristics_report.{}'.format(slicer)).sum()
            cols = ['Measured Total Site Energy MBtu', 'Predicted Total Site Energy MBtu']
        else:
            if slicer in ['Location Heating Region', 'Vintage', 'Heating Fuel']:
              if 'electricity' in fields:
                  measured = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['kwh_nrm_per_home']]
                  measured['Measured Per House Site Electricity MBtu'] = 3412.0 * 0.000001 * measured['kwh_nrm_per_home']
                  house_count = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['Weight']].sum().values[0]
                  predicted = pd.read_csv('../../analysis_results/resstock_pnw.csv', index_col=['name'])[['building_characteristics_report.{}'.format(slicer), 'simulation_output_report.Total Site Electricity kWh', 'led_lighting_upgrade.run_measure', 'r13_wall_insulation_upgrade_(if_uninsulated).run_measure', 'triple_pane_windows_upgrade_(if_single_pane).run_measure', 'upgrade_package_(all_or_none).run_measure', 'upgrade_package_(allow_individual_options).run_measure']]
                  predicted = remove_upgrades(predicted)
                  predicted['Weight'] = house_count / len(predicted.index)
                  predicted['Predicted Total Site Electricity MBtu'] = 3412.0 * 0.000001 * predicted['simulation_output_report.Total Site Electricity kWh'] * predicted['Weight']
                  predicted = predicted.groupby('building_characteristics_report.{}'.format(slicer)).sum()
                  predicted['Predicted Per House Site Electricity MBtu'] = predicted['Predicted Total Site Electricity MBtu'] / predicted['Weight']
                  cols = ['Measured Per House Site Electricity MBtu', 'Predicted Per House Site Electricity MBtu', 'Weight']
              elif 'gas' in fields:
                  measured = pd.read_csv('../../analysis_results/outputs/pnw/Natural Gas Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['thm_nrm_per_home']]
                  measured['Measured Per House Site Gas MBtu'] = 29.3 * 3412.0 * 0.000001 * measured['thm_nrm_per_home']
                  house_count = pd.read_csv('../../analysis_results/outputs/pnw/Natural Gas Consumption {}.tsv'.format(slicer), index_col=['Dependency={}'.format(slicer)], sep='\t')[['Weight']].sum().values[0]
                  predicted = pd.read_csv('../../analysis_results/resstock_pnw.csv', index_col=['name'])[['building_characteristics_report.{}'.format(slicer), 'simulation_output_report.Total Site Natural Gas therm', 'led_lighting_upgrade.run_measure', 'r13_wall_insulation_upgrade_(if_uninsulated).run_measure', 'triple_pane_windows_upgrade_(if_single_pane).run_measure', 'upgrade_package_(all_or_none).run_measure', 'upgrade_package_(allow_individual_options).run_measure']]
                  predicted = remove_upgrades(predicted)
                  predicted['Weight'] = house_count / len(predicted.index)
                  predicted['Predicted Total Site Gas MBtu'] = 29.3 * 3412.0 * 0.000001 * predicted['simulation_output_report.Total Site Natural Gas therm'] * predicted['Weight']
                  predicted = predicted.groupby('building_characteristics_report.{}'.format(slicer)).sum()
                  predicted['Predicted Per House Site Gas MBtu'] = predicted['Predicted Total Site Gas MBtu'] / predicted['Weight']
                  cols = ['Measured Per House Site Gas MBtu', 'Predicted Per House Site Gas MBtu', 'Weight']
            elif slicer == 'Location Heating Region Vintage':
              if 'electricity' in fields:
                  measured = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency=Location Heating Region', 'Dependency=Vintage'], sep='\t')[['kwh_nrm_per_home']]
                  measured['Measured Per House Site Electricity MBtu'] = 3412.0 * 0.000001 * measured['kwh_nrm_per_home']
                  house_count = pd.read_csv('../../analysis_results/outputs/pnw/Electricity Consumption {}.tsv'.format(slicer), index_col=['Dependency=Location Heating Region', 'Dependency=Vintage'], sep='\t')[['Weight']].sum().values[0]
                  predicted = pd.read_csv('../../analysis_results/resstock_pnw.csv', index_col=['name'])[['building_characteristics_report.Location Heating Region', 'building_characteristics_report.Vintage', 'simulation_output_report.Total Site Electricity kWh', 'led_lighting_upgrade.run_measure', 'r13_wall_insulation_upgrade_(if_uninsulated).run_measure', 'triple_pane_windows_upgrade_(if_single_pane).run_measure', 'upgrade_package_(all_or_none).run_measure', 'upgrade_package_(allow_individual_options).run_measure']]
                  predicted = remove_upgrades(predicted)
                  predicted['Weight'] = house_count / len(predicted.index)
                  predicted['Predicted Total Site Electricity MBtu'] = 3412.0 * 0.000001 * predicted['simulation_output_report.Total Site Electricity kWh'] * predicted['Weight']
                  predicted = predicted.rename(columns={"building_characteristics_report.Location Heating Region": "Dependency=Location Heating Region", "building_characteristics_report.Vintage": "Dependency=Vintage"})
                  predicted = predicted.groupby(['Dependency=Location Heating Region', 'Dependency=Vintage']).sum()
                  predicted['Predicted Per House Site Electricity MBtu'] = predicted['Predicted Total Site Electricity MBtu'] / predicted['Weight']
                  cols = ['Measured Per House Site Electricity MBtu', 'Predicted Per House Site Electricity MBtu', 'Weight']
              elif 'gas' in fields:
                  measured = pd.read_csv('../../analysis_results/outputs/pnw/Natural Gas Consumption {}.tsv'.format(slicer), index_col=['Dependency=Location Heating Region', 'Dependency=Vintage'], sep='\t')[['thm_nrm_per_home']]
                  measured['Measured Per House Site Gas MBtu'] = 29.3 * 3412.0 * 0.000001 * measured['thm_nrm_per_home']
                  house_count = pd.read_csv('../../analysis_results/outputs/pnw/Natural Gas Consumption {}.tsv'.format(slicer), index_col=['Dependency=Location Heating Region', 'Dependency=Vintage'], sep='\t')[['Weight']].sum().values[0]
                  predicted = pd.read_csv('../../analysis_results/resstock_pnw.csv', index_col=['name'])[['building_characteristics_report.Location Heating Region', 'building_characteristics_report.Vintage', 'simulation_output_report.Total Site Natural Gas therm', 'led_lighting_upgrade.run_measure', 'r13_wall_insulation_upgrade_(if_uninsulated).run_measure', 'triple_pane_windows_upgrade_(if_single_pane).run_measure', 'upgrade_package_(all_or_none).run_measure', 'upgrade_package_(allow_individual_options).run_measure']]
                  predicted = remove_upgrades(predicted)
                  predicted['Weight'] = house_count / len(predicted.index)
                  predicted['Predicted Total Site Gas MBtu'] = 29.3 * 3412.0 * 0.000001 * predicted['simulation_output_report.Total Site Natural Gas therm'] * predicted['Weight']
                  predicted = predicted.rename(columns={"building_characteristics_report.Location Heating Region": "Dependency=Location Heating Region", "building_characteristics_report.Vintage": "Dependency=Vintage"})
                  predicted = predicted.groupby(['Dependency=Location Heating Region', 'Dependency=Vintage']).sum()
                  predicted['Predicted Per House Site Gas MBtu'] = predicted['Predicted Total Site Gas MBtu'] / predicted['Weight']
                  cols = ['Measured Per House Site Gas MBtu', 'Predicted Per House Site Gas MBtu', 'Weight']
           
        df = measured.join(predicted)[cols]
        df = df.reset_index()
        marker_labels = df.ix[:,0]
        if marker_color:
            marker_colors = df['Dependency=Vintage']
            marker_colors = [list(set(marker_colors)).index(i) for i in marker_colors.tolist()]          
            marker_labels = zip(df['Dependency=Location Heating Region'], df['Dependency=Vintage'])
        if weighted_area:
            df['HouseCount'] = df['Weight'] * 0.001
        draw_scatter_plot(df, cols, marker_labels, slicer, weighted_area=weighted_area, setlims=setlims, marker_colors=marker_colors, marker_shapes=marker_shapes, size=size, marker_color_all=marker_color_all, show_labels=show_labels, leg_label=leg_label)
    if save:
        if len(slices) == 1:
          filename = os.path.join('..', '..', 'analysis_results', 'outputs', 'pnw', 'saved images', 'Scatter_2slice_{}.png'.format(fields))
        else:
          filename = os.path.join('..', '..', 'analysis_results', 'outputs', 'pnw', 'saved images', 'Scatter_1slice_{}.png'.format(fields))
        plt.savefig(filename, bbox_inches='tight', dpi=200)
        trim_white(filename)
        plt.close()

class Create_DFs():
    
    def __init__(self, file):
        self.session = rdb.create_session(file)
        
    def electricity_consumption_location_heating_region(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_climate_zones(df)
        df = util.assign_heating_location(df)
        df = util.assign_electricity_consumption(df)
        df = df.groupby(['Dependency=Location Heating Region'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['kwh_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['kwh_nrm_per_home'] = df['kwh_nrm'] / df['Count']
        df['kwh_nrm_total'] = df['kwh_nrm_per_home'] * df['Weight']           
        return df

    def electricity_consumption_vintage(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_vintage(df)
        df = util.assign_electricity_consumption(df)
        df = df.groupby(['Dependency=Vintage'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['kwh_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['kwh_nrm_per_home'] = df['kwh_nrm'] / df['Count']
        df['kwh_nrm_total'] = df['kwh_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df['Dependency=Vintage'] = pd.Categorical(df['Dependency=Vintage'], ['<1950', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s'])
        df = df.sort_values(by=['Dependency=Vintage']).set_index(['Dependency=Vintage'])             
        return df
        
    def electricity_consumption_heating_fuel(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_heating_fuel(df)
        df = util.assign_electricity_consumption(df)    
        df = df.groupby(['Dependency=Heating Fuel'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['kwh_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['kwh_nrm_per_home'] = df['kwh_nrm'] / df['Count']
        df['kwh_nrm_total'] = df['kwh_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df = df.sort_values(by=['Dependency=Heating Fuel']).set_index(['Dependency=Heating Fuel'])             
        return df
        
    def electricity_consumption_location_heating_region_vintage(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_climate_zones(df)
        df = util.assign_heating_location(df)
        df = util.assign_vintage(df)
        df = util.assign_electricity_consumption(df)
        df = df.groupby(['Dependency=Location Heating Region', 'Dependency=Vintage'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['kwh_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['kwh_nrm_per_home'] = df['kwh_nrm'] / df['Count']
        df['kwh_nrm_total'] = df['kwh_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df['Dependency=Vintage'] = pd.Categorical(df['Dependency=Vintage'], ['<1950', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s'])
        df = df.sort_values(by=['Dependency=Location Heating Region', 'Dependency=Vintage']).set_index(['Dependency=Location Heating Region', 'Dependency=Vintage'])             
        return df        
        
    def natural_gas_consumption_location_heating_region(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_climate_zones(df)
        df = util.assign_heating_location(df)
        df = util.assign_natural_gas_consumption(df)
        df = df.groupby(['Dependency=Location Heating Region'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['thm_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['thm_nrm_per_home'] = df['thm_nrm'] / df['Count']
        df['thm_nrm_total'] = df['thm_nrm_per_home'] * df['Weight']           
        return df

    def natural_gas_consumption_vintage(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_vintage(df)
        df = util.assign_natural_gas_consumption(df)
        df = df.groupby(['Dependency=Vintage'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['thm_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['thm_nrm_per_home'] = df['thm_nrm'] / df['Count']
        df['thm_nrm_total'] = df['thm_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df['Dependency=Vintage'] = pd.Categorical(df['Dependency=Vintage'], ['<1950', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s'])
        df = df.sort_values(by=['Dependency=Vintage']).set_index(['Dependency=Vintage'])             
        return df
        
    def natural_gas_consumption_location_heating_region_vintage(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_climate_zones(df)
        df = util.assign_heating_location(df)        
        df = util.assign_vintage(df)
        df = util.assign_natural_gas_consumption(df)
        df = df.groupby(['Dependency=Location Heating Region', 'Dependency=Vintage'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['thm_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['thm_nrm_per_home'] = df['thm_nrm'] / df['Count']
        df['thm_nrm_total'] = df['thm_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df['Dependency=Vintage'] = pd.Categorical(df['Dependency=Vintage'], ['<1950', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s'])
        df = df.sort_values(by=['Dependency=Location Heating Region', 'Dependency=Vintage']).set_index(['Dependency=Location Heating Region', 'Dependency=Vintage'])
        return df

    def natural_gas_consumption_heating_fuel(self):
        df = util.create_dataframe(self.session, rdb)
        df = util.assign_heating_fuel(df)
        df = util.assign_natural_gas_consumption(df)
        df = df.groupby(['Dependency=Heating Fuel'])
        count = df.agg(['count']).ix[:, 0]
        weight = df.agg(['sum'])['Weight']
        df = df[['thm_nrm']].sum()
        df['Count'] = count
        df['Weight'] = weight
        df['thm_nrm_per_home'] = df['thm_nrm'] / df['Count']
        df['thm_nrm_total'] = df['thm_nrm_per_home'] * df['Weight']
        df = df.reset_index()
        df = df.sort_values(by=['Dependency=Heating Fuel']).set_index(['Dependency=Heating Fuel'])             
        return df
        
def to_figure(df, file):
    
    sns.set(font_scale=1)
    f, ax = plt.subplots(figsize=(10, 10))
    ax = sns.heatmap(df, annot=True, annot_kws={'size': 10}, fmt='.2f')
    plt.savefig(file)
    plt.close()
    
def add_option_prefix(df):
    for col in df.columns:
        if not 'Dependency=' in col and not 'Count' in col and not 'Weight' in col and not 'group' in col:
            if col in ['Propane, 100% Usage', 'MSHP, SEER 18.0, 9.6 HSPF, 60% Conditioned', 'Room AC, EER 9.8, 10% Conditioned', 'Room AC, EER 9.8, 20% Conditioned', 'Room AC, EER 9.8, 30% Conditioned', 'Room AC, EER 9.8, 50% Conditioned']:
                df.rename(columns={col: 'Option=FIXME {}'.format(col)}, inplace=True)
            else:
                df.rename(columns={col: 'Option={}'.format(col)}, inplace=True)
    return df

def remove_upgrades(predicted):
    predicted = predicted[predicted['led_lighting_upgrade.run_measure']==0]
    predicted = predicted[predicted['r13_wall_insulation_upgrade_(if_uninsulated).run_measure']==0]
    predicted = predicted[predicted['triple_pane_windows_upgrade_(if_single_pane).run_measure']==0]
    predicted = predicted[predicted['upgrade_package_(all_or_none).run_measure']==0]
    predicted = predicted[predicted['upgrade_package_(allow_individual_options).run_measure']==0]
    return predicted
    
if __name__ == '__main__':
    
    datafiles_dir = '../../analysis_results/outputs/pnw'
    heatmaps_dir = 'heatmaps'

    dfs = Create_DFs('rbsa.sqlite')
    
    # for category in ['Electricity Consumption Location Heating Region', 'Electricity Consumption Vintage', 'Electricity Consumption Heating Fuel', 'Electricity Consumption Location Heating Region Vintage', 'Natural Gas Consumption Location Heating Region', 'Natural Gas Consumption Vintage', 'Natural Gas Consumption Heating Fuel', 'Natural Gas Consumption Location Heating Region Vintage']:
        # print category
        # method = getattr(dfs, category.lower().replace(' ', '_'))
        # df = method()
        # df.to_csv(os.path.join(datafiles_dir, '{}.tsv'.format(category)), sep='\t')

        # for col in ['Count', 'Weight']:
            # if col in df.columns:
                # del df[col]
        # to_figure(df, os.path.join(heatmaps_dir, '{}.png'.format(category)))
        
    do_plot(slices=['Location Heating Region', 'Vintage', 'Heating Fuel'], fields='weights', weighted_area=False, save=True, setlims=(0,None))
    do_plot(slices=['Location Heating Region', 'Vintage', 'Heating Fuel'], fields='electricity_perhouse', weighted_area=True, save=True, setlims=(0,90))
    do_plot(slices=['Location Heating Region', 'Vintage', 'Heating Fuel'], fields='gas_perhouse', save=True, setlims=(0,140))    
    
    do_plot(slices=['Location Heating Region Vintage'], fields='electricity_perhouse', save=True, setlims=(0,180), size='large', marker_color=True)
    do_plot(slices=['Location Heating Region Vintage'], fields='gas_perhouse', save=True, setlims=(0,180), size='large', marker_color=True)
            