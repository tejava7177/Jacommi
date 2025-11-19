// /static/firebase-messaging-sw.js
// ※ 파일 위치를 /static/ 아래에 두고, main.js에서 그 경로로 register 했습니다.
importScripts("https://www.gstatic.com/firebasejs/9.6.11/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/9.6.11/firebase-messaging-compat.js");

// 네가 준 firebaseConfig 동일하게 사용
firebase.initializeApp({
  apiKey: "AIzaSyCbwo-yB-TT2kL02iuidq8rK88CPaYaI6w",
  authDomain: "jacommi-2a250.firebaseapp.com",
  projectId: "jacommi-2a250",
  storageBucket: "jacommi-2a250.firebasestorage.app",
  messagingSenderId: "836824860779",
  appId: "1:836824860779:web:e95b568119b5ff0498092e",
  measurementId: "G-NLS1JQL6Y7"
});

const messaging = firebase.messaging();

// 백그라운드 수신 시 알림 표시
messaging.onBackgroundMessage((payload) => {
  console.log("[SW] background message:", payload);
  const n = (payload && payload.notification) || {};
  const title = n.title || (payload.data && payload.data.title) || "오늘의 일본어";
  const body  = n.body  || (payload.data && payload.data.body)  || "새 문장을 확인해보세요";
  self.registration.showNotification(title, { body });
});