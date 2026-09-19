from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def extract_host_and_tld(url):
    cleaned = url.strip()
    if cleaned.startswith("https://"):
        cleaned = cleaned[8:]
    elif cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    host = cleaned.split("/")[0].split("?")[0].split(":")[0]
    if not host:
        host = "example.com"

    parts = host.split(".")
    tld = parts[-1] if len(parts) > 1 else "com"
    return host, tld


def browsing_steps(url):
    host, tld = extract_host_and_tld(url)

    return [
        {
            "nodeId": "browser",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "Internal",
            "title": "Browser Cache Check",
            "message": f"User navigates to {url}. Browser checks local and OS DNS cache. Cache miss for '{host}'. Preparing DNS query.",
            "raw": f"CLIENT ACTION: NAVIGATE\nURL: {url}\nCache Check: {host} (Not found / Expired)\nAction: Request resolution via OS Stub Resolver",
            "fields": [
                {"label": "Target Host", "value": host},
                {"label": "Local Cache", "value": "Miss"},
                {"label": "Next Step", "value": "Query Stub Resolver"}
            ]
        },
        {
            "nodeId": "stub-resolver",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "C→S",
            "title": "Query to Stub Resolver",
            "message": f"OS Stub Resolver forwards the recursive query for {host} (Type A) to the configured recursive DNS server (8.8.8.8) via UDP port 53.",
            "raw": f"Standard query 0x1a2b A {host}\nSource: 192.168.1.105:54821\nDestination: 8.8.8.8:53 (UDP)\nFlags: Recursion Desired (RD = 1)",
            "fields": [
                {"label": "Resolver", "value": "OS Stub Resolver"},
                {"label": "Destination", "value": "8.8.8.8:53"},
                {"label": "Recursion Desired", "value": "1"},
                {"label": "Query Type", "value": "A (IPv4)"}
            ]
        },
        {
            "nodeId": "recursive-resolver",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "C→S",
            "title": "Recursive Resolver Resolution",
            "message": f"Recursive Resolver (8.8.8.8) checks its cache. On a cache miss, it begins iterative resolution starting from the Root DNS Servers (.).",
            "raw": f"RECURSIVE RESOLVER [8.8.8.8]\nLookup: {host}\nCache: Not Found\nAction: Initiating iterative query -> Root DNS Servers (.)",
            "fields": [
                {"label": "Server", "value": "Recursive (8.8.8.8)"},
                {"label": "Mode", "value": "Iterative Lookup"},
                {"label": "Target", "value": "Root Hints (.)"}
            ]
        },
        {
            "nodeId": "root-server",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "S→C",
            "title": "Root Server Referral (.)",
            "message": f"Root DNS Server (.) inspects query for {host} and responds with a referral to the Top-Level Domain (TLD) nameservers for .{tld}.",
            "raw": f"ROOT SERVER RESPONSE\nQuery: {host} IN A\nAnswer: 0 records\nAuthority: {tld}. IN NS a.gtld-servers.net\nAdditional: a.gtld-servers.net IN A 192.5.6.30",
            "fields": [
                {"label": "Server", "value": "Root [a.root-servers.net]"},
                {"label": "Referral", "value": f".{tld} TLD"},
                {"label": "Next Step", "value": f"Query .{tld} TLD Server"}
            ]
        },
        {
            "nodeId": "tld-server",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "S→C",
            "title": f"TLD Server Referral (.{tld})",
            "message": f"The .{tld} TLD Server receives the query for {host} and returns a referral to the Authoritative Name Servers for {host}.",
            "raw": f"TLD SERVER RESPONSE (.{tld})\nQuery: {host} IN A\nAuthority: {host}. IN NS ns1.{host}.\nAuthority: {host}. IN NS ns2.{host}.\nAdditional: ns1.{host}. IN A 204.79.197.200",
            "fields": [
                {"label": "Server", "value": f"TLD (.{tld})"},
                {"label": "Delegation", "value": f"ns1.{host}"},
                {"label": "Next Step", "value": "Query Authoritative NS"}
            ]
        },
        {
            "nodeId": "authoritative-dns",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "S→C",
            "title": "Authoritative DNS Answer",
            "message": f"Authoritative nameserver for {host} returns the definitive IPv4 (A) record mapping to 93.184.216.34.",
            "raw": f"AUTHORITATIVE ANSWER\nQuery: {host} IN A\nAnswer:\n  {host}. 300 IN A 93.184.216.34\nFlags: Authoritative Answer (AA = 1)",
            "fields": [
                {"label": "Server", "value": f"ns1.{host}"},
                {"label": "Record Type", "value": "A"},
                {"label": "IP Address", "value": "93.184.216.34"},
                {"label": "TTL", "value": "300s"}
            ]
        },
        {
            "nodeId": "dns-response",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "S→C",
            "title": "DNS Response to Browser",
            "message": f"Recursive resolver delivers the resolved IP address (93.184.216.34) back to the browser. Resolution complete.",
            "raw": f"DNS RESPONSE (TO BROWSER)\nStatus: NOERROR\nAnswer: {host} -> 93.184.216.34\nResolution Time: 28 ms\nNext Action: TCP Handshake + TLS on port 443",
            "fields": [
                {"label": "Domain", "value": host},
                {"label": "Resolved IP", "value": "93.184.216.34"},
                {"label": "Status", "value": "NOERROR"},
                {"label": "Port", "value": "443 (HTTPS)"}
            ]
        },
        {
            "nodeId": "tls-handshake",
            "section": "TLS",
            "protocol": "TLS 1.3",
            "direction": "C↔S",
            "title": "TLS 1.3 Handshake",
            "message": f"Browser and web server at 93.184.216.34 negotiate TLS 1.3. Cryptographic cipher suites, server certificate, and ECDHE session keys are exchanged.",
            "raw": f"1. Client Hello (SNI={host}, TLS 1.3, KeyShare: X25519)\n2. Server Hello (Cipher: TLS_AES_256_GCM_SHA384, Server KeyShare)\n3. EncryptedExtensions, Certificate (CN={host}), Finished\n4. Client Finished -> Symmetric Session Key Active",
            "fields": [
                {"label": "Protocol", "value": "TLS 1.3"},
                {"label": "SNI", "value": host},
                {"label": "Cipher", "value": "TLS_AES_256_GCM_SHA384"},
                {"label": "Session", "value": "Encrypted Channel Ready"}
            ]
        },
        {
            "nodeId": "https-request",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "C→S",
            "title": "HTTPS GET Request",
            "message": f"Browser transmits an encrypted HTTP GET request over the established TLS tunnel requesting web content for {host}.",
            "raw": f":method: GET\n:scheme: https\n:authority: {host}\n:path: /\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Visualizer/2.0\naccept: text/html,application/xhtml+xml\naccept-encoding: gzip, deflate, br",
            "fields": [
                {"label": "Method", "value": "GET"},
                {"label": "Path", "value": "/"},
                {"label": "Host", "value": host},
                {"label": "Security", "value": "TLS 1.3 Encrypted"}
            ]
        },
        {
            "nodeId": "web-server",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "S→C",
            "title": "Web Server 200 OK Response",
            "message": f"Web server returns encrypted HTTP 200 OK along with the HTML document payload. Browser renders the web page.",
            "raw": f":status: 200 OK\ncontent-type: text/html; charset=UTF-8\ncontent-encoding: gzip\nserver: web-cluster\ncontent-length: 1256\n\n[Payload: <!DOCTYPE html><html><head><title>{host}</title></head><body><h1>Welcome to {host}</h1></body></html>]",
            "fields": [
                {"label": "Status", "value": "200 OK"},
                {"label": "Content-Type", "value": "text/html"},
                {"label": "Content-Length", "value": "1,256 B"},
                {"label": "State", "value": "Page Rendered"}
            ]
        }
    ]


def mail_steps(to, subject, body):
    return [
        {
            "nodeId": "mail-client",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "Internal",
            "title": "Mail Client Preparation",
            "message": f"Mail User Agent (MUA) prepares message for '{to}' and initiates TCP connection to SMTP submission server on port 587.",
            "raw": f"CLIENT: mail.local (MUA)\nRecipient: {to}\nSubject: {subject}\nAction: Connect to smtp.example.com:587 (TCP Handshake established)",
            "fields": [
                {"label": "Client", "value": "MUA (Mail User Agent)"},
                {"label": "Server", "value": "smtp.example.com"},
                {"label": "Port", "value": "587 (Submission)"}
            ]
        },
        {
            "nodeId": "smtp-server",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "SMTP Server 220 Greeting",
            "message": "The mail server acknowledges TCP connection and greets the client with service readiness banner (RFC 5321).",
            "raw": "220 smtp.example.com ESMTP Postfix Service Ready (Mail Submission Agent)",
            "fields": [
                {"label": "Status Code", "value": "220"},
                {"label": "Server", "value": "smtp.example.com"},
                {"label": "State", "value": "Service Ready"}
            ]
        },
        {
            "nodeId": "ehlo",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "C↔S",
            "title": "EHLO Extended Handshake",
            "message": "Client identifies itself with EHLO. Server announces supported extensions including STARTTLS, AUTH, and 8BITMIME.",
            "raw": "C: EHLO client.network.local\nS: 250-smtp.example.com at your service\nS: 250-SIZE 35882577\nS: 250-8BITMIME\nS: 250-STARTTLS\nS: 250-AUTH PLAIN LOGIN\nS: 250 HELP",
            "fields": [
                {"label": "Command", "value": "EHLO"},
                {"label": "Status", "value": "250 OK"},
                {"label": "Extensions", "value": "STARTTLS, AUTH, SIZE"}
            ]
        },
        {
            "nodeId": "starttls",
            "section": "TLS",
            "protocol": "SMTP/TLS",
            "direction": "C↔S",
            "title": "STARTTLS Security Upgrade",
            "message": "Client issues STARTTLS command. Server agrees (220 Ready), and both parties negotiate TLS 1.3 encryption.",
            "raw": "C: STARTTLS\nS: 220 2.0.0 Ready to start TLS\n>>> [TLS 1.3 Cryptographic Handshake]\n>>> Cipher: TLS_AES_256_GCM_SHA384\n>>> [Session upgraded to secure encrypted channel]",
            "fields": [
                {"label": "Command", "value": "STARTTLS"},
                {"label": "Response", "value": "220 Ready"},
                {"label": "Security", "value": "TLS 1.3 Encrypted"}
            ]
        },
        {
            "nodeId": "auth",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "C↔S",
            "title": "Client Authentication (AUTH)",
            "message": "Client authenticates with mail server using base64 credentials over the secure encrypted channel.",
            "raw": "C: AUTH LOGIN\nS: 334 VXNlcm5hbWU6 (Username:)\nC: c3R1ZGVudEBleGFtcGxlLmNvbQ== (student@example.com)\nS: 334 UGFzc3dvcmQ6 (Password:)\nC: cGFzc3dvcmQxMjM= (********)\nS: 235 2.7.0 Authentication successful",
            "fields": [
                {"label": "Mechanism", "value": "AUTH LOGIN"},
                {"label": "User", "value": "student@example.com"},
                {"label": "Status", "value": "235 Auth Successful"}
            ]
        },
        {
            "nodeId": "mail-from",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "C↔S",
            "title": "MAIL FROM Envelope Sender",
            "message": "Client specifies sender reverse-path address for return notifications and bounce handling.",
            "raw": "C: MAIL FROM:<student@example.com> BODY=8BITMIME\nS: 250 2.1.0 Ok sender <student@example.com> accepted",
            "fields": [
                {"label": "Command", "value": "MAIL FROM"},
                {"label": "Sender", "value": "student@example.com"},
                {"label": "Response", "value": "250 OK"}
            ]
        },
        {
            "nodeId": "rcpt-to",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "C↔S",
            "title": "RCPT TO Envelope Recipient",
            "message": f"Client specifies destination recipient '{to}'. Server validates recipient mailbox.",
            "raw": f"C: RCPT TO:<{to}>\nS: 250 2.1.5 Ok recipient <{to}> accepted",
            "fields": [
                {"label": "Command", "value": "RCPT TO"},
                {"label": "Recipient", "value": to},
                {"label": "Response", "value": "250 OK"}
            ]
        },
        {
            "nodeId": "data",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "C↔S",
            "title": "DATA Message Transmission",
            "message": f"Client issues DATA. Server permits input (354). Client sends RFC 5322 headers, subject '{subject}', and message body ending with <CRLF>.<CRLF>.",
            "raw": f"C: DATA\nS: 354 End data with <CR><LF>.<CR><LF>\nC: From: \"Student\" <student@example.com>\nC: To: <{to}>\nC: Subject: {subject}\nC: Content-Type: text/plain; charset=utf-8\nC: \nC: {body}\nC: .",
            "fields": [
                {"label": "Command", "value": "DATA"},
                {"label": "Subject", "value": subject},
                {"label": "Termination", "value": "<CRLF>.<CRLF>"}
            ]
        },
        {
            "nodeId": "250-ok",
            "section": "SMTP",
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "250 OK Delivery Confirmation",
            "message": "Server confirms message accepted, queues for delivery with Queue ID, and acknowledges session closure via QUIT.",
            "raw": "S: 250 2.0.0 Ok: queued as 8A5B2F9C3\nC: QUIT\nS: 221 2.0.0 smtp.example.com Service closing transmission channel",
            "fields": [
                {"label": "Status", "value": "250 OK"},
                {"label": "Queue ID", "value": "8A5B2F9C3"},
                {"label": "Session", "value": "Closed (221 Bye)"}
            ]
        }
    ]


def streaming_steps(quality, url="https://video.example.com/stream"):
    return [
        {
            "nodeId": "browser",
            "section": "Streaming",
            "protocol": "Media",
            "direction": "Internal",
            "title": "HTML5 Video Player Init",
            "message": f"User initiates video streaming at {quality}. HTML5 Media Source Extensions (MSE) player initializes buffer targets.",
            "raw": f"PLAYER_ACTION: Initialize Stream\nTarget: {url}\nQuality Preset: {quality}\nPlayer: HTML5 MSE (Media Source Extensions)\nBuffer Target: 10 seconds ahead",
            "fields": [
                {"label": "Player", "value": "HTML5 MSE"},
                {"label": "Selected Quality", "value": quality},
                {"label": "State", "value": "Initializing"}
            ]
        },
        {
            "nodeId": "dns",
            "section": "DNS",
            "protocol": "DNS",
            "direction": "C↔S",
            "title": "DNS CDN Edge Resolution",
            "message": "Browser resolves Anycast CDN edge server domain (video-cdn.example.com) for optimized video streaming.",
            "raw": "DNS QUERY: video-cdn.example.com IN A\nDNS ANSWER: video-cdn.example.com 60 IN A 104.244.42.129\nEdge Location: Region Anycast POP",
            "fields": [
                {"label": "Domain", "value": "video-cdn.example.com"},
                {"label": "CDN Edge IP", "value": "104.244.42.129"},
                {"label": "TTL", "value": "60s"}
            ]
        },
        {
            "nodeId": "tls",
            "section": "TLS",
            "protocol": "TLS 1.3",
            "direction": "C↔S",
            "title": "TLS 1.3 Handshake with CDN",
            "message": "Fast TLS 1.3 handshake with CDN edge node negotiating HTTP/2 (ALPN: h2) for multiplexed video chunk delivery.",
            "raw": "TLS 1.3 HANDSHAKE (CDN Edge)\nALPN: h2 (HTTP/2)\nServer Certificate: *.video-cdn.example.com\nCipher: TLS_AES_128_GCM_SHA256\nLatency: 12ms to Edge",
            "fields": [
                {"label": "Security", "value": "TLS 1.3"},
                {"label": "ALPN", "value": "h2 (HTTP/2)"},
                {"label": "Latency", "value": "12ms"}
            ]
        },
        {
            "nodeId": "http-request",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "C→S",
            "title": "HTTP Master Playlist Request",
            "message": "Client sends HTTP/2 GET request for HLS master streaming manifest (master.m3u8).",
            "raw": "GET /hls/master.m3u8 HTTP/2\nHost: video-cdn.example.com\nAccept: application/vnd.apple.mpegurl\nUser-Agent: VideoStreamPlayer/3.1",
            "fields": [
                {"label": "Method", "value": "GET"},
                {"label": "Path", "value": "/hls/master.m3u8"},
                {"label": "Protocol", "value": "HLS over HTTP/2"}
            ]
        },
        {
            "nodeId": "manifest-stream-info",
            "section": "Streaming",
            "protocol": "HLS / Manifest",
            "direction": "S→C",
            "title": "Manifest & Stream Info Response",
            "message": "CDN delivers M3U8 multi-bitrate playlist with profiles for 360p, 480p, 720p, and 1080p.",
            "raw": "HTTP/2 200 OK\nContent-Type: application/vnd.apple.mpegurl\n\n#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,360p.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=854x480,480p.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720,720p.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=5500000,RESOLUTION=1920x1080,1080p.m3u8",
            "fields": [
                {"label": "Format", "value": "M3U8 Master Playlist"},
                {"label": "Profiles", "value": "360p, 480p, 720p, 1080p"},
                {"label": "Status", "value": "200 OK"}
            ]
        },
        {
            "nodeId": "quality-selection",
            "section": "Streaming",
            "protocol": "ABR Logic",
            "direction": "Internal",
            "title": "Quality Selection & ABR Decision",
            "message": f"Adaptive Bitrate (ABR) engine evaluates network throughput and selects '{quality}' resolution.",
            "raw": f"ABR DECISION ENGINE:\nAvailable Throughput: 18.4 Mbps\nUser Selection: {quality}\nTarget Playlist: /hls/{quality}/index.m3u8\nChunk Length: 4.0 seconds per segment",
            "fields": [
                {"label": "Selected Quality", "value": quality},
                {"label": "Bitrate", "value": "Optimal"},
                {"label": "Engine", "value": "Adaptive Bitrate (ABR)"}
            ]
        },
        {
            "nodeId": "media-segment-1",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "C↔S",
            "title": "Media Segment 1 Download (0-4s)",
            "message": f"Client downloads video chunk 1 (00:00 - 00:04) for {quality}. CDN returns binary MPEG-TS / fMP4 data.",
            "raw": f"GET /hls/{quality}/segment_001.ts HTTP/2\n\nHTTP/2 200 OK\nContent-Type: video/mp2t\nContent-Length: 1,385,420 bytes\n[Segment 1: Timestamps 00:00.000 -> 00:04.000]",
            "fields": [
                {"label": "Segment", "value": "1 (00:00 - 00:04)"},
                {"label": "Size", "value": "1.38 MB"},
                {"label": "Status", "value": "200 OK"}
            ]
        },
        {
            "nodeId": "media-segment-2",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "C↔S",
            "title": "Media Segment 2 Download (4-8s)",
            "message": f"Client downloads video chunk 2 (00:04 - 00:08) for {quality} while chunk 1 starts buffering.",
            "raw": f"GET /hls/{quality}/segment_002.ts HTTP/2\n\nHTTP/2 200 OK\nContent-Type: video/mp2t\nContent-Length: 1,420,110 bytes\n[Segment 2: Timestamps 00:04.000 -> 00:08.000]",
            "fields": [
                {"label": "Segment", "value": "2 (00:04 - 00:08)"},
                {"label": "Size", "value": "1.42 MB"},
                {"label": "Buffer Added", "value": "+4.0 seconds"}
            ]
        },
        {
            "nodeId": "media-segment-3",
            "section": "HTTP",
            "protocol": "HTTP/2",
            "direction": "C↔S",
            "title": "Media Segment 3 Download (8-12s)",
            "message": f"Client downloads video chunk 3 (00:08 - 00:12) to build a robust forward buffer and prevent stutter.",
            "raw": f"GET /hls/{quality}/segment_003.ts HTTP/2\n\nHTTP/2 200 OK\nContent-Type: video/mp2t\nContent-Length: 1,390,880 bytes\n[Segment 3: Timestamps 00:08.000 -> 00:12.000]",
            "fields": [
                {"label": "Segment", "value": "3 (00:08 - 00:12)"},
                {"label": "Size", "value": "1.39 MB"},
                {"label": "Buffer Health", "value": "12s Ahead"}
            ]
        },
        {
            "nodeId": "playback",
            "section": "Streaming",
            "protocol": "Media",
            "direction": "Internal",
            "title": "Demux, Decode & Smooth Playback",
            "message": "MSE appends segments to SourceBuffer. Hardware video decoder plays video smoothly on screen.",
            "raw": "MSE PIPELINE:\nSourceBuffer.appendBuffer() -> Demux Audio/Video Tracks\nHardware Acceleration: Active (GPU Decoders)\nPlayback State: PLAYING (Smooth 60 fps, 0 buffer under-runs)\nBuffer Health: Green (Optimal)",
            "fields": [
                {"label": "Playback State", "value": "Playing Smoothly"},
                {"label": "Resolution", "value": quality},
                {"label": "Hardware Decoders", "value": "H.264 / AAC"}
            ]
        }
    ]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.get_json() or {}
    activity = data.get("activity")

    if activity == "browsing":
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "Please enter a URL"}), 400
        return jsonify({"steps": browsing_steps(url)})

    elif activity == "mail":
        to = data.get("to", "").strip()
        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip()

        if not to or not subject or not body:
            return jsonify({
                "error": "Please fill in To, Subject and Body"
            }), 400

        return jsonify({
            "steps": mail_steps(to, subject, body)
        })

    elif activity == "streaming":
        quality = data.get("quality", "720p")
        url = data.get("url", "").strip() or "https://video.example.com/stream"
        return jsonify({
            "steps": streaming_steps(quality, url)
        })

    return jsonify({"error": "Unknown activity"}), 400


if __name__ == "__main__":
    app.run(debug=True)