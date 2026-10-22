# 📱 폰용 매크로 대시보드 — GitHub Pages 배포

매주 자동으로 대시보드를 재생성해 GitHub Pages에 올리고, 폰 홈 화면에 앱처럼 설치합니다.
**ECOS 키는 코드에 없습니다** — GitHub 저장소 Secret으로만 주입됩니다(공개돼도 안전).

로컬은 이미 `git` 초기화 + 최초 커밋까지 되어 있습니다. 아래 순서만 따라 하세요.

---

## 1. GitHub에 저장소 만들기 (공개)
1. https://github.com/new 접속
2. Repository name: **`macro-dashboard`** (원하는 이름 가능)
3. **Public** 선택 → *(공개 저장소라야 Actions 사용시간 무제한)*
4. README/.gitignore 체크 **해제** (이미 로컬에 있음) → **Create repository**

## 2. 로컬 → GitHub 푸시
프로젝트 폴더(`D:\Claude code\경제지표설계`)에서:
```bash
git remote add origin https://github.com/lsh99y-boop/macro-dashboard.git
git push -u origin main
```
*(저장소 이름을 다르게 지었으면 URL도 맞춰 바꾸세요.)*

## 3. ECOS 키를 Secret으로 등록 ⚠️ 필수
저장소 페이지 → **Settings → Secrets and variables → Actions → New repository secret**
- Name: **`ECOS_KEY`**
- Secret: 본인 ECOS 키 (로컬 `.ecos_key` 파일에 저장된 값 그대로)
- **Add secret**

> 키 원문은 이 문서에 적지 않았습니다(공개 저장소 유출 방지). `.ecos_key` 파일을 열어 복사하세요.

## 4. Pages 켜기
저장소 **Settings → Pages → Build and deployment → Source: `GitHub Actions`** 선택.

## 5. 첫 빌드 실행
**Actions** 탭 → 좌측 **Build & Deploy Macro Dashboard** → **Run workflow** → **Run**.
2~3분 뒤 초록 체크가 뜨면 완료. (이후 매주 월요일 자동 실행 + 코드 push 시에도 실행)

## 6. 폰에서 열고 설치
주소: **`https://lsh99y-boop.github.io/macro-dashboard/`**
*(사용자명/저장소명에 맞게)*

- **아이폰(Safari)**: 주소 열기 → 공유 → **홈 화면에 추가**
- **안드로이드(Chrome)**: 주소 열기 → ⋮ → **홈 화면에 추가 / 앱 설치**

홈 화면 아이콘으로 실행되고, 한 번 열어두면 **오프라인에서도** 마지막 화면이 보입니다.

---

## 갱신 & "잠금" 관련
- **공개 저장소 = Actions 무제한.** 횟수·비용으로 잠기지 않습니다.
- 데이터는 **월간**이라 주 1회 자동이면 충분. 즉시 최신을 원하면 **Actions → Run workflow**.
- ⚠️ **유일한 주의**: 예약(cron)은 저장소에 **60일간 커밋이 없으면 자동 일시정지**됩니다.
  GitHub가 메일로 알려주며, **Actions 탭에서 "Enable workflow" 한 번**이면 재개됩니다.
  (또는 아무 때나 Run workflow 하면 유지)

## 비공개로 하고 싶으면
저장소를 Private로 만들면 URL이 공개되지 않지만, **GitHub Pages는 Private 저장소에서
유료(Pro 이상)** 입니다. 무료로 비공개를 원하면 다른 호스팅(예: Cloudflare Access)이 필요 —
필요 시 말씀해 주세요.
