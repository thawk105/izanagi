# 段 6 裁定 — [T-897]

裁定時刻: 2026-08-13 08:00 JST

## 0. 親の実測

- 焦点走 1: `test_build_admission.py` **50 passed / rc=0** (request 908802.nqsv)。
- 焦点走 2: 波及 8 file **2 failed / 777 passed / 17 skipped**。赤は
  `test_campaign.py::test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds`
  と `::test_trigger_binding_rejects_crossed_materialized_predicate_and_mask` の 2 件のみ。
- stock `transaction.cc` に骨格 token は **0 件** (stock build は無影響)。

## 1. レビュー A の裁定

| # | 判定 | 採否 |
|---|---|---|
| F1 raw string / 行継続で自前字句解析が fail-open | **real** | **採用 (字句解析ごと撤去)** |
| F2 同じ字句解析が正当な source を過剰拒否 | **real** | **採用 (同上)** |
| F3 変異帰属が M4/M6/NUL/comment/marker 順序で不成立 | **real** | **採用 (spec を実装形から再導出)** |
| 凍結定数は patch と byte 一致 (1,209 bytes、`2fa8ad5b…`) | real | 確認済み (最重要リスクが clean) |
| N01〜N14 は裁定どおり | real | 確認済み |

## 2. レビュー B の裁定

| # | 判定 | 採否 |
|---|---|---|
| 1 block 外の BOM まで拒否し裁定より狭い | **real** | **採用 (撤去)** |
| 2 既存 2 nodeid が確実に赤 | **real** | **採用 (fixture を直す)** |
| 3 M4/M6 等の変異帰属が不成立 | **real** | **採用 (A-F3 と同一)** |
| 4 `expected_source` の例外順序 | nit | 受容 (pin する nodeid なし) |
| 5 経路 + coverage/freq がすべて accept | real | **確認済み — 本 wave の最重要検証** |
| receipt bytes / import DAG は保全 | real | 確認済み |

## 3. 親の設計裁定 — **gate は「block の bytes」を検証し、「block が生きた C++ か」は検証しない**

自前 C++ 字句解析を**撤去する**。理由は 3 つ。

1. レビュー A が静的追跡で **両方向の誤り**を実証した。raw string / 行継続で
   (a) 偽 block を受理し (F1)、(b) 正当な source を拒否する (F2)。
   **過剰拒否は正当な build を止めるため、fail-open と同等以上に有害**である。
2. 正しい C++ 字句解析 (翻訳フェーズ 1〜3、raw string、行継続、trigraph) は本 wave の scope を超える。
   誤った字句解析を残すのは、謳うだけで発火しない保証 (あるいは逆に誤爆する保証) である。
3. 段 4 裁定 §3 は既に「block **外**の任意 C++ は scope 外 (RP-2)」と定めている。
   コメントによる block の無効化・raw string 内の囮 block は、いずれも block 外の C++ 意味論であり
   RP-2 に属する。

**同じ理由で file 全体の BOM / NUL / UTF-8 decode 検査も撤去する** (レビュー B 所見 1)。
block 内の非正準 bytes は block 逐語比較で必ず落ちる。block 外は scope 外である。

**規律 2 の判定:** 撤去後も、wave 前 (gate 不在) と比べれば受理集合は真に縮小している。
撤去するのは「正しくない検査」であって「正しい検査」ではない。

**残存限界 (worklog に明記):**
- R1: block 全体をコメント / raw string で無効化した source (レビュー A の N03 / F1 囮)。
- R2: block 外での `izanagi_gate_pass` 再代入 (段 3 レンズ A の N12)。
- R3: derive/require から compiler read までの ABA 窓。
いずれも RP-2 / RP-3 として裁定パッケージへ。

## 4. fix 指示 (1 単位、Codex `role=author`)

**所有 file (これ以外を編集してはならない):**
- `orchestrator/campaign/build_admission.py`
- `orchestrator/tests/test_build_admission.py`
- `orchestrator/tests/test_campaign.py` (**fixture の入力だけ**)

**F-1 字句解析と file 全体検査の撤去**
`_cpp_block_comment_ranges` / `_visible_directives` を削除。BEGIN/END は raw bytes に対する
directive regex の全 match をそのまま数える。file 全体の BOM / NUL / `decode("utf-8")` 検査も削除。
残す検査は「BEGIN 1 件・END 1 件・BEGIN が END より前」「block bytes ∈ {凍結} ∪
{凍結の hole を 32 emitter 出力で置換したもの}」「marker 0 件のとき骨格 token が残っていれば reject」
「ENOENT だけ no-op、他の `OSError` は reject」。

**F-2 `test_campaign.py` の fixture 修正**
`_write_materialized_trigger_source` (`:5361-5390`) を、手書き最小 block ではなく
`axis_trigger_gating.FROZEN_TEMPLATE_BLOCK_BYTES` から組み立てるよう直す。
**既存 test の断言・期待値・期待文言を 1 文字も変えてはならない。**
反転・緩和・skip・削除・xfail 化は禁止。fixture の入力を現実の materialization に揃えるだけである。
これで正経路は元の断言のまま緑になり、交差マスク側も本来の層 (pipeline の mask 検査) に到達して
元の期待文言に戻るはずである。**そうならなければ実装側が誤りであり、期待値を変えずに報告して止めよ。**

**F-3 テストの帰属修正**
撤去した検査 (comment visibility / BOM / NUL / decode) に対応する負例 node を削除する。
`N07-nul` は削除するか、NUL を **block 内の hole 行**へ置いて hole membership で落ちる形に直す。
BEGIN/END が**逆順**の負例を追加する (`begins[0].start() >= ends[0].start()` の単独帰属)。
`test_trigger_axis_semantic_validator_precedes_class_selection` は診断文だけの差なので
**kill の証拠に使えない**旨をコメントで明記するか、受理集合が変わる形へ直す。

**禁止 (規律 2):**
production の受理集合を広げる方向の変更、fail-open 化、警告化、env/CLI での無効化、
既存テストの期待値の反転・緩和・skip・削除。**テストが赤いときは実装側を直す。**
期待値が誤りだと判断したら、実装を変えずに報告して止めること。

## 5. 変異 spec の再導出 (DW-M01 / DW-M02 / DW-M07)

段 4 の事前登録 11 件のうち **M4 (1 物理行制約) と M6 (CR payload 保持) は実装形に対応する
anchor が存在しない**ことがレビュー A・B から独立に指摘された。両者は block 逐語比較 1 本に
吸収されている。**erratum として台帳に残し**、fix 後の最終 commit で実装形から完全集合を
再導出する (DW-M07)。M4/M6 は削除し、代わりに次を登録する。

- M4' BEGIN/END の順序検査 (`begins[0].start() >= ends[0].start()`) を削除。
- M6' 32 emitter tuple の生成範囲を `range(32)` → `range(1, 32)` にする (mask 0 の欠落)。

期待 node はレビュー B の帰属表を出発点とし、**fix 後に実測で完全集合を再導出する**。
