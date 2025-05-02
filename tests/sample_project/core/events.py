from panther.events import Event


@Event.startup
async def startup():
    print('Starting Up')

@Event.startup
async def shutdown():
    print('Shutting Down')
