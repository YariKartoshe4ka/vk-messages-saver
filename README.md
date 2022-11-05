# vk-messages-saver

[![Maintanance](https://img.shields.io/maintenance/yes/2022?style=flat-square)](https://github.com/YariKartoshe4ka/vk-messages-saver/commits/master)
[![Releases](https://img.shields.io/github/v/release/YariKartoshe4ka/vk-messages-saver?style=flat-square)](https://github.com/YariKartoshe4ka/vk-messages-saver/releases)
[![VK API](https://img.shields.io/static/v1?label=API&message=5.131&color=a938e4&labelColor=000000&logo=vk&style=flat-square)](https://dev.vk.com/)
[![PyPI](https://img.shields.io/pypi/pyversions/vkms?style=flat-square)](https://pypi.org/project/vkms/)
[![Speed](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/YariKartoshe4ka/bf106ade592cbea6189b89f71c7545e9/raw/vkms-speed.json)](https://github.com/YariKartoshe4ka/vk-messages-saver/actions)

Утилита для сохранения переписок ВКонтакте


### Установка

Загружаем и устанавливаем последнюю версию VKMS из [PyPI](https://pypi.org/project/vkms/)

```bash
pip install vkms
```


### Использование

1. Получаем токен доступа с правами на сообщения от официального приложения. Можно воспользоваться [этим сайтом](https://vkhost.github.io/). После авторизации копируем из адресной строки параметр *access_token* и вставляем его в терминал

    ```bash
    export ACCESS_TOKEN='...'
    ```

2. Запускаем VKMS и скачиваем полную информацию о переписках

    ```bash
    vkms dump
    ```

    Теперь можно спарсить полученные данные в удобный для чтения формат

    ```bash
    vkms parse
    ```


### Функции

В данный момент VKMS может:

- Сохранять переписки в программном формате (JSON), доступна многопоточная загрузка (`vkms dump`)
- Сохранять переписки в удобном для чтения формате (`vkms parse`)
    - TXT, за основу была взята структура формата [hikiko4ern'а](https://github.com/hikiko4ern/vk_dump)
    - HTML, кастомная верстка, максимально приближенная к официальному приложению VK Android

<table>
    <tr align="center">
        <th>HTML</th>
        <th>TXT</th>
    </tr>
    <tr>
        <td width="50%"><img src="docs/html_saver_example.png" alt="Пример переписки в HTML формате"></td>
        <td width="50%"><img src="docs/txt_saver_example.png" alt="Пример переписки в TXT формате"></td>
    </tr>
</table>

- Загружать вложения, доступна многопоточная загрузка (`vkms atch`)
    - Фото
    - Документы
    - Стикеры
    - Подарки
    - Голосовые сообщения
    - Граффити

[Подробное описание](https://github.com/YariKartoshe4ka/vk-messages-saver/blob/master/docs/DOCS.md)
