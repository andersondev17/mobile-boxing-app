# Boxing Training API & Mobile App

## ⚖️ Stability & Runtime Requirements

To ensure predictable behavior and reproducibility during human testing, the following environment constraints are strictly enforced:

### 🐍 Python Environment
- **Locked Version:** **Python 3.10.x** or **Python 3.11.x**.
- **Reason:** MediaPipe and PyTorch dependencies are stable on these versions. Newer versions (e.g., 3.14) are NOT supported and may cause initialization failures.
- **Setup:**
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # or .venv\Scripts\activate
  pip install -r apps/backend/app/requirements.txt
  ```

### 🌍 Environment Modes (`ENV_MODE`)
The backend is now explicit about its dependency requirements. Set `ENV_MODE` in your `.env` file:
- `local_real` (Default): Requires running instances of **MongoDB (27017)** and **Redis (6379)**. The system will FAIL if these services are missing.
- `dev_mock`: Allows the system to fallback to in-memory mocks (`mongomock-motor`, `fakeredis`) for UI/Flow testing without infrastructure.

### 📱 Mobile Connectivity
- The mobile app dynamically resolves the backend URL.
- DO NOT hardcode local IPs in the `.env` file unless absolutely necessary for specific network configurations.
- Default behavior uses `EXPO_PUBLIC_LOCAL_IP` variable or auto-detection.

### 🛠️ Network Robustness
- **Jitter Buffer:** A 3-frame reordering window is implemented in the WebSocket route to handle out-of-order biometric data packets.


