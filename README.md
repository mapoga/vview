# vview

Interface for Foundry's Nuke to change the version of selected nodes

## Preview


## Features

- Simple popup heavily inspired by Hiero
- Live preview
- Update to node range
- Support for relative path
- Tumbnail generation in the background

## Requirements

- Nuke 13.0+ (python>=3.7.3)

## Install

### Download
Download the .zip file of this project and unpack it somewhere.

Once unpacked, the .zip file can be deleted.
ex: `C:\Users\my_user\.nuke\vview`

or Use the appropriate command.
```shell
# Linux / Macos
git clone https://github.com/mapoga/vview ~/.nuke/vview

# Windows PowerShell
git clone https://github.com/mapoga/vview ~\.nuke\vview

# Windows Command Prompt
git clone https://github.com/mapoga/vview %USERPROFILE%\.nuke\vview
```

### Configure
Add this line to your `init.py` file. Adjust the path to your own install path.
```python
nuke.pluginAddPath(r"C:\Users\my_user\.nuke\vview")
```
In your `menu.py` file, add this line. Feel free to change the shortcut to your liking.
```python
nuke.menu('Nodes').
```

