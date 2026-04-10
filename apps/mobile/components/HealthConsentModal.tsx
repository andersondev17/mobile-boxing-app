/**
 * HealthConsentModal
 *
 * Displays a consent dialog (Ley 1581 Colombia) before linking a smartwatch
 * and streaming health/biometric sensor data (heart rate, etc.).
 *
 * Restriction C-05: Consent MUST be obtained before reading health data.
 *
 * @module components/HealthConsentModal
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
 * Props for {@link HealthConsentModal}.
 */
export interface HealthConsentModalProps {
  /** Controls modal visibility. */
  visible: boolean;
  /** Called when the user taps "Vincular reloj". */
  onAccept: () => void;
  /** Called when the user taps "Omitir". */
  onDecline: () => void;
}

/**
 * Modal that requests health-data consent before linking a smartwatch.
 *
 * The modal is not dismissible by tapping the backdrop — the user must
 * make an explicit choice via one of the two action buttons.
 *
 * @example
 * <HealthConsentModal
 *   visible={showHealthConsent}
 *   onAccept={handleAccept}
 *   onDecline={handleDecline}
 * />
 */
const HealthConsentModal: React.FC<HealthConsentModalProps> = ({
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
          <Text style={styles.title}>Datos de salud del smartwatch</Text>

          {/* Description */}
          <Text style={styles.body}>
            Tus datos de ritmo cardíaco nos ayudan a correlacionar tu
            rendimiento físico con la precisión técnica. Solo accedemos a
            los sensores del dispositivo durante una sesión activa.
          </Text>

          <Text style={styles.legalNote}>
            Tratamiento de datos de salud conforme a la Ley 1581 de 2012
            (Colombia).
          </Text>

          {/* Actions */}
          <View style={styles.actions}>
            <Pressable
              style={[styles.button, styles.buttonPrimary]}
              onPress={onAccept}
              accessibilityRole="button"
              accessibilityLabel="Vincular smartwatch y permitir datos de salud"
            >
              <Text style={styles.buttonPrimaryText}>Vincular reloj</Text>
            </Pressable>

            <Pressable
              style={[styles.button, styles.buttonSecondary]}
              onPress={onDecline}
              accessibilityRole="button"
              accessibilityLabel="Omitir vinculación de smartwatch"
            >
              <Text style={styles.buttonSecondaryText}>Omitir</Text>
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

export default HealthConsentModal;
