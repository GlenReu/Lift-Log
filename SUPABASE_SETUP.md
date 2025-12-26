# Supabase Setup (Dauerhaft Kostenlos)

## ✅ Was du bekommst

- **Dauerhaft kostenlose PostgreSQL-Datenbank** (kein Ablaufdatum!)
- 500MB Speicher
- Automatische Backups
- Sehr zuverlässig und schnell

---

## 🚀 Setup (5 Minuten)

### Schritt 1: Supabase-Projekt erstellen

1. Gehe zu: **https://supabase.com**
2. Klicke **"Start your project"** → **Sign up**
3. Registriere dich mit GitHub oder E-Mail (kostenlos)
4. Nach dem Login: Klicke **"New Project"**

### Schritt 2: Projekt konfigurieren

1. **Organization:** Erstelle eine neue (z.B. "Personal")
2. **Project name:** `lift-log`
3. **Database Password:** Wähle ein sicheres Passwort
   - ⚠️ **WICHTIG:** Speichere dieses Passwort irgendwo sicher!
4. **Region:** Wähle **Frankfurt** (näher zu Render.com)
5. **Pricing Plan:** Free (schon ausgewählt)
6. Klicke **"Create new project"**
7. Warte 1-2 Minuten (Datenbank wird erstellt)

### Schritt 3: DATABASE_URL kopieren

1. Klicke auf **"Project Settings"** (Zahnrad-Icon links unten)
2. Gehe zu **"Database"** (in der linken Sidebar)
3. Scrolle runter zu **"Connection string"**
4. Wähle **"URI"** (nicht "Session mode")
5. Kopiere die komplette URL

   Sie sieht so aus:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```

6. **Ersetze `[YOUR-PASSWORD]`** mit deinem Database Password aus Schritt 2

### Schritt 4: In Render.com verbinden

1. Gehe zu: **https://dashboard.render.com**
2. Öffne deinen **"lift-log"** Web Service
3. Klicke auf **"Environment"** (links in der Sidebar)
4. Suche **DATABASE_URL** (falls schon vorhanden)
   - Falls vorhanden: Klicke "Edit" und ersetze den Wert
   - Falls nicht vorhanden: Klicke **"Add Environment Variable"**
     - **Key:** `DATABASE_URL`
     - **Value:** [Die kopierte Supabase URL einfügen]
5. Klicke **"Save Changes"**

### Schritt 5: Deployment abwarten

1. Render wird automatisch neu deployen (2-3 Minuten)
2. Warte bis "Deploy successful" angezeigt wird
3. Öffne deine App-URL
4. **Fertig!** Daten werden jetzt dauerhaft in Supabase gespeichert ✅

---

## 🔍 Datenbank anschauen

### In Supabase Dashboard:

1. Gehe zu deinem Supabase-Projekt
2. Klicke **"Table Editor"** (links)
3. Hier siehst du alle Tabellen:
   - `training_plans`
   - `exercises`
   - `workouts`
   - `sets`
   - usw.

### Daten direkt ansehen:

1. Klicke auf eine Tabelle (z.B. "exercises")
2. Du siehst alle Einträge in einer Tabellenansicht
3. Kannst auch direkt bearbeiten (Vorsicht!)

---

## 📊 Daten von alter Datenbank migrieren (Optional)

Falls du schon Trainingsdaten in der Render PostgreSQL hast:

### Export aus Render:

1. Render Dashboard → PostgreSQL "lift-log-db"
2. Klicke **"Connect"** → External Connection
3. Nutze `pg_dump` um Daten zu exportieren:
   ```bash
   pg_dump <RENDER_DATABASE_URL> > backup.sql
   ```

### Import in Supabase:

1. Supabase Dashboard → SQL Editor
2. Öffne `backup.sql` und kopiere den Inhalt
3. Füge ein und klicke "Run"

**ODER einfacher:** Beginne neu - die alte Render DB läuft ja noch 30 Tage!

---

## ❓ Troubleshooting

### Problem: App startet nicht

**Lösung:** Check Render Logs
```
Dashboard → lift-log → Logs (oben)
```

Suche nach Fehlermeldungen mit "database" oder "connection"

### Problem: "could not connect to server"

**Lösung:** DATABASE_URL prüfen
1. Ist das Password richtig ersetzt? (Kein `[YOUR-PASSWORD]` mehr)
2. Ist die komplette URL kopiert?
3. Keine Leerzeichen am Anfang/Ende?

### Problem: Tabellen existieren nicht

**Lösung:** App startet und erstellt Tabellen automatisch
- Einfach einmal die App-URL aufrufen
- Tabellen werden beim ersten Start erstellt

---

## 💰 Kosten

- **Supabase Free:** 0€/Monat, 500MB Speicher, **dauerhaft kostenlos**
- **Render Web Service Free:** 0€/Monat

**Komplett kostenlos - für immer!** ✅

Limit: 500MB = ca. 50.000+ Trainingssets. Mehr als genug!

---

## 🔒 Sicherheit

- Supabase hat automatische Backups
- Daten sind verschlüsselt
- Du kannst jederzeit Backups erstellen:
  - Supabase Dashboard → Database → Backups

---

## ✅ Status prüfen

Nach dem Setup solltest du sehen:
- Supabase Dashboard → Project: **"Active"** (grün)
- Render Web Service → Logs: Keine Connection Errors
- App öffnen → Training funktioniert
- Training loggen → Daten bleiben gespeichert!
- Supabase Table Editor → Daten erscheinen in Tabellen

---

## 📝 Wichtige Links

- **Supabase Dashboard:** https://supabase.com/dashboard
- **Supabase Docs:** https://supabase.com/docs
- **Render Dashboard:** https://dashboard.render.com

---

## 🎉 Vorteile vs. Render PostgreSQL

| Feature | Render PostgreSQL | Supabase |
|---------|-------------------|----------|
| Kostenlos | 90 Tage | **Dauerhaft** ✅ |
| Speicher | 500MB | 500MB |
| Backups | Ja | **Automatisch** ✅ |
| UI | Nur via psql | **Table Editor** ✅ |
| Limits | Nach 90 Tagen weg | **Keine** ✅ |

Viel Erfolg! 🚀
