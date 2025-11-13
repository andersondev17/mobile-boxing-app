/**
 * Componente que muestra el video de la cámara y el canvas de overlay
 */
const VideoStream = ({ videoRef, canvasRef }) => {
  return (
    <div className="video-container">
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline 
        muted
      />
      <canvas ref={canvasRef} />
    </div>
  )
}

export default VideoStream















