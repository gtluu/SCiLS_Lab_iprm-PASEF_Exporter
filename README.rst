About
=====
iprm-PASEF Exporter is a simple tool to create MGF and mzML files from iprm-PASEF datasets acquired on the Bruker
timsTOF fleX and processed in SCiLS Lab.

As of SCiLS Lab 2025b, creation of *.mgf and *.mzML files containing MS/MS fragmentation data is a manual process
requiring user created files. To assist in this process, a script utilizing the SCiLS Lab Python API has been created
to export MS/MS data. Importantly, prior to export, feature lists should be manually validated to ensure that the
spatial distribution of precursor and fragment features match. Currently, T-ReX^3 feature finding only takes the 1/K0
window into account when correlating fragments to precursors; spatial distribution is not considered.

Installation
============
For information of installing SCiLS Lab iprm-PASEF Exporter, please see the
`Installation <https://gtluu.github.io/SCiLS_Lab_iprm-PASEF_Exporter/installation.html>`_ page.

Usage
=====
For information on using SCiLS Lab iprm-PASEF Exporter, please see the
`Usage <https://gtluu.github.io/SCiLS_Lab_iprm-PASEF_Exporter/usage.html>`_ page.
