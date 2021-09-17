# GuidedHRTFsPython
> __Current State Of Work__ (August 2021) 
>  
> - The project is still in a test phase. It works and provides good results, but needs further evaluation.
> - The postprocessing and upsampling of the Head-Related Impulse Responses (HRIRs) is not part of the repository as this is currently topic of research ([research project](https://www.th-koeln.de/reskue)).
> - We are still looking for a better project name...

# Overview

<img src="./resources/doc/overview.png" alt="Overview" width="400"/>

GuidedHRTFs is a GUI-application for fast and easy Head-Related Transfer Function (HRTF) measurements in regular rooms with only few additional hardware components. The system is based on a stationary loudspeaker and the HTC Vive system for tracking head movements (no HMD, just two [Trackers](https://www.vive.com/us/accessory/vive-tracker/)). A user can first measure some HRTFs for any number of freely selectable directions. In a second step, he can be guided with the help of an algorithm that suggests additional measurement positions for more uniform spherical coverage.

> The system is not primarily intended for lay use at home. A certain amount of experience, or ambition, is required to set up the system.

The measurement procedure is as follows:  


1. Place a loudspeaker in the room, put in-ear microphones on, connect the audio hardware
2. Mount a Vive Tracker on the head and start SteamVR  
3. Run the application and perform a quick calibration routine with a second Vive Tracker
4. (Optional: Perform a center impulse response measurement with a reference microphone)  
5. Perform as many Head-Related Impulse Response (HRIR) measurements as desired by simply moving the head to the disired direction  
6. After that, the system can suggest additional measurement positions to improve the spherical coverage of the dataset  
7. (Optional: With the microphones still in the ears, perform headphone measurements for one or more headphones to obtain individual headphone transfer functions and compensation filters)  

 <br>
 <br>
 <br>
 
# Additional Hardware
## Measurement Equipment
Needless to say, a pair of in-ear microphones is required. We used [these DIY microphones](https://www.researchgate.net/publication/331988584_The_PIRATE_an_anthropometric_earPlug_with_exchangeable_microphones_for_Individual_Reliable_Acquisition_of_Transfer_functions_at_the_Ear_canal_entrance), but any available in-ear microphones should work.

A good measurement loudspeaker should be available. Ideally, the loudspeaker should be rather small to approximate a point source.
> The low frequency response of the loudspeaker is not that important, as we replace the low-frequency components of the HRTF below 200Hz by an appropriate low-frequency extension [[1](#references)].

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
    conda activate Guided_HRTFs_env  
    ```  
    
5. To start the application run  
    ```
    python main.py
    ```
    
 > On some machines the _vispy_ package causes problems. You can uninstall the vispy package, then the graphical display of the loudspeaker position will be disabled.  

 <br>
 <br>

 ## Install SteamVR
 In order to enable communication with the Vive system, [SteamVR](https://store.steampowered.com/app/250820/SteamVR/) has to be running in the background. SteamVR can be installed via Steam (user account required).
  <br>
 <br>
 <br>

# Before starting the application

SteamVR needs to be running in the background with both trackers connected

  <img src="./resources/doc/steamvr_status.png" alt="Overview" width="300"/>
 <br>
 <br>
 <br>

# Configuration
<img src="./resources/doc/configure_window.png" alt="Overview" width="600"/>
<br>
<br>

## Configure Audio Hardware
- In the _Audio Device Status_ panel, you can select the audio input and output device, the samplerate and a custom channel assignment. This comes handy in case you want the input channels 1&2 for the measurements, but maybe input/output channel 7 for the feedback loop.
- Channel Assignment:
    - __Output Excitation__: Output for measurement speaker or left channel during headphone measurement
    - __Output Excitation 2__: Right channel for headphone measurement
    - __Output Feedback Loop__: Mirrored output of the excitation signal
    - __Input Left Ear Mic__: Input for left in-ear microphone or reference microphone during center measurement
    - __Input Right Ear Mic__: Input for right in-ear microphone.
    - __Input Feedback Loop__: Direct input for "dry" excitation signal from __Output Feedback Loop__
- Don´t change the audio settings during a measurement. If needed, you can change the channel configurations for HRIR, center and HPCF measurements, but do not change the samplerate once you started.

The image below shows audio routing examples for the three different measurement cases:
<img src="./resources/doc/measurement_wiring.png" alt="Measurement Wiring" width="600"/>

<br>
<br>

## Tracker Calibration
### A) Calibration using Vive Trackers

Two Vive Trackers are needed for the calibration. The acutal _head tracker_ and a _calibration tracker_. After the calibration, the _calibration tracker_ can be turned off.

> By default, the application assigns the _head tracker_ role to the first tracker it detects, thus the first one that was connected to SteamVR. With the `Switch Tracker Roles` button, the roles of the _head tracker_ and _calibration tracker_ can be switched. Before the calibration, the correct role assignment can be easily verified by rotating the _calibration tracker_ while holding it and looking at the displayed angle. The rotation should not affect the angle (see _Background information_ below). 

1. __Calibrate Speaker Position:__ Hold the _calibration tracker_ to the acoustical center of the speaker and press the `Calibrate Speaker` button in the GUI.

2. __Calibrate Tracker Offset:__ With the _head tracker_ attached to the head, hold the _calibration tracker_ to each ear (the bottom center of the tracker to the ear canal) and press the corresponding calibration button (`Calibrate Left / Right Ear`).

3. __Calibrate Tracker Rotation:__ Place the _calibration tracker_ on a planar surface (e.g. floor), pointing towards a desired view direction (LED on the tracker facing in opposite direction). Point the head into the same direction, so that the orientation of the _calibration tracker_ matches the orientation of the head, and press the `Calibrate Orientation` button. 

The calibration steps can be repeated in any order, if necessary. If the _head tracker_ slips during the measurement, the calibration steps 2 & 3 should be repeated. In the same way, calibration step 1 should be repeated if the loudpseaker is moved during the measurement.

<img src="./resources/doc/tracker_calibration_steps.png" alt="Tracker Calibration Steps" width="600"/>
<br>
<br>


> Background information on the calibration: In the uncalibrated state, the displayed angle simply represents the spherical angle between the _head tracker_ as the origin of a spherical coordinate system and the _calibration tracker_ as a reference point in space, as shown in the picture below:
>
> <img src="./resources/doc/tracking_coordinates.png" alt="Measurement Wiring" width="220"/>
>  
>The calibration then "connects" the tracking to head center and loudspeaker:
>
> - While calibrating the speaker position in the first calibration step, the current position of the _calibration tracker_ is stored. From then on, this stored position is used for the reference point and the _calibration tracker_ only serves for calibration.  
> - The other two calibration steps are due to the fact that the _head tracker_ does not represent the actual rotation center of the head.
>   - In order to get the position of the head center, the positions of the ears relative to the _head tracker_ are stored. The head center is then approximated as the midpoint between the ears.
>   - The third calibration steps compensates the rotational offset of the tracker as it can be placed arbitrarily on the head.

<br>
<br>
<br>

### B) Calibration using external tracking system (OSC)
In case you are using another tracking system wich can communicate via OSC, you do not have to perform a calibration. The external tracking system has to take care of the calibration. The external system should supply the __relative__ angle (azimuth, elevation, and radius) between the loudspeaker and the user's head, and __not__ the head orientation of the user. The bottom left panel _Vive Tracker Status_ becomes _OSC Input Status_ and will blink if OSC messages are received. 

<br>
 <br>
 <br>

# Performing Measurements
<br>
 
<img src="./resources/doc/measurement_window.png" alt="Overview" width="600"/>

> Before starting a measurement session, the session should be given a name so that the exported file can be identified later on. For every new session, the session name must be changed, otherwise the previos session will be overwritten.

1. Perform a center measurement with a reference microphone. Place the microphone where the head center will be during the measurements and connect the microphone to the left input (Ch1) of the audio interface. 
2. Place the in-ear microphones in the ear canals and connect them to the left / right input of the audio interface (Ch1/Ch2). Set adequate levels for the output and input of the audio interface
3. Perform measurements. It is best to activate the _Auto Measurement Mode_, where a measurement is triggered when the head is still for 2 seconds. During the measurement, keep the head still for the entire time (even after the sweep is finished) until a sound for a successfull or a failed measurement signals the end of the measurement. 
    > You can pause the automatic measurement at any time to have a look at the measurements already done in the `Data List` tab. There, you can also delete erroneous measurements. The source positions of the measurements will also be shown in the virtual speaker position display.
    <br>

    > A good starting point is to perform around 30 measurements for a full spherical coverage. This should take around 5 minutes.
3. After the inital measurements, the _Point Recommender_ algorithm can suggest additional points. The recommended point will show up in the virtual speaker position display. By pressing `Start Guidance`, a spoken word guidance tells where to move the head (always assuming you are initally looking towards the speaker), followed by a guiding "ping" tone indicating the distance to desired view direction. It is a two step procedure, first guiding the head orientation on the horizontal plance, and then guiding the head orientation to the exact spot by tilting down, up, left, or right.  

<br>
 <br>

# Performing Headphone Measurements

A headphone compensation filter (HPCF) is required for accurate binaural reproduction using the acquired HRTFs. Measuring the individual HPCF directly after the individual HRTF measurements has the advantage of compensating for the in-ear microphones used and their possibly uneven placement in the ear canal.

In the application, it is possible to measure headphone impulse responses (HPIR) from which a HPCF can be estimated.

1. Set the name of the headphone
2. Connect the headphones to the stereo output of the audio interface (Ch1/Ch2).
3. Put on the headphones while keeping the in-ear microphones from the HRTF measurement in place. 
4. Perform about 10 to 15 headphone measurements. Put the headphones on and off between each measurement, resulting in slightly different positions of the headphones on the head for each measurement
5. For measuring another pair of headphones, simply click `Clear/Start New`. The HPIRs have already been saved (see section _Output & Post Processing_) .


The plots during the HPCF measurement (see picture below) show the magnitude responses of the HPIRs (left/right separated) and an estimation of the resulting HPCF filter based on [this](https://github.com/spatialaudio/hptf-compensation-filters)[2] approach. The estimated filter is not exported. 

<img src="./resources/doc/hp_measurement.png" alt="Overview" width="300"/>

> In our lab, we are mostly using [this](https://github.com/spatialaudio/hptf-compensation-filters) approach for generating HPCF filters, where a variable parameter _beta_ is used to regularize the inversion. Since this regularization parameter has to be set by hand, we considered it useful to include an estimation plot of the final HPCF (with variable _beta_) in the application. 

<br>
 <br>
 <br>

# Data Export
The application has no export functionality. The measurement data is bundled after each single measurement as a Matlab file (.mat) and stored by default in the folder "Measurements" relative to the root folder of the Python-application (The export folder can be customized in the Configure-panel). Three different .mat files are stored: 

* **HRIRs**: Impulse repsonses and raw recorded signals for each HRIR, together with the corresponding source positions of every HRIR in [Az(0...360°), El(90...-90°), R(m)]. Furthermore, metadata such as the used sampling rate, head-dimension and sweep parameters are stored. The filename consists of `"measured_points_{session name}_{current date}.mat`.
* **Center IR** IR and raw signals for the center measurement. If the center measurement is performed multiple times, every measurement is stored (in the same .mat-file).
* **Headphone IRs**: IRs and raw signals for each HPIR measurement repetition with the regularization amount parameter _beta_ from the HPCF estimation. The HPCF estimate is not exported. The filename consists of `"headphone_ir_{hp name}_{current date}.mat`.

> Note that if a .mat file with the same name already exists, it will be overwritten!

The measurement system provides deconvolved HRIRs without further post-processing. Further post-processing and upsampling should be done seperately in Matlab, at least in the current state of work. Besides the HRIRs, additionaly the raw recorded sweeps and the feedback loop sweeps are stored (if no real feedback loop was recorded, the excitation signal is stored as the feedback loop).

<br>
<br>

# References

[1] Bernschütz, B. (2013). A Spherical Far Field HRIR/HRTF Compilation of the Neumann KU 100. Fortschritte Der Akustik -- AIA-DAGA 2013, 592--595. http://www.audiogroup.web.fh-koeln.de/FILES/AIA-DAGA2013_HRIRs.pdf

[2] Schärer, Z. and Lindau, A. (2009): Evaluation of Equalization Methods for Binaural Synthesis. Proc. of the 126th AES Convention
