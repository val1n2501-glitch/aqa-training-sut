"use strict";
const byId = (id) => document.getElementById(id);
const statuses = {todo: "К выполнению", in_progress: "В работе", done: "Выполнено"};
const priorities = {low: "Низкий", medium: "Средний", high: "Высокий"};
const limit = 20;
let offset = 0;
let listVersion = 0;
let editingId = null;
let deletingId = null;
let appliedFilters = new URLSearchParams(new FormData(byId("filters")));

function message(id, text = "") {
  byId(id).textContent = text;
  byId(id).hidden = !text;
}
async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(path, {...options, signal: controller.signal});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = body.error;
      const details = (error?.details || []).map((item) => `${item.loc.join(".")}: ${item.message}`).join("; ");
      throw new Error(`${error?.message || "Ошибка API"} (${response.status})${details ? ": " + details : ""}`);
    }
    return response.status === 204 ? null : await response.json();
  } catch (error) {
    if (error.name === "AbortError") throw new Error("API не ответил за 10 секунд.");
    if (error instanceof TypeError) throw new Error("Не удалось связаться с API. Проверьте подключение.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
function json(method, data) {
  return {method, headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)};
}
function formData(form) {
  const data = Object.fromEntries(new FormData(form));
  data.due_date = data.due_date || null;
  return data;
}
function element(tag, text, testId) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (testId) node.dataset.testid = testId;
  return node;
}
function taskCard(task) {
  const card = element("article", undefined, `task-item-${task.id}`);
  card.className = "task";
  card.append(element("h3", task.title, `task-title-${task.id}`));
  if (task.description) card.append(element("p", task.description, `task-description-${task.id}`));
  const meta = element("p");
  meta.className = "meta";
  meta.append(element("span", statuses[task.status], `task-status-${task.id}`), " · ",
    element("span", priorities[task.priority], `task-priority-${task.id}`),
    ` · #${task.id} · Срок: ${task.due_date || "не задан"}`);
  card.append(meta);
  const actions = element("div");
  actions.className = "actions";
  const statusLabel = element("label", "Изменить статус");
  const select = element("select", undefined, `change-status-${task.id}`);
  for (const [value, label] of Object.entries(statuses)) select.add(new Option(label, value));
  select.value = task.status;
  select.addEventListener("change", () => mutate(select, async () => {
    try { await request(`/api/tasks/${task.id}`, json("PATCH", {status: select.value})); }
    catch (error) { select.value = task.status; throw error; }
  }, "Статус обновлён"));
  statusLabel.append(select);
  const edit = element("button", "Изменить", `edit-task-${task.id}`);
  edit.addEventListener("click", () => {
    editingId = task.id;
    for (const key of ["title", "description", "status", "priority", "due_date"]) {
      byId("edit-form").elements.namedItem(key).value = task[key] ?? "";
    }
    message("edit-error");
    byId("edit-dialog").showModal();
  });
  const remove = element("button", "Удалить", `delete-task-${task.id}`);
  remove.className = "danger";
  remove.addEventListener("click", () => {
    deletingId = task.id;
    byId("delete-title").textContent = task.title;
    message("delete-error");
    byId("delete-dialog").showModal();
  });
  actions.append(statusLabel, edit, remove);
  card.append(actions);
  return card;
}
async function loadTasks() {
  const version = ++listVersion;
  byId("loading").hidden = false;
  byId("empty").hidden = true;
  byId("previous").disabled = true;
  byId("next").disabled = true;
  const params = new URLSearchParams(appliedFilters);
  for (const [key, value] of [...params]) if (!value) params.delete(key);
  params.set("limit", limit);
  params.set("offset", offset);
  try {
    const data = await request(`/api/tasks?${params}`);
    if (version !== listVersion) return;
    if (offset > 0 && offset >= data.total) {
      offset = Math.max(0, Math.floor((data.total - 1) / limit) * limit);
      return await loadTasks();
    }
    byId("task-list").replaceChildren(...data.items.map(taskCard));
    byId("empty").hidden = data.items.length !== 0;
    byId("page-info").textContent = `Всего: ${data.total} · Страница ${Math.floor(offset / limit) + 1}`;
    byId("previous").disabled = offset === 0;
    byId("next").disabled = offset + limit >= data.total;
  } catch (error) {
    if (version === listVersion) {
      byId("task-list").replaceChildren();
      byId("page-info").textContent = "";
      message("error", error.message);
    }
  } finally {
    if (version === listVersion) byId("loading").hidden = true;
  }
}
async function mutate(control, action, success, dialogError) {
  if (control.disabled) return;
  control.disabled = true;
  message("error");
  message("success");
  if (dialogError) message(dialogError);
  try {
    await action();
    message("success", success);
    await loadTasks();
  } catch (error) {
    message(dialogError || "error", error.message);
  } finally {
    control.disabled = false;
  }
}
byId("create-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  mutate(form.querySelector("button"), async () => {
    await request("/api/tasks", json("POST", formData(form)));
    form.reset();
  }, "Задача создана");
});
byId("edit-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  mutate(form.querySelector("button"), async () => {
    await request(`/api/tasks/${editingId}`, json("PUT", formData(form)));
    byId("edit-dialog").close();
  }, "Задача обновлена", "edit-error");
});
byId("confirm-delete").addEventListener("click", (event) => mutate(event.currentTarget, async () => {
  await request(`/api/tasks/${deletingId}`, {method: "DELETE"});
  byId("delete-dialog").close();
}, "Задача удалена", "delete-error"));
byId("cancel-edit").addEventListener("click", () => byId("edit-dialog").close());
byId("cancel-delete").addEventListener("click", () => byId("delete-dialog").close());
byId("filters").addEventListener("submit", (event) => {
  event.preventDefault();
  appliedFilters = new URLSearchParams(new FormData(event.currentTarget));
  offset = 0;
  message("error");
  message("success");
  loadTasks();
});
byId("previous").addEventListener("click", () => { offset -= limit; loadTasks(); });
byId("next").addEventListener("click", () => { offset += limit; loadTasks(); });
loadTasks();
