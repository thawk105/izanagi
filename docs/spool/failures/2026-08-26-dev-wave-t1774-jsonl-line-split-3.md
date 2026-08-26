---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1774-jsonl-line-split
seq: 3
---

## 再発

### F606

- **再発: 2026-08-26** — 段 1 の編集面重複走査を、変更予定の production file 2 本の path だけで
  組んだため、1 回目の走査が稼働中 wave の編集中 file を落とした。実際には別 wave が
  `orchestrator/tests/test_codex_worker_launch.py` を編集しており、その file は本 wave が
  負例テストを置く自然な置き場だった。「重複ゼロ」と brief に書く直前にテスト file を
  含む pattern で走査し直して検出したため、偽の結論には至っていない (near miss)。
  型は F606 と同じ「走査の網が実際の編集予約より狭い」である。
  走査対象は変更予定の production file だけでなく、**その file を検査する既存テスト file と、
  新設予定の path** も含めて組む。恒久対応は F606 既存のとおり変わらない。

## supersede 追記

- F609 **supersede: 2026-08-26** — 「恒久対応: 未実施」を解消した。`parse_jsonl` を含む 6 式を `split("\n")` / `split(b"\n")` へ置き換え、U+0085 / U+2028 / U+2029 を含む event 行を受理する負例テストと、6 式それぞれの変異を単独で kill する CRLF 負例テストを `orchestrator/tests/test_codex_jsonl_line_split.py` に置いた。実測した受理差と却下した代案は {{D:jsonl-line-boundary-is-lf-only}} が正本である。**同型の未修理箇所が 1 つ残る** — `tools/check_codex_hooks.py` の `_parse_events` が Codex JSON event の str stdout を `splitlines()` で切っており、同じ 3 文字で同じく割れる。D971 が 6 箇所を明示列挙しているため本 wave では触らず、担い手を新しい T として起票した。
- F540 **supersede: 2026-08-26** — 「根本原因: 特定できていない」は F609 が特定し、本 wave が恒久修理した。当時は読み取り時点の pending 系条件が疑われたが、実際は完成した stdout の 1 event が U+2028 / U+2029 で 2 行に割られ、`Unterminated string` になって `stdout_invalid` が立っていた。`_evidence_status()` がどの条件で invalid を返したかを receipt へ記録する改修は、本 wave の scope 外として引き続き裁定パッケージにある。
