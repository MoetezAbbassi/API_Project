/**
 * API Service - Handles all HTTP requests to the backend
 */
const API = {
  BASE_URL: 'https://fitness-api-moatezabbassi-gqeueufbhfejbue6.francecentral-01.azurewebsites.net',
  
  // Token management
  getToken() {
    const token = localStorage.getItem('token');
    console.log('getToken called, token exists:', !!token);
    return token;
  },
  
  setToken(token) {
    console.log('setToken called, token:', token ? token.substring(0, 20) + '...' : 'null');
    if (token) {
      localStorage.setItem('token', token);
    }
  },
  
  clearToken() {
    console.log('clearToken called');
    localStorage.removeItem('token');
  },
  
  // User management
  getUser() {
    const user = localStorage.getItem('user');
    console.log('getUser called, user:', user);
    return user ? JSON.parse(user) : null;
  },
  
  setUser(user) {
    console.log('setUser called:', user);
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  },
  
  clearUser() {
    console.log('clearUser called');
    localStorage.removeItem('user');
  },
  
  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getToken();
  },
  
  // Build headers
  getHeaders(includeAuth = true, isFormData = false) {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    if (includeAuth && this.getToken()) {
      headers['Authorization'] = `Bearer ${this.getToken()}`;
    }
    return headers;
  },
  
  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.BASE_URL}${endpoint}`;
    const headers = this.getHeaders(options.auth !== false, options.isFormData);
    
    const config = {
      method: options.method || 'GET',
      headers: headers
    };
    
    if (options.body && !options.isFormData) {
      config.body = JSON.stringify(options.body);
    } else if (options.body && options.isFormData) {
      config.body = options.body;
      delete config.headers['Content-Type']; // Let browser set it
    }
    
    console.log('API Request:', endpoint, 'Headers:', config.headers);
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      console.log('API Response:', endpoint, 'Status:', response.status);
      
      if (!response.ok) {
        // Handle 401 Unauthorized
        if (response.status === 401) {
          console.log('401 Unauthorized - clearing auth and redirecting');
          this.clearToken();
          this.clearUser();
          window.location.href = 'index.html';
        }
        throw { status: response.status, ...data };
      }
      
      return data;
    } catch (error) {
      if (error.status) {
        throw error;
      }
      throw { status: 0, msg: 'Network error. Please check your connection.' };
    }
  },
  
  // ===== AUTH ENDPOINTS =====
  auth: {
    login(username, password) {
      // Backend accepts either username or email
      console.log('🔐 API.auth.login called with:', username);
      return API.request('/api/auth/login', {
        method: 'POST',
        body: { username, password },
        auth: false
      });
    },
    
    verifyLogin(userId, code) {
      console.log('🔐 API.auth.verifyLogin called with userId:', userId, 'code:', code);
      return API.request('/api/auth/verify-login', {
        method: 'POST',
        body: { user_id: userId, code },
        auth: false
      });
    },
    
    resendCode(userId) {
      return API.request('/api/auth/resend-code', {
        method: 'POST',
        body: { user_id: userId },
        auth: false
      });
    },
    
    register(userData) {
      return API.request('/api/auth/register', {
        method: 'POST',
        body: userData,
        auth: false
      });
    },
    
    getProfile() {
      return API.request('/api/auth/profile');
    },
    
    updateProfile(data) {
      return API.request('/api/auth/profile', {
        method: 'PUT',
        body: data
      });
    },
    
    changePassword(currentPassword, newPassword) {
      return API.request('/api/auth/change-password', {
        method: 'POST',
        body: { current_password: currentPassword, new_password: newPassword }
      });
    }
  },
  
  // ===== WORKOUTS ENDPOINTS =====
  workouts: {
    getAll(page = 1, perPage = 10) {
      return API.request(`/api/workouts?page=${page}&per_page=${perPage}`);
    },
    
    get(id) {
      return API.request(`/api/workouts/${id}`);
    },
    
    create(data) {
      return API.request('/api/workouts', {
        method: 'POST',
        body: data
      });
    },
    
    update(id, data) {
      return API.request(`/api/workouts/${id}`, {
        method: 'PUT',
        body: data
      });
    },
    
    delete(id) {
      return API.request(`/api/workouts/${id}`, {
        method: 'DELETE'
      });
    },
    
    addExercise(workoutId, exerciseId, sets, reps, weight, duration) {
      return API.request(`/api/workouts/${workoutId}/exercises`, {
        method: 'POST',
        body: { exercise_id: exerciseId, sets, reps, weight_used: weight, weight_unit: 'kg', duration }
      });
    },
    
    updateExercise(workoutId, exerciseId, data) {
      return API.request(`/api/workouts/${workoutId}/exercises/${exerciseId}`, {
        method: 'PUT',
        body: data
      });
    },
    
    removeExercise(workoutId, exerciseId) {
      return API.request(`/api/workouts/${workoutId}/exercises/${exerciseId}`, {
        method: 'DELETE'
      });
    },
    
    complete(id, caloriesBurned, duration) {
      return API.request(`/api/workouts/${id}/complete`, {
        method: 'POST',
        body: { calories_burned: caloriesBurned, duration }
      });
    },
    
    getStats(userId) {
      return API.request(`/api/workouts/stats/${userId}`);
    }
  },
  
  // ===== EXERCISES ENDPOINTS =====
  exercises: {
    getAll(page = 1, perPage = 20, muscleGroup = null, difficulty = null) {
      let url = `/api/exercises?page=${page}&per_page=${perPage}`;
      if (muscleGroup) url += `&muscle_group=${encodeURIComponent(muscleGroup)}`;
      if (difficulty) url += `&difficulty=${encodeURIComponent(difficulty)}`;
      return API.request(url);
    },
    
    get(id) {
      return API.request(`/api/exercises/${id}`);
    },
    
    search(query) {
      return API.request(`/api/exercises/search?q=${encodeURIComponent(query)}`);
    },
    
    create(exerciseData) {
      return API.request('/api/exercises', {
        method: 'POST',
        body: exerciseData
      });
    },
    
    delete(id) {
      return API.request(`/api/exercises/${id}`, {
        method: 'DELETE'
      });
    },
    
    getMuscleGroups() {
      return API.request('/api/exercises/muscle-groups');
    }
  },
  
  // ===== DASHBOARD ENDPOINTS =====
  dashboard: {
    getSummary(userId) {
      return API.request(`/api/dashboard/${userId}/summary`);
    },
    
    getWorkoutStats(userId) {
      return API.request(`/api/dashboard/${userId}/workout-stats`);
    },
    
    getNutritionStats(userId) {
      return API.request(`/api/dashboard/${userId}/nutrition-stats`);
    },
    
    getCaloriesGraph(userId, days = 7) {
      return API.request(`/api/dashboard/${userId}/calories-graph?days=${days}`);
    },
    
    getRecentActivity(userId, limit = 10) {
      return API.request(`/api/dashboard/${userId}/recent-activity?limit=${limit}`);
    }
  },
  
  // ===== ML ENDPOINTS =====
  ml: {
    identifyEquipment(formData) {
      return API.request('/api/ml/identify-equipment', {
        method: 'POST',
        body: formData,
        isFormData: true
      });
    },
    
    addExerciseToWorkout(exerciseData) {
      return API.request('/api/ml/add-exercise-to-workout', {
        method: 'POST',
        body: exerciseData
      });
    },
    
    getEquipmentList() {
      return API.request('/api/ml/equipment-list');
    },
    
    getEquipmentExercises(equipmentKey) {
      return API.request(`/api/ml/equipment/${equipmentKey}/exercises`);
    }
  },
  
  // ===== NUTRITION ENDPOINTS =====
  nutrition: {
    search(query) {
      return API.request(`/api/nutrition/search?q=${encodeURIComponent(query)}`);
    },
    
    analyze(description) {
      return API.request('/api/nutrition/analyze', {
        method: 'POST',
        body: { description }
      });
    }
  },
  
  // ===== MEALS ENDPOINTS =====
  meals: {
    // Get all meals for current user
    getAll(page = 1, perPage = 20, startDate = null, endDate = null) {
      const user = API.getUser();
      if (!user) return Promise.reject({ msg: 'Not logged in' });
      
      let url = `/api/meals/${user.user_id}?page=${page}&per_page=${perPage}`;
      if (startDate) url += `&start_date=${startDate}`;
      if (endDate) url += `&end_date=${endDate}`;
      return API.request(url);
    },
    
    // Get meals for current user (shorthand)
    getMine(page = 1, perPage = 20) {
      return API.request(`/api/meals?page=${page}&per_page=${perPage}`);
    },
    
    // Get single meal by ID
    get(mealId) {
      return API.request(`/api/meals/${mealId}`);
    },
    
    // Create a new meal with items
    create(mealData) {
      return API.request('/api/meals', {
        method: 'POST',
        body: mealData
      });
    },
    
    // Update a meal
    update(mealId, data) {
      return API.request(`/api/meals/${mealId}`, {
        method: 'PUT',
        body: data
      });
    },
    
    // Delete a meal
    delete(mealId) {
      return API.request(`/api/meals/${mealId}`, {
        method: 'DELETE'
      });
    },
    
    // Get daily nutrition summary
    getDailySummary(date = null) {
      let url = '/api/meals/nutrition/summary';
      if (date) url += `?date=${date}`;
      return API.request(url);
    },
    
    // Analyze meal from image (ML recognition)
    analyzeImage(imageFile) {
      const formData = new FormData();
      formData.append('image', imageFile);
      
      return API.request('/api/meals/analyze-image', {
        method: 'POST',
        body: formData,
        isFormData: true
      });
    },
    
    // Analyze meal from text description
    analyzeText(items) {
      return API.request('/api/meals/analyze-text', {
        method: 'POST',
        body: { items }
      });
    },
    
    // Search for foods
    searchFoods(query) {
      return API.request(`/api/meals/search?q=${encodeURIComponent(query)}`);
    }
  },
  
  // ===== PROGRAMS ENDPOINTS =====
  programs: {
    getAll() {
      return API.request('/api/programs');
    },
    
    get(id) {
      return API.request(`/api/programs/${id}`);
    },
    
    start(id) {
      return API.request(`/api/programs/${id}/start`, {
        method: 'POST'
      });
    }
  },
  
  // ===== CALENDAR ENDPOINTS =====
  calendar: {
    getEvents(startDate, endDate) {
      return API.request(`/api/calendar?start=${startDate}&end=${endDate}`);
    },
    
    createEvent(data) {
      return API.request('/api/calendar', {
        method: 'POST',
        body: data
      });
    }
  },
  
  // ===== WEIGHT TRACKING ENDPOINTS =====
  weight: {
    addEntry(userId, data) {
      return API.request(`/api/users/${userId}/weight`, {
        method: 'POST',
        body: data
      });
    },
    
    getHistory(userId, days = 90) {
      return API.request(`/api/users/${userId}/weight?days=${days}`);
    },
    
    updateEntry(userId, entryId, data) {
      return API.request(`/api/users/${userId}/weight/${entryId}`, {
        method: 'PUT',
        body: data
      });
    },
    
    deleteEntry(userId, entryId) {
      return API.request(`/api/users/${userId}/weight/${entryId}`, {
        method: 'DELETE'
      });
    }
  }
};

// Export for use in other modules
window.API = API;
