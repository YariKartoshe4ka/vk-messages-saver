import os

from . import actions
from .argparser import parse_args


def main():
    args = parse_args()

    os.makedirs(f'{args.out_dir}/.json/', exist_ok=True)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if args.action == 'dump':
        actions.dump(
            base_dir,
            args.out_dir,
            args.include,
            args.exclude,
            args.token,
            args.threads
        )

    elif args.action == 'parse':
        actions.parse(args.out_dir, args.include, args.exclude, args.peer_id, args.fmt)

    elif args.action == 'atch':
        actions.atch(args.out_dir, args.include, args.exclude, args.peer_id)
