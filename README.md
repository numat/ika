ika
===

Python ≥3.8 driver and command-line tool for IKA products.
 - Eurostar 60/100 control overhead stirrers
 - MATRIX ORBITAL shaker
 - RET control-visc hotplate/stirrer
 - Vacstar control vacuum pump

Installation
============

```
pip install ika-control
```

Usage
=====

## Command Line

```
$ ika <serial-to-ethernet-ip>:<port> --type hotplate
$ ika <serial-to-ethernet-ip>:<port> --type overhead
$ ika <serial-to-ethernet-ip>:<port> --type shaker
$ ika <serial-to-ethernet-ip>:<port> --type vacuum
```


## Python

This uses Python ≥3.5's async/await syntax to asynchronously communicate with an IKA device. For example:

```python
import asyncio
from ika import Hotplate, OverheadStirrer

async def get():
    async with OverheadStirrer('ip-address:port') as strirrer:
        print(await stirrer.get())
    async with Hotplate('ip-address:port') as hotplate:
        print(await hotplate.get())


asyncio.run(get())
```
Hardware configuration
======================
For Control-Visc hotplates, make sure the "Eurostar" control option is turned off
in the system settings.  Otherwise, the device will turn the heater off when the serial
cable is unplugged.

Acknowledgements
================

©2023 Alexander Ruddick

Uses code from [the Hein group](https://gitlab.com/heingroup/ika), but otherwise no affiliation.
As of 2023, that project appears to have been abandoned.
