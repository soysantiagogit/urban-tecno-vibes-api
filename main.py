from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import session
from pydantic import BaseModel
from typing import Optional
from database import sessionLocal, engine
from dotenv import load_dotenv
import os
import models
import auth

#seguridad de correo y contraseña 
load_dotenv(dotenv_path="C:/Users/ediso/OneDrive/Desktop/ECOMMERCE/backend/.env")

#crea las tablas automaticamente 
models.Base.metadata.create_all(bind=engine)

#crear usuario admin por defecto al arrancar el servidor 
def crear_admin():
    db = sessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        admin = db.query(models.Usuario).filter(models.Usuario.email == admin_email).first()
        if not admin:
            nuevo_admin = models.Usuario(
                nombre="administrador",
                email=admin_email,
                password=auth.hashear_password(admin_password),
                es_admin=True
            )
            db.add(nuevo_admin)
            db.commit()
            print("Usuario admin creado correctamente")
        else:
            print("admin ya existe")
    finally:
        db.close()
        
crear_admin()

app = FastAPI(title="E-commerce API", version="1.0.0")

#CORS --> permite que el frontend (html/js) pueda consumir la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#sesión de la base de datos 
def get_db():
    db = sessionLocal()
    try:
        yield db 
    finally:
        db.close()
        
#get del inicio 
@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la api de E-commerce"}


#===============================================
#SHEMAS 
#===============================================

#USUARIOS
class UsuarioRegistro(BaseModel):
    nombre: str
    email: str 
    password: str 
    
class UsuarioRespuesta(BaseModel):
    id: int 
    nombre: str 
    email: str 
    es_admin: bool
    
    class Config:
        from_attributes = True
        
#CATEGORIAS 
class CategoriaSchema(BaseModel):
    nombre: str 
    
#PRODUCTOS 
class ProductoSchema(BaseModel): 
    nombre: str 
    descripcion: str 
    precio: float
    stock: int 
    imagen_url: Optional[str] = None
    categoria_id: int 

#PEDIDOS 
class DetallePedidoSchema(BaseModel):
    producto_id: int 
    cantidad: int 
    
class PedidoSchema(BaseModel):
    detalles: list[DetallePedidoSchema]
    
#IMAGEN PRODUCTOS
class ImagenSchema(BaseModel):
    url: str
    
#==============================================
#SCHEMAS ADMIN UTV
#==============================================

#PROVEEDORES 
class ProveedorSchema(BaseModel):
    nombre: str 
    contacto: str 
    telefono: str 
    email: str 
    direccion: str 

#COMPRAS
class CompraSchema(BaseModel):
    proveedor_id: int
    fecha: str 
    notas: Optional[str] = None
 
#DETALLES COMPRAS     
class DetalleCompraSchema(BaseModel):
    producto_id: int 
    cantidad: int 
    precio_compra: float 

#GASTOS    
class GastoSchema(BaseModel):
    categoria: str 
    descripcion: str 
    monto: float 
    fecha: str 
    comprobante: Optional[str] = None

#INGRESOS    
class IngresoSchema(BaseModel):
    categoria: str
    descripcion: str 
    monto: float 
    fecha: str 

#SOCIOS    
class SocioSchema(BaseModel):
    usuario_id: int 
    nombre: str 
    porcentaje: float

#SUELDOS     
class SueldoSchema(BaseModel):
    socio_id: int 
    monto: float 
    fecha: str 
    mes: str 

#CAJA DIARIA    
class CajaDiariaSchema(BaseModel):
    fecha: str
    ingresos_ventas: float = 0 
    ingresos_otros: float = 0
    gastos: float = 0
    sueldos: float = 0 
    compras: float = 0
    notas: Optional[str] = None 
    

#===============================================
#AUTENTICACIÓN 
#===============================================

#POST /registro --> registra un nuevo usuario 
@app.post("/registro")
def registro(usuario: UsuarioRegistro,db: session = Depends(get_db)):
    #verifica que el email no exista ya
    existe = db.query(models.Usuario).filter(
        models.Usuario.email == usuario.email
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    #hashear la contraseña 
    password_hash = auth.hashear_password(usuario.password)
    
    nuevo_usuario = models.Usuario(
        nombre = usuario.nombre,
        email = usuario.email,
        password = password_hash        
    )    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {"mensaje": "Usuario registrado correctamente", "Usuario": nuevo_usuario.nombre}

#POST /login --> devuelve el token JWT 
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: session = Depends(get_db)):
    usuario_db = db.query(models.Usuario).filter(
        models.Usuario.email == form_data.username
    ).first()
    
    if not usuario_db:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    if not auth.verificar_password(form_data.password, usuario_db.password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    token = auth.crear_token({"sub": usuario_db.email})
    return {"access_token": token, "token_type": "bearer"}
 
#GET /perfil --> ruta protegida, devuelve datos del usuario actual 
@app.get("/perfil")
def perfil(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "es_admin": usuario.es_admin
    }
    
#===============================================
#CATEGORIAS 
#===============================================

#GET CATEGORIAS/ devuelve todas las categorias 
@app.get("/categorias")
def get_categorias(db: session = Depends(get_db)):
    return db.query(models.Categoria).all()

#POST /Categorias --> crea una nueva categoria (solo admin)
@app.post("/categorias")
def crear_categoria(categoria: CategoriaSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    #verificar que sea admin 
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="solo los administradores pueden crear categorías")
    
    #verificar que no exista ya 
    exite = db.query(models.Categoria).filter(models.Categoria.nombre == categoria.nombre).first()
    if exite:
        raise HTTPException(status_code=400, detail="la categoría ya existe")
    
    nueva = models.Categoria(nombre=categoria.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"mensaje": "Categoria crea correctamente", "Categoria": nueva}


#===============================================
#PRODUCTOS 
#===============================================

#GET /Productos --> devuelve todos los productos 
@app.get("/productos")
def get_productos(db: session = Depends(get_db)):
    return db.query(models.Producto).all()

#GET /Producto/{id} --> devuelve un producto por su id 
@app.get("/productos/{id}")
def get_producto(id: int, db: session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

#POST /productos --> agrega un nuevo producto (solo admin)
@app.post("/productos")
def crear_producto(producto: ProductoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    #verificar que sea el admin 
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear productos")
    
    nuevo = models.Producto(**producto.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Producto creado correctamente", "Producto": nuevo}

#PUT /Productos/{id} --> actualiza un producto (solo admin)
@app.put("/producto/{id}")
def actualizar_producto(id: int, producto: ProductoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden actualizar productos")

    producto_db = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado") 
    
    producto_db.nombre = producto.nombre
    producto_db.descripcion = producto.descripcion 
    producto_db.precio = producto.precio 
    producto_db.stock = producto.stock 
    producto_db.imagen_url = producto.imagen_url
    producto_db.categoria_id = producto.categoria_id
    db.commit()
    return {"mensaje": "Producto acutualizado correctamente", "producto": producto_db}

#DELITE /producto/{id} --> elimina un producto (solo admin)
@app.delete("/producto/{id}")
def eliminar_producto(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden eliminar productos")
    
    producto_db = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto_db)
    db.commit()
    return {"mensaje": "Producto eliminado correctamente"}    

# GET /productos/{id}/imagenes → obtiene todas las imágenes 
@app.get("/productos/{id}/imagenes")
def get_imagenes(id: int, db: session = Depends(get_db)):
    return db.query(models.ImagenProducto).filter(models.ImagenProducto.producto_id == id).all()

# POST /productos/{id}/imagenes → agrega una imagen (solo admin)
@app.post("/productos/{id}/imagenes")
def agregar_imagen(id: int, imagen: ImagenSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden agregar imágenes")

    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    nueva_imagen = models.ImagenProducto(producto_id=id, url=imagen.url)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return {"mensaje": "Imagen agregada correctamente", "imagen": nueva_imagen}

# DELETE /productos/imagenes/{id} → elimina una imagen (solo admin)
@app.delete("/productos/imagenes/{id}")
def eliminar_imagen(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden eliminar imágenes")

    imagen = db.query(models.ImagenProducto).filter(models.ImagenProducto.id == id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    db.delete(imagen)
    db.commit()
    return {"mensaje": "Imagen eliminada correctamente"}

#===============================================
#PEDIDOS 
#===============================================

#GET /pedidos --> devuelve todos los pedidos (solo admin)
@app.get("/pedidos")
def get_pedidos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="solo los administradores pueden ver todos los pedidos")
    return db.query(models.Pedido).all()

#GET /pedidos/{id} --> devuelve el pedido de los clientes (solo admin)
@app.get("/pedidos/{id}/detalles")
def get_detalles_pedido(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden ver los detalles")

    detalles = db.query(models.DetallePedido).filter(models.DetallePedido.pedido_id == id).all()
    resultado = []
    for detalle in detalles:
        producto = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
        resultado.append({
            "producto": producto.nombre,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.cantidad * detalle.precio_unitario
        })
    return resultado

#GET /pedidos/mis-pedidos --> devuelve los pedidos del usuario logueado
@app.get("/pedidos/mis-pedidos")
def  get_mis_pedidos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    return db.query(models.Pedido).filter(models.Pedido.usuario_id == usuario.id).all()

#POST /pedidos --> crea un nuevo pedido
@app.post("/pedidos")
def crear_pedido(pedido: PedidoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    #crea el pedido 
    nuevo_pedido = models.Pedido(usuario_id=usuario.id, estado="pendiente") 
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    
    #agrega los detalles del pedido  
    for detalle in pedido.detalles:
        #verifica que el producto exista y tenga stock 
        producto = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"producto {detalle.producto_id} no encotrado")
        if producto.stock < detalle.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {producto.nombre}")
        
        #crear el detalle 
        nuevo_detalle = models.DetallePedido(
            pedido_id=nuevo_pedido.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            precio_unitario=producto.precio
        )
        db.add(nuevo_detalle)
        
        #reducir el stock del producto 
        producto.stock -= detalle.cantidad
        
    db.commit()
    return {"mensaje": "pedido creado correctamente", "pedido_id": nuevo_pedido.id}

#PUT /pedidos/{id}/estado --> actializa el estado de un pedido (solo admin)
@app.put("/pedidos/{id}/estado")
def actualizar_estado(id: int, estado: str, email: str = Depends(auth.obtener_usuario_actual), db:session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=403, detail="solo los administradores pueden actualizar el estado")
    
    pedido = db.query(models.Pedido).filter(models.Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    pedido.estado = estado
    db.commit()
    return {"mensaje": "Estado actualizado correctamente", "pedido_id": id, "estado":estado}

#===============================================
#CLIENTES 
#===============================================

@app.get("/clientes")
def get_clientes(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden ver los clientes")
    return db.query(models.Usuario).all()



#============================================================
# ENDPOINTS ADMIN UTV
#============================================================

# ============================================
# PROVEEDORES
# ============================================

@app.get("/proveedores")
def get_proveedores(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Proveedor).filter(models.Proveedor.activo == True).all()

@app.post("/proveedores")
def crear_proveedor(proveedor: ProveedorSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nuevo = models.Proveedor(**proveedor.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Proveedor agregado correctamente", "proveedor": nuevo}

@app.put("/proveedores/{id}")
def actualizar_proveedor(id: int, proveedor: ProveedorSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    proveedor_db = db.query(models.Proveedor).filter(models.Proveedor.id == id).first()
    if not proveedor_db:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    for key, value in proveedor.dict().items():
        setattr(proveedor_db, key, value)
    db.commit()
    return {"mensaje": "Proveedor actualizado correctamente"}

@app.delete("/proveedores/{id}")
def eliminar_proveedor(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    proveedor_db = db.query(models.Proveedor).filter(models.Proveedor.id == id).first()
    if not proveedor_db:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    proveedor_db.activo = False
    db.commit()
    return {"mensaje": "Proveedor eliminado correctamente"}

# ============================================
# COMPRAS
# ============================================

@app.get("/compras")
def get_compras(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Compra).all()

@app.post("/compras")
def crear_compra(compra: CompraSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nueva = models.Compra(
        proveedor_id=compra.proveedor_id,
        fecha=compra.fecha,
        notas=compra.notas,
        total=0,
        estado="pendiente"
    )
    return {"mensaje": "Compra registrada correctamente", "compra_id": nueva.id}

@app.post("/compras/{id}/detalles")
def agregar_detalle_compra(id: int, detalle: DetalleCompraSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    compra = db.query(models.Compra).filter(models.Compra.id == id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    nuevo_detalle = models.DetalleCompra(
        compra_id=id,
        producto_id=detalle.producto_id,
        cantidad=detalle.cantidad,
        precio_compra=detalle.precio_compra
    )
    db.add(nuevo_detalle)

    # actualizar stock del producto
    producto = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
    if producto:
        producto.stock += detalle.cantidad

        # registrar movimiento de stock
        movimiento = models.StockMovimiento(
            producto_id=detalle.producto_id,
            tipo="entrada",
            cantidad=detalle.cantidad,
            motivo="compra",
            fecha=compra.fecha
        )
        db.add(movimiento)

    # actualizar total de la compra
    compra.total += detalle.cantidad * detalle.precio_compra
    db.commit()
    return {"mensaje": "Detalle agregado y stock actualizado"}

@app.get("/compras/{id}/detalles")
def get_detalles_compra(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    detalles = db.query(models.DetalleCompra).filter(models.DetalleCompra.compra_id == id).all()
    resultado = []
    for detalle in detalles:
        producto = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
        resultado.append({
            "producto": producto.nombre if producto else "Desconocido",
            "cantidad": detalle.cantidad,
            "precio_compra": detalle.precio_compra,
            "subtotal": detalle.cantidad * detalle.precio_compra
        })
    return resultado

# ============================================
# GASTOS
# ============================================

@app.get("/gastos")
def get_gastos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Gasto).all()

@app.post("/gastos")
def crear_gasto(gasto: GastoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nuevo = models.Gasto(
        categoria=gasto.categoria,
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        fecha=gasto.fecha,
        comprobante=gasto.comprobante
    )
    return {"mensaje": "Gasto registrado correctamente", "gasto": nuevo}

@app.delete("/gastos/{id}")
def eliminar_gasto(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    gasto = db.query(models.Gasto).filter(models.Gasto.id == id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(gasto)
    db.commit()
    return {"mensaje": "Gasto eliminado correctamente"}

# ============================================
# INGRESOS
# ============================================

@app.get("/ingresos")
def get_ingresos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Ingreso).all()

@app.post("/ingresos")
def crear_ingreso(ingreso: IngresoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nuevo = models.Ingreso(
        categoria=ingreso.categoria,
        descripcion=ingreso.descripcion,
        monto=ingreso.monto,
        fecha=ingreso.fecha
    )
    return {"mensaje": "Ingreso registrado correctamente", "ingreso": nuevo}

# ============================================
# SOCIOS Y SUELDOS
# ============================================

@app.get("/socios")
def get_socios(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Socio).filter(models.Socio.activo == True).all()

@app.post("/socios")
def crear_socio(socio: SocioSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nuevo = models.Socio(
        usuario_id=socio.usuario_id,
        nombre=socio.nombre,
        porcentaje=socio.porcentaje
    )      
    return {"mensaje": "Socio registrado correctamente"}

@app.get("/sueldos")
def get_sueldos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.Sueldo).all()

@app.post("/sueldos")
def registrar_sueldo(sueldo: SueldoSchema, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    nuevo = models.Sueldo(
        socio_id=sueldo.socio_id,
        monto=sueldo.monto,
        fecha=sueldo.fecha,
        mes=sueldo.mes
    )
    return {"mensaje": "Sueldo registrado correctamente"}

@app.put("/sueldos/{id}/pagar")
def pagar_sueldo(id: int, email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    sueldo = db.query(models.Sueldo).filter(models.Sueldo.id == id).first()
    if not sueldo:
        raise HTTPException(status_code=404, detail="Sueldo no encontrado")
    sueldo.pagado = True
    db.commit()
    return {"mensaje": "Sueldo marcado como pagado"}

# ============================================
# REPORTES
# ============================================

@app.get("/reportes/resumen")
def get_resumen(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    # totales generales
    total_ventas = sum(p.precio * p.stock for p in db.query(models.Producto).all())
    total_gastos = sum(g.monto for g in db.query(models.Gasto).all())
    total_ingresos = sum(i.monto for i in db.query(models.Ingreso).all())
    total_compras = sum(c.total for c in db.query(models.Compra).all())
    total_sueldos = sum(s.monto for s in db.query(models.Sueldo).filter(models.Sueldo.pagado == True).all())
    total_pedidos = db.query(models.Pedido).count()
    total_productos = db.query(models.Producto).count()
    total_proveedores = db.query(models.Proveedor).filter(models.Proveedor.activo == True).count()

    return {
        "total_ventas_stock": total_ventas,
        "total_gastos": total_gastos,
        "total_ingresos_adicionales": total_ingresos,
        "total_compras": total_compras,
        "total_sueldos_pagados": total_sueldos,
        "balance": total_ingresos - total_gastos - total_sueldos,
        "total_pedidos": total_pedidos,
        "total_productos": total_productos,
        "total_proveedores": total_proveedores
    }

@app.get("/reportes/stock-bajo")
def get_stock_bajo(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    # productos con stock menor a 5
    productos = db.query(models.Producto).filter(models.Producto.stock <= 5).all()
    return productos

@app.get("/stock/movimientos")
def get_movimientos(email: str = Depends(auth.obtener_usuario_actual), db: session = Depends(get_db)):
    return db.query(models.StockMovimiento).all()