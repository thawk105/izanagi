# 段 1 brief — [T-139] land 2 session 2 (承認 manifest + resolver + 受領証 writer + semantic validator)

- wave: `dev-wave-t139-manifest-land2-s2` / 2026-08-11
- branch: `worktree-dev-wave-t139-manifest-w2`、base tip `4c65c3f7` (session 1 の `c6ab6272` + local main 取り込み)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2`
- job artifact: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s2/`
- `F_r` = `39d760985a5e37d20464c394760bf65596156566` (D282 payload を fold した commit)
- 受入・実測環境: Pegasus。計算ノードへ出すのは受入全走のみ。所在は worklog、機体固有は環境 runbook

## 本 session は最終 session ではない → **land しない** (S6 (a))

session 1 の「入っていないもの」のうち、本 session が閉じるのは
manifest 実体 / resolver / `PreregBinding` / trust root / raw snapshot API / 受領証 writer /
固定 semantic validator / conformance vectors の 8 件である。
残る `submit_pilot` / PBS preflight / driver / collector / correctness 還流 (§S7 #4) /
certified 側 consumer / pilot 投入 / §S7 #5 (変異の単一理由帰属) / §S7 #6 (`a05` build 手順) は
本 session の scope 外であり、**少なくとももう 1 session を要する。**
したがって段 9 は local main 取り込みを行わず、branch tip を次 session へ引き渡して終える。

## 確定裁定 (2026-08-11 第 9 回、全問推奨どおり、worklog 420 / 一次控え §92)

| ID | 適用 |
|---|---|
| RP-1 | (a) manifest + resolver + 受領証 writer + 固定 semantic validator + conformance vectors を本 session に統合。D234 の**外部署名は不変**、manifest 解決は内部 helper。`alpha_reservation` は manifest へ再掲せず resolver が D282 payload から直接読む |
| RP-2 | (a) trust root は `operational_boundary` の解釈として明文化 + 安価な部分集合のみ実装。resolver source 自身の identity 束縛は境界の内側として実装しない |
| RP-3 | (a) raw snapshot API と consumer 結線を semantic validator と同時に行う |
| RP-4 | (a) pilot 解禁条件 = 公表 core 3 文書の凍結承認 + fold。**`b03` consumer を 1 行も書かない**、§S7 #7 は [T-793] へ委譲 |
| RP-5 | (a) `dev_wave_codex.py` の argv 制約 2 件は [T-789] へ。`DW-O01` は現状のまま (本 wave で編集しない) |

## scope (成果物影響つき — DW-G05)

| # | 実装するもの | 実装しない場合に成果物のどの値が動くか |
|---|---|---|
| 1 | **approval manifest 実体** (固定 path の data + loader) | 未実装なら resolver が承認集合を持たず、`submit_pilot` の受理述語が存在しない。試行台帳に「承認済み事前登録で測った」と書けない |
| 2 | **`resolve_effective_preregistration` / `PreregBinding`** (D234 決定 (7) の (i)〜(vii)) | 未実装なら `F` の子孫で core を書き換えた blob を core と申告でき、**certified 選択の根拠になる事前登録 identity が producer 選択になる** |
| 3 | **台帳 → manifest の第 1 矢印** (`F_r` の `docs/decisions.md` から D282 payload を読み manifest と exact 一致を要求) | 未実装なら `approval_fold_commit = F_r` を保った偽 manifest が自己整合し、**未承認 blob が承認済み identity になる** (§S7 #1) |
| 4 | **Git trust root 部分集合** (`PATH` 非継承・絶対 path 起動・全 `GIT_*` 破棄・`GIT_CONFIG_NOSYSTEM`・commit-graph 無効・alternates / promisor 拒否・`--no-pager`・fsmonitor 無効) | 未実装なら偽 `git` が `rev-parse` / `merge-base` を偽装し、**`F_r` より前の測定が受理される** (§S7 #2) |
| 5 | **raw snapshot API + consumer 結線** (単一 fd / snapshot、component 単位 `O_NOFOLLOW`、symlink 拒否) | 未実装なら検査時と hash 時で別 raw を読め、`a03` / run log / intent / correctness evidence の**参照先が入れ替わる** (§S7 #3) |
| 6 | **受領証 writer の認可** (§6.10。writer 自体が `PreregBinding` を必須 keyword-only で受け、三つ組と `measurement_head` を照合してから publish) | 未実装なら別経路の writer が受領証を publish でき、**防壁の支配点が消える** |
| 7 | **固定 semantic validator** (§6 の cross-field 制約全件 + §7.1 の 20 項目) | 未実装なら §7.1 の 20 項目が**1 つも発火しない**。schema 適合が受理と読み替えられ、適格 verdict が producer 申告で決まる |
| 8 | **conformance vectors** (正例 1 + §6 各制約の負例 1 本以上) + manifest による digest pin | 未実装なら承認契約 (`record-items-v2.md` §7) が満たされず、**engine の差で受理集合が動く**経路が残る |

**scope 外 (書かない):** `b03` consumer、`submit_pilot` / `submit_main` の本体、PBS preflight / driver /
collector、correctness anomaly 還流、certified 側 consumer、`DW-O01` の編集、pilot 投入。
D264 の 4 名前非 export は、gate 完成に伴い **`resolve_effective_preregistration` / `PreregBinding` の
2 名前だけ**解除しうる (下の (P3))。

## 不変条件 (破ったら赤)

1. **絶対規律 2/3 を緩める変更を入れない。** validator を通すために期待値・受理集合を緩めない
2. **D234 の外部署名は変えない** (RP-1 同束 (a))。`approval_manifest_ref` 引数を足さない
3. **`alpha_reservation` を manifest へ再掲しない** (RP-1 同束 (a))。resolver が D282 payload から直接読む
4. **manifest を単独の trust root にしない。** 必ず `F_r` の `docs/decisions.md` payload と exact 照合する
5. **`record-items-v2.md` / `receipt-schema-v1.json` / erratum / core / 追補 の bytes を 1 bit も変えない** (D282 の pin 対象)。`output/registry/t139-alpha-reservations.jsonl` は append-only で、本 session は追記も編集もしない
6. **schema は draft-07 のみ。** 実行環境の `jsonschema` は 3.2.0 で `Draft202012Validator` を持たない (実測)。`$defs` / `unevaluated*` / `format` 依存 keyword を使わない
7. **schema 適合を受理と読み替えない。** §7.1 の 20 項目は semantic validator が再計算する
8. **§8 の否定検査**: 列挙 8 field を受理条件の入力に使ったら落ちるテストを置く (prose 禁止だけにしない)
9. **恒真な gate を作らない。** 各 gate に「通る正例 1 つ」を必ず添える (`DW-S04`)
10. 実装面は Codex `role=author` が書く。親は brief・裁定・統合 commit・変異・全走・記録のみ

## 実測済みの前提 (段 1 で測った)

- `F_r` は本 checkout HEAD の祖先である (`merge-base --is-ancestor` = true)
- D282 の `record_items` / `receipt_schema` pin は実 blob と digest 一致 (57770 / 43106 bytes)
- `output/registry/t139-alpha-reservations.jsonl` は 143 bytes、`ledger_blob_sha256` /
  `reservation_entry_sha256` とも D282 payload と一致
- `jsonschema` = 3.2.0、`Draft7Validator` あり / `Draft202012Validator` なし
- **[前提の反証] `/usr/bin/git` の owner は `uid/gid = 0/0` (root) である。** RP-2 の事実欄が言う
  `65534/65534` (nobody) は段 3 lensA が **codex 子の sandbox 内で**測った値で、binary の SHA-256 は
  親環境と同一 (`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`)。
  すなわち sandbox の uid 再写像による見かけの値だった。
  **RP-2 (a) の選択と実装部分集合は変わらない** (部分集合は owner に依存しない) が、
  「(b) を採ると本環境を拒否する」という却下理由 1 本は消える。段 3 の攻撃対象に立て、段 4 で再裁定する

## 親の provisional 裁定 (攻撃対象。覆してよい)

- **(P1)** manifest は repo 内の**固定 path の 1 file** (`orchestrator/preregistration/` 配下、
  JSON) とし、resolver が private helper で読む。外部 path 指定の口を作らない
- **(P2)** manifest が pin する vectors digest は、vectors を書く lane の後に**別の codex lane が
  manifest file へ書き込む**。親は digest を手で埋めない (実装面の直接編集になるため)
- **(P3)** D264 の 4 名前非 export のうち、本 session は
  `resolve_effective_preregistration` / `PreregBinding` の 2 名前だけ export し、
  `submit_pilot` / `verify_receipt` は非 export のまま残す。
  `__init__.py` の docstring から「投入 gate ではない」宣言を**部分的に**書き換える
- **(P4)** 段 5 は 3 lane 並列 (A: manifest + resolver + trust root / B: snapshot + semantic validator /
  C: 受領証 writer + conformance vectors) + 統合後に (P2) の manifest pin lane
- **(P5)** conformance vectors は `orchestrator/preregistration/vectors/` 配下の JSON 群とし、
  `FROZEN_MANIFEST` (現 23 件、`output/**` のみ) には入れない

## 既存被覆と純増検出力 (性質で検索した結果)

既存 test で「凍結 blob の三つ組を読み digest を照合する」性質は
`test_t139_preregistration_binding.py` / `test_t139_blobref_digest_binding.py` /
`test_t139_approval_payload.py` が持つ。**持っていない性質は次で、本 session の純増検出力はここに限る。**

1. 承認集合を宣言する manifest が payload と食い違うときに拒否する検出力
2. `PATH` 上の偽 `git` / `GIT_*` 注入で祖先検査を偽装したときに拒否する検出力
3. 受領証 publish 経路が `PreregBinding` を持たないときに拒否する検出力
4. 受領証の §6 cross-field 制約・§7.1 の 20 項目それぞれに対する拒否の検出力
5. 検査中に path component が symlink へ差し替わったときに拒否する検出力

## 並列分割方針

段 2 (プラン 1 本) → 段 3 (2 レンズ並列) → 段 4 (親裁定 + 変異事前登録は**暫定**) →
段 5 (3 lane 並列 + manifest pin lane) → 段 6 (敵対レビュー 2 本並列 → fix → 変異 matrix → 受入全走)
→ 段 7 記録 → 段 8 自己改善 → 段 9 **land せず終端**。

段 4 の変異事前登録は暫定にとどめ、**段 6 で実装を読んで再導出する** (session 1 の申し送り 5)。
