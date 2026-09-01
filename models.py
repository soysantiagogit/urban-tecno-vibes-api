from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


#-----------------------------------------------
# TABLA DE USUARIOS 
#-----------------------------------------------
class Usuario(Base):
    __tablename__= "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    es_admin = Column(Boolean, default=False)
    pedidos = relationship("Pedido", back_populates="usuario")
    
    
#-----------------------------------------------   
# TABLA DE CATEGORIAS 
#-----------------------------------------------
class Categoria(Base):
    __tablename__="categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    productos = relationship("Producto", back_populates="categoria")
    
    
#-----------------------------------------------    
# TABLA PRODUCTO 
#-----------------------------------------------
class Producto(Base):
    __tablename__="productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String)
    precio =  Column(Float)
    stock = Column(Integer)
    imagen_url = Column(String)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria", back_populates="productos")
    imagenes = relationship("ImagenProducto", back_populates="producto")
    
    
#-----------------------------------------------    
# TABLA DE PEDIDOS 
#-----------------------------------------------
class Pedido(Base):
    __tablename__="pedidos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    estado = Column(String, default="pendiente")
    usuario = relationship("Usuario", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido")
    
    
#-----------------------------------------------    
# TABLA DE DETALLES PEDIDOS 
#-----------------------------------------------
class DetallePedido(Base):
    __tablename__="detalle_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto")
    
    
#-----------------------------------------------    
# TABLAS IMAGENES DE PRODUCTOS 
#-----------------------------------------------
class ImagenProducto(Base):
    __tablename__ = "imagenes_producto"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    url = Column(String)
    producto = relationship("Producto", back_populates="imagenes")
    
    
#=======================================================================
# TABLAS ADMIN UTV
#=======================================================================


#-----------------------------------------------
# PROVEEDORES
#-----------------------------------------------
class Proveedor(Base):
    __tablename__= "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    contacto = Column(String)
    telefono = Column(String)
    email = Column(String)
    direccion = Column(String)
    activo = Column(Boolean, default=True)
    compras = relationship("Compra", back_populates="proveedor")

#-----------------------------------------------
# COMPRAS A PROVEEDORES 
#-----------------------------------------------
class Compra(Base):
    __tablename__="compras"
    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    fecha = Column(String)
    total = Column(Float, default=0)
    estado = Column(String, default="pendiente")  #pendiente, pagada
    notas = Column(String)
    proveedor = relationship("Proveedor", back_populates="compras")
    detalles = relationship("DetalleCompra", back_populates="compra")
    
class DetalleCompra(Base):
    __tablename__= "detalle_compra"
    id = Column(Integer, primary_key=True, index=True)
    compra_id = Column(Integer, ForeignKey("compras.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer)
    precio_compra = Column(Float)
    compra = relationship("Compra", back_populates="detalles")
    producto = relationship("Producto")
    
    
#-----------------------------------------------
# MOVIMIENTOS DE STOCK 
#-----------------------------------------------
class StockMovimiento(Base):
    __tablename__="stock_movimientos"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    tipo = Column(String) #entrada, y salida 
    cantidad = Column(Integer)
    motivo = Column(String) #compra, venta, ajuste, devolucion 
    fecha = Column(String)
    producto = relationship("Producto")
    
    
#-----------------------------------------------
# GASTOS
#-----------------------------------------------
class Gasto(Base):
    __tablename__="gastos"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String) #alquiler, servicios, marketing 
    descripcion = Column(String)
    monto = Column(Float)
    fecha = Column(String)
    comprobante = Column(String) #Nro factura 
    
    
#-----------------------------------------------
# INGRESOS ADICIONALES 
#-----------------------------------------------
class Ingreso(Base):
    __tablename__="ingresos"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String) #venta, servicios, otro 
    descripcion = Column(String)
    monto = Column(Float)
    fecha = Column(String)
    

#-----------------------------------------------
# SOCIOS 
#-----------------------------------------------
class Socio(Base):
    __tablename__="socios"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nombre = Column(String)
    porcentaje = Column(Float) # % participacion en el negocio 
    activo = Column(Boolean, default=True)
    usuario = relationship("Usuario")
    sueldos = relationship("Sueldo", back_populates="socio")
    

#-----------------------------------------------
# SUELDOS 
#-----------------------------------------------
class Sueldo(Base): 
    __tablename__="sueldos"
    id = Column(Integer, primary_key=True, index=True)
    socio_id = Column(Integer, ForeignKey("socios.id"))
    monto = Column(Float)
    fecha = Column(String)
    mes = Column(String) #"2026-08"
    pagado = Column(Boolean, default=False)
    socio = relationship("Socio", back_populates="sueldos")
    

#-----------------------------------------------
# CAJA DIARIA 
#-----------------------------------------------
class CajaDiaria(Base):
    __tablename__="caja_diaria"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String, unique=True)
    ingresos_ventas = Column(Float, default=0)
    ingresos_otros = Column(Float, default=0)
    gastos = Column(Float, default=0)
    sueldos = Column(Float, default=0)
    compras = Column(Float, default=0)
    total = Column(Float, default=0)
    notas = Column(String)
    