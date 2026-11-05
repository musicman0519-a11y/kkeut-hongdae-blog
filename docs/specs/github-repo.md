# 깃허브 저장소 만들기 (사이트 + 작업 도구)

작성일: 2026-11-05 · 상태: 완료(2026-11-05 — 범위 B 전체, 비공개, 호스팅 미정, 저장소 https://github.com/musicman0519-a11y/kkeut-hongdae-blog.git) · 관련: `docs/specs/magazine-ia.md`, `docs/specs/ui-restyle.md`, 어드민 「업로드 안내」(GitHub → Vercel 흐름을 전제로 쓰여 있음)

## 문제 / 목적
사이트와 생성 스크립트가 로컬 폴더에만 있어 배포·백업·이력이 없다. 깃허브에 올려 ① 변경 이력을 남기고 ② Vercel 같은 호스팅이 저장소에서 바로 배포하게 하고 ③ 다른 컴퓨터에서도 같은 작업을 이어 가게 한다. 단, 이 폴더에는 **환자 정보·세무 매출·경쟁 의원 캡처·계약서**가 함께 있으므로 올라가면 안 되는 것을 먼저 가른다.

## 조사로 확인한 사실 (2026-11-05)
- git 2.53 있음, `gh` CLI 없음 → 깃허브 쪽 저장소 생성은 사용자가 브라우저에서 한다. 폴더는 아직 git 저장소가 아니다(중첩 .git 없음).
- 폴더 안 내용과 용량: `kkeut_seo_site/` 5MB(40파일, 배포 대상) · `scripts/` 1MB · `docs/` 1MB · `data/` 3MB(이 중 `data/kkeut/` 는 환자 정보, `data/admon/` 경쟁 의원 목록·규칙, `data/magazine/` 글 목록) · `captures/` **493MB**(경쟁 의원 캡처) · `drafts/` 1MB(감수 전 초안) · 루트에 xlsx(마케팅분석표·세무 매출·의료광고 분석)·PDF(의료광고 가이드라인)·법령 md·19.7MB GIF 「메인 배너 활용.gif」(삭제된 배너 원본)·`.serve.log`.
- `kkeut_admin.html` 은 비밀번호를 브라우저 localStorage 에만 두며 파일 안에 비밀값은 없다. 다른 파일에서도 토큰·키는 없음.
- 어드민 「업로드 안내」는 "GitHub 에 파일 올리면 Vercel 이 자동 배포" 를 전제로 쓰여 있다. 지금 blog. 도메인이 어디에 떠 있는지는 기록이 없다(미결 3).

## 범위 (In)
1. **저장소 범위 = 작업 저장소 전체에서 민감·대용량 자료를 뺀 것** (추천안). 들어가는 것: `kkeut_seo_site/`, `scripts/`, `docs/`, `data/magazine/`, `data/theme-baseline.json`, `data/admon/clinics.csv`·`rules.csv`(의원 목록·판정 규칙, 개인정보 아님), `drafts/magazine/`, `kkeut_admin.html`, `CLAUDE.md`, `.claude/`(스킬·설정 중 로컬 전용 아닌 것).
2. **.gitignore 는 허용 목록 방식**: 루트의 모든 것을 막고(`/*`) 위 항목만 예외로 연다. 새로 생기는 xlsx·캡처·영상은 자동으로 막힌다. 막는 것: `captures/`, `data/kkeut/`, 루트 xlsx·pdf·법령 md·gif·`.serve.log`, `node_modules/`, OS 임시 파일.
3. **줄바꿈 고정**: `.gitattributes` 로 텍스트는 LF(`* text=auto eol=lf`), 이미지·svg 제외 바이너리는 그대로. check_theme 의 줄바꿈 검사와 맞춘다.
4. **README.md**(저장소 첫 화면용, 짧게): 폴더 구성, 로컬 서버 띄우기, 새 글 올리는 절차 3줄, 검증 명령 2줄.
5. **첫 커밋 전 점검 스크립트** `scripts/repo_check.py`: `git ls-files`(또는 스테이징 목록)에서 금지 패턴(환자·매출·captures·xlsx·pdf·zip·mp4·gif·토큰 문자열)이 하나라도 있으면 실패. 첫 커밋과 이후 커밋 전에 돌린다.
6. **원격 연결·첫 푸시**: 사용자가 깃허브에 **비공개** 빈 저장소를 만들어 URL 을 주면, `main` 브랜치로 첫 커밋("사이트·매거진 구조·재단장 2026-11-05")을 푸시한다. 커밋 메시지 끝에 Co-Authored-By 줄.
7. **배포 연결 안내**(문서만): Vercel 에서 저장소 가져올 때 Root Directory = `kkeut_seo_site`, 빌드 없음, 출력 = 그대로. 도메인 연결은 미결 3 답을 받은 뒤.
8. 어드민 「업로드 안내」를 실제 절차(저장소에 파일 넣고 posts.json 붙이고 build.py 실행 후 커밋·푸시)로 갱신.

## 범위 밖 (Out)
- 깃허브 Actions 같은 자동화(빌드 없음이라 필요 없음). 자동 배포는 Vercel 쪽 설정으로.
- `captures/`·`data/kkeut/`·xlsx 의 별도 백업(깃허브 아님, 클라우드 드라이브 몫).
- 의료광고 모니터링·마케팅 분석 스크립트의 **실행 자료**(원자료는 안 올림, 코드만 올림).
- 공개 저장소로 전환, 라이선스 선택.
- 브랜치 전략·PR 리뷰(혼자 작업이므로 `main` 하나).
- 실제 도메인 이전·DNS 변경(미결 3 뒤 별도 작업).

## 사용자 흐름
1. 내가 .gitignore·.gitattributes·README·점검 스크립트를 만들고 `git init` → 스테이징 목록을 보여 준다(민감 파일 0개 확인).
2. 사용자가 깃허브에서 비공개 저장소를 만들어 URL 을 준다.
3. 원격 추가 → 첫 커밋 → 푸시 → 깃허브에서 파일 목록 확인.
4. (선택) Vercel 에서 저장소 연결, Root Directory 지정 → 미리보기 URL 로 확인.
5. 이후: 글 발행·디자인 수정 뒤 `repo_check.py` → 커밋 → 푸시. 커밋은 사용자가 "올려줘" 할 때만.

## 완료 기준 (2026-11-05 전부 확인)
- [x] `git status` 에 `captures/`, `data/kkeut/`, 루트 xlsx·pdf·gif·`.serve.log` 가 **보이지 않는다**(ignored).
- [x] `git ls-files` 에 `kkeut_seo_site/` 40파일, `scripts/`, `docs/`, `data/magazine/posts.json`, `kkeut_admin.html`, `CLAUDE.md`, `README.md`, `.gitignore`, `.gitattributes` 가 있다. 총 용량 15MB 이하.
- [x] `scripts/repo_check.py` 가 통과하고, 일부러 `data/kkeut/` 파일을 강제 추가(`git add -f`)하면 실패한다(테스트 뒤 되돌림).
- [x] 원격 `origin` 이 사용자가 준 URL 이고 `main` 이 푸시되어 깃허브에서 README 가 보인다.
- [x] 저장소를 새 폴더에 clone 해서 `python -X utf8 -I scripts/magazine/build.py --check` 와 `check_theme.py check` 가 그대로 통과한다(필요한 파일이 다 올라갔다는 증거).
- [x] 어드민 「업로드 안내」가 새 절차를 설명한다.

## 제약
- 환자 이름·번호·매출·계약서·경쟁 의원 캡처는 어떤 경우에도 올리지 않는다(CLAUDE.md 규칙). 허용 목록 방식 + 점검 스크립트 이중 장치.
- 커밋 메시지는 한국어, 끝에 `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. 커밋·푸시는 사용자 요청이 있을 때만.
- 줄바꿈 LF 유지. 바이너리(png·jpg·svg·webp)는 변환하지 않는다.
- `gh` 가 없으므로 저장소 생성·비공개 설정·협업자 초대는 사용자가 브라우저에서.

## 가정 / 미결 질문
**가정**
- 저장소 이름 `kkeut-hongdae-blog`, 기본 브랜치 `main`, 비공개.
- git 전역 설정이 이미 있다(user.name `musicman0519-a11y`, user.email musicman0519@gmail.com) → 그대로 쓴다. 깃허브 계정도 같은 이름으로 추정.
- `.claude/` 는 올린다(스킬·설정이 작업 방식의 일부). 로컬 전용(`settings.local.json`)만 제외.
- `drafts/magazine/` 은 올린다(비공개 저장소이고 감수 절차의 일부). 공개 저장소로 바꿀 때는 뺀다.

**미결**
1. 저장소 범위: **B. 작업 저장소 전체(민감 제외)**(추천) 인지, A. `kkeut_seo_site/` 만 올리는 최소형인지. A 면 생성 스크립트·어드민이 저장소 밖에 남아 다른 컴퓨터에서 글 발행을 못 한다.
2. 비공개 저장소로 가는지(추천). 공개면 docs/(경쟁 의원 모니터링 계획)·drafts/·admon 자료를 빼야 한다.
3. blog.kkeutclinic-hongdae.co.kr 이 지금 어디에 떠 있는지(Vercel? 호스팅 업체 FTP?). Vercel 로 간다면 저장소 연결 뒤 도메인을 옮기는 작업이 따로 필요하다.
4. 깃허브 계정·저장소 URL(사용자가 만들어서 줌).
