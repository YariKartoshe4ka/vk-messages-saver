from json import dump, load

# Названия месяцев на русском
months = [
    ' ', 'января', 'февраля', 'марта',
    'апреля', 'мая', 'июня', 'июля',
    'августа', 'сентября', 'октября',
    'ноября', 'декабря'
]


def load_peer(out_dir, peer_id):
    """
    Загружает переписку из скачанного JSON по указанному идентификатору

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer_id (int): Идентификатор переписки, JSON которой
            необходимо загрузить
    """
    with open(f'{out_dir}/.json/{peer_id}.json', 'r') as file:
        return load(file)


def dump_peer(out_dir, peer):
    """
    Выгружает объект переписки в JSON

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer (dict): Объект (словарь) переписки, которую необходимо
            выгрузить в JSON
    """
    with open(f"{out_dir}/.json/{peer['info']['peer']['id']}.json", 'w') as file:
        dump(peer, file)


def parse_peer_ids(peer_ids):
    """
    Парсит разделенный запятыми список идентификаторов переписок в
    множество, обрабатывая особые случаи

    Args:
        peer_ids (str): Разделенный запятыми список идентификаторов переписок

    Returns:
        Set[int]: Множество идентификаторов переписок
    """
    res = set()

    for peer_id in peer_ids.split(','):
        if not peer_id:
            continue

        # Сокращенный вариант идентификатора беседы
        if peer_id[0] == 'c' and peer_id[1:].isdigit():
            res.add(2000000000 + int(peer_id[1:]))

        # Идентификатор переписки с пользователем и группой
        elif peer_id.isdigit() or peer_id[0] == '-' and peer_id[1:].isdigit():
            res.add(int(peer_id))

        else:
            raise ValueError('Invalid peer ID: ' + peer_id)

    return res
