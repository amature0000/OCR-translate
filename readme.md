# OCR-translator
[![GitHub downloads](https://img.shields.io/github/downloads/amature0000/OCR-translate/total.svg?logo=github)](https://github.com/amature0000/OCR-translate/releases)

OCR-translator는 OCR을 이용해 화면의 텍스트를 추출 후 번역하는 간단한 프로그램입니다.

이 프로젝트는 [MORT](https://github.com/killkimno/MORT) 프로젝트로부터 영감을 받아 만들어졌으며, 해당 프로그램의 일부 기능을 수행합니다. 해당 프로젝트를 진행하고 유지해 주신 [monkeyhead](https://github.com/killkimno) 님께 감사드립니다.

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
![img](assets/Animation2.webp)
![img](assets/img1.png)
