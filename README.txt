About
=====
iprm-PASEF Exporter is a simple tool to create MGF and mzML files from iprm-PASEF datasets acquired on the Bruker
timsTOF fleX and processed in SCiLS Lab.

Installation
============

GUI
---
No installation is required if the packaged GUI is being used.

Manual Installation
-------------------
1. Download and install Anaconda for Windows.
2. Download and install Git for Windows.
3. Run "Anaconda Prompt".
4. Create a conda instance.

        conda create -n iprmpasef_exporter python=3.11

5. Activate conda environment.

        conda activate iprmpasef_exporter

6. Install requirements.

        pip install -r requirements.txt

7. Install SCiLS Lab API Python package.

        pip install "C:\Program Files\SCiLS\SCiLS Lab\APIClients\Python\scilslab-8.0.121-cp311-cp311-win_amd64.whl"

8. Install iprm-PASEF Exporter package.

        pip install /path/to/iprmpasef_exporter.zip

Usage
=====
As of SCiLS Lab 2025b, creation of *.mgf and *.mzML files containing MS/MS fragmentation data is a manual processes
requiring user created files. To assist in this process, a script utilizing the SCiLS Lab Python API has been created
to export MS/MS data. Importantly, prior to export, feature lists should be manually validated to ensure that the
spatial distribution of precursor and fragment features match. Currently, T-ReX^3 feature finding only takes the 1/K0
window into account when correlating fragments to precursors; spatial distribution is not considered.

GUI
---
Browse for and open an iprm-PASEF SCiLS Lab dataset using the "Browse" button under "SCiLS Lab File". Once the file has
been loaded, the "Feature List ID" dropdown menu will be populated. Select the feature list containing the iprm-PASEF
MS/MS precursor and fragment data of interest. From that feature table, an "Intensity Column Name" will need to be
selected, which will specify which column should be used to obtain intensity values for each precursor/fragment ion to
be exported (either user added or the default intensity column).

MGF or mzML files can be exported, which is specified under the "Export Format" dropdown menu. All other parameters
can either be left at their default values or modified if needed. See below for a description of parameters.

Command Line
------------
First, the UUID of a feature table of interest must be obtained. This can be done using the get_feature_lists command.

        get_feature_lists --scils /path/to/iprmpasef_imaging_data.slx

Next, the name of the column containing intensity values or statistical values used for feature sorting/prioritization
must be provided. If the name of the column is unknown, the get_intensity_column_names command can be used.

        get_intensity_column_names --scils /path/to/ms1_imaging_data.slx
        --feature_list_id 1ab234cd-5ef6-789a-bcde-f0ab123cd4ef

By default, the intensity column that is included following T-ReX^3 feature finding for iprm-PASEF SCiLS Lab projects
uses non-normalized intensity values. Therefore, a custom intensity column containing normalized intensity values
should be added prior to MS/MS export if desired.

Finally, the iprmpasef_to_mgf or iprmpasef_to_mzml command can be used to export all fragmentation data to a single
*.mgf or *.mzML file to be used for downstream analysis.

The precursor ion information (m/z and 1/K0) is obtained from any detected precursor features in the iprm-PASEF MS/MS
dataset's feature table. If no precursor is detected for a given precursor isolation window, the precursor ion
information is populated using the isolation window m/z and 1/K0 ranges. Additionally, by default, all fragment peaks
under with a relative intensity of < 1% are discarded prior to export. To modify this percentage, the
--relative_intensity_threshold parameter can be used. To disable filtering, set --relative_intensity_threshold to 0.

        iprmpasef_to_mgf --scils /path/to/ms1_imaging_data.slx --feature_list_id 1ab234cd-5ef6-789a-bcde-f0ab123cd4ef
        --intensity_column_name tic_intensity --outdir /path/to/output_directory --relative_intensity_threshold 1

        iprmpasef_to_mzml --scils /path/to/ms1_imaging_data.slx --feature_list_id 1ab234cd-5ef6-789a-bcde-f0ab123cd4ef
        --intensity_column_name tic_intensity --outdir /path/to/output_directory --relative_intensity_threshold 1
        --polarity positive

Please note that the mzML export may be missing crucial metadata for certain open-source analysis platforms.

For a full list of parameters, use the following command:

        iprmpasef_to_mgf --help

        iprmpasef_to_mzml --help

Parameters
==========

MGF
---
  --scils SCILS         Path to SCiLS .slx file.
  --outdir OUTDIR       Output directory.
  --feature_list_id FEATURE_LIST_ID
                        UUID for the MS1 feature table of interest. If
                        unknown, please run the "get_feature_lists" command.
  --intensity_column_name INTENSITY_COLUMN_NAME
                        Name of the column from the feature table to use
                        intensity values from. If unknown, please run the
                        "get_intensity_column_names" command.
  --export_single_file  If this flag is used, create a single MGF file
                        containing all MS/MS spectra. Otherwise, create
                        individual MGF files for each precursor window.
  --get_precursor_from_isolation_window
                        If this flag is used, populate the precursor m/z and
                        1/K0 values from the isolation window that was defined
                        in the iprm-PASEF timsControl method.
  --relative_intensity_threshold [0-100]
                        Fragments below this percentage of the total ion count
                        (TIC) intensity are filtered and removed from the
                        final MS/MS spectrum for a given precursor. Example:
                        relative_intensity_threshold == 1 is equal to 1% of
                        the TIC as the cutoff. Defaults to 1 (i.e. 1%).

mzML
----
  --scils SCILS         Path to SCiLS .slx file.
  --outdir OUTDIR       Output directory.
  --feature_list_id FEATURE_LIST_ID
                        UUID for the MS1 feature table of interest. If
                        unknown, please run the "get_feature_lists" command.
  --intensity_column_name INTENSITY_COLUMN_NAME
                        Name of the column from the feature table to use
                        intensity values from. If unknown, please run the
                        "get_intensity_column_names" command.
  --polarity {positive,negative}
                        Polarity of the spectra in the dataset. Either
                        "positive" or "negative".
  --barebones_metadata  Only use basic mzML metadata. Use if downstream data
                        analysis tools throw errors with descriptive CV terms.
  --export_single_file  If this flag is used, create a single mzML file
                        containing all MS/MS spectra. Otherwise, create
                        individual mzML files for each precursor window.
  --get_precursor_from_isolation_window
                        If this flag is used, populate the precursor m/z and
                        1/K0 values from the isolation window that was defined
                        in the iprm-PASEF timsControl method.
  --relative_intensity_threshold [0-100]
                        Fragments below this percentage of the total ion count
                        (TIC) intensity are filtered and removed from the
                        final MS/MS spectrum for a given precursor. Example:
                        relative_intensity_threshold == 1 is equal to 1% of
                        the TIC as the cutoff. Defaults to 1 (i.e. 1%).
  --mz_encoding {32,64}
                        Choose encoding for m/z array: 32-bit ("32") or 64-bit
                        ("64"). Defaults to 64-bit.
  --intensity_encoding {32,64}
                        Choose encoding for intensity array: 32-bit ("32") or
                        64-bit ("64"). Defaults to 64-bit.
  --compression {zlib,none}
                        Choose between ZLIB compression ("zlib") or no
                        compression ("none"). Defaults to "zlib".
