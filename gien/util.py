from hashlib                import md5

def hexhex(res):
    h = md5()
    h.update(res.encode('utf-8'))
    return h.hexdigest()
