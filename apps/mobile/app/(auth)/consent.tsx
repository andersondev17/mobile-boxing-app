/**
 * ConsentScreen
 *
 * Personal-data consent screen displayed during registration onboarding,
 * before any account is created. Implements Ley 1581 de 2012 (Colombia)
 * requirements for informed consent to data treatment.
 *
 * Flow:
 *   1. User reads the summary and optional full policy (opens browser).
 *   2. "Acepto y continúo" → POST /consent/ → navigate to sign-up.
 *   3. "Salir" → abort registration flow.
 *
 * @module app/(auth)/consent
 */

import { post } from '@/lib/api/client';
import { router } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

/** Backend endpoint for recording consent. */
const CONSENT_ENDPOINT = '/consent/';

/** URL for the full privacy policy document. */
const FULL_POLICY_URL = 'https://gymshock.app/privacy'; // TODO: reemplazar con URL real antes de producción

/**
 * Onboarding screen that collects personal-data consent (Ley 1581) before
 * allowing the user to complete registration.
 */
const ConsentScreen: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Open the full privacy-policy document in the system browser.
   * Does not block the consent flow.
   */
  const handleReadFullPolicy = async (): Promise<void> => {
    try {
      await WebBrowser.openBrowserAsync(FULL_POLICY_URL);
    } catch {
      Alert.alert('Error', 'No se pudo abrir la política de privacidad.');
    }
  };

  /**
   * Record consent on the backend, then navigate to the sign-up screen.
   * If the request fails the user is shown an error and can retry.
   */
  const handleAccept = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await post(CONSENT_ENDPOINT, {
        consent_type: 'personal_data',
        granted: true,
      });
      router.push('/(auth)/sign-up');
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Error al registrar consentimiento.';
      Alert.alert('Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Exit the registration flow without granting consent.
   */
  const handleDecline = (): void => {
    router.back();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>
            Política de tratamiento de datos personales
          </Text>
          <Text style={styles.subtitle}>Ley 1581 de 2012 — Colombia</Text>
        </View>

        {/* Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>¿Qué datos recopilamos?</Text>
          <Text style={styles.body}>
            Recopilamos tu nombre, correo electrónico y, durante sesiones de
            entrenamiento, coordenadas de articulaciones generadas por el
            modelo de visión por computadora instalado en tu dispositivo.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>¿Para qué los usamos?</Text>
          <Text style={styles.body}>
            Tus datos se utilizan exclusivamente para analizar tu técnica de
            boxeo, generar retroalimentación personalizada y mejorar los
            modelos de entrenamiento de la aplicación.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>¿Compartimos tus datos?</Text>
          <Text style={styles.body}>
            No vendemos ni compartimos tus datos personales con terceros sin
            tu consentimiento explícito. Los datos biométricos nunca abandonan
            tu dispositivo en forma de imagen o video.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Tus derechos</Text>
          <Text style={styles.body}>
            Tienes derecho a conocer, actualizar, rectificar y suprimir tus
            datos, y a revocar este consentimiento en cualquier momento desde
            la sección de configuración.
          </Text>
        </View>

        {/* Full policy link */}
        <Pressable
          onPress={handleReadFullPolicy}
          accessibilityRole="link"
          accessibilityLabel="Leer política completa de privacidad"
        >
          <Text style={styles.policyLink}>Leer política completa</Text>
        </Pressable>
      </ScrollView>

      {/* Action buttons — pinned at the bottom */}
      <View style={styles.footer}>
        <Pressable
          style={[styles.button, styles.buttonPrimary, isLoading && styles.buttonDisabled]}
          onPress={handleAccept}
          disabled={isLoading}
          accessibilityRole="button"
          accessibilityLabel="Acepto los términos y continúo con el registro"
        >
          {isLoading ? (
            <ActivityIndicator color="#000000" />
          ) : (
            <Text style={styles.buttonPrimaryText}>Acepto y continúo</Text>
          )}
        </Pressable>

        <Pressable
          style={[styles.button, styles.buttonSecondary]}
          onPress={handleDecline}
          disabled={isLoading}
          accessibilityRole="button"
          accessibilityLabel="Salir del flujo de registro"
        >
          <Text style={styles.buttonSecondaryText}>Salir</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#111111',
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingTop: 40,
    paddingBottom: 16,
  },
  header: {
    marginBottom: 32,
    alignItems: 'center',
  },
  title: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitle: {
    color: 'rgba(255,255,255,0.45)',
    fontSize: 12,
    textAlign: 'center',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    color: '#C29B2E',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  body: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 14,
    lineHeight: 22,
  },
  policyLink: {
    color: '#C29B2E',
    fontSize: 14,
    textDecorationLine: 'underline',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 8,
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    paddingTop: 12,
    gap: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.10)',
    backgroundColor: '#111111',
  },
  button: {
    borderRadius: 12,
    paddingVertical: 15,
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
  buttonDisabled: {
    opacity: 0.5,
  },
});

export default ConsentScreen;
