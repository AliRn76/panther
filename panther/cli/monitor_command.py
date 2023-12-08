import contextlib
import os
from collections import deque
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from watchfiles import watch

from panther.cli.utils import cli_error
from panther.configs import config


def monitor() -> None:
    monitoring_log_file = Path(config['base_dir'] / 'logs' / 'monitoring.log')

    def _generate_table(rows: deque) -> Panel:
        layout = Layout()

        rows = list(rows)
        _, lines = os.get_terminal_size()

        table = Table(box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column('Datetime', justify='center', style='magenta', no_wrap=True)
        table.add_column('Method', justify='center', style='cyan')
        table.add_column('Path', justify='center', style='cyan')
        table.add_column('Client', justify='center', style='cyan')
        table.add_column('Response Time', justify='center', style='blue')
        table.add_column('Status Code', justify='center', style='blue')

        for row in rows[-lines:]:  # It will give us "lines" last lines of "rows"
            table.add_row(*row)
        layout.update(table)

        return Panel(
            Align.center(Group(table)),
            box=box.ROUNDED,
            padding=(1, 2),
            title='Monitoring',
            border_style='bright_blue',
        )

    if not monitoring_log_file.exists():
        return cli_error('Monitoring file not found. (You need at least one monitoring record for this action)')

    with monitoring_log_file.open() as f:
        f.readlines()  # Set cursor at the end of file

        _, init_lines_count = os.get_terminal_size()
        messages = deque(maxlen=init_lines_count - 10)  # Save space for header and footer

        with (
            Live(
                _generate_table(messages),
                auto_refresh=False,
                vertical_overflow='visible',
                screen=True,
            ) as live,
            contextlib.suppress(KeyboardInterrupt),
        ):
            for _ in watch(monitoring_log_file):
                data = f.readline().split('|')
                # 2023-03-24 01:42:52 | GET | /user/317/ | 127.0.0.1:48856 |  0.0366 ms | 200
                messages.append(data)
                live.update(_generate_table(messages))
                live.refresh()
