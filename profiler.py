"""
Panther Framework Performance Profiler

Prerequisites:
- Install ali: https://github.com/nakabonne/ali
- Install yappi: pip install yappi

Usage:
1. Run the profiler:
   python profiler.py > benchmark_$(date +%s).txt

2. Send requests:
   ali --rate=100 http://127.0.0.1:8000

3. View results in the generated output file

* Any contribution or improvement on this profiler would be welcomed.
"""

import uvicorn
import yappi

from panther import Panther
from panther.app import API


@API()
async def hello_world():
    return {'detail': 'Hello World'}


def main():
    app = Panther(__name__, configs=__name__, urls={'': hello_world})
    yappi.start()
    uvicorn.run(app, access_log=False)
    yappi.stop()

    # Print function-level stats
    stats = yappi.get_func_stats()
    stats.print_all(columns={0: ('name', 100), 1: ('ncall', 10), 2: ('tsub', 10), 3: ('ttot', 10), 4: ('tavg', 10)})


if __name__ == '__main__':
    main()
