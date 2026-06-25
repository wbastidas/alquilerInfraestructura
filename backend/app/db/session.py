"""Motor de base de datos y gestión de sesiones de SQLAlchemy."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import obtener_configuracion

config = obtener_configuracion()

# pool_pre_ping evita errores por conexiones MariaDB caídas tras inactividad.
engine = create_engine(config.database_url, pool_pre_ping=True, future=True)

SesionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def obtener_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión de BD y la cierra al finalizar la petición."""
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
