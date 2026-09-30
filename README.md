# FirmWire GUI
This project is a web-based graphical user interface (GUI) for [FirmWire](https://github.com/FirmWire/FirmWire)

## Installation
### Prerequisites
Make sure you have Git and Docker installed and that the Docker daemon is running.
### Clone the project and submodule
```
git clone --recurse-submodules https://github.com/xAZUR3x/FirmWire-GUI.git
```
or separately:
```
git clone https://github.com/xAZUR3x/FirmWire-GUI.git
git submodule update --init --recursive
```
### Build the container
Inside the projects root folder (FirmWire-GUI) run:
```
docker build -t firmwire-gui .
```
It may take a while to build the first time.
### Run the web app
From the root folder, run the file `gui.py` with:
```
python3 gui.py
```
### Provide modem firmware
The app accepts firmware images via URL or file, just select the input type and add your modem firmware. The app provides you with a Samsung Shannon firmware image to help you get started.

## Key Features
The app contains two main views: a raw output stream and a table. You can filter through either of these based on a variety of fields and can optionally export the results to a text file.
