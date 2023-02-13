import os
from collections import deque

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from watchfiles import watch

from panther.cli.utils import error


def monitor() -> None:
    def _generate_table(rows):
        layout = Layout()
        console = Console()

        rows = list(rows)
        n_rows = os.get_terminal_size()[1]

        while n_rows >= 0:
            table = Table(box=box.MINIMAL_DOUBLE_HEAD)
            table.add_column('Datetime', justify='center', style='magenta', no_wrap=True)
            table.add_column('Method', justify='center', style='cyan')
            table.add_column('Path', justify='center', style='cyan')
            table.add_column('Client', justify='center', style='cyan')
            table.add_column('Response Time', justify='center', style='blue')
            table.add_column('Status Code', justify='center', style='blue')

            for row in rows[-n_rows:]:
                table.add_row(*row)
            layout.update(table)
            render_map = layout.render(console, console.options)

            if len(render_map[layout].render[-1]) > 2:
                n_rows -= 1  # The table is overflowing
            else:
                break

        return Panel(
            Align.center(Group(table)),
            box=box.ROUNDED,
            padding=(1, 2),
            title='Monitoring',
            border_style='bright_blue',
        )

    try:
        with open('logs/monitoring.log') as f:
            f.readlines()
            width, height = os.get_terminal_size()
            messages = deque(maxlen=height - 8)  # Save space for header and footer

            with Live(_generate_table(messages), auto_refresh=False, vertical_overflow='visible', screen=True) as live:
                # TODO: Is it only watch logs/monitoring.log or the whole directory ?
                for _ in watch('logs/monitoring.log'):
                    data = f.readline().split('|')
                    messages.append(data)
                    live.update(_generate_table(messages))
                    live.refresh()

    except FileNotFoundError:
        error("Monitor Log File Does Not Exists.\n\nHint: Make sure 'Monitor' is True in 'core/configs' "
              "or you are in a correct directory.")
    except KeyboardInterrupt:
        pass
