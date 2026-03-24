"""Provides an example how to use bluetooth"""

import sys
import asyncio

from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic, BleakError

async def print_services(client: BleakClient):
    """Print all ble services"""
    for service in client.services:
        print(f"[Service] {service}")

        for char in service.characteristics:
            if "read" in char.properties:
                try:
                    value = await client.read_gatt_char(char)
                    extra = f", Value: {value}"
                except BleakError as e:
                    extra = f", Error: {e}"
            else:
                extra = ""

            if "write-without-response" in char.properties:
                extra += f", Max write w/o rsp size: {char.max_write_without_response_size}"

            print(f"  [Characteristic] {char} ({",".join(char.properties)}){extra}")

            for descriptor in char.descriptors:
                try:
                    value = await client.read_gatt_descriptor(descriptor)
                    print(f"    [Descriptor] {descriptor}, Value: {value}")
                except BleakError as e:
                    print(f"    [Descriptor] {descriptor}, Error: {e}")


def callback(sender: BleakGATTCharacteristic, data: bytearray):
    """Callback for receiving notifications"""
    print(f"{sender}: {data}")


def handle_disconnect(device: BleakClient):
    """disco"""    
    print(f"Device was disconnected, {device}")


async def main() -> int:
    """Main function"""

    mid_level_init_guid = "0000abcd-8e22-4541-9d4c-21edae82ed19"
    mid_level_init_ack_guid = "0000bcde-8e22-4541-9d4c-21edae82ed19"
    print("Scan...")
    # devices = await BleakScanner.discover(return_adv=True)
    devices = await BleakScanner.discover()

    for value in devices:
        # device = value[0]
        device = value
        if device.name == "YOLO":
            # print(f"Advertising data: {value[1].manufacturer_data}")
            async with BleakClient(device, disconnected_callback=handle_disconnect, timeout=10.0) as client:
            # client = BleakClient(device)
                # await client.connect()
                await print_services(client)

                await client.start_notify(mid_level_init_ack_guid, callback)
                # value = await client.read_gatt_char(mid_level_init_guid)
                await client.write_gatt_char(mid_level_init_guid, bytes([0xBB]), True)
                # value = await client.read_gatt_char(mid_level_init_guid)
                # print(value)
                await asyncio.sleep(5)
                # await client.disconnect()

    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
