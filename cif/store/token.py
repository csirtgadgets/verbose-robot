import logging

from cifsdk.exceptions import AuthError
from cifsdk.constants import TOKEN

GROUPS = ['everyone']

logger = logging.getLogger('cif.store')


class TokenHandler(object):
    def __init__(self, store):
        self.store = store

    def handle_tokens_search(self, token, data, **kwargs):
        if self.store.tokens.admin(token):
            return self.store.tokens.search(data)

        raise AuthError('invalid token')

    def handle_tokens_create(self, token, data, **kwargs):
        if self.store.tokens.admin(token):
            return self.store.tokens.create(data)

        raise AuthError('invalid token')

    def handle_tokens_delete(self, token, data, **kwargs):
        if self.store.tokens.admin(token):
            return self.store.tokens.delete(data)

        raise AuthError('invalid token')

    def handle_token_write(self, token, **kwargs):
        return self.store.tokens.write(token)

    def handle_tokens_edit(self, token, data, **kwargs):
        if self.store.tokens.admin(token):
            return self.store.tokens.edit(data)

        raise AuthError('invalid token')

    def _token_create(self, d):
        logger.info('generating token for: %s' % d['username'])
        rv = self.store.tokens.create(d)
        logger.info('token created for %s: %s' % (d['username'], rv['token']))
        return rv['token']

    def token_create_admin(self, token=TOKEN, groups=GROUPS):
        if self.store.tokens.admin_exists():
            logger.info('admin token exists...')
            return

        return self._token_create({
            'username': u'admin',
            'groups': groups,
            'read': u'1',
            'write': u'1',
            'admin': u'1',
            'token': token
        })

    def token_create_smrt(self, token=None, groups=GROUPS):
        if self.store.tokens.smrt_exists():
            logger.info('smrt token exists...')
            return

        return self._token_create({
            'username': u'csirtg-smrt',
            'groups': groups,
            'write': u'1',
            'token': token
        })

    def token_create_hunter(self, token=None, groups=GROUPS):
        return self._tokens_create({
            'username': u'hunter',
            'groups': groups,
            'write': u'1',
            'token': token
        })

    def token_create_httpd(self, token=None, groups=GROUPS):
        return self._token_create({
            'username': u'httpd',
            'groups': groups,
            'read': u'1',
            'token': token
        })
