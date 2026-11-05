# 어드민 → 사이트 연동 작업 계획   (명세: docs/specs/admin-site-sync.md)

> **보류 (2026-11-05)**: 목록·sitemap 삽입 역할은 `scripts/magazine/build.py`(posts.json 기반)가 대신한다. 남는 역할(다운로드 파일 복사·도메인 보정)은 필요해지면 build.py 옵션으로. 자세한 것은 `docs/plans/magazine-ia.md` 설계 결정.

작성일: 2026-10-24 · 스택: Node 단일 파일, 외부 패키지 없음, 테스트는 Node 내장 `node:test`

## 설계 결정 (코드 쓰기 전 합의)
- 스크립트 위치: `scripts/publish-column.js`. 테스트: `scripts/publish-column.test.js`, 실행은 `node --test scripts/`.
- 스크립트는 **모듈 겸 CLI**: `require` 되면 함수만 내보내고, 직접 실행(`require.main === module`)일 때만 CLI 로 동작한다. 테스트가 임시 폴더를 사이트 폴더로 넘길 수 있도록 내부 옵션 `--site <dir>` 를 둔다(기본값은 스크립트 기준 `../kkeut_seo_site`).
- 원칙: **읽기 → 메모리에서 세 결과 계산 → 마지막에 한꺼번에 쓰기.** 중간에 하나라도 실패하면 아무 파일도 쓰지 않는다.
- 줄바꿈: 사이트 파일(columns.html, sitemap.xml)은 **CRLF**, 어드민 출력은 LF. 삽입 조각은 대상 파일의 줄바꿈을 따른다. 새 칼럼 파일은 어드민 출력 그대로(LF) 둔다.
- 테스트 픽스처: 어드민 `buildPage` 출력 구조를 그대로 본뜬 `tests/fixtures/column-test.html` 하나를 손으로 만든다(어드민은 브라우저 전용이라 Node 에서 호출 불가).

## 작업 목록
- [ ] 1. 테스트 픽스처 `tests/fixtures/column-test.html` 을 만든다 (어드민 `buildPage` 출력 구조 그대로, 본문에 `<img>` 1개와 `<`, `&` 가 든 제목 포함)
      파일: tests/fixtures/column-test.html / 확인: 파일에 `<h1>`, 「원장 칼럼 · 태그」 줄, 「날짜 · 홍대 끗 한의원 원장」 줄, `<article class="post-body`, canonical(blog 도메인 아닌 값으로) 이 모두 있다 / 의존: 없음
- [ ] 2. 걷는 뼈대: `scripts/publish-column.js` 가 입력 경로 하나를 받아 사이트 폴더에 같은 이름으로 복사한다. 같은 이름이 있으면 "이미 존재" 메시지와 종료 코드 1
      파일: scripts/publish-column.js (CLI 골격, `--site`, `require.main` 분기 포함) / 확인: 픽스처로 실행하면 `kkeut_seo_site/column-test.html` 생김, 두 번째 실행은 종료 코드 1 이고 파일 변경 없음. 확인 후 생성된 파일은 삭제 / 의존: 1
- [ ] 3. 파일명 검증: `column-` + `[a-z0-9-]+` + `.html` 이 아니면 종료 코드 1, 아무것도 쓰지 않음
      파일: scripts/publish-column.js, scripts/publish-column.test.js(신규) / 확인: `node --test scripts/` 에서 `Column-Test.html`, `test.html`, `column-한글.html` 거부, `column-a-1.html` 통과 / 의존: 2
- [ ] 4. 메타 추출 함수 `parseColumn(html)`: 제목·태그·날짜·slug·요약(본문 텍스트 앞 90자) 를 돌려주고, 필수 요소를 못 찾으면 throw
      파일: scripts/publish-column.js, scripts/publish-column.test.js / 확인: 픽스처에서 다섯 값이 기대값과 같다. `<h1>` 을 지운 입력은 throw. 요약은 태그 제거·공백 정리 후 90자 / 의존: 1, 2
- [ ] 5. 도메인 보정 함수 `fixDomain(html, site)`: canonical 과 og:url 의 도메인이 `https://blog.kkeutclinic-hongdae.co.kr` 과 다르면 치환, 같으면 그대로
      파일: scripts/publish-column.js, scripts/publish-column.test.js / 확인: 픽스처(다른 도메인) 입력 → 두 줄 모두 blog 로 바뀜, 그 외 바이트 동일. 이미 blog 인 입력 → 입력과 바이트 동일 / 의존: 4
- [ ] 6. 목록 삽입 함수 `insertListItem(columnsHtml, meta)`: `<ul class="divide-y divide-black/10">` 바로 다음 줄에 어드민 「목록 코드」와 동일한 `<li>` 를 넣고, 같은 href 가 이미 있으면 입력 그대로 반환
      파일: scripts/publish-column.js, scripts/publish-column.test.js / 확인: 실제 columns.html 복사본에 넣으면 첫 `<li>` 가 새 글, 기존 2개는 뒤에 그대로, 줄바꿈 CRLF 유지, 제목의 `<` `&` `"` 는 `&lt;` `&amp;` `&quot;` 로. 두 번 넣어도 1개 / 의존: 4
- [ ] 7. 사이트맵 삽입 함수 `insertSitemapUrl(xml, url)`: `</urlset>` 바로 앞에 한 줄 추가, 같은 URL 이 있으면 그대로 반환
      파일: scripts/publish-column.js, scripts/publish-column.test.js / 확인: 실제 sitemap.xml 복사본에 넣으면 URL 17개, CRLF 유지, 두 번 넣어도 17개, `&` 가 든 URL 은 `&amp;` / 의존: 2
- [ ] 8. 전부-또는-없음 조립: CLI 가 4~7 을 메모리에서 순서대로 수행한 뒤 마지막에 세 파일을 쓴다. 어느 단계든 throw 하면 종료 코드 1 과 이유 출력, 파일 변경 없음
      파일: scripts/publish-column.js / 확인: 임시 사이트 폴더에서 정상 실행 → 세 파일 변경. `<h1>` 없는 입력 → 세 파일 바이트 동일, 종료 코드 1. (2번의 "이미 존재" 검사도 이 흐름 안으로 옮김) / 의존: 4, 5, 6, 7
- [ ] 9. `--dry-run`: 바뀔 내용(추출한 메타, 최종 URL, 쓸 파일 3개, 삽입될 `<li>` 와 sitemap 줄)만 출력하고 쓰지 않는다
      파일: scripts/publish-column.js, scripts/publish-column.test.js / 확인: 실행 후 세 파일이 실행 전과 바이트 동일, 출력에 최종 URL 포함 / 의존: 8
- [ ] 10. 성공 출력 정리: 제목·태그·날짜·요약·최종 URL·바뀐 파일 3개를 사람이 읽기 좋게 출력하고, 스크립트 맨 위 주석에 사용법 2줄을 적는다
      파일: scripts/publish-column.js / 확인: 정상 실행 출력에 다섯 항목과 세 파일 경로가 보인다 / 의존: 8
- [ ] 11. 끝단 확인: 어드민(kkeut_admin.html)을 브라우저에서 열어 실제로 글 하나를 만들어 다운로드한 파일로 스크립트를 실행한다. 명세의 완료 기준 10개를 체크리스트로 돌린다
      파일: (변경 없음, 결과만 확인) / 확인: 완료 기준 10개 모두 체크. 확인용으로 생긴 칼럼 파일·목록 항목·sitemap 줄은 되돌린다 / 의존: 9, 10

병렬 가능: 5, 6, 7 은 서로 독립 (4 가 끝난 뒤).

## 위험 요소
- **CRLF/LF 혼재**: 사이트 파일은 CRLF, 어드민 출력은 LF. 삽입 시 대상 파일의 줄바꿈을 감지해 따라야 한다. 테스트에서 줄바꿈 보존을 명시적으로 확인한다(6, 7).
- **어드민 출력 구조 의존**: 파싱은 `kkeut_admin.html` 의 `buildPage` 템플릿(h1, 태그 줄, 날짜 줄, `<article class="post-body">`)에 묶여 있다. 어드민 템플릿이 바뀌면 깨진다. 픽스처(1)를 템플릿과 똑같이 유지하고, 못 찾으면 명확한 메시지로 중단한다(4).
- **요약 불일치 가능성**: 어드민은 본문 HTML 을 `<[^>]+>` 정규식으로 벗겨 앞 90자를 요약으로 쓴다. 같은 규칙을 쓰되 `<img>` 의 긴 data URL 이 텍스트로 새지 않는지 확인한다(4, 픽스처에 `<img>` 포함).
- **큰 파일**: 사진이 들어간 수 MB 파일을 문자열로 통째로 읽는다. Node 에서 문제없는 크기지만 정규식을 전역 백트래킹 없이 단순하게 쓴다.
- **Windows 경로**: `~/Downloads/...` 같은 경로는 셸이 풀어 주므로 스크립트는 받은 경로를 그대로 쓴다. 공백 포함 경로는 따옴표로 감싸야 함을 사용법 주석에 적는다(10).
- **어드민 안내문은 옛 흐름 그대로** (명세 미결 1). 이 계획은 어드민을 건드리지 않는다.
