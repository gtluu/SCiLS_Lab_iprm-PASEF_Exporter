Installation
============

GUI in Windows
--------------
The GUI version of the SCiLS Lab iprm-PASEF Exporter tool can be run by downloading it from
`the Github release page for this repo <https://github.com/gtluu/SCiLS_Lab_iprm-PASEF_Exporter/releases>`_. Unzip the
file and run ``iprm-PASEF_Exporter.exe``. See the :doc:`Usage <usage>` page for more information on using this tool.
No installation is required if the packaged GUI is being used.

Manual Installation on Windows
------------------------------
1. Download and install `Anaconda for Windows <https://repo.anaconda.com/archive/Anaconda3-2025.06-0-Windows-x86_64.exe>`_ if not already installed. Anaconda3-2025.06-0 for Windows is used as an example here. Follow the prompts to complete installation.

2. Download and install `Git for Windows <https://github.com/git-for-windows/git/releases/download/v2.50.1.windows.1/Git-2.50.1-64-bit.exe>`_ if not already installed.

3. Run ``Anaconda Prompt``.

4. Create a conda instance.

   .. code-block::

        conda create -n iprmpasef_exporter python=3.11

5. Activate conda environment.

   .. code-block::

        conda activate iprmpasef_exporter

6. Install requirements.

   .. code-block::

        pip install -r https://raw.githubusercontent.com/gtluu/SCiLS_Lab_iprm-PASEF_Exporter/refs/heads/main/requirements.txt

7. Install SCiLS Lab API Python package.

   .. code-block::

        pip install "C:\Program Files\SCiLS\SCiLS Lab\APIClients\Python\scilslab-8.0.121-cp311-cp311-win_amd64.whl"

8. Install iprm-PASEF Exporter package.

   .. code-block::

        pip install git+https://github.com/gtluu/SCiLS_Lab_iprm-PASEF_Exporter

9. SCiLS Lab iprm-PASEF Exporter is now ready to use. See the :doc:`Usage <usage>` page for more details.