# FreeGrid
> __Current State Of Work__ (October 2022) 
>  
> - The project is still in a test phase. It works and provides good results, but needs further evaluation.
> - The postprocessing and upsampling of the Head-Related Impulse Responses (HRIRs) is not part of the repository as this is currently topic of research ([research project](https://www.th-koeln.de/reskue)).

# Overview

<img src="./resources/doc/overview.png" alt="Overview" width="400"/>

FreeGrid is a GUI-application for fast and easy Head-Related Transfer Function (HRTF) measurements in regular rooms with only few additional hardware components. The system is based on a pair of in-ear microphones, a stationary loudspeaker and the HTC Vive system for tracking head movements (no HMD, just two [Trackers](https://www.vive.com/us/accessory/vive-tracker/)). A user can first measure some HRTFs for any number of freely selectable directions. In a second step, he can be guided with the help of an algorithm that suggests additional measurement positions for more uniform spherical coverage.

With the support of the OSC protocol it is also possible to use any other external tracking system (see [instructions](./resources/doc/manual.md)).

> **Please Note:** The system is not primarily intended for lay use at home. A certain amount of experience, or ambition, is required to set up the system.

Overview of the measurement procedure:  


1. Place a loudspeaker in the room ([room setup guidelines](./resources/doc/room_setup.md)), set up the Vive Lighthouses, connect the audio interface
2. Start SteamVR and start the FreeGrid application
3. Insert the in-ear microphones, mount the first Vive Tracker on the head
4. Calibrate the tracking system using the second Vive Tracker
5. Perform a center impulse response measurement with a reference microphone or one of the in-ear microphones
6. Perform as many HRTF measurements as desired by simply moving the head to the desired direction  
7. *Optional*: After that, the system can suggest additional measurement positions to improve the spherical coverage of the dataset  
8. *Optional*: With the microphones still in the ears, perform headphone measurements for one or more headphones to obtain individual headphone transfer functions and compensation filters

Check the full [usage instructions](./resources/doc/manual.md) for details.

 <br>
 <br>
 <br>
 
# Additional Hardware
## Measurement Equipment
Needless to say, a pair of in-ear microphones is required. We used [these DIY microphones](https://www.researchgate.net/publication/331988584_The_PIRATE_an_anthropometric_earPlug_with_exchangeable_microphones_for_Individual_Reliable_Acquisition_of_Transfer_functions_at_the_Ear_canal_entrance), but any available in-ear microphones should work.

A good measurement loudspeaker should be available. Ideally, the loudspeaker should be rather small to approximate a point source. (The low frequency response of the loudspeaker is not important, since a low-frequency extension replaces the low-frequency components of the HRTF below 200Hz anyway.)

Furthermore, an audio interface for capturing the IRs is required. It should at least have two in and outputs. A third input/output is very helpful to have a feedback loop (directly connecting Out3 -> In3) so that the software can compensate any software or DA/AD-latency.


## Tracking System
The application is intended to be used with the HTC VIVE system. This tracking system is widely available, easy to use, moderately priced, and offers very accurate and fast tracking capabilites. Unlike in many other VR/AR applications, neither the headset nor the contollers are needed, only two additionally available [Trackers](https://www.vive.com/de/accessory/vive-tracker/). 

The application can also receive external tracking data via Open Sound Control (OSC), e.g., if another tracking system is used. In this case, however, the external system must provide the relative angles between the user's head and the loudspeaker, as the OSC input only evaluates the values *Azimuth*, *Elevation* and *Radius*.

 <br>
 <br>
 <br>
 
# Install Notes:

The application requires Python with some external dependencies. For package managing, you can choose between [conda](https://docs.conda.io/en/latest/) or [pip](https://pypi.org/project/pip/), for each of which a configuration file is included (`conda_environment.yml` & `pip_requirements.txt`).

## Example install using __conda__ 
1. Download or clone this repository.
2. Install conda (Miniconda is sufficient) and download/clone this repository
3. Open a terminal window (or anaconda powershell) and navigate to the repository folder (where the `conda_environment.yml` and `main.py` files are located). To create a new Python environment with all necessary dependencies run 
    ```
    conda env create -f conda_environment.yml
    ```
4. Activate the new environment with    
    ```
    conda activate freegrid_env  
    ```  
    
5. To start the application run  
    ```
    python FreeGrid.py
    ```
    
 > On some machines the _vispy_ package causes problems. You can uninstall the vispy package, then the graphical display of the loudspeaker position will be disabled.  


 ## Install SteamVR
 In order to enable communication with the Vive system, [SteamVR](https://store.steampowered.com/app/250820/SteamVR/) has to be running in the background. SteamVR can be installed via Steam (user account required).
 <br>
 <br>
 <br>


# Related Publications

Bau, D., Lübeck, T., Arend, J. M., Dziwis, D. T., and Pörschmann, C. (2021).“Simplifying head-related transfer function measurements: A system foruse in regular rooms based on free head movements,” in Proceedings of the International Conference on Immersive and 3D Audio (I3DA),September 08-10, 2021 (Bologna, Italy), 1–6. doi:10.1109/I3DA48870.2021.9610890
([link](https://www.researchgate.net/publication/354495254_Simplifying_head-related_transfer_function_measurements_A_system_for_use_in_regular_rooms_based_on_free_head_movements))

Bau, D., and Pörschmann, C. (2022). “Technical Evaluation of an Easy-To-UseHead-Related Transfer Function Measurement System,” in Proceedings of the 48th DAGA, March 21–24, 2022 (Stuttgart, Germany), 367–370. 
([link](https://www.researchgate.net/publication/359636065_Technical_Evaluation_of_an_Easy-To-Use_Head-Related_Transfer_Function_Measurement_System))
