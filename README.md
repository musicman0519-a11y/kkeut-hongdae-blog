# 끗한의원(홍대) SEO 사이트 · 끗 매거진

hongdaekkeutclinic.com 의 정적 사이트와 발행 도구. 빌드 없음(Tailwind CDN). 자세한 규칙은 `CLAUDE.md`.

| 폴더 | 내용 |
|---|---|
| `kkeut_seo_site/` | 배포되는 유일한 폴더. HTML 21쪽, `assets/`, `sitemap.xml` |
| `kkeut_admin.html` | 칼럼 발행 어드민(브라우저에서 열어 사용) |
| `data/magazine/posts.json` | 매거진 글 목록 원본(카테고리·태그·글) |
| `scripts/magazine/` | `build.py`(목록·허브·sitemap 생성), `new_column.py`(초안 변환), `lint.py`(의료광고 표현 검사) |
| `scripts/theme/` | 공통 블록(head·header·footer·floating) 원본과 스크린샷·성능 도구 |
| `drafts/magazine/` | 원장 감수 전 초안(배포 안 됨) |
| `docs/` | 명세(`specs/`)·작업 계획(`plans/`)·편집 기준 |

## 로컬에서 보기
```
cd kkeut_seo_site
python -X utf8 -m http.server 8787 --bind 127.0.0.1
```
브라우저에서 http://127.0.0.1:8787/index.html

## 새 글 올리기
1. `kkeut_admin.html` 에서 글 작성 → 「발행 파일 만들기」 → `column-<slug>.html` 을 `kkeut_seo_site/` 에 넣고, 화면에 나온 항목을 `data/magazine/posts.json` 의 `posts` 맨 위에 붙인다.
   (초안 폴더의 글은 `python -X utf8 -I scripts/magazine/build.py --publish <slug>` 한 줄로 대신한다.)
2. `python -X utf8 -I scripts/magazine/build.py` — 매거진 홈·허브·첫 화면·시술 페이지·sitemap 갱신
3. `python -X utf8 -I scripts/check_theme.py check` 확인 → `baseline` 재저장 → 커밋·푸시

## 디자인 공통 블록을 고쳤을 때
`scripts/theme/*.html` 수정 → `python -X utf8 -I scripts/apply_theme.py` → `scripts/magazine/build.py` → `scripts/sync_admin_template.py` → `check_theme.py check`

## 커밋 전
`python -X utf8 -I scripts/repo_check.py` — 환자 정보·매출·캡처·xlsx·토큰이 섞여 있으면 실패한다.

## 배포
Vercel 등에서 저장소를 연결하고 Root Directory 를 `kkeut_seo_site` 로 둔다. 빌드 명령 없음.
