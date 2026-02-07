/**
 * Converts a timestamp string in mm:ss format to seconds
 * @param timestamp - Timestamp in format "mm:ss" (e.g., "1:23", "0:05", "10:45")
 * @returns The timestamp converted to seconds, or 0 if invalid
 * 
 * @example
 * timestampToSeconds("0:05") // returns 5
 * timestampToSeconds("1:23") // returns 83
 * timestampToSeconds("10:45") // returns 645
 */
export const timestampToSeconds = (timestamp: string): number => {
  // Match mm:ss format
  const match = timestamp.match(/^(\d+):(\d{2})$/);
  
  if (!match) {
    console.warn(`Invalid timestamp format: ${timestamp}`);
    return 0;
  }
  
  const minutes = parseInt(match[1], 10);
  const seconds = parseInt(match[2], 10);
  
  return minutes * 60 + seconds;
};

/**
 * Converts seconds to a timestamp string in mm:ss format
 * @param seconds - Number of seconds
 * @returns Timestamp in format "mm:ss"
 * 
 * @example
 * secondsToTimestamp(5) // returns "0:05"
 * secondsToTimestamp(83) // returns "1:23"
 * secondsToTimestamp(645) // returns "10:45"
 */
export const secondsToTimestamp = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};
