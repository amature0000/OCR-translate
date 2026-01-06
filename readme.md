[![GitHub downloads](https://img.shields.io/github/downloads/amature0000/SOTE/total.svg?logo=github)](https://github.com/amature0000/SOTE/releases)

![img](assets/Animation3.webp)

SOTE(Simple OCR-Translate for Everything)는 OCR을 이용해 화면의 텍스트를 추출 후 번역하는 간단한 프로그램입니다.

이 프로젝트는 [MORT](https://github.com/killkimno/MORT) 프로젝트로부터 영감을 받아 만들어졌습니다.

# SOTE - Simple OCR Translate for Everything
SOTE는 OCR을 이용해 화면 상의 텍스트를 캡처한 후, 사용자 설정에 따라 번역 서비스를 제공하는 프로그램입니다.

사용자 설정에 따라 텍스트만 추출/AI 번역/기계번역(구글)을 지원하며, AI 번역 사용 시 커스텀 프롬프트를 사용하여 맞춤 응답을 제공받을 수 있습니다.

# How to use
## Prerequisites
- [번역 대상 윈도우 언어 팩](https://support.microsoft.com/ko-kr/windows/windows%EC%9A%A9-%EC%96%B8%EC%96%B4-%ED%8C%A9-a5094319-a92d-18de-5b53-1cfc697cfca8)
- [gemini api 키](https://aistudio.google.com/api-keys) (optional)
## Usage
### [사용법 설명 링크](https://reinvented-oak-967.notion.site/SOTA-User-guide-2a14a4ebe77b801daf96f3de73345b7c)
1. 설치 프로그램을 다운받아 실행한 후, 바탕화면에 생성된 바로가기를 실행합니다.
2. 실행 시 뜨는 창에서 번역할 언어를 선택해 주세요.
3. `번역하기` 버튼 또는 설정된 단축키를 눌러 화면을 캡처합니다.
4. 프로그램 창에 한글로 번역된 결과가 출력되며, 프로그램 설정값에 따라 캡처 위치에 번역 결과를 오버레이로 표시합니다.


## System prompt
프롬프트는 상세한 지시 사항을 담고 있어야 하며, **"반드시 주어진 문장에 대한 번역만을 제공할 것" 이라는 지시 사항이 명확하게 포함되어야 합니다**
