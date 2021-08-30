import functools


def log_with_param(text):
    text = '1234' if text else '234'
    print(text, 1)

    def decorator(func, text=text):
        text = '1234' if text else '234'

        print(text, 2)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            print(text, 3)
            try:
                print('call %s():' % func.__name__)
                print('args = {}'.format(*args))
                print(text, 4)
                print('log_param = {}'.format(text))

            except Exception as ex:
                print(ex)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@log_with_param('222')
def test_with_param(p):
    print(test_with_param.__name__)


test_with_param('ppp')
