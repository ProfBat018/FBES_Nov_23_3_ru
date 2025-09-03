#region Example 1
from xmlrpc.client import DateTime


# class Car:
#     def display(self):
#         print(f"This is a {self.name}")
#
#
# c1 = Car()
#
# # c1.display()
# c1.name = "Toyota"
# c1.display()
#
#

#endregion

#region Example 2

# class Car:
#     def __init__(self, make, model, year):
#         self.make = make
#         self.model = model
#         self.year = year
#         self.price = 0
#
#     def __str__(self):
#         return f"{self.year} {self.make} {self.model} - ${self.price}"
#
#     def display(self, owners=None):
#         if owners:
#             owners_list = ', '.join(owners)
#             print(f"{self.year} {self.make} {self.model} - ${self.price} (Owners: {owners_list})")
#         else:
#             print(f"{self.year} {self.make} {self.model} - ${self.price}")
#
#
# c1 = Car("Toyota", "Camry", 2020)
# print(c1)

#endregion

#region Example 3
#
# import datetime
#
# class Car:
#     def __init__(self, make, model, year=datetime.datetime.year, color="Black"):
#         self.__make = make
#         self.__model = model
#         self.__year = year
#         self.color = color
#     def __str__(self):
#         return f"{self.__year} {self.__make} {self.__model} - {self.color}"
#
#
# c1 = Car("Mercedes", "E300", 2008)
#
# print(c1)
#
# c1._Car__year = 2010
# c1._Car__make = "Benz"

#region Example 4
#
# class Transport:
#     def __init__(self, make, model, year):
#         self._make = make
#         self._model = model
#         self._year = year
#
#
# class Car(Transport):
#     def __init__(self, make, model, year, price):
#         super().__init__(make, model, year) # делегирование конструктора
#         self.price = price
#
#     def display(self):
#         print(f"{self._year} {self._make} {self._model} - ${self.price}")
#
#
# c1 = Car("Fisker", "Karma", "2012", 120000)
#
# c1.display()
#
# c1._make = "Test"
#
# c1.display()
#

#endregion

#region Example 5
#
# class Car:
#     @property
#     def make(self):
#         return self.__make
#
#     @make.setter
#     def make(self, value):
#         self.__make = value
#
#     @property
#     def model(self):
#         return self.__model
#
#     @model.setter
#     def model(self, value):
#         self.__model = value
#
#     def __str__(self):
#         return f"{self.__make} {self.__model}"
#
#
# c1 = Car()
#
# c1.make = "Toyota"
# c1.model = "Camry"
#
# print(c1)
# endregion

#region Example 6

# class Car:
#     def __init__(self, make, model, year):
#         self.__make = make
#         self.__model = model
#         self.__year = year
#
#     @property
#     def year(self):
#         return self.__year
#
#     @year.setter
#     def year(self, value):
#         if value < 1886:  # The first car was invented in 1886
#             raise ValueError("Year cannot be less than 1886")
#         self.__year = value
#
#     def __str__(self):
#         return f"{self.__year} {self.__make} {self.__model}"

#endregion

#region Example 7

# from abc import ABC, abstractmethod
#
# class Animal(ABC):
#     @abstractmethod
#     def make_sound(self):
#         pass
#
# class Dog(Animal):
#     def make_sound(self):
#         return "Woof!"
#
# dog = Dog()
#
# anim = Animal()
#
# anim.make_sound()

#endregion


#region Example 8

class Bird:
    def fly(self):
        return "Flying"

class Airplane:
    def fly(self):
        return "Flying"

def make_it_fly(flyable):
    return flyable.fly()

bird = Bird()
plane = Airplane()
print(make_it_fly(bird))  # Output: Flying
print(make_it_fly(plane))  # Output: Flying

if (make_it_fly(bird) and make_it_fly(plane)):
    print("Both can fly")


#endregion