import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
import importlib.util

class Framework:

    def load_urls_with_importlib(self):
        # urls_path = self.base_dir / urls

        print(f'{self.base_dir = }', end='\n\n')
        print(f'{type(self.base_dir) = }', end='\n\n')
        urls_path = self.base_dir.parent / 'core/configs.py'
        print(f'{urls_path = }', end='\n\n')
        spec: ModuleSpec = importlib.util.spec_from_file_location('URLs', f'{urls_path}')
        print(f'{spec = }', end='\n\n')
        print(f'{spec.loader = }', end='\n\n')
        foo = importlib.util.module_from_spec(spec)

        # mod = importlib.import_module('core.configs.py')
        # # mod = importlib.import_module('home.ali.dev.framework.example2.core.configs.py')
        # print(f'{mod = }', end='\n\n')

        print(f'{foo = }', end='\n\n')
        print(f'{foo = }', end='\n\n')
        print(f'{type(foo) = }', end='\n\n')
        print(f'{dir(foo) = }', end='\n\n')

        # spec.loader.exec_module(foo)

        del importlib.util

    def load_urls(self):
        urls_path = self.base_dir.parent / 'core/configs.py'
        sys.path.append(f'{urls_path}')
        from configs import URLs
        print(URLs)
        # del sys

    def __init__(self, name):
        self.base_dir = Path(name).resolve()
        self.load_urls_with_importlib()

    async def __call__(self, scope, receive, send):
        assert scope['type'] == 'http'
        method = scope['method']
        path = scope['path']
        print(f'{scope = }', end='\n\n')
        print(f'{receive = }', end='\n\n')
        print(f'{send = }', end='\n\n')
        print(f'{self = }', end='\n\n')
        print(f'{method = }', end='\n\n')
        print(f'{path = }', end='\n\n')
        print(f'{dir(self) = }', end='\n\n')
        print(f'{self.__dict__ = }', end='\n\n')
        print(f'{self.__doc__ = }', end='\n\n')
        print(f'{self.__doc__ = }', end='\n\n')
        print(f'{self.base_dir = }', end='\n\n')


