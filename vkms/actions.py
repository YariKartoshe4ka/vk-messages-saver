from . import attachments, messages, saver, users
from .utils import dump_peer, load_peer


def full(base_dir, api, args):
    dump(base_dir, args.out_dir, api, args.peer_id)
    parse(args.out_dir, args.peer_id, args.fmt)


def dump(base_dir, out_dir, api, peer_id):
    peer = {}

    messages.download(base_dir, api, peer_id, peer)
    users.download(api, peer_id, peer)

    dump_peer(out_dir, peer_id, peer)


def _parse(out_dir, peer_id):
    peer = load_peer(out_dir, peer_id)
    usernames = users.parse(peer)

    return messages.parse(peer, usernames)


def parse(out_dir, peer_id, fmt):
    msgs = _parse(out_dir, peer_id)
    saver.save(out_dir, peer_id, fmt, msgs)


def atch(out_dir, peer_id):
    msgs = _parse(out_dir, peer_id)
    attachments.download(out_dir, msgs)
