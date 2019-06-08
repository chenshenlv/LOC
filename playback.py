from enum import Enum, unique
import time


@unique
class Backend(Enum):
    PYAUDIO = 1
    PYGAME = 2
    SOUNDDEVICE = 3


class Playback():

    def __init__(self, backend:Backend):
        self.backend = backend

    def play(self, freq, buffer, play_time: float = 10, channel: int = 1):
        if self.backend == Backend.PYAUDIO:
            self._pyaudio_play(freq=freq, buffer=buffer,
                               play_time=play_time, channel=channel)
        elif self.backend == Backend.PYGAME:
            self._pygame_play(freq=freq, buffer=buffer,
                              play_time=play_time, channel=channel)
        elif self.backend == Backend.SOUNDDEVICE:
            self._sounddevice_play(
                freq=freq, buffer=buffer, play_time=play_time, channel=channel)
        else:
            raise RuntimeError(
                "Trying to use unknown audio backend for playback.")

    def _pyaudio_play(self, freq, buffer, play_time, channel):
        # PyAudio doesn't seem to have context manager
        import pyaudio
        player = pyaudio.PyAudio()
        stream = player.open(
            rate=freq, format=pyaudio.paInt16, channels=channel, output=True)
        stream.write(buffer.tobytes())

        stream.close()  # this blocks until sound finishes playing
        player.terminate()

    def _sounddevice_play(self, freq, buffer, play_time, channel, loop=False):
        import sounddevice
        sounddevice.play(buffer, freq, loop=loop)  # releases GIL
        # NOTE: Since sound playback is async, allow sound playback to finish before Python exits
#        time.sleep(play_time*2)

    def _pygame_play(self, freq, buffer, play_time, channel):
        import pygame
        pygame.mixer.pre_init(freq, size=-16, channels=channel)
        pygame.mixer.init()
        sound = pygame.sndarray.make_sound(buffer)
        sound.play()
        # NOTE: Since sound playback is async, allow sound playback to finish before Python exits
        time.sleep(play_time*2)
