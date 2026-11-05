# 끗한의원(홍대) 마케팅 작업 저장소

마케팅 담당(이경세 마케팅 연구소)이 끗한의원 홍대점을 위해 돌리는 세 갈래 작업이 한 폴더에 있다. 대화는 한국어로.

**git**: 원격 https://github.com/musicman0519-a11y/kkeut-hongdae-blog (비공개, `main` 하나). `.gitignore` 는 허용 목록 방식이라 `captures/`·`data/kkeut/`·루트 xlsx·pdf·gif 는 자동으로 빠진다. 커밋 전 `python -X utf8 -I scripts/repo_check.py`(환자·매출·캡처·토큰 검사) 통과가 필수. 커밋·푸시는 사용자가 요청할 때만, 메시지는 한국어 + Co-Authored-By. 도메인은 `https://hongdaekkeutclinic.com`(2026-11-05 구매, 기준 주소; 바꿀 때는 `scripts/set_domain.py <url>` → new_column → build → baseline). 호스팅은 Vercel(Root Directory `kkeut_seo_site`, 빌드 없음) — 연결 절차는 `docs/specs/domain-connect.md`.

| 갈래 | 코드 | 데이터·산출물 |
|---|---|---|
| SEO 사이트 (hongdaekkeutclinic.com) | `kkeut_seo_site/` (정적 HTML 21쪽, 배포되는 유일한 폴더), `kkeut_admin.html`(칼럼 발행 어드민, 루트), `scripts/magazine/build.py`(매거진 목록 생성) | `kkeut_seo_site/assets/`, `data/magazine/posts.json`(글 목록 원본) |
| 의료광고 월간 모니터링(경쟁 의원 27곳) | `scripts/admon/` | `data/admon/`, `captures/<YYYY-MM>/`, 루트의 `의료광고_병원별분석_*.xlsx` |
| 끗한의원 월간 마케팅 분석표 | `scripts/kkeut/` | `data/kkeut/<월>/`(환자 정보, 공유 금지), 루트의 `끗한의원_마케팅분석표_*.xlsx` |

명세는 `docs/specs/<기능>.md`, 작업 계획은 `docs/plans/<기능>.md` (/spec → /plan → /build 한 조각씩, 조각마다 보고하고 "계속" 을 기다린다). 루트의 PDF·md 는 의료광고법 자료.

## 사이트 (kkeut_seo_site/)
- 빌드 없음. Tailwind 는 **정적 CSS**(`assets/tailwind.css`, 2026-11-05 CDN 에서 전환): 색·글꼴 토큰은 `scripts/theme/tailwind.config.js`, 새 클래스를 쓰는 마크업을 추가했으면 `node scripts/theme/tailwind_extract.js` 로 재생성(Play CDN 을 헤드리스 크롬에서 돌려 21쪽+초안+어드민 템플릿의 클래스 합집합을 뽑음, 22KB). 재생성을 빠뜨리면 그 클래스만 스타일이 없다. Pretendard, Iconify 는 CDN. 공통 블록 원본은 `scripts/theme/{head,header,footer,floating}.html` 이고 21쪽에 같은 바이트로 들어가 있다. 블록을 고치면 **이 순서로**: `python -X utf8 -I scripts/apply_theme.py`(index 포함 16쪽 치환 + 옛 색 매핑, 드롭다운을 먼저 채움, 멱등, `--check`) → `scripts/magazine/build.py`(허브 5쪽을 columns.html 로 재생성) → `scripts/sync_admin_template.py`(어드민 buildPage 동기화) → `check_theme.py check` → `baseline`. 공통 스타일은 `kkeut_seo_site/assets/site.css`.
- 로고: 원본 .ai(바탕 화면 `01_클라이언트/끗한의원/끗_LOGO_원본.ai`, 세로형 심볼+한글만)에서 뽑은 벡터 `assets/logo-mark.svg`(심볼 769B)·`logo-kr.svg`(끗 한의원)·`logo-vertical.svg`. 헤더는 심볼 + Marcellus "KKEUT CLINIC"(HTML 텍스트) + 한글 SVG, 푸터는 심볼 + 한글. 옛 `logo.png`(440×84, 흐림)는 더 이상 참조하지 않는다.
- 배너 사진 교체: `python -X utf8 -I scripts/theme/banner_photo.py <사진> --slot hero|find [--focus "68% center"]` → `assets/home/{hero,find}.webp/.jpg`(+hero-m.webp 모바일) 생성과 index.html 의 `<picture data-slot>` 교체까지 한 번에(멱등). 원본은 `drafts/photos/` 에 보관. 옛 kkeut-left/right.jpg 는 시술 카드(안티에이징센터·흉터재생센터)에서 아직 쓴다.
- 색 토큰: rose `#E0507A`(강조) · pink · blush · pinksoft(배경) · ink `#181818`(글자) · kakao · naver. 글꼴: 본문 Pretendard, h1·h2 는 site.css 전역으로 Gowun Batang, 영문 장식은 `font-display`(Marcellus). 옛 클래스(`brandorange`, `card*`, `kpink*`)는 쓰지 않는다.
- 줄바꿈: 21쪽 전부 LF(기준선 확인). 스크립트로 고칠 때는 바이너리로 읽어 파일별 줄바꿈을 보존한다.
- 로컬 확인: `kkeut_seo_site/` 에서 `python -X utf8 -m http.server 8787 --bind 127.0.0.1` 을 백그라운드로 띄우고, 브라우저는 PowerShell `Start-Process "http://127.0.0.1:8787/index.html"` 로 연다. 새 세션이면 서버가 죽어 있으니 먼저 응답을 확인한다.
- 검증 도구(프로젝트 루트에서):
  - `python -X utf8 -I scripts/check_theme.py check` — 전 쪽 title·description·canonical·JSON-LD·내부 href·줄바꿈 불변, 공통 블록 md5 일치, 옛 색 클래스 0개, sitemap·robots 불변. 기준선은 `data/theme-baseline.json`(`baseline` 모드로 재저장).
  - `node scripts/theme/shot.js <url> <out.png> [폭=1280] [mobile=0|1] [fullPage=0|1]` — CDP 에뮬레이션 스크린샷 + 가로 넘침 요소 수 + 로드된 글꼴. 모바일은 반드시 이것으로(헤드리스 `--window-size` 는 가짜 넘침).
  - `node scripts/theme/metrics.js <url> [폭=390] [mobile=1]` — 4G·CPU 4배 느리게 해서 LCP·CLS·요청·KB. `npx lighthouse` 는 권한에 막혀 못 쓰므로 이것으로 전후 비교.
- 어드민 `kkeut_admin.html` 은 칼럼 템플릿(head·헤더·푸터)을 문자열로 품고 있다. `scripts/sync_admin_template.py` 가 buildPage 를 theme 블록과 같게 맞춘다(멱등). 칼럼 본문 스타일 `.post-body` 는 site.css 에 있다.
- **매거진 구조**: 글 목록의 원본은 `data/magazine/posts.json` 하나(카테고리 5 · 고민 태그 8 · 시술 태그 = 시술 파일명 · 글 목록). `python -X utf8 -I scripts/magazine/build.py` 가 HTML 안의 `<!-- mg:이름 --> … <!-- /mg:이름 -->` 영역만 다시 쓴다(columns.html=매거진 홈, 허브 `magazine-*.html` 5쪽은 columns.html 을 템플릿으로 통째 생성, index 표지, 시술 11쪽 관련 칼럼, 칼럼의 메타·다음 글, sitemap, header.html 드롭다운). `--check` 는 바뀔 파일만 보고. 마커 밖은 손으로, 마커 안은 절대 손으로 고치지 않는다. 생성 마크업에는 브랜드 색 클래스를 쓰지 않는다. 글 0편 카테고리는 자동으로 noindex·숨김. 새 글 절차와 분류 기준은 `docs/magazine-editorial.md`(어드민 → posts.json 에 항목 붙임 → build.py → check_theme baseline).
- **감수 전 초안**은 `drafts/magazine/`(배포 안 됨): `src/<slug>.md` → `python -X utf8 -I scripts/magazine/new_column.py` → `column-*.html` + `entries.json`. `scripts/magazine/lint.py` 로 의료광고 금지 표현 검사(0건이어야 함). 감수된 글만 `build.py --publish <slug>` 로 사이트에 넣는다(`--unpublish` 로 되돌림). 원장 명의 의료 정보라 감수 전에는 올리지 않는다.
- 지켜야 할 것: 페이지별 SEO 메타·JSON-LD·본문 문구는 디자인 작업에서 건드리지 않는다. 의료광고 규제상 후기(치료경험담)·전후 사진·"최고" 류 문구를 넣지 않는다. 본사이트(www) 문구·사진을 그대로 복사하지 않는다.

## 의료광고 모니터링 (scripts/admon/)
- 매달 절차는 `scripts/admon/README.md` 순서대로. 추출 JSON 스키마는 `docs/admon-extract-schema.md`.
- 봇 차단 사이트는 우회하지 않고 `captures/<월>/blocked.csv` 로만 전달한다. 폐업·제외 사유는 `data/admon/clinics.csv` 의 포함=N 행.
- 판정(위반 소지·심각도)은 `data/admon/rules.csv` 기반 **[초안]** 이며 "일괄 신고용 아님". 엑셀·문서에 그 표시를 유지한다.

## 마케팅 분석표 (scripts/kkeut/)
- 절차는 `scripts/kkeut/README.md`. 환자 이름·번호는 `sales_load.py` 에서 해시하고, `data/kkeut/` 와 원자료는 밖으로 내보내지 않는다.
- 플랫폼명은 여신티켓(강남언니 아님). 매출은 회계 순매출(주지표)과 세무 순 수납 두 기준을 함께 둔다.
- LibreOffice 가 없어 수식 재계산은 못 한다. 검산은 `expected-<월>.csv` 와 손으로.

## 환경
- Windows 10, PowerShell 5.1 + Git Bash. 파이썬은 `python -X utf8 -I`, 노드는 내장 fetch·WebSocket 사용(외부 패키지 없음). Chrome 은 `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- 브라우저 도구가 없으므로 화면 확인은 스크린샷 파일을 읽거나 사용자에게 브라우저를 열어 준다.
