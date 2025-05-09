import os
import copy
import argparse
from scilslab import LocalSession
import numpy as np
import pandas as pd
from psims.mzml import MzMLWriter


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
    parser.add_argument('--polarity',
                        help='Polarity of the spectra in the dataset. Either "positive" or "negative".',
                        choices=['positive', 'negative'],
                        required=True,
                        type=str)
    parser.add_argument('--barebones_metadata',
                        help='Only use basic mzML metadata. Use if downstream data analysis tools throw errors with '
                             'descriptive CV terms.',
                        action='store_true')
    parser.add_argument('--export_single_file',
                        help='If this flag is used, create a single mzML file containing all MS/MS spectra. Otherwise, '
                             'create individual mzML files for each precursor window.',
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
    parser.add_argument('--mz_encoding',
                        help='Choose encoding for m/z array: 32-bit (\"32\") or 64-bit (\"64\"). Defaults to 64-bit.',
                        default=64,
                        type=int,
                        choices=[32, 64])
    parser.add_argument('--intensity_encoding',
                        help='Choose encoding for intensity array: 32-bit (\"32\") or 64-bit (\"64\"). Defaults to '
                             '64-bit.',
                        default=64,
                        type=int,
                        choices=[32, 64])
    parser.add_argument('--compression',
                        help='Choose between ZLIB compression (\"zlib\") or no compression (\"none\"). Defaults to '
                             '\"zlib\".',
                        default='zlib',
                        type=str,
                        choices=['zlib', 'none'])

    arguments = parser.parse_args()
    return vars(arguments)


def write_mzml_metadata(writer, infile, barebones_metadata):
    """
    Write metadata to mzML file using psims. Includes spectral metadata, source files, software list, instrument
    configuration, and data processing.

    :param writer: Instance of psims.mzml.MzMLWriter for output file.
    :type writer: psims.mzml.MzMLWriter
    :param infile: Input file path to be used for source file metadata.
    :type infile: str
    :param barebones_metadata: If True, omit software and data processing metadata in the resulting mzML files. Used
        for compatibility with downstream analysis software that does not have support for newer CV params or
        UserParams.
    :type barebones_metadata: bool
    """
    # Basic file descriptions: spectra level and centroid/profile status.
    file_description = ['MSn spectrum', 'centroid spectrum']
    # Source file
    sf = writer.SourceFile(os.path.split(infile)[0],
                           os.path.split(infile)[1],
                           id=os.path.splitext(os.path.split(infile)[1])[0])
    writer.file_description(file_contents=file_description, source_files=sf)
    # Add list of software.
    if not barebones_metadata:
        # TODO: add timsControl and SCiLS?
        psims_software = {'id': 'psims-writer',
                          'version': '1.3.4',
                          'params': ['python-psims', ]}
        writer.software_list([psims_software])
    # Instrument configuration.
    # Instrument source, analyzer, and detector are all hard coded to timsTOF fleX hardware and does not allow for
    # non-stock configurations.
    inst_count = 3
    source = writer.Source(inst_count, ['matrix-assisted laser desorption ionization'])
    analyzer = writer.Analyzer(inst_count, ['quadrupole', 'time-of-flight'])
    detector = writer.Detector(inst_count, ['microchannel plate detector', 'photomultiplier'])
    inst_params = []
    if not barebones_metadata:
        inst_params.append('timsTOF fleX')
    inst_config = writer.InstrumentConfiguration(id='instrument',
                                                 component_list=[source, analyzer, detector],
                                                 params=inst_params)
    writer.instrument_configuration_list([inst_config])
    # Data processing element
    if not barebones_metadata:
        proc_methods = [writer.ProcessingMethod(order=1,
                                                software_reference='psims-writer',
                                                params=['Conversion to mzML'])]
        processing = writer.DataProcessing(proc_methods, id='exportation')
        writer.data_processing_list([processing])


def write_ms2_spectrum(writer, scan, mz_encoding, intensity_encoding, compression):
    """
    Write an MS/MS spectrum to an mzML file using psims.

    :param writer: Instance of psims.mzml.MzMLWriter for output file.
    :type writer: psims.mzml.MzMLWriter
    :param scan: Object containing spectrum metadata and data arrays.
    :type scan: pyBaf2Sql.classes.BafSpectrum | pyTDFSDK.classes.TsfSpectrum | pyTDFSDK.classes.TdfSpectrum
    :param mz_encoding: m/z encoding command line parameter, either "64" or "32".
    :type mz_encoding: int
    :param intensity_encoding: Intensity encoding command line parameter, either "64" or "32".
    :type intensity_encoding: int
    :param compression: Compression command line parameter, either "zlib" or "none".
    :type compression: str
    """

    def get_encoding_dtype(encoding):
        """
        Use "encoding" command line parameter to determine numpy dtype.

        :param encoding: Encoding command line parameter, either "64" or "32".
        :type encoding: int
        :return: Numpy dtype, either float64 or float32
        :rtype: numpy.dtype
        """
        if encoding == 32:
            return np.float32
        elif encoding == 64:
            return np.float64

    # Build params list for spectrum.
    base_peak_index = np.where(scan['intensity_array'] == np.max(scan['intensity_array']))
    params = ['MSn spectrum',
              {'ms level': 2},
              {'total ion current': sum(scan['mz_array'])},
              {'base peak m/z': scan['mz_array'][base_peak_index][0].astype(float)},
              ({'name': 'base peak intensity',
                'unit_name': 'number of detector counts',
                'value': scan['intensity_array'][base_peak_index][0].astype(float)}),
              {'highest observed m/z': float(max(scan['mz_array']))},
              {'lowest observed m/z': float(min(scan['mz_array']))}]
    # Get encoding information
    encoding_dict = {'m/z array': get_encoding_dtype(mz_encoding),
                     'intensity array': get_encoding_dtype(intensity_encoding)}
    # Build precursor information dict.
    precursor_info = {'mz': scan['selected_ion_mz'],
                      'isolation_window_args': {'target': scan['selected_ion_mz']},
                      'params': [{'inverse reduced ion mobility': scan['selected_ion_mobility']}]}
    writer.write_spectrum(scan['mz_array'],
                          scan['intensity_array'],
                          id='scan=' + str(scan['scan_number']),
                          polarity=scan['polarity'],
                          centroided=True,
                          scan_start_time=0,
                          params=params,
                          precursor_information=precursor_info,
                          encoding=encoding_dict,
                          compression=compression)


def convert_iprmpasef_feature_list_to_mzml(slx, outdir, feature_list_id, intensity_column_name, polarity,
                                           barebones_metadata, mz_encoding, intensity_encoding, compression,
                                           export_single_file, get_precursor_from_isolation_window,
                                           relative_intensity_threshold=1):
    """
    Convert precursors and fragments found in a iprm-PASEF SCiLS Lab feature list to MS/MS spectra in a single mzML
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
    :param polarity: Polarity of the spectra in the dataset. Either "positive" or "negative".
    :type polarity: str
    :param barebones_metadata: If True, omit software and data processing metadata in the resulting mzML files. Used
        for compatibility with downstream analysis software that does not have support for newer CV params or
        UserParams.
    :type barebones_metadata: bool
    :param mz_encoding: Choose encoding for m/z array: 32-bit (\"32\") or 64-bit (\"64\"). Defaults to 64-bit.
    :type mz_encoding: int
    :param intensity_encoding: Choose encoding for intensity array: 32-bit (\"32\") or 64-bit (\"64\"). Defaults to
        64-bit.
    :type intensity_encoding: int
    :param compression: Choose between ZLIB compression (\"zlib\") or no compression (\"none\"). Defaults to \"zlib\".
    :type compression: str
    :param export_single_file: If this flag is used, create a single mzML file containing all MS/MS spectra. Otherwise,
        create individual mzML files for each precursor window.
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
        scan_list = []
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
            # Save to list of MS/MS dicts for export to mzML file.
            scan_list.append({'mz_array': copy.deepcopy(fragment_table['mz'].values),
                              'intensity_array': copy.deepcopy(fragment_table['intensity'].values),
                              'scan_number': count,
                              'polarity': polarity,
                              'selected_ion_mz': precursor_mz,
                              'selected_ion_mobility': precursor_ook0}),
            count += 1

        # Export MS/MS spectra to mzML file.
        # mzML writing code modified from TIMSCONVERT.
        # Initialize writer using psims.
        if export_single_file:
            mzml_filename = f'{os.path.splitext(os.path.split(slx)[-1])[0]}_iprm-PASEF_MSMS.mzML'
            writer = MzMLWriter(os.path.join(outdir, mzml_filename), close=True)
            with writer:
                # Begin mzML writer using psims.
                writer.controlled_vocabularies()
                # Start write acquisition, instrument config, processing, etc. to mzML.
                write_mzml_metadata(writer, slx, barebones_metadata)
                # Parse chunks of data and write to spectrum element.
                with writer.run(id='run',
                                instrument_configuration='instrument',
                                start_time='1969-12-31T19:00:00.000-05:00'):
                    # Count number of spectra in run
                    with writer.spectrum_list(count=len(scan_list)):
                        for scan in scan_list:
                            write_ms2_spectrum(writer, scan, mz_encoding, intensity_encoding, compression)
        else:
            for scan in scan_list:
                mzml_filename = f'{os.path.splitext(os.path.split(slx)[-1])[0]}_iprm-PASEF_mz{scan["selected_ion_mz"]}_ook0{scan["selected_ion_mobility"]}.mzML'
                writer = MzMLWriter(os.path.join(outdir, mzml_filename), close=True)
                with writer:
                    # Begin mzML writer using psims.
                    writer.controlled_vocabularies()
                    # Start write acquisition, instrument config, processing, etc. to mzML.
                    write_mzml_metadata(writer, slx, barebones_metadata)
                    # Parse chunks of data and write to spectrum element.
                    with writer.run(id='run',
                                    instrument_configuration='instrument',
                                    start_time='1969-12-31T19:00:00.000-05:00'):
                        with writer.spectrum_list(count=1):
                            write_ms2_spectrum(writer, scan, mz_encoding, intensity_encoding, compression)


def main():
    """
    Run workflow.
    """
    print('WARNING: mzML export feature is still currently in beta. Compatibility is not guaranteed with downstream '
          'analysis platforms as certain metadata may be missing from resulting mzML files.')
    args = get_args()
    if args['polarity'] == 'positive':
        args['polarity'] = '+'
    elif args['polarity'] == 'negative':
        args['polarity'] = '-'
    convert_iprmpasef_feature_list_to_mzml(slx=args['scils'],
                                           outdir=args['outdir'],
                                           feature_list_id=args['feature_list_id'],
                                           intensity_column_name=args['intensity_column_name'],
                                           polarity=args['polarity'],
                                           barebones_metadata=args['barebones_metadata'],
                                           mz_encoding=args['mz_encoding'],
                                           intensity_encoding=args['intensity_encoding'],
                                           compression=args['compression'],
                                           export_single_file=args['export_single_file'],
                                           get_precursor_from_isolation_window=args['get_precursor_from_isolation_window'],
                                           relative_intensity_threshold=args['relative_intensity_threshold'])
