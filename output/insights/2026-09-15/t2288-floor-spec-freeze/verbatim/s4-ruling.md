# 段 4 裁定 — [T-2288] workload 別 3 spec の凍結可否

親裁定。基準 main `0600887d9` (段 4 直前に再確認、wave 中に進んでいない)。
入力 = 段 1 brief、段 2 plan (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`)・レンズ B (`s3-lensB.md`)、
および親の独立実測。

## 0. 裁定の要旨

**依頼への答え: 較正値に依存しない範囲で spec を凍結する余地は無い。実装面差分ゼロで返す。**
ただし**理由は較正だけではない。** 較正と独立の前提が全 3 workload を等しく塞いでいる。
したがって「rr5 の較正さえ取れれば 3 spec を凍結できる」は偽である。
段 5・6 を飛ばし `4→7→8→9` とする (DW-S04)。実装面差分ゼロなので変異 matrix を免除する。受入全走は免除しない。

## 1. (P1-a) 1 spec = 1 workload、rr5 は凍結できない — **real、維持**

`_bind_checkout_inputs` が単一の `provenance.calibration` を全 cell へ照合し、
`calibration.workload != dict(perf.workload)` で拒否する (`floor_pair_driver.py` の cell ループ)。
この行は同関数内の「env/clocks は冗長 gate」という自己申告の対象外であり、判定の要である。

accepted な rr5 (rratio=5) 較正は **repo 全域で 0 件**。レンズ B が registered directory の外まで
広げて数え、通常 JSON から抽出した較正 artifact 13 path・SHA 重複排除後 accepted rr50=5 / rr95=1 /
**rr5=0** を得た。rr5 の artifact 自体は 1 件あるが `quality.status="rejected"` (`selection-invalid`) で、
accepted への読み替えはできない。

較正を迂回する合法な経路も無い。`attestation_mode` の値域は `required` / `none` の 2 つだけで、
`none` は固定 SHA の grandfathered v1 bytes しか受理せず `calibration=None` を返し、
floor driver はそれを明示的に拒否する (「校正済み動作点だけを測るため」と逐語で書いてある)。

## 2. (P1-b) 「較正が揃っている rr50 / rr95 も凍結できない」 — **結論は維持、根拠を 4 点訂正**

結論は維持する。ただし親 brief の根拠は次のとおり誤っていた。段 2・段 3 の訂正を採用する。

1. **「0 件」の根拠が閉包になっていなかった。** brief は `git ls-files | grep -i floor.pair` という
   **file 名検索**を根拠にしたが、loader は spec の命名を要求しない。
   親が段 3 待機中にやり直した: tracked 全域の**内容検索**で top-level
   `schema == "floor-pair-spec/v3"` の JSON は 0 件、`admission_receipt` + `binary_sha256` を持つ
   portable binary record も 0 件。tracked `.gz` **1767 件を展開して**両 literal を走査し hit 0。
   `output/` 配下の未追跡込み grep でも実 instance は 0。レンズ B が独立に base64 断片まで広げて同じ結論を得た。
2. **「receipt が無いから binary も無い」は導けない。** `binary_relpath` は tracked を要求せず
   (`_resolve_regular` は lstat のみ)、untracked / ignored なバイナリの不存在は誰も証明していない。
   正しい言い方は「`binary_sha256` を書くには build 済みである必要があり、その build を名指しする
   採用根拠が無い」である。
3. **build receipt の「strict 検証」を広く書きすぎた。** floor driver は
   `validate_portable_binary_record(record, expected_policy=None)` で呼ぶため、
   **policy 一致比較・外部 ccbench pin・contract SHA の照合は発火しない。**
   無条件で効くのは receipt の canonical SHA 整合と、admission の
   `schema` / `class == HUMAN_REVIEWED` / `review_id == S8B_FLOOR` の拒否、subject の
   `binary_sha256` 一致と `trace is False` である。この射程で報告する。
4. **較正が揃っても PerfConfig は揃わない。** `perf_config` の `extime` / `reps` / `ycsb_max_ope` は
   較正 artifact に key 自体が無く、binder も照合しない。事前登録 §11.2 の「1 測定 = 5 反復 × 3 秒」は
   **名目値**で、同節が `PerfConfig` 未校正と明記しているので実値へ転用できない。
   採用根拠は D1696 が人手責任として残しているが、その根拠が現物として無い。

## 3. (P1-c) 実装面差分ゼロで返す — **維持。ただし 3 点を主張しない**

維持する。ただし次は**書かない**。いずれも段 3 が反証した。

- **「rr50 / rr95 は rr5 を待たねばならない」** — コードにも裁定にも 3 spec の同時凍結要求は無い。
  issuer は期待 spec 列を非空とするだけで件数を 3 に固定しない。
  **ただし先行結果を見てから残りの spec や期待列を選ぶのは §5 追補 (b) の事前閉包に反する。**
  先行凍結の余地は「必要入力が揃った workload がある場合」に限られ、今はどの workload も揃っていない。
- **「較正待ちの間に準備できる範囲が無い」** — build receipt の準備は較正を引数に取らないので分離できる。
  レンズ B は既存 campaign 由来の portable record を流用する経路が**構造的には開いている**ことも確かめた
  (floor 側は `expected_policy=None` で歴史的 record を検証し、floor cell ID への再束縛を要求しない)。
  流用できる実 record が 1 件も見つからなかっただけである。
- **「差分ゼロだから順序が機械保証される」** — 凍結を今しないことは、凍結前に測ってよいという意味では
  ない。loader の HEAD blob 一致と真祖先検査は「結果を見た時刻」を検証しない (issuer 自身が非保証として
  明記している)。事前登録 §11.1 手順 6・7 の順序と採用責任はそのまま残る。

## 4. real だが scope 外と裁定する所見

- **レンズ A 所見 3: 1 cell だけの spec は構文上通り、閉包検査は対象集合の意味的正しさを示さない。**
  real。ただし件数 gate やセル検査の新設は依頼が scope 外と明示しており、D1696 / D1974 が
  意味的一致を人手責任として残している。**実装しない。** 非保証として記録する。
- **レンズ B の「registered 外にも accepted 較正がある」** (通常 JSON で rr50=9 path / rr95=2 path)。
  real。pin 先を registered directory に限る機械的要求は loader に無い。
  **しかし本 wave では何も pin しないので影響しない。** どれを pin するかは採用裁定の対象であり、
  AI が既成事実として選ばない (§11.1)。記録だけ残す。
- **rr50 の accepted が複数ある (registered 内に 3 件、重複排除後 5 件)。** どれを pin するかの
  選択規則は未裁定。**本 wave では決めない。**

## 5. 実装しない (段 5・6 を飛ばす) と裁定する根拠

- 凍結できる spec が 1 件も無い以上、書くべき実装面 file が無い。
- placeholder・仮値・未取得 artifact への前方参照で欄を埋めることは、規律 2 と §11.1 が禁じている。
  `load_frozen_spec` が唯一の loader であり、末尾で `_bind_checkout_inputs` を呼ぶため、
  前方参照 pin の spec は commit しても読めない。「凍結」にならない。
- schema / validator の拡張 (D1696)、workload 一致要求の撤去 (D15) はいずれも既裁定が禁じている。
- 依頼が gate・検査・台帳・一般化の追加を scope 外と明示している。

## 6. 構造化して返す依存 (本 wave の成果物本体)

### A. 較正と独立に、全 3 spec を等しく塞いでいるもの

| # | 欠けているもの | 実測 | producer / 決定主体 |
|---|---|---|---|
| A-1 | 候補・参照の実バイナリ (`binary_relpath` / `binary_sha256`) | 採用対象を名指しする根拠が無い。tracked 要件は無いので「不存在」とは言わない | B-4 床値測定用の build。D1641 決定 3 の site = Pegasus 計算ノード gen_S |
| A-2 | `build_receipt` が指す portable binary record | tracked 実 instance **0 件** (内容 + gzip 1767 + base64 断片で確認) | `s8b_binary_admission.issue_binary_admission_receipt`。**較正を引数に取らない** |
| A-3 | `perf_config` の `extime` / `reps` / `ycsb_max_ope` の採用根拠 | 較正 artifact に key 自体が無い。§11.2 の 5 反復 × 3 秒は名目値 | calibrator 出力を AI が委任の下で承認 (D1641 決定 3) |
| A-4 | §5 の contention セル集合の具体列 | D1641 決定 3 は「3 workload × §5 に列挙する contention セル」と方針のみ。§5 から具体列が読めない | ユーザー (D1641 決定 3 で AI 委任) |
| A-5 | 窓 2 件の日時・campaign 識別子、seed、出力名 3 個、実行設定 | 本 wave 用の具体値は存在しない | 無裁定の AI 起草値を凍結へ入れない (§11.1) |

**A-2 は本 wave が新しく可視化した依存である。** 現行の worklog「次の一手」を辿った範囲では、
B-4 床値測定用の実バイナリと `s8b-binary-admission/v3` receipt の調達を名指しする項目が見つからない。
[T-2288] の持ち越し本文は残作業を「rr5 / rr95 の較正取得、workload 別 3 spec の凍結、床値の実測、
§5 floor 欄の記入」と書いており、**A 群が前段にあることを記していない。**

### B. rr5 固有の較正依存 (鎖の現在地)

1. rr5 の accepted 較正 = 0 件。artifact は 1 件あるが `rejected` (`selection-invalid`)。
2. 拒否の連鎖: 飽和点が無い → D15 の下限基準で N=1,000,000 → その点の LLC miss 率 **0.364%** が
   `DEFAULT_CACHE_FLOOR = 0.005` (0.50%) を下回る → `cache_floor_warning=true` → `selection-invalid`。
3. **解除は [T-2592] / D1986 項 1 (裁定済み・実装待ち)。** 較正のレコード数選択規則へ
   「品質検査の取りこぼし率下限も満たす最小の値を選ぶ」を足す。下限 0.50% は動かさない。
   実装面なので Codex `role=author` と変異事前登録が要る。
4. **依頼文が前提に置いた D1936 項 6 は既に着地している** (2026-09-13、commit `b3c62ee7f`)。
   同時投入した 2 条件のうち **rr95 は accepted (`995805.nqsv`)**、rr5 が上記で拒否された。
   よって「rr5 / rr95 の較正取得が D1936 項 6 で止まっている」は現在偽である。

### C. rr50 固有

accepted が複数ある (registered 内 3 件)。どれを pin するかの選択規則が未裁定。

## 7. この wave が保証しないこと

- loader・較正 verifier・issuer・pytest・build・測定を実行していない。受理／拒否の実測は 0 件。
  「accepted と書いてある」ことの確認と、現行 verifier が実際に受理することは別である。
- 実バイナリの不存在は証明していない。untracked / ignored / repo 外は探索閉包に含めない。
- 任意符号化 (Unicode escape、多重符号化、gzip 以外の archive) まで解いた完全な不存在証明ではない。
  レンズ B が未完了範囲を名指ししている。
- 「将来も凍結不能」ではない。A 群と B 群が揃えば凍結できる。
