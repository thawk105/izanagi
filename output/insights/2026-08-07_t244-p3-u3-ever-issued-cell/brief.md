# 段 1 brief — [T-244] P3 ever-issued cell 台帳 (U-3)

前提実測は `parent-measured.md` (N1〜N9)。裁定正本は
`output/insights/2026-08-05_t244-p3-design/README.md` §9 の U-3 行、批准は worklog (269)。

## scope

U-3 = (a) の**機械化できる中核だけ**を D96 の同一変更単位で入れる。すなわち
**同一 series の連続する authority document を跨いで、既に発行済みの cell key の再発行を拒否する**。
台帳は commit 済み artifact として置き、authority 読み込み経路が読む。
**含めない**: 意味等価性の機械判定 (裁定どおり人間 gate) / epoch router / production provisioning /
authority bytes の変更 / U-8 critic 後置 / 8c 結線。

## 確定済みユーザー裁定

- **U-3 = (a)** series 全体の ever-issued cell 台帳で全世代重複拒否。意味等価性の裁定は人間 gate。
- **U-2 = (b)** 予算 root の同一性は「同一 clone 内の honest caller に対する保証」と明示的に弱めて名乗る。
  本 wave の台帳もこの trust model を継承する (台帳自身を消せる者は防げない)。
- **U-10 批准済みだが発行は 3 条件成立後** — 本番 authority は entry 0 のまま。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 裁定文の「世代」は実装に存在しない (N2/N3/N4)。本 wave はこれを
  「同一 series の連続する authority document」と読み替えて実装する。この読み替えが裁定の射程内か。
- **(P2)** 台帳の substrate = repo に commit する append-only な JSON artifact 1 本とし、
  `_authority_from_bytes` 系の検証経路が「live authority の各 cell key が台帳に載っており、
  台帳が束縛する `origin_id` と一致する」ことを要求する。runtime 側には置かない (N4 により不活性)。
- **(P3)** DW-G04 の発火 gate は、既存の同型検査 (単一 blob 内 cell 重複拒否) が
  `origins: []` のまま既に production の authority load path に存在していることをもって満たすと判断する。
  正例・負例は fixture authority で書く。
- **(P4)** 段の形は**軽量版でなく全形**にする — 受理集合 (authority の受理判定) が変わるため
  DW-C00 の除外条件に当たらない。

## 不変条件

- **I1** `reflux_origin_authority_v2.json` の bytes を変更しない (`origins: []` のまま)。
- **I2** production runtime 初期化の禁止 (`_initialize_locked`) を解除しない。lazy-create を作らない。
- **I3** 名乗りの上限は D179 §7 / D183 のまま — P3 充足・provisioning 解禁・多世代開放・
  cap-lift・certified 選択を名乗らない。**「意味等価な再発行を防いだ」とも名乗らない。**
- **I4** D96 — 新しい D を起こし、境界テストを同じ変更単位で更新する。
- **I5** 台帳が空・authority が空の初期状態で既存受入が緑のままであること。

## 成果物の形

新 artifact 1 本 + `reflux_origin_ledger.py` の検証追加 + 公開 error 文字列、
`test_reflux_origin_ledger.py` への正例 1 と負例群 (跨ぎ再発行 / 台帳欠落 / 非 canonical /
origin_id 不一致 / 空×空の正例)、D 1 本 (spool fragment)、phase3 の該当行、worklog fragment。

## 成果物影響 (DW-G05)

実装しない場合に変わるのは **authority の受理集合だけ**である。certified 選択・材料レポート・
試行台帳・proof chain の現在値と参照は、authority が空で provisioning が閉じているため不変。
放置すると、U-10 の 3 条件が成立して最初の entry が発行された後に、authority を書き換える形で
同一 cell を別 origin_id として再発行し、使用量 0 の予算を得る経路が残る。

## 分割方針

段 5 は所有を 2 分割する — 所有 A = `orchestrator/campaign/` (台帳 artifact + 検証)、
所有 B = `orchestrator/tests/` (正負例)。docs は親が書く。

## 受入・実測の環境

repo root で `python3 tools/run_tests.py` (ログインノードでは gen_S へ同期 dispatch)。
変異 matrix も同 runner。所在は worklog、機体固有情報は `docs/pegasus-runbook.md`。
