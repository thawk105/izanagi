# [T-897] build gateway の trigger axis semantic admission — wave 記録

branch `worktree-dev-wave-t897-trigger-admission` / 2026-08-12 23:49 〜 2026-08-13 (JST)。
ユーザー裁定 (2026-08-12 第 6 束) の **(b)** を実装した。敵対検証を受入条件とする裁定である。

## 何を直したか

materialized trigger predicate の exact 検査は `trigger_gate_binding` を渡した評価でしか発火せず、
binding を省略する 5 経路 (s8a trigger sweep / S-1 direct comparison / S8b oracle / S8b floor /
S-1 extime calibration) は検査に到達しないまま build へ進んでいた。検査を build gateway
(`derive_build_admission` / `require_build_admission`) へ移し、trigger 軸が materialize された
source に対しては binding の有無に関わらず必ず発火させた。

受理言語は 2 つだけである。

1. marker block (BEGIN 行頭〜END 行末) が凍結 template と逐語一致する pristine 状態。
2. 同 block が凍結 template と hole 1 行だけ異なり、その hole が
   `PREDICATE_HOLE_INDENT + emit_predicate(TriggerGateIR(mask))` (mask 0..31) と exact 一致する状態。

## 裁定を決めた 2 つの実測

**(1) `GeneratorId` は増やせない。** `_new_policy()` の preimage は
`"generator_registry": sorted(member.value for member in GeneratorId)` を含む。policy_sha256 は
全 admission receipt body の field であり outer `receipt_sha256` を決めるため、**enum member を
1 つ足すだけで過去・現在の全 receipt の SHA が変わる**。段 3 レンズ A が第 1 位に推した
「characterization 専用の typed 状態を新 GeneratorId で分離する」案は、この 1 点で実装不能だった。

**(2) `izanagi_gate_pass = true;` は emitter 言語で表現できない。** emitter の 32 述語は
要因 8 種のうち 5 種と番兵しか覆わない (`reflux_ir._ENUM_MEMBERS` は 5 件、
`axis_trigger_gating.REASON_NAMES` は 8 件)。`insert-node` / `scan-node` に対して mask 31 は
「抑制しない」を返し `true` は「抑制する」を返すので、両者は意味が一致しない。
そして「この 2 種が実際には発火しない」ことこそ s8a characterization driver が測る対象なので、
mask 31 での代替は測りたい前提を答えに使う循環になる。
したがって pristine は 33 番目の候補ではなく**骨格の単位元**であり、受理言語に含めることは
候補空間の拡大ではない。

## gate の保証と、保証しないこと

**gate は block の bytes を検証し、block が生きた C++ かは検証しない。**

段 6 レビューが自前 C++ 字句解析の**両方向の誤り**を静的追跡で実証した — raw string と行継続で
(a) 偽 block を受理し、(b) 正当な source を過剰拒否する。過剰拒否は正当な build を止めるため
fail-open と同等以上に有害である。正確な C++ 字句解析 (翻訳フェーズ 1〜3・raw string・行継続・
trigraph) は本 wave の scope を超えるので、字句解析と file 全体の BOM / NUL / decode 検査を撤去した。
実装は 158 行から 80 行になった。

残存限界:

- **R1**: block 全体をコメントや raw string で無効化した source。
- **R2**: block **外**での `izanagi_gate_pass` 再代入。
- **R3**: derive/require から compiler read までの ABA 窓 (既存の明示的残存境界)。

## 実測

| 何 | 結果 |
|---|---|
| 焦点走 (実装差分単独) | `test_build_admission.py` **50 passed / rc=0** (request 908802.nqsv、2.40 秒) |
| 焦点走 (fix 前・波及 8 file) | 2 failed / 777 passed / 17 skipped |
| 焦点走 (fix 後・波及 9 file) | **826 passed / 17 skipped / rc=0** (28.78 秒) |
| 変異 1 巡目 | 9 KILLED / 1 MISMATCH / SURVIVED 0 (M11 の期待 node 過少申告) |
| 変異 2 巡目 | **10 KILLED / MISMATCH 0 / SURVIVED 0 / rc=0** (基準走 PASSED、347 passed / 9 skipped) |
| AI provenance | 全史 rc=0、新規違反なし |

fix 前の赤 2 件は `test_campaign.py` の fixture `_write_materialized_trigger_source` が
凍結 template ではなく手書きの最小 block (契約コメント 13 行が無く、BEGIN 行に先頭 2 空白が無く、
`#else` 枝が `true;`) を書いていたためだった。**期待値を 1 文字も変えず fixture の入力を
凍結 template 由来へ直して**解消した。正経路は元の断言のまま緑になり、交差マスク側も本来の層
(pipeline の mask 検査) へ到達して元の期待文言へ戻った。

## 変異の事前登録から落とした 3 件

段 4 で 11 件を登録したが、段 6 の 2 レンズが独立に「単独帰属が成立しない」と判定した。

- **M4 (1 物理行制約の削除)**: 独立した物理行数検査は実装に存在しない。空 hole も複数行 hole も
  block 逐語比較 1 本で拒否されるため、削除できる anchor が無い。
- **M6 (CR payload 保持処理の削除)**: 同上。CRLF / CR 単独は block frame 比較で拒否される。
- **M4-prime (BEGIN/END 順序検査の削除)**: 削除しても後段の frame 検査が同じ入力を拒否する。
  **順序検査は冗長 gate であり、単独変異の証拠から外す。**

## ユーザー裁定パッケージ

### RP-1. characterization と candidate を恒久的に分離するか

**問題:** 現在の gate は pristine block を受理するが、「characterization driver が意図して
pristine を使っている」のか「candidate の置換が黙って失敗して pristine のまま残った」のかを
gateway から区別できない。後者なら report は mask M を主張しつつ実バイナリは pristine になる。

**現状 live ではない**理由: `s8a_trigger_sweep.py` と `s1_direct_comparison.py` は
quarantine の `res.passed` を先に検査するため、置換失敗はそこで捕まる。

**選択肢:** (a) `GeneratorId` へ characterization 専用 member を足す (policy schema の版上げが必要 —
全 admission receipt の SHA が変わるため、凍結 pin 閉包の移行計画とセットになる) /
(b) pristine 受理を producer 側の受領証に束縛する別機構 / (c) 現状の残存限界として受容し、
quarantine の `res.passed` 検査を正本の防壁と明記する。

**親の推奨は (c)。** (a) は凍結 bytes の全面移行を要し、得られる保証は quarantine 検査が既に
与えているものと重複する。

### RP-2. block 外の C++ 意味論をどこまで検証するか

R1 (block 全体のコメント化・raw string 囮) と R2 (block 外の `izanagi_gate_pass` 再代入)。
**選択肢:** (a) 正確な C++ 字句解析器を別 wave で作る / (b) 凍結領域を post-END の
`if (izanagi_gate_pass)` まで拡大して R2 だけ閉じる / (c) 残存限界として受容する。
**親の推奨は (b)** — R2 は凍結領域の拡大だけで閉じ、C++ 字句解析を必要としない。

### RP-3. derive/require から compiler read までの ABA 窓 (R3)

既存の明示的残存境界であり本 wave は縮めただけである。閉じるには source の内容を
fd で anchor したまま build へ渡す設計が要る。**親の推奨は現状維持**。

### RP-4. S8b の content-addressed binary store が admission を束縛しない

段 3 レンズ B の scope 外 real 所見。portable binary schema は binary / hash / store path を持つが
admission receipt を持たず、resume は store の存在と SHA だけを確認する。
admission 未証明の既存 binary でも hash が一致すれば floor の測定値・manifest・oracle report に使われる。
**親の推奨は起票**。

### RP-5. gate 導入前に生成された既存 artifact の遡及再検証

`s8a_trigger_gating_coverage.json` / `s8a_trigger_freq_t48.json` / 既存 sweep report は
gate 導入前の生成物である。WAL replay は receipt の canonicality を検査するが live source semantic は見ない。
**親の推奨は「再取得の必要なし・生成 epoch を記録する」**。

## 逐語

`verbatim/` に段 2〜段 6 の子成果物を置く。`mutation/` に spec・1 巡目 erratum・最終結果を置く。
