# GuidedHRTFsPython

## Install Notes:
The whole application is Python, so in order to run it you need Python with a bunch of external packages. 
We highly recommend using [conda](https://docs.conda.io/en/latest/) for this.

1. Install conda and download/clone this repository
2. Navigate to the repository folder (where the `environment.yml` and `main.py` files are). To create a new Python environment with all needed dependencies run
    ```sh
    conda env create -f environment.yml
    ```
3. Activate the new environment with
    ```
    conda activate Guided_HRTFs_env
    ```
    (to use another environment name edit the first line of the `environment.yml` file before creating)
4. To start the application run
    ```
    python main.py
    ```
    > SteamVR needs to be running in the background with both trackers connected BEFORE starting the application!
    
> Note for macOS: The openvr dependency in `environment.yml` is set to an older version to comply with the no longer maintained SteamVR for macOS ('macos_default beta'). For Windows, the most recent version of openvr can be used (edit the `environment.yml` file accordingly). 