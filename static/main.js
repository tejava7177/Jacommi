// /static/main.js
// 1) Firebase SDK 모듈 로드
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js";

// 2) 네가 제공한 firebaseConfig
const firebaseConfig = {
  apiKey: "AIzaSyCbwo-yB-TT2kL02iuidq8rK88CPaYaI6w",
  authDomain: "jacommi-2a250.firebaseapp.com",
  projectId: "jacommi-2a250",
  storageBucket: "jacommi-2a250.firebasestorage.app",
  messagingSenderId: "836824860779",
  appId: "1:836824860779:web:e95b568119b5ff0498092e",
  measurementId: "G-NLS1JQL6Y7"
};

// 3) 앱 초기화
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// 4) 서비스워커 등록 (static 경로에 두겠습니다)
async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return null;
  return await navigator.serviceWorker.register("/static/firebase-messaging-sw.js");
}

// 5) 권한 + 토큰 발급 + 서버 등록
async function registerFCM() {
  try {
    const swReg = await registerServiceWorker();

    // 알림 권한 요청
    if (Notification.permission !== "granted") {
      const perm = await Notification.requestPermission();
      if (perm !== "granted") {
        console.warn("🔕 Notification permission not granted.");
        return;
      }
    }

    // 네가 생성한 VAPID 공개키를 여기에 넣음
    const VAPID_KEY = "BPgK3il-_LrOiCyil_YifSDPXMwoDPsnsWZHU30OIZC4MxU773qa7KH95WgAaZ9wjjwfodc0QTGS3iolV1vVbn0";

    // 토큰 발급 (서비스워커와 함께)
    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: swReg || undefined,
    });

    if (!token) {
      console.warn("❌ Failed to get FCM token.");
      return;
    }
    console.log("✅ FCM token:", token);

    // 서버에 토큰 등록 (이미 /api/fcm/register 뷰가 있음)
    await fetch("/api/fcm/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });

  } catch (err) {
    console.error("❌ FCM registration failed:", err);
  }
}

// 6) 포그라운드 메시지 수신 시 브라우저 알림
onMessage(messaging, (payload) => {
  console.log("📩 Foreground message:", payload);
  const n = payload.notification || {};
  const title = n.title || payload.data?.title || "오늘의 일본어";
  const body  = n.body  || payload.data?.body  || "새 문장을 확인해보세요";

  // 포그라운드에서도 확실히 알림을 띄우기 위해 Notification API 사용
  if (Notification.permission === "granted") {
    new Notification(title, { body });
  }
});

// 실행
registerFCM();

// (기존 PWA 등록 로직이 있다면 함께 유지)
if ("serviceWorker" in navigator) {
  // 이미 today.html에 /static/service-worker.js를 등록했다면 그대로 두세요
}