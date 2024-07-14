import cv2
import vlc

face_detector = cv2.CascadeClassifier('face_default.xml')
eye_detector = cv2.CascadeClassifier('eye.xml')

media = vlc.MediaPlayer("test.mp4")
media.play()

webcam = cv2.VideoCapture(0)

while True:
    successful_frame_read, frame = webcam.read()

    if not successful_frame_read:
        break

    grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(grayscale_frame, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        the_face = frame[y:y + h, x:x + w]
        grayscale_face = cv2.cvtColor(the_face, cv2.COLOR_BGR2GRAY)

        eyes = eye_detector.detectMultiScale(grayscale_face, scaleFactor=1.1, minNeighbors=3)

        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(the_face, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

        if len(eyes) < 1:
            cv2.putText(frame, 'Sleeping', (x, y + h + 40), fontScale=1, fontFace=cv2.FONT_HERSHEY_PLAIN,
                        color=(255, 255, 255))
            media.pause()

    cv2.imshow('Eye Detector', frame)
    key = cv2.waitKey(1)

    if key == 27:  # Press 'Esc' key to exit
        break

webcam.release()
cv2.destroyAllWindows()
