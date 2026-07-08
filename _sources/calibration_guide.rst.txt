Calibration Guide
=================

This guide walks through the full calibration workflow: printing a pattern,
measuring points, creating a profile, and verifying the result.

Print a Calibration Pattern
---------------------------

1. Choose a pattern type:

   * **PDF** — print on paper for manual measurement
   * **SVG** — vector format editable in illustration tools
   * **STL** — 3D-print a physical reference grid on your printer bed

2. Configure the pattern for your printer's bed dimensions and preferred
   grid spacing (10 mm is a good default).

3. Generate and print the pattern.

Example — generate a PDF pattern programmatically:

.. code-block:: python

   from pathlib import Path
   from mesh_de_warper.patterns import PdfPatternGenerator, PatternConfig

   config = PatternConfig(bed_width=220, bed_height=220, spacing=10)
   gen = PdfPatternGenerator()
   gen.generate(config, Path("calibration_pattern.pdf"))

Measure the Printed Points
--------------------------

Measure the **actual** position of each printed calibration point relative to
its expected position. Record the X and Y deviation for every point.

* Use callipers for best accuracy.
* For a quicker but less precise method, use the :doc:`vision_guide` to detect
  points from a photograph.

Create a Calibration Profile
----------------------------

Enter the measured offsets into a calibration profile:

.. code-block:: python

   from mesh_de_warper.core import Calibration, Point
   from mesh_de_warper.interpolation import BilinearInterpolation

   cal = Calibration.for_bed(
       width=220, height=220, spacing=10,
       interpolation=BilinearInterpolation(),
   )

   # Set offsets at specific grid positions
   mesh = cal.mesh
   mesh[0, 0] = Point(x=0, y=0, offset_x=0.12, offset_y=-0.08)
   mesh[0, 1] = Point(x=10, y=0, offset_x=0.15, offset_y=-0.05)
   # ... repeat for all measured points

   # Save to a profile
   profile = cal.to_profile()
   profile.printer = "MyPrinter"
   profile.save(Path("my_calibration.json"))

You can also use the :doc:`../api_reference` for details on each API.

Apply the Correction
--------------------

With a calibration profile loaded, the plugin warps G-code before export:

.. code-block:: python

   from pathlib import Path
   from mesh_de_warper.core import Calibration
   from mesh_de_warper.gcode.warper import GCodeWarper
   from mesh_de_warper.interpolation import BilinearInterpolation

   cal = Calibration.for_bed(
       width=220, height=220, spacing=10,
       interpolation=BilinearInterpolation(),
   )

   warper = GCodeWarper(cal)
   warper.warp_file(Path("input.gcode"), Path("output.gcode"))

Verify
------

Print a test object after calibration:

1. Print a simple geometric object (e.g., a 100 mm square).
2. Measure the actual dimensions.
3. If further correction is needed, repeat the calibration with
   finer grid spacing or a different interpolation algorithm.
