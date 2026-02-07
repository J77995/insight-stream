import { forwardRef, useImperativeHandle, useRef } from "react";
import YouTube, { YouTubeProps, YouTubePlayer } from "react-youtube";

interface VideoPlayerProps {
  videoId: string;
}

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void;
  playVideo: () => void;
  pauseVideo: () => void;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  ({ videoId }, ref) => {
    const playerRef = useRef<YouTubePlayer | null>(null);

    useImperativeHandle(ref, () => ({
      seekTo: (seconds: number) => {
        if (playerRef.current) {
          playerRef.current.seekTo(seconds, true);
        }
      },
      playVideo: () => {
        if (playerRef.current) {
          playerRef.current.playVideo();
        }
      },
      pauseVideo: () => {
        if (playerRef.current) {
          playerRef.current.pauseVideo();
        }
      },
    }));

    const onReady: YouTubeProps["onReady"] = (event) => {
      playerRef.current = event.target;
    };

    const opts: YouTubeProps["opts"] = {
      width: "100%",
      height: "100%",
      playerVars: {
        autoplay: 0,
        modestbranding: 1,
        rel: 0,
      },
    };

    return (
      <div className="p-4 border-b border-border">
        <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-secondary">
          <YouTube
            videoId={videoId}
            opts={opts}
            onReady={onReady}
            className="absolute inset-0"
            iframeClassName="w-full h-full"
          />
        </div>
      </div>
    );
  }
);

VideoPlayer.displayName = "VideoPlayer";

export default VideoPlayer;
