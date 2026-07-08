User Guide
==========

Overview
--------

MeshDeWarper allows you to characterise and compensate for non-linear
positioning errors across the entire printable area of your 3D printer.

Workflow
--------

1. **Print a calibration pattern** — generate a PDF, SVG, or STL pattern
   and print it on your 3D printer.

2. **Measure the printed pattern** — measure the actual positions of the
   calibration points (manually or with a camera).

3. **Create a calibration profile** — enter the measured positions into the
   editor, or use the vision assistant to detect points from a photo.

4. **Apply the correction** — the plugin warps G-code before export,
   compensating for the measured distortion.

5. **Verify the result** — print a test object to verify the calibration.
