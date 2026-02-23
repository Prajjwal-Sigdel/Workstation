import asyncio
from dbus_next.aio import MessageBus

async def main():
    bus = await MessageBus().connect()
    print("Connected to the session bus!")

    service = 'org.freedesktop.ScreenSaver'
    path = '/ScreenSaver'

    try:
        introspection = await bus.introspect(service, path)
    except Exception as e:
        print("Introspection failed:", e)
        return

    proxy = bus.get_proxy_object(service, path, introspection)
    iface = proxy.get_interface('org.freedesktop.ScreenSaver')

    def on_active_changed(is_active: bool):
        if is_active:
            print("Idle threshold reached! Time to run face detection.")
        else:
            print("User is active again.")

    iface.on_active_changed(on_active_changed)
    print("Listening for ActiveChanged signals...")
    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())