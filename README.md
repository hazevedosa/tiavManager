# tiavManager
## Context-Adaptive Framework for Managing Drivers' Trust in Automated Vehicles

### Instructions for installation and use on Windows 10 platforms

The **pebl_script** and the **simulator** folders have the source codes for the NDRT and the driving simulation scripts, respectively.

#### Pre-requisites:

* Install Pupil Labs software, available at https://github.com/pupil-labs/pupil

* Install PEBL, available at http://pebl.sourceforge.net/

* Copy and paste the folder *pebl_script\vsearchForSlider* into the folder *battery* on PEBL installation directory

* Install Unreal Engine V. 4.18.3

* Download the StraightRoadMap Unreal project from https://bit.ly/2V9JgKT; copy and paste it to the *Unreal Projects* folder that is created in your *Documents* folder

#### How to start the NDRT:

* Run the script "SuRT_mod.pbl" in PEBL. Specify the SubjectID and the TrialID as follows: `sub[SubjectID]_trial[TrialID]`

#### How to start the eye tracking?

* Run the *pupil_capture* app.
* using APRIL tags on the screens (available at https://github.com/AprilRobotics/apriltag), define the four simulator surfaces with the *Surface Tracker* plugin, with the following names:

  * `"Left Monitor"`
  * `"Center Monitor"`
  * `"Right Monitor"`
  * `"PEBL Screen"`

Make sure to use enable the *Pupil Remote* plugin and to specify the `50020` TCP Port.

#### How to start the driving simulation?

Depending on the subject ID and the trial ID numbers (see *How do I define the circuit track direction?*), open the file:
`"...\Unreal Projects\StraightRoadMap\Content\DT_Spring_Landscape\Maps\TestTrack.umap"`

or the file:
`"...\Unreal Projects\StraightRoadMap\Content\DT_Spring_Landscape\Maps\ReverseTestTrack.umap"`

and then start the simulation script on the *simulator* folder with the following command:

`>> python .\DriveSimulator2.py [subId] [TrialID]`

The simulation will start, with the message *"Hello, I am MAVRIC. Please enable autonomy now."*

Using the Logitech G-27 driving wheel, the driver will be able to engage the autonomous mode by pressing the wheel button of the upper left corner.


#### How do I define the circuit track direction?

![Conditions according to subject ID and Trial number](./conditions_randomization.png)
