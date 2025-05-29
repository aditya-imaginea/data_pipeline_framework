document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("pipelineForm");
    const stepsContainer = document.getElementById("stepsContainer");

    // Add a new processing step
    window.addStep = function () {
        const stepIndex = stepsContainer.querySelectorAll(".step").length;

        const div = document.createElement("div");
        div.className = "step";

        div.innerHTML = `
            <h4>Step ${stepIndex + 1}</h4>
            <label>Main Transformation Script (required):</label>
            <input type="file" id="main_${stepIndex}"  name="main_${stepIndex}" required><br>
            <label>Pre-Hook Script (optional):</label>
            <input type="file" id="pre_${stepIndex}" name="pre_${stepIndex}"><br>
            <label>Post-Hook Script (optional):</label>
            <input type="file" id="post_${stepIndex}" name="post_${stepIndex}"><br>
            <hr>
        `;

        stepsContainer.appendChild(div);
    };

    // Handle form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const stepDivs = document.querySelectorAll(".step");
        const formData = new FormData();
        const steps = [];

        stepDivs.forEach((div, index) => {
            const mainFile = div.querySelector(`input[name=main_${index}]`)?.files?.[0];
            const preFile = div.querySelector(`input[name=pre_${index}]`)?.files?.[0];
            const postFile = div.querySelector(`input[name=post_${index}]`)?.files?.[0];

            if (!mainFile) {
                alert(`Step ${index + 1} is missing a main transformation script.`);
                return;
            }

            steps.push({
                id: `step_${index + 1}`,
                main_script: `main_${index}`,
                pre_script: preFile ? `pre_${index}` : null,
                post_script: postFile ? `post_${index}` : null
            });

            formData.append(`main_${index}`, mainFile);
            if (preFile) formData.append(`pre_${index}`, preFile);
            if (postFile) formData.append(`post_${index}`, postFile);
        });

        const pipelineJson = {
            pipeline_name: "user_submitted_pipeline",
            steps: steps
        };

        const pipelineFile = document.getElementById("pipelineDefinition").files[0];
        formData.append("pipeline", pipelineFile);
        if (!pipelineFile) {
            alert("pipeline Definition file is required.");
            return;
        }

        const datasetFile = document.getElementById("datasetFile").files[0];
        if (!datasetFile) {
            alert("Dataset file is required.");
            return;
        }
        formData.append("dataset", datasetFile);

        const batchSize = document.getElementById("batchSize").value;
        formData.append("batch_size", batchSize);

        // Debug: log FormData contents
        for (let pair of formData.entries()) {
            console.log(`${pair[0]}:`, pair[1]);
        }

        try {
            const response = await fetch("/submit_pipeline", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            document.getElementById("responseContainer").innerText = JSON.stringify(result, null, 2);
        } catch (error) {
            console.error("Error submitting pipeline:", error);
            document.getElementById("responseContainer").innerText = "Submission failed.";
        }
    });
});
