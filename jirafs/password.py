import scrypt


password = None


def encrypt_password(password, passphrase):
    return scrypt.encrypt(password, passphrase)


def decrypt_password(hashed_password, passphrase):
    try:
        return scrypt.decrypt(hashed_password, passphrase)
    except:
        return False


def cache_password(p):
    global password
    password = p


def get_password_from_login_data(login_data):
    from . import utils
    global password
    if password is not None:
        login_data.pop('password', None)
        return password

    password = login_data.pop('password')
    password_encrypted = login_data.pop('password_encrypted', False)
    if password_encrypted:
        passphrase = utils.get_user_input('Passphrase: ', password=True)
        password = decrypt_password(password, passphrase)
        if not password:
            raise ValueError('Cannot use the passphrase to decrypt the encrypted JIRA password')

    return password
