// Legal content constants for Terms and Privacy screens

export const LEGAL_CONTACT = {
  email: 'legal@gymshock.com',
  privacyEmail: 'privacy@gymshock.com',
  address: 'Liga de Boxeo de Belén, Medellín, Colombia',
  phone: '+57 (4) XXX-XXXX',
} as const;

export const TERMS_SECTIONS = [
  {
    id: 1,
    title: 'Introducción',
    content:
      'Bienvenido a la plataforma de entrenamiento técnico de boxeo para la comunidad de Medellín. Al registrarte y usar esta aplicación, aceptas estos términos y condiciones.',
  },
  {
    id: 2,
    title: 'Propósito de la Plataforma',
    content: `Esta aplicación tiene como objetivo:

• Conectar practicantes locales de boxeo con entrenadores certificados en Medellín
• Proporcionar entrenamiento técnico estructurado y progresión segura
• Prevenir lesiones mediante análisis de postura con visión por computador
• Fortalecer la comunidad de boxeo urbano en alianza con la Liga de Boxeo de Belén`,
  },
  {
    id: 3,
    title: 'Datos de Salud y Rendimiento',
    content: `Al usar esta aplicación, autorizas:

• La integración con tu smartwatch para monitorear frecuencia cardíaca, gasto calórico y tiempo activo
• El análisis de videos de entrenamiento mediante algoritmos de visión por computador (OpenCV/MediaPipe)
• El almacenamiento seguro de métricas de rendimiento físico y técnico
• La generación de reportes personalizados basados en tus datos`,
  },
  {
    id: 4,
    title: 'Responsabilidades del Usuario',
    content: `• Consultar con un médico antes de iniciar cualquier programa de entrenamiento físico
• Proporcionar información veraz sobre tu nivel de experiencia y condición física
• Seguir las recomendaciones de seguridad de los entrenadores certificados
• No utilizar la aplicación si tienes condiciones médicas que contraindiquen el boxeo`,
  },
  {
    id: 5,
    title: 'Análisis de Postura con Visión por Computador',
    content: `• Los videos capturados se procesan localmente o en servidores seguros
• Los modelos de IA (YOLO/MediaPipe) estiman la postura para mejorar tu técnica
• No compartimos tus videos con terceros sin tu consentimiento explícito
• Los análisis son complementarios, no reemplazan la supervisión de un entrenador`,
  },
  {
    id: 6,
    title: 'Conexión con Entrenadores',
    content: `• Los entrenadores listados son independientes, la app solo facilita la conexión
• Verificamos credenciales básicas, pero no somos responsables de la calidad del servicio
• Cualquier acuerdo económico es directo entre usuario y entrenador
• Reporta comportamientos inapropiados a través del sistema de reportes`,
  },
  {
    id: 7,
    title: 'Logros y Gamificación',
    content: `• El sistema de logros, niveles y rankings es para motivación personal
• No garantiza resultados físicos específicos
• Compite sanamente, el progreso real requiere consistencia y técnica adecuada`,
  },
  {
    id: 8,
    title: 'Limitación de Responsabilidad',
    content: `La aplicación proporciona herramientas de apoyo al entrenamiento, pero:

• No somos responsables por lesiones ocurridas durante entrenamientos
• No garantizamos resultados específicos de pérdida de peso o rendimiento
• Los análisis de IA son estimaciones, no diagnósticos médicos
• Recomendamos siempre supervisión profesional presencial`,
  },
  {
    id: 9,
    title: 'Modificaciones',
    content:
      'Nos reservamos el derecho de modificar estos términos. Las actualizaciones serán notificadas dentro de la aplicación.',
  },
  {
    id: 10,
    title: 'Contacto',
    content: `Para consultas sobre estos términos:
Email: ${LEGAL_CONTACT.email}
Dirección: ${LEGAL_CONTACT.address}`,
  },
] as const;

export const PRIVACY_SECTIONS = [
  {
    id: 1,
    title: 'Datos que Recopilamos',
    content: `Datos de perfil:
• Nombre, email, nivel de experiencia en boxeo
• Ubicación (para conectar con entrenadores locales)
• Foto de perfil (opcional)

Datos de salud y rendimiento:
• Frecuencia cardíaca (smartwatch)
• Gasto calórico estimado
• Tiempo activo y tipo de entrenamiento
• Historial de sesiones y progreso

Datos de análisis técnico:
• Videos de entrenamientos (guardados localmente o en servidores encriptados)
• Métricas de postura generadas por OpenCV/MediaPipe
• Evaluaciones de técnica de golpeo, guardia y desplazamientos`,
  },
  {
    id: 2,
    title: 'Cómo Usamos tus Datos',
    content: `• Personalización: Generar recomendaciones de entrenamiento adaptadas a tu nivel
• Conexión: Mostrarte entrenadores cercanos según tu ubicación
• Análisis: Procesar videos con IA para evaluar tu técnica
• Progreso: Crear reportes visuales de tu evolución física y técnica
• Investigación: Analizar tendencias anónimas para mejorar la plataforma
• Cumplimiento: Responder a requerimientos legales si es necesario`,
  },
  {
    id: 3,
    title: 'Compartir tus Datos',
    content: `Con entrenadores:
• Solo información básica de perfil cuando inicias contacto
• Métricas de progreso si autorizas explícitamente

Nunca compartimos:
• Videos de entrenamiento sin tu consentimiento
• Datos de salud con terceros con fines publicitarios
• Información personal identificable a proveedores externos`,
  },
  {
    id: 4,
    title: 'Seguridad de Datos',
    content: `• Encriptación: Todos los datos sensibles se almacenan encriptados (AES-256)
• Tokens JWT: Autenticación segura con refresh tokens
• HTTPS: Todas las comunicaciones usan protocolos seguros
• Acceso limitado: Solo personal autorizado accede a datos sensibles
• Backups: Respaldos automáticos con acceso restringido`,
  },
  {
    id: 5,
    title: 'Integración con Smartwatch',
    content: [
      'Solicitamos permisos para acceder a datos de salud solo cuando los necesitamos',
      'Puedes revocar el acceso en cualquier momento desde configuración',
      'No accedemos a datos de salud fuera de sesiones de entrenamiento',
      'Cumplimos con estándares de Apple HealthKit y Google Fit',
    ],
  },
  {
    id: 6,
    title: 'Procesamiento con Inteligencia Artificial',
    content: `• Procesamiento local: Cuando sea posible, los videos se analizan en tu dispositivo
• Servidores seguros: Videos subidos se almacenan temporalmente encriptados
• Eliminación automática: Videos procesados se eliminan tras 30 días (configurable)
• Modelos de IA: No se entrenan con tus datos sin consentimiento explícito`,
  },
  {
    id: 7,
    title: 'Tus Derechos',
    content: `• Acceso: Solicitar copia de todos tus datos
• Rectificación: Corregir datos incorrectos
• Eliminación: Borrar tu cuenta y todos los datos asociados
• Portabilidad: Exportar tus datos en formato legible
• Revocación: Retirar consentimientos otorgados

Para ejercer estos derechos: ${LEGAL_CONTACT.privacyEmail}`,
  },
  {
    id: 8,
    title: 'Cookies y Rastreo',
    content: `• Usamos analytics para mejorar la experiencia (Google Analytics, Firebase)
• Puedes desactivar el rastreo desde configuración
• No vendemos datos de rastreo a terceros`,
  },
  {
    id: 9,
    title: 'Menores de Edad',
    content: `• La aplicación está diseñada para mayores de 16 años
• Menores entre 13-16 requieren consentimiento de padres/tutores
• No recopilamos intencionalmente datos de menores de 13 años`,
  },
  {
    id: 10,
    title: 'Cambios a esta Política',
    content:
      'Actualizaremos esta política cuando sea necesario. Los cambios importantes serán notificados por email y dentro de la app.',
  },
  {
    id: 11,
    title: 'Contacto',
    content: `Preguntas sobre privacidad:
Email: ${LEGAL_CONTACT.privacyEmail}
Dirección: ${LEGAL_CONTACT.address}
Teléfono: ${LEGAL_CONTACT.phone}`,
  },
] as const;

export const LEGAL_FOOTER = {
  terms:
    'Al usar esta aplicación, confirmas que has leído, entendido y aceptado estos términos y condiciones.',
  privacy:
    'Esta política cumple con la Ley 1581 de 2012 de Protección de Datos Personales de Colombia y el RGPD (si aplica).',
} as const;

export const BUTTON_TEXT = {
  understood: 'He leído y entiendo',
} as const;
