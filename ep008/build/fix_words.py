"""Junta os números partidos pelo whisper ("5" ",000") e repõe a pontuação exata do guião."""
import json
SCRIPT = """You just jumped into a hole that goes straight through the Earth. For one second, it feels normal. Then you realize… there's no bottom. That one made me scratch my head. Let's say this tunnel is magic: no air, no heat. Because down here, it's over 5,000 degrees. You fall faster… and faster. At the center, you're flying at 28,000 kilometers per hour. And you feel completely weightless. Then gravity flips. Now it's pulling you back. You slow down… and slow down… But wait until you see where you end up. Jump from the United States, and 42 minutes later you pop out in the Indian Ocean, southwest of Australia. You float there for one second… And then you fall back in. Again. And again. Forever. Which means, right now…""".split()
w = json.load(open("build/words_raw.json")); out = []
for x in w:
    if x["w"].startswith(",") and out: out[-1]["w"] += x["w"]; out[-1]["e"] = x["e"]
    else: out.append(dict(x))
assert len(out) == len(SCRIPT), (len(out), len(SCRIPT))
for x, s in zip(out, SCRIPT): x["w"] = s
json.dump(out, open("build/words.json", "w"), indent=0); print(len(out))
