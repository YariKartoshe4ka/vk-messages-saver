from itertools import islice

# Названия месяцев на русском
months = [
    ' ', 'января', 'февраля', 'марта',
    'апреля', 'мая', 'июня', 'июля',
    'августа', 'сентября', 'октября',
    'ноября', 'декабря'
]


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


def chunks(iterable, size):
    for i in range(0, len(iterable), size):
        yield list(islice(iterable, i, i + size))
