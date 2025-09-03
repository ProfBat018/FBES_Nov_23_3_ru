# Тема урока: 
- Tuples 
- Sets
- Dictionaries
- Closures
- Decorators
- Generators

## Tuple 

`Tuple` - это неизменяемый (immutable) упорядоченный набор элементов. 
Они похожи на списки, но не могут быть изменены после создания.

они используются если вы передаете `*args` в функцию или же возвращаете сразу несколько значений из функции.

```python

def example_function():
    return 1, 2, 3  # Возвращаем кортеж из трех элементов
```

## Set

`Set` - это неупорядоченная коллекция уникальных элементов. Они полезны для удаления дубликатов из списка или для выполнения операций над множествами, 
таких как объединение, пересечение и разность. По факту - это и есть математическое множество.

В программе он может вам понадобиться, когда нужно быстро проверить наличие элемента в коллекции. 
В реальных задачах это может быть полезно, например,
для хранения уникальных идентификаторов пользователей или уникальных слов в тексте.

```python
my_set = {1, 2, 3, 4, 5}
my_set2 = {1, 2, 3, 6, 7, 8}

# объединение, пересечение и разность множеств. Разница между update методами и обычными. 
union_set = my_set | my_set2  # {1, 2, 3, 4, 5, 6, 7, 8} ## или my_set.union(my_set2)
intersection_set = my_set & my_set2  # {1, 2, 3}
difference_set = my_set - my_set2  # {4, 5}
symmetric_difference_set = my_set ^ my_set2  # {4, 5, 6, 7, 8}

my_set.difference_update(my_set2) # my_set теперь {4, 5}

```

## Dictionary 

`Dictionary` - это неупорядоченная коллекция пар "ключ-значение". 
Они позволяют быстро получать доступ к значениям по ключам.

```python

my_dict = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

```

## Closures

`Closure` - или как мы их еще называем замыкания - это функция, которая может возвращать другую функцию,
которая запоминает окружение, в котором была создана. Да, это звучит сложно, но на самом деле это очень мощный инструмент.

```python
def outer_function(msg):
    def inner_function():
        print(msg)
    return inner_function

my_closure = outer_function("Hello, World!")
my_closure()  # Выведет: Hello, World!
```

Самый главный плюс замыканий - это возможность сохранять состояние между вызовами функции. 

Студенты часто не понимают, где это может пригодиться. Например, везде где нужно сохранять состояние: 

```bash
>>> def cumulative_average():
...     data = []
...     def average(value):
...         data.append(value)
...         return sum(data) / len(data)
...     return average
...

>>> stream_average = cumulative_average()

>>> stream_average(12)
12.0
>>> stream_average(13)
12.5
>>> stream_average(11)
12.0
>>> stream_average(10)
11.5
```

# Decorators 
`Decorator` - если, сравнивать с C#, то это что-то вроде атрибутов. 
Это функция, которая принимает другую функцию и расширяет ее функциональность без изменения ее кода.
Вот пример с декоратором для логирования, который например можно использовать в Django или Flask:


```python
def log_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Вызов функции {func.__name__} с аргументами {args} и {kwargs}")
        result = func(*args, **kwargs)
        print(f"Функция {func.__name__} вернула {result}")
        return result
    return wrapper

@log_decorator
def add(a, b):
    return a + b


add(3, 5)
```

Вот список полезных декораторов в стандартной библиотеке Python:
- `@functools.lru_cache`: Кэширует результаты функции для ускорения повторных вызовов с одинаковыми аргументами.
- `@functools.wraps`: Сохраняет метаданные оригинальной функции при создании декоратора.
- `@property`: Превращает метод класса в атрибут, позволяя использовать его как свойство.
- `@staticmethod`: Определяет статический метод в классе, который не зависит от экземпляра класса.
- `@classmethod`: Определяет метод класса, который получает класс в качестве первого аргумента вместо экземпляра.


# Generators
`Generator` - это специальный тип итератора,
который позволяет вам итерироваться по данным без необходимости 
загружать все данные в память сразу.

```python
def count_up_to(max):
    count = 1
    while count <= max:
        yield count
        count += 1

counter = count_up_to(5)

print(counter)

for number in counter:
    print(number)


```





