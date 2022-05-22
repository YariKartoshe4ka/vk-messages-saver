from argparse import ArgumentParser
import os

import vk

from . import messages, users, saver


def main():
    parser = ArgumentParser()

    parser.add_argument(dest='token', metavar='TOKEN', help='Access token of an account with scope of messages')
    parser.add_argument(dest='peer_id', metavar='PEER_ID', help='ID of the conversation to dump')

    args = parser.parse_args()

    session = vk.Session(access_token=args.token)
    api = vk.API(session, v='5.131')

    base_dir = os.path.dirname(os.path.abspath(__file__))

    peer_json = messages.download(base_dir, api, args.peer_id)
    users_json = users.download(base_dir, api, peer_json)

    all_users = users.parse(users_json)
    all_messages, peer_messages = messages.parse(peer_json, all_users)

    saver.save(all_users, peer_messages, 'txt')
