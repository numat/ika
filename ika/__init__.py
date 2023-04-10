"""
Python driver for IKA equipment.

Distributed under the GNU General Public License v3
Copyright (C) 2022 NuMat Technologies
"""
from ika.driver import Hotplate, OverheadStirrer, Shaker, Vacuum


def command_line(args=None):
    """Command line tool exposed through package install."""
    import argparse
    import asyncio
    import json

    parser = argparse.ArgumentParser(description="Read device status.")
    parser.add_argument('address', type=str, help="The target TCP address:port")
    parser.add_argument('-t', '--type', help="The type of device (default 'overhead')",
                        type=str, default='overhead')
    parser.add_argument('-n', '--no-info', action='store_true', help="Exclude "
                        "device information. Reduces communication overhead.")
    args = parser.parse_args(args)
    if args.type == 'overhead':
        async def get():
            async with OverheadStirrer(args.address) as device:
                d = await device.get()
                if not args.no_info:
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    elif args.type == 'hotplate':
        async def get():
            async with Hotplate(args.address,
                                include_surface_control=not args.no_info) as device:
                d = await device.get()
                if not args.no_info:
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    elif args.type == 'shaker':
        async def get():
            async with Shaker(args.address) as device:
                d = await device.get()
                if not args.no_info:
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    elif args.type == 'vacuum':
        async def get():
            async with Vacuum(args.address) as device:
                d = await device.get()
                if not args.no_info:
                    d['info'] = await device.get_info()
                print(json.dumps(d, indent=4))
    else:
        raise ValueError(f"Unsupported device type: {args.type}")
    asyncio.run(get())


if __name__ == '__main__':
    command_line()
