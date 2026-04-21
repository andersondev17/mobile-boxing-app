/**
 * Bluetooth Low Energy (BLE) integration hooks — Preparation layer.
 *
 * STATUS: STUB — Not wired to real hardware yet.
 *
 * When hardware integration is ready:
 *   1. Install:  npx expo install react-native-ble-plx
 *   2. Add to app.json plugins: ["react-native-ble-plx"]
 *   3. Replace the stub implementations below with real BLE calls.
 *
 * Architecture:
 *   Smartwatch (BLE GATT) → useBLESmartwatch hook → Kafka producer (via backend)
 *                                                  → Zustand store → UI
 */

import { useState, useCallback, useRef } from 'react';

// Expected structure from a BLE health characteristic
export interface SmartWatchPayload {
  device_id: string;
  user_id: string;
  heart_rate: number;
  hr_variability: number;
  fatigue_index: number;
  training_load: number;
  timestamp: string;
}

export type BLEStatus = 'idle' | 'scanning' | 'connected' | 'disconnected' | 'error';

export interface UseBLESmartwatch {
  status: BLEStatus;
  deviceName: string | null;
  lastPayload: SmartWatchPayload | null;
  startScan: () => void;
  stopScan: () => void;
  disconnect: () => void;
}

/**
 * useBLESmartwatch — stub hook.
 *
 * Replace the bodies of startScan / stopScan / disconnect with
 * real react-native-ble-plx calls once the dev build is configured.
 *
 * Simulation mode: emits synthetic payloads every 1s so the UI
 * and Kafka pipeline can be tested without physical hardware.
 */
export function useBLESmartwatch(userId: string): UseBLESmartwatch {
  const [status, setStatus] = useState<BLEStatus>('idle');
  const [deviceName, setDeviceName] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<SmartWatchPayload | null>(null);
  const simulatorRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const _emitSimulated = useCallback(() => {
    const payload: SmartWatchPayload = {
      device_id: 'SIM-001',
      user_id: userId,
      heart_rate: Math.floor(60 + Math.random() * 100),
      hr_variability: Math.floor(40 + Math.random() * 40),
      fatigue_index: parseFloat((Math.random() * 0.9).toFixed(2)),
      training_load: parseFloat((5 + Math.random() * 45).toFixed(1)),
      timestamp: new Date().toISOString(),
    };
    setLastPayload(payload);
    // TODO: when real hardware is connected, POST to /api/health-metrics
    // or send directly via WebSocket side-channel
  }, [userId]);

  const startScan = useCallback(() => {
    console.warn('[BLE] Stub mode — using simulator. Install react-native-ble-plx for real hardware.');
    setStatus('connected');
    setDeviceName('Simulated Watch');
    simulatorRef.current = setInterval(_emitSimulated, 1000);
    // ── REAL IMPLEMENTATION (paste below when ready) ──────────
    // const manager = new BleManager();
    // manager.startDeviceScan(null, null, (err, device) => {
    //   if (err) { setStatus('error'); return; }
    //   if (device?.name?.includes('Watch')) {
    //     manager.stopDeviceScan();
    //     device.connect().then(d => d.discoverAllServicesAndCharacteristics())
    //       .then(d => { setDeviceName(d.name); setStatus('connected'); });
    //   }
    // });
  }, [_emitSimulated]);

  const stopScan = useCallback(() => {
    if (simulatorRef.current) clearInterval(simulatorRef.current);
    setStatus('idle');
  }, []);

  const disconnect = useCallback(() => {
    if (simulatorRef.current) clearInterval(simulatorRef.current);
    setStatus('disconnected');
    setDeviceName(null);
    setLastPayload(null);
  }, []);

  return { status, deviceName, lastPayload, startScan, stopScan, disconnect };
}
