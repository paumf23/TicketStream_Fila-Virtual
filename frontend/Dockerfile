# Usa una imagen ligera y oficial de Node.js
FROM node:20-alpine

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de definición de dependencias
COPY package*.json ./

# Instala todas las dependencias
RUN npm install

# Copia el resto del código del frontend
COPY . .

# Deshabilita la telemetría de Next.js (opcional pero buena práctica en Docker)
ENV NEXT_TELEMETRY_DISABLED 1

# Construye la aplicación Next.js para producción
RUN npm run build

# Expone el puerto 3000
EXPOSE 3000

# Arranca el servidor de producción de Next.js
CMD ["npm", "run", "start"]
