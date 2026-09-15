# 段 1 brief — [T-2288] workload 別 3 spec の凍結可否判定

wave `dev-wave-t2288-floor-spec-freeze` / branch `worktree-dev-wave-t2288-floor-spec-freeze` /
起点 local main `0600887d9`。Codex author = D95。

## 研究前進

B-4 事前登録 §5 の `floor` 欄が `未記入` である限り、材料レポートが到達できる分析 verdict は
`floor_domain_error` → protocol violation の 1 種類だけで、§7.1 の 4 分類は実効化しない。
床値を測るには「workload ごとに 1 つの凍結 spec」(D1936 項 7) が前段にある。
**この wave が進めるのはその凍結だけで、床値は測らない。完了判定は
「3 spec それぞれについて凍結可否を artifact 単位の実測で確定し、不可なら欠けている前提を
構造化して返した」こと。**

## scope

- **in:** workload 別 3 spec (`floor-pair-spec/v3`) を今の main で凍結できるかの判定と、その構造化。
- **out:** rr5 / rr95 の較正取得 (D1936 項 6 / [T-2515])、床値の実測、§5 floor 欄の記入、
  集約規則の追補 (着地済み)、集約発行・受理の配線 (着地済み)。
- **out (依頼が明示):** 仮想リスク向けの gate・検査・台帳・一般化の追加。

## 確定済みユーザー裁定 (この wave を拘束する)

- **D1936 項 7 / D1855 案 B:** 床値は workload ごとに 1 凍結 spec で測り、3 つの floor-pair summary を
  1 つの集約成果物へまとめる。別の集約基盤・台帳・manifest 形式を新設しない。
- **D1641 決定 3:** 凍結 12 項目の値 (site = Pegasus gen_S、セル集合 = 3 workload × §5 の contention セル、
  共通参照点と対照対 = byte 単位で同一の候補を独立 2 セッション、保守側最大の対象 = 凍結セル集合 × 2 時間窓の全部)。
  標本数は D1695 が n = 62 へ改めた。
- **D1641 決定 1・2:** 担当 3 者は `thawk105` 名義で操作は AI 委任。測定は認可済み。
- **D15:** calibration は (env, thread, 代表 workload) でキーする。単一 calibration で全 workload を
  賄う案は「虚偽」として却下済み。
- **D1696:** 測定前の follow-up wave で schema と validator を拡張する案は採らない。
- **§11.1 (案、D1641 決定 3 で 12 項目は確定):** 空欄を残したまま凍結 commit を作らない。
  AI が起草した候補値を無裁定の既定値として凍結へ入れない。

## 親の実測 (2026-09-15、main `0600887d9`)

| 前提 | 実測 | 出所 |
|---|---|---|
| accepted calibration (rr50) | 3 件 | `output/env/pegasus/calibration/registered/calibration-{449d0ad22f13e366,753f535a8d024727,94a4b79fa31bba3c}.json` |
| accepted calibration (rr95) | **1 件** | 同 `calibration-5c836a22eff9ab40.json` |
| accepted calibration (rr5) | **0 件** | 同 directory の全 4 file を親が開いて `workload.ycsb_rratio` を読んだ |
| tracked `s8b-binary-admission` receipt の実 instance | **0 件** | `git grep -l "s8b-binary-admission"` の hit はコード・テスト・docs・insight のみ |
| tracked `floor-pair-spec/v3` の実 instance | **0 件** | `git ls-files \| grep -i floor.pair` |
| §5 floor 欄 | `未記入` | `docs/phase3-b4-reflux-ablation-preregistration.md` §5 |

**2026-09-09 の T-2288 wave が「rr95 も 0 件」と書いたのは当時の事実で、現在は偽である** (絶対規律 7 —
当時の記録は無効化せず、現在地は自分で測り直した)。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1-a)** 1 つの凍結 spec は 1 workload しか持てない。`_bind_checkout_inputs` が単一の
  `provenance.calibration` を全 cell へ照合し、cell ごとに `calibration.workload` の一致を要求するため
  (`orchestrator/campaign/floor_pair_driver.py` の `_bind_checkout_inputs`)。よって rr5 の accepted
  calibration が 0 件である以上、**rr5 spec は凍結できず、3 spec は揃わない。**
- **(P1-b)** 較正が揃っている rr50 / rr95 も凍結できない。`artifacts[]` の exact key が
  `{artifact_id, binary_relpath, binary_sha256, build_receipt, trace}` で、`build_receipt` は
  tracked blob として `s8b_binary_admission.validate_portable_binary_record` を strict に通り、
  `admission.class == HUMAN_REVIEWED` かつ `review_id == S8B_FLOOR` を要求する。その実 instance が
  0 件で、`binary_relpath` が指す実バイナリも無い。**これは較正とは独立の前提である。**
- **(P1-c)** したがって「較正値に依存しない範囲で spec を凍結する」余地は無く、
  **本 wave は実装面差分ゼロで依存を構造化して返す。**

(P1-a)〜(P1-c) のいずれかが覆れば段 4 で裁定をやり直し、凍結できる範囲だけ実装する。

## 不変条件 (緩めない)

1. **規律 2:** 凍結 spec の必須 pin を placeholder・仮値・未取得 artifact への前方参照で埋めない。
   「凍結できない」を「弱い凍結で通す」へ言い換えない。
2. **D15 の workload 署名 gate を外さない。** 2026-09-09 の near miss (親が「欠陥」と判定し段 3 が反証) の再発を避ける。
3. **D1696 に従い、測定前に schema / validator を拡張しない。**
4. 記録された過去の測定を現行コードとの差だけで無効化しない (絶対規律 7)。
5. 依頼が scope 外と明示した gate・検査・台帳・一般化を足さない。

## 成果物の形

- `output/insights/2026-09-15/t2288-floor-spec-freeze/README.md` — 判定、実測表、欠けている前提の構造化、生証拠の所在。
- `verbatim/` に段 1〜4 の全文。
- spool fragment (worklog / decisions / failures) と worklog エントリ 1 本。
- **実装面差分は 0 を既定とする。** 覆った場合だけ段 5 を起こす。

## 並列分割方針

- 段 2: plan 1 本 (read-only、`reasoning=medium`)。「今の main で 3 spec を凍結するとしたら、
  何を file:line 単位で埋める必要があるか」を起草させ、埋められない欄を名指しさせる。
- 段 3: レンズ 2 本を並列。A = 正しさ境界・凍結境界 (placeholder 凍結や弱い pin への誘導を検出)、
  B = 閉包と反証 (「本当に凍結できないのか」を積極的に攻める。親の実測値と一般化も検査対象)。
- 段 5 は (P1-c) が維持されれば起こさない。
