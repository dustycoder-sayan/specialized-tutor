const $ = (s) => document.querySelector(s);
const state = { id: null, busy: false };

const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1];
const headers = () => ({ "Content-Type": "application/json", "X-CSRFToken": csrf() });
const render = (el, md) => { el.innerHTML = DOMPurify.sanitize(marked.parse(md)); };

function addMessage(role, text = "") {
  $("#empty")?.remove();
  const row = document.createElement("div");
  row.className = `row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "assistant") render(bubble, text); else bubble.textContent = text;
  row.append(bubble);
  $("#messages").append(row);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return bubble;
}

async function loadHistory() {
  const { conversations } = await (await fetch("/api/conversations/")).json();
  const nav = $("#history");
  nav.replaceChildren(...conversations.map((c) => {
    const item = document.createElement("div");
    item.className = "item" + (c.id === state.id ? " active" : "");
    const open = Object.assign(document.createElement("button"), { className: "open", textContent: c.title });
    open.onclick = () => openConversation(c.id);
    const del = Object.assign(document.createElement("button"), { className: "del", textContent: "Delete", ariaLabel: `Delete ${c.title}` });
    del.onclick = () => removeConversation(c.id);
    item.append(open, del);
    return item;
  }));
}

async function openConversation(id) {
  const data = await (await fetch(`/api/conversations/${id}/`)).json();
  state.id = id;
  $("#messages").replaceChildren();
  data.messages.forEach((m) => addMessage(m.role, m.content));
  $("#title").textContent = data.title;
  document.body.classList.remove("open");
  loadHistory();
}

async function removeConversation(id) {
  await fetch(`/api/conversations/${id}/`, { method: "DELETE", headers: headers() });
  if (id === state.id) newChat(); else loadHistory();
}

function newChat() {
  state.id = null;
  location.reload();
}

async function send(text) {
  state.busy = true; $("#send").disabled = true;
  addMessage("user", text);
  const bubble = addMessage("assistant");
  bubble.classList.add("typing");
  let answer = "";

  const handle = (e) => {
    if (e.type === "meta") { state.id = e.conversation_id; $("#title").textContent = e.title; }
    else if (e.type === "token") { answer += e.text; render(bubble, answer); $("#messages").scrollTop = $("#messages").scrollHeight; }
    else if (e.type === "error") { bubble.parentElement.classList.add("error"); bubble.textContent = e.message; }
  };

  try {
    const res = await fetch("/api/chat/", { method: "POST", headers: headers(), body: JSON.stringify({ conversation_id: state.id, message: text }) });
    const reader = res.body.getReader(), decoder = new TextDecoder();
    let pending = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      pending += decoder.decode(value, { stream: true });
      const lines = pending.split("\n");
      pending = lines.pop();
      lines.filter(Boolean).forEach((l) => handle(JSON.parse(l)));
    }
  } catch {
    handle({ type: "error", message: "Connection lost. Check your network and try again." });
  } finally {
    bubble.classList.remove("typing");
    state.busy = false; $("#send").disabled = false; $("#input").focus();
    loadHistory();
  }
}

$("#composer").onsubmit = (e) => {
  e.preventDefault();
  const text = $("#input").value.trim();
  if (!text || state.busy) return;
  $("#input").value = ""; $("#input").style.height = "auto";
  send(text);
};
$("#input").onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#composer").requestSubmit(); } };
$("#input").oninput = (e) => { e.target.style.height = "auto"; e.target.style.height = e.target.scrollHeight + "px"; };
$("#new-chat").onclick = newChat;
$("#toggle").onclick = () => document.body.classList.toggle("open");
document.querySelectorAll(".starters button").forEach((b) => (b.onclick = () => send(b.textContent)));
loadHistory();
