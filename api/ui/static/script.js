console.log("script.js loaded and executing."); // <<< Added for initial load debug

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded event fired."); // <<< Added for DOM ready debug

    const form = document.getElementById("pipelineForm");
    const stepsContainer = document.getElementById("stepsContainer");
    const addStepBtn = document.getElementById("addStepBtn");
    const submitPipelineBtn = document.getElementById("submitPipelineBtn");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const buttonText = document.getElementById("buttonText");
    const responseContainer = document.getElementById("responseContainer");
    const responsePre = responseContainer.querySelector("pre");
    const messageContainer = document.getElementById("messageContainer");

    // Check if critical elements are found
    if (!addStepBtn) {
        console.error("Error: addStepBtn element not found in the DOM.");
        return; // Stop execution if critical element is missing
    }
    if (!stepsContainer) {
        console.error("Error: stepsContainer element not found in the DOM.");
        return; // Stop execution if critical element is missing
    }
    if (!submitPipelineBtn) {
        console.error("Error: submitPipelineBtn element not found in the DOM.");
        return;
    }
    if (!loadingSpinner) {
        console.error("Error: loadingSpinner element not found in the DOM.");
        return;
    }
    if (!buttonText) {
        console.error("Error: buttonText element not found in the DOM.");
        return;
    }
    if (!responseContainer) {
        console.error("Error: responseContainer element not found in the DOM.");
        return;
    }
    if (!messageContainer) {
        console.error("Error: messageContainer element not found in the DOM.");
        return;
    }


    let stepIndex = -1; // Start at -1, so the first click makes it 0

    /**
     * Displays a message to the user.
     * @param {string} message - The message content.
     * @param {string} type - 'success', 'error', or 'info' to style the message.
     */
    const showMessage = (message, type) => {
        messageContainer.textContent = message;
        messageContainer.className = `p-4 mb-4 rounded-lg text-sm font-medium ${type === 'success' ? 'bg-green-100 text-green-700' : type === 'error' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'} block`;
        messageContainer.classList.remove('hidden');
        // Automatically hide the message after a few seconds
        setTimeout(() => {
            messageContainer.classList.add('hidden');
        }, 7000);
    };

    /**
     * Clears any displayed messages.
     */
    const clearMessage = () => {
        messageContainer.classList.add('hidden');
        messageContainer.textContent = '';
    };

    /**
     * Shows the loading spinner and disables the submit button.
     */
    const showLoading = () => {
        loadingSpinner.classList.remove('hidden');
        buttonText.textContent = 'Submitting...';
        submitPipelineBtn.disabled = true;
        submitPipelineBtn.classList.add('opacity-75', 'cursor-not-allowed');
    };

    /**
     * Hides the loading spinner and re-enables the submit button.
     */
    const hideLoading = () => {
        loadingSpinner.classList.add('hidden');
        buttonText.textContent = 'Submit Pipeline';
        submitPipelineBtn.disabled = false;
        submitPipelineBtn.classList.remove('opacity-75', 'cursor-not-allowed');
    };

    /**
     * Adds a new processing step dynamically to the form.
     */
    addStepBtn.addEventListener('click', () => {
        console.log("Add Step button clicked!");
        stepIndex++; // Increment to get the current 0-based index
        const stepDiv = document.createElement("div");
        stepDiv.className = "step p-5 bg-gray-50 border border-gray-200 rounded-lg shadow-sm relative";

        // IMPORTANT: input name/id attributes now use stepIndex (0-based)
        stepDiv.innerHTML = `
            <h4 class="text-lg font-semibold text-gray-800 mb-3">Step ${stepIndex + 1}</h4>
            <button type="button" class="remove-step-btn absolute top-3 right-3 text-red-500 hover:text-red-700 text-xl font-bold" aria-label="Remove step">&times;</button>
            
            <div class="mb-3">
                <label for="main_${stepIndex}" class="block text-gray-700 text-sm font-medium mb-1">
                    Main Transformation Script (required):
                </label>
                <input type="file" id="main_${stepIndex}" name="main_${stepIndex}" required
                       class="w-full p-2 border border-gray-300 rounded-md text-gray-900 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer">
                <p class="text-xs text-gray-500 mt-1">e.g., <code class="font-mono text-xs">transform_data.py</code></p>
            </div>
            
            <div class="mb-3">
                <label for="pre_${stepIndex}" class="block text-gray-700 text-sm font-medium mb-1">
                    Pre-Hook Script (optional):
                </label>
                <input type="file" id="pre_${stepIndex}" name="pre_${stepIndex}"
                       class="w-full p-2 border border-gray-300 rounded-md text-gray-900 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-yellow-50 file:text-yellow-700 hover:file:bg-yellow-100 cursor-pointer">
                <p class="text-xs text-gray-500 mt-1">Script to run before main transformation.</p>
            </div>

            <div>
                <label for="post_${stepIndex}" class="block text-gray-700 text-sm font-medium mb-1">
                    Post-Hook Script (optional):
                </label>
                <input type="file" id="post_${stepIndex}" name="post_${stepIndex}"
                       class="w-full p-2 border border-gray-300 rounded-md text-gray-900 file:mr-4 file:py-1 file:px-3 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer">
                <p class="text-xs text-gray-500 mt-1">Script to run after main transformation.</p>
            </div>
        `;
        stepsContainer.appendChild(stepDiv);

        // Add event listener to the new remove button
        stepDiv.querySelector('.remove-step-btn').addEventListener('click', () => {
            stepDiv.remove();
            // Note: When removing steps, indices of subsequent steps are NOT re-adjusted for simplicity.
            // This is fine for FormData keys, but means step numbers (e.g., "Step 3") might not be consecutive
            // if a middle step is removed. For production, you might re-index or use unique step IDs.
        });
    });

    // Handle form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearMessage();
        showLoading();
        responseContainer.classList.add('hidden'); // Hide previous response

        const formData = new FormData();
        const steps = []; // This array will hold the step metadata for the pipeline JSON
        let isValid = true;

        // Collect pipeline definition and dataset files
        const pipelineFile = document.getElementById("pipelineDefinition").files[0];
        const datasetFile = document.getElementById("datasetFile").files[0];
        const batchSize = document.getElementById("batchSize").value;

        if (!pipelineFile) {
            showMessage("Pipeline Definition file is required.", "error");
            isValid = false;
        } else {
            formData.append("pipeline", pipelineFile); // Still send original pipeline.json
        }

        if (!datasetFile) {
            showMessage("Dataset file is required.", "error");
            isValid = false;
        } else {
            formData.append("dataset", datasetFile);
        }

        if (!batchSize || parseInt(batchSize) < 1) {
            showMessage("Batch size must be a positive number.", "error");
            isValid = false;
        } else {
            formData.append("batch_size", batchSize);
        }

        // Collect step files and metadata
        const currentStepDivs = document.querySelectorAll(".step"); // Re-query all current steps
        if (currentStepDivs.length === 0) {
            showMessage("At least one pipeline step is required.", "error");
            isValid = false;
        }

        currentStepDivs.forEach((div, idx) => { // Use idx for the 0-based iteration over existing divs
            // Dynamically get the input elements using their generated names (main_0, main_1, etc.)
            // The stepIndex from addStepBtn is now the actual index for these inputs
            const mainFile = div.querySelector(`input[name="main_${idx}"]`)?.files?.[0]; 
            const preFile = div.querySelector(`input[name="pre_${idx}"]`)?.files?.[0];
            const postFile = div.querySelector(`input[name="post_${idx}"]`)?.files?.[0];

            if (!mainFile) {
                showMessage(`Step ${idx + 1} is missing a main transformation script.`, "error");
                isValid = false;
                // Do not return here; continue to check other steps for validity
            }

            // IMPORTANT: Append files to FormData with 0-indexed keys (main_0, pre_0, post_0)
            formData.append(`main_${idx}`, mainFile); // Aligns with backend expectation
            if (preFile) formData.append(`pre_${idx}`, preFile);
            if (postFile) formData.append(`post_${idx}`, postFile);

            // Construct step metadata for the pipeline JSON (send just filenames)
            steps.push({
                name: `step_${idx}`, // Use 0-based index for step name in JSON
                main_script: mainFile ? mainFile.name : null, // Ensure name is null if no file
                pre_script: preFile ? preFile.name : null,
                post_script: postFile ? postFile.name : null
            });
        });

        if (!isValid) {
            hideLoading();
            return;
        }

        // Add the pipeline definition JSON string to FormData
        const pipelineJsonBlob = new Blob([JSON.stringify({ pipeline_name: "user_submitted_pipeline", steps: steps }, null, 2)], { type: 'application/json' });
        formData.append("pipeline_definition_json", pipelineJsonBlob, "pipeline_definition.json"); // Provide a filename

        // Debug: log FormData contents (for development, remove in production)
        for (let pair of formData.entries()) {
            // Check if the value is a File object
            if (pair[1] instanceof File) {
                console.log(`${pair[0]}: File - ${pair[1].name} (${pair[1].size} bytes)`);
            } else {
                console.log(`${pair[0]}:`, pair[1]);
            }
        }

        try {
            const response = await fetch("/submit_pipeline", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            responsePre.textContent = JSON.stringify(result, null, 2);
            responseContainer.classList.remove('hidden');
            showMessage("Pipeline submitted successfully!", "success");
        } catch (error) {
            console.error("Error submitting pipeline:", error);
            responsePre.textContent = `Submission failed: ${error.message || error}`;
            responseContainer.classList.remove('hidden');
            showMessage(`Submission failed: ${error.message || 'An unknown error occurred.'}`, "error");
        } finally {
            hideLoading();
        }
    });

    // Initialize with one default step (using a real click event)
    addStepBtn.click();
});
