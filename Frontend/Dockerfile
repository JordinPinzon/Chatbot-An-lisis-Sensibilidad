FROM node:18

WORKDIR /app

# Instalar servidor de archivos estáticos
RUN npm install -g serve

# Copiar el build generado localmente
COPY build ./build

# Exponer el puerto que usará `serve`
EXPOSE 3000

# Comando por defecto para servir la app
CMD ["serve", "-s", "build", "-l", "3000", "--single"]
