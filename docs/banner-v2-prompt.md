# 메인 배너 v2 — AI 영상 생성 프롬프트·규격서

작성일: 2026-11-04 · 계획: docs/plans/main-banner-v2.md · 결과 파일 넣는 곳: 프로젝트 루트 `banner-src/`

## 0. 한눈에 보는 절차
1. 아래 **①정지 이미지 프롬프트**로 글자 없는 컷을 1~3장 만든다 (Nano Banana / Midjourney / Ideogram 등).
2. 마음에 드는 컷 1장을 **②영상 프롬프트**와 함께 이미지→영상 서비스에 넣는다 (Kling 추천, 아니면 Runway Gen-4, Veo).
   - 시작 프레임과 **끝 프레임에 같은 이미지**를 넣을 수 있는 서비스(Kling·Runway)면 그렇게 한다 → 반복 재생 시 튀지 않는다.
3. 1080p 로 내려받아 `banner-src/` 에 넣는다. 후보가 2~3개면 더 좋다. 파일명은 `서비스_번호.mp4` (예: `kling_01.mp4`).
4. 아래 **③출력 조건 체크리스트**를 확인하고 알려 주면 변환·적용으로 넘어간다.

## ① 정지 이미지 프롬프트 (이미지→영상의 첫 프레임용)
구도 핵심: 나중에 위아래를 잘라 **가로로 긴 띠(1920×660)**만 쓴다. 그래서 얼굴·어깨가 **화면 세로 가운데 60% 안**에 들어와야 한다. 머리 위와 가슴 아래는 잘려도 된다.

**영어 (그대로 복사)**
```
Beauty editorial photo, young Korean woman in her early 20s, long straight light-brown hair, dewy glowing skin, natural soft makeup, gentle closed-lip smile, wearing a plain white off-shoulder top. Medium close-up, centered, facing camera, shoulders relaxed, hands out of frame. Head and shoulders fully inside the vertical middle 60% of the frame, generous empty space on the left and right sides. Seamless solid dusty-pink studio background (#E9C9C6), soft diffused front lighting, no shadows on background. Clean, minimal, high-end Korean skincare clinic advertisement look. 16:9, 4K, photorealistic, sharp focus on eyes.
Negative: text, letters, logo, watermark, caption, jewelry, hat, glasses, hands on face, props, busy background, gradient background, harsh shadows, oversaturated, extra fingers, distorted face.
```

**한국어 (한국어 입력을 받는 서비스용)**
```
뷰티 화보 사진. 20대 초반 한국 여성, 길고 곧은 밝은 갈색 머리, 촉촉하고 윤기 나는 피부, 자연스러운 옅은 화장, 입을 다문 은은한 미소, 흰색 오프숄더 상의. 정면을 보는 미디엄 클로즈업, 화면 정중앙, 어깨 편안하게, 손은 화면 밖. 얼굴과 어깨가 화면 세로 가운데 60% 안에 들어가고 좌우에는 빈 공간을 넉넉히. 연한 분홍(#E9C9C6) 단색 스튜디오 배경, 부드러운 정면 확산광, 배경에 그림자 없음. 깔끔하고 고급스러운 한국 피부 클리닉 광고 느낌. 16:9, 4K, 사실적, 눈에 초점.
제외: 글자, 로고, 워터마크, 자막, 장신구, 모자, 안경, 얼굴에 올린 손, 소품, 복잡한 배경, 그라데이션 배경, 강한 그림자, 과한 채도, 손가락 변형, 얼굴 왜곡.
```

참고 첨부: 현재 포스터 `kkeut_seo_site/assets/banner/poster.jpg` 를 **색감·분위기 참고**로만 첨부해도 된다. 단 "같은 얼굴로" 는 요청하지 않는다(실존 모델 초상권). 글자가 들어 있는 사진이라 "글자는 넣지 말 것" 을 반드시 같이 쓴다.

## ② 영상 프롬프트 (이미지→영상)
움직임은 **아주 작게**. 카메라는 고정. 크게 움직일수록 얼굴이 무너진다.

**영어 (그대로 복사)**
```
Static camera, no camera movement. The woman slowly blinks once, breathes gently, and tilts her head very slightly to one side while keeping the soft smile. Her hair sways subtly as if in a faint breeze. Skin keeps its glow, lighting stays constant, background stays a solid dusty-pink. Slow, calm, elegant, minimal motion, like a luxury skincare commercial. No text, no logo, no watermark. 5 seconds, 1080p, 24fps.
Negative: camera zoom, camera pan, fast motion, hands entering frame, face morphing, extra fingers, flicker, text, watermark, background change.
```

**한국어**
```
카메라 고정, 카메라 움직임 없음. 여성이 천천히 한 번 눈을 깜빡이고, 가볍게 숨 쉬며, 은은한 미소를 유지한 채 고개를 아주 조금 기울인다. 머리카락이 약한 바람에 살짝 흔들린다. 피부의 윤기와 조명은 그대로, 배경은 연분홍 단색 유지. 느리고 차분하고 고급스러운 최소한의 움직임, 고급 스킨케어 광고처럼. 글자·로고·워터마크 없음. 5초, 1080p, 24fps.
제외: 줌, 패닝, 빠른 움직임, 손이 화면에 들어옴, 얼굴 변형, 손가락 변형, 깜빡임(플리커), 글자, 워터마크, 배경 변화.
```

## 서비스별 설정 메모
| 서비스 | 설정 | 비고 |
|---|---|---|
| **Kling 2.x** (추천) | Image to Video · Professional 모드 · 5초 · 16:9 · 1080p · **End frame 에 시작 이미지를 다시 넣기** | 루프가 가장 깔끔. 유료 플랜이어야 워터마크 없음 |
| Runway Gen-4 (Turbo) | Image to Video · 5초 · 16:9 · 1080p · Last frame 에 같은 이미지 | 움직임이 큰 편이라 프롬프트에 "subtle" 강조 |
| Google Veo 3 (Flow/Gemini) | Frames to Video · 8초 · 1080p · **소리 끄기** | 소리가 붙어 나오면 변환 때 제거함 |
| Hailuo 02 / Pika | Image to Video · 6초 · 1080p | 후보 추가용 |

## ③ 출력 조건 체크리스트 (받은 뒤 확인)
- [ ] 해상도 1920×1080 이상 (720p 는 받지 않는다)
- [ ] 24fps 이상
- [ ] 길이 4~10초 (끝 프레임을 시작과 같게 했으면 5초면 충분)
- [ ] 화면 어디에도 글자·로고·워터마크 없음
- [ ] 얼굴·어깨가 세로 가운데 60% 안에 있음 (위아래 20% 씩 잘려도 되는지 눈으로 확인)
- [ ] 손가락·치아·머리카락 경계가 뭉개지지 않음
- [ ] 상업 이용이 허용되는 플랜으로 생성함
- [ ] 시술 전후 비교를 연상시키는 연출 없음 (의료광고 규제)

## 받은 파일 넣는 곳
```
E:\projects\kkeut_seo_site\banner-src\   ← 여기에 mp4 저장 (사이트 폴더 kkeut_seo_site\ 에는 넣지 않음)
```
확인 명령 (Git Bash, 프로젝트 루트):
```bash
ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration -of default=nw=1 banner-src/kling_01.mp4
```
