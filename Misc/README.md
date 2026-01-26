# Senior Design Project Part I

This project is a Graphical User Interface (GUI) that uses Python / Julia to simulate data from an instrument, display real-time graphs, record trials, and playback saved data from a CSV file.

## Visual
![Alt Text](resources/mdlp-gui-showcase.gif)
## Dependencies
Python Packages:
```python
import zmq, json, os, PyQt6, csv, time, json, subprocess, pyqtgraph
```
Julia Packages:
```julia
using ZMQ, JSON
```
## Roadmap

The backend will be converted from Python to a mainly Julia backend for high efficiency handling of incoming science data. The end result will be a Python frontend and a Julia backend for a proof of concept dual language highly efficient GUI to handle incoming data, display, and perform functions of analysis, saving, and playback.

This project is planned to connect via Serial Port to an instrument and displayed ran on the University plasma chamber. To do so the code will be modified to accept real data in lieu of the simulated data. 
