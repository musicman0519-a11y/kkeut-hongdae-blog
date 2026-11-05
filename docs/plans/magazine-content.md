# 매거진 초기 글 8편 작업 계획   (명세: docs/specs/magazine-content.md)

작성일: 2026-11-05 · 대상: drafts/magazine/(사이트 밖), scripts/magazine/{new_column.py, lint.py, build.py} · 도구: Python, check_theme.py, shot.js

## 설계 결정
- **초안 원고는 마크다운**: `drafts/magazine/src/<slug>.md` = 머리말(title·category·concerns·treatments·related·date·summary·seotitle·seodesc) + 본문(`## ` 소제목, 빈 줄 문단, `[글](링크)`, `**굵게**`). 원장이 고칠 때 html 보다 쉽다.
- **변환기 `new_column.py`** 는 사이트의 `column-jemo-shaving.html` 을 그때그때 템플릿으로 읽어(허브 생성과 같은 방식) 메타·마커·본문·관련 시술 버튼만 바꾼다 → 공통 블록이 사이트와 항상 같고, ui-restyle 8 뒤에 다시 돌리면 새 디자인이 된다. 출력: `drafts/magazine/column-<slug>.html` 8개 + `drafts/magazine/entries.json`.
- **`build.py --publish <slug>`**: 초안 html 을 사이트 폴더로 복사 + entries.json 의 항목을 posts.json 맨 위에 + 전 영역 생성. `--unpublish <slug>` 는 반대(검증 뒤 되돌리기용).
- **`lint.py`**: 금지 표현 목록(편집 문서와 같음)을 정규식으로, 초안과 사이트 칼럼의 본문 텍스트만 검사. 가격은 "숫자+원" 을 전부 잡는다.
- 글은 기존 2편 톤(존댓말, 원장 1인칭). 각 글 끝 문단에 개인차·주의 문장과 예약 링크.

## 작업 목록
- [x] 1. `scripts/magazine/new_column.py`: src/*.md → column-*.html(템플릿 치환) + entries.json. 샘플 1편으로 돌려 어드민 출력과 같은 마커·구조인지 확인
      파일: scripts/magazine/new_column.py, drafts/magazine/src/ / 확인: 생성 html 의 mg:cat·mg:byline 이 build.frag_* 와 같고 h1·title·canonical 이 머리말과 일치, LF / 의존: 없음
- [x] 2. `scripts/magazine/lint.py`: 금지 표현 검사, 기존 2편에서 0건
      파일: scripts/magazine/lint.py / 확인: 기존 2편 0건, 일부러 "최고" 넣은 임시 파일에서 1건 잡힘 / 의존: 없음
- [x] 3. 초안 4편(피부 고민 2, 시술 가이드 1, 관리 1) 작성 → 변환 → lint 0건, 글자 수·h2 수·링크 검사
      파일: drafts/magazine/src/{pores,pigment-types,toning-schedule,jemo-between}.md / 확인: 본문 900~1,500자, h2 ≥3, 시술 링크·예약 링크, 개인차 문장 / 의존: 1, 2
- [x] 4. 초안 4편(처음 방문 2, 원장 노트 2) 작성 → 같은 검사
      파일: drafts/magazine/src/{first-consult,how-cost-works,why-hanuiwon,diet-and-skin}.md / 확인: 3번과 같음 / 의존: 1, 2
- [x] 5. `build.py --publish/--unpublish <slug>` + `drafts/magazine/README.md`(감수 전 초안 표시·절차)
      파일: scripts/magazine/build.py, drafts/magazine/README.md / 확인: 한 편 publish → 전 영역 노출 → unpublish → --check 변경 없음, 파일 없음 / 의존: 1
- [x] 6. 끝단: 8편 전부 publish 한 상태로 build --check 0, 허브 5쪽 noindex 없음, index 최신 글·처음 방문 영역 표시, 시술 6쪽 관련 칼럼, lint 10편 0건, 칼럼 390px 넘침 0 → 전부 unpublish, check_theme 통과
      파일: (변경 없음) / 확인: 명세 완료 기준 5개 체크 / 의존: 3, 4, 5

병렬 가능: 1·2 독립, 3·4 는 1·2 뒤 독립, 5 는 1 뒤.

## 위험 요소
- **의료광고 표현**: lint 는 단어만 잡는다. 문맥상 효과 단정("확실히 좋아집니다")은 사람이 봐야 한다 → 글마다 "개인차" 문장을 강제하고 감수에서 거른다.
- **템플릿 의존**: column-jemo-shaving.html 구조가 바뀌면(ui-restyle 8) 변환기가 못 찾을 수 있다 → 치환마다 1개 매칭 assert.
- **글자 수**: 한글 기준 900~1,500자는 공백 제외로 센다. 스크립트로 계산.
- **임시 publish 흔적**: 6번에서 반드시 unpublish 하고 `--check`·`check_theme` 로 흔적 0 확인.

## 진행 기록
- 2026-11-05 1~6번 완료(한 세션). `new_column.py`(md → html, 템플릿 = 사이트의 column-jemo-shaving.html, 목록 `- ` 지원, 글자 수·h2·링크·개인차 검사 출력), `lint.py`(규칙 5종, 음성 테스트에서 후기·최고·3만원 3건 잡힘), 초안 8편 `drafts/magazine/src/*.md` → html 8 + entries.json, `build.py --publish/--unpublish`, README.
  - 8편 본문 902~998자(공백 제외), h2 4~5개, 예약 링크·개인차 문장 전부, 시술 태그 있는 6편은 시술 링크 있음. lint 10편 0건.
  - 임시 publish 8편: build --check 변경 없음, 허브 5쪽 noindex 없음, index 최신 글·처음 방문 영역 표시, 관련 칼럼 acne1·toning2·jemo2·diet1·antiaging1·skincare1, 드롭다운 6항목, 390px 칼럼 넘침 0 → 전부 unpublish, posts 2편·허브 noindex 3쪽으로 복귀, check_theme 기준선과 일치.
  - 생성 마크업 메타 블록은 build.frag_cat/frag_byline 과 문자열 동일(8편 확인).
- **다음**: 사용자가 원장 감수 → 감수된 글부터 `build.py --publish <slug>` → check_theme baseline. 감수 피드백 뒤 백로그 나머지 7편.

## 발견 사항
- 초안 제목·요약은 감수에서 바뀔 수 있으므로 posts.json 에는 publish 시점에만 들어간다(entries.json 이 원본).
