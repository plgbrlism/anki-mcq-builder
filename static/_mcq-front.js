window.initM3Front = function (choicesList, correctAnswer, shadowRoot) {
  window.__m3Cache = undefined;
  var LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I"];
  var root = shadowRoot || document;
  var container = root.querySelector(".m3-options-group");
  var showBtn = root.querySelector("#m3-show-answer");
  var banner = root.querySelector("#m3-check-banner");
  if (!container) return;

  var indices = choicesList.map(function (_, i) { return i; });
  for (var i = indices.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = indices[i];
    indices[i] = indices[j];
    indices[j] = tmp;
  }
  var shuffled = indices.map(function (i) { return choicesList[i]; });

  var selectedText = "";

  container.innerHTML = "";
  shuffled.forEach(function (text, idx) {
    var btn = document.createElement("div");
    btn.className = "m3-option-item";
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");
    btn.tabIndex = 0;

    var pill = document.createElement("span");
    pill.className = "m3-option-pill";
    pill.textContent = LETTERS[idx] || (idx + 1);

    var content = document.createElement("span");
    content.className = "m3-option-content";
    content.textContent = text;

    btn.appendChild(pill);
    btn.appendChild(content);
    btn.addEventListener("click", function () {
      container.querySelectorAll(".m3-option-item").forEach(function (el) {
        el.classList.remove("selected");
        el.setAttribute("aria-checked", "false");
      });
      btn.classList.add("selected");
      btn.setAttribute("aria-checked", "true");
      selectedText = text;
      window.name = "m3:" + indices.join(",") + ":" + text;
      if (showBtn) showBtn.classList.add("visible");
    });
    container.appendChild(btn);
  });

  // Show Answer — evaluate inline, no pycmd flip
  if (showBtn) {
    showBtn.addEventListener("click", function () {
      if (!selectedText) return;

      // Read correct answer from hidden field
      var answerEl = document.getElementById("raw-answer");
      var answer = answerEl ? answerEl.textContent.trim() : "";
      var correct = selectedText === answer;

      // Disable further clicks
      container.querySelectorAll(".m3-option-item").forEach(function (el) {
        el.setAttribute("aria-disabled", "true");
        el.style.pointerEvents = "none";
      });

      // Apply states
      container.querySelectorAll(".m3-option-item").forEach(function (el) {
        var optText = el.querySelector(".m3-option-content").textContent;
        var isCorrect = optText === answer;
        var isSelected = optText === selectedText;

        if (isCorrect) {
          el.classList.add(isSelected ? "state-correct" : "state-missed");
        } else if (isSelected) {
          el.classList.add("state-wrong");
        }
        el.classList.remove("selected");
      });

      // Show banner
      if (banner) {
        banner.textContent = correct ? "Correct" : "Wrong";
        banner.className = "m3-check-banner visible " + (correct ? "correct" : "wrong");
      }

      // Hide Show Answer button
      showBtn.classList.remove("visible");
    });
    showBtn.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        showBtn.click();
      }
    });
  }

  // Arrow-key navigation (desktop only)
  if (!/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) {
    var items = Array.prototype.slice.call(
      container.querySelectorAll(".m3-option-item")
    );
    items.forEach(function (el, idx) {
      el.tabIndex = idx === 0 ? 0 : -1;
    });
    container.addEventListener("keydown", function (e) {
      var activeEl = shadowRoot ? shadowRoot.activeElement : document.activeElement;
      var i = items.indexOf(activeEl);
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        items[(i + 1) % items.length] &&
          items[(i + 1) % items.length].focus();
        e.preventDefault();
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        items[(i - 1 + items.length) % items.length] &&
          items[(i - 1 + items.length) % items.length].focus();
        e.preventDefault();
      }
    });
  }
};
