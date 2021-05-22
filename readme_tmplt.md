<h1 align="center">
  <br>
  <a href=#><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Logo.png" alt="banner"></a>
</h1>

<h4 align="center"> PiCameraApp: A graphical user interface (GUI) for the Picamera library written in Python using Tkinter / ttk. </h4>

<p align="center">
    <a href="#">
    <img src="#"
         alt="GitHub last commit badge">
    <a href="#">
    <img src="#"
         alt="GitHub issues badge">
    <a href="#">
    <img src="#"
         alt="GitHub pull requests badge">
</p>
      
<p align="center">
  <a href="#about">About</a> •
  <a href="#installation">Installation</a> •  
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#credits">Credits</a> •
  <a href="#support">Support</a> •
  <a href="#license">License</a>
</p>

---

## About

PiCameraApp: A graphical user interface (GUI) for the Picamera library written in Python using Tkinter / ttk.

<table>
<tr>
<td>

![Imagen/gif de preview](https://user-images.githubusercontent.com/3778024/36648609-43091bc0-1a5b-11e8-97c8-be0db1249a32.png)
<p align="right">
<sub>(Preview)</sub>
</p>

</td>
</tr>
</table>

### Features

<!-- |                            |  theProject        | ◾ Other           | -->
<!-- | -------------------------- | :----------------: | :---------------: | -->
<!-- | Feature 1                  |         ✔️         |        ❌        | -->
<!-- | Feature 2                  |         ✔️         |        ❌        | -->


## Installation
Requirements:
- [ImageTk](#) 
   - To install ImageTk: 
      
```
sudo apt-get install python-imaging
sudo apt-get install python-imaging-tk   
```
      

##### Downloading and installing steps
1. Clone or download the zip file and extract to a directory of your choosing. 


## Usage

* To run, open a terminal, change to the directory containing the source files, and enter **python PiCameraApp.py** 

### Updating


## Contributing


#### Bug Reports & Feature Requests

Please use the [issue tracker](#) to report any bugs or file feature requests.

#### Developing

Got **something interesting** you'd like to **contribute**? Read more in [contributing](#).

#### TODO List (future enhancements)

| TODO       | Description                               |
| :--------- | :----------------------------------------------------- |
| Save Camera State | Allow the user to save and restore the current camera programming state. |
| Output Samples | Allow the user to generate a simple Python script that will program the camera and take a still image or video. |
| INI File | Have a configuration file that saves / restores Preferences |
| Time Delay | Support programming the camera to take still (or videos of length **time**), starting **start time**, then every **time** sec, delaying **time** sec until **number** or **end time** is reached. |
| GPIO Support | Better suport the LED GPIO - this is still buggy (or not fully understood). Also, allow the user to specify GPIO pin(s) that can be toggled (or held high or low) while a still image or video capture is in progress. | 
| Better error checking | Reorgainze code |
| | |

#### API Reference

PiCameraApp has been developed using Python ver 2.7.13 and Python ver 3.5.3. In addition, it uses the following additonal Python libraries. See the PiCameraApp About dialog for exact versions used.

| Library    | Usage                                               |
| :--------- | :-------------------------------------------------- |
| picamera   | The python interface to the PiCamera hardware. See https://picamera.readthedocs.io/en/release-1.13/install.html |
| RPi.GPIO   | Required to toggle the LED on the camera. Can get it at http://www.raspberrypi-spy.co.uk/2012/05/install-rpi-gpio-python-library/ |
| PIL / Pillow | The Pillow fork of the Python Image Library. One issue is with PIL ImageTk under Python 3.x. It was not installed on my RPI. If you have similar PIL Import Errors use:  **sudo apt-get install python3-pil.imagetk**. |
|     |    | 



      
## Version history
[versions](/version_history.md)      

## Support

### Wiki

Do you **need some help**? Check the _articles_ from the [wiki](#).

### Known Issues

| Issue      | Description / Workaround                               |
| :--------- | :----------------------------------------------------- |
| LED | The led_pin parameter can be used to specify the GPIO pin which should be used to control the camera’s LED via the led attribute. If this is not specified, it should default to the correct value for your Pi platform. At present, the camera’s LED cannot be controlled on the Pi 3 (the GPIOs used to control the camera LED were re-routed to GPIO expander on the Pi 3). There are circumstances in which the camera firmware may override an existing LED setting. For example, in the case that the firmware resets the camera (as can happen with a CSI-2 timeout), the LED may also be reset. If you wish to guarantee that the LED remain off at all times, you may prefer to use the disable_camera_led option in config.txt (this has the added advantage that sudo privileges and GPIO access are not required, at least for LED control). Thanks https://picamera.readthedocs.io/en/release-1.13/|
| Sensor Mode | Use this with discretion. In any mode other than Mode 0 (Auto), I've experienced sudden 'freezes' of the application forcing a complete reboot. |
| framerate_range and H264 video | The App would raise an exception when attempting to cature H264 video when framerate_range was selected. The exception complained the framerate_delta could not be specified with framerate_range??? Until I resolve this bug, I don't allow capturing H264 videos with framerate_range selected. |
| framerate and framerate_delta error checking | There are cases where the code may not catch an exception. Avoid setting framerate and framerate_delta values that could add to numbers less than or equal to zero.  A future update will fix this issue.
| JPEG image parameters | The JPEG image capture parameter 'Restart' is not supported with this release. |
| H264 video parameters | The H264 video capture parameter 'Intra Period' is not supported with this release. |
| Other video paramaters | 'bitrate' and 'quality' are not supported in this release. |
| Image Effects parameters | The Image Effect parameters for 'colorbalance', 'film', 'solarize', and 'film' are not supported with this release. |
| EXIF data display | The python exif module does not support all EXIF metadata. Find a better solution. |
| Image flip buttons | The two image flip buttons on the bottom image pane are disabled. These are meant to 'flip' the PIL image that is displayed. To flip or rotate the camera image, use the buttons on the top preview pane. |
| | |      
      
      
### FAQ

### Troubleshooting

### Need more support?
Reach out to us at one of the following places:

- Website 
- E-Mail: 

## Credits

![about](https://user-images.githubusercontent.com/3778024/36648694-71283a1c-1a5c-11e8-9c85-ec1f07218cca.png)      
      
### Maintainers

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
 implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program.  If not, see http://www.gnu.org/licenses/.

[![License: This licence](#)](#)
