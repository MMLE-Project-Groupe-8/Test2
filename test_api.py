from API_group08_with_password import BioreactorClient, USER, PASSWORD, BASE_URL
import json

# API-Client initialisieren
client = BioreactorClient(BASE_URL)

print("=" * 60)
print("API TEST - Bioreactor Simulation")
print("=" * 60)

# 1. Anmelden
print("\n1. Anmelden...")
try:
    client.login(USER, PASSWORD)
    print("✓ Login erfolgreich!")
except Exception as e:
    print(f"✗ Login fehlgeschlagen: {e}")
    exit(1)

# 2. Simulation ausführen
print("\n2. Starte Bioreaktor-Simulation (micro scale)...")
try:
    # Parameter für die Simulation
    result = client.run(
        scale="micro",      # Skalierung: micro oder macro
        T=30.0,             # Temperatur
        pH=6.5,             # pH-Wert
        F1=0.5,             # Flow-Rate 1
        F2=0.5,             # Flow-Rate 2
        F3=0.5              # Flow-Rate 3
    )
    print("✓ Simulation erfolgreich ausgeführt!")
    print("\n3. Abfrageergebnis:")
    print("-" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 60)
except Exception as e:
    print(f"✗ Simulation fehlgeschlagen: {e}")
    exit(1)

# 3. Historie abrufen (optional)
print("\n4. Abrufen der Simulationshistorie...")
try:
    history = client.history()
    print(f"✓ Gesamt durchgeführte Simulationen: {len(history)}")
    if history:
        print("\nLetzte 3 Simulationen:")
        for i, item in enumerate(history[-3:], 1):
            print(f"  {i}. {json.dumps(item, indent=6, ensure_ascii=False)}")
except Exception as e:
    print(f"✗ Fehler beim Abrufen der Historie: {e}")

print("\n" + "=" * 60)
print("Test abgeschlossen!")
print("=" * 60)
