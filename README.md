# tiavManager
## Context-Adaptive Framework for Managing Drivers' Trust in Automated Vehicles

### Instructions for installation and use on Windows 10 platforms

The **pebl_script** and the **simulator** folders have the source codes for the NDRT and the driving simulation scripts, respectively.

#### Pre-requisites:

* Install Pupil Labs software, available at https://github.com/pupil-labs/pupil. For best compatibility, use version 1.21

* Install PEBL, available at http://pebl.sourceforge.net/

* Copy and paste the folder *pebl_script\vsearchForSlider* into the folder *battery* on PEBL installation directory

* Install Unreal Engine version 4.18.3

* Download the StraightRoadMap Unreal project from https://bit.ly/2V9JgKT

* Copy and paste it to the *Unreal Projects* folder that is created in your *Documents* folder

* Download and build AirSim from https://github.com/microsoft/AirSim, following the instructions. Edit settings.json (found in the AirSim folder) so that it looks like the following:

```settings.json
{
  "SeeDocsAt": "https://github.com/Microsoft/AirSim/blob/master/docs/settings.md",
  "SettingsVersion": 1.2,
  "SimMode": "Car",
  "ViewMode": "Fpv",
  "EngineSound": true,
  "LogMessagesVisible": false,
  "RecordUIVisible": false,
  "Vehicles": {
    "PhysXCar": {
      "VehicleType": "PhysXCar",
      "Cameras": {
        "fpv": {
          "CaptureSettings": [
            {
              "ImageType": -1,
              "Width": 256,
              "Height": 144,
              "FOV_Degrees": 120
            }
          ],
          "X": 0,
          "Y": -0.30,
          "Z": -1.33,
          "Pitch": 0,
          "Roll": 0,
          "Yaw": 0
        }
      }
    }
  }
}
```

* Python modules: Python 3 is required, with the following modules (easily installed with `pip`)
   * `airsim`
   * `pygame`
   * `playsound`
   * `winsound`
   * `pyttsx3`
   * `transforms3d`
   * `transforms3d`
   * `zmq`
   * `msgpack`
   * `platform`
   * `subprocess`
   * `signal`
   * `numpy`


#### How to start the NDRT:

* Specify the SubjectID and the TrialID as in the field *Participant Code* as follows: `sub[SubjectID]_trial[TrialID]`
with `[SubjectID]` as the Subject ID number and `[TrialID]` as the trial number

* Run the script `SuRT_mod.pbl` in PEBL

#### How to start the eye tracking?

* Run the *pupil_capture* app
* Using APRIL tags on the screens (available at https://github.com/AprilRobotics/apriltag), define the four simulator surfaces with the *Surface Tracker* plugin, with the following names:

  * `Left Monitor`
  * `Center Monitor`
  * `Right Monitor`
  * `PEBL Screen`

* Make sure to use enable the *Pupil Remote* plugin and to specify the `50020` TCP Port

#### How to start the driving simulation?

* Depending on the subject ID and the trial ID numbers (see *How do I define the circuit track direction?*), open the *Regular direction* file:
  * `"...\Unreal Projects\StraightRoadMap\Content\DT_Spring_Landscape\Maps\TestTrack.umap"`

* or the *Reverse direction* file:
  * `"...\Unreal Projects\StraightRoadMap\Content\DT_Spring_Landscape\Maps\ReverseTestTrack.umap"`

* Obs.: There is also a *training* track, tha can be loaded from the file:
  * `"...\Unreal Projects\StraightRoadMap\Content\DT_Spring_Landscape\Maps\trainingTrack.umap"`

* Then start the simulation script on the *simulator* folder with the following command:

  * `>> python .\DriveSimulator.py [SubjectID] [TrialID]`

* The simulation will start, with the message *"Hello, I am MAVRIC. Please enable autonomy now!"*

* Using the *Logitech G-27* driving wheel, the driver will be able to engage the autonomous mode by pressing the wheel button of the upper left corner

* To stop and quit the simulation while running, type `q` and then `[Enter]`

#### How do I define the circuit track direction?

* Check with the following map:

![Conditions according to subject ID and Trial number](https://github.com/hazevedosa/tiavManager/blob/master/conditions_randomization.PNG)
