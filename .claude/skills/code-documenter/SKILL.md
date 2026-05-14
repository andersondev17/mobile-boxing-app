---
name: code-documenter
description: Apply this skill when adding or reviewing documentation (docstrings, comments, JSDoc) in the boxing app codebase. Use for Python backend (Google-style docstrings) and TypeScript mobile (JSDoc). Trigger on: "add docstring", "document this function", "jsdoc", "add comments", "missing documentation", "docstring", "document the code", "type hints", "explain this code".
---

# Code Documenter — mobile-boxing-app

## Python — Google-style docstrings (backend)

All public functions, methods, and classes must have Google-style docstrings.

### Function with Args/Returns:
```python
def extract_features(landmarks: list) -> Optional[dict]:
    """Compute per-frame biomechanical features from pose landmarks.

    Extracts elbow flexion angle and forward reach from left arm landmarks.
    Returns None if landmarks are insufficient (fewer than 16 points).

    Args:
        landmarks: List of MediaPipe/TFLite pose landmarks, each with .x, .y, .z,
            and .visibility attributes. Must have at least 16 elements.

    Returns:
        Dict with keys:
            - elbow_angle (float): Angle at elbow joint in degrees (0-180).
            - forward_extent (float): Normalized horizontal reach (wrist.x - shoulder.x).
        None if landmarks are insufficient.
    """
```

### Class docstring:
```python
class BoxingAnalyticsService:
    """Orchestrates video and real-time boxing technique analysis.

    Singleton service that manages the baseline reference data, processes
    uploaded videos through the ML pipeline, and creates trackers for
    WebSocket real-time sessions.

    Attributes:
        temp_dir: Path for temporary video uploads.
        output_dir: Path for annotated output videos.
        baseline_data: Current reference DataFrame for DTW comparison.
    """
```

### Async function:
```python
async def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve a user document by email address.

    Args:
        email: Email address to look up (case-sensitive).

    Returns:
        User document if found, None otherwise.

    Raises:
        ConnectionError: If the MongoDB connection is unavailable.
    """
```

### When to add "Raises":
Only when the function explicitly raises an exception that callers must handle.

### One-liner docstrings (simple getters/setters):
```python
def get_baseline(self) -> Optional[pd.DataFrame]:
    """Return the current baseline DataFrame, or None if not loaded."""
```

## TypeScript — JSDoc (mobile)

### Exported component:
```typescript
/**
 * Real-time jab analysis screen using WebSocket and camera feed.
 *
 * Captures frames at 30fps, sends landmarks to backend via WebSocket,
 * and displays technique feedback as an overlay.
 *
 * @param route - Expo Router route params (optional exerciseId).
 */
export default function RealtimeAnalysisScreen({ route }: Props) {
```

### Exported hook:
```typescript
/**
 * Hook for managing real-time pose analysis via WebSocket.
 *
 * Handles connection lifecycle, sends landmark frames, and exposes
 * the latest feedback and jab detection state.
 *
 * @param userId - Authenticated user ID for session attribution.
 * @returns Object with connection status, latest feedback, and jab detection flag.
 *
 * @example
 * const { status, feedback, jabDetected } = useRealtimePose(user.id);
 */
export function useRealtimePose(userId: string): RealtimePoseResult {
```

### TypeScript type definitions:
```typescript
/** Landmark point from TFLite pose estimation (normalized 0-1 coordinates). */
export interface Landmark {
  x: number;   // Horizontal position, 0 = left edge, 1 = right edge
  y: number;   // Vertical position, 0 = top, 1 = bottom
  z: number;   // Depth relative to hip midpoint (negative = closer to camera)
}

/** Server response from WebSocket /boxing/ws/jab endpoint. */
export interface JabRealtimeServerMessage {
  feedback: string | null;     // Technique feedback text, null if no new feedback
  jab_detected: boolean;       // True if a jab was detected in this frame
  frame_index: number | null;  // Current frame counter
  tracking_state: string;      // "searching" | "tracking" | "idle"
}
```

## What NOT to document

- Private utility functions used only within the same file (unless complex)
- Obvious getters: `def get_name(self): return self.name`
- Type-annotated dataclass fields that are self-explanatory
- Test functions (pytest) — test name IS the documentation

## Comments in code (when to add inline comments)

Add inline comments when:
- Logic is non-obvious (e.g., why a magic number exists)
- A restriction is enforced (flag the restriction code)
- A workaround is implemented

```python
# C-02: user_id ALWAYS as partition key — never device_id
key = message["user_id"].encode("utf-8")

# DTW normalization constant 50 calibrated empirically against
# pro boxer baseline videos — see baseline_builder.py
score = 100.0 * np.exp(-min_dist / 50.0)
```

Do NOT add comments that restate the code:
```python
# BAD: increment counter
counter += 1

# GOOD: wrap to prevent integer overflow after long sessions
counter = (counter + 1) % MAX_FRAME_COUNT
```

## Updating existing docstrings

When modifying a function, update its docstring to reflect the new behavior. Pay attention to:
- Args section: does it still match the parameters?
- Returns section: does it still match what's returned?
- Raises section: are there new exceptions?


