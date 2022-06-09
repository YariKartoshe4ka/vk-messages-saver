from argparse import ArgumentParser
from os import getenv

from .utils import parse_peer_ids


def parse_args():
    """
    Создает объект парсера и парсит аргументы

    Returns:
        argparse.Namespace: Набор аргументов парсера
    """
    parser = ArgumentParser()

    parser.add_argument(
        '-o',
        dest='out_dir',
        metavar='OUTDIR',
        default='vkms-result',
        help='Output directory where the materials are saved'
    )
    parser.add_argument(
        '-i',
        '--include',
        type=parse_peer_ids,
        default=set(),
        help='Comma-separated list of peer IDs to process. '
             'If not specified, all peers will be processed'
    )
    parser.add_argument(
        '-e',
        '--exclude',
        type=parse_peer_ids,
        default=set(),
        help='Comma-separated list of peer IDs that DON\'T need to be processed. '
             'Ignored if the --include parameter is specified'
    )

    subparsers = parser.add_subparsers(
        dest='action',
        required=True,
        help='One of the actions to be performed'
    )

    parser_dump = subparsers.add_parser(
        'dump',
        help='Save only the necessary information (VK API method outputs) '
             'in a machine-friendly format (JSON) for further processing'
    )

    parser_dump.add_argument(
        '--token',
        help='Access token of an account with scope of messages. '
             'You also can pass it as an env variable ACCESS_TOKEN'
    )
    parser_dump.add_argument(
        '-t',
        '--threads',
        type=int,
        default=2,
        help='Number of threads to download peers, defaults to 2'
    )
    parser_dump.add_argument(
        '-m',
        '--max-msgs',
        metavar='MAX',
        type=int,
        default=75000,
        help='Maximum number of messages to be saved in each conversation. '
             'Increasing the parameter will consume more RAM. '
             'Defaults to 75000'
    )

    parser_parse = subparsers.add_parser(
        'parse',
        help='Convert machine-friendly JSON format to human-readable'
    )

    parser_parse.add_argument(
        '-f',
        dest='fmt',
        choices=('txt',),
        default='txt',
        metavar='FORMAT',
        help='An easy-to-read format in which received messages must be '
             'converted. Supported formats: %(choices)s'
    )

    parser_atch = subparsers.add_parser(
        'atch',
        help='Download messages attachments (photos, audio, etc.)'
    )

    parser_atch.add_argument(
        '-t',
        '--threads',
        type=int,
        default=8,
        help='Number of threads to download peers, defaults to 8'
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
