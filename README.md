# 🚨 Alert Waze Cops

Bot Python permettant de **surveiller automatiquement les alertes POLICE sur Waze** autour de zones géographiques définies, avec **notifications en temps réel via Telegram** et **pilotage du bot directement depuis Telegram**.


## ✨ Fonctionnalités

- 📍 Surveillance de **plusieurs zones géographiques**
- 🚓 Détection des **alertes POLICE** sur Waze
- 🔔 Notifications Telegram automatiques
- 🧠 Mémoire des alertes déjà envoyées (anti-spam)
- 🤖 **Commandes Telegram** pour gérer le bot à distance
- 🔄 Mise à jour manuelle à la demande
- 🗂️ Sauvegarde locale (JSON) de la configuration et de l’historique

---

## 🧰 Technologies utilisées

- Python 3
- API Telegram Bot
- API Waze (Live Map – GeoRSS)
- `requests`, `threading`, `json`

---

## 📦 Installation

### 1️⃣ Prérequis

- Python 3.8+
- Un bot Telegram (via @BotFather)
- `pip`

### 2️⃣ Dépendances

```bash
pip install requests
```

### 3️⃣ Lancement 

```bash
python main.py
```