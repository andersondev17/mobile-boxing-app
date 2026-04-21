import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { API, createWebSocket } from './api';
import { generateJabSequence, framesToLandmarkPayload } from './simulator';
import './index.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

// ── Helpers ──
function scoreColor(s) {
  if (s >= 85) return 'var(--green)';
  if (s >= 70) return '#86efac';
  if (s >= 50) return 'var(--amber)';
  return 'var(--red)';
}
function scoreLabel(s) {
  if (s >= 85) return 'elite';
  if (s >= 70) return 'good';
  if (s >= 50) return 'developing';
  return 'poor';
}
function uuid() { return crypto.randomUUID(); }

// ── Chart config factory ──
function makeChartData(labels, datasets) {
  return {
    labels,
    datasets: datasets.map((d, i) => ({
      borderWidth: 2,
      pointRadius: i === 0 ? 2 : 0,
      tension: 0.4,
      fill: i === 0,
      ...d,
    })),
  };
}

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: {
    legend: { labels: { color: '#9ca3af', font: { size: 11, family: 'JetBrains Mono' }, boxWidth: 12 } },
    tooltip: {
      backgroundColor: '#111318',
      borderColor: '#232630',
      borderWidth: 1,
      titleColor: '#e8eaf0',
      bodyColor: '#9ca3af',
    },
  },
  scales: {
    x: { ticks: { color: '#6b7280', font: { size: 10 } }, grid: { color: '#1a1d24' } },
    y: { ticks: { color: '#6b7280', font: { size: 10 } }, grid: { color: '#1a1d24' } },
  },
};

// ─────────────────────────────────────────────────────────────────────
// TAB: Video Analysis
// ─────────────────────────────────────────────────────────────────────
function VideoTab({ onLog }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    API.listTestRuns().then(setHistory).catch(() => {});
  }, [result]);

  const analyze = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    onLog(`Uploading ${file.name} (${(file.size / 1024).toFixed(0)} KB)…`);
    try {
      const data = await API.analyzeVideo(file);
      setResult(data);
      onLog(`✅ Analysis complete. avg_score=${data.avg_score} frames=${data.scored_frames}`, 'ok');
    } catch (e) {
      setError(e.message);
      onLog(`❌ ${e.message}`, 'err');
    } finally {
      setLoading(false);
    }
  };

  const frameScores = result?.frame_scores?.map(f => f.dtw_score) ?? [];
  const frameLabels = result?.frame_scores?.map(f => `f${f.frame_index}`) ?? [];
  const baselineCurve = result?.baseline_curve ?? [];
  const baselineLabels = baselineCurve.map((_, i) => `b${i}`);

  return (
    <div>
      {/* Upload */}
      <div className="card">
        <div className="card-title">🎬 Video Upload</div>
        <div
          className={`upload-zone${dragging ? ' dragging' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
        >
          <input type="file" accept="video/mp4,video/quicktime,.mp4,.mov"
            onChange={e => setFile(e.target.files[0])} />
          <div className="upload-icon">📹</div>
          <div className="upload-text">
            {file ? <strong style={{ color: 'var(--text)' }}>{file.name}</strong> : 'Drop a video or click to browse'}
          </div>
          <div className="upload-hint">MP4 / MOV — server-side MediaPipe processing</div>
        </div>
        {error && <div style={{ color: 'var(--red)', marginTop: 12, fontSize: 12 }}>⚠️ {error}</div>}
        <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
          <button className="btn btn-primary" onClick={analyze} disabled={!file || loading}>
            {loading ? <><span className="spinner" /> Analyzing…</> : '⚡ Analyze Technique'}
          </button>
          {file && <button className="btn btn-secondary" onClick={() => { setFile(null); setResult(null); }}>Clear</button>}
        </div>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Punch Type and Technique Level */}
          <div className="stats-grid">
            {[
              { label: 'Punch Type', value: result.punch_type_detected?.charAt(0).toUpperCase() + (result.punch_type_detected?.slice(1) || 'Unknown'), cls: 'neutral', sub: 'Detected from filename' },
              { label: 'Technique Level', value: result.technique_level?.charAt(0).toUpperCase() + (result.technique_level?.slice(1) || 'Poor'), cls: scoreLabel(result.avg_score), sub: 'Based on DTW analysis' },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div className="stat-label">{s.label}</div>
                <div className={`stat-value ${s.cls}`}>{s.value}</div>
                <div className="stat-sub">{s.sub}</div>
              </div>
            ))}
          </div>

          {/* Baseline Information */}
          {result.baseline_type && result.baseline_type !== 'none' && (
            <div className="card">
              <div className="card-title">Baseline Information</div>
              <div className="stats-grid">
                {[
                  { label: 'Baseline Type', value: result.baseline_type?.charAt(0).toUpperCase() + result.baseline_type?.slice(1), cls: 'neutral', sub: 'Reference baseline' },
                  { label: 'Baseline Used', value: result.baseline_type !== 'none' ? 'Yes' : 'No', cls: result.baseline_type !== 'none' ? 'good' : 'neutral', sub: 'Baseline matching' },
                ].map(s => (
                  <div key={s.label} className="stat-card">
                    <div className="stat-label">{s.label}</div>
                    <div className={`stat-value ${s.cls}`}>{s.value}</div>
                    <div className="stat-sub">{s.sub}</div>
                  </div>
                ))}
              </div>
              {result.baseline_used && (
                <div style={{ marginTop: 12, padding: 8, background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 6, fontSize: 12, color: 'var(--green)' }}>
                  Baseline file: {result.baseline_used?.split('/').pop() || 'Unknown'}
                </div>
              )}
            </div>
          )}

          {/* Score Metrics */}
          <div className="stats-grid">
            {[
              { label: 'Avg Score', value: result.avg_score?.toFixed(1), cls: scoreLabel(result.avg_score), sub: scoreLabel(result.avg_score) },
              { label: 'Min Score', value: result.min_score?.toFixed(1), cls: scoreLabel(result.min_score), sub: 'worst frame' },
              { label: 'Max Score', value: result.max_score?.toFixed(1), cls: scoreLabel(result.max_score), sub: 'best frame' },
              { label: 'Frames Scored', value: result.scored_frames, cls: 'neutral', sub: `of ${result.total_frames} total` },
              { label: 'Processing', value: `${result.processing_ms?.toFixed(0)}ms`, cls: 'neutral', sub: 'server time' },
            ].map(s => (
              <div key={s.label} className="stat-card">
                <div className="stat-label">{s.label}</div>
                <div className={`stat-value ${s.cls}`}>{s.value}</div>
                <div className="stat-sub">{s.sub}</div>
              </div>
            ))}
          </div>

          {/* DTW Score chart */}
          {frameScores.length > 0 && (
            <div className="card">
              <div className="card-title">📈 DTW Score per Frame</div>
              <div className="chart-wrap">
                <Line
                  data={makeChartData(frameLabels, [{
                    label: 'DTW Score',
                    data: frameScores,
                    borderColor: 'rgba(99,102,241,0.9)',
                    backgroundColor: 'rgba(99,102,241,0.08)',
                    fill: true,
                  }, {
                    label: 'Threshold (70)',
                    data: Array(frameScores.length).fill(70),
                    borderColor: 'rgba(245,158,11,0.5)',
                    borderDash: [5, 4],
                    fill: false,
                  }])}
                  options={{ ...CHART_OPTS, scales: { ...CHART_OPTS.scales, y: { ...CHART_OPTS.scales.y, min: 0, max: 100 } } }}
                />
              </div>
            </div>
          )}

          {/* Baseline comparison */}
          {baselineCurve.length > 0 && (
            <div className="card">
              <div className="card-title">🔵 Torso Rotation vs Baseline</div>
              <div className="chart-wrap">
                <Line
                  data={makeChartData(baselineLabels, [{
                    label: 'Baseline (pro)',
                    data: baselineCurve,
                    borderColor: 'rgba(34,197,94,0.8)',
                    backgroundColor: 'transparent',
                    fill: false,
                  }, {
                    label: 'User frames (avg)',
                    data: result.frame_scores?.slice(0, baselineCurve.length).map(f => f.dtw_score / 100 * 0.5) ?? [],
                    borderColor: 'rgba(99,102,241,0.7)',
                    backgroundColor: 'transparent',
                    fill: false,
                  }])}
                  options={CHART_OPTS}
                />
              </div>
            </div>
          )}

          {/* Spanish Coaching Feedback */}
          {result.coaching_feedback?.length > 0 && (
            <div className="card">
              <div className="card-title">Coaching Feedback</div>
              <ul className="feedback-list">
                {result.coaching_feedback.map((msg, i) => (
                  <li key={i} className="feedback-item">
                    <span className="feedback-icon">Coach</span>
                    <span>{msg}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Motivational Messages */}
          {result.motivational_messages?.length > 0 && (
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(194,155,46,0.1), rgba(245,208,104,0.1))' }}>
              <div className="card-title">Motivational Messages</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {result.motivational_messages.map((msg, i) => (
                  <div key={i} style={{ 
                    padding: '10px 14px', 
                    background: 'rgba(194,155,46,0.2)', 
                    border: '1px solid rgba(194,155,46,0.3)', 
                    borderRadius: 8, 
                    fontSize: 14,
                    color: 'var(--text)',
                    textAlign: 'center',
                    fontWeight: 500
                  }}>
                    {msg}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Legacy Feedback */}
          {result.feedback?.length > 0 && (
            <div className="card">
              <div className="card-title">Legacy Feedback</div>
              <ul className="feedback-list">
                {result.feedback.map((msg, i) => (
                  <li key={i} className="feedback-item">
                    <span className="feedback-icon">Feedback</span>
                    <span>{msg}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="card">
              <div className="card-title">Test Run History</div>
              <table className="hist-table">
                <thead>
                  <tr>
                    <th>Video</th><th>Avg Score</th><th>Min</th><th>Max</th><th>Frames</th><th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(r => (
                    <tr key={r.id}>
                      <td style={{ color: 'var(--text)' }}>{r.video_name}</td>
                      <td><span className={`pill ${scoreLabel(r.avg_score)}`}>{r.avg_score?.toFixed(1)}</span></td>
                      <td style={{ color: 'var(--text-muted)' }}>{r.min_score?.toFixed(1)}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{r.max_score?.toFixed(1)}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{r.scored_frames}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: 11 }}>{r.created_at?.slice(0, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// TAB: WebSocket Simulator
// ─────────────────────────────────────────────────────────────────────
const LIVE_WINDOW = 60; // keep last N scores

function SimulatorTab({ onLog }) {
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [category, setCategory] = useState('GOOD');
  const [running, setRunning] = useState(false);
  const [liveScores, setLiveScores] = useState([]);
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [metrics, setMetrics] = useState({ frames: 0, jabs: 0, lastScore: null });
  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const sessionId = useRef(uuid());
  const frameSeq = useRef(null);
  const frameIdx = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current) return;
    setWsStatus('connecting');
    onLog('Connecting WebSocket…');
    const { send, close, ws } = createWebSocket(
      sessionId.current,
      'web-tester',
      (data) => {
        if (data.type === 'pong') return;
        if (data.dtw_score != null) {
          setLiveScores(prev => [...prev.slice(-LIVE_WINDOW), data.dtw_score]);
          setMetrics(m => ({
            ...m,
            frames: m.frames + 1,
            jabs: data.jab_detected ? m.jabs + 1 : m.jabs,
            lastScore: data.dtw_score,
          }));
        }
        if (data.feedback) setCurrentFeedback(data.feedback);
        if (data.error) onLog(`WS error: ${data.error}`, 'err');
      },
      () => { setWsStatus('disconnected'); setRunning(false); wsRef.current = null; onLog('WS disconnected'); }
    );
    wsRef.current = { send, close };
    ws.onopen = () => { setWsStatus('connected'); onLog('✅ WebSocket connected'); };
  }, [onLog]);

  const disconnect = useCallback(() => {
    stopSend();
    wsRef.current?.close();
    wsRef.current = null;
    setWsStatus('disconnected');
  }, []);

  const startSend = useCallback(() => {
    if (!wsRef.current || running) return;
    frameSeq.current = generateJabSequence(category);
    frameIdx.current = 0;
    setRunning(true);
    onLog(`▶ Streaming ${category} frames…`);

    timerRef.current = setInterval(() => {
      if (!wsRef.current) { stopSend(); return; }
      const fi = frameIdx.current % 30;
      const frame = frameSeq.current[fi];
      const payload = framesToLandmarkPayload(frame, sessionId.current, 'web-tester');
      wsRef.current.send(payload);
      frameIdx.current++;
      // New sequence every 30 frames (simulate continuous jabs)
      if (fi === 29) {
        frameSeq.current = generateJabSequence(category);
        onLog(`↺ New ${category} sequence`);
      }
    }, 33); // ~30fps
  }, [running, category, onLog]);

  function stopSend() {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setRunning(false);
  }

  // Cleanup on unmount
  useEffect(() => () => { stopSend(); wsRef.current?.close(); }, []);

  const scoreLabels = liveScores.map((_, i) => `${i + 1}`);

  return (
    <div>
      {/* Controls */}
      <div className="card">
        <div className="card-title">🔌 WebSocket Simulator</div>
        <div className={`ws-status ${wsStatus}`}>
          <span className={`ws-dot${wsStatus === 'connected' ? ' pulse' : ''}`} />
          {wsStatus.toUpperCase()}
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
          {wsStatus === 'disconnected'
            ? <button className="btn btn-primary" onClick={connect}>Connect</button>
            : <button className="btn btn-danger" onClick={disconnect}>Disconnect</button>}

          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            style={{ background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', padding: '8px 12px', fontSize: 13 }}
            disabled={running}
          >
            <option value="GOOD">GOOD (score &gt;85)</option>
            <option value="ACCEPTABLE">ACCEPTABLE (70–85)</option>
            <option value="BAD">BAD (&lt;60) + fatigue</option>
          </select>

          {wsStatus === 'connected' && (
            running
              ? <button className="btn btn-danger" onClick={stopSend}>⏹ Stop</button>
              : <button className="btn btn-primary" onClick={startSend}>▶ Stream</button>
          )}
          <button className="btn btn-secondary" onClick={() => { setLiveScores([]); setMetrics({ frames: 0, jabs: 0, lastScore: null }); }}>Reset</button>
        </div>

        {currentFeedback && (
          <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 8 }}>
            💬 {currentFeedback}
          </div>
        )}
      </div>

      {/* Live metrics */}
      <div className="stats-grid">
        {[
          { label: 'Last DTW Score', value: metrics.lastScore != null ? metrics.lastScore.toFixed(1) : '—', cls: metrics.lastScore != null ? scoreLabel(metrics.lastScore) : 'neutral' },
          { label: 'Frames Sent', value: metrics.frames, cls: 'neutral' },
          { label: 'Jabs Detected', value: metrics.jabs, cls: 'neutral' },
          { label: 'Mode', value: category, cls: 'neutral' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-label">{s.label}</div>
            <div className={`stat-value ${s.cls}`}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Live score chart */}
      {liveScores.length > 0 && (
        <div className="card">
          <div className="card-title">📈 Live DTW Score Stream</div>
          <div className="chart-wrap">
            <Line
              data={makeChartData(scoreLabels, [{
                label: 'DTW Score',
                data: liveScores,
                borderColor: 'rgba(99,102,241,0.9)',
                backgroundColor: 'rgba(99,102,241,0.08)',
                fill: true,
              }, {
                label: 'Elite (85)',
                data: Array(liveScores.length).fill(85),
                borderColor: 'rgba(34,197,94,0.4)',
                borderDash: [4, 3],
                fill: false,
              }, {
                label: 'Min acceptable (70)',
                data: Array(liveScores.length).fill(70),
                borderColor: 'rgba(245,158,11,0.4)',
                borderDash: [4, 3],
                fill: false,
              }])}
              options={{ ...CHART_OPTS, animation: false, scales: { ...CHART_OPTS.scales, y: { ...CHART_OPTS.scales.y, min: 0, max: 100 } } }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// TAB: Baseline Upload
// ─────────────────────────────────────────────────────────────────────
function BaselineTab({ onLog }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const upload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const r = await API.uploadBaseline(file);
      setResult(r);
      onLog(`✅ Baseline loaded: ${r.rows} rows`, 'ok');
    } catch (e) {
      onLog(`❌ ${e.message}`, 'err');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-title">📦 Load Professional Baseline</div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
        Upload <code style={{ color: 'var(--accent)' }}>dataset/baseline_final.parquet</code> to set the reference for DTW scoring.
      </p>
      <div className="upload-zone" style={{ padding: 28 }}>
        <input type="file" accept=".parquet" onChange={e => setFile(e.target.files[0])} />
        <div className="upload-icon">📊</div>
        <div className="upload-text">{file ? file.name : 'Drop baseline_final.parquet here'}</div>
        <div className="upload-hint">.parquet — pandas format</div>
      </div>
      {result && (
        <div style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 8, padding: 12, marginTop: 12, fontSize: 13, color: 'var(--green)' }}>
          ✅ Baseline active — {result.rows} rows loaded
        </div>
      )}
      <div style={{ marginTop: 12 }}>
        <button className="btn btn-primary" onClick={upload} disabled={!file || loading}>
          {loading ? <><span className="spinner" /> Uploading…</> : '📤 Upload Baseline'}
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'video', icon: '🎬', label: 'Video Analysis' },
  { id: 'simulator', icon: '🔁', label: 'WS Simulator' },
  { id: 'baseline', icon: '📦', label: 'Baseline' },
];

export default function App() {
  const [tab, setTab] = useState('video');
  const [logs, setLogs] = useState([{ text: 'Boxing Analytics ready.', type: 'ok' }]);
  const [apiOk, setApiOk] = useState(false);
  const logRef = useRef(null);

  const addLog = useCallback((text, type = 'info') => {
    setLogs(prev => [...prev.slice(-100), { text: `[${new Date().toLocaleTimeString()}] ${text}`, type }]);
    setTimeout(() => logRef.current?.scrollTo({ top: 99999, behavior: 'smooth' }), 50);
  }, []);

  useEffect(() => {
    API.getStatus().then(s => { if (s) { setApiOk(true); addLog('Backend reachable ✅', 'ok'); } })
      .catch(() => addLog('Backend unreachable — start with: cd apps/backend && uvicorn app.main:app', 'err'));
  }, [addLog]);

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">🥊</div>
        <h1>Boxing Analytics — Web Testing</h1>
        <div className={`header-badge ${apiOk ? 'connected' : 'disconnected'}`}>
          {apiOk ? '● API ONLINE' : '○ API OFFLINE'}
        </div>
      </header>

      <div className="main">
        <nav className="sidebar">
          {TABS.map(t => (
            <div
              key={t.id}
              className={`nav-item${tab === t.id ? ' active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <span className="nav-icon">{t.icon}</span>
              {t.label}
            </div>
          ))}
          <div style={{ marginTop: 'auto', padding: 16, borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
              DTW Pipeline v0.3<br />
              <span style={{ color: 'var(--text-muted)', opacity: 0.6 }}>Python 3.10 • FastAPI</span>
            </div>
          </div>
        </nav>

        <div className="content">
          {tab === 'video' && <VideoTab onLog={addLog} />}
          {tab === 'simulator' && <SimulatorTab onLog={addLog} />}
          {tab === 'baseline' && <BaselineTab onLog={addLog} />}

          {/* Log terminal — always visible */}
          <div style={{ marginTop: 24 }}>
            <div className="card-title" style={{ fontSize: 11, marginBottom: 8 }}>🖥 Console</div>
            <div className="log-box" ref={logRef}>
              {logs.map((l, i) => (
                <div key={i} className={`log-line${l.type === 'err' ? ' err' : l.type === 'warn' ? ' warn' : ''}`}>
                  {l.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
