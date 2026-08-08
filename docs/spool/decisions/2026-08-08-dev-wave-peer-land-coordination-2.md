---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: dev-wave-peer-land-coordination
seq: 2
---

## {{D:acceptance-lease-advisory}}. 並行 wave の受入窓を排他 lease で直列化し、通知は advisory に限る

**決定:** 並行 dev-wave が同じ main を base に受入全走を重ねる衝突を、repo 外の lease directory
への排他作成 (`O_CREAT|O_EXCL`) で直列化する。取得できた 1 本だけが受入を投入し、受入と land の
終端で必ず解放する。land 成功後は保存した land 結果 JSON から固定文面を生成し、
Claude のセッション間通信で照合済み peer へ 1 度だけ main HEAD の更新を知らせる。

**land の権威は変えない。**`tools/dev_wave_land.py` の lock・ff-only・監査は不変で、lease と通知は
advisory である。受信した通知は local main を読み直す契機にだけ使い、待機・取り込み・
検査省略の根拠にしない。通知の配送は best-effort であり、順序・即時性・exactly-once を保証しない
(受信側の次の tool round まで drain されない)。

**理由:**
- 実際に無駄になるのは land の瞬間ではなく、その手前の「main 取り込み → 受入全走 (実測
  1055〜1270 秒) → land」の窓である。land 後の通知では、受入中の peer に届かず窓を閉じない。
- land 自体は既に lock 内で直列化済み (D128) であり、新しい直列化機構を land へ足す理由はない。
- 外部から来た通知は認証できない。よって受信側の作用を「再観測の契機」だけに限定すれば、
  偽の通知でも最悪の帰結は本機構が無い場合と同じ競合に留まる。

**AI 向け出力は閉じた語彙へ射影する。** 識別子は `sha256(wave)[:12]` の 12 桁 hex だけとし、
wave 名・path・branch 名の生文字列を出さない。`git check-ref-format` は指示文を含む branch 名を
受理するため、制御文字除去と長さ制限では注入面を閉じられない (規律 6)。

**却下した選択肢:**
- **セッション roster からの自動 join** — 実データでは全 worker の作業ディレクトリが repo root で
  worktree を指さず、起動文に複数のタスク ID が混ざるため一意 join が成立しない。
  宛先の特定は親が `ListAgents` で行う。
- **handoff の見出しへ宣言を相乗り** — 稼働中の実物の過半が書式非互換で宣言できず、しかも
  「宣言なし」を「並行なし」と誤報する。handoff は 10 分ごとに更新する規約なので、
  ファイル更新時刻を lease の生存判定に使うと古い宣言が恒常的に有効化される。
- **land 後の通知だけ** — 中心の窓を閉じない。

**受容した限界 (プロトタイプ基準):** TTL 超過で lease を取り直しても旧 holder の受入は止まらない
(fencing token なし)。release の権限証明は wave slug の digest だけである。claim〜release を
包む機械的な transaction は無く、契約文が終端での解放を要求するだけである。
いずれも本機構が無い場合と同じ競合へ戻るだけで悪化しない。所在は環境 runbook に書く。
