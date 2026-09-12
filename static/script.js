document.addEventListener("DOMContentLoaded", () => {

    // ==========================
    // WIZARD ELEMENTS
    // ==========================

    const steps = document.querySelectorAll(".step");
    const nextBtns = document.querySelectorAll(".next");
    const prevBtns = document.querySelectorAll(".prev");
    const progressBar = document.querySelector(".progress-bar");

    let currentStep = 0;

    // ==========================
    // UPDATE STEPS
    // ==========================

    function updateSteps() {

        steps.forEach((step, index) => {

            if (index === currentStep) {
                step.classList.add("active");
            } else {
                step.classList.remove("active");
            }

        });

        if (progressBar) {

            const progress =
                ((currentStep + 1) / steps.length) * 100;

            progressBar.style.width = progress + "%";

        }

    }

    // ==========================
    // NEXT BUTTON
    // ==========================

    nextBtns.forEach(btn => {

        btn.addEventListener("click", () => {

            if (currentStep < steps.length - 1) {

                currentStep++;
                updateSteps();

            }

        });

    });

    // ==========================
    // PREVIOUS BUTTON
    // ==========================

    prevBtns.forEach(btn => {

        btn.addEventListener("click", () => {

            if (currentStep > 0) {

                currentStep--;
                updateSteps();

            }

        });

    });

    // ==========================
    // INITIAL LOAD
    // ==========================

    updateSteps();

    // ==========================
    // THEME TOGGLE
    // ==========================

    const themeBtn =
        document.getElementById("themeToggle");

    if (themeBtn) {

        themeBtn.addEventListener("click", () => {

            document.body.classList.toggle("light-mode");

        });

    }

    // ==========================
    // FORM SUBMIT
    // ==========================

    const resumeForm =
        document.getElementById("resumeForm");

    resumeForm.addEventListener(
        "submit",
        async function (e) {

            e.preventDefault();

            console.log("FORM SUBMITTED");

            const loadingScreen =
                document.getElementById(
                    "loadingScreen"
                );

            const successScreen =
                document.getElementById(
                    "successScreen"
                );

            loadingScreen.classList.remove(
                "hidden"
            );

            const formData =
                new FormData(resumeForm);

            const data =
                Object.fromEntries(
                    formData.entries()
                );

            console.log(data);

            try {

                // The FastAPI backend serves this same index.html/script.js
                // AND the /webhook/RESUME_BUILDER endpoint from one origin,
                // so a relative path is all that's needed. If you ever
                // host the frontend separately from the API, set this to
                // the API's full URL instead, e.g. "https://api.example.com".
                const N8N_BASE_URL = "";

                const response =
                    await fetch(
                        `${N8N_BASE_URL}/webhook/RESUME_BUILDER`,
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
                            body:
                                JSON.stringify(data)
                        }
                    );

                if (!response.ok) {
                    throw new Error(
                        "Webhook returned status " + response.status
                    );
                }

                console.log(
                    "Webhook Response:",
                    response
                );

                loadingScreen.classList.add(
                    "hidden"
                );

                document.getElementById(
                    "form"
                ).style.display = "none";

                successScreen.classList.remove(
                    "hidden"
                );

            } catch (error) {

                console.error(error);

                loadingScreen.classList.add(
                    "hidden"
                );

                alert(
                    "Failed to connect to n8n webhook."
                );

            }

        }
    );

});