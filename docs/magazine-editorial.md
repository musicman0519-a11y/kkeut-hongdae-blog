# 끗 매거진 편집 기준

작성일: 2026-11-05 · 원본 데이터: `data/magazine/posts.json` (이 문서의 slug 와 같아야 한다) · 생성: `python -X utf8 -I scripts/magazine/build.py`

## 카테고리 5개
| slug | 이름 | 영문 라벨 | 허브 파일 | 분류 기준(한 줄) |
|---|---|---|---|---|
| concern | 피부 고민 | SKIN CONCERNS | magazine-concern.html | 글의 출발점이 **증상·고민**("왜 생기나, 무엇이 다른가")이면 여기 |
| guide | 시술 가이드 | TREATMENT GUIDE | magazine-guide.html | 글의 출발점이 **특정 시술·장비**(원리·통증·회복·횟수·조합)이면 여기. 시술 태그 1개 이상 필수 |
| care | 관리 & 홈케어 | AFTERCARE | magazine-care.html | **시술 전후·집에서 하는 관리**, 계절·생활습관이 주제면 여기 |
| first-visit | 처음 방문 가이드 | FIRST VISIT | magazine-first-visit.html | **병원 이용 방법**(상담 흐름·비용 구조·준비물·FAQ·진료시간)이면 여기 |
| note | 원장 노트 | DOCTOR'S NOTE | magazine-note.html | **한방 관점·진료 철학·소식**처럼 원장의 시각이 중심이면 여기 |

글 하나는 카테고리 **1개**. 둘에 걸치면 "독자가 검색창에 뭐라고 쳤을까"로 정한다(증상이면 concern, 시술명이면 guide).

## 가로 분류(태그)
**고민 태그 8개** — 글당 1~2개
| slug | 이름 | 주로 짝이 되는 시술 |
|---|---|---|
| acne | 여드름·모공 | acne.html, skincare.html |
| pigment | 기미·색소 | toning.html |
| elasticity | 탄력·주름 | lifting.html, skinbooster.html, antiaging.html |
| scar | 흉터 | scar-center.html |
| hair | 제모 | jemo.html |
| diet | 다이어트 | diet.html |
| dry | 건조·민감 | skinbooster.html, skincare.html |
| contour | 윤곽 | face-contour.html |

**시술 태그 11개** — 시술 페이지 파일명 그대로, 글당 0~2개: jemo, diet, lifting, toning, acne, skinbooster, skincare, face-contour, antiaging, antiaging-center, scar-center (모두 `.html`).

시술 태그가 붙은 글은 그 시술 페이지 하단 "관련 칼럼"에 자동으로 뜬다. 고민 태그는 허브의 필터(`magazine-concern.html#tag=acne`)와 첫 화면 "고민별 바로가기"에 쓰인다.

## 글의 형식
- 작성자 표기: `홍대 끗 한의원 원장 강민구 · 의료인 작성` (posts.json `author`).
- 요약(summary) 60~110자, 제목은 질문형·상황형을 우선("~왜 꼭 해야 할까?", "~이것만 지키세요").
- 본문에 관련 시술 페이지 링크 1개, 예약 링크 1개.
- 표지(index 커버 스토리)에 올릴 글은 `featured: 1, 2` 로 표시. 최신 글은 날짜순 자동.

## 쓰지 않는 표현 (의료광고법 56조·시행령 기준)
- 치료 경험담·후기·"환자분이 만족" 류, 전후 사진·"Before/After".
- "최고·최초·1위·유일·완치·부작용 없음·100%" 등 절대·비교 표현. 다른 의원과의 비교.
- 비용을 적을 때는 할인 **조건·기간·대상**을 같은 문장에 적는다. 조건 없는 "100원" 식 단독 표기 금지.
- 시술 효과는 "개인차가 있다"를 붙이고, 부작용·주의사항을 함께 적는다.
- 본사이트(www) 문구·사진을 그대로 옮기지 않는다.

## 주제 백로그 (카테고리당 3개, 공개 전 최소 2편씩)
| # | 카테고리 | 제목 초안 | 고민 태그 | 시술 태그 |
|---|---|---|---|---|
| 1 | concern | 모공이 커 보이는 세 가지 이유와 각각의 대처 | acne | acne, skincare |
| 2 | concern | 기미·주근깨·잡티, 뭐가 다르고 왜 구분해야 하나 | pigment | toning |
| 3 | concern | 턱선이 처져 보이는 이유: 피부 탄력과 지방의 차이 | elasticity, contour | lifting, face-contour |
| 4 | guide | 토닝은 몇 회, 몇 주 간격이 맞을까 | pigment | toning |
| 5 | guide | 온다·슈링크·인모드, 열을 넣는 깊이가 다르다 | elasticity | lifting |
| 6 | guide | 스킨부스터 종류와 피부 상태별 선택 기준 | dry, elasticity | skinbooster |
| 7 | care | 레이저 시술 후 일주일: 세안·자외선·보습 순서 | pigment, dry | toning |
| 8 | care | 겨울철 시술 후 보습, 바르는 양보다 순서 | dry | skincare |
| 9 | care | 제모 시술 사이 셀프 관리: 면도는 되고 왁싱은 안 되는 이유 | hair | jemo |
| 10 | first-visit | 첫 상담에서 묻는 것과 미리 준비하면 좋은 것 | — | — |
| 11 | first-visit | 시술 비용은 어떻게 정해지나(부위·횟수·조건) | — | — |
| 12 | first-visit | 일요일 진료 이용 안내: 예약·대기·주차 | — | — |
| 13 | note | 한의원이 피부 시술을 하는 이유 | — | antiaging |
| 14 | note | 다이어트 환과 피부: 체중 변화가 피부에 남기는 것 | diet, elasticity | diet |
| 15 | note | 체질과 피부 트러블: 같은 여드름, 다른 원인 | acne | acne |

## 발행 절차
1. 어드민(`kkeut_admin.html`)에서 글 작성 → 카테고리·태그 선택 → 「발행 파일 만들기」.
2. 내려받은 `column-<slug>.html` 을 `kkeut_seo_site/` 에 넣고, 어드민이 보여 준 JSON 항목을 `data/magazine/posts.json` 의 `posts` 맨 위에 붙인다.
3. `python -X utf8 -I scripts/magazine/build.py` 실행 → 매거진 홈·허브·첫 화면·시술 페이지·sitemap 이 갱신된다.
4. `python -X utf8 -I scripts/check_theme.py check` 로 확인 뒤 기준선 재저장.
