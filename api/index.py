from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):

    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php", "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php", "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u", "group": "AUTO LIVE 1"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php", "group": "TVRI CHANNEL"},
        {"url": "https://malingya.goblogtv.workers.dev", "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVENT+"},
        {"url": "https://ayo.maling.pl/sawitku.m3u", "group": "EVENT SAWIT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORTS NEW"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://enakmalinggo.blog/maling/logo.php", "group": "OLAHRAGA"},
        {"url": "https://enakmalinggo.blog/maling/dens.php", "group": "DENS"}
    ]

    merged_content = "#EXTM3U\n"
    seen_urls = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }

    for pl in playlists:

        try:
            response = requests.get(
                pl["url"],
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:
                continue

            response.encoding = "utf-8"
            lines = response.text.splitlines()

            current_extinf = None
            extra_tags = []

            for line in lines:

                line = line.strip()

                if not line:
                    continue

                if line.startswith("#EXTM3U"):
                    continue

                # Metadata channel
                if line.startswith("#EXTINF"):

                    if "group-title=" not in line:
                        line = line.replace(
                            "#EXTINF:-1",
                            f'#EXTINF:-1 group-title="{pl["group"]}"'
                        )

                    current_extinf = line
                    extra_tags = []

                # Tag IPTV tambahan
                elif line.startswith("#"):

                    if current_extinf:
                        extra_tags.append(line)

                # URL stream
                else:

                    stream_url = line

                    if current_extinf and stream_url not in seen_urls:

                        seen_urls.add(stream_url)

                        merged_content += current_extinf + "\n"

                        if extra_tags:
                            merged_content += "\n".join(extra_tags) + "\n"

                        merged_content += stream_url + "\n"

                    current_extinf = None
                    extra_tags = []

        except Exception as e:
            print(f"Error {pl['url']}: {e}")

    return Response(
        merged_content,
        mimetype="audio/mpegurl; charset=utf-8"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
