from collections import Counter

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from utils import BaseService


class CarService(BaseService):
    def __init__(self, root_directory_path: str) -> None:
        super().__init__(root_directory_path)

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        return self.save(model)

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        return self.save(car)

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        self.save(sale)
        return self.update(sale.car_vin, {"status": CarStatus.sold}, Car)

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        return [car for car in self.get_list(Car) if car.status == status]

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car = self.get(vin, Car)
        if not car:
            return None

        model = self.get(str(car.model), Model) if car else None
        if not model:
            return None

        sale = self.get(vin, Sale) if car else None
        return CarFullInfo.from_join(car, model, sale)

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        return self.update(vin, {"vin": new_vin}, Car)

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car | None:
        vin = sales_number.split("#")[1]
        sale = self.get(vin, Sale)
        if not sale:
            return None

        if self.delete(vin, Sale):
            car = self.update(
                sale.car_vin, {"status": CarStatus.available}, Car
            )
            return car
        return None

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales = self.get_list(Sale)
        model_sales_counter = Counter()

        for sale in sales:
            car = self.get(str(sale.car_vin), Car)
            model_sales_counter[car.model] += 1

        top_models = model_sales_counter.most_common(3)
        top_model_stats = [
            ModelSaleStats(
                car_model_name=self.get(str(model_id), Model).name,
                brand=self.get(str(model_id), Model).brand,
                sales_number=sales_number,
            )
            for model_id, sales_number in top_models
        ]

        return top_model_stats
