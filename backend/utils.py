from passlib.context import CryptContext

USERNAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_.]{2,19}$'
PASSWORD_REGEX = r'^(?=.*\d)[A-Za-z\d]{6,}$'

pwd_context = CryptContext(schemes=['bcrypt'])


def get_password_hash(plain_password) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
