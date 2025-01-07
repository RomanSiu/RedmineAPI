document.getElementById('searchForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  document.getElementById('resultsSection').classList.add('hidden');

  // Збираємо дані форми
  const contractNum = document.getElementById('contractNum').value.trim();
  const projectStage = document.getElementById('projectStage').value.trim();
  const timeFrom = document.getElementById('timeFrom').value.trim();
  const timeTo = document.getElementById('timeTo').value.trim();

  // Формуємо URL з параметрами
  const queryParams = new URLSearchParams();

  if (contractNum) queryParams.append('contract_num', contractNum);
  if (projectStage) queryParams.append('project_stage', projectStage);
  if (timeFrom) queryParams.append('time_from', timeFrom);
  if (timeTo) queryParams.append('time_to', timeTo);

  const url = `http://172.16.2.13:8000/api/redmine/issues_info?${queryParams.toString()}`;

  try {
    // Виконуємо GET-запит
    const response = await fetch(url, {
      method: 'GET'
    });

    if (!response.ok) throw new Error('Помилка отримання даних.');

    const data = await response.json();

    // Перевіряємо, чи є результати
    if (Object.keys(data).length > 0) {
      alert('Дані успішно отримані. Ви можете завантажити їх у вигляді Excel.');
    } else {
      alert('Результатів не знайдено.');
    }

    // Відображаємо кнопку для завантаження Excel
    document.getElementById('resultsSection').classList.remove('hidden');

  } catch (error) {
    alert('Сталася помилка: ' + error.message);
  }
});

// Завантаження Excel
document.getElementById('downloadExcel').addEventListener('click', function () {
  window.location.href = 'http://172.16.2.13:8000/api/redmine/download_excel';
});
