# import streamlit as st
# import cv2
# import numpy as np
# from ultralytics import YOLO
# from twilio.rest import Client
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import os

# # YOLOv8 model
# model = YOLO('bale_model.pt')

# # Twilio credentials (replace with your actual credentials)
# ACCOUNT_SID = "ACb9195ee49a5fddf63130178973ed4185"
# AUTH_TOKEN = "567e93b1987e0340c8860161b35cc650"
# FROM_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
# client = Client(ACCOUNT_SID, AUTH_TOKEN)

# # Email credentials (replace with your actual credentials)
# EMAIL_ADDRESS = "prophetnithya@gmail.com"
# EMAIL_PASSWORD = "mkbx oqnz igzd gfxo"

# # Initialize session state for object count if not already set
# if 'object_count' not in st.session_state:
#     st.session_state.object_count = 0

# if 'detection_active' not in st.session_state:
#     st.session_state.detection_active = False

# if 'stop_requested' not in st.session_state:
#     st.session_state.stop_requested = False

# # Streamlit app
# st.title("YOLO Object Detection Desktop App")

# # HTTP stream or video file input section
# input_type = st.radio("Choose input type:", ("HTTP Stream", "Video File"))

# http_stream = None
# uploaded_file = None

# if input_type == "HTTP Stream":
#     # User inputs the HTTP stream URL instead of RTSP link
#     http_stream = st.text_input("Enter HTTP stream link (e.g., http://192.168.0.100:8080/video)")
# else:
#     uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# # Phone number input (Static phone number)
# phone_number = '+919442493256'

# # Email addresses input (Allow up to 10)
# email_addresses = st.text_area("Enter up to 10 email addresses separated by commas")

# # Convert entered email addresses into a list
# recipient_emails = [email.strip() for email in email_addresses.split(',') if email.strip()]

# # Ensure the user inputs up to 10 valid email addresses
# if len(recipient_emails) > 10:
#     st.error("You can only enter up to 10 email addresses.")

# # Function to send WhatsApp message
# def send_whatsapp_message(count):
#     try:
#         message = client.messages.create(
#             body=f'Detection completed. Total objects detected: {count}',
#             from_=FROM_WHATSAPP_NUMBER,
#             to=f'whatsapp:{phone_number}'
#         )
#         st.success(f"WhatsApp message sent to {phone_number} with {count} objects detected.")
#     except Exception as e:
#         st.error(f"Error sending WhatsApp message: {str(e)}")

# # Function to send email notification
# def send_email_notification(count):
#     if recipient_emails:
#         try:
#             # Set up the email parameters
#             msg = MIMEMultipart()
#             msg['From'] = EMAIL_ADDRESS
#             msg['To'] = ", ".join(recipient_emails)  # Join recipients as comma-separated list
#             msg['Subject'] = "Detection Report"
#             body = f"Detection completed. Total objects detected: {count}"
#             msg.attach(MIMEText(body, 'plain'))

#             # Send emails to the list of recipients
#             server = smtplib.SMTP('smtp.gmail.com', 587)
#             server.starttls()
#             server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#             server.sendmail(EMAIL_ADDRESS, recipient_emails, msg.as_string())

#             st.success(f"Email sent to {len(recipient_emails)} recipients successfully!")
#         except Exception as e:
#             st.error(f"Failed to send email. Error: {e}")
#         finally:
#             server.quit()  # Terminate the SMTP session
#     else:
#         st.error("Please enter at least one valid email address.")

# # Video detection process
# def run_detection():
#     if http_stream:
#         cap = cv2.VideoCapture(http_stream)
#     elif uploaded_file:
#         temp_video_path = "temp_uploaded_video.mp4"
#         with open(temp_video_path, "wb") as f:
#             f.write(uploaded_file.read())
#         cap = cv2.VideoCapture(temp_video_path)

#     if not cap.isOpened():
#         st.error("Error: Unable to access the video stream. Check the input and try again.")
#         return

#     fps = int(cap.get(cv2.CAP_PROP_FPS))
#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#     folder_path = 'output_videos'
#     os.makedirs(folder_path, exist_ok=True)
#     output_path = os.path.join(folder_path, 'output_detection.mp4')
#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

#     zone = [(1040, 21), (1139, 19), (1141, 1026), (1038, 1028)]
#     progress_bar = st.progress(0)
#     frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None
#     current_frame = 0
#     recent_frames = []
#     frame_index = 0

#     def is_frame_recent(frame_index, recent_frames):
#         for i in recent_frames:
#             if frame_index - i < 30:
#                 return True
#         return False

#     while cap.isOpened() and st.session_state.detection_active:
#         if st.session_state.stop_requested:
#             break

#         ret, frame = cap.read()
#         if not ret:
#             break

#         results = model(frame)
#         cv2.polylines(frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

#         for result in results:
#             for box in result.boxes:
#                 if box.conf >= 0.60:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     bbox_width = x2 - x1
#                     bbox_height = y2 - y1
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
#                     centroid_x = int((x1 + x2) / 2)
#                     centroid_y = int((y1 + y2) / 2)
#                     cv2.circle(frame, (centroid_x, centroid_y), 5, (255, 255, 0), -1)

#                     if bbox_width > 50 and bbox_height > 50:
#                         if cv2.pointPolygonTest(np.array(zone, np.int32), (centroid_x, centroid_y), False) >= 0:
#                             if not is_frame_recent(frame_index, recent_frames):
#                                 if bbox_height > 75:
#                                     st.session_state.object_count += 2
#                                 else:
#                                     st.session_state.object_count += 1

#                                 recent_frames.append(frame_index)
#                                 cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 5)

#         cv2.putText(frame, f"Count: {st.session_state.object_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
#         out.write(frame)
#         frame_index += 1
#         current_frame += 1
#         if frame_count:
#             progress_bar.progress(min(current_frame / frame_count, 1.0))

#     cap.release()
#     out.release()

#     if uploaded_file:
#         os.remove(temp_video_path)

#     st.success(f"Detection complete. Total objects detected: {st.session_state.object_count}")
#     st.info(f"Video saved to {output_path}")

# if (http_stream or uploaded_file) and phone_number:
#     if st.button("Start Detection"):
#         st.session_state.detection_active = True
#         st.session_state.stop_requested = False
#         st.session_state.object_count = 0
#         run_detection()

#     if st.button("Stop Detection"):
#         st.session_state.detection_active = False
#         st.session_state.stop_requested = True
#         send_whatsapp_message(st.session_state.object_count)
#         send_email_notification(st.session_state.object_count)




import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# YOLOv8 model
model = YOLO('bale_model.pt')

# Twilio credentials (replace with your actual credentials)
ACCOUNT_SID = "ACb9195ee49a5fddf63130178973ed4185"
AUTH_TOKEN = "fae8b5a4d02b2c37ed1455d9d6cffe9c"
FROM_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Email credentials (replace with your actual credentials)
EMAIL_ADDRESS = "prophetnithya@gmail.com"
EMAIL_PASSWORD = "mkbx oqnz igzd gfxo"

# Initialize session state for object count if not already set
if 'object_count' not in st.session_state:
    st.session_state.object_count = 0

if 'detection_active' not in st.session_state:
    st.session_state.detection_active = False

# Streamlit app
st.title("YOLO Object Detection Desktop App")

# HTTP stream or video file input section
input_type = st.radio("Choose input type:", ("HTTP Stream", "Video File"))

http_stream = None
uploaded_file = None

if input_type == "HTTP Stream":
    # User inputs the HTTP stream URL instead of RTSP link
    http_stream = st.text_input("Enter HTTP stream link (e.g., http://192.168.0.100:8080/video)")
else:
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Phone number input (Static phone number)
phone_number = '+919442493256'

# Email addresses input (Allow up to 10)
email_addresses = st.text_area("Enter up to 10 email addresses separated by commas")

# Convert entered email addresses into a list
recipient_emails = [email.strip() for email in email_addresses.split(',') if email.strip()]

# Ensure the user inputs up to 10 valid email addresses
if len(recipient_emails) > 10:
    st.error("You can only enter up to 10 email addresses.")

if (http_stream or uploaded_file) and phone_number:
    if st.button("Start Detection"):
        # Reset count and set detection as active
        st.session_state.detection_active = True
        st.session_state.object_count = 0  # Reset the object count before starting detection

        # Capture video from the HTTP stream or uploaded file
        if http_stream:
            cap = cv2.VideoCapture(http_stream)
        elif uploaded_file:
            temp_video_path = "temp_uploaded_video.mp4"
            with open(temp_video_path, "wb") as f:
                f.write(uploaded_file.read())
            cap = cv2.VideoCapture(temp_video_path)

        # Check if the video stream is accessible
        if not cap.isOpened():
            st.error("Error: Unable to access the video stream. Check the input and try again.")
        else:
            # Define the stop button
            stop_button = st.button("Stop Detection")

            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Define the codec and create VideoWriter object
            folder_path = 'output_videos'  # Specify folder for saving videos
            os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
            output_path = os.path.join(folder_path, 'output_detection.mp4')  # Save video in the folder
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Define the detection zone
            zone = [(1040, 21), (1139, 19), (1141, 1026), (1038, 1028)]
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

                # Check if the stop button has been pressed
                if stop_button:
                    st.session_state.detection_active = False

            cap.release()
            out.release()

            # Clean up temp video file if uploaded
            if uploaded_file:
                os.remove(temp_video_path)

            # Detection complete
            st.success(f"Detection complete. Total objects detected: {st.session_state.object_count}")
            st.info(f"Video saved to {output_path}")

            # Send WhatsApp message via Twilio
            try:
                message = client.messages.create(
                    body=f'Detection completed. Total objects detected: {st.session_state.object_count}',
                    from_=FROM_WHATSAPP_NUMBER,
                    to=f'whatsapp:{phone_number}'
                )
                st.success(f"WhatsApp message sent to {phone_number} with {st.session_state.object_count} objects detected.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

            # Send email notification
            if recipient_emails:
                try:
                    # Set up the email parameters
                    msg = MIMEMultipart()
                    msg['From'] = EMAIL_ADDRESS
                    msg['To'] = ", ".join(recipient_emails)  # Join recipients as comma-separated list
                    msg['Subject'] = "Detection Report"
                    body = f"Detection completed. Total objects detected: {st.session_state.object_count}"
                    msg.attach(MIMEText(body, 'plain'))

                    # Send emails to the list of recipients
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

                    server.sendmail(EMAIL_ADDRESS, recipient_emails, msg.as_string())  # Send email to all recipients in one call

                    st.success(f"Email sent to {len(recipient_emails)} recipients successfully!")
                except Exception as e:
                    st.error(f"Failed to send email. Error: {e}")
                finally:
                    server.quit()  # Terminate the SMTP session
            else:
                st.error("Please enter at least one valid email address.")


