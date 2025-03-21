# Usa la imagen oficial de Python 3.13.2 (en este ejemplo, usamos la variante slim)
FROM python:3.13.2-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias y las instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Comando por defecto para ejecutar el bot
CMD ["python", "app.py"]
