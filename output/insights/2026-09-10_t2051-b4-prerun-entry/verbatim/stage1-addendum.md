# 段 1 brief 追補 — 親が brief 後に測った新事実 (段 4 で再裁定する)

出典はすべて親が本 job で実測した。**これらは P1 を弱める方向に働く。**

## A1. 「実走前に束縛を閉じる」作業には直近の先例があり、受理されている

[T-2101] が **2026-09-09 (本 wave の起点 main の直前) に着地**した。同 wave の一次資料
`/work/1/SFC/tanab/izanagi/output/insights/2026-09-09_t2101-proposal-binding/README.md` は
自ら次を書いている。

> **今日この gate が発火する formal 実行は無い。** 事前登録 §5 が `未記入` で、launcher が
> 要求する admission record 3 件も HEAD に存在しないため、formal B-4 は開始できない。
> 本 wave は「実走開始前に束縛を閉じる」作業である。

つまり本 repo は「今日発火しないが、実走開始前に実在する述語を閉じる」実装を受理している。
受理の条件として同 wave が示したのは、**述語が恒真でないことを変異で示すこと** (事前登録 10 変異が
全件 KILLED、期待 node 完全一致) と、**発火しない事実を正直に書くこと**である。

したがって親の P1 の「発火しないから実装しない」は、そのままでは強すぎる可能性がある。
区別すべきは次の 2 つである。

- **空の公開呼び手** (呼ばれる経路が無く、閉じる述語も無い) — 依頼が明示的に禁じたもの。
- **実走前に実在する述語を閉じる実装** (恒真でないことを変異で示せる) — 先例が受理したもの。

## A2. [T-2101] が名指しした、まだ開いている穴

同 README は「主張しない」節で、次を**開いたまま**だと明記している。本 wave の候補になりうる。

- **どの publication が権威かは強制されない。** publication root は呼び手が実行時に選び、
  issuer は別 root での再発行を防がない。任意の提案 B に対して `H(B)` を持つ registry を
  別 root へ発行すれば通る。
- **束縛の成功は耐久証拠に残らない。** 実行後に別の attempt へ付け替える経路は塞いでいない。
- **manifest membership を検査していない。** manifest の 201 行の外にある registry 行でも、
  hash が一致すれば実行できる。
- continuation の提案は内容束縛されない。

## A3. launcher が要求する admission record 3 件は HEAD に存在しない

`orchestrator/campaign/p3_b4_admission_record.py:96-102` が driver ごとに要求する
`docs/phase3-b4-reflux-ablation-admission-record-{base,sort,trigger}.json` は、
`ls` で 3 件とも不在。したがって launcher は publication の有無以前に起動できない。

## A4. 事前登録 §10 / §7.2 の記述は一部が陳腐化している

§7.2 と §10 (2026-09-08 の追記) は「正式 launcher への必須配線も無く」と書くが、
`p3_b4_launcher.py:673-685` は bootstrap で `--b4-prerun-publication` と `--b4-attempt-id` を
**必須**にしており、この配線は `cd47c4651` ([T-2101]、2026-09-09) で着地している。
**追記より後に着地したため、凍結文面の側が古い。** 本 wave は凍結文面を書き換えないが、
この差は記録する。

## A5. §6 の前提条件 9 件のうち、未充足が確定しているもの

- 前提 1 (§5 全欄記入 + commit): **未充足**。6 欄が `未記入`。
- 前提 6 (floor 再実測と参照): **未充足**。[T-2288] (2026-09-09) が発行不能を確定。
- 前提 8 (実行環境確定・単独性): **未充足**。§5 の `env_tag` が `未記入`。
- 前提 9 (§5.1.1 の分析契約を実行する経路の実在): **充足**。adapter・consumer・生成器・
  完全性検査はいずれも実在する。
- 前提 3 (閉じた critic invocation): 部分的に充足。閉じた範囲は §6 本文が自ら限定している。

## A6. 人間手番の一部は AI へ委任済み

D1638 (2026-09-05、ユーザー裁定) が 7 件の**実施主体を AI**とした。B-4 §5 floor の担当者指名・
凍結項目 12 行の空欄・測定の実施認可を含む。したがって「人間手番だから止まっている」という
説明は、少なくとも floor については正しくない。floor が止まっているのは**測定が無い**ためである
([T-2288] の実測: rr95 / rr5 の accepted calibration が 0 件)。

## A7. 正式 launcher の実測停止点

`p3_b4_launcher.py bootstrap --driver base --arm on` を実走した結果は rc=1 で、
停止点は `orchestrator.campaign.p3_b4_admission_record.B4AdmissionRecordError:
[admission-record] record is unavailable` である。publication の有無より先に admission record で止まる。

## A8. brief M13 の訂正 — 赤 precursor は 0 件でなく最大 3 件

brief の M13 は「production の赤 precursor は 0 件」と書いたが、これは**whiteboard に記録された
`rejected` が 0 件**という意味に限って正しい。親が追加で測ったところ、
`output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/` に `s4_rejections_digest.txt` があり、
`## [` 行の数え上げで**赤が 3 件**ある (WAL は 7 行)。ただし同 campaign には `loop_state.json` が
無いため whiteboard を持たず、適格性述語 (`p3_b4_analysis_ledgers.py:922-936`) が要求する
`whiteboard_result == REJECTED` を満たせない。

**したがって数は 0 件ではなく最大 3 件であり、いずれにせよ 201 件には遠い。** 結論は変わらないが、
「0 件」という数字をそのまま引かないこと。子はこの訂正後の数で判断せよ。

## この追補に対して答えてほしいこと

1. A1 の区別 (空の呼び手 / 実走前に述語を閉じる実装) は妥当か。妥当なら、本 wave で
   **恒真でない述語を閉じる実装**を 1 単位、file:line で名指しできるか。
2. A2 の 4 つの穴のうち、本 wave の scope (依頼 4 項目) に属し、かつ依頼が禁じた
   「仮想リスク向けの gate 追加」に当たらないものはあるか。あるならどれか。
3. A3〜A5 を踏まえて、停止地点の層の切り方をどう直すべきか。
