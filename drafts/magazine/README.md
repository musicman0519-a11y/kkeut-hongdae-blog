# 끗 매거진 초안 (감수 전)

이 폴더의 글은 **원장 감수 전 초안**이다. 사이트(`kkeut_seo_site/`)에 들어 있지 않고 배포되지 않는다.

- `src/<slug>.md` — 원고(머리말 + 본문). 고칠 때는 이 파일을 고친다.
- `column-<slug>.html`, `entries.json` — `python -X utf8 -I scripts/magazine/new_column.py` 가 만든 결과. 직접 고치지 않는다.

## 절차
1. 원고 작성·수정 → `python -X utf8 -I scripts/magazine/new_column.py`
2. `python -X utf8 -I scripts/magazine/lint.py` 로 금지 표현 0건 확인
3. 원장 감수 → 수정은 1번으로 돌아가 반복
4. 감수된 글만 `python -X utf8 -I scripts/magazine/build.py --publish <slug>` → 사이트 폴더 복사 + posts.json 추가 + 전 영역 생성
5. `python -X utf8 -I scripts/check_theme.py check` 확인 뒤 `baseline` 재저장

되돌리기: `build.py --unpublish <slug>`.
