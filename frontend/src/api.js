let API_BASE = import.meta.env.VITE_API_URL;
if (!API_BASE) {
  if (import.meta.env.DEV) {
    API_BASE = "http://localhost:8000";
  } else {
    console.error("VITE_API_URL is not defined in production environment!");
    API_BASE = "";
  }
}
if (API_BASE && !API_BASE.startsWith("http://") && !API_BASE.startsWith("https://")) {
  API_BASE = `https://${API_BASE}`;
}

function getHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    });

    if (response.status === 401) {
      localStorage.removeItem("token");
      window.location.reload();
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Request failed");
    }

    window.dispatchEvent(new CustomEvent("backend-status", { detail: { online: true } }));
    return response.json();
  } catch (err) {
    if (err.message && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError") || err.message.includes("Load failed") || err.message.includes("Failed to execute 'fetch'"))) {
      window.dispatchEvent(new CustomEvent("backend-status", { detail: { online: false } }));
    }
    throw err;
  }
}

export const api = {
  async login(email, password) {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Incorrect email or password");
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      window.dispatchEvent(new CustomEvent("backend-status", { detail: { online: true } }));
      return data;
    } catch (err) {
      if (err.message && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError") || err.message.includes("Load failed") || err.message.includes("Failed to execute 'fetch'"))) {
        window.dispatchEvent(new CustomEvent("backend-status", { detail: { online: false } }));
      }
      throw err;
    }
  },

  async register(email, password, fullName, organizationName) {
    const data = await request("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        organization_name: organizationName,
      }),
    });
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
    }
    return data;
  },

  logout() {
    localStorage.removeItem("token");
  },

  isAuthenticated() {
    return !!localStorage.getItem("token");
  },

  getMe() {
    return request("/auth/me");
  },

  getDashboardSummary() {
    return request("/dashboard/summary");
  },

  getProjects() {
    return request("/projects");
  },

  createProject(name) {
    return request("/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  getQueues(projectId) {
    const url = projectId ? `/queues?project_id=${projectId}` : "/queues";
    return request(url);
  },

  createQueue(projectId, name, description, priority, maxConcurrency) {
    return request("/queues", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        name,
        description,
        priority,
        max_concurrency: maxConcurrency,
      }),
    });
  },

  pauseQueue(queueId) {
    return request(`/queues/${queueId}/pause`, { method: "POST" });
  },

  resumeQueue(queueId) {
    return request(`/queues/${queueId}/resume`, { method: "POST" });
  },

  getQueueStats(queueId) {
    return request(`/queues/${queueId}/stats`);
  },

  getJobs({ projectId, queueId, status, priority, search, limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (projectId) params.append("project_id", projectId);
    if (queueId) params.append("queue_id", queueId);
    if (status) params.append("status", status);
    if (priority !== undefined) params.append("priority", priority);
    if (search) params.append("search", search);
    params.append("limit", limit);
    params.append("offset", offset);

    return request(`/jobs?${params.toString()}`);
  },

  createJob(projectId, queueName, taskName, payload, priority, delay = null) {
    const jobPayload = { ...payload };
    if (delay !== null) {
      jobPayload.delay = delay;
    }
    return request("/jobs", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        queue_name: queueName,
        task_name: taskName,
        payload: jobPayload,
        priority: parseInt(priority),
      }),
    });
  },

  getJobDetails(jobId) {
    return request(`/jobs/${jobId}`);
  },

  getJobExecutions(jobId) {
    return request(`/jobs/${jobId}/executions`);
  },

  getJobLogs(jobId) {
    return request(`/jobs/${jobId}/logs`);
  },

  retryJob(jobId) {
    return request(`/jobs/${jobId}/retry`, { method: "POST" });
  },

  cancelJob(jobId) {
    return request(`/jobs/${jobId}/cancel`, { method: "POST" });
  },

  getWorkers() {
    return request("/workers");
  },

  getDLQJobs() {
    return request("/dlq");
  },

  retryDLQJob(dlqJobId) {
    return request(`/dlq/${dlqJobId}/retry`, { method: "POST" });
  },

  getWorkflows() {
    return request("/workflows");
  },

  createWorkflow(projectId, name, description, jobs, dependencies) {
    return request("/workflows", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        name,
        description,
        jobs,
        dependencies,
      }),
    });
  },

  getWorkflowDetails(workflowId) {
    return request(`/workflows/${workflowId}`);
  },

  getFailureAnalysis(jobId) {
    return request(`/jobs/${jobId}/failure-analysis`);
  },
};
