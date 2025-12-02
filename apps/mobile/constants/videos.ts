import { Image } from 'react-native';

type VideoSource = string | { uri: string };

export const localVideos: Record<string, VideoSource> = {
    // GIFs locales
    combinacion: { uri: Image.resolveAssetSource(require('../assets/videos/Combinacion.gif')).uri },
    directoDerecha: { uri: Image.resolveAssetSource(require('../assets/videos/directoDerecha.gif')).uri },
    dobleJab: { uri: Image.resolveAssetSource(require('../assets/videos/DobleJab.gif')).uri },
    esquivaLateral: { uri: Image.resolveAssetSource(require('../assets/videos/EsquivaLateral.gif')).uri },
    ganchoCuerpo: { uri: Image.resolveAssetSource(require('../assets/videos/GanchoCuerpo.gif')).uri },
    ganchoIzquierdo: { uri: Image.resolveAssetSource(require('../assets/videos/GanchoIzquierdo.gif')).uri },
    gancho: { uri: Image.resolveAssetSource(require('../assets/videos/GanchoCuerpo.gif')).uri },
    jab: { uri: Image.resolveAssetSource(require('../assets/videos/Jab.gif')).uri },
    uppercut: { uri: Image.resolveAssetSource(require('../assets/videos/Uppercut.gif')).uri },
    girosRusos: { uri: Image.resolveAssetSource(require('../assets/videos/fuerza/girosRusos.gif')).uri },
    sombraPesas: { uri: Image.resolveAssetSource(require('../assets/videos/fuerza/sombraPesas.gif')).uri },
    // Ejemplo de cómo incluir URLs externas:
    // miVideoExterno: { uri: 'https://ejemplo.com/mi-video.gif' }
};
export type LocalVideoKey = keyof typeof localVideos;
