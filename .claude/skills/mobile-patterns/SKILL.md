---
name: mobile-patterns
description: Apply this skill when writing React Native / Expo code for the boxing app: hooks, Zustand stores, API service calls, TFLite frame processors, WebSocket landmark streaming, or offline buffer. Trigger on: "react native", "expo", "mobile", "frame processor", "tflite", "vision camera", "zustand", "websocket client", "offline buffer", "async storage", "mobile screen", "expo router", "hook", "mobile service".
---

# Mobile Patterns — mobile-boxing-app

## Stack
- React Native + Expo SDK 54 + Expo Dev Build (NOT Expo Go)
- Expo Router (file-based routing in `app/`)
- Zustand 5 for global state
- react-native-vision-camera v4.7.2 for frame processors
- TFLite on-device for landmark extraction
- `lib/api/client.ts` for all API calls (auto-refresh)

## Directory structure
```
apps/mobile/
├── app/                   # Expo Router screens
│   ├── (auth)/            # Login, register screens
│   ├── (tabs)/            # Bottom tab navigation
│   └── exercises/
│       ├── realtime/      # WebSocket analysis (current: base64, must migrate to landmarks)
│       └── technique/     # Technique guides
├── lib/
│   ├── api/
│   │   ├── auth.ts        # Google OAuth PKCE + JWT auth functions
│   │   └── client.ts      # API client with auto-refresh interceptor
│   └── config/env.ts      # Platform-aware URL detection
├── store/
│   └── authStore.ts       # Zustand auth store (persisted to AsyncStorage)
├── services/
│   └── realtimePoseService.ts  # WebSocket client (needs migration to landmarks)
├── hooks/
│   └── useSavedExercises.ts    # SQLite local exercise storage
└── interfaces/
    └── interfaces.d.ts    # JabRealtimeFramePayload, JabRealtimeServerMessage, etc.
```

## API calls: always via lib/api/client.ts

```typescript
import { apiClient } from '@/lib/api/client'

// GET request
const exercises = await apiClient.get('/exercises/')

// POST request
const response = await apiClient.post('/consent/', {
  consent_type: 'biometric_data',
  granted: true
})

// Client handles: Authorization header injection, 401 token refresh, retry
```

Never use raw `fetch()` for authenticated calls — always `apiClient`.

## Zustand store pattern

```typescript
// store/poseStore.ts
import { create } from 'zustand'

interface PoseState {
  isConnected: boolean
  lastFeedback: string | null
  jabCount: number
  connect: (userId: string) => void
  disconnect: () => void
  setFeedback: (feedback: string) => void
}

export const usePoseStore = create<PoseState>((set) => ({
  isConnected: false,
  lastFeedback: null,
  jabCount: 0,
  connect: (userId) => { /* ... */ },
  disconnect: () => set({ isConnected: false }),
  setFeedback: (feedback) => set({ lastFeedback: feedback }),
}))
```

For stores needing persistence: wrap with `persist` middleware + `AsyncStorage`.

## WebSocket pattern (landmark-based — correct approach)

```typescript
// Correct payload format (backend expects this)
const payload = {
  landmarks: landmarks,  // Array of 33 {x, y, z} objects from TFLite
  fps: 30,
  frame_index: frameCount,
  user_id: userId,
}
ws.send(JSON.stringify(payload))

// Response from backend
interface ServerMessage {
  feedback: string | null
  jab_detected: boolean
  frame_index: number | null
  tracking_state: 'searching' | 'tracking' | 'idle'
}
```

## TFLite frame processor (target architecture for Phase 1)

```typescript
import { useCameraDevice, useFrameProcessor } from 'react-native-vision-camera'
import { runOnJS } from 'react-native-reanimated'

// TFLite runs on JS worklet thread — must not block UI thread
const frameProcessor = useFrameProcessor((frame) => {
  'worklet'
  // Run TFLite inference
  const landmarks = runTFLiteInference(frame)  // returns [{x,y,z}] x33
  if (landmarks) {
    runOnJS(sendLandmarks)(landmarks)  // cross thread bridge
  }
}, [])

// sendLandmarks runs on JS thread
const sendLandmarks = (landmarks: Landmark[]) => {
  poseService.sendLandmarks(landmarks, frameCounter.current++)
}
```

## Offline buffer pattern (for WiFi reconnection)

```typescript
const offlineBuffer: BufferedFrame[] = []

const sendLandmarks = (landmarks: Landmark[], frameIndex: number) => {
  if (!poseService.isConnected()) {
    offlineBuffer.push({
      landmarks,
      timestamp: Date.now(),  // original timestamp for accurate analytics
      frameIndex,
    })
    return
  }

  // Burst buffered frames on reconnect
  while (offlineBuffer.length > 0) {
    const buffered = offlineBuffer.shift()!
    poseService.send({ ...buffered, buffered: true })
  }

  poseService.send({ landmarks, timestamp: Date.now(), frameIndex })
}
```

## BLE reconnection pattern

```typescript
const BLE_RETRY_INTERVALS = [1000, 2000, 4000, 8000, 16000, 30000]
let retryIndex = 0

const reconnectBLE = async () => {
  if (retryIndex >= BLE_RETRY_INTERVALS.length) {
    console.warn('BLE: max retries reached')
    return
  }
  await new Promise(r => setTimeout(r, BLE_RETRY_INTERVALS[retryIndex++]))
  try {
    await bleManager.connect(deviceId)
    retryIndex = 0  // reset on success
  } catch {
    reconnectBLE()  // recursive retry
  }
}
```

## Expo Router navigation patterns

```typescript
import { router } from 'expo-router'

// Navigate to screen
router.push('/(tabs)/home')

// Navigate with params
router.push({ pathname: '/exercises/[id]', params: { id: exerciseId } })

// Replace (no back button)
router.replace('/(auth)/login')
```

## Environment detection (lib/config/env.ts)

```typescript
import Constants from 'expo-constants'

const isAndroidEmulator = Constants.deviceName?.includes('sdk_gphone')

export const API_BASE_URL = (() => {
  if (process.env.EXPO_PUBLIC_ENV === 'production') {
    return process.env.EXPO_PUBLIC_API_URL
  }
  const ip = process.env.EXPO_PUBLIC_LOCAL_IP
  const port = process.env.EXPO_PUBLIC_BACKEND_PORT ?? '8000'
  if (isAndroidEmulator) return `http://10.0.2.2:${port}`
  return `http://${ip}:${port}`
})()
```

## Current issues to fix (mobile)
- `services/realtimePoseService.ts` sends base64 frames → must migrate to landmarks
- `package.json` has `react-native-appwrite` (unused) → remove
- `app/exercises/realtime/index.tsx` uses `expo-camera` with base64 → replace with vision camera frame processor


