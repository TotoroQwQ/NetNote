import functools

def log_with_param(text='param'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                print('call %s():' % func.__name__)
                print('args = {}'.format(*args))
                if text is None:
                    text= '111'
                print('log_param = {}'.format(text))
            except Exception as ex:
                print(ex)
            return func(*args, **kwargs)

        return wrapper

    return decorator
    
@log_with_param('222')
def test_with_param(p):
    print(test_with_param.__name__)

test_with_param('1234')