import functools
import time

from openstack import connection as os_conn

from pasted import app


def retry(ExceptionToCheck, tries=3, delay=1, backoff=1):
    """Retry calling the decorated function using an exponential backoff.

    :param ExceptionToCheck: the exception to check. may be a tuple of
                             exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the
                    delay each retry
    :type backoff: int
    """
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


class OpenStack(object):
    """Class for reusable OpenStack utility methods."""

    def __init__(self):
        """Initialization method for class.
        :param os_auth_args: dict containing auth creds.
        :type os_auth_args: dict
        """
        self.os_auth_args = {
            'username': app.config['OS_USERNAME'],
            'password': app.config['OS_PASSWORD'],
            'tenant_name': app.config['OS_TENANT_NAME'],
            'user_domain_name': app.config['OS_USER_DOMAIN_NAME'],
            'project_name': app.config['OS_PROJECT_NAME'],
            'project_domain_name': app.config['OS_PROJECT_DOMAIN_NAME'],
            'auth_url': app.config['OS_AUTH_URL'],
            'region_name': app.config['OS_REGION_NAME'],
            'insecure': app.config['OS_INSECURE'],
            'interface': app.config['OS_INTERFACE']
        }
        self.verify = self.os_auth_args['insecure'] is False
        self.os_auth_args = {
            k: v for k, v in self.os_auth_args.items() if v is not None
        }

    @property
    def conn(self):
        """Return an OpenStackSDK connection.

        :returns: object
        """
        return os_conn.Connection(verify=self.verify, **self.os_auth_args)

    def object_upload(self, key, content):
        """Upload content to a container and return its object.

        :param key: File object name.
        :type key: str
        :param content: File content.
        :type content: str
        :returns: object
        """
        return self.conn.object_store.upload_object(
            container=app.config['CDN_CONTAINER_NAME'],
            name=key,
            data=content
        )


@retry(ExceptionToCheck=Exception)
def upload(key, content):
    """Upload content to a CDN provider."""
    if app.config['CDN_PROVIDER'] == 'openstack':
        cdn_provider = OpenStack()
        return cdn_provider.object_upload(key=key,
                                          content=content).etag
