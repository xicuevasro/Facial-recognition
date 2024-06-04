import os
import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="setsisuser",
        password="setsis2021",
        database="maison"
    )
    print("Database connection successful")
except mysql.connector.Error as err:
    print(f"Database connection error: {err}")
    exit(1)

cursor = db.cursor()

personnes = [
    {"id": 1, "nom": "Ximena", "chemin": "dataset/Ximena"},
    {"id": 2, "nom": "Karima", "chemin": "dataset/Karima"}
]

for personne in personnes:
    if os.path.isdir(personne["chemin"]):
        fichiers = os.listdir(personne["chemin"])
        for fichier in fichiers:
            chemin_fichier = os.path.join(personne["chemin"], fichier)
            if os.path.isfile(chemin_fichier):
                with open(chemin_fichier, 'rb') as file:
                    photo_blob = file.read()
                insert_photo = ("INSERT INTO habitants (id, nom, photo) "
                                "VALUES (%s, %s, %s)")
                cursor.execute(insert_photo, (personne["id"], personne["nom"], photo_blob))
        db.commit()
    else:
        print(f"Le répertoire {personne['chemin']} n'existe pas.")

db.close()
print("Database connection closed.")