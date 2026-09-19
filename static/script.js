document.addEventListener("DOMContentLoaded", () => {

    // -------------------------------------------------------------
    // NODE DEFINITIONS FOR EACH PROTOCOL FLOW
    // -------------------------------------------------------------
    const PROTOCOL_NODES = {
        browsing: [
            { id: "browser", label: "Browser", section: "DNS" },
            { id: "stub-resolver", label: "Stub Resolver", section: "DNS" },
            { id: "recursive-resolver", label: "Recursive Resolver", section: "DNS" },
            { id: "root-server", label: "Root Server", section: "DNS" },
            { id: "tld-server", label: "TLD Server", section: "DNS" },
            { id: "authoritative-dns", label: "Authoritative DNS", section: "DNS" },
            { id: "dns-response", label: "DNS Response", section: "DNS" },
            { id: "tls-handshake", label: "TLS Handshake", section: "TLS" },
            { id: "https-request", label: "HTTPS Request", section: "HTTP" },
            { id: "web-server", label: "Web Server", section: "HTTP" }
        ],
        mail: [
            { id: "mail-client", label: "Mail Client", section: "SMTP" },
            { id: "smtp-server", label: "SMTP Server", section: "SMTP" },
            { id: "ehlo", label: "EHLO", section: "SMTP" },
            { id: "starttls", label: "STARTTLS", section: "TLS" },
            { id: "auth", label: "AUTH", section: "SMTP" },
            { id: "mail-from", label: "MAIL FROM", section: "SMTP" },
            { id: "rcpt-to", label: "RCPT TO", section: "SMTP" },
            { id: "data", label: "DATA", section: "SMTP" },
            { id: "250-ok", label: "250 OK", section: "SMTP" }
        ],
        streaming: [
            { id: "browser", label: "Browser", section: "Media" },
            { id: "dns", label: "DNS", section: "DNS" },
            { id: "tls", label: "TLS", section: "TLS" },
            { id: "http-request", label: "HTTP Request", section: "HTTP" },
            { id: "manifest-stream-info", label: "Manifest / Stream Info", section: "Streaming" },
            { id: "quality-selection", label: "Quality Selection", section: "Streaming" },
            { id: "media-segment-1", label: "Media Segment 1", section: "HTTP" },
            { id: "media-segment-2", label: "Media Segment 2", section: "HTTP" },
            { id: "media-segment-3", label: "Media Segment 3", section: "HTTP" },
            { id: "playback", label: "Playback", section: "Streaming" }
        ]
    };

    let currentActivity = "browsing";
    let steps = [];
    let currentStep = -1;
    let paused = false;
    let timer = null;
    let stepSpeed = 1600;

    const $ = (id) => document.getElementById(id);

    // -------------------------------------------------------------
    // INITIALIZATION & TAB SWITCHING
    // -------------------------------------------------------------
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            const activity = tab.dataset.activity;
            currentActivity = activity;

            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            document.querySelectorAll(".activity-form").forEach(form => form.classList.add("hidden"));
            $("form-" + activity).classList.remove("hidden");

            if (activity === "browsing") {
                $("activityBadge").textContent = "Browsing";
                $("protocolFlow").textContent = "DNS → TLS → HTTP";
            } else if (activity === "mail") {
                $("activityBadge").textContent = "Mail";
                $("protocolFlow").textContent = "SMTP / STARTTLS";
            } else if (activity === "streaming") {
                $("activityBadge").textContent = "Streaming";
                $("protocolFlow").textContent = "DNS → HLS / ABR";
            }

            clearVisualization();
            renderNodeFlow(activity);
        });
    });

    // Speed Control listener
    $("speedSelect").addEventListener("change", (e) => {
        stepSpeed = parseInt(e.target.value, 10) || 1600;
        if (!paused && steps.length && currentStep < steps.length - 1) {
            clearInterval(timer);
            startAnimation();
        }
    });

    // -------------------------------------------------------------
    // RENDER NODE FLOW PIPELINE
    // -------------------------------------------------------------
    function renderNodeFlow(activity) {
        const container = $("nodeFlowContainer");
        container.innerHTML = "";

        const nodes = PROTOCOL_NODES[activity] || [];
        nodes.forEach((node, index) => {
            // Create Node Card
            const nodeEl = document.createElement("div");
            nodeEl.className = "flow-node";
            nodeEl.dataset.index = index;
            nodeEl.dataset.nodeId = node.id;

            let tagClass = "tag-dns";
            if (node.section === "TLS") tagClass = "tag-tls";
            else if (node.section === "HTTP") tagClass = "tag-http";
            else if (node.section === "SMTP") tagClass = "tag-smtp";
            else if (node.section === "Streaming" || node.section === "Media") tagClass = "tag-media";

            nodeEl.innerHTML = `
                <div class="node-idx">${index + 1}</div>
                <div class="node-label">${escapeHtml(node.label)}</div>
                <span class="node-tag ${tagClass}">${escapeHtml(node.section)}</span>
            `;

            // Clicking any node jumps directly to that step
            nodeEl.addEventListener("click", () => {
                if (steps.length > 0) {
                    paused = true;
                    $("pauseVizBtn").textContent = "▶ Resume";
                    showStep(index);
                } else {
                    // Preview message if simulation not yet started
                    previewNode(node, index);
                }
            });

            container.appendChild(nodeEl);

            // Add connecting downward arrow except after last node
            if (index < nodes.length - 1) {
                const arrowEl = document.createElement("div");
                arrowEl.className = "flow-arrow";
                arrowEl.dataset.arrowIndex = index;
                arrowEl.innerHTML = "↓";
                container.appendChild(arrowEl);
            }
        });
    }

    function previewNode(node, index) {
        $("messageStage").innerHTML = `
            <div class="empty-stage">
                <div class="network">⇄</div>
                <h3>${escapeHtml(node.label)} (Step ${index + 1})</h3>
                <p>Click <strong>Visit</strong>, <strong>Send Email</strong>, or <strong>Play</strong> on the left panel to execute this simulation step.</p>
            </div>
        `;
    }

    // -------------------------------------------------------------
    // STATUS & LOGGING
    // -------------------------------------------------------------
    function setStatus(activity, text) {
        const ids = {
            browsing: "browsingStatus",
            mail: "mailStatus",
            streaming: "streamingStatus"
        };
        if ($(ids[activity])) {
            $(ids[activity]).textContent = text;
        }
    }

    function addLog(text) {
        const log = $("activityLog");
        const empty = log.querySelector(".empty");
        if (empty) empty.remove();

        const item = document.createElement("div");
        item.className = "log-item";
        item.textContent = new Date().toLocaleTimeString() + " — " + text;
        log.prepend(item);
    }

    $("clearLog").addEventListener("click", () => {
        $("activityLog").innerHTML = '<div class="empty">No activity yet.</div>';
    });

    // -------------------------------------------------------------
    // RUN ACTIVITY / SIMULATION
    // -------------------------------------------------------------
    async function runActivity(payload, activity, logText) {
        clearInterval(timer);
        setStatus(activity, "Running simulation...");

        try {
            const response = await fetch("/api/simulate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Simulation failed");
            }

            steps = data.steps || [];
            currentStep = -1;
            paused = false;

            $("pauseVizBtn").textContent = "⏸ Pause";
            addLog(logText);
            renderTimeline();
            renderNodeFlow(activity);
            startAnimation();

        } catch (error) {
            console.error(error);
            setStatus(activity, "Error: " + error.message);
        }
    }

    // -------------------------------------------------------------
    // ACTIVITY BUTTON LISTENERS
    // -------------------------------------------------------------
    $("visitBtn").addEventListener("click", () => {
        const url = $("url").value.trim();
        if (!url) {
            setStatus("browsing", "Enter a URL first");
            return;
        }

        runActivity(
            { activity: "browsing", url: url },
            "browsing",
            "Visited " + url
        );
    });

    $("sendMailBtn").addEventListener("click", () => {
        const to = $("mailTo").value.trim();
        const subject = $("mailSubject").value.trim();
        const body = $("mailBody").value.trim();

        if (!to || !subject || !body) {
            setStatus("mail", "Fill in To, Subject, and Body");
            return;
        }

        runActivity(
            { activity: "mail", to: to, subject: subject, body: body },
            "mail",
            "Email dispatched to " + to
        );
    });

    $("playBtn").addEventListener("click", () => {
        const url = $("streamingUrl").value.trim() || "https://video.example.com/live/lecture";
        const quality = $("quality").value;

        $("progressBar").style.width = "40%";

        runActivity(
            { activity: "streaming", quality: quality, url: url },
            "streaming",
            "Started " + quality + " streaming: " + url
        );
    });

    $("pauseBtn").addEventListener("click", () => {
        setStatus("streaming", "Playback Paused");
        addLog("Streaming playback paused by user.");
    });

    // -------------------------------------------------------------
    // TIMELINE RENDERING
    // -------------------------------------------------------------
    function renderTimeline() {
        const timeline = $("timeline");
        timeline.innerHTML = "";

        steps.forEach((step, index) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = "timeline-dot";
            dot.title = `Step ${index + 1}: ${step.title}`;

            dot.addEventListener("click", () => {
                paused = true;
                $("pauseVizBtn").textContent = "▶ Resume";
                showStep(index);
            });

            timeline.appendChild(dot);
        });

        updateCounter();
    }

    function updateCounter() {
        $("stepCounter").textContent = `${Math.max(0, currentStep + 1)} / ${steps.length}`;

        document.querySelectorAll(".timeline-dot").forEach((dot, index) => {
            dot.classList.toggle("active", index === currentStep);
            dot.classList.toggle("completed", index < currentStep);
        });
    }

    // -------------------------------------------------------------
    // SHOW PROTOCOL STEP & ANIMATE PIPELINE
    // -------------------------------------------------------------
    function showStep(index) {
        if (!steps.length) return;

        currentStep = Math.max(0, Math.min(index, steps.length - 1));
        const step = steps[currentStep];

        // 1. Update Phase Badge
        const phaseBadge = $("phaseBadge");
        phaseBadge.className = "phase-pill";
        const section = step.section || "Protocol";
        phaseBadge.textContent = section + " Phase";

        if (section === "DNS") phaseBadge.classList.add("phase-dns");
        else if (section === "TLS") phaseBadge.classList.add("phase-tls");
        else if (section === "HTTP") phaseBadge.classList.add("phase-http");
        else if (section === "SMTP") phaseBadge.classList.add("phase-smtp");
        else if (section === "Streaming" || section === "Media") phaseBadge.classList.add("phase-streaming");

        $("protocolBadge").textContent = step.protocol || "Protocol";

        // 2. Animate and Highlight Nodes & Arrows in the Left Flowchart
        const nodeEls = document.querySelectorAll(".flow-node");
        const arrowEls = document.querySelectorAll(".flow-arrow");

        nodeEls.forEach((nodeEl, i) => {
            nodeEl.classList.remove("node-active", "node-completed");
            const idxBadge = nodeEl.querySelector(".node-idx");

            if (i < currentStep) {
                nodeEl.classList.add("node-completed");
                if (idxBadge) idxBadge.textContent = "✓";
            } else if (i === currentStep) {
                nodeEl.classList.add("node-active");
                if (idxBadge) idxBadge.textContent = (i + 1).toString();
                // Smoothly bring active node into view within flow column
                nodeEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
            } else {
                if (idxBadge) idxBadge.textContent = (i + 1).toString();
            }
        });

        arrowEls.forEach((arrowEl, i) => {
            arrowEl.classList.remove("arrow-active", "arrow-completed");
            if (i < currentStep) {
                arrowEl.classList.add("arrow-completed");
            } else if (i === currentStep) {
                arrowEl.classList.add("arrow-active");
            }
        });

        // 3. Determine Direction styling & endpoints
        let dirBadgeText = "CLIENT → SERVER";
        let dirClass = "dir-cs";
        let trackClass = "";
        let srcEndpoint = "Client";
        let dstEndpoint = "Server";

        if (step.direction === "S→C") {
            dirBadgeText = "SERVER → CLIENT";
            dirClass = "dir-sc";
            trackClass = "reverse";
            srcEndpoint = "Client";
            dstEndpoint = "Server / DNS";
        } else if (step.direction === "C↔S") {
            dirBadgeText = "MUTUAL EXCHANGE / TLS";
            dirClass = "dir-bi";
            trackClass = "bidirectional";
            srcEndpoint = "Client";
            dstEndpoint = "Server / Security";
        } else if (step.direction === "Internal") {
            dirBadgeText = "LOCAL PROCESS";
            dirClass = "dir-int";
            trackClass = "internal";
            srcEndpoint = "Client Host";
            dstEndpoint = "Local Runtime";
        }

        // 4. Generate Decoded Field Chips
        const fieldsHtml = (step.fields || []).map(f => `
            <div class="field">
                <b>${escapeHtml(f.label)}:</b> ${escapeHtml(f.value)}
            </div>
        `).join("");

        // 5. Render Inspection Stage Content
        $("messageStage").innerHTML = `
            <div class="stage-content">
                <div class="stage-top">
                    <span class="protocol-name">${escapeHtml(step.protocol || "PROTOCOL")}</span>
                    <span class="direction-badge ${dirClass}">${dirBadgeText}</span>
                </div>

                <div class="stage-title">
                    Step ${currentStep + 1} of ${steps.length}: ${escapeHtml(step.title)}
                </div>

                <div class="stage-desc">
                    ${escapeHtml(step.message)}
                </div>

                <div class="network-track ${trackClass}">
                    <div class="endpoint-box">${srcEndpoint}</div>
                    <div class="transit-line">
                        <div class="transit-packet"></div>
                    </div>
                    <div class="endpoint-box">${dstEndpoint}</div>
                </div>

                <div class="raw-container">
                    <div class="raw-header">
                        <span>RAW TRANSMISSION FRAME</span>
                        <button type="button" class="copy-btn" id="copyRawBtn">Copy</button>
                    </div>
                    <pre class="raw">${escapeHtml(step.raw)}</pre>
                </div>

                <div class="fields">
                    ${fieldsHtml}
                </div>
            </div>
        `;

        // Attach Copy Button Handler
        const copyBtn = $("copyRawBtn");
        if (copyBtn) {
            copyBtn.addEventListener("click", () => {
                navigator.clipboard.writeText(step.raw).then(() => {
                    copyBtn.textContent = "Copied!";
                    setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
                }).catch(err => {
                    console.error("Failed to copy", err);
                });
            });
        }

        // Update Counter
        updateCounter();

        // Update simulated video progress if in streaming
        if (currentActivity === "streaming") {
            const progressPercent = Math.round(((currentStep + 1) / steps.length) * 100);
            $("progressBar").style.width = progressPercent + "%";
        }

        // Completion trigger
        if (currentStep === steps.length - 1) {
            setStatus(currentActivity, "Completed ✓");
        }
    }

    // -------------------------------------------------------------
    // PLAYBACK AUTOMATION
    // -------------------------------------------------------------
    function startAnimation() {
        if (!steps.length) return;

        if (currentStep === -1 || currentStep >= steps.length - 1) {
            showStep(0);
        } else {
            showStep(currentStep);
        }

        clearInterval(timer);
        timer = setInterval(() => {
            if (paused) return;

            if (currentStep < steps.length - 1) {
                showStep(currentStep + 1);
            } else {
                clearInterval(timer);
                $("pauseVizBtn").textContent = "↻ Finished";
            }
        }, stepSpeed);
    }

    // -------------------------------------------------------------
    // CONTROLS
    // -------------------------------------------------------------
    $("nextBtn").addEventListener("click", () => {
        if (!steps.length) return;
        paused = true;
        $("pauseVizBtn").textContent = "▶ Resume";
        if (currentStep < steps.length - 1) {
            showStep(currentStep + 1);
        }
    });

    $("prevBtn").addEventListener("click", () => {
        if (!steps.length) return;
        paused = true;
        $("pauseVizBtn").textContent = "▶ Resume";
        if (currentStep > 0) {
            showStep(currentStep - 1);
        }
    });

    $("pauseVizBtn").addEventListener("click", () => {
        if (!steps.length) return;

        if (currentStep >= steps.length - 1) {
            // If finished, replay from beginning
            paused = false;
            $("pauseVizBtn").textContent = "⏸ Pause";
            showStep(0);
            startAnimation();
            return;
        }

        paused = !paused;
        $("pauseVizBtn").textContent = paused ? "▶ Resume" : "⏸ Pause";
        if (!paused) {
            startAnimation();
        }
    });

    $("replayBtn").addEventListener("click", () => {
        if (!steps.length) return;
        paused = false;
        $("pauseVizBtn").textContent = "⏸ Pause";
        showStep(0);
        startAnimation();
    });

    // -------------------------------------------------------------
    // RESET
    // -------------------------------------------------------------
    function clearVisualization() {
        clearInterval(timer);
        steps = [];
        currentStep = -1;
        paused = false;

        $("protocolBadge").textContent = "Waiting";
        $("phaseBadge").className = "phase-pill";
        $("phaseBadge").textContent = "Ready";
        $("stepCounter").textContent = "0 / 0";
        $("timeline").innerHTML = "";

        $("messageStage").innerHTML = `
            <div class="empty-stage">
                <div class="network">⇄</div>
                <h3>Waiting for activity...</h3>
                <p>
                    Select an activity from the left panel and click 
                    <strong>Visit</strong>, <strong>Send Email</strong>, or <strong>Play</strong> 
                    to visualize the live protocol exchange.
                </p>
            </div>
        `;
    }

    // -------------------------------------------------------------
    // UTILITY
    // -------------------------------------------------------------
    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[char]));
    }

    // Initialize initial browsing nodes
    renderNodeFlow("browsing");
});