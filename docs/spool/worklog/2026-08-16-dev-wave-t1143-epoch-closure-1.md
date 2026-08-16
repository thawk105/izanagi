---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1143-epoch-closure
seq: 1
title: campaign_verifier_epoch の束縛対象へ verifier 実装 4 file を加え exact 12 path にした — 閉じたのは lock 後の drift だけで、再 export shim は開いたままと明記する (コード + テスト + docs、branch worktree-dev-wave-t1143-epoch-closure、変異 matrix = 7/7 KILLED・path 単位の判別まで成立)
---

## 本文

**塞いだもの・塞がなかったものを先に書く。** 本 wave が閉じるのは
**「E1 lock を記録した後に verifier の実装 bytes だけを書き換えても epoch が変わらない」**
経路だけである。次はいずれも**閉じていない**。「規律 2 の穴を塞いだ」と読める記述をしてはならない
(段 3 レンズ A と段 6 焦点再レビューの明示要求)。

- `orchestrator/verifier/__init__.py` の再 export。`pipeline.py` は
  `from ..verifier import verify_trace_dir` で実体を解決するので、この shim 1 行を
  別実装へ向ければ束縛した 4 file の bytes を 1 byte も変えずに gate を無効化できる。
- `report.py` / `cli.py` / `__main__.py` と wrapper `orchestrator/verify.py`。
- 弱化して **commit してから**作る fresh lock。新しい `E1` として受理される。
- `__pycache__`・monkeypatch・`sys.modules`・`PYTHONPATH`、未束縛 bootstrap、pipeline の推移依存。

- **裁定の前提はコードと実データで確認できた。** 実 corpus の `output/**/campaign.lock` は
  32 本すべて v1 で、`contract_loader_blob_sha256s` を持つ v2 は 0 本 (実測)。
  凍結成果物に文字列 `exact 8 path` も epoch 診断も 0 件。`campaign_lock.py` の bytes を
  pin する live な台帳・manifest も 0 件だった。**この 0 件は path 検索だけでは確定しない** —
  段 3 レンズ A の指摘を受け、`FROZEN_MANIFEST` の 23 key (全て `output/**` でソース path は 0)、
  レポートの `generator.sha256` (各 report module 自身の `__file__` hash)、`source_digest` の
  対象集合 (CCBench の C++ path)、`REQUIRED_CODE_IDENTITY_PATHS`、
  `silo_ladder_rung1` の runtime binding という key 側・role 側でも数え直して確定した。
- **段 2 プランと段 3・段 6 の全レビューが `__init__.py` の追加 (exact 13) を推したが、親は
  exact 12 で land すると裁定した。** 批准された裁定文が名指ししたのは 4 file であり、
  12 / 13 / 14 / 16 の選択は脅威モデルの選択そのものだからである。実装せず
  {{T:epoch-closure-verifier-dispatch-face}} としてユーザー裁定へ返す。
  **費用の時計を添える** — 裁定 #11 が根拠にした「v2 lock が 0 件」は現時点でも成立しており
  (実測 32 本全て v1)、campaign を回して v2 lock が積まれると以後の拡張は既存成果物を壊す。
- **段 3 の敵対 2 本はいずれも NO-GO**、段 6 は review A が NO-GO・review B が所見ゼロの GO、
  焦点再レビューが NO-GO だった。**段 3 の 2 レンズは独立に同じ blocker (再 export shim) へ
  収束した。**
- **段 6 の fix は 2 巡走った。どちらも変異の証拠能力を守るための test 側修正で、production は
  1 byte も変えていない。**
  - 第 1 巡 (review A の所見): `_committed_closure_repo()` と `_expected_fixture_epoch()` が
    fixture を production の閉包定数から作っていたため、閉包から path を外す変異を入れると
    その file が作られず `FileNotFoundError` で落ちた。**certified gate に到達する前の赤を
    KILLED と記録してしまう**ので、test 専用の独立 literal 12 path tuple へ切り替えた。
  - 第 2 巡 (焦点再レビューの所見): 第 1 巡の結果、期待 epoch (12 path 由来) と記録 epoch
    (変異後 11 path 由来) がずれ、**drift 対象と無関係な 3 node まで落ちる**ようになった。
    親が probe を実走してこれを実測で確認し (4 変異とも drift test の 4 node 全部が赤)、
    drift 前に同じ campaign を `HISTORICAL_RAW` で読んだ記録 epoch を期待値に使う形へ替えた。
    `HISTORICAL_RAW` は current closure を参照しないので閉包定数の変異に対して不変である。
- **変異 matrix は 2 走した。** 走 1 (probe) は baseline PASSED、**SURVIVED 0 / TIMEOUT 0 /
  PARSE_ERROR 0**、KILLED 2 / MISMATCH 5。MISMATCH はすべて期待 node の不足であって
  検出力の欠如ではない (`DW-M08` の probe + erratum 経路)。この走で M1〜M4 の判別不成立を
  実測し、fix 第 2 巡へつないだ。
  走 2 (権威走、固定 commit `ae19c506`) は baseline PASSED、
  **KILLED 7 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**。
  **7 変異すべてで登録した期待 node が 1 件も欠けず過不足なく落ちた。**
- **path 単位の判別まで実証できた。** 閉包から `core.py` を外すと、落ちる drift node は
  `[core.py]` ただ 1 本で `[dsg.py]` `[model.py]` `[parse.py]` は緑のまま。4 変異とも同じ形で、
  「その path の drift 検出だけが失われる」という純増検出力の直接証拠になっている。
- **M5 / M6 は `DW-M08` の diagnostic sensitivity pin として別枠に記録する。**
  scope 文字列を旧文言へ戻す変異で、受理集合も fail-closed 挙動も変えない。
  KILLED と数えているが「受理集合を守った kill」ではなく「構造化診断の pin」である。
  M7 (記録 map と現在 map の比較を常に不一致にする) は過剰拒否の正例で、clean な E1 正例
  2 node が落ちた。
- **`docs/failures.md` の「8 path」記述は書き換えなかった。** 当該記述は 2026-08-11 の事故の
  記録であり「その時点で 8 path だった」は事実だからである。歴史記録は遡及改変しない。
  現行契約は {{D:epoch-closure-verifier-twelve}} が持つ。
- **背景待ちの完了通知が producer 生存中に届く事象を 1 wave で 3 回踏んだ。**
  いずれも `.done` も成果物も無く producer は生存していた。
  `DW-O01` の「完了は `.done` と exit code だけで判定し通知を判定にしない」に従い、
  成果物実在 + `.done` + producer 死の 3 点照合で毎回弾いて待ちを張り直した。実害ゼロ。
  **既存規律で防げているので dev-wave docs は変更しない。**
- **焦点テストの 1 走目が login node の bounded local で `rc=16` になり、テストが 0 件走った。**
  cgroup の `memory.max` / `memory.oom.group` を走行中に attest できないという理由である。
  `tools/run_tests.py --force-dispatch` で計算ノードへ回して 347 passed を得た。
  段 5 実装子と段 6 fix 子も同じ理由で pytest を 1 件も実走できておらず、
  **実測はすべて親が行った。子は「実装済み・未実走」と正しく申告しており偽の緑は無い。**
- **段 8 の裁定は候補ゼロ (docs 変更なし)。** 上の 2 件はどちらも既存 failures 台帳に
  同型が記録済みだった。偽完了は同一 wave 内 5 回の再発と「1 度弾いたから以後は正しいとは
  扱えない」まで記載済みで、本 wave の 3 回は頻度でも下回る。bounded local の `rc=16` は
  「単独再走の 1 回目」という親の焦点走の文脈込みで記載済みである。新情報が無いので追記しない。

### 工数

codex 子 9 本、合計 4,467.9 秒 / 239 model call / CLI reported 1,510,970 token
(receipt.json の実測。全 9 本 accepted)。

| 段 | 子 | model / effort | wall s | calls | outcome |
|---|---|---|---|---|---|
| 2 | plan | gpt-5.6-sol / max | 788.3 | 36 | accepted |
| 3 | consult sol | gpt-5.6-sol / max | 828.5 | 51 | accepted (NO-GO) |
| 3 | consult luna | gpt-5.6-luna / max | 1068.9 | 50 | accepted (NO-GO) |
| 5 | author | gpt-5.6-sol / high | 439.5 | 19 | accepted、pytest 実走 0 |
| 6 | review A | gpt-5.6-sol / high | 333.1 | 25 | accepted (NO-GO) |
| 6 | review B | gpt-5.6-sol / high | 198.8 | 11 | accepted (GO、所見ゼロ) |
| 6 | fix 1 | gpt-5.6-sol / high | 203.2 | 14 | accepted、pytest 実走 0 |
| 6 | focus | gpt-5.6-sol / high | 355.8 | 17 | accepted (NO-GO) |
| 6 | fix 2 | gpt-5.6-sol / high | 251.8 | 16 | accepted、pytest 実走 0 |

## 次の一手差分

### 完了

- [T-1143] enforcement source closure を exact 12 path へ広げ、verifier 実装
  `core/dsg/model/parse` を `campaign_verifier_epoch` へ束縛した。lock 記録後に verifier の
  bytes だけを書き換えて同じ epoch のまま certified 集合へ入る経路を閉じた。
  残余 (再 export shim・cross-version namespace・別閉包) は新規 3 項へ分離した。
  remaining: none
  base: 5f3286923e5425c242d541314cd5f4b40966b0402236d381b1a4f14fb6ca8d30

### 新規

- {{T:epoch-closure-verifier-dispatch-face}} **P1・ユーザー裁定待ち**: verifier package の
  どこまでを enforcement source closure に入れるか。(a) exact 12 のまま (現状。
  `__init__.py` の 1 行差し替えで gate を無効化できる経路が残る) / (b) exact 13 =
  `__init__.py` を追加し `pipeline.py` が実際に解決する dispatch 面を閉じる /
  (c) exact 14 = さらに `report.py` (import 時の判定差し替えと rejection payload) /
  (d) exact 16 = さらに `cli.py` / `__main__.py` (wrapper `orchestrator/verify.py` も要る)。
  段 2 プランと段 3・段 6 の全レビューが最低でも (b) を推している。
  **費用の時計**: 実 corpus の v2 lock は現時点で 0 本なので、いま広げれば既存成果物は
  1 件も壊れない。campaign を回して v2 lock が積まれると以後の拡張は成果物を壊す。
- {{T:epoch-cross-version-namespace}} **P2・ユーザー裁定待ち**: 旧定義の `E1` を新閉包の
  certified 選択から排除する機構が無い。oracle の artifact validator は scope を非空文字列
  としか検査せず、judge は `state=E1` と `certified_eligible=true` だけで採用する。
  択一は (a) hash domain を `/v2` へ上げる / (b) oracle 側で現行 scope の exact 一致を要求する /
  (c) 現状維持 (v2 lock 0 本なので実物は無い)。本 wave は (c) を採り domain を据え置いた。
- {{T:qualification-verifier-closure}} **P2・新規**: T126 qualification の code identity は
  verifier では `core.py` しか含まず、`dsg/model/parse` の変更に反応しない。
  qualification 成果物が旧 correctness 実装を指し続ける。threat scope に含めるかを決める。
