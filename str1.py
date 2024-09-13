import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
from twilio.rest import Client
import os
import shutil

# YOLOv8 model
model = YOLO('bale_model.pt')

# Twilio credentials (replace with your actual credentials)
ACCOUNT_SID = "ACb9195ee49a5fddf63130178973ed4185"
AUTH_TOKEN = "533e02dc49560d470fd5beb40ba69471"
FROM_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Variables to store the state
object_count = 0
detection_active = False
 # Define object_count globally

# Directory for temporary storage
temp_dir = "temp_files"
os.makedirs(temp_dir, exist_ok=True)

# Streamlit app
st.title("YOLO Object Detection Desktop App")

# Video upload section
video_file = st.file_uploader("Upload a video for detection", type=["mp4", "mov", "avi"])

# Phone number input
phone_number = st.text_input("Enter your phone number with country code (e.g., +123456789)")

if video_file is not None and phone_number:
    if st.button("Start Detection"):
        # Save uploaded video file
        video_path = os.path.join(temp_dir, video_file.name)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video_file, buffer)

        # Reset count and set detection as active
        detection_active = True
        object_count = 0  # Reset the object count before starting detection

        # Capture video from the saved file path
        cap = cv2.VideoCapture(video_path)

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the codec and create VideoWriter object
        output_path = os.path.join(temp_dir, 'output_detection3.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Define the detection zone (ensure coordinates are correct)
        zone = [(400, 150), (420, 150), (420, 450), (400, 440)]
        progress_bar = st.progress(0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        current_frame = 0
        recent_frames = []

        # Function to check if a frame is recent
        def is_frame_recent(frame_index, recent_frames):
            for i in recent_frames:
                if frame_index - i < 30:
                    return True
            return False

        frame_index = 0  # Initialize the frame index

        while cap.isOpened() and detection_active:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)

            # Draw the detection zone
            cv2.polylines(frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

            for result in results:
                for box in result.boxes:
                    # Filter by confidence
                    if box.conf >= 0.60:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bbox_width = x2 - x1
                        bbox_height = y2 - y1

                        # Draw the bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

                        # Calculate and draw the centroid
                        centroid_x = int((x1 + x2) / 2)
                        centroid_y = int((y1 + y2) / 2)
                        cv2.circle(frame, (centroid_x, centroid_y), 5, (255, 255, 0), -1)
                        size_text = f"W: {bbox_width} H: {bbox_height}"
                        cv2.putText(frame, size_text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                        # Check if the centroid is within the zone
                        if bbox_width > 50 and bbox_height > 50:
                            if cv2.pointPolygonTest(np.array(zone, np.int32), (centroid_x, centroid_y), False) >= 0:
                                if not is_frame_recent(frame_index, recent_frames):
                                    if bbox_height > 75:
                                        object_count += 2  # Large object count as 2
                                    else:
                                        object_count += 1  # Normal object count as 1

                                    recent_frames.append(frame_index)
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 5)

            cv2.putText(frame, f"Count: {object_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

            # Write the frame to output video
            out.write(frame)

            frame_index += 1
            current_frame += 1
            progress_bar.progress(min(current_frame / frame_count, 1.0))

        cap.release()
        out.release()

        # Detection complete
        st.success(f"Detection complete. Total objects detected: {object_count}")
        # st.video(output_path)

    # Separate button to send WhatsApp message
    # if st.button("Send WhatsApp Notification"):
        if phone_number == FROM_WHATSAPP_NUMBER.replace('whatsapp:', ''):
            st.error("Recipient phone number cannot be the same as the sender phone number")
        else:
            try:
                # Send WhatsApp message via Twilio
                message = client.messages.create(
                    body=f'Detection completed. Total objects detected: {object_count}',
                    from_=FROM_WHATSAPP_NUMBER,
                    to=f'whatsapp:{phone_number}'
                )
                st.success(f"WhatsApp message sent to {phone_number} and {object_count}")

                # Clean up temporary files
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))

            except Exception as e:
                st.error(f"Error: {str(e)}")
