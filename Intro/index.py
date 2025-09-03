# def log_decorator(func):
#     def wrapper(*args, **kwargs):
#         print(f"Вызов функции {func.__name__} с аргументами {args} и {kwargs}")
#         result = func(*args, **kwargs)
#         print(f"Функция {func.__name__} вернула {result}")
#         return result
#     return wrapper
#
# @log_decorator
# def add(a, b, **kwargs):
#     return a + b
#
#
# add(3, 5, test="example")
#
# print("Hello", "world!", sep=", ", end="")
# print("This is a test.")
#
#


# def count_up_to(max):
#     count = 1
#     while count <= max:
#         yield count
#         count += 1
#
# counter = count_up_to(5)
#
# print(counter)
#
# for number in counter:
#     print(number)


nums = [1, 2, 3, 4, 5]

nums.__iter__()

iterator = iter(nums)

for num in iterator:
    print(num)
