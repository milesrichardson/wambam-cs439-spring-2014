from Crypto.Cipher import AES
from base64 import b64encode, b64decode


encrypter = None

def setup_encyrption(app):
    global encrypter
    encrypter = AES.new(app.config["SECRET_KEY"])


def pad_string(raw):
    return raw + (16 - (len(raw)%16)) * ' '

def encrypt_string(plain):
    #add characters until the string has a length multiple of 16
    if encrypter is None:
        return plain
    return b64encode(encrypter.encrypt(pad_string(plain)))

def decrypt_string(enc):
    #remove spaces from end of string
    if encrypter is None:
        return enc
    try:
        return encrypter.decrypt(b64decode(enc)).rstrip()
    except:
        return enc


def encrypt_dictionary(plaintext):
    keys = plaintext.keys()
    encrypted = {}
    for k in keys:
        if isinstance(plaintext[k], basestring):
            encrypted[k] = encrypt_string(plaintext[k])
        elif isinstance(plaintext[k], float):
            encrypted[k] = encrypt_string(str(plaintext[k]))
    return encrypted

def decrypt_object(encrypted):
    keys = [key for key in dir(encrypted) if not key.startswith('__')]
    plaintext = {}
    for k in keys:
        try:
            value = getattr(encrypted, k)
            if isinstance(value, basestring):
                plaintext[k] = decrypt_string(value)
        except:
            pass
    return plaintext
