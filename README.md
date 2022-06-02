# vk-messages-saver

[![Maintanance](https://img.shields.io/maintenance/yes/2022?style=flat-square)](https://github.com/YariKartoshe4ka/vk-messages-saver/commits/master)
[![Releases](https://img.shields.io/github/v/release/YariKartoshe4ka/vk-messages-saver?style=flat-square)](https://github.com/YariKartoshe4ka/vk-messages-saver/releases)
[![VK API](https://img.shields.io/static/v1?label=API&message=5.131&color=a938e4&labelColor=000000&logo=vk&style=flat-square)](https://dev.vk.com/)
[![PyPI](https://img.shields.io/pypi/pyversions/vkms?style=flat-square)](https://pypi.org/project/vkms/)
![](https://img.shields.io/codacy/grade/7d64b70fa82f4aac9e61ae88d6d9a2b2?style=flat-square)

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
- Загружать вложения, доступна многопоточная загрузка (`vkms atch`)
    - Фото
    - Документы
    - Стикеры
    - Подарки
    - Голосовые сообщения
    - Граффити

[Подробное описание](docs/DOCS.md)
