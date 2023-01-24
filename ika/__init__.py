"""
Python driver for IKA equipment.

Distributed under the GNU General Public License v3
Copyright (C) 2022 NuMat Technologies
"""
from ika.driver import Hotplate, OverheadStirrer


def command_line(args=None):
    """Command line tool exposed through package install."""
    import argparse
    import asyncio
    import json

    parser = argparse.ArgumentParser(description="Read device status.")
    parser.add_argument('address', help="The IP address of the device.")
    parser.add_argument('-p', '--port', help="The port of the device (default 23)",
                        type=int, default=23)
    parser.add_argument('-t', '--type', help="The type of device (default 'overhead')",
                        type=str, default='overhead')
    parser.add_argument('-n', '--no-info', action='store_true', help="Exclude "
                        "device information. Reduces communication overhead.")
    args = parser.parse_args(args)
    if args.type == 'overhead':
        async def get():
            async with OverheadStirrer(args.address, args.port) as device:
                d = await device.get()
                if not args.no_info and d.get('on', True):
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    elif args.type == 'hotplate':
        async def get():
            async with Hotplate(args.address, args.port) as device:
                d = await device.get()
                if not args.no_info and d.get('on', True):
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    elif args.type in ['vacuum']:
        raise NotImplementedError((f"Not implemented yet for device type: {args.type}"))
    else:
        raise ValueError(f"Unsupported device type: {args.type}")
    asyncio.run(get())


if __name__ == '__main__':
    command_line()
