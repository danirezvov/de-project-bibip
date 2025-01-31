import os
from functools import wraps
from typing import Type, Union, List
import inflect
from pydantic import BaseModel

LINE_SIZE = 500
p = inflect.engine()


def write_tracker(func):
    """Декоратор для отслеживания изменений размера файла после записи."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        file_path = args[1] if len(args) > 1 else None
        if not file_path:
            raise ValueError("Database path is required.")

        if not os.path.isfile(file_path):
            open(file_path, "w").close()

        try:
            old_size = os.path.getsize(file_path)
            func(*args, **kwargs)
            new_size = os.path.getsize(file_path)

            if new_size == old_size:
                raise IOError("Запись не произведена")

            return new_size // LINE_SIZE
        except Exception as e:
            raise RuntimeError(
                f"Ошибка при обработке файла '{file_path}': {e}"
            )

    return wrapper


@write_tracker
def append(prepared_data: str, file_path: str) -> int:
    """Добавляет строку данных в файл."""
    with open(file_path, "a") as file:
        file.write(prepared_data)


def get_prepared_data(data: str, line_size=LINE_SIZE) -> str:
    """Подготавливает строку к записи, дополняя пробелами."""
    return f"{data.ljust(line_size - 2)}\n"


def sort_data(data: List[str]) -> List[str]:
    """Сортирует строки по первому элементу."""
    if not data:
        raise ValueError("Input data cannot be None or empty.")
    return sorted(data, key=lambda x: x.split(",")[0])


def data_to_dict(data: List[str]) -> dict:
    """Преобразует список строк в словарь."""
    if not data:
        raise ValueError("Input data cannot be None or empty.")
    return {k: v for k, v in (item.split(",") for item in data)}


class BaseService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path

    def _handle_append_result(
        self, result: int, instance: BaseModel, action="save"
    ) -> int:
        """Обрабатывает результат добавления данных в файл."""
        if result:
            print(
                f"{action.capitalize()} object [{str(instance)}] successfully."
            )
            if action == "index":
                self.refresh(instance)
            return result
        raise IOError(f"Failed to process {action} [{str(instance)}].")

    def index(self, instance: BaseModel, line_in_db: int):
        """Добавляет объект в индекс."""
        index_db_path = self._get_index_db_path(instance)
        data = get_prepared_data(f"{instance.index()},{line_in_db}")
        return self._handle_append_result(
            append(data, index_db_path), instance, action="index"
        )

    def save(self, instance: BaseModel) -> BaseModel:
        """Сохраняет объект в базу данных."""
        db_path = self._get_model_db_path(instance)
        data = get_prepared_data(str(instance))

        id = self._handle_append_result(append(data, db_path), instance)
        if self.index(instance=instance, line_in_db=id):
            return instance

    def update(
        self,
        instance_or_index: Union[BaseModel, str],
        updated_parts: dict,
        cls: Type[BaseModel],
    ) -> BaseModel:
        """Обновляет объект в базе данных."""
        instance, index = (
            (instance_or_index, instance_or_index.index())
            if isinstance(instance_or_index, BaseModel)
            else (None, instance_or_index)
        )
        num_line = self.get_num_line(index, cls)
        instance = instance or self.get_object_by_num_line(num_line, cls)

        updated_instance = instance.model_copy(update=updated_parts)
        self._overwrite_line(
            self._get_model_db_path(cls), num_line, updated_instance
        )

        if updated_instance.index() != index:
            self.update_index(index, updated_instance.index(), cls)

        return updated_instance

    def update_index(
        self, old_index: str, new_index: str, cls: Type[BaseModel]
    ) -> None:
        """Обновляет индекс объекта."""
        index_db_path = self._get_index_db_path(cls)
        with open(index_db_path, "r+") as file:
            data = data_to_dict(file.readlines())

            if old_index in data:
                data[new_index] = data.pop(old_index)

            file.seek(0)
            file.truncate()
            for k, v in data.items():
                file.write(f"{k},{v}")
            file.flush()

    def refresh(self, instance: BaseModel) -> int:
        """Пересортировывает индексный файл."""
        db_index_path = self._get_index_db_path(instance)
        try:
            with open(db_index_path, "r+") as file:
                sorted_data = sort_data(file.readlines())
                file.seek(0)
                file.writelines(sorted_data)
                file.flush()
            return len(sorted_data)
        except Exception as e:
            raise RuntimeError(
                f"Error processing file {db_index_path}: {str(e)}"
            )

    def get_num_line(self, index: str, cls: Type[BaseModel]) -> int:
        """Получает номер строки в файле по индексу."""
        index_db_path = self._get_index_db_path(cls)
        with open(index_db_path, "r") as file:
            prepared_data = data_to_dict(file.readlines())

        if index not in prepared_data:
            raise KeyError(f"{index} does not exist.")

        return int(prepared_data[index])

    def get_object_by_num_line(
        self, num_line: int, cls: Type[BaseModel]
    ) -> BaseModel:
        """Получает объект из файла по номеру строки."""
        with open(self._get_model_db_path(cls), "r") as file:
            file.seek((num_line - 1) * LINE_SIZE if num_line > 1 else 0)
            return cls.from_str(file.readline().strip())

    def get(self, index: str, cls: Type[BaseModel]) -> BaseModel:
        """Получает объект по индексу."""
        try:
            num_line = self.get_num_line(index, cls)
            instance = self.get_object_by_num_line(num_line, cls)
            return instance if not instance.is_deleted else None
        except Exception as e:
            print(e)
            return None

    def get_list(self, cls: Type[BaseModel]) -> List[BaseModel]:
        """Получает список всех объектов из файла."""
        with open(self._get_model_db_path(cls), "r") as file:
            return [cls.from_str(line.strip()) for line in file]

    def delete(self, index: str, cls: Type[BaseModel]):
        """Помечает объект как удаленный."""
        return self.update(index, {"is_deleted": True}, cls)

    def _overwrite_line(
        self, file_path: str, num_line: int, new_instance: BaseModel
    ):
        """Перезаписывает строку в файле."""
        with open(file_path, "r+") as file:
            file.seek((num_line - 1) * LINE_SIZE)
            file.write(get_prepared_data(str(new_instance)))
            file.flush()

    def _get_model_db_path(
        self, instance_or_cls: Union[BaseModel, Type[BaseModel]]
    ) -> str:
        """Возвращает путь к файлу модели."""
        cls = (
            instance_or_cls
            if isinstance(instance_or_cls, type)
            else instance_or_cls.__class__
        )
        return os.path.join(
            self.root_directory_path, f"{p.plural(cls.__name__).lower()}.txt"
        )

    def _get_index_db_path(
        self, instance_or_cls: Union[BaseModel, Type[BaseModel]]
    ) -> str:
        """Возвращает путь к файлу индексов."""
        cls = (
            instance_or_cls
            if isinstance(instance_or_cls, type)
            else instance_or_cls.__class__
        )
        return os.path.join(
            self.root_directory_path,
            f"{p.plural(cls.__name__).lower()}_index.txt",
        )
