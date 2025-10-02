# OCR-translator
[![GitHub downloads](https://img.shields.io/github/downloads/amature0000/OCR-translate/total.svg?logo=github)](https://github.com/amature0000/OCR-translate/releases)

OCR-translator는 OCR을 이용해 화면의 텍스트를 추출 후 번역하는 간단한 프로그램입니다.

이 프로젝트는 [MORT](https://github.com/killkimno/MORT) 프로젝트로부터 영감을 받아 만들어졌으며, 해당 프로그램의 일부 기능을 수행합니다.

# How to use
## Prerequisites
- [번역 대상 윈도우 언어 팩](https://support.microsoft.com/ko-kr/windows/windows%EC%9A%A9-%EC%96%B8%EC%96%B4-%ED%8C%A9-a5094319-a92d-18de-5b53-1cfc697cfca8)
- [gemini api 키](https://aistudio.google.com/api-keys)
## Usage
1. 설치 프로그램을 다운받아 실행한 후, 바탕화면에 생성된 바로가기를 실행합니다.
2. 실행 시 뜨는 창에서 번역할 언어를 선택해 주세요.
4. `번역하기` 버튼 또는 설정된 핫키를 눌러 화면을 캡처합니다.
5. 프로그램 창에 한글로 번역된 결과가 출력되며, 프로그램 설정값에 따라 캡처 위치에 번역 결과를 오버레이로 표시합니다.

**듀얼 모니터를 사용 중이라면, 메뉴 바의 모니터 탭을 통해 캡처할 모니터를 선택할 수 있습니다.**

## Settings
메뉴 바의 환경설정 탭을 통해 프로그램의 필수 설정값들을 수정할 수 있습니다.
- 핫키: 캡처 단축키를 지정합니다
- 프롬프트: LLM에게 OCR로 추출한 문장을 어떻게 처리할지 명령합니다.
- API: **발급받은 API 키** 및 사용할 gemini 모델명을 작성하세요.
- 폰트: 프로그램 설치 경로 `OCR Translate/app/fonts`에 원하는 폰트를 설치하여 적용할 수 있습니다.

## System prompt
환경설정의 프롬프트는 gemini가 전달받은 OCR 추출 텍스트를 기반으로 원하는 응답을 출력하도록 제어하는 명령어입니다. 해당 프롬프트는 상세한 지시 사항을 담고 있어야 하며, **"반드시 주어진 문장에 대한 번역만을 제공할 것" 이라는 지시 사항이 포함되어야 합니다**

# MORT
MORT는 사용자가 지정한 영역을 OCR(광학 문자 인식) 기술로 읽어 들인 뒤, 원하는 번역 API(예: DeepL, Papago, Google Translate 등)를 통해 실시간으로 번역 결과를 제공합니다.

# Why not MORT?
MORT 프로그램은 많은 기능을 갖췄으며, 복잡하고 정밀한 기능을 제공하지만 몇 가지 문제점이 존재합니다.
* 핫키 등록 실패: 몇몇 게임에서는 키보드 입력을 MORT가 인식하지 못해 핫키 동작이 불가능합니다.
* 문장 파싱: MORT는 화면 상의 텍스트를 분석하여 문장 단위로 분리하는데, 일부 환경에서 잘못된 분류가 발생하고, 오역이 발생합니다.
* 캐싱: LLM 토큰을 절약하기 위해 MORT는 응답을 캐싱하는데, 잘못된 응답 또한 검사 없이 캐싱하여 번역의 질이 떨어집니다.

# Difference between MORT and this project
MORT는 다양한 게임의 스토리와 대사를 번역하기 위해 개발되었으며, 반복되는 문장이 많아 캐싱 기능을 핵심적으로 지원합니다.

하지만 이러한 MORT의 특징은 경쟁 기반 게임의 중복이 적은 텍스트(툴팁, 시스템 설명 등)를 번역할 때 필요하지 않은 기능이며, 오히려 잘못된 응답을 캐싱하여 번역의 질을 저하시키는 문제가 발생할 수 있습니다.

OCR-translator 프로젝트는 이러한 문제점을 해결하기 위해 개발되었으며, MORT와는 달리 특정 종류의 게임에 최적화하는 것을 목표로 하는 프로젝트입니다.
 
# Long-term, private project
이 프로젝트는 개인이 사용하기 위한 목적으로 개발되었습니다. 일부 기능은 미구현으로 남을 수 있으며, 이 프로젝트를 참조하여 개인 프로젝트에 활용할 수 있습니다.

# Demonstration
![img](assets/Animation3.webp)
![img](assets/img.png)
