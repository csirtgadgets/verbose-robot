from flask import request, _request_ctx_stack
import re


def aggregate(data, field='indicator', sort='confidence', sort_secondary='reported_at'):
    x = set()
    rv = []
    for d in sorted(data, key=lambda x: x[sort], reverse=True):
        if d[field] not in x:
            x.add(d[field])
            rv.append(d)

    rv = sorted(rv, key=lambda x: x[sort_secondary], reverse=True)
    return rv
