const ICONS = [
    'apple', 'apricot', 'banana', 'big_win', 'cherry', 'grapes', 'lemon', 'lucky_seven', 'orange', 'pear', 'strawberry', 'watermelon',
];

/**
 * @type {number} The minimum spin time in seconds
 */
const BASE_SPINNING_DURATION = 2.7;

/**
 * @type {number} The additional duration to the base duration for each row (in seconds).
 * It makes the typical effect that the first reel ends, then the second, and so on...
 */
const COLUMN_SPINNING_DURATION = 0.3;


var cols;


window.addEventListener('DOMContentLoaded', function(event) {
    cols = document.querySelectorAll('.col');

    setInitialItems();
});

function setInitialItems() {
    let baseItemAmount = 40;

    for (let i = 0; i < cols.length; ++i) {
        let col = cols[i];
        let amountOfItems = baseItemAmount + (i * 3); // Increment the amount for each column
        let elms = '';
        let firstThreeElms = '';

        for (let x = 0; x < amountOfItems; x++) {
            let icon = getRandomIcon();
            let item = '<div class="icon" data-item="' + icon + '"><img src="/static/items/' + icon + '.png"></div>';
            elms += item;

            if (x < 3) firstThreeElms += item; // Backup the first three items because the last three must be the same
        }
        col.innerHTML = elms + firstThreeElms;
    }
}

/**
 * Called when the start-button is pressed.
 *
 * @param elem The button itself
 */
function spin(elem) {
    let duration = BASE_SPINNING_DURATION + randomDuration();

    for (let col of cols) { // set the animation duration for each column
        duration += COLUMN_SPINNING_DURATION + randomDuration();
        col.style.animationDuration = duration + "s";
    }

    // disable the start-button
    elem.setAttribute('disabled', true);

    // set the spinning class so the css animation starts to play
    document.getElementById('container').classList.add('spinning');

    // set the result delayed
    // this would be the right place to request the combination from the server
    window.setTimeout(setResult, BASE_SPINNING_DURATION * 1000 / 2);

    window.setTimeout(function () {
        // after the spinning is done, remove the class and enable the button again
        document.getElementById('container').classList.remove('spinning');
        elem.removeAttribute('disabled');
    }.bind(elem), duration * 1000);
}

/**
 * Sets the result items at the beginning and the end of the columns
 */
function setResult() {
    for (let col of cols) {

        // generate 3 random items
        let results = [
            getRandomIcon(),
            getRandomIcon(),
            getRandomIcon()
        ];

        let icons = col.querySelectorAll('.icon img');
        // replace the first and last three items of each column with the generated items
        for (let x = 0; x < 3; x++) {
            icons[x].setAttribute('src', '/static/items/' + results[x] + '.png');
            icons[(icons.length - 3) + x].setAttribute('src', '/static/items/' + results[x] + '.png');
        }
    }
}

function getRandomIcon() {
    return ICONS[Math.floor(Math.random() * ICONS.length)];
}

/**
 * @returns {number} 0.00 to 0.09 inclusive
 */
function randomDuration() {
    return Math.floor(Math.random() * 10) / 100;
}


const canvas = document.getElementById("renderCanvas");
const engine = new BABYLON.Engine(canvas, true);

const createScene = () => {
    const scene = new BABYLON.Scene(engine);

    // Camera and Lights
    const camera = new BABYLON.ArcRotateCamera("camera", Math.PI / 2, Math.PI / 3, 20, BABYLON.Vector3.Zero(), scene);
    camera.attachControl(canvas, true);

    const light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0, 1, 0), scene);
    light.intensity = 1.2;

    // Background
    const background = new BABYLON.Layer("background", null, scene);
    background.texture = new BABYLON.Texture("https://i.imgur.com/2YatYaE.jpg", scene); // Replace with a dark cave image.

    // Slot Machine Frame
    const frame = BABYLON.MeshBuilder.CreateBox("frame", { width: 16, height: 10, depth: 1 }, scene);
    frame.position.z = -2;
    const frameMaterial = new BABYLON.StandardMaterial("frameMaterial", scene);
    frameMaterial.diffuseColor = new BABYLON.Color3(0.2, 0.2, 0.2);
    frameMaterial.emissiveColor = new BABYLON.Color3(0.8, 0.8, 0.8);
    frame.material = frameMaterial;

    // Gems
    const reels = [];
    const gemColors = ["red", "orange", "yellow", "green", "blue", "purple"];

    for (let i = 0; i < 5; i++) {
        const reel = [];
        for (let j = 0; j < 5; j++) {
            const gem = BABYLON.MeshBuilder.CreateSphere(`gem${i}-${j}`, { diameter: 1 }, scene);
            gem.position.x = -8 + i * 4; // Spacing between reels
            gem.position.y = 4 - j * 2; // Spacing between gems

            const gemMaterial = new BABYLON.StandardMaterial(`gemMaterial${i}-${j}`, scene);
            const color = gemColors[Math.floor(Math.random() * gemColors.length)];
            gemMaterial.diffuseColor = BABYLON.Color3[color.toUpperCase()];
            gem.material = gemMaterial;

            reel.push(gem);
        }
        reels.push(reel);
    }

    // Spin Button Logic
    const spinButton = document.getElementById("spinButton");
    const resultText = document.getElementById("resultText");

    spinButton.addEventListener("click", () => {
        resultText.textContent = "Spinning...";
        spinButton.disabled = true;

        // Call function before spinning
        resordSpin().then(() => {
            reels.forEach((reel, index) => {
                reel.forEach((gem, i) => {
                    const animation = new BABYLON.Animation(
                        `spin${index}-${i}`,
                        "position.y",
                        30,
                        BABYLON.Animation.ANIMATIONTYPE_FLOAT,
                        BABYLON.Animation.ANIMATIONLOOPMODE_CYCLE
                    );

                    const keyFrames = [
                        { frame: 0, value: gem.position.y },
                        { frame: 15, value: gem.position.y - 10 },
                        { frame: 30, value: gem.position.y },
                    ];

                    animation.setKeys(keyFrames);
                    gem.animations = [];
                    gem.animations.push(animation);

                    scene.beginAnimation(gem, 0, 30, false);
                });
            });

            setTimeout(() => {
                resultText.textContent = "🎉 SPIN COMPLETE!";
                spinButton.disabled = false;
            }, 2000);
        });
    });

    return scene;
};

async function resordSpin() {
    try {
        // Assuming the contract has a function to record spins
        console.log('Spin recorded on:', receipt);
    } catch (error) {
        console.error('Error recording spin on:', error);
    }
}

const scene = createScene();
engine.runRenderLoop(() => {
    scene.render();
});

window.addEventListener("resize", () => {
    engine.resize();
});