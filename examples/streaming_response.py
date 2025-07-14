import json
from datetime import datetime
from time import sleep

from panther import Panther
from panther.app import GenericAPI
from panther.response import StreamingResponse


class MainPage(GenericAPI):
    def generator(self):
        """Simple number generator with delays"""
        for i in range(10):
            sleep(1)
            yield f'data: {i}\n\n'

    def get(self):
        return StreamingResponse(data=self.generator())


class ProgressStream(GenericAPI):
    def generator(self):
        """Simulate a long-running task with progress updates"""
        total_steps = 20
        for i in range(total_steps + 1):
            progress = (i / total_steps) * 100
            data = {
                'step': i,
                'total_steps': total_steps,
                'progress': round(progress, 1),
                'status': 'processing' if i < total_steps else 'completed',
                'timestamp': datetime.now().isoformat(),
            }
            yield f'data: {json.dumps(data)}\n\n'
            sleep(0.5)

    def get(self):
        return StreamingResponse(data=self.generator())


class LogStream(GenericAPI):
    def generator(self):
        """Simulate real-time log streaming"""
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        messages = [
            'Server started successfully',
            'Processing request from client',
            'Database connection established',
            'Cache miss, fetching from database',
            'User authentication successful',
            'File upload completed',
            'API rate limit approaching',
            'Memory usage: 45%',
            'Backup job started',
            'Task completed successfully',
        ]

        for i, message in enumerate(messages):
            level = log_levels[i % len(log_levels)]
            log_entry = {'timestamp': datetime.now().isoformat(), 'level': level, 'message': message, 'id': i + 1}
            yield f'data: {json.dumps(log_entry)}\n\n'
            sleep(0.8)

    def get(self):
        return StreamingResponse(data=self.generator())


class ChatStream(GenericAPI):
    def generator(self):
        """Simulate a chat bot response"""
        response_parts = [
            "Hello! I'm a streaming chatbot.",
            'I can help you with various tasks.',
            'For example, I can answer questions,',
            'provide information, or just chat!',
            'What would you like to know today?',
        ]

        for i, part in enumerate(response_parts):
            data = {
                'type': 'message',
                'content': part,
                'part': i + 1,
                'total_parts': len(response_parts),
                'timestamp': datetime.now().isoformat(),
            }
            yield f'data: {json.dumps(data)}\n\n'
            sleep(0.6)

    def get(self):
        return StreamingResponse(data=self.generator())


class ErrorHandlingStream(GenericAPI):
    def generator(self):
        """Demonstrate error handling in streaming"""
        try:
            for i in range(5):
                if i == 3:
                    # Simulate an error
                    raise Exception('Simulated error during streaming')

                data = {'step': i, 'status': 'success', 'message': f'Processed step {i}'}
                yield f'data: {json.dumps(data)}\n\n'
                sleep(1)
        except Exception as e:
            error_data = {'error': True, 'message': str(e), 'timestamp': datetime.now().isoformat()}
            yield f'data: {json.dumps(error_data)}\n\n'

    def get(self):
        return StreamingResponse(data=self.generator())


url_routing = {
    '': MainPage,
    'progress': ProgressStream,
    'logs': LogStream,
    'chat': ChatStream,
    'error-demo': ErrorHandlingStream,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
