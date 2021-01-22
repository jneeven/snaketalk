import inspect


def get_defining_class(func):
    class_name = func.__qualname__.split(".")[-2]
    print(class_name)
    print(inspect.getmodule(func))
    print(func.__globals__.keys())
    return getattr(
        inspect.getmodule(func),
        class_name,
    )
