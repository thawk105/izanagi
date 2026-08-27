# 段 4 裁定 — [T-2001] 凍結した B-4 分析契約を実行する経路

base main `343b8f5a5` / branch `worktree-dev-wave-t2001-b4-analysis-path`
入力: `s1-brief.md`、`s2-plan.md`、`s3-consult-sol.md` (blocker 6)、`s3-consult-luna.md` (blocker 5)

## 0. 親が独立に裏を取った事実 (実測。子の主張をそのまま採らない)

| # | 主張 | 判定 | 実測の根拠 |
|---|---|---|---|
| V1 | `analysis_invalid` の理由は 11 でなく 12 | **real** | doc 427-442 は箇条書き 11 項だが、1 項に `duplicate_block_id` / `unknown_block_id` が同居し意味も別 (id の重複 / 期待側に無い id) |
| V2 | doc に「入力は上の 3 つだけ」と「次の 4 つだけ」が併存 | **real** | doc 420 行 = 「上の 3 つだけ」、入力列挙は 4 項 |
| V3 | float 経路では tie 境界が壊れる | **real (親が再現)** | `on=1.1, off=1.0, ref=1.0, floor=0.1` で `as_integer_ratio()` 経路の超過 = `3/36028797018963968`。10 進 exact なら tie。`json.loads(..., parse_float=Fraction)` で exact 化できることも実測 |
| V4 | `Arm` が既存と衝突 | **real** | `orchestrator/campaign/p3_b4_closed_critic.py:70` に `Arm = Literal["on", "off"]` |
| V5 | `design_not_feasible` は既存 | **real。親 brief の実測 1 が誤り** | `orchestrator/preregistration/stress_check_simulation.py` に 5 箇所以上 |
| V6 | 焦点走に 4 node の漏れ | **real** | 4 node とも実在を確認 (`test_campaign_import_invariant.py:1078,1227`、`test_plain_runner_coverage.py:77`、`test_pytest_collection_config.py:423`) |
| V7 | main がプランの anchor を動かしたか | **不成立 (安全)** | main は base から 14 commit 先行だが、変更面は `codex_reasoning_ab` 系 + insights + docs のみ。一覧検査・campaign module は無変更 |

**親 brief の実測 1 を訂正する。** 「4 語とも Python/JSON に 0 件」は誤りで、正しくは
`scheduled_attempt_registry` / `analysis_manifest` / `analysis_invalid` の 3 語が 0 件、
`design_not_feasible` は T-139 の別実験に既存である。訂正は段 7 の記録に残す。

## 1. scope の裁定 — この wave の完了意味を先に固定する

両レンズが最重として挙げたのは同一の事実である (sol F10、luna F1/F5)。

> 新設 5 module には sanctioned caller・artifact writer・producer が無く、この wave を land しても
> certified 選択・レポート・台帳の値は 1 bit も変わらない。§6 前提条件 9 も充足しない。

**この事実を real と裁定する。同時に、これは本 wave を止める理由にしない。**

- 依頼が名指しした成果物は 4 つ (adapter / consumer / 2 台帳の生成器と再生成完全性検査 /
  割当無作為化 schedule と遵守検査) であり、producer・sanctioned CLI・report writer・
  certified selector は 1 つも含まれていない。
- 依頼は「この wave が実在させる範囲と、まだ埋めない欄を分けて記録してください」と明示した。
  **両レンズの結論はこの記録義務の中身そのものである。**
- producer の自然な所有者は稼働中の `t1840` (B-4 専用起動器) であり、
  依頼が「同じ file を編集する必要が出たら land を待て」と定めた対象と重なる。

したがって本 wave の完了意味を次に固定する。**この定義を超える主張を成果物へ書かない。**

- **実在させる:** 凍結文面 §5.1.1 の規則を実行する純関数・schema・台帳生成器・schedule 導出器と、
  それらの文面一致検査、および artifact bytes から verdict までの統合経路。
- **実在させない (後続 task):** 権威ある producer、sanctioned CLI、永続 writer、
  §7.1 全件 report generator、certified 選択への必須配線、§5 の欄記入。
- **したがって §6 前提条件 9 は本 wave では未充足のままである。** 充足したと書かない。

## 2. 所見の裁定

### 採用する must-fix (実装する)

| ID | 出所 | 内容 | 成果物影響 |
|---|---|---|---|
| A1 | sol F1 (V1) | 理由 enum は **12 member**。`duplicate_block_id` と `unknown_block_id` を別 member にする | 放置するとレポートの invalid 理由が文面と別集合になる |
| A2 | sol F3 (V3) | 契約数値は **10 進 lexical から exact 有理数**へ読む。`json.loads(..., parse_float=Fraction)` を使い、float を経由した `as_integer_ratio()` を禁じる | 放置すると境界 block の `X` が `1/2` から `1` へ変わり `A_hat`・`m`・p 値・verdict が変わる |
| A3 | sol F7 | adapter / loader の失敗を例外のまま外へ出さず、**12 理由 enum へ写して全域関数として返す** | 放置すると malformed raw が台帳とレポートから消える (file-drawer) |
| A4 | sol F4 | `theta` 区間は **exact 根の外向き有理数包囲**として型に持ち、そう名乗る。端点そのものと書かない | 放置するとレポートの区間端点が文面の値と違うのに一致と主張する |
| A5 | luna F2 | 統合経路は **raw artifact bytes を受け取り `source_artifact_sha256` を自分で再計算**する。呼び手の申告 hash を受理しない。`reflux_formal_consumer` の実在照合 idiom に倣う | 放置すると自己整合させた偽入力から成立 verdict を作れる |
| A6 | luna F6 | registry は **batch 一括受領 → 同着正規化 → seal** の API にする。単件 append だけにしない。全 permutation から同一 bytes を要求する検査を置く | 放置すると呼び手の到着順で先頭 201 件と manifest hash が変わる |
| A7 | luna F8 (V4/V5) | B-4 型に `B4` 接頭辞を付け、wire 値に schema version を必須化する (`Arm` / `design_not_feasible` の二義化を避ける。D75) | 放置すると report/automation が T-139 と B-4 を取り違える |
| A8 | luna F4 | 一致 consumer は literal だけでなく **§5.1.1 の exact section bytes hash** を持ち、かつ A/C/D の source closure を入力に取る。「先頭 n」→「末尾 n」型の意味変更を behavior mutation で拒否する | 放置すると literal が同じまま母集合の選び方だけ変えられる |
| A9 | luna F9 (V6) | 焦点走に 4 node を追加する | 診断上の欠落。初回焦点走と受入の検査集合が食い違う |
| A10 | sol F9 | 変異事前登録を**実効 gate へ再照準**する。2 層が同じ入力を拒否する箇所は両層同時変異を kill 期待つきで登録する (DW-M04) | 放置すると変異結果が gate を閉じた証拠にならない |
| A11 | luna「P1 後の path と sha256」 | **analysis source closure receipt** を生成する。5 module の repo 相対 path と sha256、§5.1.1 の section bytes hash、schema version、consumer 実行結果を canonical に列挙する | 無いと §5 の primary outcome 欄に書ける安定した path/hash が存在せず、後続 doc wave が着手できない |

### 採用する緩和 (完全には閉じないが、閂の向きを正す)

| ID | 出所 | 裁定 |
|---|---|---|
| B1 | sol F5 / luna F3 | registry の全件性は、**issuer 束縛の schedule receipt を必須引数**にし、receipt が無ければ導出も seal もしない fail-closed にする。呼び手が渡す list を authority にしない。**ただし「file-drawer を閉じた」とは書かない** — 権威 producer が不在である限り閉じない。module docstring と worklog にこの限界を明記する |
| B2 | sol F6 / luna F3 | `derive_assignment` は **seed receipt (issuer hash 付き) が無ければ動かない**。HMAC 導出は再現性を与えるが、一様性と事前性は receipt 発行者が担保するものであって本 module は証明しない、と明記する。`random`・時刻・環境変数は使わない |
| B3 | sol F2 (V2) | 純関数の中で照合できるのは 4 入力に観測側がある項 (block ごとの `reference_*`・`block_id`・block 数・違反件数) に限る。**それらは必ず関数の中で照合する** (文面の理由がそのまま当たる)。`manifest_sha256` / `registry_sha256` は観測側が 4 入力に無いため、**統合経路 (A5) が実 bytes から再計算して照合する**。どちらの検査も省かない |

### refuted / scope 外へ送る

| 出所 | 裁定 |
|---|---|
| sol F2 の「純関数は実装不能」 | **一部 refuted。** block ごとの束縛検査は 4 入力の中で実装できる。実装不能なのは台帳 2 hash だけで、B3 の二段構えで両方が走る。文面の矛盾自体は裁定パッケージへ |
| sol F10 / luna F1・F5 | **real だが scope 外。** §1 の完了意味の定義と記録義務へ転化する |
| luna F7 (依存を `A → B/C → D → consumer` にせよ) | **採用。** A8 が consumer に C/D の closure を要求するため、consumer は D の後に置く。単位分割を改訂する (下記 §3) |
| luna F10 (t1840 の将来 path は未証明) | **real。** 現時点の差分 0 件は確認済み。将来 path は証明できないので、**段 9 の land 直前に編集面を再走査する**ことを本裁定の義務にする |

## 3. プラン v2 — 単位と依存

luna F7 を容れ、consumer を最後に回す。file 所有は素集合のまま。

```
A contract            p3_b4_analysis_contract.py
├── B adapter         p3_b4_analysis_adapter.py       (A 後、C と並列)
├── C ledgers         p3_b4_analysis_ledgers.py       (A 後、B と並列)
└── D 統合 + closure  p3_b4_analysis_path.py          (B/C 後)
    └── E consumer    p3_b4_analysis_prereg_consumer.py (D 後。A/C/D の closure を検査)
```

各単位の所有 path (絶対 path は prompt で渡す):

- A: `orchestrator/campaign/p3_b4_analysis_contract.py`, `orchestrator/tests/test_p3_b4_analysis_contract.py`
- B: `orchestrator/campaign/p3_b4_analysis_adapter.py`, `orchestrator/tests/test_p3_b4_analysis_adapter.py`
- C: `orchestrator/campaign/p3_b4_analysis_ledgers.py`, `orchestrator/tests/test_p3_b4_analysis_ledgers.py`
- D: `orchestrator/campaign/p3_b4_analysis_path.py`, `orchestrator/tests/test_p3_b4_analysis_path.py`
- E: `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py`, `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`

段 2 の一覧検査の閉包 26 件 + luna の追加 4 node は、全単位の prompt へ逐語で渡す。
**`test_p3_build_authority_cli.py` の母集合は `git ls-files` なので、untracked のままの
初回走では新 file を含まない** (luna が実測)。親は統合 commit 後に必ず再走する。

## 4. 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」ことを実装後に確認し、
確認できなければ登録を取り下げて実効 gate へ再照準する (A10)。

| # | 位置 | 変異 | kill 期待 | 単一理由性の確認点 |
|---|---|---|---|---|
| M1 | contract の理由 enum | 12 member から 1 つ削る | KILLED | consumer が doc から 12 個抽出する。他層は enum を持たない |
| M2 | contract の tie 判定 | 境界を `<` にする (境界値を tie から外す) | KILLED | 境界 fixture は contract だけが評価する |
| M3 | adapter の数値読取 | `parse_float=Fraction` を外し float 経由にする | KILLED | V3 の実測値を fixture にする。adapter だけが読取を担う |
| M4 | contract の verdict 順序 | 汚染分岐を protocol violation より前へ動かす | KILLED | 両方が真の fixture は contract だけが分岐する |
| M5 | contract の入力検証 | 検証前に分岐評価を始める | KILLED | 不正型 fixture が分岐へ流れる |
| M6 | contract の順位規則 | `missing` を `rejected` と tie にする | KILLED | 順位は contract だけが持つ |
| M7 | contract の閾値 | `A_min` を成立条件に加える | KILLED | `m=6, W=6, ties=195` (`p_on=1/64 <= 1/40` かつ `A_hat=69/134 < 3/5`) |
| M8 | ledgers の選択関数 | 先頭 n を末尾 n にする | KILLED | E が behavior mutation で拒否する (A8) |
| M9 | ledgers の violation count | eligibility filter の後に数える | KILLED | filter で落ちる違反行を持つ fixture |
| M10 | ledgers の seal | batch 正規化を外す (到着順のまま) | KILLED | permutation 検査が唯一の層 |
| M11 | path の hash 再計算 | 呼び手申告 hash を受理する | KILLED | bytes と申告が食い違う fixture |
| M12 | path + ledgers 両層 | manifest の行比較と bytes 比較を**同時に**外す | KILLED (2 層同時、DW-M04 に従い事前登録) | 単独では帰属しないと sol F9 が指摘した箇所 |
| M13 | consumer の section hash | §5.1.1 の hash 照合を外す | KILLED | literal 抽出とは別層 |

**probe 先行。** 期待 node を確定できない変異は、初回を全件 SURVIVED 期待の probe として
登録し、観測 node を集めてから本登録する (DW-M07)。

## 5. 不変条件 (段 5・6 で破ったら停止)

- 規律 2 を緩める変更を採らない。既存テストの期待値を変更しない。
- `A_min` を判定の閾値にしない。`n` を予算へ切り下げない。`missing` を除外しない。
- `rejected` と `aborted` の間だけが常に tie。verdict は上から順・最初に当たった分岐で確定。
- 純関数は file system・時刻・環境変数・乱数・network・model・global state を参照しない。
- **`docs/phase3-b4-reflux-ablation-preregistration.md` を 1 byte も編集しない** (P1 維持)。
- **`p3_s4_loop.py`・3 driver・既存 launcher を 1 byte も編集しない** (t1840 との重複回避)。
- 到達不能な field を推定・既定値で補わない。fail-closed で拒否する。
- 「§6 前提条件 9 を充足した」「file-drawer を閉じた」と書かない。

## 6. 裁定パッケージ候補 (ユーザーへ返す。本 wave では実装しない)

1. **凍結文面の 3 点の不整合。** (a) 理由 enum は 11 名か 12 名か (本 wave は 12 で実装した)。
   (b) 420 行の「入力は上の 3 つだけ」は 4 つの誤記か。
   (c) `manifest_sha256` / `registry_sha256` の観測側を純関数の入力に加えるか、
   統合経路での照合を正式に許すか (本 wave は後者で実装した)。
2. **権威 producer の所有。** `execution_disposition`・実行 slot 順・`treatment_fired`・
   `contaminated`・`protocol_ok`・`precursor_hash`・reference resolver を、
   t1840 の launcher が持つか専用 wave を立てるか。
3. **schedule / registry / seed の issuer。** 誰がいつ発行し、どこへ durable に書くか。
4. **成果物へ効かせる後続層。** sanctioned CLI、永続 writer、§7.1 全件 report generator、
   certified 選択への必須配線。
5. **§5 の欄記入。** t1840 land 後に専用 doc wave を置き、A11 の closure receipt の
   path/sha256 を primary outcome 欄へ書く。それまで §6 前提条件 9 は未充足のまま。

## 7. 段 5 への指示

- 実装は Codex `role=author`、`reasoning=xhigh`、`sandbox=workspace-write` (D95)。
- 実装子は**コードとテストだけ**を編集する。docs 編集と commit をしない。
- A → B/C 並列 → D → E の順。先行単位の完了後に所有パス限定 patch を展開して次を投入する。
- 各 prompt に §5 の不変条件を**個別に列挙**する (契約文書への参照だけにしない)。
