const noteEl = document.getElementById("note");
const runBtn = document.getElementById("run");
const runLabel = runBtn.querySelector(".run-btn__label");
const runSpinner = runBtn.querySelector(".run-btn__spinner");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const resultModeEl = document.getElementById("result-mode");
const historyListEl = document.getElementById("history-list");
const modeTabs = document.querySelectorAll(".mode-tab");

let currentMode = "short";
const modeNames = { short: "สรุปสั้น", bullet: "Bullet", simple: "อธิบายง่าย" };

modeTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    modeTabs.forEach((t) => t.classList.remove("is-active"));
    tab.classList.add("is-active");
    currentMode = tab.dataset.mode;
  });
});

function setLoading(isLoading) {
  runBtn.disabled = isLoading;
  runSpinner.hidden = !isLoading;
  runLabel.textContent = isLoading ? "กำลังสรุป..." : "สรุปเลย";
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function prependHistory(record) {
  const empty = historyListEl.querySelector(".history-empty");
  if (empty) empty.remove();

  const item = document.createElement("article");
  item.className = "history-item";
  item.innerHTML = `
    <div class="history-item__meta">
      <span class="history-item__mode">${record.mode}</span>
      <span class="history-item__date">${record.date}</span>
    </div>
    <p class="history-item__text">${record.summary}</p>
  `;
  historyListEl.prepend(item);
}

async function runSummarize() {
  const text = noteEl.value.trim();
  clearError();

  if (!text) {
    showError("ยังไม่ได้กรอกเนื้อหา");
    return;
  }

  setLoading(true);
  resultModeEl.textContent = "";

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mode: currentMode }),
    });
    const data = await response.json();

    if (!data.ok) {
      showError(data.error || "เกิดข้อผิดพลาด ลองใหม่อีกครั้ง");
      return;
    }

    resultEl.innerHTML = `<p class="result__text"></p>`;
    resultEl.querySelector(".result__text").textContent = data.summary;
    resultModeEl.textContent = modeNames[currentMode] || currentMode;
    prependHistory(data.record);
  } catch (err) {
    showError("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ ตรวจสอบว่า app.py รันอยู่");
  } finally {
    setLoading(false);
  }
}

runBtn.addEventListener("click", runSummarize);
