from os import makedirs


def convert_txt(msgs):
    buf = ''
    prev_msg = None

    for msg in msgs:
        if prev_msg is None:
            buf += f'        [{msg.full_date()}]\n'

        elif msg.date.day - prev_msg.date.day >= 1:
            buf += f'\n        [{msg.full_date()}]\n'
            prev_msg = None

        text = []

        if msg.action:
            text.append(f'[{msg.action}]')

        if msg.reply_msg:
            for line in filter(None, convert_txt([msg.reply_msg]).split('\n')):
                text.append('> ' + line)

        if msg.text:
            text.append(msg.text)

        for line in filter(None, convert_txt(msg.fwd_msgs).split('\n')):
            text.append('| ' + line)

        for atch in msg.atchs:
            if atch.tp == 'photo':
                text.append(f'[фото: {atch.hash}]')
            elif atch.tp == 'audio_message':
                text.append(f'[голосвое сообщение: {atch.hash}]')
            elif atch.tp == 'wall':
                text.append(f'[пост: {atch.url}]')
            else:
                text.append('{uknown attachment}')

        for line in text:
            if line == text[0]:
                if prev_msg and prev_msg.username == msg.username:
                    username = ' ' * (len(msg.username) + 1)
                else:
                    username = msg.username + ':'

                buf += f"[{msg.time()}] {username} {line}\n"

            else:
                buf += f"{' ' * 7} {' ' * len(msg.username)}  {line}\n"

        prev_msg = msg

    return buf


def save(out_dir, peer_id, fmt, msgs):
    makedirs(f'{out_dir}/{fmt}/', exist_ok=True)

    converter = globals()['convert_' + fmt]

    with open(f'{out_dir}/{fmt}/{peer_id}.{fmt}', 'w') as file:
        file.write(converter(msgs))
