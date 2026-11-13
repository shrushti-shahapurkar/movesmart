const catchArea =
    document.getElementById("catchGameArea");

const basket =
    document.getElementById("basket");

const catchStartButton =
    document.getElementById("catchStartButton");

const catchStart =
    document.getElementById("catchStart");

const caughtElement =
    document.getElementById("caught");

const missedElement =
    document.getElementById("missed");

const timerElement =
    document.getElementById("catchTimer");

const catchMessage =
    document.getElementById("catchMessage");


let caught = 0;
let missed = 0;

let gameRunning = false;

let remainingTime = 30;

let gameStartTime;

let timerInterval;
let objectInterval;


catchStartButton.addEventListener(
    "click",
    startCatchGame
);


function startCatchGame() {

    caught = 0;
    missed = 0;

    remainingTime = 30;

    gameRunning = true;

    caughtElement.textContent = "0";
    missedElement.textContent = "0";
    timerElement.textContent = "30s";

    catchStart.style.display = "none";

    gameStartTime = Date.now();

    timerInterval = setInterval(() => {

        remainingTime--;

        timerElement.textContent =
            remainingTime + "s";

        if (remainingTime <= 0) {

            finishCatchGame();

        }

    }, 1000);


    objectInterval =
        setInterval(createFallingObject, 900);
}


catchArea.addEventListener(
    "mousemove",
    moveBasket
);


catchArea.addEventListener(
    "touchmove",
    function(event) {

        const touch = event.touches[0];

        moveBasketPosition(
            touch.clientX
        );

    }
);


function moveBasket(event) {

    moveBasketPosition(event.clientX);
}


function moveBasketPosition(clientX) {

    if (!gameRunning) return;

    const rect =
        catchArea.getBoundingClientRect();

    let x =
        clientX - rect.left - 40;

    x = Math.max(
        0,
        Math.min(
            x,
            rect.width - 80
        )
    );

    basket.style.left = x + "px";
}


function createFallingObject() {

    if (!gameRunning) return;

    const object =
        document.createElement("div");

    object.className =
        "falling-object";

    object.innerHTML =
        ["⭐", "🟢", "🔵", "🟡"][
            Math.floor(Math.random() * 4)
        ];

    const maxX =
        catchArea.clientWidth - 45;

    object.style.left =
        Math.random() * maxX + "px";

    object.style.top = "-50px";

    catchArea.appendChild(object);

    let y = -50;

    const speed =
        2 + Math.random() * 2;

    const fallInterval =
        setInterval(() => {

            if (!gameRunning) {

                clearInterval(fallInterval);

                object.remove();

                return;
            }

            y += speed;

            object.style.top =
                y + "px";


            if (checkCollision(object, basket)) {

                caught++;

                caughtElement.textContent =
                    caught;

                object.remove();

                clearInterval(fallInterval);

                return;
            }


            if (y >
                catchArea.clientHeight) {

                missed++;

                missedElement.textContent =
                    missed;

                object.remove();

                clearInterval(fallInterval);
            }

        }, 20);
}


function checkCollision(object, basket) {

    const objectRect =
        object.getBoundingClientRect();

    const basketRect =
        basket.getBoundingClientRect();

    return !(
        objectRect.right <
        basketRect.left ||

        objectRect.left >
        basketRect.right ||

        objectRect.bottom <
        basketRect.top ||

        objectRect.top >
        basketRect.bottom
    );
}


function finishCatchGame() {

    gameRunning = false;

    clearInterval(timerInterval);
    clearInterval(objectInterval);

    const total =
        caught + missed;

    const accuracy =
        total > 0
            ? (caught / total) * 100
            : 0;

    const score =
        Math.round(accuracy);

    const completionTime = 30;

    catchMessage.innerHTML = `

        <h2>🎉 Game Completed!</h2>

        <p>
            Objects Caught:
            ${caught}
        </p>

        <p>
            Objects Missed:
            ${missed}
        </p>

        <p>
            Accuracy:
            ${accuracy.toFixed(1)}%
        </p>

        <p>
            Score:
            ${score}%
        </p>

        <button onclick="saveCatchResult()"
                class="primary-button">

            Save Result & Continue

        </button>

    `;


    window.catchGameData = {

        score: score,

        accuracy: accuracy,

        completion_time: completionTime,

        errors: missed,

        objects_caught: caught,

        objects_missed: missed

    };
}


function saveCatchResult() {

    fetch("/save_game_result", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            game_name:
                "Catch Object",

            score:
                window.catchGameData.score,

            accuracy:
                window.catchGameData.accuracy,

            completion_time:
                window.catchGameData.completion_time,

            errors:
                window.catchGameData.errors,

            objects_caught:
                window.catchGameData.objects_caught,

            objects_missed:
                window.catchGameData.objects_missed

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