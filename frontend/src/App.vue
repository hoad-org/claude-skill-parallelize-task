<template>
  <div id="app" :class="{ 'dark-mode': darkMode }">
    <nav class="navbar">
      <div class="navbar-brand">
        <h1>Parallelize-Task</h1>
      </div>
      <ul class="nav-links">
        <li><router-link to="/">Dashboard</router-link></li>
        <li><router-link to="/workflows">Workflows</router-link></li>
        <li><router-link to="/analysis">Analysis</router-link></li>
        <li><router-link to="/decisions">Decisions</router-link></li>
        <li><router-link to="/execution">Execution</router-link></li>
        <li><router-link to="/monitoring">Monitoring</router-link></li>
        <li><router-link to="/performance">Performance</router-link></li>
      </ul>
      <div class="nav-controls">
        <button class="theme-toggle" @click="toggleDarkMode">
          {{ darkMode ? '☀️' : '🌙' }}
        </button>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="app-footer">
      <p>&copy; 2024 Parallelize-Task. All rights reserved.</p>
      <p class="version">v1.1.0</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useMonitoringStore } from './stores/monitoringStore'

const darkMode = ref(false)
const monitoringStore = useMonitoringStore()

onMounted(() => {
  monitoringStore.startPeriodicFetch(5000)
  darkMode.value = localStorage.getItem('darkMode') === 'true'
})

const toggleDarkMode = () => {
  darkMode.value = !darkMode.value
  localStorage.setItem('darkMode', darkMode.value)
}

onUnmounted(() => {
  // Cleanup if needed
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  color: #333;
  background: #f5f5f5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s ease;
}

#app.dark-mode {
  color: #e0e0e0;
  background: #1a1a1a;
}

.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand h1 {
  font-size: 1.5rem;
  margin: 0;
}

.nav-links {
  list-style: none;
  display: flex;
  gap: 2rem;
  flex: 1;
  margin: 0 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background-color: #34495e;
}

.nav-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.theme-toggle {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.theme-toggle:hover {
  background-color: #34495e;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: #2c3e50;
  color: white;
  text-align: center;
  padding: 1.5rem;
  margin-top: 2rem;
}

.app-footer p {
  margin: 0.25rem 0;
}

.version {
  font-size: 0.85rem;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
  }

  .nav-links {
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0 0 0;
    width: 100%;
  }

  .main-content {
    padding: 1rem;
  }
}
</style>
