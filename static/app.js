const local = false;

let ip = "";
if (!local)
    ip = "https://bgpscanvisualizer.onrender.com";
let login_page = "/login.html"
if (!local)
    login_page = "/BGPScanVisualizer/login.html"

let currentGraphRequest = 0;

const helpButton = document.getElementById("help-button");
const sidebar = document.getElementById("help-sidebar");
const handle = document.getElementById("resize-handle");

let resizing = false;

handle.addEventListener("mousedown", (e) => {
    e.preventDefault();          // Prevent text selection
    resizing = true;
    document.body.style.userSelect = "none";
});

document.addEventListener("mousemove", (e) => {
    if (!resizing) return;

    const width = window.innerWidth - e.clientX;

    sidebar.style.width =
        Math.max(325, Math.min(width, window.innerWidth * 0.8)) + "px";
});

document.addEventListener("mouseup", () => {
    resizing = false;
    document.body.style.userSelect = "";
});

helpButton.addEventListener("click", () => {
    sidebar.classList.toggle("open");
});

const loadingOverlay =
    document.getElementById("loading-overlay");

const loadingMessage =
    document.getElementById("loading-message");

function showLoading(message) {
    loadingMessage.textContent = message;
    loadingOverlay.classList.remove("hidden");
}

function hideLoading() {
    loadingOverlay.classList.add("hidden");
}

let loadingInterval = null;

function showLoading(message) {

    let dots = 0;

    loadingInterval = setInterval(() => {

        dots = (dots + 1) % 4;

        document.getElementById(
            "loading-title"
        ).textContent =
            "Loading" + ".".repeat(dots);

    }, 500);

    loadingMessage.textContent = message;

    loadingOverlay.classList.remove("hidden");
}

function hideLoading() {

    clearInterval(loadingInterval);

    loadingOverlay.classList.add("hidden");
}

let cy = cytoscape({
    container: document.getElementById("cy"),

    elements: [],

    style: [
        {
            selector: "node",
            style: {
                label: ""
            }
        },

        {
            selector: ".hovered",
            style: {
                label: "data(label)"
            }
        },

        {
            selector: 'node[type="Public_AS"]',
            style: {
                "background-color": "#ffcc00"
            }
        },

        {
            selector: 'node[type="Private_AS"]',
            style: {
                "background-color": "blue"
            }
        },

        {
            selector: 'node[type="Router"]',
            style: {
                "background-color": "green",
                shape: "rectangle"
            }
        },

        {
            selector: "edge",
            style: {
                width: 1,
                "curve-style": "haystack"
            }
        }
    ]
});

cy.on("mouseover", "node", evt => { evt.target.addClass("hovered"); });
cy.on("mouseout", "node", evt => { evt.target.removeClass("hovered"); });

function renderGraph(cy, data, layoutName = "concentric") {

    cy.elements().remove();

    cy.add([
        ...(data.nodes || []),
        ...(data.edges || [])
    ]);
    const hasEdges = data.edges && data.edges.length > 0;

    if (layoutName === "fcose") {
        cy.layout({
            name: "fcose",
            quality: "default",
            nodeRepulsion: node => 400 + node.degree() * 50,
            idealEdgeLength: edge => {
                const src = edge.source().degree();
                const tgt = edge.target().degree();

                let dif = Math.abs(src - tgt);

                return 10 + dif;
            },
            numIter: 5,
            animate: false
        }).run();
    }
    else {
        cy.layout({
            name: hasEdges ? "concentric" : "grid",
            concentric: node => node.degree(),
            spacingFactor: 2,
            minNodeSpacing: 10
        }).run();
    }

    cy.fit();
}

showLoading("Loading overview graph");

fetch(`${ip}/api/overview`, {
    credentials: "include"
})
    .then(response => {
        if (response.status === 401) {
            window.location = login_page;
            throw new Error("Unauthorized");
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    })
    .then(data => {
        if (currentGraphRequest !== 0)
            return;
        renderGraph(cy, data);
    })
    .catch(err => {
        console.error(`Request failed: ${err}, Message ${err.message}`);
    })
    .finally(() => {
        if (currentGraphRequest === 0)
            hideLoading();
    });

document
    .getElementById("run-query")
    .addEventListener("click", () => {

        const query =
            document.getElementById("cypher-query").value;

        const requestId = ++currentGraphRequest;

        showLoading("Running Cypher query");

        fetch(
            `${ip}/api/visualize`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query
                })
            }
        )
    .then(response => {
        if (response.status === 401) {
            window.location = login_page;
            throw new Error("Unauthorized");
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    })
        .then(data => {
            if (requestId !== currentGraphRequest)
                return;
            renderGraph(cy, data);
        })
        .catch(err => {
            console.error(`Request failed: ${err}, Message ${err.message}`);
        })
        .finally(() => {
            if (requestId === currentGraphRequest)
                hideLoading();
        });
    });

function runLocalLayout(newNodes, newEdges, clickedNode) {
    const neighborhood = clickedNode.union(newNodes).union(newEdges);

    const oldNodes =
        cy.nodes().not(neighborhood.nodes());

    oldNodes.lock();
    clickedNode.lock();

    let layout;

    if (newNodes.length > 200) {

        layout = neighborhood.layout({
            name: "concentric",
            fit: false,
            animate: true,
            concentric: node => node.degree(),
            spacingFactor: 1.5,
            minNodeSpacing: 10
        });

    } else {

        layout = neighborhood.layout({
            name: "fcose",

            animate: true,
            fit: false,
            randomize: false,

            quality: "default",

            nodeRepulsion: node => 800,

            idealEdgeLength: edge => 100,

            gravity: 0.25
        });

    }

    layout.on("layoutstop", () => {

        oldNodes.unlock();
        clickedNode.unlock();

    });

    layout.run();

    // Fallback
    setTimeout(() => {
        oldNodes.unlock();
        clickedNode.unlock();
    }, 3000);
}

function addInspectionResult(
    cy,
    clickedNode,
    data
) {

    const existing =
        new Set(cy.nodes().map(n => n.id()));

    const newNodes = data.nodes
        .filter(n => !existing.has(n.data.id));

    const addedNodes =
        cy.add(newNodes);

    const addedEdges =
        cy.add(data.edges);

    addedNodes.forEach(node => {
        node.position({
            x: clickedNode.position("x") +
               (Math.random() - 0.5) * 100,

            y: clickedNode.position("y") +
               (Math.random() - 0.5) * 100
        });
    });

    runLocalLayout(
        addedNodes,
        addedEdges,
        clickedNode
    );
}

cy.on("tap", "node", async evt => {

    const node = evt.target;

    const id = node.data("id");
    const type = node.data("type");
    const requestId = currentGraphRequest;
    let loadingShown = false;

    const timer = setTimeout(() => {
        loadingShown = true;
        showLoading("Inspecting neighbouring entities");
    }, 1000);

    try {

        const response = await fetch(
            `${ip}/api/inspect`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id,
                    type
                })
            }
        );

        if (response.status === 401) {
            window.location = login_page;
            return
        }

        const data = await response.json();

        if (requestId === currentGraphRequest)
            addInspectionResult(cy, node, data);

    }
    catch (err) {
        console.error(`Request failed: ${err}, Message ${err.message}`);
    }
    finally {
        clearTimeout(timer);

        if (loadingShown)
            hideLoading();
    }
});
document
    .querySelectorAll(".copy-query")
    .forEach(button => {

        button.addEventListener("click", async () => {

            const query =
                button.parentElement
                    .querySelector("pre")
                    .innerText;


            await navigator.clipboard.writeText(query);


            button.classList.add("copied");

            button.innerHTML =
                `
                <i class="fa-solid fa-check"></i>
                <span>Copied!</span>
                `;


            setTimeout(() => {

                button.classList.remove("copied");

                button.innerHTML =
                    `
                    <i class="fa-solid fa-copy"></i>
                    `;

            }, 1200);

        });

    });

document
    .getElementById("logout")
    .addEventListener("click", async () => {

        await fetch(`${ip}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });

        window.location = login_page;
    });