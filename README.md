# GuidedHRTFsPython
## Overview
<img src="./resources/doc/overview.png" alt="Overview" width="400"/>

This project is a GUI-application for fast and easy Head-Related Transfer Function (HRTF) measurements. The measurement system can be used in almost any room, wether echoic or anechoic. It has low equipment requirements and is very flexible, it can be used with any loudspeaker, in-ear-microphones, audio interface and market-avaiblable tracking system. The user can control the resolution and accuracy of the resulting grid with the effort he spends during measurement, even giving him the possibility to focus on directions he is interested in. He is free to make full spherical measurements, horizontal measurements or measurements only covering desired areas.

The procedure can be outlined as following:
1. Place a loudspeaker in the room, put on some in-ear microphones, wire everything up
2. Put the VIVE tracker on the head and start SteamVR
3. Run the application and do a quick calibration routine
4. (Beneficial: Perform a reference room-IR measurement with a reference microphone)
5. Perform as many HRIR measurements as you wish, by simply moving your head to the disired direction
6. After that, the system can suggest additional measurement positions to improve the spherical coverage of the dataset
7. (Beneficial: With the mics still in the ears, perform some headphone IRs (HPIRs) for one or more headphones)

> Currently, the system does not apply any post-processing or upsampling to the measured HRIRs. This is done via an external Matlab script

Of course, it will not work as fluently as advertised here, at least for the first run. I would suggest to spend some minutes on reading the notes below, they should clear everything up. It is indeed very easy.

We are still looking for a better name for the project...

 <br>
 <br>
 
## Additional Hardware
### Measurement Equipment
Of course, a pair of in-ear microphones is needed. We used [these DIY microphones](https://www.researchgate.net/publication/331988584_The_PIRATE_an_anthropometric_earPlug_with_exchangeable_microphones_for_Individual_Reliable_Acquisition_of_Transfer_functions_at_the_Ear_canal_entrance), but any available in-ear microphone will work.

A good measurement loudspeaker with an adequately good magnitude and phase response. It should be rather small to closely match a point source.
> Low frequency response of the speaker is not that important, since the low frequency range is not that important for an HRTF and is usually crowded with undesired room modes. We omit and replace the low frequency below 200Hz of the HRTFs anyway[[1](#references)].

An audio interface for capturing the IRs an audio interface. It should at least has 2In/2Out. A third I/O is very helpful to have a feedback loop (directly connecting Out3 -> In3), than the software can directly compensate any software- or DA/AD-latency. Digitally controlled preamps of the inputs are a big benefit to avoid L/R level mismatch.
### Tracking System
The application is highly specialized to be used with the HTC VIVE system. It is widely available, easy to use, moderate priced and offers very accurate and fast tracking capabilites. Despite many other VR/AR applications, neither the Headset nor the Contollers are needed, only the additionally available [Trackers](https://www.vive.com/de/accessory/vive-tracker/). 

Tracker handling is already built in the application (SteamVR is needed nevertheless), and with an integrated simple calibration routine, very accurate relational angles between head and loudspeaker can be achieved. 

The application is also capable of receiving external tracking data via Open Sound Control (OSC), if a different tracking system is used. But then the external system has to take care of determining the relative angle between head and loudspeaker, because the OSC input only listens to the values *Azimuth*, *Elevation* and *Radius*.

 <br>
 <br>
 
## Install Notes:
The whole application is Python, so in order to run it you need Python with a bunch of external packages. 
We highly recommend using [conda](https://docs.conda.io/en/latest/) for this.

1. Install conda (Miniconda is sufficient) and download/clone this repository
2. Open your terminal window (or anaconda prompt) and navigate to the repository folder (where the `environment.yml` and `main.py` files are located). To create a new Python environment with all necessary dependencies run
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
 
 <br>
 <br>
 
## Quick Start

### Configure
SCREENSHOT HERE
TBD

### Performing Measurements
SCREENSHOT HERE
TBD

Before starting a measurement session, it is best to give the session a name, so the exported file will be 
! for every new session, the session name MUST be changed, otherwise the previos session will be overwritten
! if the session name is chaned during a session, 

### Performing Headphone Measurements
SCREENSHOT HERE
TBD

> We are mostly using [this](https://github.com/spatialaudio/hptf-compensation-filters) approach for generating HPCF filters, where a variable regularization parameter _beta_ is used to damp inversion overshoots. Since this regularization parameter has to be set individually, we found it useful to include an estimation plot of the final HPCF (with variable _beta_) in the application. 

 <br>
 <br>

## Output & Post Processing
The output of the measurement system are the deconvolved IRs, but without any further post-processing. The post-processing and upsampling is meant to be done seperately in Matlab, at least in the current state of work. Besides the deconvoled IR, additionaly the raw recorded sweep & feedback loop sweep is stored (if no real feedbackloop was recorded, the excitation signal is stored as the feedback loop).

Currently, the measured IRs are immediately stored as a bundled .mat file after every measurement. The default save path is "$PROJECT_DIR/Measurements", but it can be changed to any path in the _Configure_ panel. Whenever a change is applied to the measurements (IR added or IR removed), the export file is immediately updated.  Three different .mat files are stored: 

* **HRIRs**: IRs & raw signals for each HRIR, together with the corresponding source positions of every HRIR in [Az(0...360°), El(90...-90°), R(m)]. Besides that, some metadata like used samplingrate and head-dimensions (if they were measured) are stored. The filename consists of `"measured_points_{session name}_{current date}.mat`. If multiple sessions are done (with different session names), each session is stored in a seperate file.
* **Reference IR** IR & raw signals for the reference (center) measurement. If the reference measurement is performed multiple times, every measurement is stored (in the same .mat-file)
* **Headphone IRs**: IRs & raw signals for each HPIR measurement repetition with the regularization value _beta_ from the HPCF-estimation. The HPCF estimate is NOT exported. The filename consists of `"headphone_ir_{hp name}_{current date}.mat`. If multiple HPs are measured, multiple files are exported. 

<br>
<br>

## References

[1] Bernschütz, B. (2013). A Spherical Far Field HRIR/HRTF Compilation of the Neumann KU 100. Fortschritte Der Akustik -- AIA-DAGA 2013, 592--595. http://www.audiogroup.web.fh-koeln.de/FILES/AIA-DAGA2013_HRIRs.pdf
