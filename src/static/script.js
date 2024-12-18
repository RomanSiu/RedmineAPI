document.getElementById('searchForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  // Збираємо дані форми
  const contractNumber = document.getElementById('contractNumber').value.trim();
  const projectStage = document.getElementById('projectStage').value.trim();
  const timeFrom = document.getElementById('timeFrom').value.trim();
  const timeTo = document.getElementById('timeTo').value.trim();

  // Формуємо URL з параметрами
  const queryParams = new URLSearchParams();

  if (contractNumber) queryParams.append('contract_number', contractNumber);
  if (projectStage) queryParams.append('project_stage', projectStage);
  if (timeFrom) queryParams.append('time_from', timeFrom);
  if (timeTo) queryParams.append('time_to', timeTo);

  const url = `http://127.0.0.1:8000/api/redmine/burned_hours?${queryParams.toString()}`;

  // Ховаємо таблицю перед новим запитом
  document.getElementById('resultsSection').classList.add('hidden');
  document.getElementById('downloadExcel').style.display = 'none';

  try {
    // Виконуємо GET-запит
    const response = await fetch(url, {
      method: 'GET'
    });

    if (!response.ok) throw new Error('Помилка отримання даних.');

    const data = await response.json(); // Очікуємо словник {ім'я: години}

    // Очищуємо таблицю
    const tableBody = document.querySelector('#resultsTable tbody');
    tableBody.innerHTML = '';

    // Перевіряємо, чи є результати
    const keys = Object.keys(data); // Отримуємо імена співробітників
    if (keys.length > 0) {
      // Заповнюємо таблицю
      keys.forEach(name => {
        const newRow = document.createElement('tr');
        newRow.innerHTML = `<td>${name}</td><td>${data[name]}</td>`;
        tableBody.appendChild(newRow);
      });

      // Відображаємо таблицю та кнопку для завантаження Excel
      document.getElementById('resultsSection').classList.remove('hidden');
      document.getElementById('downloadExcel').style.display = 'block';
    } else {
      alert('Результатів не знайдено.');
    }

  } catch (error) {
    alert('Сталася помилка: ' + error.message);
  }
});

// Завантаження Excel
document.getElementById('downloadExcel').addEventListener('click', function () {
  window.location.href = 'http://127.0.0.1:8000/api/download_excel';
});
