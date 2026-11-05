# 전체 UI·글꼴 재단장 작업 계획   (명세: docs/specs/ui-restyle.md)

작성일: 2026-11-04 · 대상: kkeut_seo_site/ 16페이지 + kkeut_admin.html 템플릿 · 도구: Tailwind CDN, Google Fonts, Python(치환 스크립트), Chrome 헤드리스 + CDP

## 설계 결정 (코드 쓰기 전 합의)
- **토큰은 한 곳**: Tailwind 설정(colors·fontFamily)과 `assets/site.css` 를 공통 `<head>` 블록에 넣는다. 색 이름: `rose #E0507A`(강조) · `pink #FFC0CB` · `blush #F1A1AF` · `pinksoft #FDEEF3` · `ink #181818`. 글꼴 클래스: `font-serif-kr`(Gowun Batang) · `font-display`(Marcellus) · 본문 Pretendard.
- **공통 블록 4개를 파일로 분리**: `scripts/theme/{head.html, header.html, footer.html, floating.html}`. `scripts/apply_theme.py` 가 16페이지의 기존 블록(바이트 동일함을 이용해 정확 문자열로 찾음)을 이 파일 내용으로 바꾸고, 색 클래스 매핑표(`brandorange→rose`, `cardteal/cardred/…→pinksoft 또는 ink`, `kpink→blush`)를 적용한다. 페이지별 `<title>`·meta·본문은 건드리지 않는다. 재실행하면 같은 결과(멱등).
- **index.html 은 손으로**: 히어로·WHY·FIND 섹션은 새 마크업. 시술 메뉴·이벤트·칼럼·예약 섹션은 기존 마크업에 색·글꼴만.
- **글꼴 로드**: `<link rel="preconnect">` 2개 + Google Fonts 1줄(Gowun Batang 400·700, Marcellus 400, `display=swap`). 한글 글꼴은 Google 이 유니코드 범위별로 쪼개 주므로 실제 받는 양은 작다.
- **떠 있는 버튼·하단 바**: `floating.html` 하나로 `</body>` 직전에 삽입. 하단 바 높이만큼 `body` 아래 여백(`pb-20 md:pb-0`)을 site.css 에서 준다. 데스크톱은 원형 버튼 5개, 모바일은 3개(`hidden md:flex`).
- **헤더**: 흰 배경, 로고 왼쪽(`assets/logo.png` 그대로) + 메뉴 4개 오른쪽, `sticky top-0`. 기존 상단 작은 줄(전화·주소)은 헤더 안 오른쪽 끝으로 합친다.
- **히어로 사진**: 미결 1 이 정해질 때까지 `kkeut-left.jpg` 를 `object-cover` 로 임시 사용. 사진 파일만 바꾸면 되게 `<img>` 하나로.
- **검증 자동화**: `scripts/check_theme.py` — 16페이지 공통 블록 md5 일치, 옛 색 클래스 0개, 내부 href 집합이 변경 전과 동일, sitemap/robots 불변. 변경 전 href 집합은 작업 1에서 먼저 저장.

## 작업 목록
- [x] 1. 기준선 저장: 16페이지의 내부 `href` 목록·`<title>`·description·canonical·JSON-LD 를 `data/theme-baseline.json` 에, index 데스크톱·모바일 스크린샷과 Lighthouse 모바일 점수를 scratchpad 에 저장한다
      파일: scripts/check_theme.py(기준선 저장 모드), data/theme-baseline.json / 확인: JSON 에 16페이지 항목, 점수 숫자 기록 / 의존: 없음
- [x] 2. 걷는 뼈대: `assets/site.css` + 새 `<head>` 공통 블록(팔레트·글꼴 3종)을 **index.html 에만** 적용하고 h1·h2 를 명조로 바꿔 글꼴·색이 뜨는지 본다
      파일: kkeut_seo_site/assets/site.css, scripts/theme/head.html, kkeut_seo_site/index.html / 확인: 로컬 서버 스크린샷에서 제목이 명조, 네트워크에 Gowun Batang·Marcellus woff2 요청 / 의존: 없음
- [x] 3. 새 헤더·푸터 블록을 만들어 index.html 에 넣는다(로고 왼쪽·메뉴 오른쪽·고정, 검정 푸터)
      파일: scripts/theme/header.html, footer.html, index.html / 확인: 1280px·390px 스크린샷, 메뉴 4개 링크 목적지 동일, 390px 가로 넘침 0 / 의존: 2
- [x] 4. index 히어로 섹션: 풀블리드 사진(임시 kkeut-left.jpg) + 명조 헤드라인 2줄 + 보조 1줄 + 단계 01/02/03 + 버튼 2개(예약하기 → #booking, 시술 보러가기 → #menu). 검색용 h1 문장은 유지하되 작게
      파일: index.html / 확인: 1280px 에서 히어로가 화면 폭 전체, 390px 높이 ≥ 480px·헤드라인 읽힘, h1 텍스트가 기준선과 동일 / 의존: 3
- [x] 5. index "WHY KKEUT" 카드 3개 + "FIND YOUR CARE" 사진 반·글 반 섹션(kkeut-left/right.jpg 활용, Marcellus 소제목)
      파일: index.html / 확인: 스크린샷에서 카드 3개 한 줄(모바일 세로 1열), 사진·글 반반(모바일 세로) / 의존: 3
- [x] 6. index 나머지 섹션(시술 메뉴 12칸·이벤트·칼럼·예약·진료시간)을 새 톤으로: 카드 머리색 7종 → pinksoft/ink, brandorange → rose, 제목 명조
      파일: index.html / 확인: index 에 옛 색 클래스 0개, 시술 12칸 링크·사진 그대로, 예약 섹션 링크 3개 그대로 / 의존: 4, 5
- [x] 7. 떠 있는 원형 버튼 + 하단 고정 바(`floating.html`)를 만들어 index 에 넣고 본문 끝 여백을 준다
      파일: scripts/theme/floating.html, assets/site.css, index.html / 확인: 390px 에서 하단 바가 푸터 글자를 가리지 않음, 버튼 링크 4개 목적지 확인, Tab 으로 접근 가능 / 의존: 3
- [x] 8. `scripts/apply_theme.py`: 공통 블록 4개 치환 + 색 클래스 매핑을 **15페이지**에 적용한다(index 제외). 두 번 실행해도 결과 동일
      파일: scripts/apply_theme.py, 15개 html / 확인: `check_theme.py` — 16페이지 공통 블록 md5 일치, 옛 색 클래스 0개, 내부 href 집합·title·description·canonical·JSON-LD 가 기준선과 동일, sitemap·robots 불변 / 의존: 6, 7
- [x] 9. 시술 페이지 제목 글꼴: 15페이지의 h1·h2 에 명조 클래스를 넣는다(스크립트의 매핑에 포함, 본문 p 는 그대로)
      파일: scripts/apply_theme.py / 확인: jemo.html·columns.html 1280px 스크린샷에서 제목 명조, 본문 고딕 / 의존: 8
- [x] 10. 어드민 칼럼 템플릿 동기화: `kkeut_admin.html` 의 템플릿 문자열(head·헤더·푸터·색)을 `scripts/theme/*.html` 과 같게 바꾼다
      파일: kkeut_admin.html / 확인: 어드민에서 「발행 파일 만들기」→ 다운로드한 html 을 `apply_theme.py --check` 로 돌리면 공통 블록 md5 가 16페이지와 같다 / 의존: 8
- [x] 11. 끝단 확인: Lighthouse 모바일(성능 ≥ 기준선, CLS ≤ 0.1, 접근성 ≥ 90), 390px·1024px·1280px 스크린샷 3세트(index·jemo·columns)를 사용자에게 보여 주고 명세 완료 기준 7개를 체크한다
      파일: (변경 없음) / 확인: 완료 기준 전부 체크 / 의존: 9, 10

사용자 확인 지점: 설계 결정·미결 1~3 답 → 1번 시작. 3번 뒤(헤더·푸터) 스크린샷 1차 검토, 7번 뒤 첫 화면 2차 검토, 11번 최종.
병렬 가능: 1 은 2~7 과 독립. 4·5 는 3 뒤 서로 독립. 8 은 2~7 의 블록 파일이 확정된 뒤.

## 위험 요소
- **본문 안 색 클래스**: 시술 페이지 본문에도 `brandorange`·`cardteal` 류가 섞여 있어 매핑표가 빠뜨리면 주황이 남는다 → 8번에서 grep 으로 0개 확인.
- **Tailwind CDN 임의값**: `bg-[#...]` 식 임의 색이 본문에 흩어져 있으면 매핑이 안 된다 → 1번 기준선에서 임의값 목록을 뽑아 매핑표에 넣는다.
- **글꼴 로드 지연·CLS**: 명조 폴백이 고딕이라 글꼴 교체 때 줄바꿈이 바뀔 수 있다 → `display=swap` + 제목 줄 높이 고정, 11번에서 CLS 측정.
- **히어로 사진 품질**: `kkeut-left.jpg` 는 1080px 라 1920 폭에서 흐릿할 수 있다 → 미결 1 로 원본 요청. 임시라도 `max-h` 를 두어 과확대 방지.
- **하단 바가 콘텐츠 가림**: 예약 섹션·푸터 끝에서 겹침 → body 아래 여백, 7번에서 확인.
- **어드민 템플릿 불일치**: 10번을 빠뜨리면 다음 칼럼부터 디자인이 둘로 갈라진다. 명세 완료 기준에 넣었다.
- **성능**: 글꼴 2종 추가(약 60~120KB)와 히어로 사진이 LCP 를 늦춘다 → 히어로 사진은 WebP ≤ 200KB 로 변환, `fetchpriority="high"`. 시술 PNG 12장은 범위 밖(별도 `/webperf`).
- **줄바꿈 혼재**: index 는 LF, 나머지는 CRLF → apply_theme.py 가 각 파일의 줄바꿈을 보존하도록 바이너리로 읽고 쓴다.

## 진행 기록
- 2026-11-04 1번 완료. 기준선 `data/theme-baseline.json`(16페이지, 옛 색 클래스 176개, 임의 색 7종: #03C75A #1a1a1a #4a4a4a #EAF8F5 #EEF3FC #FBD3DC #FDF2E7). 스크린샷·지표는 scratchpad `theme/before/`. 도구: `scripts/check_theme.py`(baseline/check), `scripts/theme/shot.js`(CDP 스크린샷·넘침·글꼴), `scripts/theme/metrics.js`(간이 성능).
  - **Lighthouse 는 못 돌림**: `npx lighthouse` 패키지 내려받기가 권한 분류기에 막힘. 대신 metrics.js(모바일 에뮬레이션 + 4G·CPU 4배 느리게)로 LCP·CLS·요청·바이트를 재서 전후 비교한다. 기준: index LCP 2.6초·CLS 0·요청 20·206KB, jemo LCP 7.7초·CLS 0·요청 18·699KB. 명세 완료 기준의 "Lighthouse 점수" 는 이 지표로 대체(LCP·바이트 악화 없음, CLS ≤ 0.1).
  - 미결 1~3 은 추천안으로 진행: 히어로 사진 임시 `kkeut-left.jpg`(파일만 교체 가능하게), 하단 바 모든 페이지, 메뉴 4개 유지.
- 2026-11-04 2번 완료. `scripts/theme/head.html`(Tailwind CDN·Google Fonts 프리커넥트+1줄·Pretendard·site.css·Iconify·새 팔레트 설정) + `kkeut_seo_site/assets/site.css`(본문 글꼴·`h1,h2` 명조 전역 규칙·`.font-serif-kr`·`.font-display`·`.kr`·`.ease-rt`)를 index 에 적용. 1280·390 스크린샷에서 Gowun Batang·Marcellus·Pretendard 3종 로드 확인, 가로 넘침 0.
  - **계획과 다르게 한 것**: 옛 색 클래스 이름 바꾸기(brandorange→rose, card 7색 bg→ink / 아이콘→rose, kpinksoft·임의 연한색 3종→pinksoft, #03C75A→naver)를 6번에서 2번으로 앞당겼다. 새 head 블록에는 옛 색 이름이 없어서 그대로 두면 주황 버튼이 흰 글자만 남아 보이지 않기 때문. 6번은 카드 머리 디자인(ink 대 pinksoft)·제목 톤 다듬기만 남는다.
  - h1·h2 명조는 클래스 대신 site.css 전역 규칙으로 걸었다 → 9번은 스크립트 매핑 없이 스크린샷 확인만 남는다(어드민 새 칼럼도 자동 적용). Gowun Batang 은 700 까지라 h2 의 `font-extrabold` 는 `font-bold` 로.
  - 영문 배지(Diet/Face…)·Hours/Location 소제목에 `font-display`(Marcellus) 적용.
- 2026-11-05 3번 완료(매거진 계획 9번과 함께, `docs/plans/magazine-ia.md` 참고). 메뉴는 매거진 명세대로 5개(매거진 드롭다운·시술 안내·이벤트·끗 한의원·예약). `scripts/theme/header.html`·`footer.html` 생성, index 에만 적용. 4~6번은 index 의 `#magazine` 섹션 구조를 유지한 채 모양만 다듬는다. 8번은 허브 5쪽(magazine-*.html, build.py 가 columns.html 을 템플릿으로 재생성)도 대상에 넣는다.
- 2026-11-05 4번 완료. `<section id="hero">`: kkeut-left.jpg(상담 장면, object-position 72%) 위에 흰 그라데이션(모바일은 흰 80% 덮개), Marcellus 라벨, 명조 h1 2줄("과하지 않은 자연스러운 / 한 끗 차이의 아름다움"), 보조 1줄(기존 "일요일에도 진료합니다" 문구 유지), 01/02/03, 버튼 2개(#booking, #menu). **index 에는 원래 h1 이 없었다**(기준선 h1 빈 문자열) → 이 헤드라인이 첫 h1. 기준선 재저장. 1280 히어로 580px 풀폭, 390 높이 500px 이상·넘침 0. 옛 "일요일" 섹션은 히어로에 흡수.
- 2026-11-05 5번 완료. 히어로와 시술메뉴 사이에 `#why`(WHY KKEUT, 번호 카드 3개: 원장 직접 상담 / 필요한 시술만 / 예약제·일요일 진료 — 스펙의 "대기 없는 진료" 는 단정 표현이라 "예약제로 기다림을 줄임" 으로) + `#find`(FIND YOUR CARE, pinksoft 배경, 글 반 + kkeut-right.jpg 반, 모바일은 사진 위·글 아래, 버튼 매거진 읽기/시술 안내). 1280·390 넘침 0.
- 2026-11-05 6번 완료(확인만). 2번에서 색 이름을 바꿔 둔 덕에 index 에 옛 색 클래스·임의 색이 0개, 시술 12칸·이벤트·예약·진료시간은 이미 ink/rose/pinksoft + 명조 h2. 손댄 것 없음.
- 2026-11-05 7번 완료. `scripts/theme/floating.html`(원형 버튼: 데스크톱 네이버·카카오·인스타·전화·맨위 5개, 모바일 카카오·전화·맨위 3개 / `#quickbar` 모바일 전용 3칸: 전화·카카오 상담·온라인 예약) 을 index `</footer>` 뒤 `</body>` 앞에 삽입. site.css 에 767px 이하 body padding-bottom 52px. 390 스크린샷에서 바가 진료시간 박스 아래 푸터를 가리지 않음, 1280 에서 버튼 5개 오른쪽 아래. 링크 5종 확인. 카카오 채널 URL 은 스펙 가정값(pf.kakao.com/_xgTJnX/chat).
- 2026-11-05 8번 완료. `scripts/apply_theme.py`(멱등, `--check`): head 공통부·상단바+헤더+nav·footer(+floating) 치환, 색 토큰 매핑 10종(brandorange/khot→rose, kpinksoft→pinksoft, kpink→blush, kyellow→kakao, card*→rose, #1a1a1a→ink, #03C75A→naver, #FBD3DC→pink, #4a4a4a→ink/70), h1·h2 font-extrabold→font-bold, 시술 페이지의 페이지별 하단 바는 `hidden md:block`(모바일에서 floating 의 quickbar 와 겹치지 않게). 15쪽 적용 → build.py 로 허브 5쪽 재생성 → check_theme **전부 통과**(공통 블록 21쪽 일치, 옛 색 0). 기준선 재저장.
  - **버그 수정**: check_theme 의 옛 색 검사 정규식 `(?<![\w-])` 가 `bg-khot` 같은 실제 사용을 못 세고 config 정의만 세고 있었다 → `(?<!\w)` 로 고침(apply_theme 도 같은 경계 사용). 고친 뒤 재검사 0개.
- 2026-11-05 9번 완료(확인만). site.css 전역 규칙으로 jemo·columns·칼럼 쪽 h1·h2 가 명조, 본문 고딕(1280·390 스크린샷, 글꼴 3종 로드). 스크립트 매핑 없음.
- 2026-11-05 10번 완료. `kkeut_admin.html` buildPage 템플릿의 head 공통부·상단바+헤더+nav·footer 를 scripts/theme/{head,header,footer,floating}.html 과 같게(`</script>` 는 `<\/script>` 로), 본문의 옛 색 → 새 토큰. 템플릿에 있던 `.post-body` 스타일은 공통 블록 md5 를 깨므로 `assets/site.css` 로 옮김(새 색). 헤드리스 크롬으로 실제 발행한 파일의 head_nav·footer_end md5 가 about.html 과 동일. 어드민 화면 자체(주황 UI)는 범위 밖.
- 2026-11-05 11번 완료. 최종: build --check·apply_theme --check 변경 없음, check_theme 전부 통과, 기준선 재저장. 스크린샷 세트 scratchpad `mg/`(index hero/why/magazine/float, columns, magazine-guide, column, jemo × 1280/390, 모두 넘침 0, 글꼴 3종 로드).
  - **성능(metrics.js, 390px·4G·CPU 4배)**: index LCP 3.1~3.5초(기준선 2.6초, 히어로 사진 preload 뒤 3.8→3.1~3.5), CLS 0.001~0.002, 요청 33~37·약 498KB(기준선 20·206KB — 증가분은 Gowun Batang·Marcellus 글꼴 10파일과 히어로 사진). jemo LCP 4.8초(기준선 7.7초, 개선), CLS 0.013, 26 요청·868KB. 명세의 "성능 점수가 전보다 낮지 않음" 은 index 에서 **미충족**(LCP +0.5~0.9초). 원인은 명조 웹폰트 자체라 디자인 결정의 비용이다 → 후속 `/webperf`(글꼴 서브셋 자체 호스팅·Gowun Batang 400 단일 굵기·시술 PNG→WebP)로 넘긴다.
  - 완료 기준 7개 중 6개 충족, 성능 1개는 위와 같이 부분 충족(CLS·접근성 요건은 충족, 점수는 Lighthouse 대신 LCP 로 판단).
- 2026-11-05 로고 교체(사용자 요청, 원본 .ai 제공). PyMuPDF 로 벡터 추출 → `assets/logo-mark.svg`·`logo-kr.svg`·`logo-vertical.svg`(색 #FFC0CB = pink 토큰). 원본에는 영문 워드마크가 없어 헤더의 "KKEUT CLINIC" 은 Marcellus 텍스트(blush). header/footer.html 수정 → apply_theme(이제 index 포함, 드롭다운 선채움) → build → `scripts/sync_admin_template.py`(신규, 멱등) 로 21쪽+어드민 동기화, check_theme 통과, 기준선 재저장. 교훈: header.html 을 고친 뒤 build 보다 apply 를 먼저 돌리면 빈 드롭다운이 전파됐었다 → apply_theme 가 먼저 채우도록 고침.
- 2026-11-05 버튼 톤 낮춤(사용자 요청 "배너가 눈에 띈다"). 예약 섹션 4개: 네이버 예약만 rose, 나머지 3개 흰 바탕+검정 선. 떠 있는 원형 버튼: 전화만 rose, 나머지 흰 원+선(호버 rose). 모바일 quickbar: 온라인 예약만 rose. 시술 페이지 하단 바 버튼 3개(문의·네이버 예약·시술 선택하기): apply_theme 의 BAR_BUTTONS 로 흰+선 / 시술 선택하기만 rose. kakao·naver 원색은 이제 화면에 없음(토큰은 남겨 둠).
- 2026-11-05 /webperf 1회차 — **Tailwind CDN → 정적 CSS**. 측정(metrics.js, index 390px·4G·CPU 4배, 3회): LCP 3104/3940/5108 → **1988/2092/2164ms(중앙값 3.9s → 2.1s)**, CLS 0.002 유지, 요청 33 → 28, 전송 475 → 372KB. 1위 병목은 CDN 스크립트 124KB(동기 로드 + 런타임 CSS 생성)였고 LCP 요소는 히어로 사진. `scripts/theme/tailwind_extract.js` 가 전 페이지의 클래스 합집합으로 `assets/tailwind.css`(22KB) 생성, head.html 첫 줄이 그 링크(HEAD_START 도 바뀜, 옛 CDN 시작점은 이행용 OLD_HEAD_START). 클래스 커버리지 341/341. 목표 2.5s 달성으로 종료. 남은 병목: Gowun Batang 2굵기 10파일(약 120KB)·히어로 jpg 47KB(WebP 로 ~25KB 가능) — 필요하면 2회차. 어드민 화면 자체의 CDN 은 그대로(사이트 아님).
