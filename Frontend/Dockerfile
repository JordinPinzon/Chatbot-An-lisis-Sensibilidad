FROM node:18

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps

# Copiar todo el código fuente
COPY . .

# Construir para producción
RUN npm run build

# Instalar servidor de archivos estáticos
RUN npm install -g serve

# Exponer puerto usado por `serve`
EXPOSE 3000

# Iniciar servidor con fallback para react-router
CMD ["serve", "-s", "build", "-l", "3000", "--single"]
