"""
Tests para la API de Música.
Pruebas unitarias y de integración usando pytest.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from musica_api.database import get_session
from musica_api.models import Cancion, Favorito, Usuario

# =============================================================================
# CONFIGURACIÓN DE FIXTURES
# =============================================================================


# Fixture para crear una base de datos en memoria para testing
@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para cada test.
    Se limpia automáticamente después de cada test.
    """
    # Crear engine en memoria (SQLite).
    # StaticPool hace que todas las conexiones compartan la MISMA base en memoria;
    # sin él, cada conexión vería una base vacía distinta.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)

    # Crear sesión
    with Session(engine) as session:
        yield session


# Fixture para cliente de pruebas
@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Crea un cliente de pruebas de FastAPI con la sesión de test.
    """

    # Override de la dependencia get_session: los endpoints usarán la base en memoria
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Fixture para crear usuarios de prueba
@pytest.fixture(name="usuario_test")
def usuario_test_fixture(session: Session):
    """
    Crea un usuario de prueba en la base de datos.
    """
    usuario = Usuario(nombre="Usuario Test", correo="test@mail.com")
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


# Fixture para crear canciones de prueba
@pytest.fixture(name="cancion_test")
def cancion_test_fixture(session: Session):
    """
    Crea una cancion de prueba en la base de datos.
    """
    cancion = Cancion(
        titulo="Canción Test",
        artista="Artista Test",
        album="Álbum Test",
        duracion=210,
        año=2020,
        genero="Rock",
    )
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


# =============================================================================
# TESTS DE USUARIOS
# =============================================================================


class TestUsuarios:
    """Tests para los endpoints de usuarios."""

    def test_listar_usuarios(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios"""
        response = client.get("/api/usuarios")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["correo"] == usuario_test.correo

    def test_crear_usuario(self, client: TestClient):
        """Test para POST /api/usuarios"""
        response = client.post(
            "/api/usuarios",
            json={"nombre": "Laura Martínez", "correo": "Laura@Mail.com"},
        )
        data = response.json()

        assert response.status_code == 201
        assert data["id"] is not None
        assert data["nombre"] == "Laura Martínez"
        assert data["correo"] == "laura@mail.com"  # se normaliza a minúsculas
        assert "fecha_registro" in data

    def test_crear_usuario_correo_duplicado(
        self, client: TestClient, usuario_test: Usuario
    ):
        """Test para verificar que no se permiten correos duplicados"""
        response = client.post(
            "/api/usuarios",
            json={"nombre": "Otro Usuario", "correo": usuario_test.correo},
        )

        assert response.status_code == 409

    def test_obtener_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios/{id}"""
        response = client.get(f"/api/usuarios/{usuario_test.id}")
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == usuario_test.id
        assert data["nombre"] == usuario_test.nombre

    def test_obtener_usuario_no_existe(self, client: TestClient):
        """Test para verificar error 404 con usuario inexistente"""
        response = client.get("/api/usuarios/9999")

        assert response.status_code == 404

    def test_actualizar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para PUT /api/usuarios/{id}"""
        response = client.put(
            f"/api/usuarios/{usuario_test.id}",
            json={"nombre": "Nombre Actualizado"},
        )
        data = response.json()

        assert response.status_code == 200
        assert data["nombre"] == "Nombre Actualizado"
        assert data["correo"] == usuario_test.correo  # lo no enviado no cambia

    def test_eliminar_usuario(
        self, client: TestClient, session: Session, usuario_test: Usuario
    ):
        """Test para DELETE /api/usuarios/{id}"""
        response = client.delete(f"/api/usuarios/{usuario_test.id}")

        assert response.status_code == 204
        assert session.get(Usuario, usuario_test.id) is None


# =============================================================================
# TESTS DE CANCIONES
# =============================================================================


class TestCanciones:
    """Tests para los endpoints de canciones."""

    def test_listar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones"""
        response = client.get("/api/canciones")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["titulo"] == cancion_test.titulo

    def test_crear_cancion(self, client: TestClient):
        """Test para POST /api/canciones"""
        response = client.post(
            "/api/canciones",
            json={
                "titulo": "Bohemian Rhapsody",
                "artista": "Queen",
                "album": "A Night at the Opera",
                "duracion": 354,
                "año": 1975,
                "genero": "Rock",
            },
        )
        data = response.json()

        assert response.status_code == 201
        assert data["id"] is not None
        assert data["titulo"] == "Bohemian Rhapsody"
        assert data["año"] == 1975

    def test_obtener_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/{id}"""
        response = client.get(f"/api/canciones/{cancion_test.id}")

        assert response.status_code == 200
        assert response.json()["artista"] == cancion_test.artista

    def test_obtener_cancion_no_existe(self, client: TestClient):
        """Test para verificar error 404 con canción inexistente"""
        response = client.get("/api/canciones/9999")

        assert response.status_code == 404

    def test_actualizar_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para PUT /api/canciones/{id}"""
        response = client.put(
            f"/api/canciones/{cancion_test.id}",
            json={"album": "Edición Especial"},
        )
        data = response.json()

        assert response.status_code == 200
        assert data["album"] == "Edición Especial"
        assert data["titulo"] == cancion_test.titulo

    def test_eliminar_cancion(
        self, client: TestClient, session: Session, cancion_test: Cancion
    ):
        """Test para DELETE /api/canciones/{id}"""
        response = client.delete(f"/api/canciones/{cancion_test.id}")

        assert response.status_code == 204
        assert session.get(Cancion, cancion_test.id) is None

    def test_buscar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/buscar"""
        # Búsqueda parcial y sin distinguir mayúsculas
        response = client.get("/api/canciones/buscar", params={"titulo": "test"})
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["id"] == cancion_test.id

        # Sin coincidencias
        response = client.get("/api/canciones/buscar", params={"titulo": "xyz"})
        assert response.json() == []

    def test_buscar_canciones_multiples_filtros(
        self, client: TestClient, session: Session
    ):
        """Test para búsqueda con múltiples parámetros"""
        session.add_all(
            [
                Cancion(
                    titulo="La Bicicleta",
                    artista="Carlos Vives",
                    duracion=227,
                    año=2016,
                    genero="Vallenato pop",
                ),
                Cancion(
                    titulo="La Gota Fría",
                    artista="Carlos Vives",
                    duracion=270,
                    año=1993,
                    genero="Vallenato",
                ),
                Cancion(
                    titulo="Tusa",
                    artista="Karol G",
                    duracion=200,
                    año=2019,
                    genero="Reguetón",
                ),
            ]
        )
        session.commit()

        # Solo por artista: 2 resultados
        response = client.get("/api/canciones/buscar", params={"artista": "vives"})
        assert len(response.json()) == 2

        # Artista + título: los filtros se combinan (AND)
        response = client.get(
            "/api/canciones/buscar",
            params={"artista": "vives", "titulo": "gota"},
        )
        data = response.json()
        assert len(data) == 1
        assert data[0]["titulo"] == "La Gota Fría"


# =============================================================================
# TESTS DE FAVORITOS
# =============================================================================


class TestFavoritos:
    """Tests para los endpoints de favoritos."""

    def test_listar_favoritos(self, client: TestClient):
        """Test para GET /api/favoritos"""
        response = client.get("/api/favoritos")

        assert response.status_code == 200
        assert response.json() == []

    def test_crear_favorito(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/favoritos"""
        response = client.post(
            "/api/favoritos",
            json={"id_usuario": usuario_test.id, "id_cancion": cancion_test.id},
        )
        data = response.json()

        assert response.status_code == 201
        assert data["id_usuario"] == usuario_test.id
        assert data["id_cancion"] == cancion_test.id
        assert "fecha_marcado" in data

    def test_crear_favorito_usuario_no_existe(
        self, client: TestClient, cancion_test: Cancion
    ):
        """Test para verificar 404 si el usuario no existe"""
        response = client.post(
            "/api/favoritos",
            json={"id_usuario": 9999, "id_cancion": cancion_test.id},
        )

        assert response.status_code == 404

    def test_crear_favorito_duplicado(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para verificar que no se permiten favoritos duplicados"""
        datos = {"id_usuario": usuario_test.id, "id_cancion": cancion_test.id}
        client.post("/api/favoritos", json=datos)
        response = client.post("/api/favoritos", json=datos)

        assert response.status_code == 409

    def test_eliminar_favorito(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para DELETE /api/favoritos/{id}"""
        favorito = Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id)
        session.add(favorito)
        session.commit()
        session.refresh(favorito)

        response = client.delete(f"/api/favoritos/{favorito.id}")

        assert response.status_code == 204
        assert session.get(Favorito, favorito.id) is None

    def test_marcar_favorito_usuario(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/usuarios/{id}/favoritos/{id_cancion}"""
        response = client.post(
            f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"
        )

        assert response.status_code == 201
        assert response.json()["id_cancion"] == cancion_test.id

    def test_listar_favoritos_usuario(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para GET /api/usuarios/{id}/favoritos"""
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()

        response = client.get(f"/api/usuarios/{usuario_test.id}/favoritos")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["id_cancion"] == cancion_test.id

    def test_eliminar_favorito_especifico(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para DELETE /api/usuarios/{id_usuario}/favoritos/{id_cancion}"""
        url = f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"
        client.post(url)

        response = client.delete(url)
        assert response.status_code == 204

        # Ya no existe: un segundo DELETE da 404
        assert client.delete(url).status_code == 404

    def test_eliminar_usuario_borra_sus_favoritos(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Al eliminar un usuario se eliminan sus favoritos (cascada)"""
        client.post(f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}")

        client.delete(f"/api/usuarios/{usuario_test.id}")

        assert client.get("/api/favoritos").json() == []


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================


class TestIntegracion:
    """Tests de integración que prueban flujos completos."""

    def test_flujo_completo(self, client: TestClient):
        """Test que verifica el flujo completo de la aplicación"""
        # 1. Crear usuario
        usuario = client.post(
            "/api/usuarios",
            json={"nombre": "Camila Torres", "correo": "camila@mail.com"},
        ).json()

        # 2. Crear canción
        cancion = client.post(
            "/api/canciones",
            json={
                "titulo": "Blinding Lights",
                "artista": "The Weeknd",
                "album": "After Hours",
                "duracion": 200,
                "año": 2019,
                "genero": "Synth-pop",
            },
        ).json()

        # 3. Marcar como favorito
        response = client.post(
            f"/api/usuarios/{usuario['id']}/favoritos/{cancion['id']}"
        )
        assert response.status_code == 201

        # 4. Verificar que aparece en favoritos del usuario
        favoritos = client.get(f"/api/usuarios/{usuario['id']}/favoritos").json()
        assert len(favoritos) == 1
        assert favoritos[0]["id_cancion"] == cancion["id"]


# =============================================================================
# TESTS DE VALIDACIÓN
# =============================================================================


class TestValidacion:
    """Tests para validaciones de datos."""

    @pytest.mark.parametrize(
        "correo", ["sin-arroba.com", "usuario@", "@dominio.com", "a@b", ""]
    )
    def test_email_invalido(self, client: TestClient, correo: str):
        """Test para verificar validación de email"""
        response = client.post(
            "/api/usuarios", json={"nombre": "Prueba", "correo": correo}
        )

        assert response.status_code == 422

    @pytest.mark.parametrize("año", [1899, 2999])
    def test_año_cancion_invalido(self, client: TestClient, año: int):
        """Test para verificar validación de año"""
        response = client.post(
            "/api/canciones",
            json={
                "titulo": "Canción",
                "artista": "Artista",
                "duracion": 200,
                "año": año,
                "genero": "Pop",
            },
        )

        assert response.status_code == 422

    def test_duracion_invalida(self, client: TestClient):
        """La duración debe ser mayor que cero"""
        response = client.post(
            "/api/canciones",
            json={
                "titulo": "Canción",
                "artista": "Artista",
                "duracion": 0,
                "año": 2020,
                "genero": "Pop",
            },
        )

        assert response.status_code == 422

    def test_campos_requeridos(self, client: TestClient):
        """Test para verificar que los campos requeridos son obligatorios"""
        response = client.post("/api/canciones", json={"titulo": "Solo título"})
        campos_con_error = {error["loc"][-1] for error in response.json()["detail"]}

        assert response.status_code == 422
        assert {"artista", "duracion", "año", "genero"} <= campos_con_error


# =============================================================================
# TESTS DE UTILIDADES
# =============================================================================


class TestUtils:
    """Tests unitarios para las funciones de utils.py."""

    def test_formatear_duracion(self):
        from utils import formatear_duracion

        assert formatear_duracion(245) == "04:05"
        assert formatear_duracion(59) == "00:59"

    def test_generar_slug(self):
        from utils import generar_slug

        assert generar_slug("  Canción de Año!! ") == "cancion-de-ano"

    def test_validar_año(self):
        from utils import obtener_año_actual, validar_año

        assert validar_año(2000)
        assert not validar_año(obtener_año_actual() + 1)
