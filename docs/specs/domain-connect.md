# 도메인 연결 — hongdaekkeutclinic.com

작성일: 2026-11-05 · 상태: 진행 중 · 관련: `docs/specs/github-repo.md`(저장소 완료)

## 문제 / 목적
사용자가 `hongdaekkeutclinic.com` 을 샀다. 깃허브 저장소의 `kkeut_seo_site/` 를 이 도메인으로 서비스한다. 지금까지 코드에 박혀 있던 `blog.kkeutclinic-hongdae.co.kr` 은 DNS 에 응답이 없어(2026-11-05 확인) 실제로 떠 있는 사이트가 아니므로, 새 도메인을 **유일한 기준 주소**로 삼는다.

## 조사로 확인한 사실
- 옛 도메인은 사이트 21쪽의 canonical·og:url, sitemap 18줄, robots.txt, build.py `BASE_URL`, 어드민 기본값, 초안 8편에 들어 있다(총 40여 파일).
- `nslookup` 결과 새 도메인·옛 도메인 모두 아직 아무 데도 가리키지 않는다.
- 저장소는 비공개. GitHub Pages 는 비공개 저장소에서 유료 플랜이 필요하므로 **Vercel(무료 Hobby)** 로 한다. 어드민 안내도 원래 Vercel 전제였다.

## 범위 (In)
1. **코드의 기준 도메인 교체**: `scripts/set_domain.py https://hongdaekkeutclinic.com` 한 번 → canonical·og:url·sitemap·robots·build.py·어드민 기본값. 초안은 `new_column.py` 로 재생성, 허브는 `build.py` 로 재생성. 기준선 재저장(canonical·og_url 변경은 의도된 것).
2. **Vercel 연결(사용자가 브라우저에서)**: vercel.com → Add New Project → GitHub `kkeut-hongdae-blog` import → **Root Directory = `kkeut_seo_site`** → Framework Preset = Other, Build Command 비움, Output Directory 비움 → Deploy → `*.vercel.app` 주소에서 사이트 확인.
3. **도메인 추가(Vercel)**: Project → Settings → Domains → `hongdaekkeutclinic.com` 추가(www 는 자동으로 apex 로 리디렉트 설정 권장).
4. **DNS(도메인 산 곳에서)**: Vercel 이 알려 주는 값 그대로. 보통 apex 는 `A  @  76.76.21.21`, www 는 `CNAME  www  cname.vercel-dns.com`. 전파 뒤 Vercel 이 SSL 을 자동 발급.
5. **확인**: `https://hongdaekkeutclinic.com/` 200, `https://www.hongdaekkeutclinic.com/` → apex 리디렉트, `/sitemap.xml`·`/robots.txt` 가 새 도메인, 아무 시술 페이지의 canonical 이 새 도메인.
6. 커밋·푸시(도메인 교체분) → Vercel 자동 재배포.

## 범위 밖 (Out)
- 옛 도메인에서의 리디렉트(떠 있지 않으므로 할 것이 없음). 나중에 옛 도메인을 살리면 301 로 새 도메인에 보낸다.
- 네이버 서치어드바이저·구글 서치콘솔 등록(별도 작업, 도메인이 뜬 뒤).
- 어드민(kkeut_admin.html)을 웹에 올리는 것(로컬 파일로만 쓴다).

## 완료 기준
- [ ] `set_domain.py --show` 가 새 도메인 한 종류만 보고한다. check_theme 통과·기준선 재저장.
- [ ] Vercel 배포 URL 에서 index·columns·jemo 가 뜬다.
- [ ] `https://hongdaekkeutclinic.com/` 과 `/sitemap.xml` 이 200 이고 canonical 이 새 도메인이다. www 는 apex 로 간다.
- [ ] 푸시 뒤 Vercel 이 자동 재배포한다(커밋 → 1~2분 뒤 반영).

## 제약 / 가정
- 호스팅 UI 조작·DNS 입력은 사용자가 한다(브라우저 도구 없음). 나는 코드·검증·명령을 맡는다.
- 기준 주소는 `https://hongdaekkeutclinic.com`(www 없는 apex). www 는 리디렉트.
- 도메인 등록 업체는 미확인 → DNS 입력 화면이 다르므로 알려 주면 그 업체 기준으로 안내.
