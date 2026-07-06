"""
Pac-Man Arcade Sound Engine
============================
All sounds are procedurally generated (no external audio files required).

Design notes:
- The mixer is (re)initialized to a known format (44100 Hz, 16-bit, mono).
  pygame.init() in main.py already opens the mixer with its own defaults
  (stereo), and raw mono buffers played through a stereo mixer come out
  garbled at double speed — so we quit and reopen it with our format.
- Tones use a band-limited "soft square" (first four odd harmonics) instead
  of a naive hard square: it keeps the chippy arcade character without the
  aliasing harshness.
- Every sound gets a short attack/release envelope so nothing clicks.
- The siren is a single seamless up-down sweep cycle looped with loops=-1,
  instead of being re-triggered every time the channel goes idle.
"""

import math
import pygame
import numpy as np

# ── Audio settings ─────────────────────────────────────────────────────────────
SAMPLE_RATE = 44100
SAMPLE_SIZE = -16       # 16-bit signed
CHANNELS = 1

_initialized = False


def _init_mixer():
    """Ensure the mixer runs at our exact format (mono buffers require it)."""
    global _initialized
    if _initialized:
        return
    if pygame.mixer.get_init() != (SAMPLE_RATE, SAMPLE_SIZE, CHANNELS):
        pygame.mixer.quit()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=SAMPLE_SIZE,
                          channels=CHANNELS, buffer=512)
    pygame.mixer.set_num_channels(8)
    _initialized = True


# ── Waveform generators ────────────────────────────────────────────────────────

def _apply_envelope(samples, attack=0.004, release=0.02):
    """Short fade-in/out so sounds never click at their edges."""
    n = len(samples)
    if n == 0:
        return samples
    a = min(n, max(1, int(SAMPLE_RATE * attack)))
    r = min(n, max(1, int(SAMPLE_RATE * release)))
    samples[:a] *= np.linspace(0.0, 1.0, a, dtype=np.float32)
    samples[-r:] *= np.linspace(1.0, 0.0, r, dtype=np.float32)
    return samples


def _wave_from_phase(phase, volume, wave):
    """Render a waveform from a phase array."""
    if wave == 'sine':
        samples = np.sin(phase)
    elif wave == 'triangle':
        samples = (2.0 / math.pi) * np.arcsin(np.sin(phase))
    else:  # 'soft' — band-limited square (first four odd harmonics)
        samples = (np.sin(phase)
                   + np.sin(3 * phase) / 3
                   + np.sin(5 * phase) / 5
                   + np.sin(7 * phase) / 7) / 1.2
    return (volume * samples).astype(np.float32)


def _generate_tone(frequency, duration, volume=0.3, wave='soft'):
    """Generate a steady tone with a click-free envelope."""
    num_samples = int(SAMPLE_RATE * duration)
    t = np.arange(num_samples, dtype=np.float32) / SAMPLE_RATE
    phase = 2.0 * math.pi * frequency * t
    return _apply_envelope(_wave_from_phase(phase, volume, wave))


def _generate_sweep(start_freq, end_freq, duration, volume=0.3, wave='sine'):
    """Generate a smooth frequency sweep via phase accumulation."""
    num_samples = int(SAMPLE_RATE * duration)
    freqs = np.linspace(start_freq, end_freq, num_samples, dtype=np.float32)
    phase = np.cumsum(2.0 * math.pi * freqs / SAMPLE_RATE)
    return _apply_envelope(_wave_from_phase(phase, volume, wave))


def _generate_siren_cycle(low_freq, high_freq, duration, volume=0.1):
    """One seamless up-then-down sweep cycle, meant to be looped forever."""
    num_samples = int(SAMPLE_RATE * duration)
    half = num_samples // 2
    freqs = np.concatenate([
        np.linspace(low_freq, high_freq, half, dtype=np.float32),
        np.linspace(high_freq, low_freq, num_samples - half, dtype=np.float32),
    ])
    phase = np.cumsum(2.0 * math.pi * freqs / SAMPLE_RATE)
    return _apply_envelope(_wave_from_phase(phase, volume, 'sine'),
                           attack=0.002, release=0.002)


def _generate_sequence(notes, volume=0.3, wave='soft'):
    """
    Generate a sequence of notes.
    notes: list of (frequency, duration) tuples; frequency 0 is a rest.
    """
    all_samples = []
    for freq, dur in notes:
        if freq == 0:  # rest
            samples = np.zeros(int(SAMPLE_RATE * dur), dtype=np.float32)
        else:
            samples = _generate_tone(freq, dur, volume, wave)
        all_samples.append(samples)
    return np.concatenate(all_samples)


def _samples_to_sound(samples):
    """Convert numpy float32 samples to a pygame Sound object."""
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=int_samples.tobytes())


# ── Sound cache ────────────────────────────────────────────────────────────────

_sound_cache = {}


class PacManSounds:
    """
    Manages all game sounds.
    Dedicated channels: 0 = effects, 1 = siren loop, 2 = chomp.
    """

    def __init__(self):
        _init_mixer()
        self._channel = pygame.mixer.Channel(0)
        self._siren_channel = pygame.mixer.Channel(1)
        self._chomp_channel = pygame.mixer.Channel(2)

        self._chomp_toggle = False   # alternates between the two waka pitches
        self._current_siren = None   # 'siren' | 'siren_frightened' | None

        self._build_sounds()

    def _build_sounds(self):
        """Pre-generate all sound effects."""
        cache = _sound_cache

        # ── Waka-waka chomp: alternating down/up chirps ──────────────────────
        if 'chomp1' not in cache:
            cache['chomp1'] = _samples_to_sound(
                _generate_sweep(550, 220, 0.06, volume=0.25, wave='triangle'))
        if 'chomp2' not in cache:
            cache['chomp2'] = _samples_to_sound(
                _generate_sweep(220, 550, 0.06, volume=0.25, wave='triangle'))

        # ── Power pellet (descending swoop) ──────────────────────────────────
        if 'power_pellet' not in cache:
            cache['power_pellet'] = _samples_to_sound(
                _generate_sweep(780, 160, 0.35, volume=0.3, wave='sine'))

        # ── Ghost eaten (rising "whoop") ─────────────────────────────────────
        if 'ghost_eaten' not in cache:
            cache['ghost_eaten'] = _samples_to_sound(
                _generate_sweep(200, 950, 0.35, volume=0.3, wave='sine'))

        # ── Death (descending warble, then two low chirps) ───────────────────
        if 'death' not in cache:
            parts = []
            for f in (720, 620, 530, 450, 380, 320):
                parts.append(_generate_sweep(f, f * 0.62, 0.14,
                                             volume=0.32, wave='sine'))
            parts.append(np.zeros(int(SAMPLE_RATE * 0.06), dtype=np.float32))
            for _ in range(2):
                parts.append(_generate_sweep(150, 420, 0.1,
                                             volume=0.32, wave='sine'))
                parts.append(np.zeros(int(SAMPLE_RATE * 0.05), dtype=np.float32))
            cache['death'] = _samples_to_sound(np.concatenate(parts))

        # ── Game start jingle ────────────────────────────────────────────────
        if 'game_start' not in cache:
            notes = [
                (262, 0.12), (330, 0.12), (392, 0.12),
                (523, 0.25), (0, 0.05),
                (523, 0.12), (587, 0.12), (659, 0.12),
                (784, 0.3),
            ]
            cache['game_start'] = _samples_to_sound(
                _generate_sequence(notes, volume=0.3))

        # ── Level clear jingle ──────────────────────────────────────────────
        if 'level_clear' not in cache:
            notes = [
                (523, 0.1), (659, 0.1), (784, 0.1),
                (1047, 0.2), (0, 0.05),
                (1047, 0.1), (784, 0.1), (659, 0.1),
                (523, 0.1), (659, 0.1), (784, 0.1),
                (1047, 0.3),
            ]
            cache['level_clear'] = _samples_to_sound(
                _generate_sequence(notes, volume=0.3))

        # ── Fruit bonus sound ─────────────────────────────────────────────────
        if 'fruit_bonus' not in cache:
            notes = [
                (440, 0.08), (554, 0.08), (659, 0.08),
                (880, 0.2),
            ]
            cache['fruit_bonus'] = _samples_to_sound(
                _generate_sequence(notes, volume=0.28))

        # ── Extra life sound ─────────────────────────────────────────────────
        if 'extra_life' not in cache:
            notes = [
                (523, 0.1), (659, 0.1), (784, 0.2),
            ]
            cache['extra_life'] = _samples_to_sound(
                _generate_sequence(notes, volume=0.3))

        # ── Sirens (seamless loop cycles) ────────────────────────────────────
        if 'siren' not in cache:
            cache['siren'] = _samples_to_sound(
                _generate_siren_cycle(200, 400, 0.5, volume=0.09))
        if 'siren_frightened' not in cache:
            cache['siren_frightened'] = _samples_to_sound(
                _generate_siren_cycle(380, 550, 0.28, volume=0.08))

    # ── Public sound methods ──────────────────────────────────────────────────

    def play_chomp(self):
        """Play the alternating waka-waka chomp sound."""
        snd = _sound_cache['chomp1' if self._chomp_toggle else 'chomp2']
        self._chomp_toggle = not self._chomp_toggle
        self._chomp_channel.play(snd)

    def play_power_pellet(self):
        """Play power pellet sound."""
        self._channel.play(_sound_cache['power_pellet'])

    def play_ghost_eaten(self):
        """Play ghost eaten sound."""
        self._channel.play(_sound_cache['ghost_eaten'])

    def play_death(self):
        """Play pac-man death sound."""
        self.stop_siren()
        self._chomp_channel.stop()
        self._channel.play(_sound_cache['death'])

    def play_game_start(self):
        """Play the game start jingle."""
        self._channel.play(_sound_cache['game_start'])

    def play_level_clear(self):
        """Play the level clear jingle."""
        self.stop_siren()
        self._channel.play(_sound_cache['level_clear'])

    def play_fruit_bonus(self):
        """Play fruit bonus sound."""
        self._channel.play(_sound_cache['fruit_bonus'])

    def play_extra_life(self):
        """Play extra life sound."""
        self._channel.play(_sound_cache['extra_life'])

    # ── Siren / ambient sound ─────────────────────────────────────────────────

    def play_siren(self, frightened=False):
        """Start (or switch) the looping siren sound."""
        want = 'siren_frightened' if frightened else 'siren'
        if self._current_siren != want:
            self._siren_channel.play(_sound_cache[want], loops=-1)
            self._current_siren = want

    def stop_siren(self):
        """Stop the siren."""
        self._siren_channel.stop()
        self._current_siren = None

    def update(self, dt, ghosts):
        """
        Update sound state. Called each frame while playing.
        Keeps the correct siren looping for the current ghost state.
        """
        from ghost import GhostMode
        any_frightened = any(g.mode == GhostMode.FRIGHTENED for g in ghosts)
        self.play_siren(frightened=any_frightened)
