import cv2
import threading
from gtts import gTTS
from tempfile import NamedTemporaryFile
from playsound import playsound
import pyttsx3 as tts
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Lists for each room

l_kitchenTable = []
l_bookShelf = []
l_bedRoomNightStand = []
l_bedRoomCloset = []
l_diningRoomTable = []

loc_list = ["l_kitchenTable",
            "l_bookShelf",
            "l_bedRoomNightStand",
            "l_bedRoomCloset",
            "l_diningRoomTable"]
obj_list = []

# QR Code Reader


camera_id = 1
delay = 1
window_name = 'OpenCV QR Code'


qcd = cv2.QRCodeDetector()
cap = cv2.VideoCapture(camera_id, cv.CAP_DSHOW)


def qrReader():
    while True:
        ret, frame = cap.read()

        if ret:
            try:
                ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(
                    frame)
            except cv2.error as e:
                print('Error: ', e)
                ret_qr = False
            if ret_qr:
                for s, p in zip(decoded_info, points):
                    if s:
                        if s in loc_list:
                            temp_location_name = str(s)
                            temp_location = eval(s)
                            # print("Temporary Location Stored: " + s)
                        elif (s not in loc_list):
                            if s not in obj_list:
                                obj_list.append(s)
                            try:
                                if s not in temp_location:
                                    # if not in the temp location, remove from any other location
                                    for i in loc_list:
                                        if s in eval(i):
                                            eval(i).remove(s)
                                            print("Removed from " + i)
                                    # add to temp location
                                    temp_location.append(s)
                                    # print out the object and the name of the location it was added to
                                    print(s + "Added to " + temp_location_name)
                            except NameError:
                                print("Location not stored")
                            # print(obj_list)
                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(
                        frame, [p.astype(int)], True, color, 8)
        # cv2.imshow(window_name, frame)


def speak(txt, lang='en'):
    try:
        gTTS(text=txt, lang=lang).write_to_fp(voice := NamedTemporaryFile())
        playsound(voice.name)
        voice.close()
    except Exception as e:
        print(e)
        engine = tts.init(driverName="espeak")
        engine.say(txt)
        engine.runAndWait()
        engine.stop()


def selection():
    selected_index = 0

    while True:
        # get the selected string
        if obj_list:
            selected_string = obj_list[selected_index]
            print(f"Selected: {selected_string[2:]}")

            # get the user input
            user_input = input(
                "Enter 'a' to move left, 'd' to move right, or 'enter' to select: ")

            # if the user enters 'a', move the selection to the left
            if user_input == 'a':
                selected_index = (selected_index - 1) % len(obj_list)

            # if the user enters 'd', move the selection to the right
            elif user_input == 'd':
                selected_index = (selected_index + 1) % len(obj_list)

            # if the user presses enter, find the location of the selected item
            elif user_input == '':
                # find the list the selected string is in
                for location in loc_list:
                    if selected_string in eval(location):
                        print(f"{selected_string[2:]} is in {location[2:]}")
                        speak(f"{selected_string[2:]} is in {location[2:]}")
                        break

        # print("No objects detected")


def databaseSend():
    # Fetch the service account key JSON file contents
    cred = credentials.Certificate(
        'PythonQrReader/QR Implemetation/projectsmartglass-aee0e-firebase-adminsdk-vmdds-842cf32920.json')

    # Initialize the app with a service account, granting admin privileges
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://projectsmartglass-aee0e-default-rtdb.firebaseio.com/'
    })

    # As an admin, the app has access to read and write all data, regradless of Security Rules
    ref = db.reference('/')
    while True:
        # for every object in the list, update the database wtih the object and the location
        if obj_list:
            for i in obj_list:
                # find the location of the object
                for location in loc_list:
                    if i in eval(location):
                        ref.update({
                            i[2:]: location[2:]
                        })

                        break
        else:
            print("HOLDING ON DATA")


# main loop
if __name__ == '__main__':

    qrReaderThread = threading.Thread(target=qrReader)
    qrReaderThread.start()

    selectionThread = threading.Thread(target=selection)
    selectionThread.start()

    databaseSendThread = threading.Thread(target=databaseSend)
    databaseSendThread.start()
    
    speak("Hello, All Systems Operational")
    
    databaseSendThread.join()
    qrReaderThread.join()
    selectionThread.join()
