from argparse import ArgumentParser
from pathlib import Path


def create_parser():
    parser = ArgumentParser()

    parser.add_argument(
        '--token',
        required=True,
        help='Access token of an account with scope of messages'
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

    subparsers = parser.add_subparsers(dest='action', help='One of the actions to be performed')

    parser_full = subparsers.add_parser('full', help='Perform full message saving (includes all of the following actions)')
    parser_dump = subparsers.add_parser('dump', help='Save only the necessary information (VK API method outputs) in a machine-friendly format (JSON) for further processing')
    parser_parse = subparsers.add_parser('parse', help='Convert machine-friendly JSON format to human-readable')
    parser_atсh = subparsers.add_parser('atсh', help='Download messages attachments (photos, audio, etc.)')

    parser_full.add_argument(
        '-f',
        dest='fmt',
        choices=('txt',),
        default='txt',
        metavar='FORMAT',
        help='An easy-to-read format in which received messages must be converted. Supported formats: %(choices)s'
    )

    parser_parse.add_argument(
        '-f',
        dest='fmt',
        choices=('txt',),
        default='txt',
        metavar='FORMAT',
        help='An easy-to-read format in which received messages must be converted. Supported formats: %(choices)s'
    )

    return parser
