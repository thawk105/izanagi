# [T-2288] B-4 床値 — workload 別 3 spec は凍結できない。塞いでいるのは較正だけではない

`authority: none`
`default_effect: no-state-change`

2026-09-15。wave `dev-wave-t2288-floor-spec-freeze`、branch `worktree-dev-wave-t2288-floor-spec-freeze`。
起点 local main `0600887d92538b3f34d894f9674d202d0a29a578`。
**実装面 (D95 決定 2) の差分は 0。** 本 wave の成果物は台帳 fragment と本スナップショットだけである。
可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と答え

依頼は「床値の集約規則のうち workload 別 3 spec の凍結だけを進める。rr5 / rr95 の較正取得と床値の実測は
scope 外とし、**較正値に依存しない範囲で spec を凍結できるかを先に判定する。依存が切れないと分かったら
実装せず、その依存を構造化して返す**」だった。

**答え: 凍結できる spec は 1 件も無い。実装面差分ゼロで返す。**
**ただし理由は較正だけではない。較正と独立の前提が全 3 workload を等しく塞いでいる。**
したがって **「rr5 の較正さえ取れれば 3 spec を凍結できる」は偽である。**

## 凍結とは何か (現物で確認した定義)

`floor-pair-spec/v3` の JSON を repo へ commit し、`floor_pair_driver.load_frozen_spec` が strict に
受理できる状態にすることである。生成器は無い — 人手で JSON を書き、driver の `--validate-only` を
通して commit する。

`load_frozen_spec` は末尾で `_bind_checkout_inputs` を呼ぶ。**唯一の loader がここで外部 artifact を
束縛するので、未取得 artifact への前方参照 pin を書いた spec は commit しても読めない。「凍結」にならない。**

凍結の機構そのものは既に通る。2026-09-08 の [T-2412] / D1774 が hash 不動点を解消し、
`provenance.source_commit` は spec を含む commit の親で loaded HEAD の真の祖先であればよい。
**今の障害は凍結機構ではなく、spec が pin すべき artifact の不在である。**

## 塞いでいるもの — A 群 (較正と独立、全 3 workload 共通)

| # | 欠けているもの | 実測 | producer / 決定主体 |
|---|---|---|---|
| A-1 | 候補・参照の実バイナリ (`binary_relpath` / `binary_sha256`) | 採用対象を名指しする根拠が無い。**tracked 要件は無い** (`_resolve_regular` は lstat のみ) ので「不存在」とは言わない | B-4 床値測定用の build。site = Pegasus 計算ノード gen_S (D1641 決定 3) |
| A-2 | `build_receipt` が指す portable binary record | tracked な実 instance **0 件** | `s8b_binary_admission.issue_binary_admission_receipt`。**較正を引数に取らない** |
| A-3 | `perf_config` の `extime` / `reps` / `ycsb_max_ope` の採用根拠 | 較正 artifact に key 自体が無く、binder も照合しない | calibrator 出力を AI が委任の下で承認 (D1641 決定 3)。照合責任は D1696 が人手に残す |
| A-4 | §5 の contention セル集合の具体列 | D1641 決定 3 は「3 workload × §5 に列挙する contention セル」と方針のみ。§5 から具体列が読めない | ユーザー (D1641 で AI 委任) |
| A-5 | 窓 2 件の日時・campaign 識別子、seed、出力名 3 個、実行設定 | 本 wave 用の具体値は存在しない | 無裁定の AI 起草値を凍結へ入れない (§11.1) |

**A-2 は本 wave が新しく可視化した依存である。** [T-2288] の持ち越し本文は残作業を
「rr5 / rr95 の較正取得、workload 別 3 spec の凍結、床値の実測、§5 floor 欄の記入」と書いており、
**A 群が前段にあることを記していない。** 現行の worklog「次の一手」を辿った範囲では、
B-4 床値測定用の実バイナリと `s8b-binary-admission/v3` receipt の調達を名指しする項目が見つからない。

`build_receipt` が受ける record のトップキーは 12 個で、receipt 本体だけを保存しても通らない。

```text
cell_id, holdout_id, configuration_id, binary, binary_sha256,
bin_hash_short, binding, configure_argv, build_argv, cached, store_path, admission_receipt
```

**この record の準備は較正の取得と分離できる。** `issue_binary_admission_receipt` は較正を引数に
取らない。さらに既存 campaign 由来の portable record を流用する経路も構造的には開いている —
floor 側は `expected_policy=None` で歴史的 record を検証し、floor cell ID への再束縛を要求しない
(段 3 レンズ B)。**流用できる実 record が 1 件も見つからなかっただけである。**

## 塞いでいるもの — B 群 (rr5 固有の較正依存)

1. accepted な rr5 (rratio=5) 較正は **repo 全域で 0 件**。artifact 自体は 1 件あるが
   `quality.status="rejected"` (`selection-invalid`) で、accepted への読み替えはできない。
2. 拒否の連鎖 (`output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md` の実測):
   飽和点が無い → D15 の下限基準で N=1,000,000 → その点の LLC miss 率 **0.364%** が
   `orchestrator/calibrator/analyze.py` の `DEFAULT_CACHE_FLOOR = 0.005` (0.50%) を下回る →
   `cache_floor_warning=true` → `selection-invalid`。
3. **解除は [T-2592] / D1986 項 1 (裁定済み・実装待ち)。** 較正のレコード数選択規則へ
   「品質検査の取りこぼし率下限も満たす最小の値を選ぶ」を足す。下限 0.50% は動かさない。
   実装面なので Codex `role=author` と変異事前登録が要る。
4. **依頼が前提に置いた D1936 項 6 は既に着地している** (2026-09-13、実装 commit `b3c62ee7f`)。
   同時投入した 2 条件のうち **rr95 は accepted (`995805.nqsv`)**、rr5 が上記で拒否された。
   よって「rr5 / rr95 の較正取得が D1936 項 6 で止まっている」は現在偽である。

較正を迂回する合法な経路は無い。`attestation_mode` の値域は `required` / `none` の 2 つだけで、
`none` は固定 SHA の grandfathered v1 bytes しか受理せず `calibration=None` を返し、
floor driver はそれを「校正済み動作点だけを測るため」と逐語で書いて明示的に拒否する。

## 塞いでいるもの — C 群 (rr50 固有)

accepted が複数ある (registered 内に 3 件、repo 全域で SHA 重複排除後 5 件)。
どれを pin するかの選択規則は未裁定。**本 wave では決めない。**

## 1 spec は 1 workload しか持てない (先行 wave の確定事項の再確認)

`_bind_checkout_inputs` が単一の `provenance.calibration` を全 cell へ照合し、
`calibration.workload != dict(perf.workload)` で拒否する。この行は同関数内の
「env/clocks は冗長 gate」という自己申告の**対象外**であり、判定の要である。
2026-09-09 の [T-2288] wave はこの要求を「欠陥」と判定して段 3 に反証されている (D15)。
**本 wave もこの gate を外す案は採らない。**

## 親の判定のうち、段 2・段 3 が訂正したもの

結論 (凍結不可・差分ゼロ) は維持されたが、**親 brief の根拠は 4 点誤っていた。**

1. **「0 件」の根拠が閉包になっていなかった。** brief は `git ls-files | grep -i floor.pair` という
   **file 名検索**を根拠にしたが、loader は spec の命名を要求しない。段 2 plan と段 3 レンズ A が
   独立に指摘した。親が段 3 待機中にやり直した結果は下の「閉包」節に置く。
2. **「receipt が無いから binary も無い」は導けない。** `binary_relpath` は tracked を要求しない。
   正しい言い方は「`binary_sha256` を書くには build 済みである必要があり、その build を名指しする
   採用根拠が無い」である。
3. **build receipt の「strict 検証」を広く書きすぎた。** floor driver は
   `validate_portable_binary_record(record, expected_policy=None)` で呼ぶため、
   **policy 一致比較・外部 ccbench pin・contract SHA の照合は発火しない。**
   無条件で効くのは receipt の canonical SHA 整合と、admission の
   `schema` / `class == HUMAN_REVIEWED` / `review_id == S8B_FLOOR` の拒否、subject の
   `binary_sha256` 一致と `trace is False` である。
4. **較正が揃っても PerfConfig は揃わない** (A-3)。brief は rr50 / rr95 を「較正が揃っている」と
   書いたが、`extime` / `reps` / `ycsb_max_ope` の採用根拠は別に要る。

## 主張しないこと (段 3 が反証した 3 点)

- **「rr50 / rr95 は rr5 を待たねばならない」** — コードにも裁定にも 3 spec の同時凍結要求は無い。
  issuer は期待 spec 列を非空とするだけで件数を 3 に固定しない。
  **ただし先行結果を見てから残りの spec や期待列を選ぶのは §5 追補 (b) の事前閉包に反する。**
  先行凍結の余地は「必要入力が揃った workload がある場合」に限られ、今はどの workload も揃っていない。
- **「較正待ちの間に準備できる範囲が無い」** — A-2 の準備は較正と分離できる。
- **「差分ゼロだから順序が機械保証される」** — 凍結を今しないことは、凍結前に測ってよいという意味では
  ない。loader の HEAD blob 一致と真祖先検査は「結果を見た時刻」を検証しない (issuer 自身が非保証として
  明記している)。事前登録 §11.1 手順 6・7 の順序と採用責任はそのまま残る。

## 閉包 (親の実測、段 3 レンズ B が独立に再現)

| 対象 | 走査方法 | 結果 |
|---|---|---|
| top-level `schema == "floor-pair-spec/v3"` の JSON | tracked 全域の**内容**検索 (`git grep`) + JSON parse | **0 件** |
| `admission_receipt` + `binary_sha256` を持つ portable binary record | 同上 | **0 件** |
| 両 literal の圧縮内埋め込み | tracked `.gz` **1767 件を展開して**走査 | hit 0 |
| `output/` 配下の未追跡込み | `grep -rl --binary-files=text` | 実 instance 0 (hit はすべて insight の散文と変異台帳) |
| base64 断片 (3 通りのバイト境界) | レンズ B が通常内容と gzip 展開後の両方で走査 | 0 件 |
| accepted 較正の全域内訳 | レンズ B が通常 JSON 13 path を抽出、SHA 重複排除 | rr50=5 / rr95=1 / **rr5=0** |

## real だが scope 外と裁定した所見

- **1 cell だけの spec は構文上通り、閉包検査は対象集合の意味的正しさを示さない** (段 3 レンズ A)。
  件数 gate やセル検査の新設は依頼が scope 外と明示しており、D1696 / D1974 が意味的一致を
  人手責任として残している。**実装しない。**
- **registered directory の外にも accepted 較正がある。** pin 先を registered に限る機械的要求は
  loader に無い。**本 wave では何も pin しないので影響しない。** どれを pin するかは採用裁定の対象で、
  AI が既成事実として選ばない (§11.1)。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。訂正された根拠を含む原文 |
| `verbatim/s2-plan-prompt.md` / `s2-plan.md` | 段 2 plan の投げ文と成果物 (codex, read-only) |
| `verbatim/s3-lensA-prompt.md` / `s3-lensA.md` | 段 3 レンズ A — 正しさ境界・凍結境界 |
| `verbatim/s3-lensB-prompt.md` / `s3-lensB.md` | 段 3 レンズ B — 閉包と反証 |
| `verbatim/s4-ruling.md` | 段 4 裁定 (親) |

## 本 wave が保証しないこと

- **loader・較正 verifier・issuer・build・測定を実行していない。受理／拒否の実測は 0 件。**
  「accepted と書いてある」ことの確認と、現行 verifier が実際に受理することは別である。
- **実バイナリの不存在は証明していない。** untracked / ignored / repo 外は探索閉包に含めない。
- 任意符号化 (Unicode escape、多重符号化、gzip 以外の archive) まで解いた完全な不存在証明ではない。
  レンズ B が未完了範囲を `verbatim/s3-lensB.md` の「数え落としの残余」で名指ししている。
- **「将来も凍結不能」ではない。** A 群と B 群が揃えば凍結できる。
- **実装面差分が 0 なので DW-S04 により変異 matrix を免除した。受入全走は免除していない** (結果は worklog)。
