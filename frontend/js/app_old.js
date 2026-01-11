(function () {
  // Auth guard - redirect if not logged in
  if (!window.api.getToken()) {
    window.location.href = "index.html";
    return;
  }

  const msgEl = document.getElementById("message");

  function showMessage(text, type) {
    msgEl.textContent = text;
    msgEl.className = `message ${type}`;
    msgEl.classList.remove("hidden");
    setTimeout(() => msgEl.classList.add("hidden"), 4000);
  }

  function setDefaultDate() {
    const today = new Date().toISOString().split("T")[0];
    const workoutDate = document.getElementById("workoutDate");
    const goalDate = document.getElementById("goalDate");
    if (workoutDate) workoutDate.value = today;
    if (goalDate) goalDate.value = today;
  }

  function activateTab(tabName) {
    document.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));
    const tab = document.getElementById(tabName);
    if (tab) tab.classList.add("active");

    document.querySelectorAll(".nav-link").forEach((a) => a.classList.remove("active"));
    document.querySelector(`.nav-link[data-tab="${tabName}"]`)?.classList.add("active");
  }

  async function loadDashboard() {
    try {
      const token = window.api.getToken();
      const headers = token ? { "Authorization": `Bearer ${token}` } : {};

      const [exercises, workouts, goals, meals] = await Promise.all([
        window.api.request("/exercises?page=1&per_page=100").then(r => r).catch(() => ({ total: 0, data: [] })),
        window.api.request("/workouts").then(r => r).catch(() => ({ data: [] })),
        window.api.request("/goals").then(r => r).catch(() => ({ data: [] })),
        window.api.request("/meals").then(r => r).catch(() => ({ data: [] }))
      ]);

      document.getElementById("totalExercises").textContent = exercises?.total || exercises?.data?.length || 0;
      document.getElementById("totalWorkouts").textContent = (workouts?.data || []).length || 0;
      document.getElementById("activeGoals").textContent = (goals?.data || []).filter((g) => g.status === "active").length || 0;

      const totalCalories = (meals?.data || []).reduce((sum, m) => sum + (m.calories || 0), 0);
      document.getElementById("totalCalories").textContent = totalCalories || 0;

      const recentBox = document.getElementById("recentWorkouts");
      const list = workouts?.data || [];
      if (list.length) {
        recentBox.innerHTML = list.slice(0, 5).map((w) => `
          <div class="list-item">
            <div class="list-item-info">
              <h4>${w.name || "Workout"}</h4>
              <p>${w.date || "-"} • ${w.duration || 0} minutes</p>
            </div>
            <span class="badge badge-success">Done</span>
          </div>
        `).join("");
      } else {
        recentBox.innerHTML = '<div class="empty-state"><p>No workouts yet</p></div>';
      }
    } catch (e) {
      showMessage("Failed to load dashboard", "error");
    }
  }

  async function loadExercises() {
    try {
      const search = document.getElementById("exerciseSearch")?.value.trim() || "";
      const muscle = document.getElementById("muscleFilter")?.value || "";

      let url = `/exercises?page=1&per_page=50`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (muscle) url += `&muscle_group=${encodeURIComponent(muscle)}`;

      const response = await window.api.request(url);
      const exercises = response?.data || [];

      const html = exercises.length
        ? exercises.map((ex) => `
          <div class="list-item">
            <div class="list-item-info">
              <h4>${ex.name}</h4>
              <p>Muscle: ${ex.muscle_group} • Difficulty: ${ex.difficulty}</p>
            </div>
            <button class="btn btn-small btn-secondary" type="button">Add</button>
          </div>
        `).join("")
        : '<div class="empty-state"><p>No exercises found</p></div>';

      document.getElementById("exercisesList").innerHTML = html;
    } catch (e) {
      showMessage("Failed to load exercises", "error");
    }
  }

  async function loadWorkouts() {
    try {
      const res = await window.api.request("/workouts");

      if (!res?.success && res?.status === 405) {
        showMessage("Workouts endpoint not enabled. Contact admin.", "error");
        document.getElementById("workoutsList").innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
        return;
      }

      const workouts = res?.data || [];
      const html = workouts.length
        ? workouts.map((w) => `
          <div class="list-item">
            <div class="list-item-info">
              <h4>${w.name}</h4>
              <p>${w.date} • ${w.duration} minutes</p>
            </div>
            <button class="btn btn-small btn-danger" type="button" onclick="deleteWorkout('${w.id}')">Delete</button>
          </div>
        `).join("")
        : '<div class="empty-state"><p>No workouts yet</p></div>';

      document.getElementById("workoutsList").innerHTML = html;
    } catch (e) {
      showMessage("Failed to load workouts", "error");
    }
  }

  async function loadMeals() {
    try {
      const res = await window.api.request("/meals");

      if (!res?.success && res?.status === 405) {
        showMessage("Meals endpoint not enabled. Contact admin.", "error");
        document.getElementById("mealsList").innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
        return;
      }

      const meals = res?.data || [];
      const html = meals.length
        ? meals.map((m) => `
          <div class="list-item">
            <div class="list-item-info">
              <h4>${m.name}</h4>
              <p>${m.meal_type} • ${m.calories} cal</p>
            </div>
            <button class="btn btn-small btn-danger" type="button" onclick="deleteMeal('${m.id}')">Delete</button>
          </div>
        `).join("")
        : '<div class="empty-state"><p>No meals logged</p></div>';

      document.getElementById("mealsList").innerHTML = html;
    } catch (e) {
      showMessage("Failed to load meals", "error");
    }
  }

  async function loadGoals() {
    try {
      const res = await window.api.request("/goals");

      if (!res?.success && res?.status === 405) {
        showMessage("Goals endpoint not enabled. Contact admin.", "error");
        document.getElementById("goalsList").innerHTML = '<div class="empty-state"><p>Endpoint not available</p></div>';
        return;
      }

      const goals = res?.data || [];
      const html = goals.length
        ? goals.map((g) => `
          <div class="list-item">
            <div class="list-item-info">
              <h4>${g.title}</h4>
              <p>Target: ${g.target_date}</p>
            </div>
            <div class="list-item-actions">
              <span class="badge ${g.status === 'completed' ? 'badge-success' : 'badge-warning'}">${g.status}</span>
              <button class="btn btn-small btn-danger" type="button" onclick="deleteGoal('${g.id}')">Delete</button>
            </div>
          </div>
        `).join("")
        : '<div class="empty-state"><p>No goals set</p></div>';

      document.getElementById("goalsList").innerHTML = html;
    } catch (e) {
      showMessage("Failed to load goals", "error");
    }
  }

  async function createWorkout(e) {
    e.preventDefault();
    const data = {
      name: document.getElementById("workoutName").value.trim(),
      date: document.getElementById("workoutDate").value,
      duration: parseInt(document.getElementById("workoutDuration").value, 10),
      notes: document.getElementById("workoutNotes").value.trim(),
    };

    const res = await window.api.request("/workouts", { method: "POST", body: JSON.stringify(data) });
    if (res?.success) {
      showMessage("Workout created!", "success");
      e.target.reset();
      setDefaultDate();
      loadWorkouts();
      loadDashboard();
    } else {
      showMessage(res?.message || "Error creating workout", "error");
    }
  }

  async function createMeal(e) {
    e.preventDefault();
    const data = {
      name: document.getElementById("mealName").value.trim(),
      calories: parseInt(document.getElementById("mealCalories").value, 10),
      meal_type: document.getElementById("mealType").value,
    };

    const res = await window.api.request("/meals", { method: "POST", body: JSON.stringify(data) });
    if (res?.success) {
      showMessage("Meal logged!", "success");
      e.target.reset();
      loadMeals();
      loadDashboard();
    } else {
      showMessage(res?.message || "Error logging meal", "error");
    }
  }

  async function createGoal(e) {
    e.preventDefault();
    const data = {
      title: document.getElementById("goalTitle").value.trim(),
      description: document.getElementById("goalDescription").value.trim(),
      target_date: document.getElementById("goalDate").value,
      status: document.getElementById("goalStatus").value,
    };

    const res = await window.api.request("/goals", { method: "POST", body: JSON.stringify(data) });
    if (res?.success) {
      showMessage("Goal created!", "success");
      e.target.reset();
      setDefaultDate();
      loadGoals();
      loadDashboard();
    } else {
      showMessage(res?.message || "Error creating goal", "error");
    }
  }

  async function handleImageUpload(file) {
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
      document.getElementById("previewImg").src = e.target.result;
      document.getElementById("preview").classList.remove("hidden");
    };
    reader.readAsDataURL(file);

    // Upload
    const formData = new FormData();
    formData.append("image", file);

    const res = await window.api.request("/ml/identify-equipment", {
      method: "POST",
      body: formData,
    });

    if (res?.success) {
      const equipment = res.data || res;
      document.getElementById("machineName").textContent = equipment.equipment_name || "Unknown Equipment";
      document.getElementById("confidenceScore").textContent =
        Math.round((equipment.confidence || 0) * 100) + "%";
      document.getElementById("predictionResult").classList.remove("hidden");
      showMessage("Equipment identified!", "success");
    } else {
      showMessage(res?.message || "Failed to identify equipment", "error");
    }
  }

  // Init on page load
  document.addEventListener("DOMContentLoaded", () => {
    setDefaultDate();
    loadDashboard();

    // Nav links
    document.querySelectorAll(".nav-link").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const tab = a.getAttribute("data-tab");
        activateTab(tab);

        if (tab === "dashboard") loadDashboard();
        if (tab === "exercises") loadExercises();
        if (tab === "workouts") loadWorkouts();
        if (tab === "meals") loadMeals();
        if (tab === "goals") loadGoals();
      });
    });

    // Forms
    const workoutForm = document.getElementById("workoutForm");
    const mealForm = document.getElementById("mealForm");
    const goalForm = document.getElementById("goalForm");

    if (workoutForm) workoutForm.addEventListener("submit", createWorkout);
    if (mealForm) mealForm.addEventListener("submit", createMeal);
    if (goalForm) goalForm.addEventListener("submit", createGoal);

    // Exercise filters
    const exerciseSearch = document.getElementById("exerciseSearch");
    const muscleFilter = document.getElementById("muscleFilter");
    if (exerciseSearch) exerciseSearch.addEventListener("input", loadExercises);
    if (muscleFilter) muscleFilter.addEventListener("change", loadExercises);

    // Image upload
    const uploadBox = document.getElementById("uploadBox");
    const imageInput = document.getElementById("imageInput");
    
    if (uploadBox && imageInput) {
      uploadBox.addEventListener("click", () => imageInput.click());
      imageInput.addEventListener("change", () => handleImageUpload(imageInput.files[0]));

      // Drag & drop
      uploadBox.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = "var(--primary)";
      });
      uploadBox.addEventListener("dragleave", () => {
        uploadBox.style.borderColor = "var(--border)";
      });
      uploadBox.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = "var(--border)";
        const file = e.dataTransfer.files?.[0];
        handleImageUpload(file);
      });
    }

    // Add to workout button
    const addBtn = document.getElementById("addToWorkoutBtn");
    if (addBtn) {
      addBtn.addEventListener("click", () => {
        activateTab("workouts");
        loadWorkouts();
      });
    }

    // Logout
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        window.api.clearToken();
        window.location.href = "index.html";
      });
    }
  });

  // Global functions for delete operations
  window.deleteWorkout = async (id) => {
    if (!confirm("Delete this workout?")) return;
    const res = await window.api.request(`/workouts/${id}`, { method: "DELETE" });
    if (res?.success) {
      showMessage("Workout deleted", "success");
      loadWorkouts();
    } else {
      showMessage(res?.message || "Failed to delete", "error");
    }
  };

  window.deleteMeal = async (id) => {
    if (!confirm("Delete this meal?")) return;
    const res = await window.api.request(`/meals/${id}`, { method: "DELETE" });
    if (res?.success) {
      showMessage("Meal deleted", "success");
      loadMeals();
    } else {
      showMessage(res?.message || "Failed to delete", "error");
    }
  };

  window.deleteGoal = async (id) => {
    if (!confirm("Delete this goal?")) return;
    const res = await window.api.request(`/goals/${id}`, { method: "DELETE" });
    if (res?.success) {
      showMessage("Goal deleted", "success");
      loadGoals();
    } else {
      showMessage(res?.message || "Failed to delete", "error");
    }
  };
})();
