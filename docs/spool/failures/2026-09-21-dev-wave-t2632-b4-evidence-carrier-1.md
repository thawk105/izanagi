---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2632-b4-evidence-carrier
seq: 1
---

## 新規

### {{F:equivalent-mutant-drift-set-does-not-bound-control-flow-mutants}}. contract loader closure の file への変異を、等価変異で実測した drift 集合の外だけで数えようとしたが、入口停止を外す変異はその外の test からも drift へ到達した [変異帰属] [誤前提]

- 事象: [T-2632] は `orchestrator/campaign/p3_s4_loop.py` (contract loader closure の member) に変異を注入した。等価変異 E1 の注入で drift する 150 node を実測し、
  drift 一覧と交わらない新設 test だけを選べば注入の KILL を帰属できると段 6 裁定 §5 に登録した。焦点再レビューが、S13 (評価前検証の削除) と S8 (破損で `{}` を返す) は
  drive を通す破損 test の入口停止を外し、その先の `ident.ensure_campaign_identity` の live binding 照合 (drift) へ到達させると指摘した。
  E1 ではこの test は入口で止まるので drift 一覧に入らない。注入の probe で S13・S8 は同 test 8 node で落ちたが、落ちた理由は変異の狙いと区別できなかった。
- 根本原因: 等価変異の drift 集合は「等価変異の制御フローで到達する live binding 照合」しか数えない。変異が早期 return や停止を外すと、同じ test が
  等価変異では通らない経路を進み、drift に届く。drift 集合は変異ごとに違いうる。
- 恒久対応: 割り振りを直した (段 6 裁定 §5.1) — S13 は変異を独立 clone の commit に焼いて dispatch する commit 群へ移し (commit なら HEAD blob と live bytes が一致し drift が出ない)、
  S8 は loader を直接呼ぶ test だけで検出させた。final は 21 件すべて期待どおり。memory `mutation-discipline` に「closure member への変異で停止・分岐を外すものは commit 群へ」を追記した。
- 再発検知: closure member (`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`) を変異させる wave は、変異ごとに「等価変異では止まる経路を開くか」を見て、開くものは commit 群で走らせる。

### {{F:swallowed-rejection-reason-guessed-from-assertion}}. 拒否理由を握りつぶして汎用の outcome を返す既存関数の赤を、assert の文面だけから推測して fix を 1 巡空費した [誤前提] [手順漏れ]

- 事象: [T-2632] の焦点走 f2 で `test_base_provenance_duplicate_reuses_selected_attempt` が `assert 'aborted' == 'duplicate'` で落ちた。親は fixture の attempt の並び
  (採用 commit の後の abort) が原因と推測して fix を投げ、f3 でも同じ赤が残った。`_resolve_duplicate` は certified 認定の `ArtifactAdmissionError` を捕えて
  `aborted` にまとめるので、log には理由が出ない。親が読み取り probe で同じ fixture を組み直接呼ぶと、理由は `verify anomalies must be exact int zero`、
  直すと次に `receipt evidence does not match WAL verifies` (受領証の `tags` が既定の 1 件) だった。修正案を probe で確かめてから fix させ、f5 で緑になった。
- 根本原因: 拒否理由を握りつぶす関数の赤は、assert の値 (`aborted`) からは理由が一意に決まらない。親は理由を観測する前に原因を仮定した。
- 恒久対応: memory `read-the-failure-before-retrying` に「汎用 outcome に畳む関数の赤は、fix を投げる前に同じ fixture で内側の関数を直接呼ぶ読み取り probe
  (job dir、repo に入れない) で拒否理由を出し、修正案も probe で確かめる」を追記した。段 6 裁定 §4.1・§4.2 に誤診断と訂正を追記で残した。
- 再発検知: fix を投げる前に、赤の理由が log の原文 (例外文) から直接読めるかを確かめる。読めなければ probe を先に書く。

## 再発

### F71

- **再発: 2026-09-21** — [T-2632] の commit 群の自作 harness が失敗 node を `IZANAGI_FAILURE ... nodeid="[^"]*"` で抜き、引用符を含む parametrize id
  (`corrupt_report_stops[False-{"schema_version":...}]`) を途中で切った。final の前に `-rf` の要約行 (`| FAILED <nodeid>`) からの抽出へ切り替え、probe の観測も
  同じ規則で抜き直したので、誤った判定は出ていない (near miss、`output/insights/2026-09-21/t2632-b4-evidence-carrier/README.md` §6)。
