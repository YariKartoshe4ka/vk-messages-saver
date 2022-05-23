from argparse import ArgumentParser
from os import getenv
from pathlib import Path


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        '--token',
        help='Access token of an account with scope of messages. '
             'You also can pass it as an env variable ACCESS_TOKEN'
    )
    parser.add_argument(
        '--peer',
        dest='peer_id',
        required=True,
        help='ID of the conversation to dump'
    )
    parser.add_argument(
        '-o',
        dest='out_dir',
        metavar='OUTDIR',
        type=Path,
        default='vkms-result',
        help='Output directory where the materials are saved'
    )

    subparsers = parser.add_subparsers(
        dest='action',
        help='One of the actions to be performed'
    )

    parser_full = subparsers.add_parser(
        'full',
        help='Perform full message saving '
             '(includes all of the following actions)'
    )
    subparsers.add_parser(
        'dump',
        help='Save only the necessary information (VK API method outputs) '
             'in a machine-friendly format (JSON) for further processing'
    )
    parser_parse = subparsers.add_parser(
        'parse',
        help='Convert machine-friendly JSON format to human-readable'
    )
    subparsers.add_parser(
        'atch',
        help='Download messages attachments (photos, audio, etc.)'
    )

    parser_full.add_argument(
        '-f',
        dest='fmt',
        choices=('txt',),
        default='txt',
        metavar='FORMAT',
        help='An easy-to-read format in which received messages must be '
             'converted. Supported formats: %(choices)s'
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

    args = parser.parse_args()

    token = getenv('ACCESS_TOKEN') or args.token

    if token is None:
        parser.error(
            'You must define token as an ACCESS_TOKEN env variable '
            'or using the --token argument'
        )

    args.token = token

    return args
