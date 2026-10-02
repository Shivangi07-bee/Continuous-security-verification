const DATA_FILES = {
    experiments: "../output/experimental_results.json",
    verification: "../output/verification_report.json",
    rules: "../output/security_rule_report.json"
};

let experimentsData = null;
let commandCenterHTML = "";


/* =========================================================
   HELPERS
========================================================= */

async function loadJSON(path) {
    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(`Unable to load ${path}`);
    }

    return response.json();
}


function escapeHTML(value) {
    if (value === undefined || value === null) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   COMMAND CENTER
========================================================= */

function renderMetrics() {

    const items =
        experimentsData.experiments || [];

    document.getElementById("experimentCount")
        .textContent = items.length;

    document.getElementById("passCount")
        .textContent =
        items.filter(
            x => x.observed_result === "PASS"
        ).length;

    document.getElementById("failCount")
        .textContent =
        items.filter(
            x => x.observed_result === "FAIL"
        ).length;

    document.getElementById("reviewCount")
        .textContent =
        items.filter(
            x => x.observed_result === "REVIEW"
        ).length;
}


function renderExperiments() {

    const container =
        document.getElementById("experiments");

    container.innerHTML = "";

    const items =
        experimentsData.experiments || [];

    items.forEach(item => {

        const row =
            document.createElement("div");

        row.className = "experiment";

        row.innerHTML = `
            <div class="exp-id">
                ${escapeHTML(item.id)}
            </div>

            <div>
                <div class="exp-type">
                    ${escapeHTML(item.change_type)}
                </div>

                <div class="exp-change">
                    ${escapeHTML(item.change)}
                </div>
            </div>

            <div class="result ${escapeHTML(
                item.observed_result
            )}">
                ${escapeHTML(
                    item.observed_result
                )}
            </div>
        `;

        row.style.cursor = "pointer";

        row.addEventListener(
            "click",
            () => openExperimentScreen(item)
        );

        container.appendChild(row);
    });
}


function renderTerminal() {

    const terminal =
        document.getElementById("terminal");

    terminal.innerHTML = "";

    const items =
        experimentsData.experiments || [];

    addTerminalLine(
        terminal,
        "SYSTEM",
        "Security intelligence engine initialized"
    );

    addTerminalLine(
        terminal,
        "REPO",
        "Google Online Boutique loaded"
    );

    addTerminalLine(
        terminal,
        "SYSTEM",
        `${items.length} controlled experiments available`
    );

    items.forEach(item => {

        let type = "";

        if (item.observed_result === "FAIL") {
            type = "danger";
        }

        if (item.observed_result === "REVIEW") {
            type = "warning";
        }

        if (
            item.observed_result === "PASS" ||
            item.observed_result === "NOT_TARGETED"
        ) {
            type = "success";
        }

        addTerminalLine(
            terminal,
            item.id,
            `${item.change_type} → ${item.observed_result}`,
            type
        );
    });
}


function addTerminalLine(
    terminal,
    prefix,
    message,
    type = ""
) {

    const line =
        document.createElement("div");

    line.className = type;

    line.innerHTML = `
        <span class="terminal-time">
            [${escapeHTML(prefix)}]
        </span>
        ${escapeHTML(message)}
    `;

    terminal.appendChild(line);
}


/* =========================================================
   SCREEN NAVIGATION
========================================================= */


  function injectModalStyles() {
    if (document.getElementById("securityModalStyles")) {
        return;
    }

    const style = document.createElement("style");

    style.id = "securityModalStyles";

    style.textContent = `
        .security-modal-overlay {
            position: fixed;
            inset: 0;
            z-index: 9999;

            display: flex;
            align-items: center;
            justify-content: center;

            padding: 30px;

            background: rgba(0, 0, 0, 0.72);
            backdrop-filter: blur(7px);

            animation: modalFadeIn 0.18s ease-out;
        }

        .security-modal {
            width: min(920px, 94vw);
            max-height: 86vh;

            overflow: auto;

            position: relative;

            background:
                linear-gradient(
                    135deg,
                    rgba(0, 229, 255, 0.035),
                    transparent 40%
                ),
                #070b10;

            border: 1px solid #1c3340;

            box-shadow:
                0 0 0 1px rgba(0, 229, 255, 0.04),
                0 0 45px rgba(0, 229, 255, 0.13),
                0 25px 80px rgba(0, 0, 0, 0.65);
        }

        .security-modal::before {
            content: "";

            position: absolute;
            top: 0;
            left: 0;

            width: 110px;
            height: 2px;

            background: var(--cyan);

            box-shadow: 0 0 18px var(--cyan);
        }

        .security-modal-topbar {
            min-height: 66px;

            padding: 15px 18px;

            display: flex;
            align-items: center;
            justify-content: space-between;

            gap: 20px;

            border-bottom: 1px solid var(--line);

            background: rgba(5, 7, 10, 0.86);
        }

        .security-modal-system {
            display: block;

            color: var(--cyan);

            font-family: "JetBrains Mono", monospace;

            font-size: 8px;

            letter-spacing: 1.5px;

            margin-bottom: 6px;
        }

        .security-modal-topbar h1 {
            margin: 0;

            font-family: "JetBrains Mono", monospace;

            font-size: 14px;

            letter-spacing: 1px;

            color: var(--text);
        }

        .security-modal-close {
            flex-shrink: 0;

            border: 1px solid #29404c;

            background: #080d12;

            color: var(--cyan);

            padding: 9px 12px;

            cursor: pointer;

            font-family: "JetBrains Mono", monospace;

            font-size: 8px;

            letter-spacing: 1px;
        }

        .security-modal-close:hover {
            border-color: var(--cyan);

            box-shadow:
                0 0 16px rgba(0, 229, 255, 0.12);
        }

        .security-modal-content {
            padding: 20px;
        }

        .security-modal-footer {
            padding: 12px 18px;

            display: flex;

            justify-content: space-between;

            gap: 15px;

            border-top: 1px solid var(--line);

            color: #52616c;

            font-family: "JetBrains Mono", monospace;

            font-size: 7px;

            letter-spacing: 1px;
        }

        .security-modal-footer .online {
            color: var(--green);
        }

        body.security-modal-open {
            overflow: hidden;
        }

        @keyframes modalFadeIn {

            from {
                opacity: 0;
                transform: scale(0.985);
            }

            to {
                opacity: 1;
                transform: scale(1);
            }

        }

        @media (max-width: 700px) {

            .security-modal-overlay {
                padding: 12px;
            }

            .security-modal {
                width: 96vw;
                max-height: 91vh;
            }

            .security-modal-content {
                padding: 14px;
            }

            .security-modal-topbar h1 {
                font-size: 11px;
            }

        }
    `;

    document.head.appendChild(style);
}


function openScreen(title, content) {

    injectModalStyles();

    closeSecurityModal();


    const overlay = document.createElement("div");

    overlay.className = "security-modal-overlay";

    overlay.id = "securityModal";


    overlay.innerHTML = `

        <section
            class="security-modal"
            role="dialog"
            aria-modal="true"
        >

            <div class="security-modal-topbar">

                <div>

                    <span class="security-modal-system">
                        SECURITY VERIFICATION // MODULE
                    </span>

                    <h1>
                        ${escapeHTML(title)}
                    </h1>

                </div>


                <button
                    class="security-modal-close"
                    id="securityModalClose"
                    type="button"
                >
                    ESC // CLOSE
                </button>

            </div>


            <div class="security-modal-content">

                ${content}

            </div>


            <div class="security-modal-footer">

                <span>
                    CONTINUOUS SECURITY VERIFICATION
                </span>

                <span>
                    RESEARCH ENVIRONMENT
                </span>

                <span class="online">
                    ● SYSTEM OPERATIONAL
                </span>

            </div>

        </section>

    `;


    document.body.appendChild(overlay);

    document.body.classList.add(
        "security-modal-open"
    );


    document
        .getElementById("securityModalClose")
        .addEventListener(
            "click",
            closeSecurityModal
        );


    overlay.addEventListener(
        "click",
        function(event) {

            if (event.target === overlay) {

                closeSecurityModal();

            }

        }
    );


    document.addEventListener(
        "keydown",
        handleSecurityModalKeydown
    );


    requestAnimationFrame(
        function() {

            const modal =
                overlay.querySelector(
                    ".security-modal"
                );

            if (modal) {

                modal.scrollTop = 0;

            }

        }
    );
}


function handleSecurityModalKeydown(event) {

    if (event.key === "Escape") {

        closeSecurityModal();

    }
}


function closeSecurityModal() {

    const overlay =
        document.getElementById(
            "securityModal"
        );


    if (overlay) {

        overlay.remove();

    }


    document.body.classList.remove(
        "security-modal-open"
    );


    document.removeEventListener(
        "keydown",
        handleSecurityModalKeydown
    );
}


function returnToCommandCenter() {

    closeSecurityModal();

    window.scrollTo({

        top: 0,

        behavior: "instant"

    });

}

/* =========================================================
   EXPERIMENT SCREEN
========================================================= */

function openExperimentScreen(item) {

    const result =
        item.observed_result || "UNKNOWN";

    let decisionClass =
        "decision-review";

    let decisionText =
        "MANUAL VALIDATION REQUIRED";


    if (result === "PASS") {

        decisionClass =
            "decision-pass";

        decisionText =
            "SECURITY RULE PRESERVED";
    }


    if (result === "FAIL") {

        decisionClass =
            "decision-fail";

        decisionText =
            "SECURITY REGRESSION DETECTED";
    }


    if (result === "NOT_TARGETED") {

        decisionClass =
            "decision-neutral";

        decisionText =
            "SECURITY VERIFICATION NOT TARGETED";
    }


    openScreen(
        `${item.id} // ${item.change_type}`,

        `

        <div class="module-status">

            <span>
                ANALYSIS MODULE
            </span>

            <strong>
                ACTIVE
            </strong>

        </div>


        <div class="security-result ${decisionClass}">

            <div class="result-icon">

                ${result === "FAIL" ? "×" : "✓"}

            </div>


            <div>

                <small>
                    SECURITY DECISION
                </small>

                <strong>
                    ${escapeHTML(decisionText)}
                </strong>

            </div>

        </div>


        <div class="analysis-grid">


            <div class="analysis-card">

                <span>
                    SERVICE EVOLUTION
                </span>

                <strong>
                    ${escapeHTML(
                        item.change_type
                    )}
                </strong>

            </div>


            <div class="analysis-card">

                <span>
                    OBSERVED RESULT
                </span>

                <strong>
                    ${escapeHTML(result)}
                </strong>

            </div>


            <div class="analysis-card wide">

                <span>
                    REPOSITORY CHANGE
                </span>

                <p>
                    ${escapeHTML(item.change)}
                </p>

            </div>


            <div class="analysis-card">

                <span>
                    SECURITY PROPERTY
                </span>

                <strong>
                    ${escapeHTML(
                        item.security_property ||
                        "N/A"
                    )}
                </strong>

            </div>


            <div class="analysis-card">

                <span>
                    EXPECTED BEHAVIOR
                </span>

                <strong>
                    ${escapeHTML(
                        item.expected_behavior ||
                        "N/A"
                    )}
                </strong>

            </div>


            <div class="analysis-card wide">

                <span>
                    FRAMEWORK INTERPRETATION
                </span>

                <p>
                    ${escapeHTML(
                        item.interpretation ||
                        "No interpretation available."
                    )}
                </p>

            </div>


        </div>


        <div class="access-terminal">

            <div>

                <span>
                    [REPOSITORY]
                </span>

                Google Online Boutique

            </div>


            <div>

                <span>
                    [ANALYSIS]
                </span>

                Repository-aware security verification

            </div>


            <div>

                <span>
                    [DECISION]
                </span>

                ${escapeHTML(result)}

            </div>

        </div>

        `
    );
}


/* =========================================================
   PIPELINE SCREEN
========================================================= */

function openPipelineScreen(index) {

    const stages = [

        {
            title:
                "01 // CHANGE EXTRACTION",

            command:
                "REPOSITORY → CHANGE SET",

            description:
                "Detects files and artifacts modified between repository revisions.",

            output:
                "Changed files, affected services and artifact types."
        },


        {
            title:
                "02 // SEMANTIC ANALYSIS",

            command:
                "CHANGE SET → SEMANTIC SIGNALS",

            description:
                "Identifies security-relevant semantic changes.",

            output:
                "Authorization, transaction, interface, state and service-call signals."
        },


        {
            title:
                "03 // IMPACT MAPPING",

            command:
                "SEMANTICS → SECURITY IMPACT",

            description:
                "Maps changed services and relationships to affected security properties.",

            output:
                "Affected services and security properties."
        },


        {
            title:
                "04 // EVIDENCE COLLECTION",

            command:
                "IMPACT → REPOSITORY EVIDENCE",

            description:
                "Collects concrete changed-code evidence for affected properties.",

            output:
                "Added lines, removed lines and changed repository evidence."
        },


        {
            title:
                "05 // TARGETED VERIFICATION",

            command:
                "EVIDENCE → SECURITY DECISION",

            description:
                "Applies the relevant verification rules to the affected security properties.",

            output:
                "PASS / FAIL / REVIEW."
        }

    ];


    const stage =
        stages[index];


    if (!stage) {
        return;
    }


    openScreen(
        stage.title,

        `

        <div class="module-status">

            <span>
                PIPELINE MODULE
            </span>

            <strong>
                RUNNING
            </strong>

        </div>


        <div class="pipeline-command">

            ${escapeHTML(
                stage.command
            )}

        </div>


        <div class="analysis-grid">


            <div class="analysis-card wide">

                <span>
                    MODULE FUNCTION
                </span>

                <p>
                    ${escapeHTML(
                        stage.description
                    )}
                </p>

            </div>


            <div class="analysis-card wide">

                <span>
                    MODULE OUTPUT
                </span>

                <strong>
                    ${escapeHTML(
                        stage.output
                    )}
                </strong>

            </div>


        </div>


        <div class="access-terminal">

            <div>

                <span>
                    [INPUT]
                </span>

                Repository evolution

            </div>


            <div>

                <span>
                    [ENGINE]
                </span>

                ${escapeHTML(
                    stage.command
                )}

            </div>


            <div class="success">

                <span>
                    [STATUS]
                </span>

                MODULE READY

            </div>

        </div>

        `
    );
}


/* =========================================================
   REPOSITORY SCREEN
========================================================= */

function openRepositoryScreen() {

    openScreen(
        "02 // SUBJECT SYSTEM",

        `

        <div class="module-status">

            <span>
                REPOSITORY CONTEXT
            </span>

            <strong>
                TRACKED
            </strong>

        </div>


        <div class="analysis-grid">


            <div class="analysis-card wide">

                <span>
                    SUBJECT SYSTEM
                </span>

                <strong>
                    GOOGLE ONLINE BOUTIQUE
                </strong>

            </div>


            <div class="analysis-card">

                <span>
                    ARCHITECTURE
                </span>

                <strong>
                    MICROSERVICES
                </strong>

            </div>


            <div class="analysis-card">

                <span>
                    ANALYSIS MODE
                </span>

                <strong>
                    EVOLUTION-AWARE
                </strong>

            </div>


            <div class="analysis-card wide">

                <span>
                    REPOSITORY
                </span>

                <p>
                    GoogleCloudPlatform / microservices-demo
                </p>

            </div>


        </div>


        <div class="access-terminal">

            <div>

                <span>
                    [STATUS]
                </span>

                SUBJECT SYSTEM TRACKED

            </div>


            <div>

                <span>
                    [ROLE]
                </span>

                Experimental evaluation environment

            </div>

        </div>

        `
    );
}


/* =========================================================
   LIVE VERIFICATION SCREEN
========================================================= */

async function openRunScreen() {

    openScreen(
        "LIVE // SECURITY VERIFICATION",

        `

        <div class="module-status">

            <span>
                VERIFICATION ENGINE
            </span>

            <strong>
                EXECUTING
            </strong>

        </div>


        <div class="run-console">

            <div>

                <span>
                    [ENGINE]
                </span>

                Initializing verification backend...

            </div>


            <div>

                <span>
                    [REPOSITORY]
                </span>

                Google Online Boutique

            </div>


            <div>

                <span>
                    [PIPELINE]
                </span>

                Change → Impact → Evidence → Verification

            </div>


            <div>

                <span>
                    [STATUS]
                </span>

                Awaiting experiment selection...

            </div>

        </div>


        <div class="run-selection">

            <label>
                SELECT EVOLUTION SCENARIO
            </label>


            <select id="screenExperimentSelect">

                <option value="E1">
                    E1 — AUTHORIZATION REGRESSION
                </option>

                <option value="E2">
                    E2 — TRANSACTION VALIDATION
                </option>

                <option value="E3">
                    E3 — API CONTRACT EVOLUTION
                </option>

                <option value="E4">
                    E4 — DOCUMENTATION EVOLUTION
                </option>

            </select>


            <button
                id="executeScreenButton"
                class="execute-button"
            >

                ▶ EXECUTE VERIFICATION

            </button>

        </div>


        <div
            id="liveResult"
            class="live-result"
        ></div>

        `
    );


    document
        .getElementById(
            "executeScreenButton"
        )
        .addEventListener(
            "click",
            executeVerification
        );
}


async function executeVerification() {

    const select =
        document.getElementById(
            "screenExperimentSelect"
        );

    const button =
        document.getElementById(
            "executeScreenButton"
        );

    const resultBox =
        document.getElementById(
            "liveResult"
        );


    const experiment =
        select.value;


    button.disabled = true;


    resultBox.innerHTML = `

        <div class="run-console">

            <div>

                <span>
                    [ENGINE]
                </span>

                Executing ${escapeHTML(
                    experiment
                )}...

            </div>


            <div>

                <span>
                    [BACKEND]
                </span>

                Running continuous verification pipeline...

            </div>

        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/run",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        experiment
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Verification failed."
            );

        }


        const rules =
            data.security_rules || {};


        const passed =
            rules.passed || 0;

        const failed =
            rules.failed || 0;

        const review =
            rules.review_required || 0;


        let resultClass =
            "result-review";

        let resultText =
            "MANUAL VALIDATION REQUIRED";


        if (failed > 0) {

            resultClass =
                "result-fail";

            resultText =
                "SECURITY REGRESSION DETECTED";

        }

        else if (
            passed > 0 &&
            review === 0
        ) {

            resultClass =
                "result-pass";

            resultText =
                "SECURITY VERIFICATION PASSED";

        }


        resultBox.innerHTML = `

            <div class="security-result ${resultClass}">

                <div class="result-icon">

                    ${failed > 0 ? "×" : "✓"}

                </div>


                <div>

                    <small>
                        VERIFICATION RESULT
                    </small>

                    <strong>
                        ${resultText}
                    </strong>

                </div>

            </div>


            <div class="analysis-grid">


                <div class="analysis-card">

                    <span>
                        BASE
                    </span>

                    <strong>
                        ${escapeHTML(
                            data.base
                        )}
                    </strong>

                </div>


                <div class="analysis-card">

                    <span>
                        HEAD
                    </span>

                    <strong>
                        ${escapeHTML(
                            data.head
                        )}
                    </strong>

                </div>


                <div class="analysis-card">

                    <span>
                        PASS
                    </span>

                    <strong class="pass-text">
                        ${passed}
                    </strong>

                </div>


                <div class="analysis-card">

                    <span>
                        FAIL
                    </span>

                    <strong class="fail-text">
                        ${failed}
                    </strong>

                </div>


                <div class="analysis-card">

                    <span>
                        REVIEW
                    </span>

                    <strong class="review-text">
                        ${review}
                    </strong>

                </div>


                <div class="analysis-card">

                    <span>
                        SECURITY IMPACTS
                    </span>

                    <strong>
                        ${
                            data.security_impact
                                ?.total_impacts || 0
                        }
                    </strong>

                </div>


            </div>


            <div class="access-terminal">

                <div>

                    <span>
                        [ENGINE]
                    </span>

                    Verification cycle completed

                </div>


                <div>

                    <span>
                        [DECISION]
                    </span>

                    ${escapeHTML(
                        resultText
                    )}

                </div>

            </div>

        `;

    }


    catch (error) {

        resultBox.innerHTML = `

            <div class="security-result result-fail">

                <div class="result-icon">
                    ×
                </div>


                <div>

                    <small>
                        ENGINE ERROR
                    </small>

                    <strong>
                        ${escapeHTML(
                            error.message
                        )}
                    </strong>

                </div>

            </div>

        `;

    }


    finally {

        button.disabled = false;

    }
}


/* =========================================================
   COMMAND CENTER EVENTS
========================================================= */

function setupPipelineEvents() {

    document
        .querySelectorAll(
            ".pipeline-node"
        )
        .forEach(
            (node, index) => {

                node.style.cursor =
                    "pointer";


                node.addEventListener(
                    "click",
                    () => {

                        openPipelineScreen(
                            index
                        );

                    }
                );

            }
        );
}


function setupRepositoryEvent() {

    const panel =
        document.querySelector(
            ".repository-panel"
        );


    if (!panel) {
        return;
    }


    panel.style.cursor =
        "pointer";


    panel.addEventListener(
        "click",
        openRepositoryScreen
    );
}


function setupRunButton() {

    const panel =
        document.querySelector(
            ".experiments-panel"
        );


    if (!panel) {
        return;
    }


    const header =
        panel.querySelector(
            ".panel-header"
        );


    const controls =
        document.createElement(
            "div"
        );


    controls.className =
        "command-run-control";


    controls.innerHTML = `

        <span>
            LIVE VERIFICATION
        </span>


        <button
            id="openRunScreen"
            class="run-button"
        >

            ▶ OPEN VERIFICATION CONSOLE

        </button>

    `;


    header.insertAdjacentElement(
        "afterend",
        controls
    );


    document
        .getElementById(
            "openRunScreen"
        )
        .addEventListener(
            "click",
            openRunScreen
        );
}


/* =========================================================
   COMMAND CENTER INITIALIZATION
========================================================= */

function initializeCommandCenter() {

    renderMetrics();

    renderExperiments();

    renderTerminal();

    setupPipelineEvents();

    setupRepositoryEvent();

    setupRunButton();
}


/* =========================================================
   INITIAL DASHBOARD LOAD
========================================================= */

async function initializeDashboard() {

    try {

        experimentsData =
            await loadJSON(
                DATA_FILES.experiments
            );


        const dashboard =
            document.querySelector(
                ".dashboard"
            );


        /*
         * Save the complete original
         * command-center layout.
         */
        commandCenterHTML =
            dashboard.innerHTML;


        initializeCommandCenter();


        window.scrollTo({
            top: 0,
            behavior: "instant"
        });


        console.log(
            "[SECURITY ENGINE] Command center online."
        );

    }


    catch (error) {

        console.error(error);


        const experiments =
            document.getElementById(
                "experiments"
            );


        if (experiments) {

            experiments.innerHTML = `

                <div class="loading">

                    SECURITY ENGINE DATA LINK ERROR

                </div>

            `;

        }

    }

}


initializeDashboard();