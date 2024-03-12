# AGV 알고리즘 개발 일정

## 손성준

### 1. 데이터 추출 및 매핑

- **목표**: Excel 데이터를 추출하고 시각화하여 쉽게 이해할 수 있는 형태로 변환
- **작업 내용**:
    - Excel 데이터를 추출하여 필요한 정보를 정확하게 파악
    - 데이터를 매핑하여 시각화 도구를 사용하여 그래픽으로 표현
- **예상 완료일**: 2024.03.14

### 2. 충전 알고리즘 구현

- **목표**: 배터리충전 알고리즘을 추가
- **작업 내용**:
    - 배터리가 기준치까지 소진되면 충전소 이동 알고리즘 구현
    - 충전 중인 AGV를 제외한 AGV들끼리 업무를 수행하도록 
- **예상 완료일**: 2024.04.01

### 3. 회피 방식 및 회전 알고리즘 추가(제자리 선회 지양)

- **목표**: 에너지, 부품 소모 및 마모를 방지를 위한 알고리즘 구현 
- **작업 내용**:
    - 다양한 방식의 회피 알고리즘이 존재, AGV가 자리를 물고(3node)가면서 대처 
    - FMS가 직접 경로를 지정해서 회피할 수 있도록 하는 알고리즘도 고려
- **예상 완료일**: 2024.04.15

### 4. 시뮬레이션 시스템 구현

- **목표**: AGV 알고리즘의 동작을 시뮬레이션하여 시각적으로 확인 가능한 시스템 구현
- **작업 내용**:
  - 주어진 input 데이터를 원하는 output 를 줄 수 있도록 코드 구현
  - AGV 알고리즘이 구현된 시스템을 시뮬레이션 환경에 구축
  - AGV의 작업 수행 과정을 시각화하여 영상으로 제공
- **예상 완료일**: 2024.05.01