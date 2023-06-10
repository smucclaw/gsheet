# this script helps maintain a pool of vue dev servers listening on a range of ports.
# you can bring up a new server with the "up" command.
# and you can bring it down with the "down" command.
# the servers are allocated out of a pool of slots.
# if you repeat an "up" command and a server is still running for that combo of uuid/ssid/sid,
# that slot will be refreshed with the latest purs file.
#
# we limit ourselves a maximum poolsize and if we exceed that poolsize we just arbitrarily
# kill off the oldest server and launch a new one in its place.

# commands:
#
# v8k list
#     List all allocated vue servers sorted by last update time,
#         oldest first
#
# v8k up --uuid u --ssid ss --sheetid s file.purs
#     If no server is already serving that UUID-SSID-SID combo,
#     create a new vue server somewhere in the 8000 range
#     and initialize it with the file.purs.
#
#     (Note: replaces the oldest existing vue server
#     if we have reachedd the pool size limit.)
#
#     Return the url of the vue app on STDOUT.
#
#     If a server is already serving that UUID-SSID-SID combo,
#     update it with a new file.purs.
#
# v8k down --uuid uu --ssid ss --sheetid s
#     Delete an existing vue server by UUID-SSID-SID combo.
#
# v8k downdir slotname
#     Delete an existing vue server by slot number.

import asyncio
import shutil
import sys
import os
import re
from os.path import isfile, getmtime
import argparse
import json
import subprocess
from pathlib import Path
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import aiofiles
import aioshutil
import aiostream

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent_extras as pyrse

try:
  v8k_workdir: Path = Path(os.environ['V8K_WORKDIR'])
except KeyError:
  print(
    'V8K_WORKDIR not set in os.environ -- check your gunicorn config!!',
    file=sys.stderr
  )
  v8k_workdir: Path = Path()

try:
  v8k_slots_arg: str | None = f'--poolsize {os.environ["V8K_SLOTS"]}'
except KeyError:
  v8k_slots_arg = None

v8k_startport: str = os.environ.get('v8k_startport', '')

def getjson(pathin: str | os.PathLike):
  pathin = Path(pathin)
  with open(pathin, 'r') as read_file:
    json_str = read_file.read().strip()
    # print(f'getjson: {pathin} {json_str}', file=sys.stderr)
    data = json.loads(json_str)
    data['jsonfile'] = pathin
    data['modtime'] = getmtime(pathin)
  return data

def read_all(workdir: str | os.PathLike) -> Mapping[str, Mapping[str, Any]]:
    workdir_path = Path(workdir)

    vue_descriptors = [getjson(f) for f in workdir_path.glob('*/v8k.json')]

    descriptor_map = {descriptor['slot']: descriptor for descriptor in vue_descriptors}
    return descriptor_map

def print_server_info(portnum: int) -> Sequence[Any]:
    completed = subprocess.run([f"ps wwaux | grep port={portnum} | grep -v grep | grep -v startport="], shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mymatches = re.findall(r'^\S+\s+(\d+).*port=(\d+)', completed.stdout.decode('utf-8'), re.MULTILINE)
    if mymatches:
        for mymatch in mymatches:
            print(f"\tpid {mymatch[0]} is listening on port {mymatch[1]}", file=sys.stderr)
    else:
        print(f"\tport {portnum} is no longer listened, as far as we can detect", file=sys.stderr)
    return mymatches

@curry
def do_list(
  args: argparse.Namespace,
  workdir: str | os.PathLike
) -> None:
  descriptors = read_all(workdir)
  for descriptor in sorted(descriptors.values(), key=lambda js: int(js['slot'])):
    print(f"* {descriptor['dir']}", file=sys.stderr)
    print_server_info(descriptor['port'])

@curry
def do_find(
  args: argparse.Namespace,
  workdir: str | os.PathLike
) -> None:
    vuedict = read_all(workdir)
    # is there already a server running on the desired uuid-ssid-sheetid?
    existing = {s: js for (s, js) in vuedict.items()
                if js['ssid'] == args.ssid
                and js['sheetid'] == args.sheetid
                and js['uuid'] == args.uuid
                }
    for (s, js) in existing.items():
        print(f"* found allocated server on our uuid/ssid/sheetid: {js['slot']}", file=sys.stderr)
        mymatches = print_server_info(js['port'])
        if mymatches:
          print(f":{js['port']}/{js['base_url']}") # match the STDOUT convention in do_up

@curry
def do_up(
  args: argparse.Namespace,
  workdir: str | os.PathLike
) -> Mapping[str, str | Callable[[], None]]:
    vuedict = read_all(workdir)

    if not isfile(args.filename):
      print(f"have you got the right filename? I can't see {args.filename} from here", file=sys.stderr)

    dead_slots = []
    start_port = args.startport
    pool_size = args.poolsize
    print(f"** startport = {start_port}", file=sys.stderr)
    print(f"** poolsize = {pool_size}", file=sys.stderr)

    # is there already a server running on the desired uuid-ssid-sheetid?
    existing = [js for js in vuedict.values()
                if js['ssid'] == args.ssid
                and js['sheetid'] == args.sheetid
                and js['uuid'] == args.uuid
                ]

    need_to_relaunch = True
    for e in existing:
      print(f"** found allegedly existing server(s) on our uuid/ssid/sheetid: {e['slot']}", file=sys.stderr)
      mymatches = print_server_info(e['port'])
      if mymatches:
        print(f"server seems to be still running for port {e['port']}!", file=sys.stderr)
        need_to_relaunch = False
        print("refreshing the purs file", file=sys.stderr)
        # [TODO] do this in a more atomic way with a tmp file and a rename, because the vue server may try to
        #  reread the file too soon, when the cp hasn't completed.
        purs_file = Path(e['dir']) / "src" / "RuleLib" / "Interview.purs"
        print(f"cp {args.filename} {purs_file}", file=sys.stderr)
        # subprocess.run(["cp", args.filename, purs_file])
        shutil.copy(args.filename, purs_file)
        # subprocess.run(["touch", join(e['dir'], "v8k.json")])
        (Path(e['dir']) / 'v8k.json').touch()
        print(f":{e['port']}{e['base_url']}") # the port and base_url returned on STDOUT are read by the caller hello.py
      else:
        print("but the server isn't running any longer.", file=sys.stderr)
        dead_slots.append(str(e['slot']))

    if not need_to_relaunch:
      return pyrs.m()

    server_slots = {f"{n:02}" for n in range(0, pool_size)}
    available_slots = server_slots - set(vuedict.keys()) | set(dead_slots)

    print(f"server_slots    = {server_slots}", file=sys.stderr)
    print(f"vuedict.keys()  = {vuedict.keys()}", file=sys.stderr)
    print(f"dead_slots      = {dead_slots}", file=sys.stderr)
    print(f"available_slots = {available_slots}", file=sys.stderr)

    match (len(available_slots), len(existing), len(vuedict) >= pool_size):
      case (0, _ , _) | (_, 0, True):
        oldest = min(vuedict.values(), key=lambda js: js['modtime'])
        print(f"oldest = {oldest}", file=sys.stderr)
        print(f"** pool size reached, will replace oldest server {oldest['slot']}", file=sys.stderr)
        asyncio.run(take_down(vuedict, oldest['slot']))
        available_slots = {oldest['slot']}
      case _: pass

    chosen_slot = next(iter(available_slots))

    print(f"available_slots = {available_slots}", file=sys.stderr)
    print(f"chosen_slot     = {chosen_slot}", file=sys.stderr)

    portnum = int(start_port) + int(chosen_slot)
    print(f"** chose {chosen_slot} out of available slots {available_slots}, port={portnum}", file=sys.stderr)

    server_config_dir = Path(workdir) / f"vue-{chosen_slot}"
    server_config_cli = ('npm', 'run', 'serve', '--', f'--port={portnum}')

    server_config = {
      "ssid": args.ssid,
      "sheetid": args.sheetid,
      "uuid": args.uuid,
      "port": portnum,
      "slot": chosen_slot,
      "dir": f'{server_config_dir}',
      "base_url": f'{Path("/") / args.uuid / args.ssid / args.sheetid}',
      # "cli": ['npm', 'run', 'serve', '--', f'--port={portnum}']
      "cli": f'{" ".join(server_config_cli)}'
    }

    # child_pid = os.fork()
    # # if this leads to trouble we may need to double-fork with grandparent-wait
    # if child_pid > 0:  # in the parent
    #   print(f"v8k: fork(parent): returning port {portnum}", file=sys.stderr)
    #   with open(v8k_outfile, 'a+') as outfile:
    #     print(f":{server_config['port']}{server_config['base_url']}", file=outfile) # the port and base_url returned on STDOUT are read by the caller hello.py
    #   return
    # else:  # in the child
    #  print("v8k: fork(child): continuing to run", file=sys.stderr)

    async def vue_purs_post_process():
      # rsync_command = f"rsync -a {workdir}/vue-small/ {server_config['dir']}/"
      # subprocess.run([rsync_command], shell=True)
      rsync_args = pyrs.v(
        '-a',
        f'{Path(workdir) / "vue-small"}/',
        f'{server_config_dir}/'
      )

      print(f'rsync {rsync_args}', file=sys.stderr)
      rsync_coro = asyncio.subprocess.create_subprocess_exec(
        'rsync', rsync_args
      )

      # subprocess.run(["cp", args.filename, join(server_config['dir'], "src", "RuleLib", "PDPADBNO.purs")])
      cp_coro = aioshutil.copy(
        args.filename,
        server_config_dir / 'src' / 'RuleLib' / 'Interview.purs'
      )

      os.environ["BASE_URL"] = server_config['base_url']

      async with (
        asyncio.TaskGroup() as taskgroup,
        aiofiles.open(server_config_dir / 'v8k.json', 'w') as write_file
      ):
        taskgroup.create_task(rsync_coro)
        taskgroup.create_task(cp_coro)
        await write_file.write(json.dumps(server_config))

      # os.chdir(server_config['dir'])
      # deliberately not capturing STDOUT and STDERR so it goes to console and we can see errors
      runvue = subprocess.run(server_config_cli, cwd = server_config_dir)

    print("v8k: fork(child): exiting", file=sys.stderr)

    return pyrs.m(
      port = server_config['port'],
      base_url = server_config['base_url'],
      vue_purs_tasks = aiostream.stream.just(vue_purs_post_process())
    )
    # sys.exit(0)

@curry
async def take_down(vuedict, slot) -> None:
  portnum = vuedict[slot]['port']
  if not portnum:
    print("unable to resolve portnum for slot " + slot + "; exiting", file=sys.stderr)
    # sys.exit(2)
  mymatches = print_server_info(portnum)
  if mymatches:
    async for mymatch in aiostream.stream.just(mymatches):
      print("killing pid " + mymatch[0] + " running vue server on port " + mymatch[1], file=sys.stderr)
      asyncio.subprocess.create_subprocess_exec('kill', mymatch[0])
  else:
    print(f"unable to find pid running vue server on port {portnum}", file=sys.stderr)

@curry
def do_down(
  args: argparse.Namespace,
  workdir: str | os.PathLike
) -> None:
  vuedict = read_all(workdir)
  # is there already a server running on the desired uuid-ssid-sheetid?
  existing = {s: js for (s, js) in vuedict.items()
              if js['ssid'] == args.ssid
              and js['sheetid'] == args.sheetid
              and js['uuid'] == args.uuid
              }

  for (s, js) in existing.items():
    print(f"* found allocated server(s) on our uuid/ssid/sheetid: {js['slot']}", file=sys.stderr)
    print_server_info(js['port'])
    take_down(vuedict, s)

@curry
def do_downdir(
  args: argparse.Namespace,
  workdir: str | os.PathLike
) -> None:
  vuedict = read_all(workdir)
  match vuedict:
    case {args.slotname: _}:
      take_down(vuedict, args.slotname)
    case _:
      print("slot does not exist! If the directory does exist you may need to rm -rf it by hand.", file=sys.stderr)

def setup_argparser() -> argparse.ArgumentParser:
  argparser = argparse.ArgumentParser(description='Manage a herd of Vue dev servers')
  argparser.add_argument('--workdir', action='store', required=("V8K_WORKDIR" not in os.environ),
                          help="workdir for v8k workers")

  subparsers = argparser.add_subparsers(help="sub-command help")

  parser_list = subparsers.add_parser('list', help='list servers')
  parser_list.set_defaults(func=do_list)

  parser_find = subparsers.add_parser('find', help='find server running a certain uuid ssid sid combo')
  parser_find.add_argument('--uuid', action='store', required=True, help="secret string, usually a UUID")
  parser_find.add_argument('--ssid', action='store', required=True, help="spreadsheet ID")
  parser_find.add_argument('--sheetid', action='store', required=True, help="sheet ID")
  parser_find.set_defaults(func=do_find)

  parser_up = subparsers.add_parser('up', help='create, replace, or update a server')
  parser_up.add_argument('--uuid', action='store', required=True, help="secret string, usually a UUID")
  parser_up.add_argument('--ssid', action='store', required=True, help="spreadsheet ID")
  parser_up.add_argument('--sheetid', action='store', required=True, help="sheet ID")
  parser_up.add_argument('--poolsize', action='store', required=False, type=int,
                          help="number of servers in the pool", default=9)
  parser_up.add_argument('--startport', action='store', required=True,
                          help="bottom port number of pool", default=8011)
  parser_up.add_argument('filename', metavar='file.purs', type=str, help="Purescript file")
  parser_up.set_defaults(func=do_up)

  parser_down = subparsers.add_parser('down', help='bring down a server')
  parser_down.set_defaults(func=do_down)
  parser_down.add_argument('--uuid', action='store', required=True, help="secret string, usually a UUID")
  parser_down.add_argument('--ssid', action='store', required=True, help="spreadsheet ID")
  parser_down.add_argument('--sheetid', action='store', required=True, help="sheet ID")

  parser_downdir = subparsers.add_parser('downdir', help='bring down a server by explicit slot name')
  parser_downdir.set_defaults(func=do_downdir)
  parser_downdir.add_argument('slotname', metavar='slot', type=str, help="two-digit slot id of vue server")

  return argparser

@curry
def main(
  command: str,
  uuid: str,
  spreadsheet_id: str,
  sheet_id: str,
  uuid_ss_folder: str | os.PathLike,
) -> Mapping[str, str | Callable[[], None]] | None:
  v8k_args: Sequence[str] = pyrse.sq(
    f'--workdir={v8k_workdir}',
    command,
  ) + (pyrse.sq(v8k_slots_arg) if v8k_slots_arg else pyrse.sq()) + pyrse.sq(
    f'--uuid={uuid}',
    f'--ssid={spreadsheet_id}',
    f'--sheetid={sheet_id}',
    f'--startport={v8k_startport}',
    f'{Path(uuid_ss_folder) / "purs" / "LATEST.purs"}'
  ) # type: ignore

  print(f'hello.py main: calling {" ".join(v8k_args)}', file=sys.stderr)

  parser: argparse.ArgumentParser = setup_argparser()
  args: argparse.Namespace = parser.parse_args(v8k_args)

  if not hasattr(args, 'func'):
    print("v8k: list / find / up / down / downdir")
    if "V8K_WORKDIR" in os.environ:
      print(f"V8K_WORKDIR = {os.environ['V8K_WORKDIR']}")
  else:
    if args.workdir is not None:
      workdir = args.workdir
    elif "V8K_WORKDIR" in os.environ:
      workdir = os.environ["V8K_WORKDIR"]
    else:
      print("v8k: you need to export V8K_WORKDIR=\"/home/something/multivue\"", file=sys.stderr)
      return
      # sys.exit(1)
    return args.func(args, workdir)

# if __name__ == '__main__':
#   main(sys.argv)