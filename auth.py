from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

#configuracion para hashear contraseñas 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#configuracion JTW
SECRET_KEY = "ecommerce-clave-secreta-super-segura-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hashear_password(password: str):
    return pwd_context.hash(password)

def verificar_password(password: str, password_hash: str):
    return pwd_context.verify(password, password_hash)

def crear_token(data: dict):
    to_encode = data.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expira})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalido")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    