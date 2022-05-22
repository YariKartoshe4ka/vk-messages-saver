def convert(messages):
    buf = ''
    prev_msg = None

    for msg in messages:
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

        if prev_msg is not None and prev_msg.user is msg.user:
            for line in text:
                if line == text[0]:
                    buf += f"[{msg.time()}] {' ' * len(msg.user.name)}  {line}\n"
                else:
                    buf += f"{' ' * 7} {' ' * len(msg.user.name)}  {line}\n"

        else:
            for line in text:
                if line == text[0]:
                    buf += f"[{msg.time()}] {msg.user.name}: {line}\n"
                else:
                    buf += f"{' ' * 7} {' ' * len(msg.user.name)}  {line}\n"

        prev_msg = msg

    return buf


def save(users, messages, fmt):
    with open('output.txt', 'w') as file:
        file.write(convert(messages))
