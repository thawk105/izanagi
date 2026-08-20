---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1214-floor-protocol-resolver-audit
seq: 2
---

## {{D:floor-protocol-consumer-audit}}. 床値 protocol path 固定読取り consumer 6 件の現況を確定し、resolver 化は追加不要と裁定する

**決定:** 床値 protocol の固定 path を読む consumer 6 件のうち、「現在の protocol を caller に
選ばせず index authority 経由で解決する」設計 (D460 型) は既に `certified_writer_admission.py`・
`s8b_holdout_admission.py._authority()`・`tools/pegasus/floor_campaign.sh` の3件へ適用済みと確認した。
残り3件のうち `s8b_prediction_runner.py` と `s8b_ratified_freeze.py` は、呼び手が渡す
`pre_oracle_head` (ただし seal 時点の `git rev-parse HEAD` との一致検査で拘束される) 時点の
protocol bytes を証明鎖として再検証する設計であり、これを current resolver 経由に置き換えると
過去 commit 時点の証明が別の protocol bytes で再検証されてしまうため、literal path のまま維持する
のが正しい。残り1件 (`s8b_holdout_freeze.py:1362-1365`、v2 candidate 生成の working tree 直読) は
性質上 current の literal read で D460 型変換の対象になり得るが、既存の別チケット
(生成移行 chain の候補生成 CLI) が (a) `output/s8b-freeze-budget-approvals/g1.json` (承認 artifact)
不在、(b) `BUDGET_APPROVAL_SHA256` 未 ratify、(c) official mode の result.json 不在、の3条件が
揃わず今日も到達不能であることを実測し、本 wave では実装しない。

**理由:**

- `pre_oracle_head` の安全性の実体は「歴史 commit だから安全」という抽象論ではなく、
  seal 時点の `git rev-parse HEAD` との一致検査 (`s8b_prediction_runner.py:1523-1529`) にある。
  呼び手が任意の過去 commit を自由選択できる経路は実測で確認できなかった。
- 過去の別 wave の完了記録 (2026-08-17) は「証明鎖の歴史錨定3件」と表現していたが、
  実際は2件が歴史錨定、1件は current literal read (別チケットで休眠中) であり不正確だった。
  本決定はこの分類を訂正する。
- D460 自身は `certified_writer_admission` の current resolver 化だけを決定しており、
  他 module・shell wrapper の配線は「後続の裁定パッケージ」へ明示的に deferred されていた
  (恒久除外ではない)。歴史錨定 consumer を対象外とする論拠は D460 が既に決めていたからではなく、
  証明鎖の再現性を守るという本決定独自の判断である。

**却下した選択肢:**

- 残り3件を一律 resolver 経由へ変換する — 歴史錨定2件では過去の証明鎖が別 bytes で
  再検証されることになり、未承認 path 差し替えを防ぐという当初の目的と正面から矛盾する。
- 発火条件不成立のまま v2 candidate 生成側を先行実装する — 条件付き機能は発火条件を満たす
  既存 artifact が無ければ実装しない (dev-wave `DW-G04`)。承認 artifact も official result も
  存在しない状態での実装は投機的である。

**残る既知の限界 (このwaveでは対応せず、別チケットで裁定パッケージとして扱う):**

- ratified document 内の `floor_protocol.path` は canonical な相対 POSIX path であること以外の
  namespace 制約が無い dynamic pointer で、`s8b_ratified_freeze.py` の literal
  `_SELECTOR_PROTOCOL_PATH` (本決定が対象とする経路) とは独立しクロスチェックもされていない。
  literal path 側が安全でも、この dynamic pointer 側の受理拡大は未解決のまま残る (T-1216 が対象、
  本 wave の敵対相談で再確認・file:line 証跡を追加)。
- `s8b_prediction_runner.py` (`_git_bytes`)、`s8b_floor_campaign.py` (`_pre_oracle_blob`)、
  `s8b_ratified_freeze.py` の間で、ambient `GIT_DIR` / replace-refs 等を除去する Git 読取り衛生化の
  適用が不統一であり、`source_digest._sanitized_git_env` と同型の穴が複数 producer/consumer に
  またがる可能性がある (T-1215 が対象、族一般化の第2 consumer 候補として file:line 証跡を追加)。
