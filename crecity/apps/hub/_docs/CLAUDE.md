# CLAUDE.md — hub (허브)

앱 간 협력의 단일 교차점. 계약(포트·DTO)만 소유하고 구체 스포크를 import하지 않는다.
현재 슬라이스: dispatcher(`GET /hub/myself`). 공개된 교차 협력 계약은 아직 없다.
스포크가 소비할 포트는 `hub/app/ports/`에, DTO는 `hub/app/dtos/`에 둔다.
