Installation
============

Prerequisites
-------------

* Ultimaker Cura 5.0 or later
* Python 3.12 or later

Installing from Release
-----------------------

1. Download the latest ``.curaplugin`` from the `Releases page`_.
2. Open Cura and go to **Extensions -> Manage Plugins**.
3. Click **Install from file** and select the downloaded package.
4. Restart Cura.

Installing from Source
----------------------

.. code-block:: bash

   git clone https://github.com/cura-xy-calibration/CuraXYCalibration.git
   cd CuraXYCalibration
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,test]"

.. _Releases page: https://github.com/cura-xy-calibration/CuraXYCalibration/releases
