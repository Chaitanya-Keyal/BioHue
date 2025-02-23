# BioHue

BioHue is an application that analyzes images based on their color properties and classifies
them into predefined categories. It consists of a Python-FastAPI backend, a React-Next.js
frontend, and a MongoDB database for storing user data and analysis history.

## Key Features

- User Authentication: Users can register and log in to upload images and view their analysis history.
- Image Analysis Workflow:

  - Users select a substrate and upload an image.
  - The backend processes the image and classifies it as Positive, Negative, or Moderate based on [predefined thresholds](backend/src/substrates.json).

- History Tracking: Analysis results are stored in MongoDB, allowing users to view past results.

## Algorithm Breakdown

OpenCV is used for image analysis, following these steps:

1. Extracting the Prominent Region

   - Image Decoding: The uploaded image is converted from bytes into an OpenCV matrix.
   - Saturation-Based Region Detection:
     - The image is converted to HSV color space, and a binary mask highlights areas with high saturation.
     - Morphological operations (opening and closing) refine the mask by removing noise and filling gaps.
   - Contour Selection:
     - The algorithm detects contours in the binary mask and selects the largest one.
     - If the detected region is too small compared to the total image area, it is ignored.
   - Glare Removal:
     - Pixels with brightness exceeding a glare threshold are identified.
     - The average color of surrounding non-glare pixels is computed and used to replace glare-affected areas.
   - Circular Cropping:
     - A bounding box is drawn around the selected region, and a circular mask is applied.
     - This ensures consistency in shape and removes unnecessary background regions.

2. Computing the Metric

   - The extracted region’s RGB channels are separated.
   - A predefined mathematical formula (specific to the selected substrate) is applied to compute a numeric metric which is then classified.
