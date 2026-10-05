# HTS Magnet Data Plotting and Analysis

This project provides Python scripts for loading, processing, and visualizing magnet measurement data from multiple experiments. It is designed to help compare and analyze magnetic field strengths under different conditions.

## Features

- Load and process HTS magnet test data from LabView export files, producing a cleaned dataset with sensor corrections.
- Overlay scatter plots of magnetic field vs. current for different datasets.
- Customizable plot appearance (labels, colors, titles)
- Support for swapping current columns for specific datasets
- Publication-quality plot output with configurable styles

## Run it in your browser (no install)

The `docs/` folder contains a browser version of MagTrace (Cleaner, Plotter and Combiner) that runs entirely client side. Nothing is uploaded: files are parsed and plotted in your browser.

Once GitHub Pages is enabled for this repository it is served at:

**https://fionnf.github.io/MagTrace/**

### Enabling GitHub Pages (one time, repository owner)

1. Open the repository on GitHub and go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Push to `master` (or run the *Deploy MagTrace web app to GitHub Pages* workflow from the **Actions** tab). The workflow in `.github/workflows/pages.yml` publishes the `docs/` folder.

Alternatively choose **Deploy from a branch**, branch `master`, folder `/docs`; the same files are served without the workflow.

### Using the web version

- **Cleaner**: load the raw LabView export (any extension; semicolon separated, first line skipped, two header rows). Choose the timestamp unit, tick the columns to plot, set a time range and excluded regions, then **Save cleaned CSV**. The file is downloaded and also made available to the other tabs.
- **Plotter**: pick a cleaned file (saved in the Cleaner or loaded from disk), choose X, Y, Y2 and Y3 columns and press **Plot**. Zoom by dragging, export a PNG with the camera icon.
- **Combiner**: tick the cleaned files to append, order them with the arrows, and press **Combine & save**. Timestamps are offset so the files run consecutively.

To work on the web version locally, serve the folder with any static server, e.g. `python -m http.server -d docs` and open http://localhost:8000/.

## Desktop version

## Requirements

- Python 3.7+
- pandas
- matplotlib
- numpy

## Installation
- Install python
- Install dependencies with: `pip install -r requirements.txt`

## Usage
- Run the script with the command: `python main.py` from the root directory in the command line, or run the file in your IDE of choice.
### Cleaning Data
- Use the clean data tab to load and process raw data files, make sure to set the filetype to 'All' to be able to open the labview file. 
- Select sensors to plot and apply any necessary corrections.
- Select range of data to plot.
- Select ranges of data to remove.
- Save the cleaned data to a new file.
### Plotting Data
- Use the plot data tab to load cleaned data files (the ones you saved in the previous step). These should be visible in the file browser.
- Select datasets to plot.
- Choose whether to swap current columns for specific datasets.
- Customize plot appearance (labels, colors, titles).
- Generate the plot.
- Save the plot to a file in the desired format (e.g., PNG, PDF).
### Combining Data
- In the case od multiple datasets, you can combine them into a single plot for the same magnet. Eg. if you have multiple datasets for the same magnet, you can select them and plot them together consecutively like after a LabView crash. 
- Use the combine data tab to load cleaned data files.
- Use these combined files in the plot data tab to generate a single plot with all selected datasets.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements
This project was developed as part of the HTS magnet development in the Barnes Group at ETH. Special thanks to the team for their contributions and support.


