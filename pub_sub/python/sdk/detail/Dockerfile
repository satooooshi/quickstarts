FROM node:latest
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 3006
# CMD ["sleep", "3600"]
# hit an ERR_OSSL_EVP_UNSUPPORTED error
ENV NODE_OPTIONS=--openssl-legacy-provider
CMD [ "npm", "start"]

# docker build -t superheatedboy/tokenapi:latest .
# docker run -it -p 3002:3002 superheatedboy/tokenapi:latest
