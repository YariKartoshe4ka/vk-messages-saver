# vk-messages-saver | Changelog

## [Unreleased]
#### Security
- Исправлен баг с неправильной конвертацией перепсики в HTML (XSS уязвимость)

## [1.0.2] - 2023-05-31
#### Fixed
- Исправлен баг с бесконечным циклом в `peers.py` при количестве переписок > 200
- Исправлен баг с обработкой сообщений с идентификатором отправителя 0

## [1.0.1] - 2023-03-13
#### Fixed
- Исправлен баг с кодировками записываемых файлов (на Windows появляется ошибка *UnicodeEncodeError*)
- Исправлен баг с локалями месяцов при генерации дат `msg.full_date()`
- Исправлен баг с загрузкой диалога, состоящего из сообщений только одного участника

## [1.0.0] - 2022-11-05
#### Added
- Добавлена опция `-a/--append` (`vkms dump`), отвечающая за дозапись новых сообщений
- Добавлена опция `--export-json` (`vkms dump`), отвечающая за сохранение переписки в JSON формате
- Добавлена опция `-v` (`vkms dump`), отвечающая за уровень логгирования
- Добавлена опция `--ts` (`vkms atch`), отвечающая за типы скачиваемых вложений
- У опции `--max` (`vkms dump`) появилось новое значение `all` (для загрузки переписки целиком)
- Добавлена темная тема для HTML формата, переключиться на которую можно, нажав клавишу "**t**"
- Добавлена обработка событий возвращения в беседу и выхода из беседы
#### Changes
- **BREAKING:** Переход от JSON формата к SQLite. Переписки, загруженные предыдущими версиями
VKMS, больше не поддерживаются. Возможность сохранить переписку в JSON формате оставлена
- Парсер формата TXT переписан и теперь использует константное кол-во памяти, а не линейное
(появилась возможность обработки длинных переписок)
- Переход от самодельных пулов на *ThreadPoolExecutor* (ускорение загрузки)
#### Fixed
- Обработка удаленных фото и комментариев к записи больше не вызывает ошибку
- Исправлен баг в двух парсерах (TXT и HTML), связанный с неправильным разделением сообщений по датам


## [0.2.0] - 2022-07-06
#### Added
- Реализован новый удобный для чтения формат - HTML
#### Changed
- Автоматическое версионирование проекта через *setuptools_scm*
#### Deprecated
- Прекращена поддержка Python 3.7 из-за используемой библиотеки [minify-html](https://pypi.org/project/minify-html/)
#### Fixed
- Загрузка вложений не только из сообщений первого порядка, но и из пересланных сообщений

## [0.1.0] - 2022-06-09
#### Added
- Сохранение информации о переписке в JSON формате (`vkms dump`), мультипоточная загрузка
- Парсинг полученной информации в удобный для чтения формат (`vkms parse`)
- Реализован первый удобный для чтения формат - TXT
- Сохранение вложений переписки (`vkms atch`), мультипоточная загрузка
- Логгирование всех внутренних событий на разных уровнях (*DEBUG* - *ERROR*)

[Unreleased]: https://github.com/YariKartoshe4ka/vk-messages-saver/compare/1.0.2...HEAD
[1.0.2]: https://github.com/YariKartoshe4ka/vk-messages-saver/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/YariKartoshe4ka/vk-messages-saver/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/YariKartoshe4ka/vk-messages-saver/compare/0.2.0...1.0.0
[0.2.0]: https://github.com/YariKartoshe4ka/vk-messages-saver/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/YariKartoshe4ka/vk-messages-saver/releases/tag/0.1.0
