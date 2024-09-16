import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
from twilio.rest import Client
import os

# YOLOv8 model
model = YOLO('bale_model.pt')

# Twilio credentials (replace with your actual credentials)
ACCOUNT_SID = "ACb9195ee49a5fddf63130178973ed4185"
AUTH_TOKEN = "533e02dc49560d470fd5beb40ba69471"
FROM_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Initialize session state for object count if not already set
if 'object_count' not in st.session_state:
    st.session_state.object_count = 0

if 'detection_active' not in st.session_state:
    st.session_state.detection_active = False

# Streamlit app
st.title("YOLO Object Detection Desktop App")

# RTSP link input section
rtsp_link = st.text_input("Enter RTSP link (e.g., rtsp://<username>:<password>@<ip>:<port>/<stream>)")

# Phone number input
phone_number = st.text_input("Enter your phone number with country code (e.g., +123456789)")

if rtsp_link and phone_number:
    if st.button("Start Detection"):
        # Reset count and set detection as active
        st.session_state.detection_active = True
        st.session_state.object_count = 0  # Reset the object count before starting detection

        # Capture video from the RTSP link
        cap = cv2.VideoCapture(rtsp_link)

        # Check if the RTSP stream is accessible
        if not cap.isOpened():
            st.error("Error: Unable to access the RTSP stream. Check the link and try again.")
        else:
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Define the codec and create VideoWriter object
            output_path = 'output_detection3.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Define the detection zone (ensure coordinates are correct)
            zone = [(400, 150), (420, 150), (420, 450), (400, 440)]
            progress_bar = st.progress(0)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None
            current_frame = 0
            recent_frames = []

            # Function to check if a frame is recent
            def is_frame_recent(frame_index, recent_frames):
                for i in recent_frames:
                    if frame_index - i < 30:
                        return True
                return False

            frame_index = 0  # Initialize the frame index

            while cap.isOpened() and st.session_state.detection_active:
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
                                            st.session_state.object_count += 2  # Large object count as 2
                                        else:
                                            st.session_state.object_count += 1  # Normal object count as 1

                                        recent_frames.append(frame_index)
                                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 5)

                cv2.putText(frame, f"Count: {st.session_state.object_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

                # Write the frame to output video
                out.write(frame)

                frame_index += 1
                current_frame += 1
                if frame_count:
                    progress_bar.progress(min(current_frame / frame_count, 1.0))

            cap.release()
            out.release()

            # Detection complete
            st.success(f"Detection complete. Total objects detected: {st.session_state.object_count}")

    # Separate button to send WhatsApp message
    if st.button("Send WhatsApp Notification"):
        if phone_number == FROM_WHATSAPP_NUMBER.replace('whatsapp:', ''):
            st.error("Recipient phone number cannot be the same as the sender phone number")
        else:
            try:
                # Send WhatsApp message via Twilio
                message = client.messages.create(
                    body=f'Detection completed. Total objects detected: {st.session_state.object_count}',
                    from_=FROM_WHATSAPP_NUMBER,
                    to=f'whatsapp:{phone_number}'
                )
                st.success(f"WhatsApp message sent to {phone_number} with {st.session_state.object_count} objects detected.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
