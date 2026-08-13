---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: t979-cheap-history-scan
seq: 1
title: 受領証の履歴走査を安価先行の二段構えにして 26.3 秒から 0.71 秒へ下げ、消える検出器を機械 guard へ移した (コード + docs、変異 10/10 期待どおり、branch worktree-t979-cheap-history-scan)
---

## 本文

ユーザー裁定 (rulings 第 9 束 #2) の選択肢 (i)「構文検証を通した安価出力を不在の十分な証明とする」
を実装条件 4 点つきで実施した wave。設計は {{D:cheap-first-history-scan}}。

### 前提は実測してから着手した

D328 (2026-08-12) が凍結チェーン検証を保留にしており、その理由の一つが「受入の床に
ファイル数比例の走査 (約 24 秒)」だった。保留で対象が消えていないかを先に確かめた。
保留は check_id 単位の bytes 同一性検査を対象にしており、`inspect_receipt_history` の
履歴走査は保留対象外で、本番経路は生きていた。

### 親 brief の誤りを 2 件、段 3 の敵対レンズが摘出し実測で確定した

1. 「既存の near-copy テストは `--find-copies-harder` の追加を検出しない」は**誤り**だった。
   実装は OID 比較より先に path 検査を見るため、この flag が付くと near-copy は `C` record になり
   判定が `True` へ変わって既存テストは赤になる ({{F:coverage-inventory-without-tracing-judgment-order}})。
2. **その検出力は二段構えにすると死ぬ。** near-copy は安価出力に対象 path も対象 OID も出さないので
   trigger が発火せず、高価走行に到達しない。裁定の実装条件「`--find-copies-harder` を機械的に排除」は
   この検出器の移動を見越したものであり、guard は受理集合の保存そのものを担う。

裏取りは synthetic repo の実測で行った (git 2.34.1)。**`-C` を 2 回書くと
`--find-copies-harder` と 1 byte 違わぬ raw 出力になる**ことも同じ実測で確認し、
禁止文字列の不在検査では守れないことが確定した。

### 段 6 の敵対レビューが NO-GO を出し、guard の自己参照を摘出した

初回実装の guard は「完成 argv が凍結定数のいずれかと一致するか」を見ており、
**定数そのものへ `-C` を足す変異は比較対象も同時に変わるため素通り**していた
({{F:self-referential-argv-guard}})。実際に止めていたのはテスト側の literal 比較だけで、
「production の機械 guard が禁止 flag を殺す」という主張は成立していなかった。
併せて、status 非依存の検査が `_git` seam しか捕捉しておらず `_git_rc` を使う変異を通す点、
高価側だけが壊れたときの fail-closed control が二段構え後に存在しない点も摘出された。
must-fix 7 件に fix を当て、焦点再レビューが F1〜F7 すべて `closed` で **GO** を出した。

### 実測 (HEAD `e4623d72`、reachable 3,572 / descendants 2,920 / targets 2,919)

| 量 | 値 |
|---|---|
| 二段構え (3 回) | **0.704 / 0.706 / 0.710 秒**、判定 `False` |
| 高価走行単独 (同一機体・同一入力) | **26.271 秒**、判定 `False` |
| 安価走行単独 | 0.710 秒 |
| 包含 | 成立 (安価・高価とも path 11,448 件 / 非零 dst OID 12,279 件で一致) |

**言えるのはここまでである。** 短縮したのは健全な trigger 不発入力に対する uncached な
helper 1 回であり、**受入全走 wall と consumer 別 critical path は未測定**である
(worker ID が無く critical path を再構成できない — 既起票の [T-980] が同内容)。
trigger 発火時は安価と高価の**両方**を払うため従来より重い。
裁定パッケージの見積り 0.37 秒には届いていない。差の約 0.35 秒は Python 側で
約 19.6 万件の record を解析するコストで、これが新しい律速である。
見積りは git コマンド単体の時間から出ており、解析コストを含んでいなかった。
包含は有限観測では証明されない — 根拠は diffcore が既存 filepair を対応付けるだけで
新しい path/OID を生成しないことに置き、テストは回帰検査であって証明ではない。

### 変異は検出器の移動まで実証した

本走は **10/10 期待どおり、MISMATCH ゼロ** (baseline 60 passed、runner 範囲 =
`orchestrator/tests/test_t080_freeze_migration.py`)。内訳は
**受理集合の kill 7 件 / fail-closed の kill 1 件 / 構造 pin 1 件 (受理集合を変えないので
kill に数えない) / 意味不変の正例 1 件 SURVIVED**。
初回は期待 node の完全集合を導出する probe と位置づけ、MISMATCH 8 件を実測から機械生成し直して
再登録・再走した (手で転記すると取りこぼすため生成を script 化した)。

新旧両走 (DW-M08) で検出器の移動を実証した。同一変異 (`-C` 二重化) を当てると、
wave 前 HEAD `9e2923c6` では赤 **1 件** (near-copy の期待値 = 振る舞いによる検出)、
wave 後 HEAD `e4623d72` では赤 **14 件** (うち **13 件**が production guard 由来、
残り 1 件は定数の literal 比較で先に赤になる) だった。
wave 後も同じ matrix テストが赤だが理由が違う — near-copy は cheap miss で高価走行に届かず、
case 1 (modified) が高価走行へ到達して guard に弾かれる。

### 段 2・3 と段 6 の review 子は省かなかった

正しさ防壁 (凍結受領証の改竄検査) に触り、故障時意味論が変わる wave のため軽量版にしていない。
Codex 子は 8 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1 / focus 1)、
model call 合計 283、wall clock 合計 6,109 秒、全本 rc=0。
実装子・fix 子はいずれも sandbox から計算ノードへ届かず (`qstat` の socket 作成が拒否され rc=16)
テストを 1 本も実走できていない。焦点走・変異・受入はすべて親が計算ノードへ dispatch して実走した。

### 段 8 は dev-wave docs を変更しなかった

候補 4 件を裁定した。新しい失敗型 2 件は failures へ送った
({{F:self-referential-argv-guard}} と {{F:coverage-inventory-without-tracing-judgment-order}})。
残る 2 件 (変異 harness の `--attempt-out` を `--wrapper-attempt` と対で渡す契約、
Codex 実装子が計算ノードへ届かず必ず未実走になること) は**本文へ足さない**。
前者は harness が起動前に rc=2 と理由文で fail-closed にしており
「機械化できる対応は機械化を優先する」を既に満たす。後者は `DW-S05-C` の
「実走できない子は closed と申告せず『実装済み・未実走』と書く」が既に覆っている。
実測のない懸念で台帳を増やさない。

### 裁定パッケージ候補 (本 wave では実装しない)

- **git 実行ファイルの trust boundary**: `PATH` 上の `git` を wrapper に差し替えられると argv 検査は
  無力になる。絶対 path 固定か trust 宣言が要る。既存の全 git 呼び出しに等しく効く問題。
- **`_git` の resource envelope**: timeout と stdout 上限が無く、親の SIGKILL・巨大出力・OOM が
  安定した `receipt.git_error` にならない。
- **安価出力の semantic completeness の fault model**: 本 wave は裁定 (i) に従い
  「構文検証を通れば record を省略しない」を信頼境界として受け入れた。信頼しない設計へ戻すなら
  独立 tree 照合か高価走行が要る。再議はユーザー命令があるときだけ。

## 次の一手差分

### 完了

- [T-979] 受領証の履歴走査を安価先行の二段構えにした。本番入力で 26.271 秒から 0.704〜0.710 秒へ。
  受理集合は不変。消える予定だった `--find-copies-harder` の検出器を production の独立 argv guard へ移し、
  新旧両走で移動を実証した (wave 前 赤 1 件 → wave 後 赤 14 件)。
  remaining: none
  base: 8b568555f71833dd54bc511ec4d83ceae1855201091251a6ba0ec9b14f8d03c6

### 新規

- {{T:git-executable-trust-boundary}} **P3・新規**:
  `_git` は `PATH` 上の `git` を起動するため、wrapper に差し替えられると完成 argv の検査は
  無力になる。絶対 path 固定か trust 宣言のどちらを採るかの択一。
  freeze receipt 検証だけでなく全 git 呼び出しに等しく効く。
- {{T:git-subprocess-resource-envelope}} **P3・新規**:
  `_git` に timeout と stdout 上限が無い。git 子の非 0 終了と SIGPIPE は拾えるが、
  親の SIGKILL・巨大出力によるハング・OOM は安定した `receipt.git_error` にならず、
  受入台帳が欠測または infra red になって失敗理由を受理拒否と区別できない。
