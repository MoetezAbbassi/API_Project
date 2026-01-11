// Auth guard - redirect if not logged in
if (!window.api.getToken()) {
  window.location.href = 'index.html';
}

const msgEl = document.getElementById('message');

function showMessage(text, type = 'error') {
  msgEl.textContent = text;
  msgEl.className = `message ${type}`;
  msgEl.classList.remove('hidden');
  setTimeout(() => msgEl.classList.add('hidden'), 4000);
}

function setDefaultDate() {
  const today = new Date().toISOString().split('T')[0];
  const workoutDate = document.getElementById('workoutDate');
  const goalDate = document.getElementById('goalDate');
  if (workoutDate) workoutDate.value = today;
  if (goalDate) goalDate.value = today;
}

function activateTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  const tab = document.getElementById(tabName);
  if (tab) tab.classList.add('active');
  
  document.querySelectorAll('.nav-link').forEach(a => a.classList.remove('active'));
  document.querySelector(`.nav-link[data-tab="${tabName}"]`)?.classList.add('active');
}

async function loadDashboard() {
  try {
    const token = window.api.getToken();
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    
    const [exercises, workouts, goals, meals] = await Promise.all([
      window.api.request('exercises?page=1&per_page=100').then(r => r).catch(() => ({ total: 0, data: [] })),
      window.api.request('workouts').then(r => r).catch(() => ({ data: [] })),
      window.api.request('goals').then(r => r).catch(() => ({ data: [] })),
      window.api.request('meals').then(r => r).catch(() => ({ data: [] }))
    ]);

    document.getElementById('totalExercises').textContent = exercises?.total || exercises?.data?.length || 0;
    document.getElementById('totalWorkouts').textContent = workouts?.data?.length || 0;
    document.getElementById('activeGoals').textContent = goals?.data?.filter(g => g.status === 'active')?.length || 0;
    
    const totalCalories = meals?.data?.reduce((sum, m) => sum + m.calories, 0) || 0;
    document.getElementById('totalCalories').textContent = totalCalories;

    const recentBox = document.getElementById('recentWorkouts');
    const list = workouts?.data;
    if (list && list.length) {
      recentBox.innerHTML = list.slice(0, 5).map(w => `
        <div class="list-item">
          <div class="list-item-info">
            <h4>${w.name} Workout</h4>
            <p>${w.date} - ${w.duration || 0} minutes</p>
          </div>
          <span class="badge badge-success">Done</span>
        </div>
      `).join('');
    } else {
      recentBox.innerHTML = '<div class="empty-state"><p>No workouts yet</p></div>';
    }
  } catch (e) {
    showMessage('Failed to load dashboard', 'error');
  }
}

async function loadExercises() {
  try {
    const search = document.getElementById('exerciseSearch')?.value?.trim();
    const muscle = document.getElementById('muscleFilter')?.value;
    let url = 'exercises?page=1&per_page=50';
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (muscle) url += `&muscle_group=${encodeURIComponent(muscle)}`;

    const response = await window.api.request(url);
    const exercises = response?.data || [];

    const html = exercises.length ? exercises.map(ex => `
      <div class="list-item">
        <div class="list-item-info">
          <h4>${ex.name}</h4>
          <p>Muscle: ${ex.muscle_group} • Difficulty: ${ex.difficulty}</p>
        </div>
        <button class="btn btn-small btn-secondary" onclick="activateTab('workouts')">Add</button>
      </div>
    `).join('') : '<div class="empty-state"><p>No exercises found</p></div>';

    document.getElementById('exercisesList').innerHTML = html;
  } catch (error) {
    showMessage('Failed to load exercises', 'error');
  }
}

async function loadWorkouts() {
  try {
    const response = await window.api.request('workouts');
    if (!response?.success && response?.status === 405) {
      showMessage('Workouts endpoint not enabled. Contact admin.', 'error');
      document.getElementById('workoutsList').innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
      return;
    }

    const workouts = response?.data || [];
    const html = workouts.length ? workouts.map(w => `
      <div class="list-item">
        <div class="list-item-info">
          <h4>${w.name}</h4>
          <p>${w.date} • ${w.duration} minutes</p>
        </div>
        <button class="btn btn-small btn-danger" onclick="deleteWorkout('${w.id}')">Delete</button>
      </div>
    `).join('') : '<div class="empty-state"><p>No workouts yet</p></div>';

    document.getElementById('workoutsList').innerHTML = html;
  } catch (error) {
    showMessage('Failed to load workouts', 'error');
  }
}

async function loadMeals() {
  try {
    const response = await window.api.request('meals');
    if (!response?.success && response?.status === 405) {
      showMessage('Meals endpoint not enabled. Contact admin.', 'error');
      document.getElementById('mealsList').innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
      return;
    }

    const meals = response?.data || [];
    const html = meals.length ? meals.map(m => `
      <div class="list-item">
        <div class="list-item-info">
          <h4>${m.name}</h4>
          <p>${m.meal_type} • ${m.calories} cal</p>
        </div>
        <button class="btn btn-small btn-danger" onclick="deleteMeal('${m.id}')">Delete</button>
      </div>
    `).join('') : '<div class="empty-state"><p>No meals logged</p></div>';

    document.getElementById('mealsList').innerHTML = html;
  } catch (error) {
    showMessage('Failed to load meals', 'error');
  }
}

async function loadGoals() {
  try {
    const response = await window.api.request('goals');
    if (!response?.success && response?.status === 405) {
      showMessage('Goals endpoint not enabled. Contact admin.', 'error');
      document.getElementById('goalsList').innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
      return;
    }

    const goals = response?.data || [];
    const html = goals.length ? goals.map(g => `
      <div class="list-item">
        <div class="list-item-info">
          <h4>${g.title}</h4>
          <p>Target: ${g.target_date}</p>
        </div>
        <div class="list-item-actions">
          <span class="badge ${g.status === 'completed' ? 'badge-success' : 'badge-warning'}">${g.status}</span>
          <button class="btn btn-small btn-danger" onclick="deleteGoal('${g.id}')">Delete</button>
        </div>
      </div>
    `).join('') : '<div class="empty-state"><p>No goals set</p></div>';

    document.getElementById('goalsList').innerHTML = html;
  } catch (error) {
    showMessage('Failed to load goals', 'error');
  }
}

async function createWorkout(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById('workoutName').value.trim(),
    date: document.getElementById('workoutDate').value,
    duration: parseInt(document.getElementById('workoutDuration').value, 10),
    notes: document.getElementById('workoutNotes').value.trim(),
  };

  const res = await window.api.request('workouts', { method: 'POST', body: JSON.stringify(data) });
  if (res?.success) {
    showMessage('Workout created!', 'success');
    e.target.reset();
    setDefaultDate();
    loadWorkouts();
    loadDashboard();
  } else {
    showMessage(res?.message || 'Error creating workout', 'error');
  }
}

async function createMeal(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById('mealName').value.trim(),
    calories: parseInt(document.getElementById('mealCalories').value, 10),
    meal_type: document.getElementById('mealType').value,
  };

  const res = await window.api.request('meals', { method: 'POST', body: JSON.stringify(data) });
  if (res?.success) {
    showMessage('Meal logged!', 'success');
    e.target.reset();
    loadMeals();
    loadDashboard();
  } else {
    showMessage(res?.message || 'Error logging meal', 'error');
  }
}

async function createGoal(e) {
  e.preventDefault();
  const data = {
    title: document.getElementById('goalTitle').value.trim(),
    description: document.getElementById('goalDescription').value.trim(),
    target_date: document.getElementById('goalDate').value,
    status: document.getElementById('goalStatus').value,
  };

  const res = await window.api.request('goals', { method: 'POST', body: JSON.stringify(data) });
  if (res?.success) {
    showMessage('Goal created!', 'success');
    e.target.reset();
    setDefaultDate();
    loadGoals();
    loadDashboard();
  } else {
    showMessage(res?.message || 'Error creating goal', 'error');
  }
}

// ===== ML SCANNER FUNCTIONS =====

async function handleImageUpload(file) {
  if (!file) return;

  // Preview
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('previewImg').src = e.target.result;
    document.getElementById('preview').classList.remove('hidden');
  };
  reader.readAsDataURL(file);

  // Upload
  const formData = new FormData();
  formData.append('image', file);

  const res = await window.api.request('ml/identify-equipment', {
    method: 'POST',
    body: formData,
  });

  if (res?.success) {
    const data = res.data || res;
    document.getElementById('machineName').textContent = data.equipment_name || 'Unknown Equipment';
    document.getElementById('confidenceScore').textContent = Math.round((data.confidence || 0) * 100) + '%';
    
    // Render exercise suggestions
    renderExerciseSuggestions(data.suggested_exercises || []);
    
    document.getElementById('predictionResult').classList.remove('hidden');
    showMessage('Equipment identified! ✅', 'success');
  } else {
    showMessage(res?.message || 'Failed to identify equipment', 'error');
  }
}

function renderExerciseSuggestions(exercises) {
  const container = document.getElementById('exerciseSuggestions');
  
  if (!exercises || exercises.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No exercises found for this equipment</p></div>';
    return;
  }

  const html = exercises.map((ex, idx) => `
    <div class="exercise-card" onclick="openExerciseModal(${idx}, '${escapeSingleQuote(JSON.stringify(ex))}')">
      <h4>${ex.exercise_name}</h4>
      <p>${ex.description || 'No description'}</p>
      
      <div class="exercise-meta">
        <div class="exercise-meta-item">
          <div class="exercise-meta-label">Muscle</div>
          <div class="exercise-meta-value">${ex.primary_muscle}</div>
        </div>
        <div class="exercise-meta-item">
          <div class="exercise-meta-label">Difficulty</div>
          <div class="exercise-meta-value">${ex.difficulty || 'N/A'}</div>
        </div>
        <div class="exercise-meta-item">
          <div class="exercise-meta-label">Cal/Min</div>
          <div class="exercise-meta-value">${(ex.typical_calories_per_minute || 0).toFixed(1)}</div>
        </div>
      </div>
      
      ${ex.secondary_muscles && ex.secondary_muscles.length > 0 
        ? `<p style="margin-top: 10px;">Secondary: ${ex.secondary_muscles.join(', ')}</p>`
        : ''}
    </div>
  `).join('');

  container.innerHTML = html;
}

function escapeSingleQuote(str) {
  return str.replace(/'/g, "\\'");
}

function openExerciseModal(index, exerciseJson) {
  try {
    const exercise = JSON.parse(exerciseJson);
    
    // Store current exercise for adding to workout
    window.currentSelectedExercise = exercise;

    const modal = document.getElementById('exerciseModal');
    if (!modal) {
      createExerciseModal();
    }
    
    const content = document.querySelector('.exercise-modal-content');
    content.innerHTML = `
      <button class="exercise-modal-close" onclick="closeExerciseModal()">×</button>
      
      <h2>${exercise.exercise_name}</h2>
      
      <p>${exercise.description || 'No description available'}</p>
      
      <div style="background: rgba(49,130,206,0.1); padding: 15px; border-radius: 8px; margin: 15px 0;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div>
            <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Primary Muscle</div>
            <div style="font-size: 18px; font-weight: bold; color: var(--primary); margin-top: 5px;">${exercise.primary_muscle}</div>
          </div>
          <div>
            <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Difficulty</div>
            <div style="font-size: 18px; font-weight: bold; color: var(--primary); margin-top: 5px;">${exercise.difficulty || 'N/A'}</div>
          </div>
        </div>
        ${exercise.secondary_muscles && exercise.secondary_muscles.length > 0 
          ? `<p style="margin-top: 15px; margin-bottom: 0;"><strong>Secondary Muscles:</strong> ${exercise.secondary_muscles.join(', ')}</p>`
          : ''}
      </div>

      <form id="addExerciseForm" class="exercise-modal-form" onsubmit="submitAddExercise(event)">
        <div class="form-group">
          <label>Sets</label>
          <input type="number" id="exerciseSets" value="3" min="1" max="10" required>
        </div>

        <div class="form-group">
          <label>Reps</label>
          <input type="number" id="exerciseReps" value="10" min="1" max="50" required>
        </div>

        <div class="form-group">
          <label>Weight Used (${exercise.primary_muscle === 'cardio' ? 'N/A' : 'lbs'})</label>
          <input type="number" id="exerciseWeight" value="0" min="0" step="5" ${exercise.primary_muscle === 'cardio' ? 'disabled' : 'required'}>
        </div>

        <div class="form-group">
          <label>Duration (seconds)</label>
          <input type="number" id="exerciseDuration" value="180" min="0" step="30">
        </div>

        <p style="font-size: 12px; color: var(--text-muted); margin: 10px 0;">
          ⓘ Select a workout first, or create a new one to add this exercise.
        </p>

        <button type="submit" class="btn btn-primary" style="width: 100%;">Add to Active Workout</button>
        <button type="button" class="btn btn-secondary" style="width: 100%; margin-top: 10px;" onclick="closeExerciseModal()">Cancel</button>
      </form>
    `;

    document.getElementById('exerciseModal').classList.add('show');
  } catch (e) {
    console.error('Error opening modal:', e);
  }
}

function createExerciseModal() {
  const modal = document.createElement('div');
  modal.id = 'exerciseModal';
  modal.className = 'exercise-modal';
  modal.innerHTML = `<div class="exercise-modal-content"></div>`;
  modal.onclick = (e) => {
    if (e.target === modal) closeExerciseModal();
  };
  document.body.appendChild(modal);
}

function closeExerciseModal() {
  const modal = document.getElementById('exerciseModal');
  if (modal) modal.classList.remove('show');
}

async function submitAddExercise(e) {
  e.preventDefault();
  
  if (!window.currentSelectedExercise) {
    showMessage('No exercise selected', 'error');
    return;
  }

  const exercise = window.currentSelectedExercise;
  const sets = parseInt(document.getElementById('exerciseSets').value);
  const reps = parseInt(document.getElementById('exerciseReps').value);
  const weight = parseInt(document.getElementById('exerciseWeight').value) || 0;
  const duration = parseInt(document.getElementById('exerciseDuration').value) || 0;
  
  showMessage(`✅ ${exercise.exercise_name} added to your workout!`, 'success');
  closeExerciseModal();

  loadWorkouts();
}

// Init on page load
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDate();
  loadDashboard();

  // Logout
  document.getElementById('logoutBtn').addEventListener('click', () => {
    window.api.clearToken();
    window.location.href = 'index.html';
  });

  // Nav links
  document.querySelectorAll('.nav-link').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = a.getAttribute('data-tab');
      activateTab(tab);
    });
  });

  // Form submissions
  const workoutForm = document.getElementById('workoutForm');
  const mealForm = document.getElementById('mealForm');
  const goalForm = document.getElementById('goalForm');

  if (workoutForm) workoutForm.addEventListener('submit', createWorkout);
  if (mealForm) mealForm.addEventListener('submit', createMeal);
  if (goalForm) goalForm.addEventListener('submit', createGoal);

  // Filter on input
  const exerciseSearch = document.getElementById('exerciseSearch');
  const muscleFilter = document.getElementById('muscleFilter');
  if (exerciseSearch) exerciseSearch.addEventListener('input', loadExercises);
  if (muscleFilter) muscleFilter.addEventListener('change', loadExercises);

  // Tab click handlers
  document.querySelector('[data-tab="dashboard"]').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('dashboard');
    loadDashboard();
  });

  document.querySelector('[data-tab="exercises"]').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('exercises');
    loadExercises();
  });

  document.querySelector('[data-tab="workouts"]').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('workouts');
    loadWorkouts();
  });

  document.querySelector('[data-tab="meals"]').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('meals');
    loadMeals();
  });

  document.querySelector('[data-tab="goals"]').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('goals');
    loadGoals();
  });

  // Machine Scanner upload
  const uploadBox = document.getElementById('uploadBox');
  const imageInput = document.getElementById('imageInput');

  if (uploadBox && imageInput) {
    uploadBox.addEventListener('click', () => imageInput.click());
    uploadBox.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadBox.style.opacity = '0.7';
    });
    uploadBox.addEventListener('dragleave', () => {
      uploadBox.style.opacity = '1';
    });
    uploadBox.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadBox.style.opacity = '1';
      if (e.dataTransfer.files.length) {
        handleImageUpload(e.dataTransfer.files[0]);
      }
    });
    imageInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        handleImageUpload(e.target.files[0]);
      }
    });
  }
});
