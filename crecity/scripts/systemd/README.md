# systemd 유닛 — 주기 작업 3종 (런치 체크리스트 L-6)

배포 호스트에서 스윕·릴레이 스크립트를 주기 실행한다. **등록·기동은 배포를 결정한 시점에**
한다(2026-08-13 결정: 당분간 배포하지 않음). 여기 파일은 그때 바로 쓸 수 있게 미리 써 둔 것이다.

| 유닛 | 주기 | 하는 일 |
| --- | --- | --- |
| `crecity-outbox-relay` | 1분 | 미발행 Outbox 이벤트 → 인앱 알림 변환 |
| `crecity-order-sweep` | 5분 | 주문 72h 만료 전이 + 마감 임박 알림 |
| `crecity-campaign-sweep` | 10분 | 지원 마감일 경과 공고 자동 CLOSED |

주기는 각 스크립트 docstring의 crontab 예시와 같다.

## 전제

- 리포지토리 루트: `/srv/crecity` (venv은 `/srv/crecity/.venv`)
- 실행 계정: `crecity` (리포와 `.env` 읽기 권한 필요)
- `.env`는 `core/key/secret_manager.py`가 **파일 위치 기준 절대경로**로 읽는다 —
  유닛에서 `EnvironmentFile`로 주입하지 않는다. `PYTHONPATH`만 넘긴다.

경로·계정이 다르면 복사 전에 치환한다.

```bash
sed -i 's#/srv/crecity#<실제 경로>#g; s#^User=crecity#User=<실제 계정>#; s#^Group=crecity#Group=<실제 그룹>#' *.service
```

## 설치

```bash
sudo cp crecity-*.service crecity-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now crecity-outbox-relay.timer crecity-order-sweep.timer crecity-campaign-sweep.timer
```

## 확인

```bash
systemctl list-timers 'crecity-*'          # 다음 실행 시각
sudo systemctl start crecity-order-sweep   # 주기를 기다리지 않고 1회 실행
journalctl -u crecity-order-sweep -n 50    # 실행 로그(스크립트 print가 그대로 들어온다)
journalctl -u crecity-outbox-relay -f
```

## 설계 판단

- **중복 실행 방지는 systemd가 한다** — `Type=oneshot` 유닛이 아직 실행 중이면 타이머가
  다시 트리거해도 systemd가 같은 유닛의 두 번째 인스턴스를 띄우지 않는다(job이 병합된다).
  cron처럼 별도 락 파일(`flock`)을 둘 필요가 없다.
- **로깅은 journald에 맡긴다** — 스크립트가 stdout에 찍는 실행 결과를 `SyslogIdentifier`로
  구분해 받는다. 파일 로그를 따로 두지 않으므로 로테이션 설정도 필요 없다
  (보존 기간은 호스트의 `journald.conf`를 따른다).
- **`TimeoutStartSec`은 주기보다 짧게** — 매달린 실행이 다음 주기를 계속 밀어내지 않도록
  끊는다. Outbox 릴레이는 발행 마킹 전에 죽어도 다음 주기가 재처리한다(유실 없음).
- **`Restart=`를 두지 않는다** — 실패하면 다음 주기가 자연스러운 재시도다. 즉시 재시도는
  DB가 내려간 상황에서 로그만 불린다.
- **`ProtectSystem=strict`는 파일시스템을 읽기 전용으로 만든다** — 현재 `DATABASE_URL`은
  TCP(host:port) 접속이라 문제가 없다. 배포 호스트에서 PostgreSQL 유닉스 소켓으로 붙인다면
  각 `.service`에 `ReadWritePaths=/run/postgresql` 한 줄을 더한다(소켓 연결에 쓰기 권한이 필요).
- **타이머 시작 시각을 어긋나게 뒀다**(`OnBootSec` 1·2·3분) — 부팅 직후 세 작업이 같은
  순간에 DB를 치지 않게 한다.
