---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2792-a1-sized-rerun-auth
seq: 1
---

## {{D:a1-sized-rerun-authorization-record-gate}}. A-1 sized の認可済み独立再現は、driver 側の定数 1 件と durable base の exact な認可 record の一致でだけ rear gate を解除し、解除対象を先行 attempt-0001 に限り、公開先は兄弟 dir とする

**決定 (D2172 項 2 の実装、択 1):** `orchestrator/campaign/paper_story_a1_paired.py` に次を実装した (Codex author、敵対レビュー 2 本、変異 matrix)。

1. **認可の exact 集合は driver の定数 1 件** `V3_SIZED_RERUN_AUTHORIZATIONS = {(sized study, "attempt-0002", "attempt-0001", "D2172", 2, "2026-09-20")}`
   (構造 = study_id, attempt 名, 解除対象の先行 attempt 名, 裁定 D 番号, 項, 裁定日)。record だけを権威にせず、将来の attempt-0003 は
   新しい裁定と定数の追加 (diff に現れる) を要する。
2. **record** は `<durable base>/<attempt 名>.authorization.json`、schema `paper-story-a1-paired-rerun-authorization/v1`、key 集合 exact =
   `{schema_version, study_id, attempt_root, source_commit, decision{id, item, decided_on}, authorization_sha256}`。self digest は
   `authorization_sha256` を除いた canonical JSON の SHA-256 (破損検出であって署名ではない)。解除対象の先行 attempt 名は record に持たせない。
   producer は subcommand `authorize-rerun` (全項目必須、定数 membership、intent / attempt root / record の不在、既存 base を要求、create-only)。
3. **rear gate** `_assert_no_prior_v3_bench_start(base, *, study_id, current_attempt, source_commit)` は走査前に record を照合し、候補 loop の末尾 2 箇所の
   「group rerun is prohibited」だけを `released = 一致 record かつ 候補 == base/attempt-0001` のとき skip する。不一致 record (別 attempt 名・別 study・
   別 source sha・裁定 field・digest・余分 key・symlink・破損) は無視でなく拒否。先行証拠の完全性検査と study differs の拒否は無条件。
   attempt-0001 以外の同 study の先行 attempt が bench に到達していれば拒否。intent / attempt root / 受領証 namespace の再使用拒否、
   anomaly 即 reject、非認証 lane は 1 byte も変えない。
4. **公開先 gate** `_exact_materialization_destination(..., attempt=, base=, source_commit=)` は 3 引数とも None なら従来、一部指定は拒否、全指定は
   base == policy base と `_validate_attempt_root` の後に record を照合し、一致時だけ兄弟 dir `<materialization_relative_path>-<attempt 名>`
   (`output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`) を expected にする。不在 = 従来の exact leaf、不一致 = 拒否。
   create-only と親 dir 実在は不変。attempt-0001 の leaf 配下には置かない。
5. **事前登録 §6.1 / §6.4 の追補 (別版)** は `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`。将来の attempt-0002 一件に限り、
   元の事前登録・policy・契約 v2・source 追補の bytes と attempt-0001 の判定・限定 L-A1S-4 は不変 (遡及しない)。erratum の名で正当化しない。
   束縛は source commit 経由で、契約 JSON / policy に sha を足さない (追補 file 自身の実行時 digest 検査は無い)。
6. **投入は本決定に含めない。** 順序は「全成果物の land → fresh submit-tree の確定 → `authorize-rerun` で record → `submit`」。どこかの層で落ちたら再投入せず報告して止める。

**理由:**
- 「1 attempt 限定」を人手 (record を書かないこと) に委ねず、定数で機械化する。record は source sha (land 後にしか確定しない) を供給し、durable base に
  置くことで「改めて認可した」事実を証拠の隣に残す (D2156 項 3 の機械化)。
- 相談 (段 3) の must-fix A1: 認可対象の attempt を限定しても、解除する先行証拠を限定しなければ、attempt-0003 が既に bench に達していても attempt-0002 が
  通る。定数に先行 attempt 名を固定して閉じた。
- 兄弟公開先は「pilot の公開先には何も書き足さない」(§6.1) と同型で attempt-0001 の leaf に触れない。leaf 配下 (一次資料 §7 の例) は第 2 attempt の公開が
  第 1 attempt の leaf の存在に依存する。
- 実測: 実 base の複製に対し patch 後の gate は record 無し = 拒否、exact = 受理、不一致 9 種 = 拒否。計算ノード焦点走 1697 passed / 0 failed。
  変異 matrix (独立 clone) の結果は一次資料 `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` §5。

**却下した選択肢:**
- record だけを権威にし定数を持たない — 任意の attempt 名の record で解除でき、「1 attempt 限定」が人手の運用になる。
- 不一致 record を無視して従来動作にする — 誤った record を置いた投入が「record 不在」と区別できず、拒否理由が曖昧になる。
- 認可 attempt の公開先を attempt-0001 の leaf 配下 `…/attempt-0002` にする — 凍結 leaf の内容集合を増やし、leaf の存在に依存する。
- record に追補 file の sha を持たせる — source commit が追補を含む tree を束縛するので冗長。契約 JSON / policy へ sha を足す案は凍結 bytes の改版になる。
- 手書き JSON で record を作る — key 集合と digest を誤りやすい。小さい producer で exact 性を機械化した。
