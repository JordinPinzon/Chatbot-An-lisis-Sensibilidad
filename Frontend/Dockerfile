FROM node:18

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de dependencias e instala
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copia todo el resto del proyecto
COPY . .

# Construye el proyecto para producción
RUN npm run build

# Usa un servidor web ligero para servir los archivos (opcional pero recomendado)
# Si usas Vite, puedes usar esto:
RUN npm install -g serve

# Expón el puerto que usa `serve` (por defecto 3000)
EXPOSE 3000

# Comando de inicio: sirve la carpeta de distribución (dist)
CMD ["serve", "-s", "dist", "-l", "3000"]
