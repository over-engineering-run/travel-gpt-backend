import sentry_sdk


def init_sentry(dsn: str):

    """
    To configure the SDK, initialize it with the integration
    before or after your app has been initialized.

    Set traces_sample_rate to 1.0 to capture 100%
    of transactions for performance monitoring.
    We recommend adjusting this value in production.
    """

    # sentry
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.5
    )
