import logging


def retry(retry_n: int, _func, *args, **kwargs):

    for i in range(retry_n+1):

        try:

            return _func(*args, **kwargs)

        except Exception as e:

            if i > 0:
                logging.info("retry %d / %d", i, retry_n)
            if i < retry_n:
                continue
            else:
                raise e

        break
