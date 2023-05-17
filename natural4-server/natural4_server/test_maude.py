import asyncio
from pathlib import Path

from natural4_maude.analyse_state_space import analyse_state_space

async def main():
  natural4_file = Path('natural4_maude') / 'examples' / 'pdpa.natural4'
  output_path = Path('.temp')
  await analyse_state_space(natural4_file, output_path)

if __name__ == '__main__':
  asyncio.run(main())