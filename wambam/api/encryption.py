from Crypto.Cipher import AES
from base64 import b64encode, b64decode


#if the encrypter is None, encryption is turned off
encrypter = None

#calling this function enables encryption
def setup_encyrption(app):
    global encrypter
    encrypter = AES.new(app.config["SECRET_KEY"])

#add spaces to the end of the string so that its length is a multiple of 16
def pad_string(raw):
    return raw + (16 - (len(raw)%16)) * " "

def encrypt_string(plain):
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
        #exception occur when enc is not base64 encoded or does not have
        #length a multiple of 16.  The string was not encrypted with the 
        #encryption function above, so assume its unencrypted
        return enc


def encrypt_dictionary(plaintext):
    keys = plaintext.keys()
    encrypted = {}
    for k in keys:
        #only encrypt the strings and floats in the dictionary
        if isinstance(plaintext[k], basestring):
            encrypted[k] = encrypt_string(plaintext[k])
        elif isinstance(plaintext[k], float):
            encrypted[k] = encrypt_string(str(plaintext[k]))
    return encrypted

def decrypt_object(encrypted):
    #ignore the special methods and attributes
    keys = [key for key in dir(encrypted) if not key.startswith("__")]
    plaintext = {}
    for k in keys:
        try:
            value = getattr(encrypted, k)
            if isinstance(value, basestring):
                plaintext[k] = decrypt_string(value)
        except:
            #if any exceptions, assume that the attribute was not encrypted
            pass
    return plaintext
