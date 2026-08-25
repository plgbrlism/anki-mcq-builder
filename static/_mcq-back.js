window.initM3Back = function (shadowRoot) {
  var LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"];

  var choicesEl = document.getElementById("raw-choices");
  var answerEl = document.getElementById("raw-answer");
  var root = shadowRoot || document;
  var container =
    root.querySelector("#m3-options-back-container") ||
    root.querySelector(".m3-options-group");
  var banner = root.querySelector("#m3-check-banner");
  var explanation = root.querySelector("#m3-explanation");
  if (!choicesEl || !answerEl || !container) return;

  var answer = answerEl.textContent.trim();

  if (typeof window.__m3Cache === "undefined") {
    window.__m3Cache =
      window.name && window.name.startsWith("m3:") ? window.name : "";
    window.name = "";
  }
  var raw = window.__m3Cache;

  var selected = "";
  var perm = null;
  if (raw.startsWith("m3:")) {
    var parts = raw.slice(3).split(":");
    if (parts.length === 2) {
      perm = parts[0].split(",").map(Number);
      selected = parts[1];
    }
  }

  if (explanation && !explanation.textContent.trim()) {
    explanation.style.display = "none";
  }

  container.innerHTML = "";

  var rawChoices = choicesEl.innerHTML
    .split(/<br\s*\/?>|\n/gi)
    .map(function (c) {
      var t = document.createElement("div");
      t.innerHTML = c;
      return t.textContent.trim();
    })
    .filter(Boolean)
    .map(function (text) {
      return { text: text };
    });

  var options =
    perm && perm.length === rawChoices.length
      ? perm.map(function (i) { return rawChoices[i]; })
      : rawChoices;

  var answered = selected !== "";

  options.forEach(function (opt, idx) {
    var btn = document.createElement("div");
    btn.className = "m3-option-item";
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");
    btn.setAttribute("aria-disabled", "true");

    var pill = document.createElement("span");
    pill.className = "m3-option-pill";
    pill.textContent = LETTERS[idx] || (idx + 1);

    var content = document.createElement("span");
    content.className = "m3-option-content";
    content.textContent = opt.text;

    btn.appendChild(pill);
    btn.appendChild(content);

    var isCorrect = opt.text === answer;
    var isSelected = opt.text === selected;

    if (isCorrect) {
      btn.classList.add(isSelected ? "state-correct" : "state-missed");
    } else if (isSelected) {
      btn.classList.add("state-wrong");
    }

    container.appendChild(btn);
  });

  if (banner && answered) {
    var correct = selected === answer;
    banner.textContent = correct ? "Correct" : "Wrong";
    banner.className =
      "m3-check-banner visible " + (correct ? "correct" : "wrong");
  }
};
