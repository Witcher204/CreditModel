const form = document.getElementById('loan-form');
const resultBox = document.getElementById('result');
const resultText = document.getElementById('result-text');

function renderPrediction(prediction) {
  resultBox.classList.remove('hidden', 'success', 'danger');

  if (prediction === 1) {
    resultBox.classList.add('danger');
    resultText.textContent = 'Результат: дефолт вероятен (1)';
    return;
  }

  resultBox.classList.add('success');
  resultText.textContent = 'Результат: дефолт маловероятен (0)';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  Object.keys(payload).forEach((key) => {
    payload[key] = Number(payload[key]);
  });

  resultBox.classList.add('hidden');

  try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Ошибка предсказания');
    }

    renderPrediction(Number(data.prediction));
    resultBox.classList.remove('hidden');
  } catch (error) {
    resultBox.classList.remove('hidden', 'success', 'danger');
    resultBox.classList.add('danger');
    resultText.textContent = error.message || 'Не удалось получить прогноз';
  }
});
