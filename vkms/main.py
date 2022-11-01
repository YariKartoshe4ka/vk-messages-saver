import logging

from . import __version__, actions
from .argparser import parse_args

log = logging.getLogger(__name__)


def _setup_logging(out_dir, verbose):
    log_level = -min(verbose, 3) % 4 * logging.DEBUG

    for module in ('vk', 'sqlalchemy', 'urllib3'):
        logging.getLogger(module).setLevel(
            logging.WARNING if verbose < 3 else log_level
        )

    logging.basicConfig(
        filename=out_dir / 'logs.txt',
        filemode='a',
        format='%(asctime)s | %(levelname)s | %(name)s | %(threadName)s |: %(message)s',
        level=log_level
    )


def main():
    """
    Входная точка программы
    """
    args = parse_args()

    (args.out_dir / '.json').mkdir(parents=True, exist_ok=True)
    (args.out_dir / '.sqlite').mkdir(parents=True, exist_ok=True)

    _setup_logging(args.out_dir, args.verbose)
    log.info(f'VKMS {__version__} started')
    log.debug(f'Arguments: {args}')

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
        actions.atch(args.out_dir, args.include, args.exclude, args.threads, args.types)

    log.info('VKMS completed\n')
