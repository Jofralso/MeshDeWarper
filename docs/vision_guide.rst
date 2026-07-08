Vision Guide
============

The experimental computer vision assistant detects calibration points
from a photograph of your printed pattern, reducing manual measurement
effort.

Prerequisites
-------------

* A camera or smartphone capable of taking a flat, well-lit photo of
  the entire calibration pattern.
* The ``vision`` extras installed:

  .. code-block:: bash

     pip install "MeshDeWarper[vision]"

Taking a Good Photo
-------------------

1. Place the printed pattern on a flat surface.
2. Position the camera directly above the pattern (top-down view).
3. Ensure even lighting — avoid shadows and glare.
4. Include the entire pattern in the frame.
5. Keep the camera parallel to the pattern to minimise perspective distortion.

Workflow
--------

The vision assistant processes an image through three stages:

1. **Lens correction** — removes optical distortion from the camera lens.
2. **Perspective correction** — warps the image to a top-down orthographic view.
3. **Point detection** — locates the printed calibration points and estimates
   their deviation from expected positions.

.. code-block:: python

   from pathlib import Path
   from mesh_de_warper.vision import VisionCalibrationAssistant

   assistant = VisionCalibrationAssistant()
   result = assistant.process_image(Path("calibration_photo.jpg"))

   if result.candidates:
       cal = result.candidates[0].to_calibration()
       print(f"Detected {len(result.candidates[0].points)} points")
   else:
       print("No calibration candidates found")

Understanding Results
---------------------

The assistant returns a list of ``CandidateCalibration`` objects, each
containing:

* ``points`` — list of detected ``(x, y, offset_x, offset_y)`` values
* ``confidence`` — a score from 0..1 indicating detection quality

Review each candidate carefully before using it. The vision system is
experimental and may produce false positives, especially with:

* Poor lighting or focus
* Non-flat surfaces
* Patterns that are partially outside the frame
* High lens distortion not fully corrected

Manual Override
---------------

You can always override individual detected points before creating a
calibration profile. Combine the vision assistant with manual measurements
for best results:

.. code-block:: python

   candidate = result.candidates[0]
   for point in candidate.points:
       print(f"({point.x:.1f}, {point.y:.1f}): "
             f"offset ({point.offset_x:.3f}, {point.offset_y:.3f})")
