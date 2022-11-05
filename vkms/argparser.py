from argparse import ArgumentParser, RawDescriptionHelpFormatter
from os import getenv
from pathlib import Path

from .utils import parse_peer_ids


class CustomHelpFormatter(RawDescriptionHelpFormatter):
    def _format_action_invocation(self, action):
        # Не повторять metavar для каждой опции
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return '/'.join(action.option_strings) + ' ' + args_string


description = 'Utility for saving VKontakte conversations'
epilog = '''examples:
  %(prog)s -vv -i c45,558891166 dump --export-json
  %(prog)s -e 100,-22822305 parse -f html
  %(prog)s atch --ts photos,audios
'''


def parse_args():
    """
    Создает объект парсера и парсит аргументы

    Returns:
        argparse.Namespace: Набор аргументов парсера
    """
    parser = ArgumentParser(
        formatter_class=CustomHelpFormatter,
        description=description,
        epilog=epilog
    )

    parser.add_argument(
        '-o',
        '--out',
        dest='out_dir',
        metavar='OUTDIR',
        type=Path,
        default='vkms-result',
        help='Output directory where the materials are saved'
    )
    include_or_exclude_group = parser.add_mutually_exclusive_group()
    include_or_exclude_group.add_argument(
        '-i',
        '--include',
        type=parse_peer_ids,
        default=set(),
        help='Comma-separated list of peer IDs to process. '
             'If not specified, all peers will be processed'
    )
    include_or_exclude_group.add_argument(
        '-e',
        '--exclude',
        type=parse_peer_ids,
        default=set(),
        help='Comma-separated list of peer IDs that DON\'T need to be processed. '
             'Incompatible with the --include flag'
    )
    parser.add_argument(
        '-v',
        dest='verbose',
        action='count',
        default=0,
        help='Increase logs verbosity level (use -vvv for greater effect)'
    )

    subparsers = parser.add_subparsers(
        dest='action',
        required=True,
        help='One of the actions to be performed',
    )

    parser_dump = subparsers.add_parser(
        'dump',
        help='Save only the necessary information (VK API method outputs) '
             'in a machine-friendly format (SQLite + JSON) for further processing',
        formatter_class=CustomHelpFormatter,
        description=description,
        epilog=epilog
    )

    parser_dump.add_argument(
        '--token',
        help='Access token of an account with scope of messages. '
             'You also can pass it as an env variable ACCESS_TOKEN'
    )
    parser_dump.add_argument(
        '--max',
        dest='max_msgs',
        metavar='MAX',
        type=lambda x: float('inf') if x.lower() == 'all' else int(x),
        default=100000,
        help='Maximum number of messages to be saved in each conversation. '
             'Defaults to 100000. Pass "all" to save the whole conversation'
    )
    parser_dump.add_argument(
        '-a',
        '--append',
        action='store_true',
        help='Don\'t re-download the peer, but only new messages'
    )
    parser_dump.add_argument(
        '-t',
        '--threads',
        type=int,
        default=2,
        help='Number of threads to download peers, defaults to 2'
    )
    parser_dump.add_argument(
        '--export-json',
        action='store_true',
        help='Additionally export peer information in JSON format'
    )

    parser_parse = subparsers.add_parser(
        'parse',
        help='Convert machine-friendly JSON format to human-readable',
        formatter_class=CustomHelpFormatter,
        description=description,
        epilog=epilog
    )

    parser_parse.add_argument(
        '-f',
        dest='fmt',
        choices=('txt', 'html'),
        default='txt',
        metavar='FORMAT',
        help='An easy-to-read format in which received messages must be '
             'converted. Supported formats: %(choices)s'
    )

    parser_atch = subparsers.add_parser(
        'atch',
        help='Download messages attachments (photos, audio, etc.)',
        formatter_class=CustomHelpFormatter,
        description=description,
        epilog=epilog
    )

    parser_atch.add_argument(
        '-t',
        '--threads',
        type=int,
        default=8,
        help='Number of threads to download attachments, defaults to 8'
    )
    parser_atch.add_argument(
        '--ts',
        dest='types',
        type=lambda x: set(x.split(',')),
        default={'photos', 'docs', 'stickers', 'gifts', 'audios', 'graffiti'},
        help='Comma-separated list of attachment types that need to be be saved. '
             'Available options: photos, docs, stickers, gifts, audios, graffiti. '
             'Defaults to all types of attachments'
    )

    args = parser.parse_args()

    if args.action == 'dump':
        token = getenv('ACCESS_TOKEN') or args.token

        if token is None:
            parser.error(
                'You must define token as an ACCESS_TOKEN env variable '
                'or using the --token argument'
            )

        args.token = token

    return args
