import logging

from . import __version__, actions
from .argparser import parse_args


def _setup_logging(out_dir):
    logging.getLogger('vk').setLevel(logging.WARNING)
    logging.basicConfig(
        filename=out_dir / 'logs.txt',
        filemode='a',
        format='[%(levelname)s] (%(asctime)s.%(msecs)03d - '
               '%(module)s - %(threadName)s): %(message)s',
        level=logging.INFO,
        datefmt='%m/%d/%Y %H:%M:%S'
    )


def main():
    """
    Входная точка программы
    """
    args = parse_args()

    (args.out_dir / '.json').mkdir(parents=True, exist_ok=True)
    (args.out_dir / '.sqlite').mkdir(parents=True, exist_ok=True)

    _setup_logging(args.out_dir)
    logging.info(f'VKMS {__version__} started')
    logging.info(f'Arguments: {args}')

    if args.action == 'dump':
        actions.dump(
            args.out_dir,
            args.include,
            args.exclude,
            args.token,
            args.threads,
            args.max_msgs,
            args.append,
            args.export_json
        )

    elif args.action == 'parse':
        actions.parse(args.out_dir, args.include, args.exclude, args.fmt)

    elif args.action == 'atch':
        actions.atch(args.out_dir, args.include, args.exclude, args.threads)

    logging.info('VKMS completed\n')
