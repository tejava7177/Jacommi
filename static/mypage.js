// /static/mypage.js
function getCsrfToken() {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".btn-delete"); // 템플릿의 클래스와 동일
  if (!btn) return;

  const id = Number(btn.dataset.id);
  if (!id) return;
  if (!confirm("이 문장을 삭제할까요?")) return;

  try {
    // ✅ 경로 파라미터 + 끝 슬래시
    const res = await fetch(`/api/sentences/delete/${id}/`, {
      method: "POST",
      headers: { "X-CSRFToken": getCsrfToken() },
    });

    if (res.ok) {
      document.querySelector(`.sentence[data-id="${id}"]`)?.remove();
    } else if (res.status === 404) {
      alert("이미 삭제되었거나 권한이 없어요.");
    } else if (res.status === 401) {
      alert("로그인이 필요합니다.");
    } else {
      const data = await res.json().catch(() => ({}));
      console.error("delete error:", data);
      alert("삭제에 실패했습니다.");
    }
  } catch (err) {
    console.error(err);
    alert("삭제 요청 중 오류가 발생했습니다.");
  }
});