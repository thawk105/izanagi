# [T-139] 本走前置 — U3 の roadmap 例外 commit と事前登録の凍結 (段 1 brief)

```text
authority: none
default_effect: no-state-change
```

## scope (docs のみ。実装差分ゼロ)

1. **roadmap §3.6(3') に paired の限定例外**を in-place で追記する (協議改訂。合意 = worklog (300) の
   T-139 項。`docs/roadmap-history/README.md` によりセレモニー 1–3 は不要、版上げ・history 凍結もしない)。
2. **新 D (D232) を spool fragment で新設**し、D19 の適用前提を「別セッション比較の採否 floor」に限定する。
   同 D に「事前登録 commit が無ければ pilot を投入しない」**順序 gate を署名で**書く。
3. **凍結事前登録**を作る。`preregistration-draft.md` の内容へ κ=20% と U1〜U11 の確定値を反映し、
   `【U#】` を 1 つも残さない。**凍結の実装は commit/blob 参照束縛のみ** — 現在木への byte-pin
   (`FROZEN_MANIFEST` 型) 検査は追加しない (main land を妨げる検査を作らない)。
4. 上記 1–3 を **同一 commit** に入れる (D134 決定 (3) の「同じ変更単位」要求)。

## 確定済みユーザー裁定 (2026-08-07、11 件全件。正本 = `2026-08-07_t139-mainrun-design/package.md`)

U1 (a) 総量型 `H_w = D_w − κ_w·S_w` / **U2 κ_W1 = κ_W2 = 0.20** / U3 本 wave の手続き /
U4 全体 80%・`d=1.0` 固定 / U5 pilot 8 + 予備 2、本走へ非合算 / U6 (a) 1 cluster 6 反復・全 6 順列各 1 回 /
U7 算術平均 / U8 primary 系列と個別公表系列に別々の累積台帳 / U9 producer → pilot → validator/consumer → 本走 /
U10 総上限 26 割当て相当、pilot 1 本目で会計痕跡を検証 / U11 (a) 予算組み直し + 予備 (b)。

## 不変条件 (緩めない)

- 絶対規律 1–6 は不変。例外は §3.6 の**測定安定性**にだけ開き、trace 分離・正しさゲート・
  正しさシグナルの後付け禁止には一切触れない。
- D19 の within-run / between-run 二分と `BETWEEN_RUN_CV = 0.030` は**不変**。例外は
  「事前登録された paired cluster 設計における同一割当て内の arm 間 contrast」にだけ適用し、
  campaign の通常 compare (variant vs baseline の別セッション比較) には及ばない。
- 例外は無条件開放にしない。少なくとも (i) 実走前 commit された事前登録、(ii) 推定・検定・区間が
  すべて cluster (割当て) level の標本共分散から構成され within-run rep を独立標本に数えない、
  (iii) cluster 内で arm 位置・直前 arm が exact に均衡、(iv) pairing 不成立 ⇒ 判定不能の
  fail-closed (D134 決定 (4)、自動 unpaired fallback 禁止)、(v) 適格性の権威は独立 validator (D162)
  — を条件として書く。
- 事前登録は authority を持つ凍結文書であり、可変状態の正本にしない (worklog 末尾・現行 phase doc が正本)。

## provisional 裁定 (親の暫定。**攻撃対象**)

- **(P1) 凍結事前登録の置き場所** = `output/insights/2026-08-07_t139-mainrun-design/preregistration.md`
  を新規作成し、`preregistration-draft.md` は履歴として**書き換えない**。同 dir の `README.md` に
  凍結版への pointer を足す。対抗案: (a) `docs/` 新規文書 + `tools/check_docs.py` の `LIVING_DOCS` 追加
  (= 実装面が発生し「docs のみ」を逸脱、Codex author 必須)、(c) draft を in-place 書き換え
  (= 逐語凍結の記録を潰す)。
- **(P2) 例外の適用範囲**を「事前登録された paired cluster 設計一般」と書く (RF study 専用にしない)。
  対抗案: 本 study 専用に限定して将来の一般化を新裁定へ送る。
- **(P3) gate の実施点** = 既存の `orchestrator/campaign/trial_registry.py::assert_prereg_ancestor`
  (`prereg_commit` が measurement checkout の祖先) を機械執行点として**名指しするだけ**とし、
  配線は producer 実装 wave に置く。本 wave では検査を追加しない。
- **(P4) 「同じ変更単位」の充足**: D232 は `docs/spool/decisions/` の fragment として同一 commit に入れ、
  canonical `docs/decisions.md` への採番・追記は段 9 land が lock 内で行う (DW-S07。wave 側で fold しない)。
  fragment と roadmap 改訂と事前登録が同一 commit にあることをもって D134 決定 (3) を満たすと解する。

## 成果物影響 (DW-G05)

- 1・2 を入れないと、同じ paired 実測に対し RF 判定と §3.6(4) の 3% floor 丸めの 2 解釈が残り、
  消費側ごとに certified 選択の受理集合が反転しうる。
- 2 の gate が無いと、事前登録なしの pilot 投入が可能になり、その全割当てが D162 の正例 artifact
  として使えず捨てになる。
- 3 が commit されないと pilot・本走の raw が `prereg_commit` を参照できず、独立 validator の
  適格性再計算が不能 = 正例 artifact が成立しない。

## 成果物の形

`docs/roadmap.md` §3.6 の追記 1 箇所、`docs/spool/decisions/` の D fragment 1 本、
`output/insights/2026-08-07_t139-mainrun-design/preregistration.md` 新規 1 本 + 同 `README.md` 1 行、
`docs/spool/worklog/` の worklog fragment 1 本。統合 commit 1 本。

## 並列分割方針

実装面ゼロのため段 5 の Codex 実装子は起動しない (親が docs 本文を編集する)。ただし本 wave は
「正しさ防壁に触る」「受理集合が変わる」に該当するため `DW-C00` の軽量版に当たらず、
段 2 起草 1 本・段 3 敵対 2 レンズ・段 6 敵対レビュー 2 本を起動する。
変異 matrix は実装差分ゼロのため射程外 (D134 決定 (2) と同型)。受入全走は親が行う。

## 実測済みの前提 (brief 前)

- roadmap §3.6(3') は今も「variant と baseline は決して同一セッションで測らない」と書いており、
  D19 本文も同文を持つ。D134 決定 (3) の限定は未履行。次の D 番号は D232 (最終 = D231)。
- `preregistration` / `2026-08-07_t139-mainrun-design` を key にする byte-pin は `*.py` に 0 件。
  `FROZEN_MANIFEST` は 23 entry で当該 path を含まない (DW-O09 の pin 閉包、docs path も検索済み)。
- commit 束縛機構は実在する — `trial_registry.py::assert_prereg_ancestor` と
  `s8c_preregistration.py` の commit 指定 blob 評価 (DW-O13 の入力実在確認)。
- 事前登録文書の先例は `docs/phase3-main-experiment.md` / `docs/phase3-8c-preregistration.md`
  (ともに `LIVING_DOCS` 登録済み) と `output/env/pegasus/.../preregistration.md` (run artifact 併置)。
- 受入・実測環境: 親の worktree (login node) で `tools/run_tests.py` 受入形と `tools/check_docs.py`。
  計測は行わない (性能値を主張しない wave)。
