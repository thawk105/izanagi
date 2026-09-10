# [T-524] 実験単位を slot 組へ改める最小形 — 実施記録

D1269 の最小形を実装した wave の記録。branch `worktree-dev-wave-t524-slot-experiment-unit`。

## 何を作ったか

実験単位を `(prereg_generation, holdout, arm, replicate_slot)` の組へ改め、承認 artifact が
全 slot と個数を固定し、下流が predeclared receipt の全列挙と消費を検査する形にした。
設計判断の正本は decisions。ここには経緯と逐語だけを置く。

**承認側 (attempt registry genesis)**

- slot へ `prereg_generation` を必須 field で足し、schema を `p3-8c-attempt-registry/v3` へ上げた。
- **root 全体で世代が単一**であることを全 reader に要求する。series key は変更していない。
- genesis 作成器は `prereg_generation` を必須引数に取り、全 slot の同名 field と exact 一致を要求する。
  slot への自動補完経路は作らない。
- 世代は event row へ複製せず capability digest に含めて束縛する。
- schema 分岐は「current なら v2」ではなく schema ごとの明示 map にした。

**下流側 (outer acceptance receipt)**

- receipt schema を `p3-8c-trial-acceptance-receipt/v5` へ上げ、attempt registry の path・
  prefix bytes/hash・slot projection (世代・全 unit・個数)・内容 commit・発効 commit を束縛する。
- `verify_acceptance_receipt` が prefix を独立に replay し、genesis 由来の**非空**期待集合と
  final terminal を照合する。期待集合は genesis 側から作り terminal 側から導出しない。
- final terminal は `observed` / `terminal-failure` だけを数える。`retryable-failure` は中間、
  `not-consumed` は運べない。
- 下流の消費入口は current schema (v5) を必須とする。v1〜v4 は読取可能だが下流 capability へ到達しない。
- 内容 commit 時点の blob が genesis のみであることと、`rev-list --all` による第二 root 不在を
  発行側と同じ境界で要求する。

## 作らなかったもの (段 4 / 段 6 裁定)

発行側の全列挙 helper、production genesis producer、人間承認 authority、全世代台帳、
revocation、expiry、check registry、汎用 core への一般化、`replicate_index > 0` の受理、
`not-consumed` の outer receipt 搬送、独立 clone 間 best-of-N の閉塞。

## 親の前提が現物で覆された経過

段 1 brief の中心 2 前提は誤りだった。

| 前提 | 判定 | 実測 |
|---|---|---|
| (P1) 承認 artifact = 条件凍結 artifact | **反証** | 条件凍結は世代番号の出所。全 slot と個数を固定しているのは attempt registry genesis |
| (P2) 別 manifest を N 個登録する経路が空いている | **反証** | canonical path の create-only と全 ref 第二 root 検査で、path 面・commit 面は変更前から閉じていた |
| (P3) 失敗・却下も消費に数える | **支持 (精密化のうえ一部不採用)** | `retryable-failure` は中間。`not-consumed` は receipt へ運べないので正例から外した |
| (P4) 既存 g1..g13 を変えずに実装できる | **支持** | 世代は activation report から取得できる |

残っていた実際の穴は、**世代の意味束縛が無いこと**と、**下流に検査が一切ないこと**の 2 点だけだった。

## 段 3 が中心設計を否定した

- **series key へ世代を入れる案は受理集合を広げる。** 同じ series に別世代の `attempt_index=0` を
  1 件ずつ置いた形が別 series として通る。世代の単一性は root 全体の不変条件として書いた。
- **発行側の全列挙 helper は純増でない。** outer acceptance は既に 6 report・manifest exact・
  genesis initial・report↔terminal の合成で全 unit 消費を強制している。同じ入力を前後の層が
  拒否する位置には変異を登録できず、単一理由性を満たせない。重心を下流へ移した。

## 段 6 が blocker 2 件を捕まえた

1. **旧 schema への downgrade が新検査の迂回路だった。** 下流の消費入口が v1〜v4 を同じ
   verified capability へ通していた。**追加したテスト自身が、v5 から attempt field を抜いて
   v4 に落とした receipt を verified にしていた。**
2. **事前固定が下流で未証明だった。** 検証器が registry の自己整合性しか見ないため、結果を見てから
   完成済みの registry を 1 commit で置いても通った。

加えて must-fix 2 件 (下流の履歴検査が HEAD ancestry だけ / projection 再照合に変異 killer が無い)、
nit 1 件 (揮発分類の漏れ)。全件 real と裁定し、**発行側に既に在る gate を下流からも使う**形で閉じた。

## fix は 3 巡かかった

| 巡 | 赤 | 原因 | production 変更 |
|---|---|---|---|
| 1 | 5 | 揮発分類の漏れ、厳密 pin の追随、test helper の誤り | なし |
| 2 | 13 | **commit 種別の取り違え** — attempt row は `prereg_content_commit` を持つのに receipt の `prereg_commit` と比較していた | あり |
| 3 | 0 | 受領証へ内容 commit と発効 commit を既存名で束縛 | あり |

2 巡目の原因は親が現物で特定した。子の報告だけでは「別の commit である」ことに到達しない。

## 子はテストを 1 件も実走できなかった

実装子 1 名と fix 子 3 名の計 4 名すべてが、Pegasus への投入で `qstat -Q` preflight rc=1 /
rc=16 / `child_started=false` となり、テストを実走できなかった。**4 名とも「実装済み・未実走」と
正直に申告し、緑とは報告しなかった。** テストの実測はすべて親が行った (焦点走 4 回)。

## 変異 matrix

`mutation-ledger.json` が正本。**baseline PASSED / KILLED 5 / SURVIVED 0 / MISMATCH 0 /
期待 node 完全一致 5/5。**

| M | 無効化した述語 | 検出したテスト |
|---|---|---|
| M1 | v3 reader の root 単一世代 | 1 本 |
| M2 | genesis 作成器の引数 ↔ 全 slot 一致 | 1 本 |
| M3a | v5 の全 unit 消費 | 1 本 |
| M3b | v5 の projection 再照合 | 1 本 |
| M4 | 下流入口の current schema 要求 | 3 本 |

M3 を M3a / M3b に割ったのは、段 6 レビュー B が「projection 再照合だけを無効化しても赤くなる
テストが無い」と実測で示したためである。DW-M07 に従い probe (全件 SURVIVED 期待) で観測 node を
集めてから、期待 node の完全集合で本走した。

**erratum: M3a の赤は意図した拒否ではなく `IndexError` 経由である。** 同じ 1 行が
「終端欠落の拒否」と「添字の安全」を兼ねているため、無効化すると空 list への添字で落ちる。
受理側へは倒れず fail-closed のままであり、赤くなるのはその述語専用のテスト 1 本だけなので
単独帰属は保たれるが、理由が意図どおりでないことをここに残す。

## main 取り込みの合成監査

両親がともに実装面を触ったため、Codex `role=author` が合成監査と merge message を起草した。

- textual な競合 0 件。両親がともに触ったのはテスト 3 ファイル (main 側 +1268 行)。
- **併合後の未 commit 走行が `contract-loader-drift` で 21 件赤になった。** HEAD blob 束縛による
  既知の型で、実装の回帰ではない。merge を commit して再走し 758 passed / 0 failed。
- 監査子は「758 passed は補助事実であり、健全判定は差分・call path・schema gate・揮発 path の
  現物照合に基づく」と明記した。監査中に main がさらに進んでいたことも併せて報告した。

## 逐語

`verbatim/` に段 2・段 3 (2 本)・段 5・段 6 (fix 3 本 + review 2 本)・段 9 合成監査の 10 本を置く。
段 4 と段 6 の裁定は `ruling-stage4.md` / `ruling-stage6.md`。

## 次 wave の出発点

正式系列は現在 production から起動できない (`create_attempt_registry_genesis` の caller が
すべてテストで、CLI にも subcommand が無い)。本 wave の scope 外として実装していない。
worklog の「次の一手」に新規 4 件として起票した。
