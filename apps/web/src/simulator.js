// Synthetic landmark generator — mirrors simulate_real_client.py logic in JS
// Used by the WebSocket simulator tab to generate realistic test frames

const FEATURES = [
  'elbow_angle_left', 'forward_extent_left', 'torso_rotation',
  'vertical_displacement', 'knee_flexion', 'weight_transfer',
  'hand_speed', 'retraction_speed',
];

function normalRand(mean = 0, std = 1) {
  // Box-Muller
  const u = 1 - Math.random();
  const v = Math.random();
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

// Jab punch trajectory simulation
// frame 0-10: extension, 10-20: peak, 20-30: retraction
function generateJabFrame(frameIdx, category = 'GOOD') {
  const phase = frameIdx / 30;      // 0→1
  const extension = Math.sin(Math.PI * phase); // peaks at frame 15

  const noise = category === 'GOOD' ? 0.02 : category === 'ACCEPTABLE' ? 0.08 : 0.25;
  // Fatigue multiplier for BAD
  const fatigue = category === 'BAD' ? (frameIdx < 10 ? 1.0 : frameIdx < 20 ? 0.75 : 0.4) : 1.0;

  return {
    elbow_angle_left: clamp(normalRand(160 * (1 - 0.6 * extension) * fatigue, noise * 20), 20, 180),
    forward_extent_left: clamp(normalRand(0.35 * extension * fatigue, noise * 0.1), 0, 0.8),
    torso_rotation: clamp(normalRand(0.15 * extension * fatigue, noise * 0.05), 0, 0.5),
    vertical_displacement: clamp(normalRand(0.3, noise * 0.02), 0, 0.8),
    knee_flexion: clamp(normalRand(150 * fatigue, noise * 10), 90, 180),
    weight_transfer: clamp(normalRand(0.05 * extension * fatigue, noise * 0.02), -0.3, 0.3),
    hand_speed: clamp(normalRand(5 * extension * fatigue, noise * 1), 0, 15),
    retraction_speed: clamp(normalRand(2 * (1 - extension) * fatigue, noise * 0.5), 0, 8),
    frame_index: frameIdx,
    tracking_state: 'tracking',
  };
}

// Build a 30-frame jab sequence
export function generateJabSequence(category = 'GOOD') {
  return Array.from({ length: 30 }, (_, i) => generateJabFrame(i, category));
}

// Named landmarks stub (WebSocket expects 'landmarks' field)
export function framesToLandmarkPayload(features, sessionId, userId) {
  return {
    type: 'landmarks',
    landmarks: _featuresToFakeLandmarks(features),
    timestamp: Date.now(),
    session_id: sessionId,
    user_id: userId,
    fps: 30,
  };
}

// Backwards-compatible adapter: inject features directly via a special key
// The WebSocket handler reads 'landmarks', but for testing we can abuse the
// direct features path if available, or send simplified mock landmarks
function _featuresToFakeLandmarks(features) {
  // Build a 33-landmark array where we encode the known values into positions
  // mediapipe uses. This is a simulation scaffold only.
  const lm = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, z: 0.0, v: 0.95 }));
  // Encode elbow angle as wrist position delta (simplified)
  const ext = features.forward_extent_left || 0.3;
  lm[15] = { x: 0.5 + ext, y: 0.4, z: -0.1, v: 0.95 }; // left wrist
  lm[11] = { x: 0.5, y: 0.4, z: 0.0, v: 0.95 };         // left shoulder
  lm[13] = { x: 0.5 + ext * 0.5, y: 0.45, z: -0.05, v: 0.95 }; // left elbow
  lm[12] = { x: 0.45, y: 0.4, z: 0.0, v: 0.95 };        // right shoulder
  lm[14] = { x: 0.45, y: 0.45, z: 0.0, v: 0.95 };
  lm[16] = { x: 0.42, y: 0.42, z: 0.0, v: 0.95 };
  lm[23] = { x: 0.5, y: 0.6, z: 0.0, v: 0.95 };
  lm[24] = { x: 0.45, y: 0.6, z: 0.0, v: 0.95 };
  lm[25] = { x: 0.5, y: 0.75, z: 0.0, v: 0.95 };
  lm[26] = { x: 0.45, y: 0.75, z: 0.0, v: 0.95 };
  lm[27] = { x: 0.5, y: 0.9, z: 0.0, v: 0.95 };
  lm[28] = { x: 0.45, y: 0.9, z: 0.0, v: 0.95 };
  return lm;
}
