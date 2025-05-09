import os
import sys
import io
from scilslab import LocalSession
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QButtonGroup, QMessageBox
from exporter.iprmpasef_exporter_template import Ui_IprmpasefExporterWindow
from exporter.mgf import convert_iprmpasef_feature_list_to_mgf
from exporter.mzml import convert_iprmpasef_feature_list_to_mzml


class IprmpasefExporterWindow(QMainWindow, Ui_IprmpasefExporterWindow):
    """PySide6 GUI Window Class"""
    def __init__(self):
        super(IprmpasefExporterWindow, self).__init__()

        self.session = None

        # self.input
        self.args = {'scils': '',
                     'outdir': '',
                     'export_format': '',
                     'feature_list_id': '',
                     'intensity_column_name': '',
                     'export_single_file': False,
                     'get_precursor_from_isolation_window': True,
                     'relative_intensity_threshold': 1,
                     'polarity': 'positive',
                     'barebones_metadata': False,
                     'mz_encoding': 64,
                     'intensity_encoding': 64,
                     'compression': 'zlib'}

        # setup UI
        self.setupUi(self)
        # Set line edits to read only
        self.ScilsLineEdit.setReadOnly(True)
        self.OutputDirectoryLineEdit.setReadOnly(True)
        # Hide mzML parameters
        self.MzmlExportParametersLabel.setVisible(False)
        self.PolarityLabel.setVisible(False)
        self.PolarityPositiveRadio.setVisible(False)
        self.PolarityNegativeRadio.setVisible(False)
        self.BarebonesMetadataCheckbox.setVisible(False)
        self.MzEncodingLabel.setVisible(False)
        self.MzEncoding32bitRadio.setVisible(False)
        self.MzEncoding64bitRadio.setVisible(False)
        self.IntensityEncodingLabel.setVisible(False)
        self.IntensityEncoding32bitRadio.setVisible(False)
        self.IntensityEncoding64bitRadio.setVisible(False)
        self.CompressionLabel.setVisible(False)
        self.CompressionZlibRadio.setVisible(False)
        self.CompressionNoneRadio.setVisible(False)
        # Group radio buttons
        self.PolarityGroup = QButtonGroup()
        self.PolarityGroup.addButton(self.PolarityPositiveRadio)
        self.PolarityGroup.addButton(self.PolarityNegativeRadio)
        self.MzEncodingGroup = QButtonGroup()
        self.MzEncodingGroup.addButton(self.MzEncoding32bitRadio)
        self.MzEncodingGroup.addButton(self.MzEncoding64bitRadio)
        self.IntensityEncodingGroup = QButtonGroup()
        self.IntensityEncodingGroup.addButton(self.IntensityEncoding32bitRadio)
        self.IntensityEncodingGroup.addButton(self.IntensityEncoding64bitRadio)
        self.CompressionGroup = QButtonGroup()
        self.CompressionGroup.addButton(self.CompressionZlibRadio)
        self.CompressionGroup.addButton(self.CompressionNoneRadio)
        # Set defaults
        self.GetPrecursorFromIsolationWindowCheckbox.setChecked(True)
        self.RelativeIntensityThresholdSpinBox.setMinimum(0)
        self.RelativeIntensityThresholdSpinBox.setMaximum(100)
        self.RelativeIntensityThresholdSpinBox.setValue(1)
        self.PolarityPositiveRadio.setChecked(True)
        self.MzEncoding64bitRadio.setChecked(True)
        self.IntensityEncoding64bitRadio.setChecked(True)
        self.CompressionZlibRadio.setChecked(True)

        # File browser dialogues
        # Select SLX file
        self.ScilsBrowseButton.clicked.connect(self.select_slx)
        # Select output directory
        self.OutputDirectoryBrowseButton.clicked.connect(self.select_output_directory)

        # Get and set export format from combo box
        # Show/hide mzML parameters
        self.ExportFormatCombo.addItems(['', 'MGF', 'mzML (Beta)'])
        self.ExportFormatCombo.currentIndexChanged.connect(self.export_format_selected)

        # Update intensity column names when feature list selected
        # Update args when feature list or intensity column name selected
        self.FeatureListIdCombo.currentIndexChanged.connect(self.feature_list_selected)
        self.IntensityColumnNameCombo.currentIndexChanged.connect(self.intensity_column_name_selected)

        # Run
        self.RunButton.clicked.connect(self.run)

    def close_session(self):
        """
        Close SCiLS session to free *.slx and *.sbd files.
        """
        self.session.close()
        self.session = None

    def select_slx(self):
        """
        Select *.slx file when Browse button is clicked and populate the feature list combo box.
        """
        self.ScilsBrowseButton.setEnabled(False)
        self.FeatureListIdCombo.setEnabled(False)
        self.IntensityColumnNameCombo.setEnabled(False)
        self.OutputDirectoryBrowseButton.setEnabled(False)
        self.ExportFormatCombo.setEnabled(False)
        self.RunButton.setEnabled(False)

        if self.session is not None:
            self.close_session()

        # Get SLX path
        input_path = QFileDialog().getOpenFileName(self,
                                                   caption='Select SCiLS Lab File...',
                                                   dir='',
                                                   filter='SCiLS Lab (*.slx)')[0].replace('/', '\\')
        if os.path.isfile(input_path):
            self.args['scils'] = input_path
            self.ScilsLineEdit.setText(input_path)
            # Update combo box feature list names/IDs
            self.session = LocalSession(filename=self.args['scils'])
            dataset = self.session.dataset_proxy
            feature_lists = dataset.feature_table.get_feature_lists()
            for index, row in feature_lists.iterrows():
                self.FeatureListIdCombo.addItem('|'.join([row['name'], row['id']]))

        self.ScilsBrowseButton.setEnabled(True)
        self.FeatureListIdCombo.setEnabled(True)
        self.IntensityColumnNameCombo.setEnabled(True)
        self.OutputDirectoryBrowseButton.setEnabled(True)
        self.ExportFormatCombo.setEnabled(True)
        self.RunButton.setEnabled(True)

    def select_output_directory(self):
        """
        Select output directory when Browse button is clicked.
        """
        self.args['outdir'] = QFileDialog().getExistingDirectory(self, 'Select Directory...', '').replace('/', '\\')
        self.OutputDirectoryLineEdit.setText(self.args['outdir'])

    def export_format_selected(self, index):
        """
        Set export format when combo box is modified and show or hide mzML specific parameters if mzML is selected.

        :param index: Index of selected ExportFormatCombo item.
        """
        self.args['export_format'] = self.ExportFormatCombo.itemText(index)
        if self.args['export_format'] == 'mzML (Beta)':
            self.args['export_format'] = 'mzML'
            self.MzmlExportParametersLabel.setVisible(True)
            self.PolarityLabel.setVisible(True)
            self.PolarityPositiveRadio.setVisible(True)
            self.PolarityNegativeRadio.setVisible(True)
            self.BarebonesMetadataCheckbox.setVisible(True)
            self.MzEncodingLabel.setVisible(True)
            self.MzEncoding32bitRadio.setVisible(True)
            self.MzEncoding64bitRadio.setVisible(True)
            self.IntensityEncodingLabel.setVisible(True)
            self.IntensityEncoding32bitRadio.setVisible(True)
            self.IntensityEncoding64bitRadio.setVisible(True)
            self.CompressionLabel.setVisible(True)
            self.CompressionZlibRadio.setVisible(True)
            self.CompressionNoneRadio.setVisible(True)
        else:
            self.MzmlExportParametersLabel.setVisible(False)
            self.PolarityLabel.setVisible(False)
            self.PolarityPositiveRadio.setVisible(False)
            self.PolarityNegativeRadio.setVisible(False)
            self.BarebonesMetadataCheckbox.setVisible(False)
            self.MzEncodingLabel.setVisible(False)
            self.MzEncoding32bitRadio.setVisible(False)
            self.MzEncoding64bitRadio.setVisible(False)
            self.IntensityEncodingLabel.setVisible(False)
            self.IntensityEncoding32bitRadio.setVisible(False)
            self.IntensityEncoding64bitRadio.setVisible(False)
            self.CompressionLabel.setVisible(False)
            self.CompressionZlibRadio.setVisible(False)
            self.CompressionNoneRadio.setVisible(False)

    def feature_list_selected(self, index):
        """
        Set feature list when combo box is modified and populate list of column names from that feature list.

        :param index: Index of selected FeatureListIdCombo item.
        """
        self.ScilsBrowseButton.setEnabled(False)
        self.FeatureListIdCombo.setEnabled(False)
        self.IntensityColumnNameCombo.setEnabled(False)
        self.OutputDirectoryBrowseButton.setEnabled(False)
        self.ExportFormatCombo.setEnabled(False)
        self.RunButton.setEnabled(False)

        feature_list_name, feature_list_id = self.FeatureListIdCombo.itemText(index).split('|')
        self.args['feature_list_id'] = feature_list_id
        dataset = self.session.dataset_proxy
        feature_list = dataset.feature_table.get_features(self.args['feature_list_id'],
                                                          include_all_user_columns=True)
        for col in feature_list.columns.values.tolist():
            self.IntensityColumnNameCombo.addItem(col)

        self.ScilsBrowseButton.setEnabled(True)
        self.FeatureListIdCombo.setEnabled(True)
        self.IntensityColumnNameCombo.setEnabled(True)
        self.OutputDirectoryBrowseButton.setEnabled(True)
        self.ExportFormatCombo.setEnabled(True)
        self.RunButton.setEnabled(True)

    def intensity_column_name_selected(self, index):
        """
        Set name of the column to use for exported intensity values when a column name is selected.

        :param index: Index of selected IntensityColumnNameCombo item.
        """
        self.args['intensity_column_name'] = self.IntensityColumnNameCombo.itemText(index)

    def run(self):
        """
        Run workflow.
        """
        # Replace stdout with Progress Update Stream.
        sys.stderr = io.StringIO()

        # Gray out and disable ability to click all buttons
        self.ScilsBrowseButton.setEnabled(False)
        self.FeatureListIdCombo.setEnabled(False)
        self.IntensityColumnNameCombo.setEnabled(False)
        self.OutputDirectoryBrowseButton.setEnabled(False)
        self.ExportFormatCombo.setEnabled(False)
        self.RunButton.setEnabled(False)

        self.close_session()

        # Collect arguments from GUI
        self.args['outdir'] = str(self.OutputDirectoryLineEdit.text())
        if self.args['outdir'] == '':
            self.args['outdir'] = os.path.dirname(self.args['scils'])
        if not os.path.isdir(self.args['outdir']):
            os.mkdir(self.args['outdir'])
        if self.ExportSingleFileCheckbox.isChecked():
            self.args['export_single_file'] = True
        elif not self.ExportSingleFileCheckbox.isChecked():
            self.args['export_single_file'] = False
        if self.GetPrecursorFromIsolationWindowCheckbox.isChecked():
            self.args['get_precursor_from_isolation_window'] = True
        elif not self.GetPrecursorFromIsolationWindowCheckbox.isChecked():
            self.args['get_precursor_from_isolation_window'] = False
        self.args['relative_intensity_threshold'] = int(self.RelativeIntensityThresholdSpinBox.text())
        if self.PolarityPositiveRadio.isChecked() and not self.PolarityNegativeRadio.isChecked():
            self.args['polarity'] = 'positive'
        elif not self.PolarityPositiveRadio.isChecked() and self.PolarityNegativeRadio.isChecked():
            self.args['polarity'] = 'negative'
        if self.BarebonesMetadataCheckbox.isChecked():
            self.args['barebones_metadata'] = True
        elif not self.BarebonesMetadataCheckbox.isChecked():
            self.args['barebones_metadata'] = False
        if self.MzEncoding64bitRadio.isChecked() and not self.MzEncoding32bitRadio.isChecked():
            self.args['mz_encoding'] = 64
        elif not self.MzEncoding64bitRadio.isChecked() and self.MzEncoding32bitRadio.isChecked():
            self.args['mz_encoding'] = 32
        if self.IntensityEncoding64bitRadio.isChecked() and not self.IntensityEncoding32bitRadio.isChecked():
            self.args['intensity_encoding'] = 64
        elif not self.IntensityEncoding64bitRadio.isChecked() and self.IntensityEncoding32bitRadio.isChecked():
            self.args['intensity_encoding'] = 32
        if self.CompressionZlibRadio.isChecked() and not self.CompressionNoneRadio.isChecked():
            self.args['compression'] = 'zlib'
        elif not self.CompressionZlibRadio.isChecked() and not self.CompressionNoneRadio.isChecked():
            self.args['compression'] = 'none'

        # Check for required arguments
        if self.args['scils'] == '' or \
                self.args['outdir'] == '' or \
                self.args['export_format'] == '' or \
                self.args['feature_list_id'] == '' or \
                self.args['intensity_column_name'] == '':
            args_error = QMessageBox(self)
            args_error.setWindowTitle('Error')
            args_error.setText('One or more required arguments are missing. Please check export parameters and try again.')
            args_error.exec()

        # Convert to mgf
        if self.args['export_format'] == 'MGF':
            convert_iprmpasef_feature_list_to_mgf(slx=self.args['scils'],
                                                  outdir=self.args['outdir'],
                                                  feature_list_id=self.args['feature_list_id'],
                                                  intensity_column_name=self.args['intensity_column_name'],
                                                  export_single_file=self.args['export_single_file'],
                                                  get_precursor_from_isolation_window=self.args['get_precursor_from_isolation_window'],
                                                  relative_intensity_threshold=self.args['relative_intensity_threshold'])
        # Convert to mzml
        elif self.args['export_format'] == 'mzML':
            convert_iprmpasef_feature_list_to_mzml(slx=self.args['scils'],
                                                   outdir=self.args['outdir'],
                                                   feature_list_id=self.args['feature_list_id'],
                                                   intensity_column_name=self.args['intensity_column_name'],
                                                   polarity=self.args['polarity'],
                                                   barebones_metadata=self.args['barebones_metadata'],
                                                   mz_encoding=self.args['mz_encoding'],
                                                   intensity_encoding=self.args['intensity_encoding'],
                                                   compression=self.args['compression'],
                                                   export_single_file=self.args['export_single_file'],
                                                   get_precursor_from_isolation_window=self.args['get_precursor_from_isolation_window'],
                                                   relative_intensity_threshold=self.args['relative_intensity_threshold'])

        # Finish and/or error message boxes
        finished = QMessageBox(self)
        finished.setWindowTitle('iprm-PASEF Exporter')
        finished.setText('iprm-PASEF Exporter has finished running.')
        finished.exec()

        stderr = sys.stderr.getvalue()
        if stderr != '':
            error = QMessageBox(self)
            error.setWindowTitle('Error')
            error.setText(stderr)
            error.exec()

        self.ScilsLineEdit.setText('')
        self.FeatureListIdCombo.clear()
        self.IntensityColumnNameCombo.clear()

        self.ScilsBrowseButton.setEnabled(True)
        self.FeatureListIdCombo.setEnabled(True)
        self.IntensityColumnNameCombo.setEnabled(True)
        self.OutputDirectoryBrowseButton.setEnabled(True)
        self.ExportFormatCombo.setEnabled(True)
        self.RunButton.setEnabled(True)


def main():
    app = QApplication([])
    window = IprmpasefExporterWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
