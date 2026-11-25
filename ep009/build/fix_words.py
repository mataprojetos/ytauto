"""Repõe a pontuação/grafia exata do guião nas palavras do whisper (mesmo número de palavras)."""
import json
SCRIPT = """You just fell out of a plane. No parachute. Good news: you've got about three minutes to think about your choices. First problem: you're ten kilometers up. It's minus fifty degrees, and there's barely any air. You might pass out. Honestly? Best nap of your life. You'll wake up on the way down. Now you're falling at 200 kilometers per hour. That's your top speed. Spread your arms and legs like a starfish. It actually slows you down. Water? Bad idea. At this speed, it hits like concrete. What you want is snow. Or trees. Or a really, really soft hill. Sounds impossible? In 1944, a pilot fell almost six kilometers… into pine trees and deep snow. He walked away with a sprained leg. That one made me scratch my head. And in 1972, a flight attendant fell over ten kilometers, trapped in a piece of the plane. She survived. She still holds the world record. So next time you're on a plane, you'll know exactly what to do… if you…""".split()
w = json.load(open("build/words_raw.json"))
assert len(w) == len(SCRIPT), (len(w), len(SCRIPT))
for x, s in zip(w, SCRIPT): x["w"] = s
json.dump(w, open("build/words.json", "w"), indent=0); print(len(w))
