# ODL 납품 QA 도구

1. 촬영 PC에서 축약 패키지 만들기 (기존과 동일)
   python odl_pack_for_analysis.py "녹화폴더\records"

2. 분석 PC에서 QA 실행 (ZIP을 풀어 한 폴더에 세션별 폴더로 둔 뒤)
   pip install numpy pandas scipy opencv-contrib-python-headless pyyaml imageio-ffmpeg
   python odl_delivery_qa.py <패키지_폴더> <calibration.yaml> <결과_폴더>

결과: qa_report.md (구매자용 1장 요약), per_frame_blur_<세션>.csv (프레임별 블러), b1/b2/b3 상세 표.
캘리브레이션 검사는 세션당 몇 분 걸립니다. 빠르게 보려면 --skip-calib.

추가(2026-11-01): per_frame_view_<세션>.csv — 프레임별 카메라 방향(수평 아래 각도, 기울기, 고개 돌림 속도). 작업대 작업 구간과 이동·정면 응시 구간을 각도로 거를 수 있습니다.
