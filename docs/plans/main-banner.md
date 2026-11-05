# 메인 배너 작업 계획   (명세: docs/specs/main-banner.md)

작성일: 2026-10-30 · 도구: ffmpeg 9(로컬), Pillow 12, Chrome 헤드리스 + CDP 에뮬레이션(모바일 확인)

## 설계 결정 (코드 쓰기 전 합의)
- **산출 파일**: `kkeut_seo_site/assets/banner/main.mp4`, `main.webm`, `poster.jpg`. 원본 GIF 는 프로젝트 루트에 그대로 두고 사이트 폴더에는 넣지 않는다.
- **변환 명령은 스크립트로**: `scripts/make-banner.sh` (Git Bash 용) 하나에 ffmpeg 명령 3개를 적어 누구나 다시 만들 수 있게 한다. 해상도는 1920 폭으로 줄인다(원본 2390 은 과함, 포스터 1600px JPG q80 ≈ 44KB 확인됨).
- **마크업 위치**: `index.html` 의 `</nav>` 와 `<section class="py-14 md:py-16">`(일요일 섹션) 사이에 `<section id="hero-banner">` 하나를 끼운다. 기존 줄은 한 글자도 바꾸지 않는다.
- **비율 고정**: 섹션에 `aspect-ratio: 2390/821` 을 주어 로딩 중 높이가 잡히게 한다(CLS 방지). 모바일(`max-width: 767px`)에서는 높이 240px 고정 + `object-fit: cover; object-position: 50% 50%` 로 가운데를 보여 준다.
- **링크 영역**: 배너 섹션을 `position: relative` 로 두고 `<a>` 4개를 `position: absolute` + 퍼센트 좌표(left/top/width/height)로 얹는다. 좌표는 첫 프레임에서 글자 상자를 재서 정한다(대략 x 60~70%, y 60~86% 영역에 4줄). 모바일에서는 `hidden md:block`. 각 `<a>` 에 `aria-label` 과 포커스 시 보이는 외곽선.
- **재생 제어**: `<video autoplay muted loop playsinline preload="metadata" poster="...">`, `<link rel="preload" as="image" href="poster.jpg">`. `prefers-reduced-motion: reduce` 이면 작은 인라인 스크립트로 `video.pause()` 하고 `removeAttribute('autoplay')`.
- **링크 목적지**: About Us → `about.html`, Official Website → `https://www.kkeutclinic-hongdae.co.kr`(새 탭), KakaoTalk → `https://pf.kakao.com/_xgTJnX/chat`(본사이트에서 확인한 실제 채널, 새 탭), Reservation → `#booking`.

## 작업 목록
- [x] 1. 변환 스크립트 `scripts/make-banner.sh` 를 만들고 실행해 MP4·WebM·포스터 3개를 `assets/banner/` 에 생성한다
      파일: scripts/make-banner.sh, kkeut_seo_site/assets/banner/{main.mp4,main.webm,poster.jpg} / 확인: 세 파일 존재, MP4·WebM 각 ≤ 1.5MB, 포스터 ≤ 200KB, `ffprobe` 로 MP4 가 1920 폭·약 2.9초·무음임을 확인. 사이트 폴더에 `.gif` 없음 / 의존: 없음
- [x] 2. 걷는 뼈대: index.html 의 nav 아래에 배너 섹션을 넣어 포스터 이미지만 전체 폭으로 보이게 한다(영상·링크 없이)
      파일: kkeut_seo_site/index.html / 확인: 로컬 서버에서 1280px 스크린샷에 메뉴 바로 아래 배너가 보이고 「일요일」 섹션이 그 아래에 있다. 다른 15개 페이지 바이트 변경 없음(`git diff --stat` 대신 `md5sum` 비교) / 의존: 1
- [x] 3. 포스터를 `<video>` 로 바꿔 소리 없이 자동 반복 재생되게 한다(MP4·WebM 두 소스, 포스터 유지)
      파일: kkeut_seo_site/index.html / 확인: CDP 로 2초 뒤 0.5초 간격 스크린샷 두 장의 픽셀이 다르다(재생 중). `main.mp4`·`main.webm` 을 잠시 이름 바꾸면 같은 자리에 포스터가 같은 크기로 보인다 / 의존: 2
- [x] 4. 비율 고정과 포스터 preload 로 로딩 중 레이아웃 밀림을 없앤다
      파일: kkeut_seo_site/index.html / 확인: Lighthouse(Chrome 헤드리스) 모바일 CLS ≤ 0.1, 작업 2 이전 점수와 성능 차이 5점 이내 / 의존: 3
- [x] 5. 첫 프레임에서 메뉴 글자 4개의 상자 좌표(퍼센트)를 재서 `docs/plans/main-banner.md` 아래 「좌표」 절에 기록한다
      파일: docs/plans/main-banner.md (좌표 표) / 확인: 네 상자의 left/top/width/height 퍼센트가 적혀 있고, 포스터 위에 상자를 그린 확인용 이미지에서 글자가 상자 안에 들어간다 / 의존: 1
- [x] 6. 좌표대로 투명 링크 4개를 얹고 목적지를 연결한다(데스크톱만)
      파일: kkeut_seo_site/index.html / 확인: CDP 로 각 글자 중심 좌표를 클릭하면 `about.html`, 본사이트(새 탭), 카카오 채널, `#booking` 으로 간다. Tab 4번으로 네 링크에 차례로 포커스되고 `aria-label` 이 읽힌다 / 의존: 3, 5
- [x] 7. 모바일(390px)에서 가운데 자르기 높이 240px 로 보이게 하고 링크 영역은 숨긴다
      파일: kkeut_seo_site/index.html / 확인: CDP 에뮬레이션 390px 스크린샷에서 배너 높이 ≥ 200px, 모델 얼굴이 보이고, 가로 넘침 요소 0개, 링크 4개가 `display:none` / 의존: 6
- [x] 8. `prefers-reduced-motion` 사용자는 영상 대신 포스터만 보게 한다
      파일: kkeut_seo_site/index.html / 확인: CDP `Emulation.setEmulatedMedia({features:[{name:'prefers-reduced-motion',value:'reduce'}]})` 로 열면 2초 뒤 두 스크린샷이 동일(정지) / 의존: 3
- [x] 9. 끝단 확인: 명세 완료 기준 8개를 체크리스트로 돌리고 데스크톱·모바일 스크린샷을 사용자에게 보여 준다
      파일: (변경 없음) / 확인: 완료 기준 8개 모두 체크, 로컬 서버 주소 안내 / 의존: 4, 6, 7, 8

병렬 가능: 1 과 5 는 서로 독립(5 는 GIF 첫 프레임만 있으면 됨). 7 과 8 은 6 이 끝난 뒤 서로 독립.

## 위험 요소
- **카카오 자리표시자**: 이 사이트의 시술 페이지 15개에 있는 카카오 링크는 `https://pf.kakao.com` 까지만이라 채널 홈으로 간다(실제 채널 아님). 배너는 본사이트의 실제 주소 `pf.kakao.com/_xgTJnX/chat` 를 쓴다. 나머지 15개 페이지 교체는 이 계획 범위 밖이며 별도 작업으로 권한다.
- **자동 재생 정책**: `muted` + `playsinline` 이 없으면 iOS·Chrome 이 재생을 막는다. 두 속성을 빠뜨리지 않는지 3번에서 확인한다.
- **저장 데이터 모드·느린 망**: 브라우저가 영상을 안 받을 수 있다. 포스터가 항상 먼저 보이도록 2번 뼈대를 포스터로 시작한 이유.
- **좌표 어긋남**: 링크 영역은 퍼센트라 폭에 무관하지만, `object-fit: cover` 로 자르는 구간(모바일)에서는 어긋난다. 그래서 모바일은 링크를 숨긴다. 태블릿(768~1024px)은 비율 유지 구간이라 괜찮지만 7번에서 1024px 도 한 번 찍어 확인한다.
- **GIF→MP4 색 바뀜**: GIF 는 256색이라 변환 시 분홍 배경에 띠(밴딩)가 생길 수 있다. 1번에서 `-crf 23` 과 `yuv420p` 로 뽑고 포스터와 색이 눈에 띄게 다르면 `-crf 20` 으로 낮춘다.
- **홀수 해상도**: H.264 는 폭·높이가 짝수여야 한다. 1920×660(2390:821 비율) 로 맞춘다.
- **Lighthouse 기준선**: 4번 비교를 위해 2번 **전에** index.html 점수를 한 번 재 두어야 한다. 2번 시작 때 먼저 잰다.

## 좌표 (5번 결과, 포스터 1920×660 기준, 글자 상자 + 여백 8px)
| 링크 | left | top | width | height | 목적지 |
|---|---|---|---|---|---|
| About Us | 62.97% | 60.00% | 5.73% | 4.55% | about.html |
| Official Website | 60.00% | 66.82% | 8.70% | 4.55% | https://www.kkeutclinic-hongdae.co.kr (새 탭) |
| KakaoTalk | 62.50% | 73.64% | 6.20% | 4.55% | https://pf.kakao.com/_xgTJnX/chat (새 탭) |
| Reservation | 61.77% | 80.61% | 6.93% | 4.55% | #booking |
클릭하기 쉽도록 실제 링크는 세로 여백을 늘려 height 6.8% (글자 위아래 약 7px 추가) 로 쓴다. 네 상자 사이 간격이 약 2.3% 라 겹치지 않는다.

## 발견 사항 (이번 작업에서 고치지 않음)
- 첫 화면 Lighthouse 모바일 성능이 원래 35점(LCP 25.8초). 원인은 시술 메뉴 사진 12장이 각 300~520KB PNG 인 것과 Tailwind·Iconify CDN 스크립트. 사진을 WebP/JPG 로 줄이면 크게 개선될 것. `/webperf` 로 별도 진행 권장.
- `slider-4.png` 와 `MainInfo_Left.png` 는 같은 파일(중복). 네이버 캐러셀 명세에서도 이미지 중복 금지라 정리 필요.
- 시술 페이지 15개의 카카오 링크가 `https://pf.kakao.com` 자리표시자. 실제 채널 `https://pf.kakao.com/_xgTJnX/chat` 로 교체 필요.
- index.html 은 LF, 나머지 페이지는 CRLF 로 줄바꿈이 섞여 있음. `/constraints` 에서 통일 규칙을 정하면 좋음.
