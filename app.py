from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def browsing_steps(url):
    host = url.replace("https://", "").replace("http://", "").split("/")[0]

    return [
        {
            "protocol": "DNS",
            "direction": "C→S",
            "title": "DNS Query",
            "message": f"Client asks DNS for the IP address of {host}.",
            "raw": f"Query: A {host}",
            "fields": [
                {"label": "Query Type", "value": "A"},
                {"label": "Domain", "value": host}
            ]
        },
        {
            "protocol": "DNS",
            "direction": "S→C",
            "title": "DNS Response",
            "message": f"DNS returns an IPv4 address for {host}.",
            "raw": f"Answer: {host} → 93.184.216.34",
            "fields": [
                {"label": "Type", "value": "A"},
                {"label": "IP", "value": "93.184.216.34"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "C→S",
            "title": "HTTP GET Request",
            "message": "Client requests the web page.",
            "raw": f"GET / HTTP/1.1\nHost: {host}\nConnection: keep-alive",
            "fields": [
                {"label": "Method", "value": "GET"},
                {"label": "Host", "value": host},
                {"label": "Version", "value": "HTTP/1.1"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "S→C",
            "title": "HTTP Response",
            "message": "Server sends a successful response.",
            "raw": "HTTP/1.1 200 OK\nContent-Type: text/html",
            "fields": [
                {"label": "Status", "value": "200 OK"},
                {"label": "Content-Type", "value": "text/html"}
            ]
        }
    ]


def mail_steps(to, subject, body):
    return [
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "SMTP Server Greeting",
            "message": "The mail server welcomes the client.",
            "raw": "220 mail.example.com Service Ready",
            "fields": [
                {"label": "Server", "value": "mail.example.com"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "C→S",
            "title": "EHLO",
            "message": "Client identifies itself.",
            "raw": "EHLO student.example.com",
            "fields": [
                {"label": "Command", "value": "EHLO"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "EHLO Response",
            "message": "Server accepts the greeting.",
            "raw": "250 mail.example.com OK",
            "fields": [
                {"label": "Status", "value": "250 OK"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "C→S",
            "title": "MAIL FROM",
            "message": "Client specifies the sender.",
            "raw": "MAIL FROM:<student@example.com>",
            "fields": [
                {"label": "Command", "value": "MAIL FROM"},
                {"label": "Sender", "value": "student@example.com"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "MAIL FROM Response",
            "message": "Server accepts the sender.",
            "raw": "250 2.1.0 OK",
            "fields": [
                {"label": "Status", "value": "250 2.1.0 OK"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "C→S",
            "title": "RCPT TO",
            "message": "Client specifies the recipient.",
            "raw": f"RCPT TO:<{to}>",
            "fields": [
                {"label": "Command", "value": "RCPT TO"},
                {"label": "Recipient", "value": to}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "RCPT TO Response",
            "message": "Server accepts the recipient.",
            "raw": "250 2.1.5 OK",
            "fields": [
                {"label": "Status", "value": "250 2.1.5 OK"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "C→S",
            "title": "DATA",
            "message": "Client sends the email content.",
            "raw": f"DATA\nSubject: {subject}\n\n{body}\n.",
            "fields": [
                {"label": "Command", "value": "DATA"},
                {"label": "Subject", "value": subject}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "Message Accepted",
            "message": "Server accepts the message.",
            "raw": "250 2.0.0 Message accepted for delivery",
            "fields": [
                {"label": "Status", "value": "250 2.0.0"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "C→S",
            "title": "QUIT",
            "message": "Client closes the SMTP session.",
            "raw": "QUIT",
            "fields": [
                {"label": "Command", "value": "QUIT"}
            ]
        },
        {
            "protocol": "SMTP",
            "direction": "S→C",
            "title": "Session Closed",
            "message": "Server closes the connection.",
            "raw": "221 2.0.0 Bye",
            "fields": [
                {"label": "Status", "value": "221 2.0.0"}
            ]
        }
    ]


def streaming_steps(quality):
    return [
        {
            "protocol": "DNS",
            "direction": "C→S",
            "title": "DNS Query",
            "message": "Client asks DNS for the streaming server.",
            "raw": "Query: A video.example.com",
            "fields": [
                {"label": "Domain", "value": "video.example.com"}
            ]
        },
        {
            "protocol": "DNS",
            "direction": "S→C",
            "title": "DNS Response",
            "message": "DNS returns the streaming server IP.",
            "raw": "Answer: video.example.com → 203.0.113.20",
            "fields": [
                {"label": "IP", "value": "203.0.113.20"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "C→S",
            "title": "Manifest Request",
            "message": f"Client requests the playlist for {quality} quality.",
            "raw": "GET /video/playlist.m3u8 HTTP/1.1\nHost: video.example.com",
            "fields": [
                {"label": "Method", "value": "GET"},
                {"label": "Quality", "value": quality}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "S→C",
            "title": "Manifest Response",
            "message": "Server returns the video playlist.",
            "raw": "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=2500000\nsegment_01.ts",
            "fields": [
                {"label": "Type", "value": "Playlist / Manifest"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "C→S",
            "title": "Segment 1 Request",
            "message": "Client requests video segment 1.",
            "raw": "GET /video/segment_01.ts HTTP/1.1",
            "fields": [
                {"label": "Segment", "value": "01"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "S→C",
            "title": "Segment 1 Response",
            "message": "Server sends video segment 1.",
            "raw": "HTTP/1.1 200 OK\nContent-Type: video/mp2t",
            "fields": [
                {"label": "Status", "value": "200 OK"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "C→S",
            "title": "Segment 2 Request",
            "message": "Client requests video segment 2.",
            "raw": "GET /video/segment_02.ts HTTP/1.1",
            "fields": [
                {"label": "Segment", "value": "02"}
            ]
        },
        {
            "protocol": "HTTP",
            "direction": "S→C",
            "title": "Segment 2 Response",
            "message": "Server sends video segment 2.",
            "raw": "HTTP/1.1 200 OK\nContent-Type: video/mp2t",
            "fields": [
                {"label": "Status", "value": "200 OK"}
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

        return jsonify({
            "steps": streaming_steps(quality)
        })

    return jsonify({"error": "Unknown activity"}), 400


if __name__ == "__main__":
    app.run(debug=True)