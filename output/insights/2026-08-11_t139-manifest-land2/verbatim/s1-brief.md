# [T-139] land 2 — 段 1 brief (session 1)

branch `worktree-dev-wave-t139-manifest-w2`、開始 tip `9bec416f` (local main `62ddcc93` 取り込み済み)。
land 1 の fold commit `F_r` = `39d760985a5e37d20464c394760bf65596156566`。
S6 (a) により land 2 は複数 session に跨る。**land は最後の session が 1 回だけ行う。本 session は land しない。**

## 本 session の scope (land 2 全体の第 1 分割)

1. **erratum v2 対応** — `_validate_t139_core_s7_stresscheck_v1` を承認済み v2 (2 operation) 用へ書き換え、
   `DRAFT_ERRATA` → `APPROVED_ERRATA` へ移し、test の path/digest pin を承認 payload へ差し替える。
   *不実装なら:* 承認済み core 合成が 1 度も再現できず、以後の全 manifest が `composed_sha256` を持てない。
2. **approval manifest + resolver** (`resolve_effective_preregistration` / `PreregBinding`) —
   §S7 #1 (台帳 → manifest の第 1 矢印)、#2 (`PATH` 差し替え)、#3 (symlink / TOCTOU) を必須検査に含める。
   *不実装なら:* `approval_fold_commit = F_r` を保った偽 manifest が未承認 blob を承認済み identity にでき、
   certified 選択・材料レポート・試行台帳の全参照が未承認 blob を指しうる。

**本 session で着手しない** (同一 branch の後続 session): 受領証 writer + 固定 semantic validator、
`a13` 台帳 consumer、`submit_pilot` + PBS preflight / driver / collector、correctness verifier の構造化還流、
certified 側 consumer、pilot 投入・測定。

## 確定済みユーザー裁定 (覆さない)

R1 (a) 2 段 land / R3 (a) `a13` は canonical main 台帳・append-only 全履歴検査 /
R5 (a) `verify_receipt` → `verify_prereg_receipt` へ改名 / S1 3 文書承認済み / S2 core 逐語は 2 operation /
S4 pilot slot は exact `[1..8]` / S5 (a) 予約 entry は land 1 で main 済み / S6 (a) 複数 session・land 1 回 /
S7 7 層は land 2 の必須要件 / C-2b `b03` の正本は公表 core 側、land 2 は消費側 / D264 4 名前の非 export は本 wave が解く。

## 不変条件

- **D282 が承認した 6 blob の bytes を 1 bit も動かさない** (`target_core` / `addendum_a` / `derivation_map` /
  `erratum_s15` / `record_items` / `receipt_schema` / `erratum_s7_v2`)。動かすなら承認 decision の再発行が要る。
- `output/registry/t139-alpha-reservations.jsonl` は append-only。既存 1 行を編集・削除・並べ替え・再作成しない。
- 絶対規律 1 — correctness 用は trace-enabled build、性能計測は trace-disabled build の別走。
- 絶対規律 3 — verifier は pass/fail でなく「どの trx 間のどの依存で G2 が出たか」を構造化して返す。
- **D264 の非 export は本 session では解かない。** gate が完成するのは受領証 validator まで揃った後であり、
  本 session の 2 名前 (`resolve_effective_preregistration` / `PreregBinding`) だけ先に export すると
  「gate 完成まで」の条件を満たさない。

## 段 1 で実測した事実 (一次資料で再確認済み。素案から更新)

- `_validate_t139_core_s7_stresscheck_v1` は `operations の要素数は 1 必須` / `対象語句出現は exact 1 件` を
  強制し、`_S7_NEW_TEXT_SHA256` = `92fd7175…01a4` を pin する。承認 v2 は **2 operation** (core 221 行 =
  `225268a9…8e89`、333 行 = `a7852ad9…9952`)。**validator 本体の書き換えが要る** — path 差し替えでは通らない。
- D282 の承認 v2 は path `output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md`、
  commit `d0e76451…78d9`、sha256 `deedd71b…4df2`。test の `DRAFT_ERRATUM_REF` は `0`×40 / `0`×64 の placeholder。
- `EXPECTED_TWO_ERRATA_COMPOSED_SHA256` と `EXPECTED_S7_OPERATION_LINE_SHA256` は**既に test に存在する**
  (第 1 波が置いた)。承認 payload の `e0b0caea…8e0c` と一致するか段 2 で照合させる。
- **DW-O09 pin 閉包 (実測):** 承認 blob path を pin する `*.py` は
  `orchestrator/tests/test_t139_preregistration_binding.py:54,59` の 2 箇所だけ (草案 path)。
  合成 digest の他出現はすべて insights の歴史記録で、live pin ではない。
- `orchestrator/preregistration/` は `__init__` (28) / `addendum_envelope` (186) / `blobref` (266) /
  `erratum` (509)。**manifest・resolver・writer・台帳 consumer・submit は 1 file も無い。**
- **`tools/spool_fold.py --dry-run` が `invalid`** — 第 1 波の fragment
  `docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-w1-1.md` の `base:` digest が現本文と不一致。
  **land 前に直す必要がある** (最終 session の land 直前に carry 解決後の digest で再計算する)。

## 承認済み裁定の前提を覆す新事実 (段 4 で再裁定)

- **N1. pilot 投入 (land 2 scope 7) は本 session どころか land 2 全体で着手不可の可能性が高い。**
  worklog 407 の次の一手が「**本走投入は段階 2 の再提出後まで依然不可**」と明記し、公表 core 段階 2 wave
  (`dev-wave-t139-pubcore-stage2`) は現在**段 6 走行中で未 land**。さらに handoff w3 が「公表 core 側の 3 文書は
  承認候補であり、発効はユーザーの凍結承認とその fold 後。land 2 は『公表 core wave が land した』だけを
  根拠に発効済みと扱ってはならない」と定める。→ **land 2 の scope 7 と §S7 #7 (`b03`) は外部依存で blocked。**
- **N2. §S7 #7 の読み先が main に存在しない。** C-2b により `b03` consumer の読み先は新 core v2 §8.2 と
  追補 P `p03` だが、いずれも公表 core 段階 2 の未 land branch にしかない。
  → **`b03` consumer は最終 session まで着手不能。**

## 成果物の形 (本 session)

`orchestrator/preregistration/` の新 module (manifest + resolver) と `erratum.py` の改訂、対応 test、
変異事前登録と matrix、worklog / decisions fragment、逐語凍結。**land しない。**

## 分割方針

編集ファイル所有を素集合にして段 5 を 2 並列にする。

- **A**: `orchestrator/preregistration/erratum.py` + `orchestrator/tests/test_t139_preregistration_binding.py`
- **B**: `orchestrator/preregistration/manifest.py` (新) + `resolver.py` (新) + 新 test file 群

A は B の前提 (合成 digest を resolver が呼ぶ) なので、B には A の公開 API 署名だけを brief で先渡しし、
A の完了を待たずに並列で書かせる。統合時に親が署名一致を確認する。

## 攻撃対象の provisional 裁定 (段 3 で攻撃させる)

- **(P1)** 上の A/B 分割で段 5 を 2 並列にでき、B が A の実装完了を待たなくても署名先渡しで足りる。
- **(P2)** §S7 #2 (`PATH` 差し替え) の対策は「`git` を絶対 path で解決し、解決結果の実体 digest を
  受領証へ記録する」で足りる。`PATH` を無害化する必要はない。
- **(P3)** §S7 #3 (symlink / TOCTOU) の対策は「開いた fd を保持したまま hash と parse を行う
  (`O_NOFOLLOW` + fd 再利用)」で足りる。path を 2 度開かない設計にすれば検査時と使用時の raw は同一。
- **(P4)** §S7 #1 (台帳 → manifest の第 1 矢印) は「resolver が `F_r` の `docs/decisions.md` から D282
  payload を parse し、manifest の三つ組集合・erratum 順序・合成 digest・保証境界と exact 一致を要求する」
  で閉じる。manifest 側に追加の署名機構は要らない。
- **(P5)** D264 の非 export を本 session で解かない判断 (上記不変条件) が S6 (a) と矛盾しない。
