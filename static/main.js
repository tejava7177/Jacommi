// /static/main.js
// --- Firebase SDK (ESM) ---
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getMessaging, getToken, onMessage, deleteToken } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js";

// --- Firebase config ---
const firebaseConfig = {
  apiKey: "AIzaSyCbwo-yB-TT2kL02iuidq8rK88CPaYaI6w",
  authDomain: "jacommi-2a250.firebaseapp.com",
  projectId: "jacommi-2a250",
  storageBucket: "jacommi-2a250.firebasestorage.app",
  messagingSenderId: "836824860779",
  appId: "1:836824860779:web:e95b568119b5ff0498092e",
  measurementId: "G-NLS1JQL6Y7",
};
const VAPID_KEY =
  "BPgK3il-_LrOiCyil_YifSDPXMwoDPsnsWZHU30OIZC4MxU773qa7KH95WgAaZ9wjjwfodc0QTGS3iolV1vVbn0";

// --- Firebase init ---
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// --- DOM helpers ---
const $ = (sel) => document.querySelector(sel);
const notifBtn = $("#notifToggle");
const saveCalBtn = $("#saveTodayBtn");
const LS_TOKEN_KEY = "fcm_token";

const setBell = (on) => {
  if (!notifBtn) return;
  notifBtn.classList.toggle("on", !!on);
  notifBtn.classList.toggle("off", !on);
  notifBtn.setAttribute("aria-pressed", on ? "true" : "false");
  notifBtn.title = on ? "알림 켜짐" : "알림 꺼짐";
};

// --- CSRF helper (same-origin POST 시 권장) ---
function getCsrfToken() {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

// ---- Sentence saving helpers ----
async function saveSentence(payload) {
  const res = await fetch("/api/sentences/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  return { res, data };
}

function markSaved(btn, created) {
  if (!btn) return;
  btn.textContent = created ? "★ 저장됨" : "★ 저장됨(갱신)";
  btn.classList.add("saved");
  btn.setAttribute("aria-pressed", "true");
  btn.setAttribute("aria-disabled", "true");
  btn.disabled = true;
}

// ---- Service Worker register ----
async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return null;
  try {
    // 정적 경로에 sw 파일 존재 필요
    return await navigator.serviceWorker.register("/static/firebase-messaging-sw.js");
  } catch (e) {
    console.warn("ServiceWorker register failed:", e);
    return null;
  }
}

// ---- Subscribe (permission + token + server register) ----
async function subscribeNotifications() {
  const swReg = await registerServiceWorker();

  // 1) 권한 요청
  if (Notification.permission !== "granted") {
    const perm = await Notification.requestPermission();
    if (perm !== "granted") {
      setBell(false);
      return { ok: false, reason: "permission_denied" };
    }
  }

  // 2) FCM 토큰 발급
  const token = await getToken(messaging, {
    vapidKey: VAPID_KEY,
    serviceWorkerRegistration: swReg || undefined,
  }).catch((e) => {
    console.error("getToken failed:", e);
    return null;
  });
  if (!token) {
    setBell(false);
    return { ok: false, reason: "token_failed" };
  }

  // 3) 서버 등록
  try {
    await fetch("/api/fcm/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ token }),
    });
  } catch (e) {
    console.warn("Token register API failed:", e);
    // 서버 에러여도 로컬 상태는 유지
  }
  localStorage.setItem(LS_TOKEN_KEY, token);
  setBell(true);
  console.log("✅ FCM token:", token);
  return { ok: true, token };
}

// ---- Unsubscribe (delete token + server unregister) ----
async function unsubscribeNotifications() {
  const curr = localStorage.getItem(LS_TOKEN_KEY);
  try {
    await deleteToken(messaging);
  } catch (e) {
    console.warn("deleteToken failed:", e);
  }
  // 서버 토큰 해제 (없으면 404 무시)
  try {
    await fetch("/api/fcm/unregister", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ token: curr }),
    }).catch(() => {});
  } catch {}
  localStorage.removeItem(LS_TOKEN_KEY);
  setBell(false);
  return { ok: true };
}

// ---- Foreground message -> Notification ----
onMessage(messaging, (payload) => {
  console.log("📩 Foreground message:", payload);
  const n = payload.notification || {};
  const title = n.title || payload.data?.title || "오늘의 일본어";
  const body = n.body || payload.data?.body || "새 문장을 확인해보세요";
  if (Notification.permission === "granted") {
    new Notification(title, { body });
  }
});

// ---- Button wiring ----
function wireButtons() {
  // 초기 벨 상태
  const hasToken = !!localStorage.getItem(LS_TOKEN_KEY);
  setBell(Notification.permission === "granted" && hasToken);

  // 알림 토글
  if (notifBtn) {
    notifBtn.addEventListener("click", async () => {
      const isOn = notifBtn.classList.contains("on");
      if (isOn) {
        await unsubscribeNotifications();
      } else {
        await subscribeNotifications();
      }
    });
  }

  // "오늘 문장 캘린더에 저장" 버튼
  if (saveCalBtn) {
  saveCalBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/calendar/insert-today", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => ({}));

      if (res.status === 401) {
        alert("로그인이 필요해요. 오른쪽 상단에서 Google 로그인 후 다시 시도해주세요.");
        return;
      }
      if (res.status === 400 && data?.error === "google_not_linked") {
        alert("Google 연동이 필요해요. 로그인 버튼으로 Google 연결 후 다시 시도해주세요.");
        return;
      }
      // ✅ 중복 삽입 방지 메시지
      if (res.status === 409 || data?.error === "already_inserted") {
        alert("이미 오늘 내용은 작성했습니다.");
        return;
      }

      if (res.ok && (data.ok ?? true)) {
        alert("📅 오늘 문장을 캘린더에 저장했습니다.");
      } else {
        console.error("Calendar API error:", data);
        alert("캘린더 저장에 실패했습니다.");
      }
    } catch (e) {
      console.error(e);
      alert("캘린더 저장 요청 중 오류가 발생했습니다.");
    }
  });
}
}

// ---- Per-sentence "save" buttons ----
function wireSaveButtons() {
  const buttons = document.querySelectorAll(".save-sent-btn");
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    // Skip if already marked saved in prior interaction
    if (btn.dataset.bound === "1") return;
    btn.dataset.bound = "1";

    btn.addEventListener("click", async () => {
      // Prevent double clicks
      if (btn.disabled) return;

      const payload = {
        date: btn.dataset.date,
        topic: btn.dataset.topic || "",
        idx: Number(btn.dataset.idx || 0),
        jp: btn.dataset.jp || "",
        ko: btn.dataset.ko || "",
      };

      // simple guard
      if (!payload.date || !payload.jp) {
        alert("문장 정보가 올바르지 않습니다.");
        return;
      }

      try {
        btn.disabled = true;
        btn.classList.add("loading");

        const { res, data } = await saveSentence(payload);

        if (res.status === 401) {
          alert("로그인이 필요합니다. 우측 상단에서 Google 로그인 후 다시 시도하세요.");
          btn.disabled = false;
          btn.classList.remove("loading");
          return;
        }

        if (res.ok && (data.ok ?? true)) {
          // created: True(신규), False(기존 갱신)
          markSaved(btn, !!data.created);
        } else if (res.status === 409 || data?.error === "already_saved") {
          // 서버에서 중복 저장 방지 로직이 있다면 이 경로로 안내
          alert("이미 저장한 문장입니다.");
          markSaved(btn, false);
        } else {
          console.error("save API error:", data);
          alert("저장에 실패했습니다.");
          btn.disabled = false;
          btn.classList.remove("loading");
        }
      } catch (e) {
        console.error(e);
        alert("요청 중 오류가 발생했습니다.");
        btn.disabled = false;
        btn.classList.remove("loading");
      }
    });
  });
}

// DOM 준비 후 실행
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    wireButtons();
    wireSaveButtons();
  });
} else {
  wireButtons();
  wireSaveButtons();
}

// --- Backward compatibility (legacy global) ---
async function requestFcmPermissionAndRegister() {
  return await subscribeNotifications();
}
window.requestFcmPermissionAndRegister = requestFcmPermissionAndRegister;
window.initNotifications = requestFcmPermissionAndRegister;