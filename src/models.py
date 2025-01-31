from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class BaseModel(BaseModel):
    """
    Базовый класс модели с общим полем `is_deleted`, которое указывает,
    удален ли объект.
    """
    is_deleted: bool = False


class CarStatus(StrEnum):
    """
    Перечисление, представляющее статус автомобиля.

    Атрибуты:
        available: Автомобиль доступен.
        reserve: Автомобиль зарезервирован.
        sold: Автомобиль продан.
        delivery: Автомобиль в процессе доставки.
    """
    available = "available"
    reserve = "reserve"
    sold = "sold"
    delivery = "delivery"

    def __str__(self):
        """
        Возвращает строковое представление значения статуса автомобиля.
        """
        return self.value


class Car(BaseModel):
    """
    Модель автомобиля с такими атрибутами, как vin, модель, цена, дата начала
    и статус.

    Атрибуты:
        vin: Уникальный идентификатор автомобиля.
        model: Идентификатор модели автомобиля.
        price: Цена автомобиля.
        date_start: Дата начала продажи автомобиля.
        status: Текущий статус автомобиля.
    """
    vin: str
    model: int
    price: Decimal
    date_start: datetime
    status: CarStatus

    def index(self) -> str:
        """
        Возвращает уникальный идентификатор автомобиля (VIN) для индексации.

        Возвращает:
            str: VIN автомобиля.
        """
        return self.vin

    def __str__(self):
        """
        Строковое представление автомобиля со всеми его атрибутами.

        Возвращает:
            str: Строка, разделенная запятыми, представляющая атрибуты автомобиля.
        """
        return (
            f"{self.vin},"
            f"{self.model},"
            f"{self.price},"
            f"{self.date_start.isoformat()},"
            f"{self.status}")

    @classmethod
    def from_str(cls, data: str) -> "Car":
        """
        Преобразует строку с разделителями запятыми в экземпляр автомобиля.

        Аргументы:
            data (str): Строка с разделителями запятыми, содержащая атрибуты
            автомобиля.

        Возвращает:
            Car: Экземпляр автомобиля, созданный из строки.

        Исключения:
            ValueError: Если строка не имеет правильного формата.
        """
        parts = data.strip().split(",")
        if len(parts) != 5:
            raise ValueError(f"Неверный формат автомобиля: {data}")
        return cls(
            vin=parts[0],
            model=parts[1],
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4]),
        )


class Model(BaseModel):
    """
    Модель автомобиля с атрибутами id, name и brand.

    Атрибуты:
        id: Уникальный идентификатор модели автомобиля.
        name: Название модели автомобиля.
        brand: Бренд модели автомобиля.
    """
    id: int
    name: str
    brand: str

    def index(self) -> str:
        """
        Возвращает уникальный идентификатор модели для индексации.

        Возвращает:
            str: ID модели автомобиля.
        """
        return str(self.id)

    def __str__(self):
        """
        Строковое представление модели автомобиля.

        Возвращает:
            str: Строка, разделенная запятыми, представляющая атрибуты модели.
        """
        return f"{self.id},{self.name},{self.brand}"

    @classmethod
    def from_str(cls, data: str) -> "Model":
        """
        Преобразует строку с разделителями запятыми в экземпляр модели автомобиля.

        Аргументы:
            data (str): Строка с разделителями запятыми, содержащая атрибуты
            модели.

        Возвращает:
            Model: Экземпляр модели, созданный из строки.

        Исключения:
            ValueError: Если строка не имеет правильного формата.
        """
        parts = data.strip().split(",")
        if len(parts) != 3:
            raise ValueError("Неверный формат модели")
        return cls(id=int(parts[0]), name=parts[1], brand=parts[2])


class Sale(BaseModel):
    """
    Модель продажи автомобиля с атрибутами, такими как номер продажи, VIN
    автомобиля, дата продажи и стоимость.

    Атрибуты:
        sales_number: Номер продажи.
        car_vin: VIN автомобиля, который был продан.
        sales_date: Дата продажи.
        cost: Стоимость автомобиля при продаже.
    """
    sales_number: str
    car_vin: str
    sales_date: datetime
    cost: Decimal

    def index(self) -> str:
        """
        Возвращает VIN автомобиля для индексации.

        Возвращает:
            str: VIN автомобиля.
        """
        return self.car_vin

    def __str__(self):
        """
        Строковое представление продажи с атрибутами.

        Возвращает:
            str: Строка, разделенная запятыми, представляющая атрибуты продажи.
        """
        return (
            f"{self.sales_number},{self.car_vin},{self.sales_date},{self.cost}"
        )

    @classmethod
    def from_str(cls, data: str) -> "Sale":
        """
        Преобразует строку с разделителями запятыми в экземпляр продажи.

        Аргументы:
            data (str): Строка с разделителями запятыми, содержащая атрибуты
            продажи.

        Возвращает:
            Sale: Экземпляр продажи, созданный из строки.

        Исключения:
            ValueError: Если строка не имеет правильного формата.
        """
        parts = data.strip().split(",")
        if len(parts) != 4:
            raise ValueError("Неверный формат продажи")
        return cls(
            sales_number=parts[0],
            car_vin=parts[1],
            sales_date=datetime.fromisoformat(parts[2]),
            cost=Decimal(parts[3]),
        )


class CarFullInfo(BaseModel):
    """
    Полная информация об автомобиле, включая данные о модели, статусе, цене,
    дате начала продажи и стоимости продажи.

    Атрибуты:
        vin: Уникальный идентификатор автомобиля.
        car_model_name: Название модели автомобиля.
        car_model_brand: Бренд модели автомобиля.
        price: Цена автомобиля.
        date_start: Дата начала продажи.
        status: Статус автомобиля.
        sales_date: Дата продажи автомобиля (если была).
        sales_cost: Стоимость продажи автомобиля (если была).
    """
    vin: str
    car_model_name: str
    car_model_brand: str
    price: Decimal
    date_start: datetime
    status: CarStatus
    sales_date: datetime | None
    sales_cost: Decimal | None

    @classmethod
    def from_join(cls, car: Car, model: Model, sale: Sale) -> "CarFullInfo":
        """
        Создает объект полной информации о автомобиле, объединяя данные из
        автомобиля, модели и продажи.

        Аргументы:
            car (Car): Экземпляр автомобиля.
            model (Model): Экземпляр модели автомобиля.
            sale (Sale): Экземпляр продажи.

        Возвращает:
            CarFullInfo: Объект с полной информацией о автомобиле.
        """
        if None in (car, model):
            return None
        return cls(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sale.sales_date if sale else None,
            sales_cost=sale.cost if sale else None,
        )


class ModelSaleStats(BaseModel):
    """
    Статистика продаж по модели автомобиля.

    Атрибуты:
        car_model_name: Название модели автомобиля.
        brand: Бренд модели автомобиля.
        sales_number: Количество продаж данной модели.
    """
    car_model_name: str
    brand: str
    sales_number: int

    @classmethod
    def from_str(cls, data: str) -> "ModelSaleStats":
        """
        Преобразует строку с разделителями запятыми в экземпляр статистики
        продаж модели.

        Аргументы:
            data (str): Строка с разделителями запятыми, содержащая статистику
            продаж.

        Возвращает:
            ModelSaleStats: Экземпляр статистики продаж модели.
        """
        parts = data.strip().split(",")
        if len(parts) != 3:
            raise ValueError("Неверный формат статистики продаж")
        return cls(
            car_model_name=parts[0], brand=parts[1], sales_number=int(parts[2])
        )
