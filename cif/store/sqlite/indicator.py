import os
import arrow
import json
from base64 import b64decode, b64encode
import ipaddress
import re
import logging
import time
from pprint import pprint

from sqlalchemy import Column, Integer, String, Float, DateTime, UnicodeText, desc, ForeignKey, or_, Index
from sqlalchemy.orm import relationship, backref, class_mapper, lazyload
from sqlalchemy.ext.declarative import declarative_base

import networkx as nx
from networkx.readwrite import json_graph

from csirtg_indicator import resolve_itype
from cifsdk.exceptions import InvalidSearch
from cifsdk.constants import VALID_FILTERS, DATA_PATH, PYVERSION
from cif.store.plugin.indicator import IndicatorManagerPlugin

from .ip import Ip
from .fqdn import Fqdn
from .url import Url
from .hash import Hash


if PYVERSION > 2:
    basestring = (str, bytes)

REQUIRED_FIELDS = ['provider', 'indicator', 'tags', 'group', 'itype']
HASH_TYPES = ['sha1', 'sha256', 'sha512', 'md5']

GRAPH_PATH = os.getenv('CIF_STORE_GRAPH_PATH', 'cifv4.gpickle')
GRAPH_GEXF_PATH = os.getenv('CIF_STORE_GRAPH_GEXF_PATH', 'cifv4.gexf')

Base = declarative_base()

logger = logging.getLogger('cif.store.sqlite')


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, index=True)
    indicator = Column(UnicodeText, index=True)
    group = Column(String)
    itype = Column(String, index=True)
    tlp = Column(String)
    provider = Column(String, index=True)
    portlist = Column(String)
    asn_desc = Column(UnicodeText, index=True)
    asn = Column(Float)
    cc = Column(String, index=True)
    protocol = Column(Integer)
    reported_at = Column(DateTime, index=True)
    first_at = Column(DateTime)
    last_at = Column(DateTime, index=True)
    confidence = Column(Float, index=True)
    probability = Column(Float, index=True)
    timezone = Column(String)
    city = Column(String)
    longitude = Column(String)
    latitude = Column(String)
    peers = Column(UnicodeText)
    description = Column(UnicodeText)
    additional_data = Column(UnicodeText)
    rdata = Column(UnicodeText, index=True)
    count = Column(Integer)
    region = Column(String, index=True)
    related = Column(String, index=True)

    tags = relationship(
        'Tag',
        primaryjoin='and_(Indicator.id==Tag.indicator_id)',
        backref=backref('tags', uselist=True),
        lazy='subquery',
        cascade="all,delete"
    )

    messages = relationship(
        'Message',
        primaryjoin='and_(Indicator.id==Message.indicator_id)',
        backref=backref('messages', uselist=True),
        lazy='subquery',
        cascade="all,delete"
    )

    def __init__(self, **kwargs):

        self.uuid = kwargs.get('uuid')
        self.indicator = kwargs.get('indicator')
        self.group = kwargs.get('group', 'everyone')
        self.itype = kwargs.get('itype')
        self.tlp = kwargs.get('tlp')
        self.provider = kwargs.get('provider')
        self.portlist = str(kwargs.get('portlist', None))
        self.asn = kwargs.get('asn')
        self.asn_desc = kwargs.get('asn_desc')
        self.cc = kwargs.get('cc')
        self.protocol = kwargs.get('protocol')
        self.reported_at = kwargs.get('reported_at')
        self.first_at = kwargs.get('first_at')
        self.last_at = kwargs.get('last_at')
        self.confidence = kwargs.get('confidence')
        self.probability = kwargs.get('probability')
        self.reference = kwargs.get('reference')
        self.reference_tlp = kwargs.get('reference_tlp')
        self.timezone = kwargs.get('timezone')
        self.city = kwargs.get('city')
        self.longitude = kwargs.get('longitude')
        self.latitude = kwargs.get('latitude')
        self.peers = kwargs.get('peers')
        self.description = kwargs.get('description')
        self.additional_data = kwargs.get('additional_data')
        self.rdata = kwargs.get('rdata')
        self.rdata_type = kwargs.get('rdata_type')
        self.count = kwargs.get('count')
        self.region = kwargs.get('region')
        self.related = kwargs.get('related')

        if self.reported_at and isinstance(self.reported_at, basestring):
            self.reported_at = arrow.get(self.reported_at).datetime

        if self.last_at and isinstance(self.last_at, basestring):
            self.last_at = arrow.get(self.last_at).datetime

        if self.first_at and isinstance(self.first_at, basestring):
            self.first_at = arrow.get(self.first_at).datetime

        if self.peers is not None:
            self.peers = json.dumps(self.peers)

        if self.additional_data is not None:
            self.additional_data = json.dumps(self.additional_data)


class Ipv4(Base):
    __tablename__ = 'indicators_ipv4'

    id = Column(Integer, primary_key=True)
    ipv4 = Column(Ip, index=True)
    mask = Column(Integer, default=32)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class Ipv6(Base):
    __tablename__ = 'indicators_ipv6'

    id = Column(Integer, primary_key=True)
    ip = Column(Ip(version=6), index=True)
    mask = Column(Integer, default=64)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class Fqdn(Base):
    __tablename__ = 'indicators_fqdn'

    id = Column(Integer, primary_key=True)
    fqdn = Column(Fqdn, index=True)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class Url(Base):
    __tablename__ = 'indicators_url'

    id = Column(Integer, primary_key=True)
    url = Column(Url, index=True)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class Hash(Base):
    __tablename__ = 'indicators_hash'

    id = Column(Integer, primary_key=True)
    hash = Column(Hash, index=True)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    tag = Column(String, index=True)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )

    __table_args__ = (Index('ix_tags_indicator', "tag", "indicator_id"),)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    message = Column(UnicodeText)

    indicator_id = Column(Integer, ForeignKey('indicators.id', ondelete='CASCADE'))
    indicator = relationship(
        Indicator,
    )


class IndicatorManager(IndicatorManagerPlugin):

    def __init__(self, handle, engine, **kwargs):
        super(IndicatorManager, self).__init__(**kwargs)

        self.handle = handle
        Base.metadata.create_all(engine)

        self.graph = nx.Graph()

        if os.path.exists(GRAPH_PATH):
            self.graph = nx.read_gpickle(GRAPH_PATH)


    def to_dict(self, obj):
        d = {}
        for col in class_mapper(obj.__class__).mapped_table.c:
            a = getattr(obj, col.name)
            if a is None or a == 'None' or a == '':
                continue

            d[col.name] = a
            if d[col.name] and (col.name.endswith('time') or col.name.endswith('_at')):
                d[col.name] = getattr(obj, col.name).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        try:
            d['tags'] = [t.tag for t in obj.tags]
        except AttributeError:
            pass

        try:
            d['message'] = [b64encode(m.message) for m in obj.messages]
        except AttributeError:
            pass

        return d

    def is_valid_indicator(self, i):
        if isinstance(i, Indicator):
            i = i.__dict__()

        for f in REQUIRED_FIELDS:
            if not i.get(f):
                raise ValueError("Missing required field: {} for \n{}".format(f, i))

    def create(self, token, data):
        return self.upsert(token, data)

    def _filter_indicator(self, filters, s):

        for k, v in list(filters.items()):
            if k not in VALID_FILTERS:
                del filters[k]

        if not filters.get('indicator'):
            return s

        i = filters.pop('indicator')
        if PYVERSION == 2:
            if isinstance(i, str):
                i = unicode(i)

        try:
            itype = resolve_itype(i)
        except TypeError as e:
            logger.error(e)
            s = s.join(Message).filter(Indicator.Message.like('%{}%'.format(i)))
            return s

        if itype in ['email']:
            s = s.filter(Indicator.indicator == i)
            return s

        if itype == 'ipv4':
            ip = ipaddress.IPv4Network(i)
            mask = ip.prefixlen

            if mask < 8:
                raise InvalidSearch('prefix needs to be >= 8')

            start = str(ip.network_address)
            end = str(ip.broadcast_address)

            logger.debug('{} - {}'.format(start, end))

            s = s.join(Ipv4).filter(Ipv4.ipv4 >= start)
            s = s.filter(Ipv4.ipv4 <= end)

            return s

        if itype == 'ipv6':
            ip = ipaddress.IPv6Network(i)
            mask = ip.prefixlen

            if mask < 32:
                raise InvalidSearch('prefix needs to be >= 32')

            start = str(ip.network_address)
            end = str(ip.broadcast_address)

            logger.debug('{} - {}'.format(start, end))

            s = s.join(Ipv6).filter(Ipv6.ip >= start)
            s = s.filter(Ipv6.ip <= end)
            return s

        if itype == 'fqdn':
            s = s.join(Fqdn).filter(or_(
                    Fqdn.fqdn.like('%.{}'.format(i)),
                    Fqdn.fqdn == i)
            )
            return s

        if itype == 'url':
            s = s.join(Url).filter(Url.url == i)
            return s

        if itype in HASH_TYPES:
            s = s.join(Hash).filter(Hash.hash == str(i))
            return s

        raise ValueError

    def _filter_terms(self, filters, s):

        for k, v in filters.items():
            if k in ['nolog', 'days', 'hours', 'groups', 'limit', 'feed']:
                continue

            if k == 'reported_at':
                if ',' in v:
                    start, end = v.split(',')
                    s = s.filter(Indicator.reported_at >= arrow.get(start).datetime)
                    s = s.filter(Indicator.reported_at <= arrow.get(end).datetime)
                else:
                    s = s.filter(Indicator.reported_at >= arrow.get(v).datetime)

            elif k == 'tags':
                t = v.split(',')
                s = s.outerjoin(Tag)
                s = s.filter(or_(Tag.tag == tt for tt in t))

            elif k == 'confidence':
                if ',' in str(v):
                    start, end = str(v).split(',')
                    s = s.filter(Indicator.confidence >= float(start))
                    s = s.filter(Indicator.confidence <= float(end))
                else:
                    s = s.filter(Indicator.confidence >= float(v))

            elif k == 'probability':
                if ',' in str(v):
                    start, end = str(v).split(',')
                    if start == 0:
                        s = s.filter(or_(Indicator.probability >= float(start), Indicator.probability == None))
                        s = s.filter(Indicator.probability <= float(end))
                    else:
                        s = s.filter(Indicator.probability >= float(start))
                        s = s.filter(Indicator.probability <= float(end))
                else:
                    if float(v) == 0:
                        s = s.filter(or_(Indicator.probability == None, Indicator.probability >= float(v)))
                    else:
                        s = s.filter(Indicator.probability >= float(v))

            elif k == 'itype':
                s = s.filter(Indicator.itype == v)

            elif k == 'provider':
                s = s.filter(Indicator.provider == v)

            elif k == 'asn':
                s = s.filter(Indicator.asn == v)

            elif k == 'asn_desc':
                s = s.filter(Indicator.asn_desc.like('%{}%'.format(v)))

            elif k == 'cc':
                s = s.filter(Indicator.cc == v)

            elif k == 'rdata':
                s = s.filter(Indicator.rdata == v)

            elif k == 'region':
                s = s.filter(Indicator.region == v)

            elif k == 'related':
                s = s.filter(Indicator.related == v)

            elif k == 'uuid':
                s = s.filter(Indicator.uuid == v)

            else:
                raise InvalidSearch('invalid filter: %s' % k)

        return s

    def _filter_groups(self, filters, token, s):
        if token:
            groups = token.get('groups', 'everyone')
        else:
            groups = filters.get('groups')

        if isinstance(groups, str):
            groups = [groups]

        s = s.filter(or_(Indicator.group == g for g in groups))
        return s

    def _search(self, filters, token):
        myfilters = dict(filters.items())

        s = self.handle().query(Indicator)

        # group support

        s = self._filter_indicator(myfilters, s)
        s = self._filter_terms(myfilters, s)

        if myfilters.get('groups'):
            return self._filter_groups(myfilters, None, s)

        return self._filter_groups({}, token, s)

    def _cleanup_timestamps(self, i):
        if not i.get('last_at'):
            i['last_at'] = arrow.utcnow().datetime.replace(tzinfo=None)

        if not i.get('reported_at'):
            i['reported_at'] = arrow.utcnow().datetime.replace(tzinfo=None)

        if PYVERSION == 2:
            i['last_at'] = arrow.get(i['last_at']).datetime.replace(tzinfo=None)
            i['reported_at'] = arrow.get(i['reported_at']).datetime.replace(tzinfo=None)

        if not i.get('first_at'):
            i['first_at'] = i['last_at']

    def search(self, token, filters, limit=500):
        s = self._search(filters, token)

        limit = filters.pop('limit', limit)

        rv = s.order_by(desc(Indicator.reported_at)).limit(limit)

        return [self.to_dict(i) for i in rv]

    def delete(self, token, data=None):
        if type(data) is not list:
            data = [data]

        ids = []
        for d in data:
            if d.get('id'):
                ids.append(Indicator.id == d['id'])
            else:
                ids.append(Indicator.id == i.id for i in self._search(d, token))

        if len(ids) == 0:
            return 0

        s = self.handle().query(Indicator).filter(or_(*ids))
        rv = s.delete()
        self.handle().commit()

        return rv

    def _upsert_itype(self, s, i):
        if i.itype == 'ipv4':
            match = re.search('^(\S+)\/(\d+)$', i.indicator)  # TODO -- use ipaddress
            if match:
                ipv4 = Ipv4(ipv4=match.group(1), mask=match.group(2), indicator=i)
            else:
                ipv4 = Ipv4(ipv4=i.indicator, indicator=i)

            s.add(ipv4)

        elif i.itype == 'ipv6':
            match = re.search('^(\S+)\/(\d+)$', i.itype)  # TODO -- use ipaddress
            if match:
                ip = Ipv6(ip=match.group(1), mask=match.group(2), indicator=i)
            else:
                ip = Ipv6(ip=i.indicator, indicator=i)

            s.add(ip)

        elif i.itype == 'fqdn':
            fqdn = Fqdn(fqdn=i.indicator, indicator=i)
            s.add(fqdn)

        elif i.itype == 'url':
            url = Url(url=i.indicator, indicator=i)
            s.add(url)

        elif i.itype == HASH_TYPES:
            h = Hash(hash=i.indicator, indicator=i)
            s.add(h)

        return s

    def _insert_graph(self, i):
        g = self.graph

        g.add_node(i['indicator'], itype=i['itype'])
        for t in i.get('tags'):
            g.add_node(t)
            g.add_edge(i['indicator'], t)

        pprint(i)

        reported_at = arrow.get(i['reported_at'])
        reported_at = '{}'.format(reported_at.format('YYYY-MM-DD'))
        g.add_node(reported_at)
        g.add_edge(i['indicator'], reported_at)

        for a in ['asn', 'asn_desc', 'cc', 'timezone', 'region', 'city']:
            if not i.get(a):
                continue

            g.add_node(i[a])
            g.add_edge(i['indicator'], i[a])

        if i.get('peers'):
            for p in i['peers']:
                for a in ['asn', 'cc', 'prefix']:
                    g.add_node(p[a])
                    g.add_edge(i['indicator'], p[a])

    def search_graph(self, token, data, **kwargs):
        rv = json_graph.node_link_data(self.graph)

        return rv

    def upsert(self, token, data, **kwargs):
        if type(data) == dict:
            data = [data]

        s = self.handle()

        n = 0
        cached_added = {}

        for d in data:

            tags = d.get("tags", [])

            self._insert_graph(d)

            if len(tags) > 0:
                if isinstance(tags, basestring):
                    tags = tags.split(',')

                del d['tags']

            i = s.query(Indicator).options(lazyload('*')).filter_by(
                provider=d['provider'],
                itype=d['itype'],
                indicator=d['indicator'],
            ).order_by(Indicator.last_at.desc())

            if d.get('rdata'):
                i = i.filter_by(rdata=d['rdata'])

            if d['itype'] == 'ipv4':
                match = re.search('^(\S+)\/(\d+)$', d['indicator'])  # TODO -- use ipaddress
                if match:
                    i = i.join(Ipv4).filter(Ipv4.ipv4 == match.group(1), Ipv4.mask == match.group(2))
                else:
                    i = i.join(Ipv4).filter(Ipv4.ipv4 == d['indicator'])

            elif d['itype'] == 'ipv6':
                match = re.search('^(\S+)\/(\d+)$', d['indicator'])  # TODO -- use ipaddress
                if match:
                    i = i.join(Ipv6).filter(Ipv6.ip == match.group(1), Ipv6.mask == match.group(2))
                else:
                    i = i.join(Ipv6).filter(Ipv6.ip == d['indicator'])

            elif d['itype'] == 'fqdn':
                i = i.join(Fqdn).filter(Fqdn.fqdn == d['indicator'])

            elif d['itype'] == 'url':
                i = i.join(Url).filter(Url.url == d['indicator'])

            elif d['itype'] in HASH_TYPES:
                i = i.join(Hash).filter(Hash.hash == d['indicator'])

            if len(tags):
                i = i.join(Tag).filter(Tag.tag == tags[0])

            r = i.first()
            if r and not isinstance(r, Indicator):
                r = r.get(i.indicator_id)

            # if the record exists..
            if r and d.get('last_at') and arrow.get(d.get('last_at')).datetime <= arrow.get(r.last_at).datetime:
                logger.debug('skipping: %s' % d['indicator'])
                continue

            if r:
                r.count += 1
                if not d.get('last_at'):
                    d['last_at'] = arrow.utcnow()
                r.last_at = arrow.get(d['last_at']).datetime.replace(tzinfo=None)

                r.reported_at = d.get('reported_at', arrow.utcnow().datetime)
                r.reported_at = arrow.get(r.reported_at).datetime.replace(tzinfo=None)

                if d.get('message'):
                    m = Message(message=d['message'], indicator=r)
                    s.add(m)

                n += 1

                continue

            # check to see if it's been added in the cache
            if cached_added.get(d['indicator']):
                if d.get('last_at') in cached_added[d['indicator']]:
                    logger.debug('skipping: %s' % d['indicator'])
                    continue

            # new record
            cached_added[d['indicator']] = set()

            self._cleanup_timestamps(d)

            ii = Indicator(**d)
            s.add(ii)

            for t in tags:
                t = Tag(tag=t, indicator=ii)
                s.add(t)

            if d.get('message'):
                m = Message(message=d['message'], indicator=ii)
                s.add(m)

            self._upsert_itype(s, ii)

            n += 1
            cached_added[d['indicator']].add(d['last_at'])

        logger.debug('committing')
        start = time.time()
        s.commit()
        nx.write_gpickle(self.graph, GRAPH_PATH)
        nx.write_gexf(self.graph, GRAPH_GEXF_PATH)
        logger.debug('done: %0.2f' % (time.time() - start))
        return n
