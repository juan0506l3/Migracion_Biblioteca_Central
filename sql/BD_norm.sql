-- TABLA EDITORIAL
CREATE TABLE Editoriales (
    id_editorial SERIAL PRIMARY KEY,
    nombre VARCHAR(255)
);

-- TABLA LIBROS
CREATE TABLE Libros (
    id_libro SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    fecha_publicacion DATE,
    id_editorial INT,
    FOREIGN KEY (id_editorial) REFERENCES Editoriales(id_editorial)
);

-- TABLA AUTORES
CREATE TABLE Autores (
    id_autor SERIAL PRIMARY KEY,
    nombre VARCHAR(255)
);

-- RELACION LIBRO - AUTOR
CREATE TABLE Libro_Autor (
    id_libro INT,
    id_autor INT,
    PRIMARY KEY (id_libro, id_autor),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro),
    FOREIGN KEY (id_autor) REFERENCES Autores(id_autor)
);

-- TABLA CATEGORIAS
CREATE TABLE Categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    descripcion TEXT
);

-- RELACION LIBRO - CATEGORIA
CREATE TABLE Libro_Categoria (
    id_libro INT,
    id_categoria INT,
    PRIMARY KEY (id_libro, id_categoria),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro),
    FOREIGN KEY (id_categoria) REFERENCES Categorias(id_categoria)
);

-- TABLA USUARIOS
CREATE TABLE Usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    correo VARCHAR(255)
);

-- TABLA PRESTAMOS
CREATE TABLE Prestamos (
    id_prestamo SERIAL PRIMARY KEY,
    id_usuario INT,
    fecha_salida DATE,
    estado VARCHAR(20),
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);

-- RELACION PRESTAMO - LIBRO
CREATE TABLE Prestamo_Libro (
    id_prestamo INT,
    id_libro INT,
    PRIMARY KEY (id_prestamo, id_libro),
    FOREIGN KEY (id_prestamo) REFERENCES Prestamos(id_prestamo),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro)
);

-- TABLA SEDES
CREATE TABLE Sedes (
    id_sede SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    ubicacion VARCHAR(255)
);

-- INVENTARIO
CREATE TABLE Inventario (
    id_sede INT,
    id_libro INT,
    cantidad INT,
    PRIMARY KEY (id_sede, id_libro),
    FOREIGN KEY (id_sede) REFERENCES Sedes(id_sede),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro)
);

-- TABLA RESEÑAS
CREATE TABLE Reseñas (
    id_reseña SERIAL PRIMARY KEY,
    id_usuario INT,
    id_libro INT,
    comentario TEXT,
    calificacion INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro)
);