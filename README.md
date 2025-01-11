# Motion Detection Script

## Project Overview

This Python script implements motion detection using a camera or video stream. It is useful for security applications, surveillance projects, or other scenarios where motion detection in a video is required.

## Features
- Real-time motion detection
- Processing of video recordings or webcam streams
- Flexible customization options for sensitivity and output
- Telegram notifications when motion is detected
- Can be configured to run as a service for automatic recovery after power outages

## Requirements
To run this script, you need the following software and libraries:

- Python 3.x
- OpenCV (cv2)
- NumPy
- `python-telegram-bot` library for Telegram notifications

You can install the dependencies using the following command:
```bash
pip install opencv-python-headless numpy python-telegram-bot
```

## Usage

1. **Clone the repository** (if hosted on GitHub):
    ```bash
    git clone <repository-link>
    ```

2. **Configure the YAML file**:
    - Open the `config.yaml` file in a text editor.
    - Adjust the parameters to suit your needs. Below is an example of typical settings:
      ```yaml
      video_source: 0  # Use 0 for webcam, or provide the path to a video file
      sensitivity: 50  # Adjust sensitivity level (higher = less sensitive)
      save_output: true  # Set to true to save motion-detected video
      output_path: "./videos/output.avi"  # Path to save the output video

      # Telegram Configuration
      telegram:
        bot_token: "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your Telegram Bot Token
        chat_id: "YOUR_TELEGRAM_CHAT_ID"      # Replace with your Telegram Chat ID
      ```
    - Replace `YOUR_TELEGRAM_BOT_TOKEN` with the token of your Telegram bot (you can create one using the BotFather on Telegram).
    - Replace `YOUR_TELEGRAM_CHAT_ID` with your chat ID (you can find this by sending a message to your bot and checking the bot updates).
    - Save the changes to `config.yaml`.

3. **Run the script**:
    ```bash
    python motion_detection.py
    ```

4. **Run as a Service** (Recommended):
    - To ensure the script automatically restarts after a power outage or system reboot, configure it to run as a service.
    - Create a systemd service file (Linux example):
      ```bash
      sudo nano /etc/systemd/system/motion_detection.service
      ```
      Add the following content:
      ```ini
      [Unit]
      Description=Motion Detection Service
      After=network.target

      [Service]
      ExecStart=/usr/bin/python3 /path/to/motion_detection.py
      WorkingDirectory=/path/to/your/project
      Restart=always
      User=your-username

      [Install]
      WantedBy=multi-user.target
      ```
    - Enable and start the service:
      ```bash
      sudo systemctl enable motion_detection.service
      sudo systemctl start motion_detection.service
      ```

5. **Adjust options**: Customize the parameters in the script or the `config.yaml` file to modify sensitivity, output options, or Telegram settings.

### How the Script Works

1. The script accesses a camera or video file as the source. By default, it uses the system's webcam.
2. The video frames are converted to grayscale to enhance processing speed.
3. The background is modeled by comparing consecutive frames, and motion is detected through the difference.
4. Areas of motion are highlighted with rectangles.
5. When motion is detected, a notification is sent via Telegram with details about the detection and, optionally, a snapshot or video.
6. The video with motion markers is displayed in real time.

### Robustness and Reliability
- **Service Execution**: Running the script as a service ensures it automatically restarts in the event of a power outage or system reboot, making it highly reliable for continuous operation.
- **Error Handling**: The script includes basic error handling to ensure stable execution.
- **Telegram Notifications**: Alerts are sent promptly to ensure you are aware of any detected motion, even if you are away from the system.
- **Automatic Recovery**: The combination of service execution and robust configurations minimizes downtime and maximizes reliability.

### Customization Options
- **Sensitivity**:
  Adjust the motion threshold in `config.yaml` to ignore smaller or larger movements.
- **Video Source**:
  Modify the `video_source` parameter in `config.yaml` to analyze a pre-recorded video or use a different camera.
- **Result Storage**:
  Enable or disable saving detected motion videos using the `save_output` parameter in `config.yaml`.
- **Telegram Notifications**:
  Configure the `telegram` section in `config.yaml` to enable or disable Telegram notifications, and set the bot token and chat ID.

### Tips to Avoid Errors

1. **Check Dependencies**:
   Ensure all required libraries are installed before running the script.
2. **Camera Access**:
   - Make sure no other application is blocking the camera.
   - Verify that the camera is enabled in your system settings.
3. **Performance Issues**:
   - If the script runs slowly, reduce the resolution of the video capture.
   - Disable unnecessary background processes on your system.
4. **Background Movements**:
   - Avoid moving objects in the background (e.g., fans or windows with passing cars), as they can trigger motion detection.
5. **Lighting**:
   - Inconsistent lighting (e.g., flickering lights or changing daylight) may cause false positives. Use stable lighting conditions.
6. **Telegram Configuration**:
   - Ensure that the bot token and chat ID in `config.yaml` are correct.
   - Test the bot connection by sending a test message before running the script.

## Example Output
After starting the script, the camera is activated, and areas with motion are highlighted. Notifications about motion detection are sent to Telegram. Motion areas are visually marked in the video.

## Customizations
If you have specific requirements (e.g., saving results, integrating into a larger project, or adjusting motion sensitivity), you can modify the code or the `config.yaml` file. Detailed documentation is included within the code.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact
For questions or issues, feel free to contact me:
- **Email**: d.w.github(at)472a.de
