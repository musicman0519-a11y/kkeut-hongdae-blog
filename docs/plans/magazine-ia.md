# 매거진형 정보 구조 재구성 작업 계획   (명세: docs/specs/magazine-ia.md)

작성일: 2026-11-05 · 대상: kkeut_seo_site/ 16쪽 + 신규 허브 5쪽 + kkeut_admin.html · 도구: Python(생성 스크립트), check_theme.py, shot.js

## 설계 결정 (코드 쓰기 전 합의)
- **글 목록의 원본은 파일 하나**: `data/magazine/posts.json`. 항목 = slug · title · category(5개 중 1) · concerns(고민 태그 ≤2) · treatments(시술 페이지 파일명 ≤2) · date · summary · featured(표지 순서, 선택). 어드민은 이 JSON 한 항목을 조각으로 내보내고, 사람은 **이 파일 한 군데에만** 붙인다. (명세의 "목록·허브·index·sitemap 조각"을 조각 1개 + 생성 스크립트로 줄임. 결과는 같고 붙일 곳이 4→1.)
- **생성 스크립트** `scripts/magazine/build.py`: posts.json 을 읽어 HTML 안의 표시 영역 `<!-- mg:이름 -->…<!-- /mg:이름 -->` 만 다시 쓴다. 대상: columns.html(탭·목록) · 허브 5쪽(파일 전체 생성) · index.html(커버·최신 글·처음 방문) · 시술 11쪽(관련 칼럼) · column-*.html(다음에 읽을 글) · sitemap.xml(허브·칼럼 URL) · `scripts/theme/header.html`(매거진 드롭다운). 멱등(두 번 돌려도 같음), 줄바꿈 보존(바이너리로 읽고 각 파일의 기존 줄바꿈 유지, 신규는 LF — 기준선상 16쪽 전부 LF). 목록은 정적 HTML 로 남으므로 검색엔진이 읽는다.
- **허브 파일명·태그 slug 고정**: 허브 `magazine-{concern,guide,care,first-visit,note}.html`. 고민 태그 slug 8개: `acne`(여드름·모공) `pigment`(기미·색소) `elasticity`(탄력·주름) `scar`(흉터) `hair`(제모) `diet`(다이어트) `dry`(건조·민감) `contour`(윤곽). 시술 태그 = 시술 페이지 파일명(jemo, toning …).
- **태그 필터는 클라이언트 JS + URL 해시**(`magazine-concern.html#tag=acne`). 항목에 `data-tags` 를 두고 해시와 칩 클릭으로 거른다. JS 가 없으면 전체가 보인다. 별도 페이지 없음.
- **빈 카테고리 숨김 규칙**: 글 0편인 카테고리는 허브에 `<meta name="robots" content="noindex">`, sitemap 제외, 매거진 홈 탭·헤더 드롭다운에서 제외. 모두 build.py 가 결정한다.
- **기준선(check_theme) 운영**: 각 조각 끝에 `check` 를 돌려 **의도한 변경만**(예: columns title, sitemap) 보고되는지 확인한 뒤 `baseline` 으로 재저장하고 진행 기록에 사유를 적는다. href 는 추가만 하고 없애지 않는다.
- **ui-restyle 과의 순서**: 이 계획의 1~8 은 본문 영역만 건드려 ui-restyle 과 독립. 9(헤더 드롭다운)는 ui-restyle 3(header.html)과 같이 하고, 15쪽+허브 5쪽에 공통 블록을 퍼뜨리는 일은 ui-restyle 8(apply_theme.py)이 맡는다. index 의 섹션 모양 다듬기는 ui-restyle 4~6 이 이 계획 8 의 구조 위에서 한다.
- **admin-site-sync 계획(publish-column.js, 미착수)은 보류**: 목록·sitemap 삽입 역할을 build.py 가 대신한다. 남는 역할(어드민 다운로드 파일을 사이트 폴더로 복사·도메인 보정)은 필요해지면 build.py 옵션으로.

## 작업 목록
- [x] 1. 걷는 뼈대: `data/magazine/posts.json` 에 기존 2편을 넣고, `scripts/magazine/build.py` 가 columns.html 의 `<!-- mg:list -->` 영역만 다시 쓰게 한다
      파일: data/magazine/posts.json, scripts/magazine/build.py, kkeut_seo_site/columns.html(마커 삽입) / 확인: 실행 뒤 columns.html 목록 2편이 전과 같은 제목·요약·href, 두 번 실행해 diff 0, CRLF 유지, `check_theme.py check` 통과 / 의존: 없음
- [x] 2. 편집 문서 `docs/magazine-editorial.md`: 카테고리 5개 정의·영문 라벨·분류 1줄 기준, 고민 태그 8개·시술 태그 11개 표, 주제 백로그 15개(카테고리당 3), 규제 금지 표현 목록
      파일: docs/magazine-editorial.md / 확인: 백로그 15개·태그 19개가 세어지고 posts.json 의 slug 와 문서의 slug 가 같다 / 의존: 없음 (1과 병렬)
- [x] 3. columns.html 을 매거진 홈으로: title·h1·description 을 "끗 매거진"으로, 카테고리 탭(글 있는 것만, `mg:tabs`), 목록 항목에 카테고리 라벨·고민 태그 칩 표시
      파일: columns.html, build.py / 확인: 1280·390 스크린샷에서 탭 2개(시술 가이드·관리&홈케어)와 글 2편, 넘침 0; check 에서 columns title·description·h1 변경만 보고 → 기준선 재저장 / 의존: 1
- [x] 4. 허브 5쪽 생성: 템플릿 `scripts/magazine/hub.html`(현재 columns.html 과 같은 공통 블록) + build.py 가 고유 title·description·canonical·BreadcrumbList JSON-LD·목록을 채워 `magazine-*.html` 5개를 쓴다. 0편이면 noindex + "준비 중" 문구. sitemap.xml 의 `mg:urls` 영역에 글 있는 허브 URL 추가
      파일: scripts/magazine/hub.html, build.py, kkeut_seo_site/magazine-*.html(신규 5), sitemap.xml / 확인: 5 파일 존재·CRLF, 2쪽은 글 목록·3쪽은 noindex, sitemap 에 허브 2개 추가, 5쪽 공통 블록 md5 가 columns.html 과 같음 → 기준선 재저장(sitemap) / 의존: 3
- [x] 5. 허브 고민 태그 필터: 칩 8개 + `#tag=` 해시로 항목 거르기(JS 20줄 안팎, 인라인), 매거진 홈에도 같은 칩
      파일: hub.html, columns.html, build.py / 확인: `magazine-care.html#tag=pigment` 로 열면 해당 글만 보이고 칩이 활성, 해시 없으면 전체; JS 끄고 열어도 전체 목록 보임 / 의존: 4
- [x] 6. 칼럼 2편에 상단 메타 블록(카테고리 링크 · 고민 태그 칩 · 작성일 · "홍대 끗 한의원 원장 강민구 · 의료인 작성") 과 하단 `mg:next`(같은 카테고리→같은 태그 순으로 2~3편, 없으면 영역 숨김) 를 넣고 build.py 가 채운다
      파일: column-jemo-shaving.html, column-summer-skin-care.html, build.py / 확인: 두 글이 서로를 "다음에 읽을 글"로 가리킴, 메타 블록의 카테고리 링크가 허브로 감, h1·title 불변, check 통과 / 의존: 4
- [x] 7. 시술 11쪽 하단 "관련 칼럼" 영역: 각 페이지 footer 앞에 `mg:related` 마커를 넣고 build.py 가 시술 태그가 같은 글 ≤3 을 채운다. 0편이면 마커만 남고 화면에 아무것도 없음
      파일: 시술 11쪽, build.py / 확인: jemo.html 에 1편 표시, 글 없는 페이지는 빈 영역 없음(스크린샷), 11쪽 CRLF 유지, check 통과(href 추가만) / 의존: 4
- [x] 8. index.html 표지 구조: 기존 「원장 칼럼」 섹션 자리에 ① 커버 스토리(`featured` 1+2, `mg:cover`) ② 고민별 바로가기 8칸(정적, 허브+해시 링크) ③ 최신 글 6(`mg:latest`) ④ 처음 방문 가이드 3(`mg:first`, 0편이면 숨김)
      파일: index.html, build.py / 확인: 1280·390 스크린샷, 8칸 href 가 `magazine-concern.html#tag=…` 8종, 커버 2편·최신 2편 표시, 처음 방문 영역 없음, h1·meta 불변, LF 유지, 넘침 0 / 의존: 4
- [x] 9. 헤더 메뉴 5개(매거진 · 시술 안내 · 이벤트 · 끗 한의원 · 예약) + 매거진 드롭다운(`mg:nav`, 글 있는 카테고리만). ui-restyle 3번(header.html)과 함께 진행하고, 블록 전파는 ui-restyle 8에 맡긴다
      파일: scripts/theme/header.html, build.py, index.html / 확인: 데스크톱 드롭다운 항목 2개, 모바일 가로 스크롤 5항목·넘침 0, 링크 목적지 5개 확인 / 의존: 3, ui-restyle 3
- [x] 10. 어드민: 카테고리 선택(5 고정)·고민 태그 체크(8)·시술 태그 체크(11, 기존 관련 시술 드롭다운은 유지)·작성자 표기, buildPage 에 메타 블록·`mg:next` 마커, 출력 상자를 「posts.json 항목」 하나로 교체(목록·sitemap 코드 상자 제거), 임시저장에 새 필드 포함
      파일: kkeut_admin.html / 확인: 글 하나 발행 → html 과 JSON 조각 → posts.json 에 붙이고 build.py 실행 → 매거진 홈·허브·index 최신·시술 관련·sitemap 에 전부 뜸, check 통과(기준선 재저장) / 의존: 6, 7, 8
- [x] 11. 끝단 확인: build.py 전체 재실행 diff 0, `check` 통과 상태로 기준선 재저장, 스크린샷 세트(index·columns·magazine-guide·column-jemo-shaving·jemo, 1280/390)를 보여 주고 명세 완료 기준 9개를 체크. 어드민 템플릿의 옛 디자인(주황)은 ui-restyle 10 몫임을 기록
      파일: (변경 없음) / 확인: 완료 기준 전부 체크 / 의존: 9, 10

사용자 확인 지점: 설계 결정 → 1번 시작. 3번 뒤 매거진 홈 스크린샷, 8번 뒤 표지 구조 스크린샷, 11번 최종.
병렬 가능: 1·2 독립. 5·6·7·8 은 4 뒤 서로 독립. 9 는 ui-restyle 3 과 묶임.

## 위험 요소
- **기준선 검증과의 충돌**: columns title 변경·sitemap 변경·신규 페이지는 check 가 실패로 본다 → 조각마다 "의도한 변경만"인지 눈으로 확인하고 재저장. 기준선을 아무 때나 덮지 않는다.
- **ui-restyle 과 같은 파일(index.html, header.html) 동시 편집**: 8번은 섹션 구조만, 모양은 ui-restyle 몫으로 선을 긋는다. 9번은 ui-restyle 3 과 한 조각으로 진행.
- **마커가 깨지면 생성이 엉뚱한 곳에 들어감**: build.py 는 마커 쌍이 정확히 1개가 아니면 그 파일을 건너뛰고 경고, 전체 종료 코드 1.
- **column-*.html 메타 블록은 어드민 출력과 같은 마크업이어야 함**: 6번에서 손으로 넣은 블록을 10번 buildPage 가 그대로 찍는지 문자열 비교.
- **JS 필터와 검색엔진**: 필터는 보이기/숨기기만 하고 HTML 은 전체 목록 그대로이므로 색인에는 영향 없음. 해시 링크는 한 URL 로 취급된다.
- **글이 2편뿐인 동안의 빈 느낌**: 허브 3개·처음 방문 영역·드롭다운이 숨겨져 사이트가 작아 보인다. 글 쓰기 명세(`magazine-content.md`)를 바로 이어서 진행해야 한다.
- **줄바꿈**: 기준선(data/theme-baseline.json) 기준 16쪽 전부 LF. CLAUDE.md 의 "나머지는 CRLF" 는 낡은 메모. 신규 파일도 LF.

## 진행 기록
- 2026-11-05 1번 완료. `data/magazine/posts.json`(카테고리 5·고민 태그 8·시술 11·글 2편, author 포함), `scripts/magazine/build.py`(`--check` 모드 있음), columns.html 목록에 `mg:list` 마커. 두 번 실행 diff 0, LF 유지. diff 는 마커 + 라벨(태그→카테고리명) + 호버 클래스뿐.
  - **생성 마크업은 브랜드 색 클래스를 쓰지 않는다**(`text-black/55`, `group-hover:underline`). 옛 head(brandorange)·새 head(rose) 어느 쪽에서도 같은 모양이 나야 하고, ui-restyle 8 의 치환 스크립트와 서로 덮어쓰지 않기 위해서다.
  - check_theme 실패 16건은 전부 ui-restyle 진행 중 상태(15쪽 옛 색 클래스·head 불일치)로 이번 변경과 무관. columns.html 의 title·description·h1·href 는 통과.

- 2026-11-05 2번 완료. `docs/magazine-editorial.md`(카테고리·태그 표, 금지 표현, 백로그 15, 발행 절차). slug 일치 스크립트 확인.
- 2026-11-05 3번 완료. columns.html title·description·og·h1 을 "끗 매거진"으로, 탭(`mg:tabs`, 글 있는 카테고리만 → 전체·시술 가이드·관리&홈케어), 목록에 고민 태그 칩. 1280·390 스크린샷 OK, 넘침 0. check 는 columns title·description·h1 변경만 새로 보고 → 기준선 재저장. 참고: Bash 히어독으로 파이썬 소스를 쓰면 `\n` 이 줄바꿈으로 바뀌므로 build.py 는 Edit 도구로 고친다.
- 2026-11-05 4번 완료. **계획과 다르게**: 별도 `hub.html` 템플릿 대신 build.py 가 columns.html(렌더된 것)을 그때그때 템플릿으로 읽어 허브 5쪽을 통째로 쓴다 → 공통 블록이 자동으로 같고(ui-restyle 8 뒤에도 재실행만 하면 됨) 파일이 하나 적다. 허브: 고유 title·description·canonical·og·BreadcrumbList, 0편이면 noindex + "준비 중" 안내. sitemap 은 수동 칼럼 2줄을 지우고 `mg:urls` 영역(글 있는 허브 + 칼럼 전부)으로. 결과: guide·care 에 글, concern·first-visit·note 는 noindex·sitemap 제외. 5쪽 공통 블록 md5 = columns.html, LF. check 는 sitemap 변경만 새로 보고 → 기준선 재저장(페이지 21).
- 2026-11-05 5번 완료. columns.html 에 칩 영역(`mg:chips`, 전체+8개)·`#mg-none` 빈 안내·인라인 JS(해시 `#tag=slug` 로 `data-tags` 항목 거르기, footer 앞에 두어 공통 블록 md5 유지). 허브는 템플릿을 통해 자동 상속. `magazine-care.html#tag=pigment` 스크린샷에서 칩 활성·해당 글만 표시, 정적 HTML 에는 hidden 없음(JS 없으면 전체). 넘침 0.
- 2026-11-05 6·7·8번 완료(한 번에). 칼럼 2편: `mg:cat`(끗 매거진 · 카테고리 링크) / h1 / `mg:byline`(날짜 · 원장 강민구 · 의료인 작성 + 고민 태그 칩 → `columns.html#tag=`) / 하단 「매거진 목록」 버튼 + `mg:next`(NEXT READ, 같은 카테고리→태그 겹침→최신 순 ≤3). 시술 11쪽: 떠 있는 바 앞 `mg:related`(`<section id="related">`, 시술 태그 일치 글 ≤3, 없으면 마커만) → 현재 jemo 만 표시. index: 「원장 칼럼」 섹션 → `<section id="magazine">`(KKEUT MAGAZINE 라벨 · 커버 `mg:cover` featured 1 큰 카드 + 2 · 고민별 8칸 · `mg:latest` · `mg:first`). **계획과 다르게**: 최신 글은 표지에 실린 글을 제외(2편뿐일 때 중복 방지) → 지금은 영역 숨김. 고민별 8칸은 `columns.html#tag=…`(매거진 홈)로 연결 — 글이 적은 동안 피부 고민 허브(0편)보다 전체 목록 필터가 유용. 스크린샷 1280·390 넘침 0, h1·meta 불변.
- 2026-11-05 9번 완료(= ui-restyle 3번). `scripts/theme/header.html`(sticky 흰 헤더, 로고 왼쪽, 데스크톱 메뉴 5개 + 매거진 드롭다운 `mg:nav`, lg 이상 전화·네이버 예약, **모바일은 로고+예약 1줄 / 메뉴 4개 2줄** — 한 줄 5개는 390px 에서 가로 스크롤이 생겨 바꿈) + `footer.html`(bg-ink, 푸터 메뉴 5개, blush 호버, Marcellus 저작권). index 에만 적용(다른 20쪽은 ui-restyle 8 에서). build.py 가 header.html 과 index 의 `mg:nav` 를 같이 채움(글 있는 카테고리만). 1280·390 넘침 0, 링크 목적지는 기존 집합 안(about.html 추가).
- 2026-11-05 10번 완료. 어드민: 카테고리 select 5 · 고민 태그 체크 8 · 시술 태그 체크 11(관련 시술 버튼 드롭다운 유지) · 임시저장/불러오기에 새 필드 · buildPage 가 `mg:cat`·`mg:byline`·`mg:next` 마커와 build.py 와 **문자열 동일**한 메타 블록 출력 · 출력 상자는 posts.json 항목 하나(목록·sitemap 상자 제거) · 업로드 안내 수정. 헤드리스 크롬으로 실제 발행(scratchpad `mg/admin-test.js`) → posts.json 반영 → build → 매거진 홈·guide 허브·index·toning 관련·sitemap·NEXT READ 전부 노출, care 허브·jemo 에는 없음, 멱등 확인 → 전부 되돌림(흔적 없음). 어드민 템플릿의 옛 head·푸터(주황)는 ui-restyle 10 몫.
- 2026-11-05 11번 완료. build --check 변경 없음, 기준선 재저장(21쪽), check_theme 는 ui-restyle 진행 중 항목(옛 색 클래스, 공통 블록 index≠나머지)만 남음. 스크린샷은 scratchpad `mg/`.

## 발견 사항
- CLAUDE.md 의 "index 는 LF, 나머지는 CRLF" 는 현재와 다르다(16쪽 전부 LF). /up 때 고칠 것.
- 칼럼 페이지의 주황 구분선(`bg-brandorange` div)·버튼 색은 ui-restyle 8 치환 대상.
- 어드민을 file:// 로 열면 Toast UI 에디터 CDN 이 안 붙어 기본 입력창으로 떨어진다(헤드리스 테스트에서 확인). 실제 사용엔 영향 없음.
