import face_recognition
import cv2
import numpy as np
import mysql.connector as mysql
import RPi.GPIO as GPIO
import time
from datetime import datetime

GPIO.setmode(GPIO.BOARD)           #GPIO - utilizando o numero do pino
GPIO.setwarnings(False)            #desabilitar mensagens

led_vm = 11
led_vr = 12
GPIO.setup(led_vm,GPIO.OUT)
GPIO.setup(led_vr,GPIO.OUT)

# Faz a conexao com o banco de dados
db = mysql.connect(host="localhost", user="root", passwd="vitor123", db="face_recognition")
cursor = db.cursor()

# Abre a captura de video na camera
video_capture = cv2.VideoCapture(0)

# Configura as imagens de referencia para reconhecer os rostos
vitor_image = face_recognition.load_image_file("/home/pi/Desktop/UNIP/Faces/vitor.jpg")
vitor_face_encoding = face_recognition.face_encodings(vitor_image)[0]

alessandro_image = face_recognition.load_image_file("/home/pi/Desktop/UNIP/Faces/alessandro.jpg")
alessandro_face_encoding = face_recognition.face_encodings(alessandro_image)[0]

ney_image = face_recognition.load_image_file("/home/pi/Desktop/UNIP/Faces/ney.jpg")
ney_face_encoding = face_recognition.face_encodings(ney_image)[0]

#douglas_image = face_recognition.load_image_file("/home/pi/Desktop/UNIP/Faces/douglas.jpg")
#douglas_face_encoding = face_recognition.face_encodings(douglas_image)[0]

# Cria as matrizes dos rostos e nomes
known_face_encodings = [
    vitor_face_encoding,
    alessandro_face_encoding,
    ney_face_encoding,
    #douglas_face_encoding
]

known_face_names = [
    "Vitor",
    "Alessandro",
    "Ney",
    #"Douglas"
]

# Inicializa as variaveis
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
name_old = ""

while True:
    # Seta um unico quadro de video
    ret, frame = video_capture.read()

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    rgb_small_frame = small_frame[:, :, ::-1]

    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Desconhecido"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)

    process_this_frame = not process_this_frame

    # Exibe os resultados
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Desenha o retangulo ao redor da face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Desenha o nome ao redor da face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        
        if name == "Desconhecido":
            GPIO.output(led_vm,GPIO.HIGH)
            #time.sleep(2)
            GPIO.output(led_vr,GPIO.LOW)
        else:
            GPIO.output(led_vr,GPIO.HIGH)
            #time.sleep(2)
            GPIO.output(led_vm,GPIO.LOW)
        
        if name != name_old:
            query = "INSERT INTO movimentacoes (cod_usuario, data) VALUES (%s,%s)"
            date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            values = (name, date_now)
            cursor.execute(query, values)
            db.commit()
            name_old = name
            print(cursor.rowcount, "Registro Inserido")

    cv2.imshow('Video', frame)

    # Se pressionado a tecla 'q' sai do programa
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a webcam
video_capture.release()
cv2.destroyAllWindows()