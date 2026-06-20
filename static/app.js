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
            selector: 'node[type="public_as"]',
            style: {
                "background-color": "#ffcc00"
            }
        },

        {
            selector: 'node[type="private_as"]',
            style: {
                "background-color": "blue"
            }
        },

        {
            selector: 'node[type="router"]',
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
        ...data.nodes,
        ...data.edges
    ]);

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
            name: "concentric",
            concentric: node => node.degree(),
            spacingFactor: 2,
            minNodeSpacing: 10
        }).run();
    }

    cy.fit();
}

fetch("/api/overview")
    .then(r => r.json())
    .then(data => renderGraph(cy, data))
    .catch(err => console.error(err));

document
    .getElementById("run-query")
    .addEventListener("click", () => {

        const query =
            document.getElementById("cypher-query").value;

        fetch("/api/visualize", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query
            })
        })
        .then(r => r.json())
        .then(data => {
            console.log(data);

            renderGraph(cy, data);
        })
        .catch(err => console.error(err));
    });