from . import attachments, messages, saver, users
from .utils import dump_peer, load_peer


def dump(base_dir, out_dir, api, owner, peer_id):
    peer = {'info': api.messages.getConversationsById(peer_ids=str(peer_id))['items'][0]}
    peer['info']['owner'] = owner

    messages.download(base_dir, api, peer_id, peer)
    users.download(api, peer)

    dump_peer(out_dir, peer_id, peer)


def _parse(out_dir, peer_id):
    peer = load_peer(out_dir, peer_id)
    info = peer['info']
    usernames = users.parse(peer)

    return info, messages.parse(peer, usernames)


def parse(out_dir, peer_id, fmt):
    info, msgs = _parse(out_dir, peer_id)
    saver.save(out_dir, fmt, info, msgs)


def atch(out_dir, peer_id):
    _, msgs = _parse(out_dir, peer_id)
    attachments.download(out_dir, msgs)
