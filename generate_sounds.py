from pydub.generators import Sine

# Correct sound
Sine(440).to_audio_segment(duration=500).export("correct.wav", format="wav")

# Wrong sound
Sine(220).to_audio_segment(duration=500).export("wrong.wav", format="wav")

# Timeout sound
Sine(330).to_audio_segment(duration=500).fade_out(500).export("timeout.wav", format="wav")