# HTS Magnet Data Plotting and Analysis

This project provides Python scripts for loading, processing, and visualizing magnet measurement data from multiple experiments. It is designed to help compare and analyze magnetic field strengths under different conditions.

## Features

- Load and process HTS magnet test data from LabView export files, producing a cleaned dataset with sensor corrections.
- Overlay scatter plots of magnetic field vs. current for different datasets.
- Customizable plot appearance (labels, colors, titles)
- Support for swapping current columns for specific datasets
- Publication-quality plot output with configurable styles

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


