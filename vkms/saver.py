def convert(msgs):
    buf = ''
    prev_msg = None

    for msg in msgs:
        print(msg.username)
        if prev_msg is None:
            buf += f'        [{msg.full_date()}]\n'

        elif msg.date.day - prev_msg.date.day >= 1:
            buf += f'\n        [{msg.full_date()}]\n'
            prev_msg = None

        text = []

        if msg.text:
            text.append(msg.text)

        for line in filter(None, convert(msg.fwd_msgs).split('\n')):
            text.append('| ' + line)

        for at in msg.attachments:
            text.append(str(at))

        if prev_msg is not None and prev_msg.username == msg.username:
            for line in text:
                if line == text[0]:
                    buf += f"[{msg.time()}] {' ' * len(msg.username)}  {line}\n"
                else:
                    buf += f"{' ' * 7} {' ' * len(msg.username)}  {line}\n"

        else:
            for line in text:
                if line == text[0]:
                    buf += f"[{msg.time()}] {msg.username}: {line}\n"
                else:
                    buf += f"{' ' * 7} {' ' * len(msg.username)}  {line}\n"

        prev_msg = msg

    return buf


def save(out_dir, peer_id, fmt, msgs):
    with open(f'{out_dir}/{peer_id}.txt', 'w') as file:
        file.write(convert(msgs))
