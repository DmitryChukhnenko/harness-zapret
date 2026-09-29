# Живая проверка

## Результат 29 сентября 2026

Docker Desktop Linux engine 29.8.0. Все три образа собраны, контейнеры работают;
в конце диагностик live strategy пустая, deployment `idle`, reconcile `PASS`.
Сохранённые [результаты с метками времени и SHA-256](evidence/live-20260929.json)
получены командами ниже, исходные архивы находятся в `data/reports/live/`.

| Проверка | Измеренный результат |
|---|---|
| Offline suite Windows / Linux | 69 passed на каждой платформе |
| Live topology pytest | 1 passed; client default route через Zapret, FORWARD растёт, HTTPS OPEN |
| Blockcheck2 custom smoke | exit 0; 3 факта; 2 стратегии, включая `s1<d1`, argv совпадает после обратимого shell quoting |
| Recheck | 4 OPEN-факта: 2 домена × 2 точки, каждый минимум на 2 IP |
| Exclusion lease | candidate остановлен, exclusions очищены, active PID сохранён |
| П-5: watchdog | обе точки живы; одна осечка не откатывает; ожидание; закрытие окна; guard/repair rollback и nfqws2 восстановлен |
| П-6/П-7 | overlap отклонён и lock освобождён; client control недоступен → UNMEASURED без rollback |
| П-11 | strategy drift и client route drift обнаружены снаружи; после восстановления PASS |
| П-12 | занятый operation lock, незапланированный watchdog, та же строка и unsafe строка отклонены |
| Независимость | lifecycle прошёл при остановленном Harness; без Zapret прямой client curl завершился timeout 28 |

В lifecycle используется отдельный каталог deployment, fixture допуска и сокращённые
окна ожидания 1/5 секунд, наблюдения 2/60 секунд. Сетевые пробы, nfqws2, nftables,
блокировки, запись backup и rollback настоящие. Недоступность client моделируется
реальным firewall reject управляющего TCP-соединения. Эти данные закрывают
перечисленные механизмы в лаборатории; они не доказывают прохождение gates на
двух реальных датах или эффективность обхода конкретного DPI.

Первый smoke завершился timeout: отсутствовали hexdump и CAP_KILL для остановки
nfqws2 под другим UID. Исправления внесены; неуспешный архив сохранён рядом с успешным.
Также исправлены libcap-dev для сборки и фильтрация транзита Docker internal bridge.

## Повторение диагностик

Автоматическая приёмка по умолчанию проверяет контролируемые fixtures.
Она помечает live-критерии `NOT_RUN_BY_OFFLINE_SUITE`. Для живых проверок:

```sh
docker info
docker compose config --quiet
docker compose build
docker compose up -d
docker compose exec harness harness doctor
docker compose exec -e HARNESS_LIVE_TESTS=1 harness python -m pytest -m live -q
```

`doctor` должен подтвердить nftables, client default route через `172.31.0.2` и
приращение gateway FORWARD counter. Не считайте чтение статического Compose
доказательством пути пакетов. При несовместимом kernel проверка не превращается в PASS.

Следующие команды требуют **пустого лабораторного стенда без установленной стратегии**.
Скрипты отказывают при активном профиле или занятом operation lock. Они временно
запускают nfqws2, создают сетевые сбои, затем восстанавливают состояние. Blockcheck
smoke ограничен 120 секундами и разрешён вне ночного окна именно как диагностика;
его архив не включается в admission history.

```sh
docker compose cp tools/blockcheck_smoke.py zapret:/app/blockcheck_smoke.py
docker compose cp tools/live_lifecycle.py zapret:/app/live_lifecycle.py
docker compose cp tools/live_recheck.py zapret:/app/live_recheck.py
docker compose exec -e HARNESS_LIVE_TESTS=1 zapret python /app/blockcheck_smoke.py
docker compose exec -e HARNESS_LIVE_TESTS=1 zapret python /app/live_lifecycle.py
docker compose exec -e HARNESS_LIVE_TESTS=1 zapret python /app/live_recheck.py
```

С host, в активированном venv (PowerShell), для drift и проверки потери узлов:

```powershell
$env:HARNESS_LIVE_TESTS = '1'
python tools/live_control_check.py
Remove-Item Env:\HARNESS_LIVE_TESTS
docker compose cp zapret:/state/live/. data/reports/live
```

`live_control_check.py` останавливает только контейнеры этого Compose-проекта и
восстанавливает их в `finally`. Он проверяет rollback ещё раз с выключенным Harness.

## Blockcheck2 и полный pipeline

Настройте свои домены и ночное окно в config, затем:

```sh
docker compose exec harness harness pipeline --provider mock
docker compose exec harness harness acceptance
```

Raw `.log`, события `.events.jsonl` и metadata должны относиться к одному UUID.
Проверьте зафиксированную ревизию в выводе doctor и наличие фактических IP в facts.
Для допуска нужны повторный прогон и вторая календарная дата. По окончании окна
перебор должен завершиться даже при незаконченной сетке. Полный sweep при активном
боевом профиле отказывает; используйте `recheck --run-id <UUID исходного sweep>`.

## Выкатка и сторож (П-5…П-7, П-12)

После допуска и успешной перепроверки с обеих точек:

```sh
docker compose exec harness harness llm --run-id <UUID исходного sweep>
docker compose exec harness harness deploy --run-id <UUID перепроверки>
docker compose exec harness harness reconcile
docker compose logs zapret
docker compose exec harness harness watchdog
docker compose exec harness harness rollback
```

Сохраните pre/post snapshots `get_config`, `service_status`, deployment state и
probe results в `data/reports`. На отдельной лабораторной конфигурации предъявите:

1. Guard включает все работающие домены общей стратегии; repair — сломанные домены
   исправляемого класса. Оба списка сохраняют точки исходных замеров.
2. Одна осечка/один плохой tick не откатывает; требуемые последовательные ticks откатывают.
3. Repair deadline ещё не истёк — ожидание; истёк при устойчивом провале — rollback.
4. Успешное окно — accepted; старая строка после rollback и nfqws2 действительно работает.
5. `docker compose stop client`, watchdog: UNMEASURED, без отката из-за отсутствия client;
   затем `docker compose start client`.
6. При остановленном harness локальный watchdog продолжает писать ticks; затем
   `docker compose start harness`. Это проверка независимости отката.
7. Одновременный watchdog пропускает занятый tick. Проверка OS-lock автоматизирована
   тестом `test_overlap_rejected_then_released`; реальный журнал должен показать отсутствие overlap.
8. Перебор занят / watchdog неактивен / строка уже установлена / unsafe строка:
   операция должна отказать до изменения конфигурации.

Изменения firewall для искусственного сетевого сбоя выполняйте только в отдельном
lab и сохраняйте команды вместе с результатами. Наличие теста state machine само
по себе не закрывает требование П-5 о живой системе.

## Остальные критерии

- П-1/П-2: дважды ingest одного UUID; сравнить SQLite totals и gates; вторая дата
  подтверждается metadata, а не ручным изменением timestamps в live evidence.
- П-3: сравнить отправленные и вернувшиеся стратегии; missing перечислены явно.
- П-4: сравнить event `argv`/facts после реального blockcheck; текст `s1<d1` не должен
  становиться перенаправлением. Deployment намеренно отклоняет такие символы.
- П-8: overlap без вреда PASS, измеренный вред FAIL, отсутствие данных UNKNOWN.
  Docker lab имеет только одну routing-ветку; fixture проверяет обе ветви invariant.
- П-9: `harness llm-eval` — offline набор; `harness llm-eval --live` — отдельный
  платный Mistral contract check с synthetic summary.
- П-10: подключить внешний ReportSink, проверить получение вне lab, затем отключить
  sink и получить `REPORT_DELIVERY_FAILED`. Без внешнего sink live критерий открыт.
- П-11: `reconcile --initialize`, затем `reconcile`. Ручное изменение strategy или
  client default route должно дать DRIFT. Expected хранится снаружи Zapret.

Полная двухдатная квалификация, внешний ReportSink и платный Mistral вызов здесь
не выполнялись. П-1/П-2/П-3/П-8/П-9 имеют fixture evidence; П-10 требует внешнего
получателя. Новые live verdicts добавляйте только вместе с фактическими архивами.
