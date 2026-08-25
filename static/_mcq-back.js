window.initM3Back = function() {
  const LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"];
  const choicesEl = document.getElementById("raw-choices");
  const answerEl = document.getElementById("raw-answer");
  const container = document.getElementById("m3-options-back-container");
  const banner = document.getElementById("m3-check-banner");
  const explanation = document.getElementById("m3-explanation");
  if (!choicesEl || !answerEl || !container) return;

  const answer = answerEl.textContent.trim();

  let selected = "";
  let perm = null;
  if (window.name) {
    try {
      const data = JSON.parse(window.name);
      perm = data.perm;
      selected = data.selected || "";
    } catch (e) {}
  }
  window.name = ""; 

  if (explanation && !explanation.textContent.trim()) {
    explanation.style.display = "none";
  }

  const rawChoices = choicesEl.innerHTML
    .split(/<br\s*[\/]?>|\n/gi)
    .map(c => {
      const t = document.createElement("div");
      t.innerHTML = c;
      return t.textContent.trim();
    })
    .filter(Boolean);

  const options = (perm && perm.length === rawChoices.length)
    ? perm.map(i => rawChoices[i])
    : rawChoices;

  container.innerHTML = "";
  options.forEach((optText, idx) => {
    const btn = document.createElement("button");
    btn.className = "m3-option-item";
    btn.type = "button";
    btn.disabled = true;
    btn.innerHTML = `<span class="m3-option-pill">${LETTERS[idx] || (idx + 1)}</span>` +
                    `<span class="m3-option-content">${optText}</span>`;

    const isCorrect = optText === answer;
    const isSelected = optText === selected;

    if (isCorrect) {
      btn.classList.add(isSelected ? "state-correct" : "state-missed");
    } else if (isSelected) {
      btn.classList.add("state-wrong");
    }

    container.appendChild(btn);
  });

  if (banner && selected !== "") {
    const correct = selected === answer;
    banner.textContent = correct ? "Correct" : "Wrong";
    banner.className = "m3-check-banner visible " + (correct ? "correct" : "wrong");
  }
};
