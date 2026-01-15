/**
 * Main Application Module - Handles all app functionality
 */
const App = {
  // State
  currentTab: 'dashboard',
  user: null,
  caloriesChart: null,
  
  // Initialize
  init() {
    console.log('App.init() called');
    console.log('localStorage token:', localStorage.getItem('token') ? 'present' : 'missing');
    console.log('localStorage user:', localStorage.getItem('user'));
    
    this.checkAuth();
    this.user = API.getUser();
    
    // Verify we have valid user data, not just a token
    if (!this.user || !this.user.user_id) {
      console.error('No valid user data found, user:', this.user);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = 'index.html';
      return;
    }
    
    console.log('App initialized with user:', this.user.user_id, 'username:', this.user.username);
    
    this.bindEvents();
    this.showTab('dashboard');
    this.updateUserInfo();
  },
  
  // Check authentication
  checkAuth() {
    const token = localStorage.getItem('token');
    console.log('checkAuth - token exists:', !!token);
    if (!token) {
      console.log('No token, redirecting to login');
      window.location.href = 'index.html';
    }
  },
  
  // Update user info in sidebar
  updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    if (userInfo && this.user) {
      userInfo.textContent = `Welcome, ${this.user.username}`;
    }
  },
  
  // Bind event listeners
  bindEvents() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = e.currentTarget.dataset.tab;
        console.log('Nav link clicked, tab:', tab);
        this.showTab(tab);
      });
    });
    
    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', () => this.logout());
    
    // Dashboard period select
    document.getElementById('chartPeriod')?.addEventListener('change', (e) => {
      this.loadCaloriesChart(parseInt(e.target.value));
    });
    
    // Workout form
    document.getElementById('createWorkoutForm')?.addEventListener('submit', (e) => this.handleCreateWorkout(e));
    
    // Exercise form
    document.getElementById('createExerciseForm')?.addEventListener('submit', (e) => this.handleCreateExercise(e));
    
    // Exercise filters
    document.getElementById('muscleFilter')?.addEventListener('change', () => this.loadExercises());
    document.getElementById('difficultyFilter')?.addEventListener('change', () => this.loadExercises());
    document.getElementById('exerciseSearch')?.addEventListener('input', this.debounce(() => this.loadExercises(), 300));
    
    // ML Scanner
    this.setupMLScanner();
    
    // Goal form
    document.getElementById('createGoalForm')?.addEventListener('submit', (e) => this.handleCreateGoal(e));
    
    // Add to workout form
    document.getElementById('addToWorkoutForm')?.addEventListener('submit', (e) => this.handleAddToWorkout(e));
    
    // Profile forms
    document.getElementById('profileForm')?.addEventListener('submit', (e) => this.handleUpdateProfile(e));
    document.getElementById('passwordForm')?.addEventListener('submit', (e) => this.handleChangePassword(e));
    
    // Modal close
    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', () => this.closeModals());
    });
    
    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeModals();
      });
    });
    
    // Add to workout form in modal
    document.getElementById('addToWorkoutModalForm')?.addEventListener('submit', (e) => this.handleAddToWorkout(e));
  },
  
  // Show tab
  showTab(tab) {
    this.currentTab = tab;
    
    // Update nav
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.dataset.tab === tab);
    });
    
    // Update content - remove active from all, add to selected one
    document.querySelectorAll('.tab-content').forEach(content => {
      if (content.id === tab) {
        content.classList.add('active');
        content.classList.remove('hidden');
      } else {
        content.classList.remove('active');
        content.classList.add('hidden');
      }
    });
    
    // Load tab data
    this.loadTabData(tab);
  },
  
  // Load tab data
  loadTabData(tab) {
    switch (tab) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'workouts':
        this.loadWorkouts();
        break;
      case 'exercises':
        this.loadExercises();
        this.loadMuscleGroups();
        break;
      case 'ml':
        this.loadEquipmentList();
        break;
      case 'meals':
        this.loadMeals();
        this.loadNutritionSummary();
        break;
      case 'profile':
        this.loadProfile();
        break;
    }
  },
  
  // ===== DASHBOARD =====
  async viewWorkoutDetails(workoutId) {
    try {
      const data = await API.workouts.get(workoutId);
      const workout = data.data || data;
      
      document.getElementById('workoutDetailName').textContent = workout.name || workout.workout_type || 'Workout';
      document.getElementById('workoutDetailType').textContent = `Type: ${workout.workout_type || 'unknown'}`;
      document.getElementById('workoutDetailDate').textContent = `Date: ${this.formatDate(workout.workout_date)}`;
      
      const statusBadge = document.getElementById('workoutDetailStatus');
      statusBadge.textContent = workout.status || 'pending';
      statusBadge.className = `badge ${workout.status === 'completed' ? 'badge-success' : 'badge-warning'}`;
      
      const exercisesContainer = document.getElementById('workoutDetailExercises');
      const exercises = workout.exercises || [];
      
      if (exercises.length === 0) {
        exercisesContainer.innerHTML = '<div class="empty-state"><p>No exercises in this workout</p></div>';
      } else {
        exercisesContainer.innerHTML = exercises.map(ex => `
          <div style="border: 1px solid var(--border); padding: 1rem; margin-bottom: 1rem; border-radius: var(--radius-sm);">
            <h5>${ex.exercise?.name || ex.exercise_name || 'Unknown Exercise'}</h5>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem;">
              <div>
                <span style="color: var(--text-secondary); font-size: 0.9rem;">Sets × Reps</span>
                <p style="font-weight: bold;">${ex.sets} × ${ex.reps}</p>
              </div>
              <div>
                <span style="color: var(--text-secondary); font-size: 0.9rem;">Weight</span>
                <p style="font-weight: bold;">${ex.weight_used || 0} ${ex.weight_unit || 'kg'}</p>
              </div>
              <div>
                <span style="color: var(--text-secondary); font-size: 0.9rem;">Calories</span>
                <p style="font-weight: bold;">${(ex.calories_burned || 0).toFixed(1)}</p>
              </div>
            </div>
          </div>
        `).join('');
      }
      
      document.getElementById('workoutDetailsModal').classList.remove('hidden');
    } catch (error) {
      console.error('Error loading workout details:', error);
      this.showMessage('Failed to load workout details', 'error');
    }
  },

  async loadDashboard() {
    console.log('=== loadDashboard called ===');
    if (!this.user) {
      console.error('❌ No user found in loadDashboard');
      return;
    }
    
    try {
      console.log('📊 Loading dashboard for user:', this.user.user_id);
      
      // Load summary stats
      const summaryResponse = await API.dashboard.getSummary(this.user.user_id);
      console.log('📥 Summary response:', summaryResponse);
      
      const summary = summaryResponse.data || summaryResponse;
      console.log('📊 Extracted summary data:', summary);
      
      // Update total workouts
      console.log('🔍 Looking for totalWorkouts element...');
      document.getElementById('totalWorkouts').textContent = String(summary.total_workouts || 0);
      console.log('✅ Set totalWorkouts to:', summary.total_workouts);
      
      // Update calories burned with average
      console.log('🔍 Looking for totalCaloriesBurned element...');
      const caloriesBurned = Math.round(summary.total_calories_burned || 0);
      const avgPerWorkout = summary.total_workouts > 0 
        ? Math.round(caloriesBurned / summary.total_workouts) 
        : 0;
      
      const caloriesEl = document.getElementById('totalCaloriesBurned');
      caloriesEl.textContent = String(caloriesBurned);
      
      // Create average text
      const labelEl = caloriesEl.nextElementSibling;
      if (labelEl) {
        labelEl.innerHTML = `Calories Burned<br><small style="font-size: 0.7rem; color: var(--text-muted);">${avgPerWorkout} avg/workout</small>`;
      }
      console.log('✅ Set calories burned to:', caloriesBurned, 'avg:', avgPerWorkout);
      
      // Load calories chart
      console.log('📈 Loading calories chart...');
      this.loadCaloriesChart(7);
      
      // Load weight chart
      console.log('⚖️ Loading weight chart...');
      this.loadDashboardWeightChart();
      
      // Load workout calendar
      console.log('📅 Loading workout calendar...');
      this.loadWorkoutCalendar();
    } catch (error) {
      console.error('❌ Failed to load dashboard:', error);
    }
  },
  
  async loadCaloriesChart(days = 7) {
    if (!this.user) {
      console.error('No user found in loadCaloriesChart');
      return;
    }
    
    try {
      console.log('Loading calories chart for days:', days);
      
      const response = await API.dashboard.getCaloriesGraph(this.user.user_id, days);
      console.log('Chart response:', response);
      
      const data = response.data || response;
      
      console.log('Chart data:', data);
      
      const canvas = document.getElementById('caloriesChart');
      if (!canvas) {
        console.error('caloriesChart canvas not found');
        return;
      }
      
      const ctx = canvas.getContext('2d');
      
      if (this.caloriesChart) {
        this.caloriesChart.destroy();
      }
      
      console.log('Creating chart with labels:', data.labels, 'burned:', data.calories_burned, 'consumed:', data.calories_consumed);
      
      this.caloriesChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.labels || [],
          datasets: [
            {
              label: 'Calories Consumed',
              data: data.calories_consumed || [],
              borderColor: '#e53e3e',
              backgroundColor: 'rgba(229, 62, 62, 0.1)',
              tension: 0.4,
              fill: true,
              borderWidth: 2,
              yAxisID: 'y'
            },
            {
              label: 'Calories Burned',
              data: data.calories_burned || [],
              borderColor: '#38a169',
              backgroundColor: 'rgba(56, 161, 105, 0.1)',
              tension: 0.4,
              fill: true,
              borderWidth: 2,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              labels: { color: '#94a3b8', font: { size: 12 } },
              position: 'top'
            }
          },
          scales: {
            x: {
              ticks: { color: '#64748b' },
              grid: { color: 'rgba(100, 116, 139, 0.2)' },
              title: {
                display: true,
                text: 'Date',
                color: '#94a3b8'
              }
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              ticks: { color: '#e53e3e' },
              grid: { color: 'rgba(100, 116, 139, 0.2)' },
              beginAtZero: true,
              title: {
                display: true,
                text: 'Calories Consumed',
                color: '#e53e3e'
              }
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              ticks: { color: '#38a169' },
              grid: { drawOnChartArea: false },
              beginAtZero: true,
              title: {
                display: true,
                text: 'Calories Burned',
                color: '#38a169'
              }
            }
          }
        }
      });
      console.log('Chart created successfully');
    } catch (error) {
      console.error('Failed to load calories chart:', error);
    }
  },
  
  async loadWorkoutCalendar() {
    const container = document.getElementById('recentWorkouts');
    if (!container) {
      console.error('recentWorkouts container not found');
      return;
    }
    
    try {
      // Fetch all workouts with exercise details
      const response = await API.workouts.getAll(1, 100);
      let workouts = (response.data || response.workouts || []);
      
      console.log('Fetched workouts:', workouts);
      
      // Also fetch meals for calendar display
      try {
        const mealsResponse = await API.meals.getMine(1, 100);
        this.allMeals = mealsResponse.data || mealsResponse.meals || [];
        console.log('Fetched meals for calendar:', this.allMeals);
      } catch (e) {
        console.log('Could not fetch meals for calendar:', e);
        this.allMeals = [];
      }
      
      // Store workouts for month navigation
      this.allWorkouts = workouts;
      
      // Start with current month
      const today = new Date();
      this.currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      
      // Render calendar
      this.renderWorkoutCalendar();
    } catch (error) {
      console.error('Failed to load workout calendar:', error);
      container.innerHTML = '<div class="empty-state"><p>Failed to load workout calendar</p></div>';
    }
  },
  
  renderWorkoutCalendar() {
    const container = document.getElementById('recentWorkouts');
    if (!container) return;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Get workouts for the current month
    const monthStart = this.currentMonth;
    const monthEnd = new Date(monthStart.getFullYear(), monthStart.getMonth() + 1, 1);
    
    const workoutsThisMonth = this.allWorkouts.filter(w => {
      const wDate = new Date(w.workout_date);
      wDate.setHours(0, 0, 0, 0);
      return wDate >= monthStart && wDate < monthEnd;
    });
    
    // Get meals for the current month
    const mealsThisMonth = (this.allMeals || []).filter(m => {
      const mDate = new Date(m.meal_date);
      mDate.setHours(0, 0, 0, 0);
      return mDate >= monthStart && mDate < monthEnd;
    });
    
    // Generate calendar HTML with month navigation
    const calendarHTML = this.generateWorkoutCalendarWithNav(workoutsThisMonth, mealsThisMonth, this.currentMonth);
    container.innerHTML = calendarHTML;
    
    // Attach month navigation listeners
    document.getElementById('prevMonth')?.addEventListener('click', () => {
      this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() - 1, 1);
      this.renderWorkoutCalendar();
    });
    
    document.getElementById('nextMonth')?.addEventListener('click', () => {
      this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 1);
      this.renderWorkoutCalendar();
    });
    
    // Add hover listeners for workout days
    document.querySelectorAll('.calendar-day-with-workout').forEach(day => {
      day.addEventListener('mouseenter', (e) => {
        const workoutId = e.currentTarget.dataset.workoutId;
        const workout = this.allWorkouts.find(w => w.workout_id === workoutId);
        if (workout) {
          console.log('Showing tooltip for workout:', workout);
          this.showWorkoutTooltip(e.currentTarget, workout);
        }
      });
      
      day.addEventListener('mouseleave', (e) => {
        const tooltip = e.currentTarget.querySelector('.workout-tooltip');
        if (tooltip) {
          tooltip.style.display = 'none';
        }
      });
      
      day.addEventListener('click', (e) => {
        const workoutId = e.currentTarget.dataset.workoutId;
        const dateStr = e.currentTarget.dataset.date;
        const workout = this.allWorkouts.find(w => w.workout_id === workoutId);
        this.showDayDetails(dateStr, workout);
      });
    });
    
    // Add click listeners for all calendar days (for meals)
    document.querySelectorAll('.calendar-day[data-date]').forEach(day => {
      day.addEventListener('click', (e) => {
        const dateStr = e.currentTarget.dataset.date;
        this.showDayDetails(dateStr);
      });
    });
  },
  
  // Helper to format date as YYYY-MM-DD in local timezone (avoids UTC conversion issues)
  formatDateLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },
  
  generateWorkoutCalendarWithNav(workouts, meals, monthDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Month navigation
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'];
    
    const currentMonthName = monthNames[monthDate.getMonth()];
    const currentYear = monthDate.getFullYear();
    
    // Calendar generation
    const firstDay = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1).getDay();
    const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
    
    let calendarDays = [];
    
    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      calendarDays.push('<div class="calendar-day calendar-day-empty"></div>');
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(monthDate.getFullYear(), monthDate.getMonth(), day);
      const dateStr = this.formatDateLocal(date);
      
      // Find workout for this date
      const workout = workouts.find(w => {
        const wDate = new Date(w.workout_date);
        wDate.setHours(0, 0, 0, 0);
        return this.formatDateLocal(wDate) === dateStr;
      });
      
      // Find meals for this date
      const dayMeals = meals.filter(m => {
        const mDate = m.meal_date?.split('T')[0] || m.meal_date;
        return mDate === dateStr;
      });
      const hasMeals = dayMeals.length > 0;
      
      let dayClass = 'calendar-day';
      let indicators = '';
      
      // Check if today
      const isToday = this.formatDateLocal(date) === this.formatDateLocal(today);
      
      if (isToday) {
        dayClass += ' calendar-day-today';
      }
      
      // Add workout indicator
      if (workout) {
        if (workout.status === 'completed') {
          dayClass += ' calendar-day-completed';
          indicators += `<span class="workout-indicator" style="background: #38a169;">✓</span>`;
        } else {
          dayClass += ' calendar-day-planned';
          indicators += `<span class="workout-indicator" style="background: #ed8936;">→</span>`;
        }
      }
      
      // Add meal indicator
      if (hasMeals) {
        dayClass += ' calendar-day-with-meals';
        indicators += `<span class="meal-indicator" style="background: #60a5fa;">🍽</span>`;
      }
      
      const dayContent = `${indicators}<span class="day-date">${day}</span>`;
      
      if (workout) {
        const dayHtml = `<div class="${dayClass} calendar-day-with-workout" data-workout-id="${workout.workout_id}" data-date="${dateStr}" title="Click to view">${dayContent}</div>`;
        calendarDays.push(dayHtml);
      } else {
        calendarDays.push(`<div class="${dayClass}" data-date="${dateStr}" title="Click to view">${dayContent}</div>`);
      }
    }
    
    return `
      <div class="workout-calendar">
        <div class="calendar-header">
          <button id="prevMonth" class="calendar-nav-btn" title="Previous month">
            <span>‹</span>
          </button>
          <h3 class="calendar-month-year">${currentMonthName} ${currentYear}</h3>
          <button id="nextMonth" class="calendar-nav-btn" title="Next month">
            <span>›</span>
          </button>
        </div>
        
        <div class="calendar-legend">
          <div class="legend-item">
            <span class="workout-indicator" style="background: #3b82f6;">⊙</span>
            <span>Today</span>
          </div>
          <div class="legend-item">
            <span class="workout-indicator" style="background: #38a169;">✓</span>
            <span>Workout Done</span>
          </div>
          <div class="legend-item">
            <span class="workout-indicator" style="background: #ed8936;">→</span>
            <span>Workout Planned</span>
          </div>
          <div class="legend-item">
            <span class="meal-indicator" style="background: #60a5fa;">🍽</span>
            <span>Meals Logged</span>
          </div>
        </div>
        
        <div class="calendar-weekdays">
          <div class="weekday">Sun</div>
          <div class="weekday">Mon</div>
          <div class="weekday">Tue</div>
          <div class="weekday">Wed</div>
          <div class="weekday">Thu</div>
          <div class="weekday">Fri</div>
          <div class="weekday">Sat</div>
        </div>
        
        <div class="calendar-grid">
          ${calendarDays.join('')}
        </div>
      </div>
    `;
  },
  
  showDayDetails(dateStr, workout = null) {
    // Get meals for this date
    const dayMeals = (this.allMeals || []).filter(m => {
      const mDate = m.meal_date?.split('T')[0] || m.meal_date;
      return mDate === dateStr;
    });
    
    // Get workout for this date
    if (!workout) {
      workout = (this.allWorkouts || []).find(w => {
        const wDate = new Date(w.workout_date);
        return this.formatDateLocal(wDate) === dateStr;
      });
    }
    
    // Format date for display (parse as local date to avoid timezone shift)
    const [year, month, day] = dateStr.split('-').map(Number);
    const localDate = new Date(year, month - 1, day);
    const displayDate = localDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    
    // Build meals HTML
    let mealsHtml = '';
    if (dayMeals.length > 0) {
      mealsHtml = `
        <div class="day-details-section">
          <h4>🍽️ Meals (${dayMeals.length})</h4>
          ${dayMeals.map(meal => {
            const items = meal.items || [];
            const itemsList = items.map(i => i.food_name).join(', ') || 'No items recorded';
            return `
              <div class="day-meal-item">
                <div class="meal-header">
                  <span class="meal-type-badge meal-type-${meal.meal_type}">${this.getMealTypeEmoji(meal.meal_type)} ${meal.meal_type}</span>
                  <span class="meal-calories">${Math.round(meal.total_calories || 0)} cal</span>
                </div>
                <div class="meal-foods">${itemsList}</div>
                <div class="meal-macros-small">
                  P: ${Math.round(meal.protein_g || 0)}g | C: ${Math.round(meal.carbs_g || 0)}g | F: ${Math.round(meal.fats_g || 0)}g
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      mealsHtml = '<div class="day-details-section"><h4>🍽️ Meals</h4><p class="empty-text">No meals logged this day</p></div>';
    }
    
    // Build workout HTML
    let workoutHtml = '';
    if (workout) {
      const exercises = workout.exercises || [];
      workoutHtml = `
        <div class="day-details-section">
          <h4>💪 Workout</h4>
          <div class="day-workout-item">
            <div class="workout-name">${workout.name || workout.notes || 'Workout'}</div>
            <div class="workout-status status-${workout.status}">${workout.status}</div>
            ${exercises.length > 0 ? `<div class="workout-exercises">${exercises.map(e => e.exercise_name || e.name).join(', ')}</div>` : ''}
          </div>
        </div>
      `;
    } else {
      workoutHtml = '<div class="day-details-section"><h4>💪 Workout</h4><p class="empty-text">No workout logged this day</p></div>';
    }
    
    // Calculate day totals for meals
    const totalCals = dayMeals.reduce((sum, m) => sum + (m.total_calories || 0), 0);
    const totalProtein = dayMeals.reduce((sum, m) => sum + (m.protein_g || 0), 0);
    const totalCarbs = dayMeals.reduce((sum, m) => sum + (m.carbs_g || 0), 0);
    const totalFats = dayMeals.reduce((sum, m) => sum + (m.fats_g || 0), 0);
    
    const summaryHtml = dayMeals.length > 0 ? `
      <div class="day-totals">
        <h4>📊 Day Totals</h4>
        <div class="totals-grid">
          <div class="total-item"><span class="total-value">${Math.round(totalCals)}</span><span class="total-label">Calories</span></div>
          <div class="total-item"><span class="total-value">${Math.round(totalProtein)}g</span><span class="total-label">Protein</span></div>
          <div class="total-item"><span class="total-value">${Math.round(totalCarbs)}g</span><span class="total-label">Carbs</span></div>
          <div class="total-item"><span class="total-value">${Math.round(totalFats)}g</span><span class="total-label">Fats</span></div>
        </div>
      </div>
    ` : '';
    
    const html = `
      <div class="day-details-popup" id="dayDetailsPopup">
        <div class="day-details-content">
          <div class="day-details-header">
            <h3>📅 ${displayDate}</h3>
            <button class="btn btn-small btn-secondary" onclick="App.closeDayDetails()">✕</button>
          </div>
          ${summaryHtml}
          ${mealsHtml}
          ${workoutHtml}
        </div>
      </div>
    `;
    
    // Remove existing popup if any
    this.closeDayDetails();
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Close on click outside
    document.getElementById('dayDetailsPopup').addEventListener('click', (e) => {
      if (e.target.id === 'dayDetailsPopup') this.closeDayDetails();
    });
  },
  
  closeDayDetails() {
    const popup = document.getElementById('dayDetailsPopup');
    if (popup) popup.remove();
  },
  
  showWorkoutTooltip(element, workout) {
    // Remove any existing tooltip
    const existingTooltip = element.querySelector('.workout-tooltip');
    if (existingTooltip) {
      existingTooltip.remove();
    }
    
    const tooltip = document.createElement('div');
    tooltip.className = 'workout-tooltip';
    
    const workoutName = workout.name || workout.notes || 'Workout';
    
    tooltip.innerHTML = `
      <div class="tooltip-content">
        <h4>${workoutName}</h4>
      </div>
    `;
    
    element.appendChild(tooltip);
    
    // Position tooltip with edge detection to prevent it from going off-screen
    setTimeout(() => {
      const elementRect = element.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();
      
      // Default position: centered below the day
      let top = elementRect.height + 10;
      let left = (elementRect.width - tooltipRect.width) / 2;
      
      // Check if tooltip goes off the right edge
      if (elementRect.left + left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - elementRect.left - tooltipRect.width - 10;
      }
      
      // Check if tooltip goes off the left edge
      if (elementRect.left + left < 10) {
        left = 10 - elementRect.left;
      }
      
      // Check if tooltip goes off the bottom
      if (elementRect.bottom + top + tooltipRect.height > window.innerHeight - 10) {
        top = -(tooltipRect.height + 10);
      }
      
      tooltip.style.top = top + 'px';
      tooltip.style.left = left + 'px';
      tooltip.style.display = 'block';
    }, 0);
  },
  
  showWorkoutDetails(workout) {
    // Handle exercises - they might be in different formats
    let exercises = [];
    
    if (workout.exercises && Array.isArray(workout.exercises)) {
      exercises = workout.exercises;
    } else if (workout.workout_exercises && Array.isArray(workout.workout_exercises)) {
      exercises = workout.workout_exercises;
    }
    
    // Build exercise list
    const exerciseList = exercises
      .map(e => {
        const exName = e.name || e.exercise_name || e.exercise?.name || 'Unknown Exercise';
        const reps = e.reps || '-';
        const sets = e.sets || '-';
        const weight = e.weight_used ? ` @ ${e.weight_used}${e.weight_unit || 'lbs'}` : '';
        const duration = e.duration_seconds ? ` (${Math.round(e.duration_seconds / 60)}min)` : '';
        return `<li><strong>${exName}</strong><br/>Sets: ${sets} | Reps: ${reps}${weight}${duration}</li>`;
      })
      .join('');
    
    const workoutDate = workout.workout_date ? new Date(workout.workout_date).toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric',
      month: 'long', 
      day: 'numeric' 
    }) : 'No date';
    const workoutName = workout.name || workout.notes || 'Workout';
    const totalCalories = Math.round(workout.total_calories_burned || 0);
    const totalDuration = exercises.reduce((sum, e) => sum + (e.duration_seconds || 0), 0);
    const durationMinutes = Math.round(totalDuration / 60);
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'workout-modal-overlay';
    modal.innerHTML = `
      <div class="workout-modal">
        <div class="modal-header">
          <h2>${workoutName}</h2>
          <button class="modal-close">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="modal-info">
            <div class="info-item">
              <span class="info-label">Date:</span>
              <span class="info-value">${workoutDate}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Duration:</span>
              <span class="info-value">${durationMinutes > 0 ? durationMinutes + ' minutes' : 'Not recorded'}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Calories Burned:</span>
              <span class="info-value" style="color: #f97316; font-weight: bold;">${totalCalories} kcal</span>
            </div>
          </div>
          
          <div class="modal-exercises">
            <h3>Exercises</h3>
            ${exercises.length > 0 ? `<ul class="exercises-list">${exerciseList}</ul>` : '<p class="no-exercises">No exercises recorded</p>'}
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="modal-close-btn">Close</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal handlers
    const closeBtn = modal.querySelector('.modal-close');
    const closeBtnFooter = modal.querySelector('.modal-close-btn');
    
    const closeModal = () => {
      modal.style.animation = 'modalFadeOut 0.3s ease-out forwards';
      setTimeout(() => {
        modal.remove();
      }, 300);
    };
    
    closeBtn.addEventListener('click', closeModal);
    closeBtnFooter.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
    
    // Show modal
    modal.style.animation = 'modalFadeIn 0.3s ease-out';
  },
  
  async loadRecentWorkouts() {
    const container = document.getElementById('recentWorkouts');
    if (!container) return;
    
    try {
      const data = await API.workouts.getAll(1, 10);
      let workouts = (data.data || data.workouts || []);
      
      // Filter to show only completed workouts, sorted by most recent first
      workouts = workouts
        .filter(w => w.status === 'completed')
        .sort((a, b) => new Date(b.workout_date) - new Date(a.workout_date))
        .slice(0, 5);
      
      if (workouts.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No completed workouts yet</p></div>';
        return;
      }
      
      container.innerHTML = workouts.map(w => `
        <div class="list-item" style="cursor: pointer;" onclick="App.viewWorkoutDetails('${w.workout_id}')">
          <div class="list-item-info">
            <h4>${w.name || w.notes || w.workout_type || 'Workout'}</h4>
            <p>Type: ${w.workout_type || 'unknown'}</p>
            <p>${this.formatDate(w.workout_date)} • ${w.exercises?.length || 0} exercises</p>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('loadRecentWorkouts error:', error);
      container.innerHTML = '<div class="empty-state"><p>Failed to load recent workouts</p></div>';
    }
  },
  
  getActivityIcon(type) {
    const icons = {
      workout: '🏋️',
      meal: '🍽️',
      goal: '🎯',
      exercise: '💪'
    };
    return icons[type] || '📌';
  },
  
  // ===== WORKOUTS =====
  async loadWorkouts() {
    const container = document.getElementById('workoutsList');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading workouts...</div>';
    
    try {
      const data = await API.workouts.getAll();
      const workouts = data.data || data.workouts || [];
      
      console.log('Loaded workouts:', workouts);
      
      if (workouts.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No workouts yet. Create your first workout!</p></div>';
        return;
      }
      
      container.innerHTML = workouts.map(w => `
        <div class="list-item" data-id="${w.workout_id}" style="cursor: pointer;" onclick="App.viewWorkoutDetails('${w.workout_id}')">
          <div class="list-item-info">
            <h4>${w.notes || w.workout_type || 'Workout'}</h4>
            <p>Type: ${w.workout_type || 'unknown'}</p>
            <p>${this.formatDate(w.workout_date)} • ${w.exercises?.length || 0} exercises • ${w.total_duration_minutes || 0} min</p>
          </div>
          <div class="list-item-actions">
            <span class="badge ${w.status === 'completed' ? 'badge-success' : 'badge-warning'}">
              ${w.status || 'pending'}
            </span>
            ${w.status !== 'completed' ? `
              <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); App.addExerciseToWorkout('${w.workout_id}')">+ Exercise</button>
              <button class="btn btn-success btn-small" onclick="event.stopPropagation(); App.completeWorkout('${w.workout_id}')">Complete</button>
            ` : ''}
            <button class="btn btn-danger btn-small" onclick="event.stopPropagation(); App.deleteWorkout('${w.workout_id}')">Delete</button>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('loadWorkouts error:', error);
      container.innerHTML = '<div class="empty-state"><p>Failed to load workouts</p></div>';
    }
  },
  
  async handleCreateWorkout(e) {
    e.preventDefault();
    console.log('handleCreateWorkout called');
    
    const workoutName = document.getElementById('workoutName').value.trim();
    const workoutType = document.getElementById('workoutType').value;
    const workoutDate = document.getElementById('workoutDate').value || new Date().toISOString().split('T')[0];
    const notes = document.getElementById('workoutNotes').value.trim();
    
    console.log('Workout form data:', { workoutName, workoutType, workoutDate, notes });
    
    if (!workoutName || !workoutType) {
      this.showMessage('Please fill in workout name and type', 'error');
      return;
    }
    
    try {
      const result = await API.workouts.create({ 
        name: workoutName,
        workout_type: workoutType, 
        workout_date: workoutDate,
        notes 
      });
      console.log('Workout created:', result);
      this.showMessage('Workout created!', 'success');
      e.target.reset();
      this.loadWorkouts();
    } catch (error) {
      console.error('Workout creation error:', error);
      this.showMessage(error.msg || 'Failed to create workout', 'error');
    }
  },
  
  async completeWorkout(workoutId) {
    try {
      await API.workouts.update(workoutId, { status: 'completed' });
      this.showMessage('Workout marked as completed!', 'success');
      this.loadWorkouts();
    } catch (error) {
      this.showMessage(error.msg || 'Failed to complete workout', 'error');
    }
  },

  async addExerciseToWorkout(workoutId) {
    // Store current workout id and show exercises tab
    this.currentWorkoutId = workoutId;
    this.showMessage('Click on an exercise and click "Add to Workout" to add exercises', 'info');
    this.showTab('exercises');
  },
  
  async deleteWorkout(id) {
    if (!confirm('Delete this workout?')) return;
    
    try {
      await API.workouts.delete(id);
      this.showMessage('Workout deleted', 'success');
      this.loadWorkouts();
    } catch (error) {
      this.showMessage(error.msg || 'Failed to delete workout', 'error');
    }
  },
  
  // ===== EXERCISE MANAGEMENT =====
  async handleCreateExercise(e) {
    e.preventDefault();
    
    const name = document.getElementById('newExerciseName').value.trim();
    const primaryMuscle = document.getElementById('newExerciseMuscle').value;
    const difficulty = document.getElementById('newExerciseDifficulty').value;
    const description = document.getElementById('newExerciseDescription').value.trim();
    const typicalCalories = parseFloat(document.getElementById('newExerciseCalories').value) || 8.0;
    
    if (!name || !primaryMuscle || !difficulty) {
      this.showMessage('Please fill in all required fields', 'error');
      return;
    }
    
    try {
      const result = await API.exercises.create({
        name,
        primary_muscle_group: primaryMuscle,
        difficulty_level: difficulty,
        description: description || `${name} exercise`,
        typical_calories_per_minute: typicalCalories
      });
      
      this.showMessage('Exercise created successfully!', 'success');
      e.target.reset();
      
      // Reload exercises list
      this.loadExercises();
    } catch (error) {
      console.error('Exercise creation error:', error);
      this.showMessage(error.msg || error.message || 'Failed to create exercise', 'error');
    }
  },
  
  async deleteExercise(exerciseId, exerciseName) {
    if (!confirm(`Delete exercise "${exerciseName}"? This cannot be undone if it's in use.`)) return;
    
    try {
      await API.exercises.delete(exerciseId);
      this.showMessage(`Exercise "${exerciseName}" deleted successfully!`, 'success');
      this.loadExercises();
    } catch (error) {
      console.error('Exercise deletion error:', error);
      // Check if error is because exercise is in use
      if (error.error?.code === 'CONFLICT') {
        this.showMessage(error.error.message, 'error');
      } else {
        this.showMessage(error.msg || 'Failed to delete exercise', 'error');
      }
    }
  },

  // ===== EXERCISES =====
  async loadMuscleGroups() {
    try {
      const data = await API.exercises.getMuscleGroups();
      const select = document.getElementById('filterMuscle');
      if (select && data.muscle_groups) {
        select.innerHTML = '<option value="">All Muscle Groups</option>' +
          data.muscle_groups.map(g => `<option value="${g}">${g}</option>`).join('');
      }
    } catch (error) {
      console.error('Failed to load muscle groups:', error);
    }
  },
  
  async loadExercises() {
    const container = document.getElementById('exercisesList');
    if (!container) return;
    
    const muscleGroup = document.getElementById('muscleFilter')?.value;
    const difficulty = document.getElementById('difficultyFilter')?.value;
    const search = document.getElementById('exerciseSearch')?.value;
    
    container.innerHTML = '<div class="loading">Loading exercises...</div>';
    
    try {
      let data;
      if (search) {
        data = await API.exercises.search(search);
      } else {
        data = await API.exercises.getAll(1, 50, muscleGroup, difficulty);
      }
      
      const exercises = Array.isArray(data.data)
        ? data.data
        : (Array.isArray(data.exercises) ? data.exercises : (Array.isArray(data) ? data : []));
      
      if (exercises.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No exercises found</p></div>';
        return;
      }
      
      container.innerHTML = exercises.map(ex => `
        <div class="exercise-card">
          <h4>${ex.name}</h4>
          <p>${ex.description || 'No description'}</p>
          <div class="exercise-meta">
            <span class="exercise-tag">${ex.primary_muscle_group || 'Unknown'}</span>
            <span class="exercise-tag">${ex.difficulty_level || 'Any'}</span>
          </div>
          <div class="exercise-actions">
            <button class="btn btn-primary" onclick="App.openAddToWorkoutModal('${ex.exercise_id}', '${ex.name.replace(/'/g, "\\'")}')" style="flex: 1;">Add to Workout</button>
            <button class="btn btn-danger" onclick="App.deleteExercise('${ex.exercise_id}', '${ex.name.replace(/'/g, "\\'")}')" style="flex: 1; margin-left: 8px;">Delete</button>
          </div>
        </div>
      `).join('');
    } catch (error) {
      container.innerHTML = '<div class="empty-state"><p>Failed to load exercises</p></div>';
    }
  },
  
  // ===== ML SCANNER =====
  setupMLScanner() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('equipmentImage');
    
    if (!uploadArea || !fileInput) return;
    
    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File selected
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        this.handleImageUpload(e.target.files[0]);
      }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        this.handleImageUpload(e.dataTransfer.files[0]);
      }
    });
  },
  
  handleImageUpload(file) {
    if (!file.type.startsWith('image/')) {
      this.showMessage('Please select an image file', 'error');
      return;
    }
    
    // Show preview
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      preview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
    
    // Analyze image
    this.analyzeEquipment(file);
  },
  
  async analyzeEquipment(file) {
    const resultContainer = document.getElementById('predictionResult');
    resultContainer.innerHTML = '<div class="loading">Analyzing image...</div>';
    resultContainer.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
      const response = await API.ml.identifyEquipment(formData);
      const data = response.data;  // Extract data from response wrapper
      
      console.log('Equipment analysis result:', data);
      
      resultContainer.innerHTML = `
        <div class="equipment-detected">
          <h3>Equipment Detected</h3>
          <div class="equipment-name">${data.equipment_name || 'Unknown'}</div>
          <div class="confidence-bar">
            <div class="confidence-fill" style="width: ${(data.confidence || 0) * 100}%"></div>
          </div>
          <div class="confidence-text">${Math.round((data.confidence || 0) * 100)}% confidence</div>
          ${data.primary_muscles && data.primary_muscles.length > 0 ? `
            <div class="muscle-tags" style="margin-top: 1rem;">
              ${data.primary_muscles.map(m => `<span class="muscle-tag">${m}</span>`).join('')}
            </div>
          ` : ''}
        </div>
        
        ${data.quick_exercises && data.quick_exercises.length > 0 ? `
          <h3>Suggested Exercises</h3>
          <div class="exercises-grid">
            ${data.quick_exercises.map(ex => `
              <div class="exercise-card">
                <h4>${ex.name || ex.exercise_name || 'Exercise'}</h4>
                <p>${ex.description || ''}</p>
                <div class="exercise-meta">
                  ${ex.primary_muscle ? `<span class="exercise-tag">${ex.primary_muscle}</span>` : ''}
                  ${ex.difficulty ? `<span class="exercise-tag">${ex.difficulty}</span>` : ''}
                </div>
                <div class="exercise-actions">
                  <button class="btn btn-primary btn-small" onclick="App.openAddToWorkoutModal(null, '${(ex.name || ex.exercise_name || '').replace(/'/g, "\\'")}', '${data.equipment_key}')">
                    Add to Workout
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      `;
    } catch (error) {
      resultContainer.innerHTML = `<div class="empty-state"><p>${error.msg || 'Failed to analyze image'}</p></div>`;
    }
  },
  
  clearImagePreview() {
    document.getElementById('imagePreview').classList.add('hidden');
    document.getElementById('predictionResult').classList.add('hidden');
    document.getElementById('equipmentImage').value = '';
  },
  
  async loadEquipmentList() {
    const container = document.getElementById('equipmentList');
    if (!container) return;
    
    try {
      const data = await API.ml.getEquipmentList();
      const equipment = data.equipment || [];
      
      container.innerHTML = equipment.map(eq => `
        <button class="btn btn-secondary btn-small" onclick="App.loadEquipmentExercises('${eq.key}')">
          ${eq.name}
        </button>
      `).join(' ');
    } catch (error) {
      container.innerHTML = '';
    }
  },
  
  async loadEquipmentExercises(key) {
    try {
      const data = await API.ml.getEquipmentExercises(key);
      
      const resultContainer = document.getElementById('predictionResult');
      resultContainer.classList.remove('hidden');
      resultContainer.innerHTML = `
        <div class="equipment-detected">
          <h3>${data.equipment_name || key}</h3>
          ${data.primary_muscles ? `
            <div class="muscle-tags">
              ${data.primary_muscles.map(m => `<span class="muscle-tag">${m}</span>`).join('')}
            </div>
          ` : ''}
        </div>
        
        ${data.exercises && data.exercises.length ? `
          <h3>Exercises</h3>
          <div class="exercises-grid">
            ${data.exercises.map(ex => `
              <div class="exercise-card">
                <h4>${ex.name}</h4>
                <p>${ex.description || ''}</p>
                <div class="exercise-actions">
                  <button class="btn btn-primary btn-small" onclick="App.openAddToWorkoutModal(null, '${ex.name.replace(/'/g, "\\'")}', '${key}')">
                    Add to Workout
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      `;
    } catch (error) {
      this.showMessage(error.msg || 'Failed to load exercises', 'error');
    }
  },
  
  // ===== ADD TO WORKOUT MODAL =====
  selectedExercise: null,
  
  async openAddToWorkoutModal(exerciseId, exerciseName, equipmentKey = null) {
    this.selectedExercise = { exerciseId, exerciseName, equipmentKey };
    
    // Load user's workouts
    const select = document.getElementById('selectWorkout');
    select.innerHTML = '<option value="">Loading workouts...</option>';
    
    try {
      const data = await API.workouts.getAll();
      const workouts = (data.data || data.workouts || []).filter(w => w.status !== 'completed');
      
      if (workouts.length === 0) {
        select.innerHTML = '<option value="">No active workouts - create one first</option>';
      } else {
        select.innerHTML = '<option value="">Select a workout</option>' +
          workouts.map(w => `<option value="${w.workout_id}">${w.name} (${this.formatDate(w.workout_date)})</option>`).join('');
      }
    } catch (error) {
      console.error('Failed to load workouts:', error);
      select.innerHTML = '<option value="">Failed to load workouts</option>';
    }
    
    // Show modal
    document.getElementById('modalExerciseName').textContent = exerciseName;
    document.getElementById('addToWorkoutModal').classList.remove('hidden');
  },
  
  async handleAddToWorkout(e) {
    e.preventDefault();
    
    const workoutId = document.getElementById('selectWorkout').value;
    const sets = parseInt(document.getElementById('modalSets').value) || 3;
    const reps = parseInt(document.getElementById('modalReps').value) || 10;
    const weight = parseFloat(document.getElementById('modalWeight').value) || 0;
    
    if (!workoutId) {
      this.showMessage('Please select a workout', 'error');
      return;
    }
    
    try {
      if (this.selectedExercise.exerciseId) {
        // Add existing exercise
        await API.workouts.addExercise(workoutId, this.selectedExercise.exerciseId, sets, reps, weight);
      } else {
        // Add from ML suggestion
        await API.ml.addExerciseToWorkout({
          workout_id: workoutId,
          exercise_name: this.selectedExercise.exerciseName,
          equipment_key: this.selectedExercise.equipmentKey,
          sets,
          reps,
          weight_used: weight,
          weight_unit: 'kg'
        });
      }
      
      this.showMessage('Exercise added to workout!', 'success');
      this.closeModals();
      e.target.reset();
    } catch (error) {
      const errorMsg = error.msg || error.error?.message || 'Failed to add exercise';
      this.showMessage(errorMsg, 'error');
    }
  },
  
  closeModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
  },
  
  // ===== MEALS =====
  mealItems: [], // Store current meal items
  _searchResults: [], // Store search results for click handler
  
  async loadMeals() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    const mealDateInput = document.getElementById('mealDate');
    const scanMealDateInput = document.getElementById('scanMealDate');
    if (mealDateInput) mealDateInput.value = today;
    if (scanMealDateInput) scanMealDateInput.value = today;
    
    // Setup meals event listeners if not already done
    this.setupMealsEvents();
    
    // Load meal history
    await this.loadMealHistory();
  },
  
  setupMealsEvents() {
    // Only setup once
    if (this._mealsEventsSetup) return;
    this._mealsEventsSetup = true;
    
    // Manual meal button
    document.getElementById('logMealManualBtn')?.addEventListener('click', () => {
      document.getElementById('manualMealForm')?.classList.remove('hidden');
      document.getElementById('photoMealForm')?.classList.add('hidden');
    });
    
    // Photo meal button  
    document.getElementById('logMealPhotoBtn')?.addEventListener('click', () => {
      document.getElementById('photoMealForm')?.classList.remove('hidden');
      document.getElementById('manualMealForm')?.classList.add('hidden');
    });
    
    // Close form buttons
    document.getElementById('closeMealFormBtn')?.addEventListener('click', () => {
      document.getElementById('manualMealForm')?.classList.add('hidden');
    });
    
    document.getElementById('closePhotoFormBtn')?.addEventListener('click', () => {
      document.getElementById('photoMealForm')?.classList.add('hidden');
    });
    
    // Create meal form
    document.getElementById('createMealForm')?.addEventListener('submit', (e) => this.handleCreateMeal(e));
    
    // Add food item button
    document.getElementById('addFoodItemBtn')?.addEventListener('click', () => this.addEmptyFoodItem());
    
    // Food search
    const foodSearchInput = document.getElementById('foodSearchInput');
    if (foodSearchInput) {
      foodSearchInput.addEventListener('input', this.debounce(() => this.searchFoods(), 300));
      foodSearchInput.addEventListener('focus', () => this.searchFoods());
      foodSearchInput.addEventListener('blur', () => {
        // Delay hiding to allow click to register
        setTimeout(() => {
          document.getElementById('foodSearchResults')?.classList.add('hidden');
        }, 300);
      });
    }
    
    // Photo upload
    this.setupMealPhotoUpload();
  },
  
  setupMealPhotoUpload() {
    const uploadArea = document.getElementById('mealUploadArea');
    const fileInput = document.getElementById('mealImage');
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        this.handleMealImageSelect(file);
      }
    });
    
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.handleMealImageSelect(file);
      }
    });
    
    document.getElementById('clearMealImage')?.addEventListener('click', () => {
      document.getElementById('mealImagePreview')?.classList.add('hidden');
      document.getElementById('mealAnalysisResult')?.classList.add('hidden');
      document.getElementById('mealUploadArea')?.classList.remove('hidden');
      document.getElementById('mealImage').value = '';
    });
    
    document.getElementById('saveScanMealBtn')?.addEventListener('click', () => this.saveScanMeal());
  },
  
  async handleMealImageSelect(file) {
    // Show preview
    const preview = document.getElementById('mealImagePreview');
    const previewImg = document.getElementById('mealPreviewImg');
    const uploadArea = document.getElementById('mealUploadArea');
    const spinner = document.getElementById('analyzingSpinner');
    const resultDiv = document.getElementById('mealAnalysisResult');
    
    previewImg.src = URL.createObjectURL(file);
    preview.classList.remove('hidden');
    uploadArea.classList.add('hidden');
    
    // Analyze image
    spinner.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
    try {
      const result = await API.meals.analyzeImage(file);
      const data = result.data || result;
      
      console.log('Meal analysis result:', data);
      
      // Store for later use
      this.scannedMealData = data;
      
      // Display detected foods
      const foodsList = document.getElementById('detectedFoodsList');
      
      // Add description header if available
      let html = '';
      if (data.description) {
        html += `<div class="meal-description-header"><strong>Detected:</strong> ${data.description}</div>`;
      }
      
      html += data.recognized_foods.map(food => `
        <div class="detected-food-item">
          <div>
            <span class="detected-food-name">${food.food_name}</span>
            <span class="detected-food-confidence">(${Math.round(food.confidence * 100)}% confidence)</span>
          </div>
          <span class="detected-food-calories">${Math.round(food.calories)} cal</span>
        </div>
      `).join('');
      
      foodsList.innerHTML = html;
      
      // Display totals
      const totals = data.totals;
      document.getElementById('scanCalories').textContent = Math.round(totals.calories);
      document.getElementById('scanProtein').textContent = Math.round(totals.protein_g) + 'g';
      document.getElementById('scanCarbs').textContent = Math.round(totals.carbs_g) + 'g';
      document.getElementById('scanFats').textContent = Math.round(totals.fats_g) + 'g';
      
      resultDiv.classList.remove('hidden');
    } catch (error) {
      console.error('Meal analysis failed:', error);
      this.showMessage('Failed to analyze meal image', 'error');
    } finally {
      spinner.classList.add('hidden');
    }
  },
  
  async saveScanMeal() {
    if (!this.scannedMealData) return;
    
    const mealType = document.getElementById('scanMealType').value;
    const mealDate = document.getElementById('scanMealDate').value;
    
    // Send complete food data with calories and macros
    const items = this.scannedMealData.recognized_foods.map(food => ({
      food_name: food.food_name,
      quantity: food.quantity || 100,
      quantity_unit: food.unit || 'g',
      calories: food.calories || 0,
      protein_g: food.protein_g || 0,
      carbs_g: food.carbs_g || 0,
      fats_g: food.fats_g || 0
    }));
    
    try {
      await API.meals.create({
        meal_type: mealType,
        meal_date: mealDate,
        items: items,
        notes: 'Scanned meal'
      });
      
      this.showMessage('Meal saved successfully!', 'success');
      
      // Reset form
      document.getElementById('photoMealForm')?.classList.add('hidden');
      document.getElementById('mealImagePreview')?.classList.add('hidden');
      document.getElementById('mealAnalysisResult')?.classList.add('hidden');
      document.getElementById('mealUploadArea')?.classList.remove('hidden');
      document.getElementById('mealImage').value = '';
      this.scannedMealData = null;
      
      // Reload meals list
      await this.loadMealHistory();
      await this.loadNutritionSummary();
    } catch (error) {
      console.error('Failed to save meal:', error);
      this.showMessage('Failed to save meal', 'error');
    }
  },
  
  async searchFoods() {
    const input = document.getElementById('foodSearchInput');
    const resultsDiv = document.getElementById('foodSearchResults');
    
    if (!input || !resultsDiv) return;
    
    const query = input.value.trim();
    
    if (query.length < 2) {
      resultsDiv.classList.add('hidden');
      return;
    }
    
    try {
      const result = await API.meals.searchFoods(query);
      const foods = result.data?.foods || result.foods || [];
      
      if (foods.length === 0) {
        resultsDiv.innerHTML = '<div class="food-search-item">No foods found</div>';
      } else {
        resultsDiv.innerHTML = foods.map((food, index) => `
          <div class="food-search-item" data-food-index="${index}">
            <div class="food-search-item-name">${food.food_name}</div>
            <div class="food-search-item-info">${food.calories_per_100g} cal/100g | P: ${food.protein_per_100g}g | C: ${food.carbs_per_100g}g | F: ${food.fats_per_100g}g</div>
          </div>
        `).join('');
        
        // Store foods for click handler reference
        this._searchResults = foods;
        
        // Add click handlers using mousedown (fires before blur)
        resultsDiv.querySelectorAll('.food-search-item').forEach(item => {
          item.addEventListener('mousedown', (e) => {
            e.preventDefault(); // Prevent blur from firing
            const index = parseInt(item.dataset.foodIndex);
            const food = this._searchResults[index];
            if (food) {
              this.addFoodItem(food);
              resultsDiv.classList.add('hidden');
              input.value = '';
            }
          });
        });
      }
      
      resultsDiv.classList.remove('hidden');
    } catch (error) {
      console.error('Food search failed:', error);
    }
  },
  
  addFoodItem(food) {
    const itemId = Date.now();
    const item = {
      id: itemId,
      food_name: food.food_name,
      quantity: food.default_serving || 100,
      quantity_unit: food.default_unit || 'g',
      calories_per_100g: food.calories_per_100g,
      protein_per_100g: food.protein_per_100g,
      carbs_per_100g: food.carbs_per_100g,
      fats_per_100g: food.fats_per_100g
    };
    
    this.mealItems.push(item);
    this.renderFoodItems();
    this.updateMealTotals();
    
    // Scroll to the food items list to show the newly added item
    const container = document.getElementById('foodItemsList');
    if (container) {
      container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  },
  
  addEmptyFoodItem() {
    // Just focus search and scroll to it
    const searchInput = document.getElementById('foodSearchInput');
    if (searchInput) {
      searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      searchInput.focus();
    }
  },
  
  removeFoodItem(itemId) {
    this.mealItems = this.mealItems.filter(item => item.id !== itemId);
    this.renderFoodItems();
    this.updateMealTotals();
  },
  
  renderFoodItems() {
    const container = document.getElementById('foodItemsList');
    if (!container) return;
    
    if (this.mealItems.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No food items added yet. Search for foods above.</p></div>';
      return;
    }
    
    container.innerHTML = this.mealItems.map(item => `
      <div class="food-item" data-id="${item.id}">
        <div class="food-item-info">
          <div class="food-item-name">${item.food_name}</div>
          <div class="food-item-nutrition">
            ${this.calculateItemNutrition(item).calories} cal
          </div>
        </div>
        <div class="food-item-quantity">
          <input type="number" value="${item.quantity}" min="1" step="1" onchange="App.updateFoodItemQuantity(${item.id}, this.value)">
          <span>${item.quantity_unit}</span>
        </div>
        <button class="btn-remove" onclick="App.removeFoodItem(${item.id})">✕</button>
      </div>
    `).join('');
  },
  
  updateFoodItemQuantity(itemId, quantity) {
    const item = this.mealItems.find(i => i.id === itemId);
    if (item) {
      item.quantity = parseFloat(quantity) || 100;
      this.updateMealTotals();
    }
  },
  
  calculateItemNutrition(item) {
    const multiplier = item.quantity / 100;
    return {
      calories: Math.round(item.calories_per_100g * multiplier),
      protein: Math.round(item.protein_per_100g * multiplier * 10) / 10,
      carbs: Math.round(item.carbs_per_100g * multiplier * 10) / 10,
      fats: Math.round(item.fats_per_100g * multiplier * 10) / 10
    };
  },
  
  updateMealTotals() {
    let totalCalories = 0;
    let totalProtein = 0;
    let totalCarbs = 0;
    let totalFats = 0;
    
    this.mealItems.forEach(item => {
      const nutrition = this.calculateItemNutrition(item);
      totalCalories += nutrition.calories;
      totalProtein += nutrition.protein;
      totalCarbs += nutrition.carbs;
      totalFats += nutrition.fats;
    });
    
    document.getElementById('previewCalories').textContent = Math.round(totalCalories);
    document.getElementById('previewProtein').textContent = Math.round(totalProtein) + 'g';
    document.getElementById('previewCarbs').textContent = Math.round(totalCarbs) + 'g';
    document.getElementById('previewFats').textContent = Math.round(totalFats) + 'g';
  },
  
  async handleCreateMeal(e) {
    e.preventDefault();
    
    const mealType = document.getElementById('mealType').value;
    const mealDate = document.getElementById('mealDate').value;
    const mealNotes = document.getElementById('mealNotes').value;
    
    if (this.mealItems.length === 0) {
      this.showMessage('Please add at least one food item', 'error');
      return;
    }
    
    const items = this.mealItems.map(item => ({
      food_name: item.food_name,
      quantity: item.quantity,
      quantity_unit: item.quantity_unit
    }));
    
    try {
      await API.meals.create({
        meal_type: mealType,
        meal_date: mealDate,
        items: items,
        notes: mealNotes
      });
      
      this.showMessage('Meal logged successfully!', 'success');
      
      // Reset form
      this.mealItems = [];
      this.renderFoodItems();
      this.updateMealTotals();
      document.getElementById('mealType').value = '';
      document.getElementById('mealNotes').value = '';
      document.getElementById('manualMealForm')?.classList.add('hidden');
      
      // Reload data
      await this.loadMealHistory();
      await this.loadNutritionSummary();
    } catch (error) {
      console.error('Failed to create meal:', error);
      this.showMessage('Failed to log meal', 'error');
    }
  },
  
  async loadNutritionSummary() {
    try {
      const result = await API.meals.getDailySummary();
      const data = result.data || result;
      
      document.getElementById('todayCalories').textContent = Math.round(data.total_calories || 0);
      document.getElementById('todayProtein').textContent = Math.round(data.total_protein_g || 0) + 'g';
      document.getElementById('todayCarbs').textContent = Math.round(data.total_carbs_g || 0) + 'g';
      document.getElementById('todayFats').textContent = Math.round(data.total_fats_g || 0) + 'g';
    } catch (error) {
      console.error('Failed to load nutrition summary:', error);
    }
  },
  
  async loadMealHistory() {
    const container = document.getElementById('mealsList');
    if (!container) return;
    
    try {
      // Get today's date for filtering
      const today = new Date().toISOString().split('T')[0];
      const result = await API.meals.getMine(1, 50);
      const allMeals = result.data || result.meals || [];
      
      // Filter to show only today's meals
      const meals = allMeals.filter(meal => {
        const mealDate = meal.meal_date?.split('T')[0] || meal.meal_date;
        return mealDate === today;
      });
      
      if (meals.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No meals logged today. Start tracking your nutrition!</p></div>';
        return;
      }
      
      // Store meals for tooltips
      this.allMeals = allMeals;
      
      container.innerHTML = meals.map(meal => {
        // Get food items list
        const items = meal.items || [];
        const itemsList = items.length > 0 
          ? items.map(item => `${item.food_name} (${item.quantity || 100}${item.quantity_unit || 'g'})`).join(', ')
          : 'No items';
        
        return `
          <div class="meal-card" data-meal-id="${meal.meal_id}" title="Foods: ${itemsList}">
            <div class="meal-info">
              <span class="meal-type-badge meal-type-${meal.meal_type}">${this.getMealTypeEmoji(meal.meal_type)} ${meal.meal_type}</span>
              <div class="meal-name">${meal.notes || meal.meal_type}</div>
              ${items.length > 0 ? `<div class="meal-items-preview">${items.map(i => i.food_name).slice(0, 3).join(', ')}${items.length > 3 ? '...' : ''}</div>` : ''}
              <div class="meal-macros">
                <span class="meal-macro">🔥 <strong>${Math.round(meal.total_calories || 0)}</strong> cal</span>
                <span class="meal-macro">P: <span>${Math.round(meal.protein_g || 0)}g</span></span>
                <span class="meal-macro">C: <span>${Math.round(meal.carbs_g || 0)}g</span></span>
                <span class="meal-macro">F: <span>${Math.round(meal.fats_g || 0)}g</span></span>
              </div>
              <div class="meal-actions">
                <button class="btn btn-small btn-secondary" onclick="App.showMealDetails('${meal.meal_id}')">View</button>
                <button class="btn btn-small btn-success" onclick="App.showAddItemToMeal('${meal.meal_id}')">+ Add Item</button>
                <button class="btn btn-small btn-danger" onclick="App.deleteMeal('${meal.meal_id}')">Delete</button>
              </div>
            </div>
            <div class="meal-calories">
              <div class="meal-calories-value">${Math.round(meal.total_calories || 0)}</div>
              <div class="meal-calories-label">calories</div>
            </div>
          </div>
        `;
      }).join('');
    } catch (error) {
      console.error('Failed to load meal history:', error);
      container.innerHTML = '<div class="empty-state"><p>Failed to load meals</p></div>';
    }
  },
  
  showMealDetails(mealId) {
    const meal = this.allMeals?.find(m => m.meal_id === mealId);
    if (!meal) return;
    
    const items = meal.items || [];
    const itemsHtml = items.length > 0 
      ? items.map(item => `
          <div class="meal-detail-item">
            <span>${item.food_name}</span>
            <span>${item.quantity || 100}${item.quantity_unit || 'g'}</span>
            <span>${Math.round(item.calories || 0)} cal</span>
          </div>
        `).join('')
      : '<p>No food items recorded</p>';
    
    const html = `
      <div class="meal-details-popup" id="mealDetailsPopup">
        <div class="meal-details-content">
          <div class="meal-details-header">
            <h3>${this.getMealTypeEmoji(meal.meal_type)} ${meal.meal_type?.charAt(0).toUpperCase() + meal.meal_type?.slice(1) || 'Meal'}</h3>
            <button class="btn btn-small btn-secondary" onclick="App.closeMealDetails()">✕</button>
          </div>
          <p class="meal-details-date">${meal.meal_date || 'Today'}</p>
          <div class="meal-details-items">
            <h4>Food Items:</h4>
            ${itemsHtml}
          </div>
          <div class="meal-details-totals">
            <div class="total-item"><span class="total-value">${Math.round(meal.total_calories || 0)}</span><span class="total-label">Calories</span></div>
            <div class="total-item"><span class="total-value">${Math.round(meal.protein_g || 0)}g</span><span class="total-label">Protein</span></div>
            <div class="total-item"><span class="total-value">${Math.round(meal.carbs_g || 0)}g</span><span class="total-label">Carbs</span></div>
            <div class="total-item"><span class="total-value">${Math.round(meal.fats_g || 0)}g</span><span class="total-label">Fats</span></div>
          </div>
        </div>
      </div>
    `;
    
    // Remove existing popup if any
    this.closeMealDetails();
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Close on click outside
    document.getElementById('mealDetailsPopup').addEventListener('click', (e) => {
      if (e.target.id === 'mealDetailsPopup') this.closeMealDetails();
    });
  },
  
  closeMealDetails() {
    const popup = document.getElementById('mealDetailsPopup');
    if (popup) popup.remove();
  },
  
  showAddItemToMeal(mealId) {
    this.currentMealId = mealId;
    
    const html = `
      <div class="meal-add-item-popup" id="mealAddItemPopup">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Add Item to Meal</h3>
            <button class="btn btn-small btn-secondary" onclick="App.closeAddItemToMeal()">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label for="addItemFoodName">Food Name</label>
              <input type="text" id="addItemFoodName" placeholder="e.g., chicken, rice, salad" class="form-input">
              <div id="addItemFoodResults" class="food-search-results hidden"></div>
            </div>
            <div class="form-group">
              <label for="addItemQuantity">Quantity</label>
              <div class="quantity-input">
                <input type="number" id="addItemQuantity" value="100" min="1" class="form-input" style="flex: 1;">
                <select id="addItemUnit" class="form-select" style="flex: 0.6;">
                  <option value="g">grams</option>
                  <option value="ml">ml</option>
                  <option value="cup">cup</option>
                  <option value="slice">slice</option>
                  <option value="piece">piece</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <button class="btn btn-primary btn-full" onclick="App.saveAddItemToMeal()">Add Item</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Setup food search
    const foodInput = document.getElementById('addItemFoodName');
    foodInput.addEventListener('input', this.debounce(() => this.searchAddItemFoods(), 300));
    foodInput.addEventListener('focus', () => this.searchAddItemFoods());
    
    // Close on click outside
    document.getElementById('mealAddItemPopup').addEventListener('click', (e) => {
      if (e.target.id === 'mealAddItemPopup') this.closeAddItemToMeal();
    });
  },
  
  async searchAddItemFoods() {
    const searchInput = document.getElementById('addItemFoodName').value.trim();
    const resultsDiv = document.getElementById('addItemFoodResults');
    
    if (!searchInput || searchInput.length < 2) {
      resultsDiv.classList.add('hidden');
      return;
    }
    
    try {
      const response = await fetch(`${API.BASE_URL}/api/meals/foods?search=${encodeURIComponent(searchInput)}`);
      const data = await response.json();
      const foods = data.foods || [];
      
      if (foods.length === 0) {
        resultsDiv.innerHTML = '<div class="search-item">No foods found</div>';
        resultsDiv.classList.remove('hidden');
        return;
      }
      
      resultsDiv.innerHTML = foods.slice(0, 5).map(food => `
        <div class="search-item" onclick="App.selectAddItemFood('${food}')">${food}</div>
      `).join('');
      resultsDiv.classList.remove('hidden');
    } catch (error) {
      console.error('Failed to search foods:', error);
    }
  },
  
  selectAddItemFood(foodName) {
    document.getElementById('addItemFoodName').value = foodName;
    document.getElementById('addItemFoodResults').classList.add('hidden');
  },
  
  async saveAddItemToMeal() {
    const foodName = document.getElementById('addItemFoodName').value.trim();
    const quantity = parseInt(document.getElementById('addItemQuantity').value) || 100;
    const unit = document.getElementById('addItemUnit').value || 'g';
    
    if (!foodName) {
      alert('Please enter a food name');
      return;
    }
    
    try {
      const response = await fetch(`${API.BASE_URL}/api/meals/${this.currentMealId}/add-item`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          food_name: foodName,
          quantity: quantity,
          quantity_unit: unit
        })
      });
      
      if (response.ok) {
        this.closeAddItemToMeal();
        await this.loadMealHistory();
        console.log('Item added successfully');
      } else {
        alert('Failed to add item');
      }
    } catch (error) {
      console.error('Failed to add item:', error);
      alert('Error adding item');
    }
  },
  
  closeAddItemToMeal() {
    const popup = document.getElementById('mealAddItemPopup');
    if (popup) popup.remove();
  },
  
  getMealTypeEmoji(type) {
    const emojis = {
      'breakfast': '🌅',
      'lunch': '☀️',
      'dinner': '🌙',
      'snack': '🍿',
      'other': '📦'
    };
    return emojis[type] || '🍽️';
  },
  
  async deleteMeal(mealId) {
    if (!confirm('Are you sure you want to delete this meal?')) return;
    
    try {
      await API.meals.delete(mealId);
      this.showMessage('Meal deleted', 'success');
      await this.loadMealHistory();
      await this.loadNutritionSummary();
    } catch (error) {
      console.error('Failed to delete meal:', error);
      this.showMessage('Failed to delete meal', 'error');
    }
  },

  // ===== PROFILE =====
  // loadProfile moved to weight tracking section below
  
  
  async handleUpdateProfile(e) {
    e.preventDefault();
    
    const data = {
      age: parseFloat(document.getElementById('profileAge').value) || null,
      current_weight: parseFloat(document.getElementById('profileWeight').value) || null,
      target_weight: parseFloat(document.getElementById('profileTargetWeight').value) || null,
      height: parseFloat(document.getElementById('profileHeight').value) || null
    };
    
    try {
      const user = this.user;
      const response = await API.request(`/api/users/${user.user_id}`, {
        method: 'PUT',
        body: data
      });
      
      // Update local user object
      if (response.data) {
        this.user.age = response.data.age;
        this.user.current_weight = response.data.current_weight;
        this.user.target_weight = response.data.target_weight;
        this.user.height = response.data.height;
      }
      
      this.showMessage('Profile updated!', 'success');
      
      // Reload weight chart to show new target weight
      this.loadWeightChart();
    } catch (error) {
      this.showMessage(error.msg || 'Failed to update profile', 'error');
    }
  },
  
  async handleChangePassword(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
      this.showMessage('Please fill in all password fields', 'error');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      this.showMessage('New passwords do not match', 'error');
      return;
    }
    
    if (newPassword.length < 6) {
      this.showMessage('Password must be at least 6 characters', 'error');
      return;
    }
    
    try {
      await API.auth.changePassword(currentPassword, newPassword);
      this.showMessage('Password changed!', 'success');
      e.target.reset();
    } catch (error) {
      this.showMessage(error.msg || 'Failed to change password', 'error');
    }
  },
  
  // ===== LOGOUT =====
  logout() {
    API.clearToken();
    API.clearUser();
    window.location.href = 'index.html';
  },
  
  // ===== HELPERS =====
  showMessage(message, type) {
    // Remove existing messages
    document.querySelectorAll('.message').forEach(m => m.remove());
    
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = message;
    document.body.appendChild(div);
    
    setTimeout(() => div.remove(), 3000);
  },
  
  formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  },
  
  // Weight Tracking Functions
  async loadProfile() {
    try {
      const data = await API.auth.getProfile();
      
      document.getElementById('profileUsername').value = data.username || '';
      document.getElementById('profileEmail').value = data.email || '';
      document.getElementById('profileAge').value = data.age || '';
      document.getElementById('profileWeight').value = data.current_weight || '';
      document.getElementById('profileTargetWeight').value = data.target_weight || '';
      document.getElementById('profileHeight').value = data.height || '';
      
      // Load weight history and chart
      this.loadWeightChart();
      
      // Set today's date as default for new weight entry
      document.getElementById('newWeightDate').valueAsDate = new Date();
      
      // Bind weight entry form
      document.getElementById('addWeightBtn')?.addEventListener('click', (e) => this.handleAddWeightEntry(e));
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  },
  
  async loadWeightChart() {
    if (!this.user) return;
    
    try {
      const response = await API.weight.getHistory(this.user.user_id, 90);
      const data = response.data || response;
      
      // Create weight chart
      this.createWeightChart(data, 'weightChart');
    } catch (error) {
      console.error('Failed to load weight history:', error);
    }
  },
  
  async loadDashboardWeightChart() {
    if (!this.user) return;
    
    try {
      const response = await API.weight.getHistory(this.user.user_id, 90);
      const data = response.data || response;
      
      // Create weight chart for dashboard
      this.createWeightChart(data, 'weightDashboardChart');
    } catch (error) {
      console.error('Failed to load weight history for dashboard:', error);
    }
  },
  
  createWeightChart(data, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Destroy existing chart if it exists
    const ctx = canvas.getContext('2d');
    if (ctx && this.weightCharts && this.weightCharts[canvasId]) {
      this.weightCharts[canvasId].destroy();
    }
    
    if (!this.weightCharts) {
      this.weightCharts = {};
    }
    
    // Prepare data
    const dates = [];
    const weights = [];
    
    if (data.entries && data.entries.length > 0) {
      data.entries.forEach(entry => {
        dates.push(new Date(entry.entry_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        weights.push(entry.weight);
      });
    }
    
    // Create horizontal line data for target weight
    const targetWeight = data.target_weight;
    const targetLine = targetWeight ? Array(dates.length).fill(targetWeight) : null;
    
    // Create chart
    const datasets = [
      {
        label: 'Weight (kg)',
        data: weights,
        borderColor: '#3182ce',
        backgroundColor: 'rgba(49, 130, 206, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#3182ce',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointHoverRadius: 7
      }
    ];
    
    // Add target weight line if it exists
    if (targetLine) {
      datasets.push({
        label: `Target Weight (${targetWeight}kg)`,
        data: targetLine,
        borderColor: '#38a169',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
        tension: 0
      });
    }
    
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#f1f5f9',
              font: { size: 12 }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(52, 73, 94, 0.3)' }
          },
          x: {
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(52, 73, 94, 0.3)' }
          }
        }
      }
    });
    
    this.weightCharts[canvasId] = chart;
  },
  
  async handleAddWeightEntry(e) {
    e.preventDefault();
    
    const weight = parseFloat(document.getElementById('newWeightInput').value);
    const entryDate = document.getElementById('newWeightDate').value;
    const notes = document.getElementById('newWeightNotes').value;
    
    if (!weight || weight <= 0) {
      this.showMessage('Please enter a valid weight', 'error');
      return;
    }
    
    try {
      const data = {
        weight: weight,
        entry_date: entryDate,
        notes: notes || null
      };
      
      await API.weight.addEntry(this.user.user_id, data);
      
      this.showMessage('Weight entry added!', 'success');
      
      // Clear form
      document.getElementById('newWeightInput').value = '';
      document.getElementById('newWeightNotes').value = '';
      document.getElementById('newWeightDate').valueAsDate = new Date();
      
      // Reload weight charts
      this.loadWeightChart();
      if (this.currentTab === 'dashboard') {
        this.loadDashboardWeightChart();
      }
    } catch (error) {
      this.showMessage(error.msg || 'Failed to add weight entry', 'error');
    }
  },
  
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => App.init());
