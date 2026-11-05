# 깃허브 저장소 만들기 작업 계획   (명세: docs/specs/github-repo.md)

작성일: 2026-11-05 · 원격: https://github.com/musicman0519-a11y/kkeut-hongdae-blog.git (비공개) · 도구: git 2.53, Python

## 설계 결정
- `.gitignore` 는 허용 목록: `/*` 로 루트를 전부 막고 `!/kkeut_seo_site/` 등 필요한 항목만 연다. 하위 폴더 안에서도 `*.xlsx`·`*.pdf`·`*.zip`·`*.gif`·`*.mp4`·`.serve.log`·`node_modules/`·`settings.local.json` 은 전역으로 막는다.
- `data/` 는 `magazine/`·`theme-baseline.json`·`admon/clinics.csv`·`admon/rules.csv`·`admon/codes.csv` 만. `data/kkeut/`·`data/admon/extract/`·캡처는 절대 안 올림.
- 점검 스크립트 `scripts/repo_check.py` 는 `git ls-files` + 스테이징 목록을 금지 패턴과 대조. 경로 패턴(kkeut/, captures/, 매출, 환자, 계약) + 확장자 + 파일 내용의 토큰 패턴(`ghp_`, `sk-`, `AKIA`).
- 첫 커밋 메시지(한국어) + Co-Authored-By. 푸시는 사용자가 URL 을 주었으므로 이번 한 번은 바로 한다. 이후 푸시는 요청 시.

## 작업 목록
- [x] 1. `.gitignore`(허용 목록) + `.gitattributes`(LF) 만들고 `git init -b main` → `git status --short --ignored` 로 막힌 것·올라갈 것 확인
      파일: .gitignore, .gitattributes / 확인: 추적 후보에 captures·data/kkeut·xlsx·pdf·gif·.serve.log 없음, kkeut_seo_site 40파일 있음 / 의존: 없음
- [x] 2. `README.md`(구성·로컬 서버·새 글 절차·검증 명령)
      파일: README.md / 확인: 명령 4개가 실제 파일과 일치 / 의존: 없음
- [x] 3. `scripts/repo_check.py` + 음성 테스트(`git add -f data/kkeut/...` 뒤 실패 → 되돌림)
      파일: scripts/repo_check.py / 확인: 정상 상태 통과, 강제 추가 시 종료 코드 1 / 의존: 1
- [x] 4. 어드민 「업로드 안내」·설정 문구를 새 절차(posts.json → build.py → 커밋·푸시)로 갱신
      파일: kkeut_admin.html / 확인: 안내 5단계가 README 와 같은 절차 / 의존: 2
- [x] 5. 첫 커밋 → `origin` 추가 → `git push -u origin main` → 깃허브에서 파일 수·README 확인(사용자)
      파일: (저장소) / 확인: push 성공, `git ls-files | wc -l` 과 용량 ≤ 15MB / 의존: 1~4
- [x] 6. scratchpad 에 clone → `build.py --check`·`check_theme.py check`·`apply_theme.py --check` 통과 → 명세·CLAUDE.md·메모리 갱신
      파일: docs/specs/github-repo.md, CLAUDE.md / 확인: clone 에서 세 검사 통과 / 의존: 5

## 위험 요소
- **허용 목록이 너무 좁아 필요한 파일이 빠짐** → 6번 clone 검증으로 잡는다.
- **파일명에 한글·공백**: 루트의 xlsx 들은 막히지만 `captures/2026-11/의원명/` 같은 경로도 폴더째 막는다.
- **줄바꿈 변환**: `text=auto eol=lf` 로 체크아웃이 LF 고정. Windows 전역 `core.autocrlf` 가 true 여도 속성이 우선.
- **큰 파일**: `kkeut_seo_site/assets/home/*.png` 12장 ~5MB 는 허용(깃허브 100MB 한도 내).

## 진행 기록
- 2026-11-05 1~5번 완료. `.gitignore`(허용 목록)·`.gitattributes`(LF)·`README.md`·`scripts/repo_check.py`(경로 6종·내용 4종, 자기 자신은 내용 검사 제외). `git init -b main` → 추적 후보 118파일 5.6MB, 막힌 것: captures/·data/kkeut/·루트 xlsx 7·pdf 4·gif·.serve.log·__pycache__·data/admon 원자료. 음성 테스트(data/kkeut CSV 강제 추가 → 검출) 통과 후 되돌림. 어드민 「업로드 안내」 5단계 갱신. 첫 커밋 3ba3c06 → origin main 푸시 성공(자격 증명은 Windows Git Credential Manager 에 이미 있었음).
  - 참고: 파이썬이 텍스트 모드로 쓴 파일(posts.json, site.css, svg, 일부 스크립트)은 로컬에서 CRLF 지만 .gitattributes 로 저장소에는 LF 로 들어감. HTML 21쪽은 로컬도 LF.
- 2026-11-05 6번 완료. 새 폴더에 clone(118파일, 10MB 체크아웃) → build --check·apply_theme --check·check_theme·repo_check 전부 통과, HTML 21쪽 LF, 민감 폴더·xlsx·pdf 없음.
