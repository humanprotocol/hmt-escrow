import time
import logging


logger = logging.getLogger("hmt_escrow.job")


def with_retry(fn, retries=3, delay=5, backoff=2):
    """Retry a function

    Mainly used with handle_transaction to retry on case of failure.
    Uses expnential backoff.

     Args:
        fn: <Partial> to run with retry logic.
        retries: number of times to retry the transaction
        delay: time to wait (exponentially)
        backoff: defines the rate of grow for the exponential wait.

    Returns:
        False if transaction never succeeded, the return of the function
        otherwise

    Raises:
        No error

    NOTE:
        If the partial returns a Boolean and it happens to be False,
    we would not know if the tx succeeded and it will retry.
    """

    wait_time = delay

    for i in range(retries):
        try:
            result = fn()
            if result:
                return result
        except Exception as e:
            name = getattr(fn, "__name__", "partial")
            logger.warning(
                f"(x{i+1}) {name} exception: {e}. Retrying after {wait_time} sec..."
            )

        time.sleep(wait_time)
        wait_time *= backoff

    return False
