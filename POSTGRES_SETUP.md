# PostgreSQL Setup für Render.com (Kostenlos)

## ✅ Was du bekommst

- Kostenlose PostgreSQL-Datenbank (500MB)
- Daten bleiben für immer gespeichert
- Automatische Backups
- Funktioniert auf Render.com UND lokal

---

## 🚀 Setup auf Render.com (5 Minuten)

### Schritt 1: PostgreSQL-Datenbank erstellen

1. Gehe zu: https://dashboard.render.com
2. Klicke **"New +"** → **"PostgreSQL"**
3. Einstellungen:
   - **Name:** `lift-log-db`
   - **Database:** `liftlog`
   - **User:** `liftlog` (automatisch)
   - **Region:** Frankfurt (gleich wie deine App)
   - **PostgreSQL Version:** 16
   - **Datadog API Key:** (leer lassen)
   - **Plan:** **Free**
4. Klicke **"Create Database"**
5. Warte 1-2 Minuten

### Schritt 2: Datenbank mit App verbinden

1. Wenn Datenbank erstellt: Kopiere **"Internal Database URL"**
   (sieht so aus: `postgresql://user:pass@...`)
2. Gehe zu deinem **"lift-log" Web Service**
3. Klicke auf **"Environment"** (links in der Sidebar)
4. Klicke **"Add Environment Variable"**
5. Füge hinzu:
   - **Key:** `DATABASE_URL`
   - **Value:** [Die kopierte Internal Database URL einfügen]
6. Klicke **"Save Changes"**

### Schritt 3: App neu deployen

1. Die App wird automatisch neu gebaut
2. Warte 2-3 Minuten
3. Öffne die App-URL
4. **Fertig!** Daten werden jetzt in PostgreSQL gespeichert ✅

---

## 🏠 Lokales Testen

Die App funktioniert lokal weiterhin mit SQLite:
- **Lokal (Mac):** Nutzt `training.db` (SQLite)
- **Render.com:** Nutzt PostgreSQL

Keine Änderung an deinem Workflow nötig!

---

## 🔍 Datenbank anschauen

### Auf Render.com:

1. Dashboard → PostgreSQL "lift-log-db"
2. Klicke **"Connect"** (oben rechts)
3. Wähle **"External Connection"**
4. Nutze ein Tool wie:
   - **Postico** (Mac): https://eggerapps.at/postico2/
   - **pgAdmin**: https://www.pgadmin.org/
   - **TablePlus**: https://tableplus.com/

### Verbindungsdaten:

Alles steht im Render Dashboard unter "Connections".

---

## 📊 Daten migrieren (von alter SQLite)

Falls du schon Trainingsdaten hast:

```bash
# Auf Render.com:
# Die neue PostgreSQL-DB ist leer, also keine Migration nötig
# Alle alten Daten sind in deiner lokalen training.db gespeichert
```

Wenn du lokale Daten übertragen willst, sag Bescheid!

---

## ❓ Troubleshooting

### Problem: App startet nicht

**Lösung:** Check Logs auf Render
```
Dashboard → lift-log → Logs (oben)
```

### Problem: "relation does not exist"

**Lösung:** Datenbank wird beim ersten Start automatisch initialisiert.
Falls nicht:
1. Render Dashboard → PostgreSQL → "Connect"
2. Nutze psql und führe aus: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
3. App neu starten

### Problem: DATABASE_URL nicht gesetzt

**Lösung:** Environment Variable prüfen:
1. Web Service → Environment
2. DATABASE_URL muss vorhanden sein

---

## 💰 Kosten

- **PostgreSQL Free:** 0€/Monat, 500MB Speicher
- **Web Service Free:** 0€/Monat

**Komplett kostenlos!** ✅

Limit: 500MB = ca. 50.000+ Trainingssets. Mehr als genug!

---

## ✅ Status prüfen

Nach dem Setup solltest du sehen:
- Render Dashboard → PostgreSQL: **"Available"** (grün)
- Web Service → Logs: Keine Errors
- App öffnen → Training funktioniert
- Training loggen → Daten bleiben nach Neustart!
