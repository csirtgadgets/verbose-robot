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

    def token_create_admin(self, token=None, groups=GROUPS):
        logger.info('testing for admin tokens...')
        if self.store.tokens.admin_exists():
            logger.info('admin token exists...')
            return

        if TOKEN:
            token = TOKEN

        logger.info('admin token does not exist, generating..')
        rv = self.store.tokens.create({
            'username': u'admin',
            'groups': groups,
            'read': u'1',
            'write': u'1',
            'admin': u'1',
            'token': token
        })
        logger.info('admin token created: {}'.format(rv['token']))
        return rv['token']

    def token_create_fm(self, token=None, groups=GROUPS):
        logger.info('testing for fm tokens...')
        if self.store.tokens.fm_exists():
            logger.info('fm token exists...')
            return

        rv = self.store.tokens.create({
            'username': u'csirtg-fm',
            'groups': groups,
            'write': u'1',
            'token': token
        })
        logger.info('fm token created: {}'.format(rv['token']))
        return rv['token']

    def token_create_hunter(self, token=None, groups=GROUPS):
        logger.info('generating hunter token')
        rv = self.store.tokens.create({
            'username': u'hunter',
            'groups': groups,
            'write': u'1',
            'token': token
        })
        logger.info('hunter token created: {}'.format(rv['token']))
        return rv['token']

    def token_create_httpd(self, token=None, groups=GROUPS):
        logger.info('generating httpd token')
        rv = self.store.tokens.create({
            'username': u'httpd',
            'groups': groups,
            'read': u'1',
            'token': token
        })
        logger.info('httpd token created: {}'.format(rv['token']))
        return rv['token']