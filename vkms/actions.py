import logging
from time import sleep

import vk
from sqlalchemy import func
from vk.exceptions import VkAPIError

from . import attachments
from . import database as db
from . import messages, peers, saver, users

log = logging.getLogger(__name__)


def dump(out_dir, include, exclude, token, nthreads, max_msgs, append, export_json):
    """
    Скачивает указанные переписки в формате JSON (результаты обращений к VK API)

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно сохранить
        exclude (set): Множество идентификаторов переписок, которые не нужно сохранять
        token (str): Токен доступа к VK API
        nthreads (int): Количество потоков, загружающих переписки
        max_msgs (int):  Кол-во сообщений, которое нужно сохранить (может быть меньше
            заявленного, если переписка содержит меньше сообщений)
        append (bool): Режим дозаписи новых сообщений
        export_json (bool): Дополнительно экспортировать данные о переписке а JSON формате
    """
    # Получаем объект для работы с VK API
    class API(vk.API):
        def on_api_error_6(self, request):
            sleep(1)
            return self.send(request)

        def get_captcha_key(self, request):
            return input(f'Captcha needed ({request.api_error.captcha_img}): ')

    api = API(access_token=token, v='5.131')

    # Загружаем информацию о владельце страницы
    try:
        account = api.users.get()[0]
    except VkAPIError:
        print('Failed to load base information. '
              'See logs for details: ' + out_dir / 'logs.txt')

        return

    # Загружаем информацию о всех переписках пользователя
    peers_info = peers.download(api)

    # Создаем словарь вида id-переписка для быстрого доступа к JSON'у конкретной переписки
    peer_by_id = {peer['peer']['id']: peer for peer in peers_info}

    # Создаем множество идентификаторов для последующей выборки нужных
    peer_ids = set(peer_by_id.keys())

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    peer_ids = list(peer_ids)

    processed = 0

    log.debug(f"Peers: {', '.join(map(str, peer_ids))}")

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        log.debug(f'Processing peer {peer_id}')

        print(f'{round(processed / len(peer_ids) * 100)}%', end='\r')

        db_path = out_dir / f'.sqlite/{peer_id}.sqlite'

        if not append:
            # Если переписку нужно загрузить заново, полностью очищаем БД
            db_path.unlink(missing_ok=True)

        session = db.connect(db_path)

        if not append:
            # Сохраняем информацию о переписке и владельце страницы
            db.Base.metadata.create_all(session.bind)
            session.add(db.Peer(id=peer_id, account=account, info=peer_by_id[peer_id]))
            session.flush()

        try:
            # Сохраняем все сообщения и информацию об участниках переписки
            user_ids = set()
            group_ids = set()

            pres_user_ids = {
                id for id, in
                session.query(db.User.id).filter(db.User.id > 0)
            }
            pres_group_ids = {
                abs(id) for id, in
                session.query(db.User.id).filter(db.User.id < 0)
            }

            # Идентификатор последнего сообщения переписки
            start_msg_id, _ = session.query(
                db.Message.id,
                func.max(db.Message.date)
            ).one_or_none()

            for chunk in messages.download(api, peer_id, nthreads, max_msgs, start_msg_id):
                msgs = []

                for msg_json in chunk:
                    msg = db.Message(json=msg_json)
                    msgs.append(msg)

                    users.collect(msg_json, user_ids, group_ids)

                session.bulk_save_objects(msgs)

            if user_ids or group_ids:
                # Исключаем пользователей, которые уже есть в БД
                user_ids -= pres_user_ids
                group_ids -= pres_group_ids

                for chunk in users.download(api, nthreads, user_ids, group_ids):
                    session.bulk_save_objects(db.User(user_json) for user_json in chunk)

        except VkAPIError as e:
            log.error(f'Downloading peer {peer_id} failed: {e}')
            session.rollback()
            return

        # Все хорошо, сохраняем изменения
        session.commit()

        # Если нужно, дополнительно экспортируем информацию в JSON
        if export_json:
            peers.export_json(out_dir, session)

        processed += 1

    print('100%')


def parse(out_dir, include, exclude, fmt):
    """
    Сохраняет полученные переписки в удобном для чтения формате

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно сохранить
        exclude (set): Множество идентификаторов переписок, которые не нужно сохранять
        fmt (str): Формат, в котором следует сохранять переписки
    """
    # Получаем идентификаторы всех скачанных переписок
    peer_ids = {int(file.name.rstrip('.sqlite')) for file in out_dir.glob('.sqlite/*.sqlite')}

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    processed = 0

    log.debug(f"Peers: {', '.join(map(str, peer_ids))}")

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        log.debug(f'Processing peer {peer_id}')

        session = db.connect(out_dir / f'.sqlite/{peer_id}.sqlite')

        print(f'{round(processed / len(peer_ids) * 100)}%', end='\r')

        peer = peers.Peer(session)
        saver.save(out_dir, fmt, peer)

        processed += 1

    print('100%')


def atch(out_dir, include, exclude, nthreads, types):
    """
    Скачивает вложения указанных переписок

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно обработать
        exclude (set): Множество идентификаторов переписок, которые не нужно обрабатывать
        nthreads (int): Количество потоков, загружающих вложения
    """
    # Получаем идентификаторы всех скачанных переписок
    peer_ids = {int(file.name.rstrip('.sqlite')) for file in out_dir.glob('.sqlite/*.sqlite')}

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    log.debug(f"Peers: {', '.join(map(str, peer_ids))}")

    peer_ids_cnt = 0

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        log.debug(f'Processing peer {peer_id}')

        session = db.connect(out_dir / f'.sqlite/{peer_id}.sqlite')

        print(f'{round(peer_ids_cnt / len(peer_ids) * 100)}%', end='\r')

        peer = peers.Peer(session)
        attachments.download(out_dir, peer, nthreads, types)

        peer_ids_cnt += 1

    print('100%')
