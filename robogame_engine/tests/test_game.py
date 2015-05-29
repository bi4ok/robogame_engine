# -*- coding: utf-8 -*-

import math
import random
from robogame_engine import GameObject, Scene, constants
from robogame_engine.geometry import Point


class HoneyHolder:
    """Класс объекта, который может нести мёд"""
    _honey_speed = 1
    _honey = 0
    _honey_max = 0
    _honey_source = None
    _honey_state = 'hold'

    honey = property(lambda self: self._honey, doc="""Количество мёда у объекта""")

    def set_inital_honey(self, loaded, maximum):
        """Задать начальние значения: honey_loaded - сколько изначально мёда, honey_max - максимум"""
        self._honey = loaded
        if maximum == 0:
            raise Exception("honey_max can't be zero!")
        self._honey_max = maximum

    def _end_exchange(self, event):
        self._honey_source = None
        self._honey_state = 'hold'
        event()

    def _stop_loading_honey(self):
        self._honey_source = None
        self._honey_state = 'hold'

    def _update(self, is_moving=False):
        """Внутренняя функция для обновления переменных отображения"""
        if is_moving or (self._honey_source and not self.near(self._honey_source)):
            self._stop_loading_honey()
        elif self._honey_state == 'loading':
            honey = self._honey_source._get_honey()
            if not honey or not self._put_honey(honey):
                self._end_exchange(event=self.on_honey_loaded)
        elif self._honey_state == 'unloading':
            honey = self._get_honey()
            if not honey or not self._honey_source._put_honey(honey):
                self._end_exchange(event=self.on_honey_unloaded)

    def _get_honey(self):
        if self._honey > self._honey_speed:
            self._honey -= self._honey_speed
            return self._honey_speed
        elif self._honey > 0:
            value = self._honey
            self._honey = 0
            return value
        return 0.0

    def _put_honey(self, value):
        self._honey += value
        if self._honey > self._honey_max:
            self._honey = self._honey_max
            return False
        return True

    def on_honey_loaded(self):
        """Обработчик события 'мёд загружен' """
        pass

    def on_honey_unloaded(self):
        """Обработчик события 'мёд разгружен' """
        pass

    def load_honey_from(self, source):
        """Загрузить мёд от ... """
        self._honey_state = 'loading'
        self._honey_source = source

    def unload_honey_to(self, target):
        """Разгрузить мёд в ... """
        self._honey_state = 'unloading'
        self._honey_source = target

    def is_full(self):
        """полностью заполнен?"""
        return self.honey >= self._honey_max


class SceneObjectsGetter:
    _objects_holder = None
    __flowers = None
    __bees = None
    __beehives = None

    @property
    def flowers(self):
        if self.__flowers is None:
            self.__flowers = self._objects_holder.get_objects_by_type(cls=Flower)
        return self.__flowers

    @property
    def bees(self):
        if self.__bees is None:
            self.__bees = self._objects_holder.get_objects_by_type(cls=Bee)
        return self.__bees

    @property
    def beehives(self):
        if self.__beehives is None:
            self.__beehives = self._objects_holder.get_objects_by_type(cls=BeeHive)
        return self.__beehives


class Bee(GameObject, HoneyHolder, SceneObjectsGetter):
    _MAX_HONEY = 100
    sprite_filename = 'bee.jpg'  # TODO вынести в тему, по имени класса
    __my_beehive = None

    def __init__(self, pos=None):
        super(Bee, self).__init__(pos)
        self.set_inital_honey(loaded=0, maximum=self._MAX_HONEY)
        self._objects_holder = self._scene

    @property
    def my_beehive(self):
        if self.__my_beehive is None:
            self.__my_beehive = self._scene.get_objects_by_type(Flower)
        return self.__my_beehive

    def update(self):
        pass

class Flower(GameObject, HoneyHolder):
    sprite_filename = 'flower.jpg'
    _MIN_HONEY = 100
    _MAX_HONEY = 200

    def __init__(self, pos, max_honey=None):
        super(Flower, self).__init__(pos=pos)
        if max_honey is None:
            max_honey = random.randint(self._MIN_HONEY, self._MIN_HONEY)
        self.set_inital_honey(loaded=0, maximum=max_honey)

    def update(self):
        pass

class BeeHive(GameObject, HoneyHolder):
    sprite_filename = 'beehive.jpg'

    def __init__(self, pos, max_honey):
        super(BeeHive, self).__init__(pos=pos)
        self.set_inital_honey(loaded=0, maximum=max_honey)

class Rect:

    def __init__(self, x=0, y=0, w=10, h=10):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def reduce(self, dw=0, dh=0):
        self.w -= dw
        self.h -= dh

    def shift(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def __str__(self):
        return "{}x{} ({}, {})".format(self.w, self.h, self.x, self.y)


class Beegarden(Scene, SceneObjectsGetter):
    _FLOWER_JITTER = 10


    def prepare(self, speed=5, flowers_count=5, beehives_count=1):
        self._place_flowers_and_beehives(
            flowers_count=flowers_count,
            beehives_count=beehives_count,
        )
        self._set_game_speed(speed=speed)
        self._objects_holder = self

    def _place_flowers_and_beehives(self, flowers_count, beehives_count):

        flower = Rect(w=104, h=100)  # TODO получать значения из спрайтов
        beehive = Rect(w=150, h=117)
        field = Rect(w=self.field_width, h=self.field_height)
        field.reduce(dw=beehive.w, dh=beehive.h)
        if beehives_count >= 2:
            field.reduce(dw=beehive.w)
        if beehives_count >= 3:
            field.reduce(dh=beehive.h)
        if field.w < flower.w or field.h < flower.h:
            raise Exception("Too little field...")
        if constants.DEBUG:
            print "Initial field", field

        cell = Rect()
        side = math.sqrt(field.w * field.h * flower.h / float(flowers_count * flower.w))
        cell.w = int(side * flower.w / flower.h)
        cell.h = int(side)
        if constants.DEBUG:
            print "Initial cell", cell

        cells_in_width, cells_in_height, cells_count = 5, 5, 25
        while True:
            cells_in_width = int(float(field.w) / cell.w) - 1  # еще одна ячейка на джиттер
            cells_in_height = int(float(field.h) / cell.h) - 1
            cells_count = cells_in_width * cells_in_height
            if cells_count >= flowers_count or cells_in_height == 0 or cells_in_width == 0:
                break
            dw = (float(field.w) - cells_in_width * cell.w) / cells_in_width
            dh = (float(field.h) - cells_in_height * cell.h) / cells_in_height
            if dw > dh:
                cell.w -= 1
            else:
                cell.h -= 1
        if constants.DEBUG:
            print "Adjusted cell", cell, cells_in_width, cells_in_height

        cell_numbers = [i for i in range(cells_count)]

        jit_box = Rect(w=int(cell.w * self._FLOWER_JITTER), h=int(cell.h * self._FLOWER_JITTER))
        jit_box.shift(dx=(cell.w - jit_box.w) // 2, dy=(cell.h - jit_box.h) // 2)
        if constants.DEBUG:
            print "Jit box", jit_box

        field.w = cells_in_width * cell.w + jit_box.w
        field.h = cells_in_height * cell.h + jit_box.h
        if constants.DEBUG:
            print "Adjusted field", field

        beehives_w = beehive.w
        beehives_h = beehive.h
        if beehives_count >= 2:
            beehives_w = beehive.w * 2
        if beehives_count >= 3:
            beehives_h = beehive.h * 2

        field.x = beehive.w + (self.field_width - field.w - beehives_w) // 2.0 + flower.w // 3
        field.y = beehive.h + (self.field_height - field.h - beehives_h) // 2.0
        if constants.DEBUG:
            print "Shifted field", field

        max_honey = 0
        flowers = []
        while len(flowers) < flowers_count:
            cell_number = random.choice(cell_numbers)
            cell_numbers.remove(cell_number)
            cell.x = (cell_number % cells_in_width) * cell.w
            cell.y = (cell_number // cells_in_width) * cell.h
            dx = random.randint(0, jit_box.w)
            dy = random.randint(0, jit_box.h)
            pos = Point(field.x + cell.x + dx, field.y + cell.y + dy)
            flower = Flower(pos)  # автоматически добавит к списку цаетов
            flowers.append(flower)
            max_honey += flower.honey
        max_honey /= float(beehives_count)
        max_honey = int(round((max_honey / 1000.0) * 1.3)) * 1000
        if max_honey < 1000:
            max_honey = 1000
        for i in range(beehives_count):
            if i == 0:
                pos = Point(90, 75)
            elif i == 1:
                pos = Point(self.field_width - 90, 75)
            elif i == 2:
                pos = Point(90, self.field_height - 75)
            else:
                pos = Point(self.field_width - 90, self.field_height - 75)
            BeeHive(pos=pos, max_honey=max_honey)  # сам себя добавит

    @classmethod
    def get_beehive(cls, team):
        # TODO сделать автоматическое распределение ульев - внизу, по кол-ву команд
        try:
            return cls.__beehives[team - 1]
        except IndexError:
            try:
                return cls.__beehives[0]
            except IndexError:
                return None

    def _set_game_speed(self, speed):
        if speed > constants.NEAR_RADIUS:
            speed = constants.NEAR_RADIUS
        GameObject._default_speed = speed
        honey_speed = int(speed / 5.0)
        if honey_speed < 1:
            honey_speed = 1
        HoneyHolder._honey_speed = honey_speed


class WorkerBee(Bee):
    all_bees = []

    def is_other_bee_target(self, flower):
        for bee in WorkerBee.all_bees:
            if hasattr(bee, 'flower') and bee.flower and bee.flower._id == flower._id:
                return True
        return False

    def get_nearest_flower(self):
        flowers_with_honey = [flower for flower in self.flowers if flower.honey > 0]
        if not flowers_with_honey:
            return None
        nearest_flower = None
        for flower in flowers_with_honey:
            if self.is_other_bee_target(flower):
                continue
            if nearest_flower is None or self.distance_to(flower) < self.distance_to(nearest_flower):
                nearest_flower = flower
        return nearest_flower

    def go_next_flower(self):
        if self.is_full():
            self.move_at(self.my_beehive)
        else:
            self.flower = self.get_nearest_flower()
            if self.flower is not None:
                self.move_at(self.flower)
            elif self.honey > 0:
                self.move_at(self.my_beehive)
            else:
                i = random.randint(0, len(self.flowers) - 1)
                self.move_at(self.flowers[i])

    def on_born(self):
        WorkerBee.all_bees.append(self)
        self.go_next_flower()

    def on_stop_at_flower(self, flower):
        for bee in self.bees:
            if not isinstance(bee, self.__class__) and self.near(bee):
                self.sting(bee)
        else:
            if flower.honey > 0:
                self.load_honey_from(flower)
            else:
                self.go_next_flower()

    def on_honey_loaded(self):
        self.go_next_flower()

    def on_stop_at_beehive(self, beehive):
        self.unload_honey_to(beehive)

    def on_honey_unloaded(self):
        self.go_next_flower()


class GreedyBee(WorkerBee):

    def get_nearest_flower(self):
        flowers_with_honey = [flower for flower in self.flowers if flower.honey > 0]
        if not flowers_with_honey:
            return None
        nearest_flower = None
        max_honey = 0
        for flower in flowers_with_honey:
            if self.is_other_bee_target(flower):
                continue
            if flower.honey > max_honey:
                nearest_flower = flower
                max_honey = flower.honey
        if nearest_flower:
            return nearest_flower
        return random.choice(flowers_with_honey)


class NextBee(GreedyBee):
    pass


class Next2Bee(GreedyBee):
    pass


if __name__ == '__main__':
    beegarden = Beegarden(
        name="My little garden",
        beehives_count=4,
        flowers_count=50,
        speed=50,
        field=(1280, 720),
        # theme='dark',
    )

    count = 12
    bees = [WorkerBee() for i in range(count)]
    bees_2 = [GreedyBee() for i in range(count)]
    bees_3 = [NextBee() for i in range(count)]
    bees_4 = [Next2Bee() for i in range(count)]

    bee = WorkerBee()
    bee.move_at(Point(1000, 1000))  # проверка на выход за границы экрана

    beegarden.go()
