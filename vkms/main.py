import os

import vk

from . import actions
from .argparser import parse_args


def main():
    args = parse_args()

    os.makedirs(f'{args.out_dir}/.json/', exist_ok=True)

    session = vk.Session(access_token=args.token)
    api = vk.API(session, v='5.131')

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if args.action == 'dump':
        owner = api.users.get()[0]
        actions.dump(base_dir, args.out_dir, api, owner, args.peer_id)

    elif args.action == 'parse':
        actions.parse(args.out_dir, args.peer_id, args.fmt)

    elif args.action == 'atch':
        actions.atch(args.out_dir, args.peer_id)
