window.initM3Front = function(choicesList) {
  const LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"];
  const container = document.getElementById("m3-options-container");
  if (!container) return;

  const indices = choicesList.map((_, i) => i);
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }
  const shuffled = indices.map(i => choicesList[i]);

  window.name = JSON.stringify({ perm: indices, selected: "" });

  container.innerHTML = "";
  shuffled.forEach((text, idx) => {
    const btn = document.createElement("button");
    btn.className = "m3-option-item";
    btn.type = "button";
    btn.innerHTML = `<span class="m3-option-pill">${LETTERS[idx] || (idx + 1)}</span>` +
                    `<span class="m3-option-content">${text}</span>`;
    
    btn.onclick = () => {
      container.querySelectorAll(".m3-option-item").forEach(el => el.classList.remove("selected"));
      btn.classList.add("selected");
      window.name = JSON.stringify({ perm: indices, selected: text });
    };

    container.appendChild(btn);
  });
};
