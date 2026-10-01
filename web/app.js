const DATA_FILES = {
    experiments: "../output/experimental_results.json",
    verification: "../output/verification_report.json",
    rules: "../output/security_rule_report.json"
};


async function loadJSON(path) {

    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(`Unable to load ${path}`);
    }

    return response.json();
}


function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


function renderMetrics(experiments, verification, rules) {

    const experimentList = experiments.experiments || [];

    setText(
        "experimentCount",
        experimentList.length
    );

    const pass =
        experimentList.filter(
            item => item.observed_result === "PASS"
        ).length;

    const fail =
        experimentList.filter(
            item => item.observed_result === "FAIL"
        ).length;

    const review =
        experimentList.filter(
            item => item.observed_result === "REVIEW"
        ).length;

    setText("passCount", pass);
    setText("failCount", fail);
    setText("reviewCount", review);
}


function renderExperiments(experiments) {

    const container =
        document.getElementById("experiments");

    container.innerHTML = "";

    const items =
        experiments.experiments || [];

    items.forEach(item => {

        const row =
            document.createElement("div");

        row.className = "experiment";

        const result =
            item.observed_result || "UNKNOWN";

        row.innerHTML = `
            <div class="exp-id">
                ${item.id}
            </div>

            <div>
                <div class="exp-type">
                    ${escapeHTML(item.change_type)}
                </div>

                <div class="exp-change">
                    ${escapeHTML(item.change)}
                </div>
            </div>

            <div class="result ${result}">
                ${result}
            </div>
        `;

        container.appendChild(row);
    });
}


function renderTerminal(experiments) {

    const terminal =
        document.getElementById("terminal");

    terminal.innerHTML = "";

    const items =
        experiments.experiments || [];

    addTerminalLine(
        terminal,
        "SYSTEM",
        "Repository context loaded: Google Online Boutique"
    );

    addTerminalLine(
        terminal,
        "SYSTEM",
        "Continuous verification engine initialized"
    );

    addTerminalLine(
        terminal,
        "SYSTEM",
        `${items.length} controlled experiments discovered`
    );

    items.forEach(item => {

        let type = "normal";

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

    addTerminalLine(
        terminal,
        "ENGINE",
        "Evaluation dataset processed successfully",
        "success"
    );
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


async function initializeDashboard() {

    try {

        const [
            experiments,
            verification,
            rules
        ] = await Promise.all([

            loadJSON(DATA_FILES.experiments),

            loadJSON(DATA_FILES.verification),

            loadJSON(DATA_FILES.rules)

        ]);

        renderMetrics(
            experiments,
            verification,
            rules
        );

        renderExperiments(
            experiments
        );

        renderTerminal(
            experiments
        );

        console.log(
            "[SECURITY ENGINE] Dashboard initialized."
        );

    } catch (error) {

        console.error(error);

        document.getElementById(
            "experiments"
        ).innerHTML = `
            <div class="loading">
                DATA LINK ERROR — RUN DASHBOARD THROUGH LOCAL SERVER
            </div>
        `;

        document.getElementById(
            "terminal"
        ).innerHTML += `
            <div class="danger">
                <span class="terminal-time">
                    [ERROR]
                </span>
                Unable to establish data link.
            </div>
        `;
    }
}


initializeDashboard();