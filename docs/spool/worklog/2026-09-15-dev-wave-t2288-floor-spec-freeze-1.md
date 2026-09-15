---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2288-floor-spec-freeze
seq: 1
title: [T-2288] workload 別 3 spec は凍結できず、塞いでいるのが較正だけでないことを確定した (docs のみ、branch worktree-dev-wave-t2288-floor-spec-freeze、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー依頼は「床値の集約規則のうち workload 別 3 spec の凍結だけを進める。集約規則の追補と
  集約発行・受理の配線は着地済み。rr5 / rr95 の較正取得と床値の実測はこの wave の scope 外とし、
  較正値に依存しない範囲で spec を凍結できるかを先に判定する。依存が切れないと分かったら実装せず、
  その依存を構造化して返す」。あわせて「codex は『前提鎖が残るので独立 wave に数えない』と保留したが、
  範囲を較正に依存しない spec 凍結へ絞り、依存が切れなければ差分ゼロで返す形にして採った」と伝えられた。
- **答えは「凍結できる spec は 1 件も無い」。実装面差分ゼロで返した。** ただし
  **理由は較正だけではない。較正と独立の前提が全 3 workload を等しく塞いでいる。**
  したがって「rr5 の較正さえ取れれば 3 spec を凍結できる」は偽である。一次資料は
  `output/insights/2026-09-15/t2288-floor-spec-freeze/README.md`。
- **依頼の前提を 1 つ訂正した。** 依頼は rr5 / rr95 の較正取得を D1936 項 6 に紐づけていたが、
  **項 6 は 2026-09-13 に着地しており、同時投入した 2 条件のうち rr95 は accepted である。**
  rr5 だけが `selection-invalid` で拒否され、その解除は [T-2592] / D1986 項 1 (裁定済み・実装待ち) にある。
- **本 wave が新しく可視化した依存 (A-2)。** 凍結 spec の `artifacts[].build_receipt` は
  `s8b-binary-admission/v3` を内包する portable binary record を tracked で要求する。
  その実 instance は repo に 1 件も無い。**この依存は較正と分離できる** — 発行器
  `issue_binary_admission_receipt` は較正を引数に取らない。にもかかわらず
  [T-2288] の持ち越し本文も現行の次の一手も、この調達を名指ししていなかった。
- **親 brief の根拠が 4 点誤っており、段 2 plan と段 3 の 2 レンズが独立に訂正した。** 結論は変わらない。
  (1) 「0 件」を `git ls-files | grep -i floor.pair` という **file 名検索**で断定していた。loader は
  spec の命名を要求しない。(2) 「receipt が無いから binary も無い」は導けない (binary は tracked 不要)。
  (3) build receipt の「strict 検証」を広く書きすぎた — floor driver は `expected_policy=None` で
  呼ぶので policy 一致比較・外部 ccbench pin・contract SHA の照合は**発火しない**。
  (4) 較正が揃っても `extime` / `reps` / `ycsb_max_ope` の採用根拠は別に要る。
- **親は段 3 待機中に閉包を取り直した。** tracked 全域の内容検索で top-level
  `schema == "floor-pair-spec/v3"` の JSON は 0 件、portable binary record も 0 件。
  tracked `.gz` 1767 件を展開して両 literal を走査し hit 0。`output/` の未追跡込み grep でも 0。
  段 3 レンズ B が独立に base64 断片まで広げて同じ結論に達し、あわせて
  **accepted 較正の全域内訳 (SHA 重複排除後 rr50=5 / rr95=1 / rr5=0)** を出した。
- **段 3 が反証し、報告に書かないと裁定した 3 点。** (a)「rr50 / rr95 は rr5 を待たねばならない」
  — 3 spec の同時凍結要求はコードにも裁定にも無い (ただし先行結果を見てから残りを選ぶのは
  §5 追補 (b) の事前閉包に反する)。(b)「較正待ちの間に準備できる範囲が無い」— A-2 は分離できる。
  (c)「差分ゼロだから順序が機械保証される」— loader は「結果を見た時刻」を検証しない。
- **real だが scope 外と裁定した所見 2 件。** 1 cell だけの spec は構文上通り閉包検査は対象集合の
  意味的正しさを示さない (D1696 / D1974 が人手責任として残している)。registered directory の外にも
  accepted 較正がある (本 wave は何も pin しないので影響しない)。いずれも依頼が gate・検査の追加を
  scope 外と明示しているため実装しない。
- **段 3 を省かなかったのが効いた。** 2026-09-09 の [T-2288] wave は親の中心判定が段 3 に反証されており、
  今回も親の根拠 4 点が段 2・段 3 で訂正された。結論は同じでも、誤った根拠のまま
  「較正さえ取れれば凍結できる」と書けば次 wave が空振りしていた。
- **実装面差分が 0 なので DW-S04 により変異 matrix を免除した。受入全走は免除していない。**
- 受入全走: 段 7 の記録 commit 後に投入する (本 fragment を書いた時点では未実施)。
- **段 8 の改善候補 1 件は見送った。** `tools/dev_wave_wait.py acceptance --help` は argv の `--` 区切りを
  parse 前に要求するため rc=2 で落ちる (親が実測)。DW-O27 へ 1 行足そうとしたが、同節は
  1052 bytes > 単節予算 1000 bytes になり `check_docs.py` が赤になった。既存本文はいずれも規範なので、
  予算を作るために削らずに撤回した (skill 契約「予算のために安全義務を削除・弱化してはならない」)。
  投入の定型そのものは `docs/pegasus-runbook.md` の「受入 lease の待ち手」に `--` 込みで載っている。
- 工数: codex 子 3 本 (plan 1 = medium 326.4 s / 12 call、consult 2 = medium 174.6 s / 9 call (lane=sol) と
  514.3 s / 22 call (lane=luna))。段 4 で「実装しない」と裁定したため段 5・6 の子は起動していない。
- 手順の実測 2 件。`git worktree add` が 13 分以上かかった (24983 file、他 3 session が同時に add していた)。
  `dev_wave_submodule_init.py` が 1 回目に `runtime-io-failure: update-no-fetch` で赤になり、
  DW-O08 に従い同じ引数で 1 度だけ再実行して成功した。

## 次の一手差分

### 更新

- [T-2288] **P1・前提 2 群が未充足**: 集約規則の追補と集約発行・受理の配線は着地済み。
  **workload 別 3 spec の凍結は、較正 (B 群) と較正に依存しない前提 (A 群) の両方で止まっている。**
  A 群 = 候補・参照の実バイナリ、`s8b-binary-admission/v3` を内包する portable binary record
  ({{T:b4-floor-binary-admission-supply}})、`extime`/`reps`/`ycsb_max_ope` の採用根拠、
  §5 contention セル集合の具体列、窓 2 件の日時・seed・出力名・実行設定。
  B 群 = rr5 の accepted 較正 ([T-2592] → [T-2515])。rr95 は取得済み、rr50 は複数あり選択規則が未裁定。
  A 群が済んでも床値の実測と §5 floor 欄の記入が残る。
  一次資料 `output/insights/2026-09-15/t2288-floor-spec-freeze/README.md`。
  base: 5d2b428d89acb5f503f185aa6f34751a9d982320e5ff78120c9a4f0588673207

### 新規

- {{T:b4-floor-binary-admission-supply}} **P1・新規**: B-4 床値測定用の候補・参照バイナリを build し、
  `s8b-binary-admission/v3` を内包する portable binary record を repo へ入れる。
  凍結 spec の `artifacts[].build_receipt` が tracked blob として要求するもので、実 instance は 0 件。
  **較正の取得とは独立に進められる** (発行器は較正を引数に取らない)。既存 campaign 由来の record を
  流用する経路も構造的には開いている (floor 側は `expected_policy=None` で歴史的 record を検証する)。
  実装面なので Codex `role=author` と変異事前登録が要る。
