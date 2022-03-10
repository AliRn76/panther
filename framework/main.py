class App:
    async def __call__(self, scope, receive, send):
        assert scope['type'] == 'http'
        print(f'{scope = }')
        print()
        print(f'{receive = }')
        print()
        print(f'{send = }')
        print()
        print(f'{self = }')

        method = scope['method']
        path = scope['path']

        print(f'{method = }')
        print(f'{path = }')


app = App()
