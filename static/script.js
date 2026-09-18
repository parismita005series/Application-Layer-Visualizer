document.addEventListener("DOMContentLoaded", () => {

    let steps = [];
    let currentStep = -1;
    let paused = false;
    let timer = null;


    const $ = (id) => document.getElementById(id);


    // -------------------------
    // TAB SWITCHING
    // -------------------------

    document.querySelectorAll(".tab").forEach(tab => {

        tab.addEventListener("click", () => {

            const activity = tab.dataset.activity;

            document.querySelectorAll(".tab").forEach(t => {
                t.classList.remove("active");
            });

            tab.classList.add("active");


            document.querySelectorAll(".activity-form").forEach(form => {
                form.classList.add("hidden");
            });


            $("form-" + activity).classList.remove("hidden");


            if (activity === "browsing") {
                $("activityBadge").textContent = "Browsing";
                $("protocolFlow").textContent = "DNS → HTTP";
            }

            if (activity === "mail") {
                $("activityBadge").textContent = "Mail";
                $("protocolFlow").textContent = "SMTP";
            }

            if (activity === "streaming") {
                $("activityBadge").textContent = "Streaming";
                $("protocolFlow").textContent = "DNS → HTTP";
            }


            clearVisualization();

        });

    });


    // -------------------------
    // STATUS
    // -------------------------

    function setStatus(activity, text) {

        const ids = {
            browsing: "browsingStatus",
            mail: "mailStatus",
            streaming: "streamingStatus"
        };

        $(ids[activity]).textContent = text;
    }


    // -------------------------
    // ACTIVITY LOG
    // -------------------------

    function addLog(text) {

        const log = $("activityLog");

        const empty = log.querySelector(".empty");

        if (empty) {
            empty.remove();
        }


        const item = document.createElement("div");

        item.className = "log-item";

        item.textContent =
            new Date().toLocaleTimeString() +
            " — " +
            text;


        log.prepend(item);
    }


    $("clearLog").addEventListener("click", () => {

        $("activityLog").innerHTML =
            '<div class="empty">No activity yet.</div>';

    });


    // -------------------------
    // SEND DATA TO PYTHON
    // -------------------------

    async function runActivity(payload, activity, logText) {

        clearInterval(timer);

        setStatus(activity, "Running...");


        try {

            const response = await fetch(
                "/api/simulate",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(payload)
                }
            );


            const data = await response.json();


            if (!response.ok) {
                throw new Error(data.error);
            }


            steps = data.steps;

            currentStep = -1;

            paused = false;


            $("pauseVizBtn").textContent =
                "⏸ Pause";


            addLog(logText);

            renderTimeline();

            startAnimation();


        } catch (error) {

            console.error(error);

            setStatus(
                activity,
                "Error: " + error.message
            );

        }

    }


    // -------------------------
    // BROWSING
    // -------------------------

    $("visitBtn").addEventListener("click", () => {

        const url = $("url").value.trim();


        if (!url) {

            setStatus(
                "browsing",
                "Enter a URL first"
            );

            return;
        }


        runActivity(
            {
                activity: "browsing",
                url: url
            },

            "browsing",

            "Visited " + url
        );

    });


    // -------------------------
    // MAIL
    // -------------------------

    $("sendMailBtn").addEventListener("click", () => {

        const to =
            $("mailTo").value.trim();

        const subject =
            $("mailSubject").value.trim();

        const body =
            $("mailBody").value.trim();


        if (!to || !subject || !body) {

            setStatus(
                "mail",
                "Fill in To, Subject and Body"
            );

            return;
        }


        runActivity(
            {
                activity: "mail",
                to: to,
                subject: subject,
                body: body
            },

            "mail",

            "Email sent to " + to
        );

    });


    // -------------------------
    // STREAMING
    // -------------------------

   $("playBtn").addEventListener("click", () => {

    const url =
        $("streamingUrl").value.trim();

    const quality =
        $("quality").value;


    if (!url) {

        setStatus(
            "streaming",
            "Enter a video URL first"
        );

        return;
    }


    $("progressBar").style.width =
        "65%";


    runActivity(
        {
            activity: "streaming",
            url: url,
            quality: quality
        },

        "streaming",

        "Started " + quality + " streaming: " + url
    );

});


    $("pauseBtn").addEventListener("click", () => {

        $("progressBar").style.width =
            "25%";

        setStatus(
            "streaming",
            "Paused"
        );

        addLog(
            "Streaming playback paused."
        );

    });


    // -------------------------
    // TIMELINE
    // -------------------------

    function renderTimeline() {

        const timeline =
            $("timeline");


        timeline.innerHTML = "";


        steps.forEach((step, index) => {

            const dot =
                document.createElement("button");


            dot.type = "button";

            dot.className =
                "timeline-dot";


            dot.addEventListener(
                "click",
                () => {

                    paused = true;

                    $("pauseVizBtn").textContent =
                        "▶ Resume";

                    showStep(index);

                }
            );


            timeline.appendChild(dot);

        });


        updateCounter();

    }


    function updateCounter() {

        $("stepCounter").textContent =
            `${Math.max(0, currentStep + 1)} / ${steps.length}`;


        document
            .querySelectorAll(".timeline-dot")
            .forEach((dot, index) => {

                dot.classList.toggle(
                    "active",
                    index === currentStep
                );

            });

    }


    // -------------------------
    // SHOW PROTOCOL STEP
    // -------------------------

    function showStep(index) {

        if (!steps.length) {
            return;
        }


        currentStep =
            Math.max(
                0,
                Math.min(index, steps.length - 1)
            );


        const step =
            steps[currentStep];


        const reverse =
            step.direction === "S→C";


        const fields =
            step.fields
                .map(field => {

                    return `
                        <span class="field">
                            <b>${escapeHtml(field.label)}:</b>
                            ${escapeHtml(field.value)}
                        </span>
                    `;

                })
                .join("");


        $("protocolBadge").textContent =
            step.protocol;


        $("messageStage").innerHTML = `

            <div>

                <div class="stage-top">

                    <span class="protocol-name">
                        ${escapeHtml(step.protocol)} MESSAGE
                    </span>

                    <span class="direction">
                        ${reverse
                            ? "SERVER → CLIENT"
                            : "CLIENT → SERVER"}
                    </span>

                </div>


                <h3>
                    Step ${currentStep + 1}:
                    ${escapeHtml(step.title)}
                </h3>


                <p>
                    ${escapeHtml(step.message)}
                </p>


                <div class="network-arrow
                    ${reverse ? "reverse" : ""}">

                    <span>CLIENT</span>

                    <span class="line"></span>

                    <span>SERVER</span>

                </div>


                <pre class="raw">${escapeHtml(step.raw)}</pre>


                <div class="fields">
                    ${fields}
                </div>

            </div>

        `;


        updateCounter();


        if (currentStep === steps.length - 1) {

            const active =
                document
                    .querySelector(".tab.active")
                    .dataset.activity;


            setStatus(
                active,
                "Completed ✓"
            );

        }

    }


    // -------------------------
    // AUTO PLAY
    // -------------------------

    function startAnimation() {

        if (!steps.length) {
            return;
        }


        showStep(0);


        clearInterval(timer);


        timer = setInterval(() => {

            if (paused) {
                return;
            }


            if (currentStep < steps.length - 1) {

                showStep(currentStep + 1);

            } else {

                clearInterval(timer);

            }

        }, 1800);

    }


    // -------------------------
    // CONTROLS
    // -------------------------

    $("nextBtn").addEventListener("click", () => {

        if (!steps.length) return;


        paused = true;

        $("pauseVizBtn").textContent =
            "▶ Resume";


        if (currentStep < steps.length - 1) {

            showStep(currentStep + 1);

        }

    });


    $("prevBtn").addEventListener("click", () => {

        if (!steps.length) return;


        paused = true;

        $("pauseVizBtn").textContent =
            "▶ Resume";


        if (currentStep > 0) {

            showStep(currentStep - 1);

        }

    });


    $("pauseVizBtn").addEventListener("click", () => {

        if (!steps.length) return;


        paused = !paused;


        $("pauseVizBtn").textContent =
            paused
                ? "▶ Resume"
                : "⏸ Pause";

    });


    $("replayBtn").addEventListener("click", () => {

        if (!steps.length) return;


        paused = false;

        $("pauseVizBtn").textContent =
            "⏸ Pause";


        startAnimation();

    });


    // -------------------------
    // RESET
    // -------------------------

    function clearVisualization() {

        clearInterval(timer);


        steps = [];

        currentStep = -1;

        paused = false;


        $("protocolBadge").textContent =
            "Waiting";


        $("stepCounter").textContent =
            "0 / 0";


        $("timeline").innerHTML = "";


        $("messageStage").innerHTML = `

            <div class="empty-stage">

                <div class="network">
                    ⇄
                </div>

                <h3>
                    Waiting for activity...
                </h3>

                <p>
                    Perform an activity from the left
                    panel to visualize the protocol exchange.
                </p>

            </div>

        `;

    }


    // -------------------------
    // SECURITY
    // -------------------------

    function escapeHtml(value) {

        return String(value).replace(
            /[&<>"']/g,
            char => ({

                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"

            }[char])
        );

    }

});