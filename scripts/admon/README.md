# 홍대 의료광고 월간 모니터링 — 재실행 절차

대상: `data/admon/clinics.csv` 에서 `포함=Y` 인 의원(2026-11 기준 26곳). 전월 파일은 `--prev` 로 넘긴다.
모든 명령은 프로젝트 루트(`E:\projects\kkeut_seo_site`)에서 Git Bash 로 실행. Python 은 `-X utf8 -I` 를 붙인다.

## 0. 준비
```bash
MONTH=2026-11
PREV="C:/Users/music/Downloads/의료광고_병원별분석_종합_홍대_10개원2026_10월.xlsx"   # 전월 완성본
mkdir -p captures/$MONTH data/admon/extract
```
전월 형식 참고 문서가 필요하면: `python -X utf8 -I scripts/admon/dump_format.py "$PREV" data/admon/format-prev.md data/admon/codes.csv`

## 1. 대상 목록 (매달 변동분만 손질)
- `data/admon/clinics.csv` 의 `포함`, `홈페이지`, `이벤트URL`, `사유` 를 갱신한다. 폐업·이전·신규는 여기서만 바꾼다.
- 엑셀로 보려면: `python -X utf8 -I scripts/admon/build_clinic_list.py data/admon/clinics.csv "홍대_피부과_대상목록_$MONTH.xlsx"`

## 2. 캡처
```bash
node scripts/admon/capture.js --clinics data/admon/clinics.csv --sites data/admon/sites.json --out captures/$MONTH --max-pages 10
# 일부만:  --only "미소앤봄의원,나인의원"
```
- 의원별 `captures/<월>/<병원명>/`: `NN_<라벨>.png`(긴 페이지는 `_p1,_p2…` 분할), 같은 이름 `.txt`(페이지 텍스트), `imgs/`(배너 원본 이미지), `meta.json`.
- 차단(403/429/503)·폐업(410)은 `captures/<월>/blocked.csv` 에만 기록된다. **우회하지 않는다.** 사용자가 직접 캡처를 폴더에 넣으면 3단계부터 똑같이 처리 — 스크린샷 모음 1장이면 PIL 로 조각을 잘라 `NN_<라벨>.png` 로 저장하고 `meta.json` 에 `manualCapture` 를 적는다(2026-11-04 프로젝트유의원 예). `blocked.csv` 에 있어도 추출 JSON 에 섹션이 있으면 `build_xlsx.py` 가 캡처 완료로 취급하고 `차단 목록` 시트 처리 열에 '수동 캡처 제공 → 추출 완료' 로 적는다. 부분 캡처라 10월 행수 70% 기준에 못 미치면 `diff` 의 '소멸' 후보는 미캡처일 뿐이니 소멸로 쓰지 않는다.
- 사이트별 설정(`data/admon/sites.json`): `eventUrls`(추가 캡처 URL), `skipUrls`(멈추는 페이지 제외), `popupNext`/`tabs`(셀렉터).
- 렌더러가 멈추면 도구가 Chrome 을 재시작하고 2차 시도는 저해상도(lite)로 찍는다. 그래도 실패하면 `meta.json` 의 `notes` 에 `capture_failed` 로 남는다 → 다시 `--only` 로 돌리거나 `imgs/` 의 원본 배너로 추출.

## 3. 추출 (의원마다 `data/admon/extract/<병원명>.json`, 스키마는 `docs/admon-extract-schema.md`)
가격이 **텍스트**로 렌더링되는 사이트는 파서로:
```bash
# 상품명/정가/이벤트가/'시술예약' 반복형 (로바에·셀린·톡스앤필 등)
python -X utf8 -I scripts/admon/text_to_extract.py 로바에의원 2026-11-02 data/admon/extract/로바에의원.json "첫방문 이벤트=captures/2026-11/로바에의원/04_event_첫방문 이벤트.txt=04_event_첫방문 이벤트.png"
# 사이트별 특수 형식
python -X utf8 -I scripts/admon/text_formats.py beautylounge "뷰티라운지의원 홍대점" 2026-11-02 data/admon/extract/뷰티라운지의원\ 홍대점.json "이벤트=<txt>=<png>"
python -X utf8 -I scripts/admon/text_formats.py ppeum "홍대예쁨주의쁨의원" ...      # 'NN% 이벤트가정가' 붙은 형식
python -X utf8 -I scripts/admon/text_formats.py maypure "메이퓨어의원 홍대입구점" ...   # '이름: 가격원' 문장형
```
가격이 **이미지 배너**인 사이트(나인·미소앤봄·오블리주·밴스 등)는 조각을 만들어 Claude 가 읽고 JSON 을 쓴다:
```bash
python -X utf8 -I scripts/admon/segments.py captures/2026-11/나인의원 <미리보기폴더> --only 02   # 2,000px 조각
```
읽을 때 규칙: 숫자가 애매하면 `"확인필요"`, 같은 배너 안 정가 불일치는 `note` 에 적는다.

## 4·5. 전월 대비 + 판정 초안 + 엑셀
```bash
python -X utf8 -I scripts/admon/diff.py --extract data/admon/extract --prev "$PREV" --out data/admon/master-$MONTH.csv --summary data/admon/diff-$MONTH.csv
python -X utf8 -I scripts/admon/build_xlsx.py --prev "$PREV" --master data/admon/master-$MONTH.csv --clinics data/admon/clinics.csv \
   --extract data/admon/extract --captures captures/$MONTH --rules data/admon/rules.csv --month "2026년 11월" \
   --out "의료광고_병원별분석_종합_홍대_26개원_2026년11월.xlsx"
```
- 판정(위반 소지·심각도)은 `data/admon/rules.csv` 기반 **[초안]** 이다. 10월 원본 판정 재현율이 범주 55%·심각도 48% 수준이라 반드시 검수한다. 규칙 검증: `python -X utf8 -I scripts/admon/judge.py --eval "$PREV"`.
- 엑셀의 `확인필요` 시트와 `차단 목록` 시트를 먼저 보고, 병원별 시트 J열·대시보드 ①의 "핵심 발견"과 요약 메모는 사람이 쓴다.
- 수식(COUNTA/COUNTIF/SUMPRODUCT/MINIFS·MAXIFS)은 Excel 이 열 때 계산된다. LibreOffice 가 없어 자동 재계산 검증은 하지 않았다.

## 알려진 한계
- 봇 차단: 프로젝트유·케이트·닥터에버스(403), 폐업: 톤즈(410). 샤인빔은 서버 502 가 잦다.
- 헤드리스 Chrome 이 멈추는 사이트(밴스·블리비·풀페이스·케이트·유앤미·벨아미 등): 홈 스크린샷 대신 `imgs/` 배너 원본으로 추출한다.
- 이미지 읽기는 오독 가능 → 모든 행에 출처 캡처가 있으니 `확인필요` 와 함께 대조.
