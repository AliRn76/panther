import contextlib
import logging
import os
import platform
import signal
from collections import deque
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from panther.cli.utils import import_error
from panther.configs import config
from panther.middlewares.monitoring import WebsocketMonitoringMiddleware

with contextlib.suppress(ImportError):
    from watchfiles import watch

logger = logging.getLogger('panther')


class Monitoring:
    def __init__(self):
        self.rows = deque()
        self.monitoring_log_file = Path(config.BASE_DIR / 'logs' / 'monitoring.log')

    def monitor(self) -> None:
        if error := self.initialize():
            # Don't continue if initialize() has error
            logger.error(error)
            return

        with (
            self.monitoring_log_file.open() as f,
            Live(
                self.generate_table(),
                vertical_overflow='visible',
                screen=True,
            ) as live,
            contextlib.suppress(KeyboardInterrupt),
        ):
            f.readlines()  # Set cursor at the end of the file

            if platform.system() == 'Windows':
                watching = watch(self.monitoring_log_file, force_polling=True)
            else:
                watching = watch(self.monitoring_log_file)

            for _ in watching:
                for line in f.readlines():
                    # line = datetime | method | path | ip:port | response_time(seconds) | status
                    columns = line.split('|')
                    if len(columns) != 2:  # Can be `datetime | ` on initiation.
                        columns[4] = self._clean_response_time(columns[4])
                        self.rows.append(columns)
                        live.update(self.generate_table())

    def initialize(self) -> str:
        # Check requirements
        try:
            from watchfiles import watch
        except ImportError as e:
            return import_error(e, package='watchfiles').args[0]

        # Check log file
        if not self.monitoring_log_file.exists():
            return (
                f'`{self.monitoring_log_file}` file not found. '
                f'Make sure `panther.middlewares.monitoring.MonitoringMiddleware` is in your `MIDDLEWARES`.\n'
                f'documentation: https://PantherPy.github.io/middlewares/#monitoring-middleware'
            )

        # Initialize Deque
        self.update_rows()

        # Register the signal handler
        if platform.system() != 'Windows':
            signal.signal(signal.SIGWINCH, self.update_rows)

    def generate_table(self) -> Panel:
        # 2023-03-24 01:42:52 | GET | /user/317/ | 127.0.0.1:48856 |  0.0366 ms | 200

        table = Table(box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column('Datetime', justify='center', style='magenta', no_wrap=True)
        table.add_column('Method', justify='center', style='cyan', no_wrap=True)
        table.add_column('Path', justify='center', style='cyan', no_wrap=True)
        table.add_column('Client', justify='center', style='cyan')
        table.add_column('Response Time', justify='center', style='blue')
        table.add_column('Status', justify='center', style='blue', no_wrap=True)

        for row in self.rows:
            table.add_row(*row)

        return Panel(
            Align.center(Group(table)),
            box=box.ROUNDED,
            padding=(0, 2),
            title='Monitoring',
            border_style='bright_blue',
        )

    def update_rows(self, *args, **kwargs):
        # Top = -4, Bottom = -2 --> -6
        # Print of each line needs two line, so --> x // 2
        lines = (os.get_terminal_size()[1] - 6) // 2
        self.rows = deque(self.rows, maxlen=lines)

    @classmethod
    def _clean_response_time(cls, response_time: str) -> str:
        if response_time == WebsocketMonitoringMiddleware.ConnectedConnectionTime:
            return response_time
        response_time = float(response_time)
        time_unit = ' s'

        if response_time < 0.01:
            response_time = response_time * 1_000
            time_unit = 'ms'

        elif response_time >= 60:
            response_time = response_time / 60
            time_unit = ' m'

        return f'{round(response_time, 4)} {time_unit}'


monitor = Monitoring().monitor
