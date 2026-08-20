---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1172-land-lease-renew
seq: 2
---

## {{D:renew-non-acquiring-primitive}}. 受入 lease の land 直前 renew は非取得型 primitive で行う

**決定:** `tools/wave_land_window.py` の `claim()` を land 直前の renew として再利用しない。
同 file へ新設した `renew(lease_dir, wave)` は、既に自分 (`self_holder`) が保持し stale でない
lease の mtime だけを touch する。`_create_lease`/`_ensure_ticket`/`_queue_head`/
`_drop_ticket_best_effort` をどの分岐からも呼ばず、lease 不在・他者保持・stale・payload 不正・
retry 尽きのいずれも取得を試みない。`tools/dev_wave_land.py::main()` は `land()` 呼び出し直前で
renew を呼ぶが、stderr へのログ出力は `land()` 呼び出し後 (release ログの直前) へ遅延させる —
renew の呼び出し自体は land 直前のまま、print だけを移すことで、land() が例外・中断を送出した
場合の stderr 完全空文字契約 (`test_main_unexpected_exception_or_interrupt_never_releases`) を
壊さない。

**理由:**

- `claim()` の再利用は、[T-1275] wave (2026-08-17) の段3 敵対相談2レンズが独立に「lease/ticket
  を新規生成しうる」ことを実コードから成立させており、一度却下されている
  (`docs/archive/worklog-phase3-0817-630-631.md:561-566`)。
- 受入 lease は D253 が明記するとおり advisory 境界であり、land 自体の権威は変えない。renew の
  失敗は best-effort として扱い、land を中断しない・rc を変えない。
- print を land 呼び出し直後に置くと、land() が例外を送出する経路でも「renew を試みた」という
  ログが既に stderr へ出てしまい、既存の例外時 stderr 完全空文字契約と衝突する。呼び出しと
  ログ出力を分離することで両方の性質を保てる。

**却下した選択肢:**

- **`claim()` を renew として再呼び出しする** — [T-1275] の実測どおり、所有権を失う・
  lease/ticket を新規生成するリスクを再導入するため不採用。
- **land 直前・呼び出し直後に renew ログを即時 print する** — 実装として単純だが、land() の
  例外経路で stderr 完全空文字契約を破る。
- **stale 判定から `os.utime()` までの間の TOCTOU を renew 側で塞ぐ** — 既存 `claim()` の
  self-renew 分岐 (`:733-761`) も同型の特性を持つ既存挙動であり、renew 固有の新規リスクでは
  ないと判断した。advisory 境界の範囲内の低頻度リスクとして許容し、族一般化 (DW-G03) の閾値
  (独立2例) を満たすまで見送る。
- **`claim()` と共有ヘルパーへ self-renew ロジックを抽出する** — DRY だが、claim() の制御フロー
  に触れず所有権喪失リスクを避けるという [T-1275] の裁定意図に反し、claim() の既存テスト資産
  への波及リスクを増やす。renew() は独立実装とした。
