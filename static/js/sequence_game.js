const sequenceStartButton =
    document.getElementById(
        "sequenceStartButton"
    );

const sequenceStart =
    document.getElementById(
        "sequenceStart"
    );

const numberContainer =
    document.getElementById(
        "numberContainer"
    );

const progressElement =
    document.getElementById(
        "sequenceProgress"
    );

const errorsElement =
    document.getElementById(
        "sequenceErrors"
    );

const timerElement =
    document.getElementById(
        "sequenceTimer"
    );

const sequenceMessage =
    document.getElementById(
        "sequenceMessage"
    );


const TOTAL_NUMBERS = 8;

let nextNumber = 1;

let errors = 0;

let startTime;

let timerInterval;


sequenceStartButton.addEventListener(
    "click",
    startSequenceGame
);


function startSequenceGame() {

    nextNumber = 1;

    errors = 0;

    progressElement.textContent =
        "0 / " + TOTAL_NUMBERS;

    errorsElement.textContent =
        "0";

    sequenceMessage.innerHTML = "";

    sequenceStart.style.display =
        "none";

    numberContainer.innerHTML = "";

    startTime = Date.now();

    timerInterval =
        setInterval(updateTimer, 100);

    createNumbers();
}


function updateTimer() {

    const elapsed =
        (Date.now() - startTime) / 1000;

    timerElement.textContent =
        elapsed.toFixed(1) + "s";
}


function createNumbers() {

    let numbers = [];

    for (
        let i = 1;
        i <= TOTAL_NUMBERS;
        i++
    ) {

        numbers.push(i);
    }


    numbers.sort(
        () => Math.random() - 0.5
    );


    numbers.forEach(number => {

        const button =
            document.createElement("button");

        button.className =
            "sequence-number";

        button.textContent =
            number;

        button.dataset.number =
            number;

        button.addEventListener(
            "click",
            function() {

                checkNumber(
                    number,
                    button
                );

            }
        );

        numberContainer.appendChild(
            button
        );

    });
}


function checkNumber(
    number,
    button
) {

    if (number === nextNumber) {

        button.classList.add(
            "correct-number"
        );

        button.disabled = true;

        nextNumber++;

        progressElement.textContent =
            (nextNumber - 1) +
            " / " +
            TOTAL_NUMBERS;


        if (
            nextNumber >
            TOTAL_NUMBERS
        ) {

            finishSequenceGame();

        }

    } else {

        errors++;

        errorsElement.textContent =
            errors;

        button.classList.add(
            "wrong-number"
        );

        setTimeout(() => {

            button.classList.remove(
                "wrong-number"
            );

        }, 300);

    }
}


function finishSequenceGame() {

    clearInterval(timerInterval);

    const completionTime =
        (Date.now() - startTime) / 1000;

    const accuracy =
        Math.max(
            0,
            (TOTAL_NUMBERS /
            (TOTAL_NUMBERS + errors)) *
            100
        );

    const speedScore =
        Math.max(
            0,
            100 -
            ((completionTime - 5) * 2)
        );

    const finalScore =
        Math.round(
            (accuracy * 0.7) +
            (speedScore * 0.3)
        );


    sequenceMessage.innerHTML = `

        <h2>🎉 Game Completed!</h2>

        <p>
            Accuracy:
            ${accuracy.toFixed(1)}%
        </p>

        <p>
            Completion Time:
            ${completionTime.toFixed(2)} sec
        </p>

        <p>
            Errors:
            ${errors}
        </p>

        <p>
            Score:
            ${finalScore}%
        </p>

        <button onclick="saveSequenceResult()"
                class="primary-button">

            Save Result & Continue

        </button>

    `;


    window.sequenceGameData = {

        score: finalScore,

        accuracy: accuracy,

        completion_time:
            completionTime,

        errors: errors

    };
}


function saveSequenceResult() {

    fetch("/save_game_result", {

        method: "POST",

        headers: {
            "Content-Type":
                "application/json"
        },

        body: JSON.stringify({

            game_name:
                "Sequence Game",

            score:
                window.sequenceGameData.score,

            accuracy:
                window.sequenceGameData.accuracy,

            completion_time:
                window.sequenceGameData.completion_time,

            errors:
                window.sequenceGameData.errors

        })

    })

    .then(response => response.json())

    .then(data => {

        if (data.success) {

            window.location.href =
                "/dashboard";

        }

    });

}