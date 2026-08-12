---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-exec-loc-and-usage-fixes
seq: 3
---

## 新規

### {{F:waiter-zero-before-artifact}}. 待ち手が producer 生存・成果物不在のまま exit 0 を返した [fail-open] [完了誤認]

- 事象: 段 5 の実装子 C を待つ `tools/dev_wave_wait.py producer` が exit 0 で終了し、
  harness が「完了」を通知した。しかしその時点で `.done` も成果物 `.md` も存在せず、
  producer は `ps` で生存していた。3 点照合 (成果物実在 + `.done` + producer 死) で弾いて
  待ちを張り直したところ、子は約 3 分後に正常完了した。
- 根本原因: 未特定。待ち手の出力ファイルは空で、`/proc/<pid>/stat` を読めず pid-only へ縮退した旨の
  行だけが残っていた。再現条件を確定できていない。
- 恒久対応: 待ち手の 0 復帰を完了の十分条件にしない。`DW-C00` は「完了は `.done` と exit code だけで
  判定し、grep も通知も判定にしない」と定めるが、**待ち手自身の 0 復帰も同じく判定にしない**。
  親は 3 点照合を必ず行う。本 wave では全 8 子でこれを実行し、1 件の誤検出を捉えた。
- 再発検知: 待ち手が 0 を返したのに成果物が無い場合は必ず本エントリを参照し、
  producer 生存を `ps -p <pid file の pid>` で確認してから再び待つ。

### {{F:uncommitted-registry-blocks-codex-launch}}. admission registry の未コミット差分が codex 子の起動を止めた [手順漏れ]

- 事象: 段 6 の敵対レビュー 2 本が、起動前検査
  `NG: Codex hook 配線の exact 検証に失敗: tools/pegasus/admission_registry.json:
  working bytes が HEAD blob から drift` で launcher_error になった。段 5 の実装子 C が
  同ファイルを変更した直後だったため。2 本とも成果物ゼロで失敗した。
- 根本原因: codex 子の起動時 hook 配線検証は、hook が依存する正本ファイルの working bytes が
  HEAD blob と一致することを要求する。段 5 → 段 6 の間に統合 commit を挟まないと、
  実装子が触った正本ファイルが必ず drift している。
  既知事象は `docs/dev-wave/` の未コミット差分だったが、**同型の穴が admission registry にもある**。
- 恒久対応: 実装子が hook 正本ファイル (`hooks/**`、`tools/pegasus_admission_registry.py`、
  `tools/pegasus/admission_registry.json`) を触った wave では、段 6 のレビュー子を投げる前に
  統合 commit を作る。`DW-S06-B` の「real 所見へ fix を投じる前に統合 snapshot patch を退避する」を
  レビュー投入前へ前倒しする形になる。
- 再発検知: 段 6 で launcher_error が出たら、まず `git status` の実装面差分と
  子の log 先頭行 (`NG: Codex hook 配線の exact 検証に失敗`) を照合する。

### {{F:parametrized-expected-nodes-abort-mutation}}. 変異 spec の期待 node に parametrize 済みテストの素の名前を書いて起動前に止まった [手順漏れ]

- 事象: 変異 harness が
  `期待 node が pytest collection に実在しない` で 2 度 abort した。原因は期待 node に
  `test_incomparable_usage_replicas_remain_fatal` のような素の関数名を書いたことで、
  実際の node id は `...[cache_read_input_tokens]` のように parametrize 接尾辞を持つ。
  併せて spec の必須 field `timeout_seconds` / `hang_timeout_seconds` の欠落と、
  `--attempt-out` の既存ファイル衝突でも各 1 回 abort した。
- 根本原因: 期待 node を実装から目視で導出したため、parametrize の展開を見落とした。
  `DW-M08` は「期待 node は完全集合」と定めるが、完全集合の**導出方法**は定めていない。
- 恒久対応: 期待 node は目視でなく **probe 走の `failed_nodes` から機械的に再導出する**。
  `DW-M08` が認める「初回を probe と明記して再登録・再走する」経路をそのまま使うのが最短で、
  本 wave もそうした (probe 台帳と本走台帳の双方を insights へ残した)。
- 再発検知: 変異 harness の abort メッセージ 3 種
  (`spec の field 集合が不正` / `期待 node が pytest collection に実在しない` /
  `fresh --attempt-out が既に存在する`) は、いずれも走行ゼロの起動前拒否である。
