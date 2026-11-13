
const gameArea = document.getElementById("targetGameArea");
const startButton = document.getElementById("startButton");
const startMessage = document.getElementById("startMessage");

const targetCountElement = document.getElementById("targetCount");
const scoreElement = document.getElementById("score");
const timerElement = document.getElementById("timer");
const gameMessage = document.getElementById("gameMessage");

const TOTAL_TARGETS = 15;

let currentTarget = 0;
let score = 0;
let correctClicks = 0;
let wrongClicks = 0;

let gameStartTime = 0;
let targetAppearTime = 0;

let totalReactionTime = 0;
let timerInterval = null;
let gameFinished = false;


// Start game
startButton.addEventListener("click", startGame);


function startGame() {

    // Reset all game values
    currentTarget = 0;
    score = 0;
    correctClicks = 0;
    wrongClicks = 0;
    totalReactionTime = 0;
    gameFinished = false;

    window.targetGameData = null;

    // Clear any previous targets
    gameArea.querySelectorAll(".target").forEach(target => {
        target.remove();
    });

    // Clear old timer
    if (timerInterval !== null) {
        clearInterval(timerInterval);
    }

    scoreElement.textContent = "0";
    targetCountElement.textContent = "0 / " + TOTAL_TARGETS;
    timerElement.textContent = "0.0s";
    gameMessage.innerHTML = "";

    startMessage.style.display = "none";
    startButton.disabled = true;

    gameStartTime = Date.now();

    timerInterval = setInterval(updateTimer, 100);

    showNextTarget();
}


// Update elapsed time
function updateTimer() {

    if (gameFinished) {
        return;
    }

    const elapsed = (Date.now() - gameStartTime) / 1000;

    timerElement.textContent = elapsed.toFixed(1) + "s";
}


// Display the next target
function showNextTarget() {

    if (currentTarget >= TOTAL_TARGETS) {

        finishGame();

        return;
    }

    currentTarget++;

    targetCountElement.textContent =
        currentTarget + " / " + TOTAL_TARGETS;

    const target = document.createElement("button");

    target.className = "target";
    target.type = "button";
    target.textContent = "🎯";
    target.setAttribute("aria-label", "Target");

    const areaWidth = Math.max(0, gameArea.clientWidth - 70);
    const areaHeight = Math.max(0, gameArea.clientHeight - 70);

    const randomX = Math.random() * areaWidth;
    const randomY = Math.random() * areaHeight;

    target.style.left = randomX + "px";
    target.style.top = randomY + "px";

    targetAppearTime = Date.now();

    target.addEventListener("click", function(event) {

        event.stopPropagation();

        if (gameFinished) {
            return;
        }

        const reaction =
            (Date.now() - targetAppearTime) / 1000;

        totalReactionTime += reaction;
        correctClicks++;

        // Update visible score
        score = Math.round(
            (correctClicks / TOTAL_TARGETS) * 100
        );

        scoreElement.textContent = score;

        target.remove();

        setTimeout(showNextTarget, 250);
    });

    gameArea.appendChild(target);
}


// Count clicks on empty game area as misses
gameArea.addEventListener("click", function(event) {

    if (
        !gameFinished &&
        event.target === gameArea
    ) {
        wrongClicks++;
    }
});


// Finish the game
function finishGame() {

    if (gameFinished) {
        return;
    }

    gameFinished = true;

    clearInterval(timerInterval);

    const completionTime =
        (Date.now() - gameStartTime) / 1000;

    // Accuracy is based on correct and incorrect clicks
    const totalClicks = correctClicks + wrongClicks;

    const accuracy = totalClicks > 0
        ? (correctClicks / totalClicks) * 100
        : 0;

    // Avoid NaN or Infinity when no targets were clicked
    const averageReaction = correctClicks > 0
        ? totalReactionTime / correctClicks
        : 0;

    // Score reflects the proportion of targets successfully hit
    const finalScore = Math.round(
        (correctClicks / TOTAL_TARGETS) * 100
    );

    gameMessage.innerHTML = `
        <h2>🎉 Game Completed!</h2>

        <p>Targets Hit: ${correctClicks} / ${TOTAL_TARGETS}</p>

        <p>Accuracy: ${accuracy.toFixed(1)}%</p>

        <p>
            Average Reaction Time:
            ${averageReaction.toFixed(2)} sec
        </p>

        <p>Score: ${finalScore}%</p>

        <p>Missed Clicks: ${wrongClicks}</p>

        <button id="saveResultButton" class="primary-button">
            Save Result & Continue
        </button>
    `;

    window.targetGameData = {
        game_name: "Target Tap",
        score: finalScore,
        accuracy: Number(accuracy.toFixed(2)),
        reaction_time: Number(averageReaction.toFixed(3)),
        completion_time: Number(completionTime.toFixed(3)),
        errors: wrongClicks,
        objects_caught: 0,
        objects_missed: 0,
        path_deviation: 0
    };

    document
        .getElementById("saveResultButton")
        .addEventListener("click", saveResult);
}


// Save result to Flask
async function saveResult() {

    const saveButton = document.getElementById("saveResultButton");

    if (!window.targetGameData || !saveButton) {
        alert("Please complete the game first.");
        return;
    }

    saveButton.disabled = true;
    saveButton.textContent = "Saving...";

    try {

        const response = await fetch("/save_game_result", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(window.targetGameData)

        });

        const data = await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.message || "Failed to save result."
            );
        }

        // Open results page after saving
        window.location.href = "/result";

    } catch (error) {

        console.error("Save result error:", error);

        alert(
            "Could not save your result. " +
            "Please try again.\n" +
            error.message
        );

        saveButton.disabled = false;
        saveButton.textContent = "Save Result & Continue";
    }
}
