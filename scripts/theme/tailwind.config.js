// Tailwind 설정(색·글꼴 토큰). 정적 CSS 는 scripts/theme/tailwind_extract.js 가 이 설정으로 만든다.
tailwind.config = { theme: { extend: {
  fontFamily: { sans: ['Pretendard','system-ui','sans-serif'], 'serif-kr': ['Gowun Batang','serif'], display: ['Marcellus','serif'] },
  colors: { rose:'#E0507A', pink:'#FFC0CB', blush:'#F1A1AF', pinksoft:'#FDEEF3', ink:'#181818', kakao:'#FEE500', naver:'#03C75A' }
} } }
