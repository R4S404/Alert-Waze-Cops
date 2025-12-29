import requests
import time
import json
import os
from datetime import datetime
import threading

# Configuration Telegram
TELEGRAM_BOT_TOKEN = "XXX"
TELEGRAM_CHAT_ID = "XXX"

# Fichiers de configuration
ALERTS_FILE = "/home/XXX/Documents/dev/waze_alerts_history.json"
LOCATIONS_FILE = "/home/xxx/Documents/dev/waze_locations.json"
CONFIG_FILE = "/home/xxx/Documents/dev/waze_config.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.waze.com/live-map/",
    "Origin": "https://www.waze.com"
}

COOKIES = {
    "_appSession": "VALEUR_ICI",
    "waze_uid": "VALEUR_ICI"
}

# Configuration par défaut
DEFAULT_LOCATIONS = [
    {"name": "XXX", "lat": 0.0000, "lon": 0.0000, "rayon": 0.01},
    {"name": "XXX", "lat": 0.0000, "lon": 0.0000, "rayon": 0.003},
    {"name": "XXX ", "lat": 0.0000, "lon": 0.0000, "rayon": 0.002},
    {"name": "XXX", "lat": 0.0000, "lon": 0.0000, "rayon": 0.005}
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"notifications_enabled": True}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"❌ Erreur sauvegarde config: {e}")

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        try:
            with open(LOCATIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    save_locations(DEFAULT_LOCATIONS)
    return DEFAULT_LOCATIONS

def save_locations(locations):
    try:
        with open(LOCATIONS_FILE, 'w') as f:
            json.dump(locations, f, indent=2)
        print(f"✅ Lieux sauvegardés: {len(locations)} point(s)")
    except Exception as e:
        print(f"❌ Erreur sauvegarde lieux: {e}")

def load_notified_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r') as f:
                data = json.load(f)
                current_time = time.time()
                return {k: v for k, v in data.items() if current_time - v < 7200}
        except:
            return {}
    return {}

def save_notified_alerts(alerts_dict):
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts_dict, f)
    except Exception as e:
        print(f"❌ Erreur sauvegarde historique: {e}")

def generate_alert_id(alert, location_name):
    lat = alert.get("location", {}).get("y") or alert.get("geometry", {}).get("coordinates", [None, None])[1]
    lon = alert.get("location", {}).get("x") or alert.get("geometry", {}).get("coordinates", [None, None])[0]
    pub_time = alert.get("pubMillis", 0)
    return f"{location_name}_{lat}_{lon}_{pub_time}"

def format_elapsed_time(pub_millis):
    if not pub_millis:
        return "Inconnu"
    timestamp = int(pub_millis) / 1000
    elapsed_seconds = int(time.time() - timestamp)
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Erreur Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi Telegram: {e}")
        return False

def get_telegram_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Erreur récupération updates: {e}")
        return None

def process_command(message_text, locations, config):
    text = message_text.strip().lower()
    
    if text.startswith("add "):
        try:
            parts = text[4:].split(",")
            if len(parts) != 4:
                return "❌ Format incorrect. Utilisez: add nom, latitude, longitude, rayon"
            
            name = parts[0].strip()
            lat = float(parts[1].strip())
            lon = float(parts[2].strip())
            rayon = float(parts[3].strip())
            
            if any(loc["name"].lower() == name.lower() for loc in locations):
                return f"❌ Un lieu nommé '{name}' existe déjà"
            
            locations.append({"name": name, "lat": lat, "lon": lon, "rayon": rayon})
            save_locations(locations)
            return f"✅ Lieu ajouté: {name} ({lat}, {lon}) - Rayon: {int(rayon*111000)}m"
        except Exception as e:
            return f"❌ Erreur: {e}\nFormat: add nom, latitude, longitude, rayon"
    
    elif text.startswith("remove "):
        name = text[7:].strip()
        original_count = len(locations)
        locations[:] = [loc for loc in locations if loc["name"].lower() != name.lower()]
        
        if len(locations) < original_count:
            save_locations(locations)
            return f"✅ Lieu supprimé: {name}"
        else:
            return f"❌ Lieu '{name}' non trouvé"
    
    elif text == "start bot":
        config["notifications_enabled"] = True
        save_config(config)
        return "✅ Notifications activées 🔔"
    
    elif text == "stop bot":
        config["notifications_enabled"] = False
        save_config(config)
        return "🔕 Notifications désactivées"
    
    elif text == "list":
        if not locations:
            return "📍 Aucun lieu surveillé"
        msg = f"📍 <b>Lieux surveillés ({len(locations)})</b>\n\n"
        for loc in locations:
            rayon_m = int(loc["rayon"] * 111000)
            msg += f"• <b>{loc['name']}</b>\n"
            msg += f"  {loc['lat']}, {loc['lon']}\n"
            msg += f"  Rayon: ~{rayon_m}m\n\n"
        return msg
    
    elif text == "update":
        return manual_update(locations)
    
    elif text == "help":
        return """📖 <b>COMMANDES DISPONIBLES</b>

<b>add nom, lat, lon, rayon</b>
Ajoute un nouveau lieu

<b>remove nom</b>
Supprime un lieu

<b>list</b>
Affiche les lieux surveillés

<b>start bot</b>
Active les notifications

<b>stop bot</b>
Désactive les notifications

<b>help</b>
Affiche cette aide"""
    
    else:
        return "❓ Commande non reconnue."

def telegram_bot_listener(locations, config):
    print("🤖 Bot Telegram démarré - En écoute des commandes...")
    offset = None
    
    while True:
        try:
            updates = get_telegram_updates(offset)
            
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = str(message["chat"]["id"])
                        
                        if chat_id == TELEGRAM_CHAT_ID:
                            text = message.get("text", "")
                            print(f"📨 Commande reçue: {text}")
                            
                            response = process_command(text, locations, config)
                            send_telegram_message(response)
        
        except Exception as e:
            print(f"❌ Erreur bot listener: {e}")
            time.sleep(5)

def get_alerts_for_location(location_name, lat, lon, rayon):
    top = lat + rayon
    bottom = lat - rayon
    left = lon - rayon
    right = lon + rayon
    url = f"https://www.waze.com/live-map/api/georss?top={top}&bottom={bottom}&left={left}&right={right}&env=row&types=alerts,traffic,users"
    try:
        r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=10)
        data = r.json()
        police_alerts = [a for a in data.get("alerts", []) if a.get("type") == "POLICE"]
        return police_alerts
    except Exception as e:
        print(f"❌ Erreur récupération données pour {location_name}: {e}")
        return []

def manual_update(locations):
    message = "🔄 <b>MISE À JOUR MANUELLE WAZE</b>\n"
    message += f"🕒 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}\n\n"

    total_found = 0

    for loc in locations:
        name = loc["name"]
        lat = loc["lat"]
        lon = loc["lon"]
        rayon = loc["rayon"]

        alerts = get_alerts_for_location(name, lat, lon, rayon)

        message += f"📍 <b>{name}</b>\n"

        if not alerts:
            message += "   ➤ Aucune alerte police\n\n"
            continue

        for alert in alerts:
            total_found += 1
            likes = alert.get("nThumbsUp", 0)
            elapsed = format_elapsed_time(alert.get("pubMillis", 0))

            a_lat = alert.get("location", {}).get("y") or alert.get("geometry", {}).get("coordinates", [None, None])[1]
            a_lon = alert.get("location", {}).get("x") or alert.get("geometry", {}).get("coordinates", [None, None])[0]

            if a_lat and a_lon:
                waze_link = f"https://www.waze.com/live-map/directions?ll={a_lat},{a_lon}&navigate=yes"
            else:
                waze_link = "Coordonnées non disponibles"

            message += f"   • Temps: {elapsed}\n"
            message += f"   • Likes: {likes}\n"
            message += f"   • {waze_link}\n\n"

    if total_found == 0:
        message += "✅ Aucune alerte trouvée dans les zones surveillées."

    return message


def main():
    config = load_config()
    locations = load_locations()
    
    bot_thread = threading.Thread(target=telegram_bot_listener, args=(locations, config), daemon=True)
    bot_thread.start()
    
    print("="*70)
    print("🚀 SURVEILLANCE WAZE DÉMARRÉE")
    print(f"Notifications: {'✅ Activées' if config['notifications_enabled'] else '🔕 Désactivées'}")
    print(f"Lieux surveillés: {len(locations)}")
    print("="*70)
    
    while True:
        try:
            print("\n" + "="*70)
            print(f"VÉRIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)
            
            config = load_config()
            
            notified_alerts = load_notified_alerts()
            print(f"📋 {len(notified_alerts)} alerte(s) en mémoire")
            
            total_alerts = 0
            new_alerts = []
            
            for location in locations:
                name = location["name"]
                lat = location["lat"]
                lon = location["lon"]
                rayon = location.get("rayon", 0.01)
                rayon_metres = int(rayon * 111000)
                print(f"\n📍 {name} - Rayon: ~{rayon_metres}m")
                print("-"*70)
                
                police_alerts = get_alerts_for_location(name, lat, lon, rayon)
                
                if police_alerts:
                    print(f"⚠️ {len(police_alerts)} alerte(s) POLICE détectée(s)")
                    for alert in police_alerts:
                        alert_id = generate_alert_id(alert, name)
                        if alert_id not in notified_alerts:
                            total_alerts += 1
                            elapsed = format_elapsed_time(alert.get("pubMillis"))
                            likes = alert.get('nThumbsUp', 0)
                            
                            a_lat = alert.get("location", {}).get("y") or alert.get("geometry", {}).get("coordinates", [None, None])[1]
                            a_lon = alert.get("location", {}).get("x") or alert.get("geometry", {}).get("coordinates", [None, None])[0]
                            
                            new_alerts.append({
                                "lieu": name,
                                "temps": elapsed,
                                "likes": likes,
                                "subtype": alert.get('subType', 'N/A'),
                                "latitude": a_lat,
                                "longitude": a_lon
                            })
                            
                            notified_alerts[alert_id] = time.time()
                            print(f"  🆕 NOUVELLE alerte - Likes: {likes} - Temps: {elapsed}")
                        else:
                            print("  ⏭️  Alerte déjà notifiée")
                else:
                    print("✅ Aucune alerte POLICE dans la zone")
            
            print("\n" + "="*70)
            print(f"RÉSUMÉ: {total_alerts} NOUVELLE(S) alerte(s) POLICE")
            print("="*70)
            
            if total_alerts > 0 and config["notifications_enabled"]:
                print("\n📱 Envoi de la notification Telegram...")

                # 👉 TITRE MODIFIÉ ICI 👈
                lieu_titre = new_alerts[0]["lieu"] if new_alerts else "Alerte"
                message = f"🚨 <b>{lieu_titre}</b> 🚨\n\n"

                message += f"⚠️ <b>{total_alerts} nouvelle(s) alerte(s)</b>\n"
                message += f"🕒 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}\n\n"
                
                for alert in new_alerts:
                    lat = alert['latitude']
                    lon = alert['longitude']
                    if lat and lon:
                        waze_link = f"https://www.waze.com/live-map/directions?ll={lat},{lon}&navigate=yes"
                    else:
                        waze_link = "Coordonnées non disponibles"
                    
                    message += f"📍<b> {alert['lieu']} </b>\n"
                    message += f"   • Temps écoulé: {alert['temps']}\n"
                    message += f"   • Likes: {alert['likes']}\n"
                    message += f"   • Lien Waze: {waze_link}\n\n"
                
                message += "━━━━━━━━━━━━━━━━━━━━\n"
                message += "🔍 Vérifiez Waze pour plus de détails"
                
                if send_telegram_message(message):
                    save_notified_alerts(notified_alerts)

            elif total_alerts > 0 and not config["notifications_enabled"]:
                print("\n🔕 Alertes détectées mais notifications désactivées")
                save_notified_alerts(notified_alerts)
            else:
                print("\n✅ Aucune nouvelle alerte à notifier")
            
            print(f"\n⏰ Prochaine vérification dans 60 secondes...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt de la surveillance")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}")
            print("⏰ Nouvelle tentative dans 60 secondes...")
            time.sleep(60)

if __name__ == "__main__":
    main()
