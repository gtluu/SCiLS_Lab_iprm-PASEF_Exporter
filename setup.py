from setuptools import setup

setup(name='iprm-PASEF_Exporter',
      version='0.1.0',
      description='iprm-PASEF MS/MS Export from SCiLS Lab Datasets.',
      url='',
      author='Gordon T. Luu',
      author_email='Gordon.Luu@Bruker.com',
      license='GPL-2.0',
      packages=['exporter'],
      entry_points={'console_scripts': ['get_feature_lists=exporter.get_feature_list_ids:main',
                                        'get_intensity_column_names=exporter.get_intensity_column_names:main',
                                        'generate_iprmpasef_precursor_lists=exporter.iprm_precursor_scheduler:main',
                                        'iprmpasef_to_mgf=exporter.mgf:main',
                                        'iprmpasef_to_mzml=exporter.mzml:main']},
      install_requires=['numpy', 'pandas', 'pyopenms', 'pyteomics', 'psims', 'PySide6'])
