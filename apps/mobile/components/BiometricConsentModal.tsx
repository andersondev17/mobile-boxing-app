/**
 * BiometricConsentModal
 *
 * Displays a consent dialog (Ley 1581 Colombia) before activating the device
 * camera for pose analysis. Must be shown — and accepted — before any camera
 * or TFLite frame-processor is started.
 *
 * Restriction C-05: Consent MUST be obtained before activating the camera.
 *
 * @module components/BiometricConsentModal
 */

import React from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

/**
 * Props for {@link BiometricConsentModal}.
 */
export interface BiometricConsentModalProps {
  /** Controls modal visibility. */
  visible: boolean;
  /** Called when the user taps "Permitir análisis". */
  onAccept: () => void;
  /** Called when the user taps "Ahora no". */
  onDecline: () => void;
}

/**
 * Modal that requests biometric-data consent before enabling the camera.
 *
 * The modal is not dismissible by tapping the backdrop — the user must
 * make an explicit choice via one of the two action buttons.
 *
 * @example
 * <BiometricConsentModal
 *   visible={showConsent}
 *   onAccept={handleAccept}
 *   onDecline={handleDecline}
 * />
 */
const BiometricConsentModal: React.FC<BiometricConsentModalProps> = ({
  visible,
  onAccept,
  onDecline,
}) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
    >
      <View style={styles.backdrop}>
        <View style={styles.card}>
          {/* Title */}
          <Text style={styles.title}>Análisis de técnica de boxeo</Text>

          {/* Description */}
          <Text style={styles.body}>
            Usaremos tu cámara para analizar tu postura y técnica. Solo
            procesamos coordenadas de articulaciones — nunca almacenamos
            imágenes o video.
          </Text>

          <Text style={styles.legalNote}>
            Tratamiento de datos biométricos conforme a la Ley 1581 de 2012
            (Colombia).
          </Text>

          {/* Actions */}
          <View style={styles.actions}>
            <Pressable
              style={[styles.button, styles.buttonPrimary]}
              onPress={onAccept}
              accessibilityRole="button"
              accessibilityLabel="Permitir análisis de pose"
            >
              <Text style={styles.buttonPrimaryText}>Permitir análisis</Text>
            </Pressable>

            <Pressable
              style={[styles.button, styles.buttonSecondary]}
              onPress={onDecline}
              accessibilityRole="button"
              accessibilityLabel="Rechazar análisis de pose"
            >
              <Text style={styles.buttonSecondaryText}>Ahora no</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  card: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  body: {
    color: 'rgba(255,255,255,0.80)',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 12,
    textAlign: 'center',
  },
  legalNote: {
    color: 'rgba(255,255,255,0.45)',
    fontSize: 11,
    lineHeight: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  actions: {
    gap: 10,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#C29B2E',
  },
  buttonPrimaryText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '700',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  buttonSecondaryText: {
    color: 'rgba(255,255,255,0.70)',
    fontSize: 16,
    fontWeight: '500',
  },
});

export default BiometricConsentModal;
