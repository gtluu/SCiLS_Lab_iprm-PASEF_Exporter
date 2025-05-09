import os
import copy
import argparse
from scilslab import LocalSession
import numpy as np
import pandas as pd
from pyteomics import mgf


def get_args():
    """
    Parse command line parameters.

    :return: Arguments with default or user specified values.
    :rtype: dict
    """
    parser = argparse.ArgumentParser()
    # General parameters
    parser.add_argument('--scils',
                        help='Path to SCiLS .slx file.',
                        required=True,
                        type=str)
    parser.add_argument('--outdir',
                        help='Output directory.',
                        default='',
                        type=str)
    parser.add_argument('--feature_list_id',
                        help='UUID for the MS1 feature table of interest. If unknown, please run the '
                             '"get_feature_lists" command.',
                        required=True,
                        type=str)
    parser.add_argument('--intensity_column_name',
                        help='Name of the column from the feature table to use intensity values from. If unknown, '
                             'please run the "get_intensity_column_names" command.',
                        required=True,
                        type=str)
    parser.add_argument('--export_single_file',
                        help='If this flag is used, create a single MGF file containing all MS/MS spectra. Otherwise, '
                             'create individual MGF files for each precursor window.',
                        action='store_true')
    parser.add_argument('--get_precursor_from_isolation_window',
                        help='If this flag is used, populate the precursor m/z and 1/K0 values from the isolation '
                             'window that was defined in the iprm-PASEF timsControl method.',
                        action='store_true')
    parser.add_argument('--relative_intensity_threshold',
                        help='Fragments below this percentage of the total ion count (TIC) intensity are filtered and '
                             'removed from the final MS/MS spectrum for a given precursor. '
                             'Example: relative_intensity_threshold == 1 is equal to 1%% of the TIC as the cutoff. '
                             'Defaults to 1 (i.e. 1%%).',
                        metavar='[0-100]',
                        default=1,
                        choices=range(0, 101),
                        type=int)

    arguments = parser.parse_args()
    return vars(arguments)


def convert_iprmpasef_feature_list_to_mgf(slx, outdir, feature_list_id, intensity_column_name, export_single_file,
                                          get_precursor_from_isolation_window, relative_intensity_threshold=1):
    """
    Convert precursors and fragments found in a iprm-PASEF SCiLS Lab feature list to MS/MS spectra in a single MGF
    file. If precursor is not found in the spectra, the precursor is inferred based on the iprm-PASEF precursor window
    that was used.

    :param slx: Path to the input SCiLS Lab *.slx file to analyze.
    :type slx: str
    :param outdir: Path to folder in which to write output file(s). Defaults to the input SCiLS Lab *.slx file path.
    :type outdir: str
    :param feature_list_id: UUID for the MS1 feature table of interest. If unknown, please run the "get_feature_lists"
        command.
    :type feature_list_id: str
    :param intensity_column_name: Name of the column from the feature table to use intensity values from. If unknown,
        please run the "get_intensity_column_names" command.
    :type intensity_column_name: str
    :param export_single_file: If this flag is used, create a single MGF file containing all MS/MS spectra. Otherwise,
        create individual MGF files for each precursor window.
    :type export_single_file: bool
    :param get_precursor_from_isolation_window: If this flag is used, populate the precursor m/z and 1/K0 values from
        the isolation window that was defined in the iprm-PASEF timsControl method.
    :type get_precursor_from_isolation_window: bool
    :param relative_intensity_threshold: Relative intensity threshold value to use for filtering out low intensity
        fragment peaks. A threshold value of '1' corresponds to a threshold of 1% of the sum of all fragment intensity
        values for a given precursor.
    :type relative_intensity_threshold: int
    """
    # Set output directory if not specified.
    if outdir == '':
        outdir = os.path.dirname(slx)
    # Set relative intensity threshold to float value.
    relative_intensity_threshold = relative_intensity_threshold / 100
    with LocalSession(filename=slx) as session:
        dataset = session.dataset_proxy
        # Get iprm-PASEF feature table from iprm SCiLS file containing precursor/fragment and isolation window columns.
        feature_list = dataset.feature_table.get_features(feature_list_id, include_all_user_columns=True)
        # Subset feature table by isolation window. Each feature table will contain all precursor and fragment features
        # detected by Bruker T-ReX feature finding in SCiLS.
        # Feature tables stored as a dict where key == isolation window string and value == pd.DataFrame.
        feature_lists = {key: value.reset_index() for key, value in feature_list.groupby('isolation_window')}
        # Process iprm-PASEF feature table for each precursor/isolation window.
        count = 1
        ms2_dict_list = []
        for window, table in feature_lists.items():
            precursor_table = table[table['type'] == 'Precursor'].reset_index()
            fragment_table = table[table['type'] == 'Fragment'].reset_index()
            # Get precursor m/z and 1/K0 values.
            if not precursor_table.empty and not get_precursor_from_isolation_window:
                # Calculated weighted average for precursor m/z and 1/K0 using feature intensity as weights.
                precursor_mz_array = (precursor_table['mz_low'] + precursor_table['mz_high']) / 2
                precursor_mz_array = precursor_mz_array.values
                precursor_ook0_array = (precursor_table['one_over_k0_low'] + precursor_table['one_over_k0_high']) / 2
                precursor_ook0_array = precursor_ook0_array.values
                precursor_mz = np.average(precursor_mz_array, weights=precursor_table[intensity_column_name])
                precursor_ook0 = np.average(precursor_ook0_array, weights=precursor_table[intensity_column_name])
            else:
                # If no precursor type feature detected via feature finding, parse and use isolation window for
                # precursor m/z and 1/K0.
                precursor_mz = float(window.split(',')[0][:-4])
                precursor_ook0 = float(window.split(',')[1][6:])
            # Filter and remove any fragment type features based on relative intensity cutoff.
            fragment_table = fragment_table[fragment_table[intensity_column_name] >= (
                    np.sum(fragment_table[intensity_column_name].values) * relative_intensity_threshold)]
            fragment_mz_array = (fragment_table['mz_low'] + fragment_table['mz_high']) / 2
            fragment_mz_array = fragment_mz_array.values
            fragment_table = pd.DataFrame({'mz': fragment_mz_array,
                                           'intensity': fragment_table[intensity_column_name].values})
            fragment_table = fragment_table.sort_values(by='mz')
            # Save to list of MS/MS dicts for export to MGF file.
            ms2_dict = {'m/z array': copy.deepcopy(fragment_table['mz'].values),
                        'intensity array': copy.deepcopy(fragment_table['intensity'].values),
                        'params': {'FEATURE_ID': count,
                                   'PEPMASS': precursor_mz,
                                   'ION_MOBILITY': precursor_ook0,
                                   'SCANS': 1,  # hard coded to 1 for now
                                   'MSLEVEL': 2}}
            ms2_dict_list.append(ms2_dict)
            count += 1
        # Export MS/MS spectra to MGF file(s).
        if export_single_file:
            mgf_filename = f'{os.path.splitext(os.path.split(slx)[-1])[0]}_iprm-PASEF_MSMS.mgf'
            mgf.write(ms2_dict_list, output=os.path.join(outdir, mgf_filename), file_mode='w')
        else:
            for ms2_dict in ms2_dict_list:
                mgf_filename = f'{os.path.splitext(os.path.split(slx)[-1])[0]}_iprm-PASEF_mz{ms2_dict["params"]["PEPMASS"]}_ook0{ms2_dict["params"]["ION_MOBILITY"]}.mgf'
                ms2_dict['params']['FEATURE_ID'] = 1
                mgf.write([ms2_dict], output=os.path.join(outdir, mgf_filename), file_mode='w')


def main():
    """
    Run workflow.
    """
    args = get_args()
    convert_iprmpasef_feature_list_to_mgf(slx=args['scils'],
                                          outdir=args['outdir'],
                                          feature_list_id=args['feature_list_id'],
                                          intensity_column_name=args['intensity_column_name'],
                                          export_single_file=args['export_single_file'],
                                          get_precursor_from_isolation_window=args['get_precursor_from_isolation_window'],
                                          relative_intensity_threshold=args['relative_intensity_threshold'])
