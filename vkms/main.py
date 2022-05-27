from os import makedirs

from . import actions
from .argparser import parse_args


def main():
    args = parse_args()

    makedirs(f'{args.out_dir}/.json/', exist_ok=True)

    if args.action == 'dump':
        actions.dump(args.out_dir, args.include, args.exclude, args.token, args.threads)

    elif args.action == 'parse':
        actions.parse(args.out_dir, args.include, args.exclude, args.fmt)

    elif args.action == 'atch':
        actions.atch(args.out_dir, args.include, args.exclude, args.threads)
