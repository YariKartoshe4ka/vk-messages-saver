import os
from io import StringIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from minify_html import minify
from pathvalidate import sanitize_filename


def save(out_dir, fmt, peer):
    """
    Конвертирует и сохраняет сообщения в удобном для чтения формате

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        fmt (str): Формат, в котором нужно сохранить переписку
        peer (peers.Peer): Объект переписки
    """
    globals()['save_' + fmt](out_dir, peer)


def save_txt(out_dir, peer):
    """
    Сохраняет переписку в формате TXT. Идея взята у hikiko4ern
    Ссылка: [https://github.com/hikiko4ern/vk_dump]
    """
    # Создаем папку для хранения переписки
    (out_dir / 'dialogs/txt').mkdir(parents=True, exist_ok=True)

    path = out_dir / 'dialogs/txt/{title}_{peer_id}.txt'.format(
        title=sanitize_filename(peer.title, replacement_text='_'),
        peer_id=peer.info['peer']['id']
    )

    # Сохраняем конвертированный текст
    with open(path, 'w') as file:
        _convert_txt_msgs(peer.msgs, peer.account['id'], file)


def _convert_txt_msgs(msgs, account_id, file=None):
    prev_msg = None

    for msg in msgs:
        # Если предыдущего сообщения не было, пишем дату текущего сообщения
        if prev_msg is None:
            file.write(f'        [{msg.full_date()}]\n')

        # Если предыдущее и текущее сообщения были отправлены в разные дни,
        # пишем дату текущего сообщения
        elif msg.date.date() != prev_msg.date.date():
            file.write(f'\n        [{msg.full_date()}]\n')
            prev_msg = None

        # Записываем полученный текст в буффер переписки
        for i, line in enumerate(_convert_txt_msg(msg, account_id)):
            if i == 0:
                if prev_msg and prev_msg.username == msg.username:
                    username = ' ' * (len(msg.username) + 1)
                else:
                    username = msg.username + ':'

                file.write(f"[{msg.time()}] {username} {line}\n")
            else:
                file.write(f"{' ' * 7} {' ' * len(msg.username)}  {line}\n")

        # Обновляем предыдущее сообщение
        prev_msg = msg


def _convert_txt_msg(msg, account_id, *, is_reply=False):
    # Буффер текста текущего сообщения (каждый элемент - новая строка)
    lines = []

    # Если сообщение является сервисным, добавляем текст действия
    if msg.action:
        lines.append(f'[{msg.action}]')

    # Если сообщение отправлено в ответ на другое, обрабатываем другое
    # сообщение отдельно
    if not is_reply and msg.reply_msg:
        for i, line in enumerate(_convert_txt_msg(msg.reply_msg, account_id, is_reply=True)):
            lines.append('{username} {line}'.format(
                username=(
                    msg.reply_msg.username + '>'
                    if i == 0 else
                    ' ' * (len(msg.reply_msg.username) + 1)
                ),
                line=line
            ))

    # Добавляем текст самого сообщения (если есть), обрабатывая обращения
    if msg.text:
        lines.extend(
            msg.replace_mention(line, r'\1')
            for line in msg.text.split('\n')
        )

    # Если есть пересланные сообщения, обрабатываем их рекурсивно
    fwd_msgs_file = StringIO()
    _convert_txt_msgs(msg.fwd_msgs, account_id, fwd_msgs_file)
    fwd_msgs_file.seek(0)

    for line in fwd_msgs_file:
        if line.rstrip():
            lines.append('| ' + line.rstrip())

    # Добавляем место/геолокацию (если есть)
    if msg.geo:
        lines.append('[место: {}, {}]'.format(*msg.geo))

    # Обрабатываем медиавложения
    for atch in msg.atchs:
        if atch.tp == 'photo':
            lines.append(f'[фото: {atch.filename}]')
        elif atch.tp == 'video':
            lines.append(f'[видео: {atch.filename}]')
        elif atch.tp == 'audio':
            lines.append(f'[аудио: {atch.title}]')
        elif atch.tp == 'doc':
            lines.append(f'[документ: {atch.filename}]')
        elif atch.tp == 'link':
            lines.append(f'[ссылка: {atch.title} ({atch.url})]')
        elif atch.tp == 'wall':
            lines.append(f'[пост: {atch.url}]')
        elif atch.tp == 'wall_reply':
            lines.append(f'[комментарий: {atch.url}]')
        elif atch.tp == 'sticker':
            lines.append(f'[стикер: {atch.filename}]')
        elif atch.tp == 'gift':
            lines.append(f'[подарок: {atch.filename}]')
        elif atch.tp == 'audio_message':
            lines.append(f'[голосвое сообщение: {atch.filename}]')
        elif atch.tp == 'graffiti':
            lines.append(f'[граффити: {atch.filename}]')

        elif atch.tp == 'call':
            lines.append('[{tp}звонок: {state}{duration}]'.format(
                tp=atch.call_type,
                state=atch.get_state(account_id),
                duration=f' ({atch.duration})' if atch.state == 'reached' else ''
            ))

        elif atch.tp == 'poll':
            pool_text = [f'[опрос: "{atch.title}", {atch.anon}, {atch.mult}]']
            max_len = len(pool_text[0])

            for ans in atch.answers:
                pool_text.append(
                    '  ["{text}":   {{indent}}{is_voted}{rate}% ({votes}/{all_votes})]'.format(
                        text=ans['text'],
                        is_voted='✓ ' if ans['id'] in atch.answer_ids else '',
                        rate=round(ans['rate']),
                        votes=ans['votes'],
                        all_votes=atch.all_votes
                    )
                )
                max_len = max(max_len, len(pool_text[-1]) - len('{indent}'))

            for line in pool_text:
                lines.append(line.format(
                    indent=' ' * (max_len - len(line) + len('{indent}'))
                ))
        else:
            lines.append('[uknown attachment]')

    # Если сообщение является исчезающим
    if msg.is_expired:
        lines.append('[Сообщение исчезло]')

    # Если сообщение было отредактировано, добавляем заметку
    elif msg.is_edited:
        lines.append('(ред.)')

    return lines


def save_html(out_dir, peer):
    """
    Сохраняет переписку в формате HTML. Верстка написана с нуля и была максимально
    приближена к версии VK на Android. В качестве бэкграунда использован шаблонизатор
    Jinja2
    """
    (out_dir / 'dialogs/html').mkdir(parents=True, exist_ok=True)

    path = out_dir / 'dialogs/html/{title}_{peer_id}.html'.format(
        title=sanitize_filename(peer.title, replacement_text='_'),
        peer_id=peer.info['peer']['id']
    )

    base_dir = Path(__file__).parent.resolve()

    # Инициализируем шаблонизатор
    env = Environment(loader=FileSystemLoader(base_dir / 'templates'))

    def relpath(path):
        return os.path.relpath(path, start=out_dir / 'dialogs/html')

    env.filters['relpath'] = relpath

    template = env.get_template('peer.html')

    # Сохраняем конвертированный текст (предварительно сжав HTML)
    with open(path, 'w') as file:
        file.write(minify(
            template.render(out_dir=out_dir, peer=peer),
            minify_js=True,
            minify_css=True
        ))
