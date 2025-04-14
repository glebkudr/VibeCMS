# Project Rules and Gotchas

## MongoDB motor: Проверка подключения

**Нельзя** использовать:
```python
if not db:
    # ...
```

**Нужно** использовать:
```python
if db is None:
    # ...
```

**Причина:**
Motor (и pymongo) Database объекты не поддерживают bool(), и попытка сделать 'if not db' вызовет ошибку:
```
NotImplementedError: Database objects do not implement truth value testing or bool(). Please compare with None instead: database is not None
```

**См. пример в admin_app/routes/admin_ui.py** 