# 🐧 Penguin Crypt

Penguin Crypt is a **web-based GUI wrapper for GPG** with safe vault and password management features.  
It turns complex Linux command-line encryption/decryption into a simple browser-based experience.

---

## ✨ Features

- 🔐 **File Encryption/Decryption**  
  - Encrypt/Decrypt files using GPG symmetric and asymmetric modes.  
  - Import,Create,Manage/Delete GPG keys through the web UI.  

- 📂 **Folder Encryption**  
  - Upload folders (tarball compression supported) and encrypt/decrypt them.  

- 🔑 **Vault Manager**  
  - Encrypted SQLCipher database to store file,folder and personal passwords.  
  - Protected with your passphrase.

- 🌐 **Web UI**  
  - Flask-based web interface, no need to run CLI commands.  
  - Upload files, manage keys, and encrypt/decrypt with a few clicks.  

---

## 🐳 Run with Docker

You don’t need to install dependencies manually — Penguin Crypt ships as a Docker image.

### Quick Start (Installation and Usage)

Install and Run docker image.

```bash
docker pull aalekh1/penguin-crypt:latest
sudo docker run -d --name penguin-crypt -p 5000:5000 aalekh1/penguin-crypt
```
Go to -> http://localhost:5000 to use the site.

You can stop the container, but if you delete or remove the container db file will be lost.


