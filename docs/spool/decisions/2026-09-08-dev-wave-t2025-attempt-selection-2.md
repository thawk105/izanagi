---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2025-attempt-selection
seq: 2
---

## {{D:attempt-selection-materialize-gate}}. attempt 単位の選別は materialize の内側 1 箇所で塞ぎ、事前登録側に台帳を作らない

**決定:** A-2 / A-6 認証の attempt 選別対策は、認証成果物を作る唯一の関数 `materialize` の
内側だけに置く。判定は 2 つで、(1) 対象 attempt の `preregistration.json` を読み
`automatic_retry is False` を含む exact 検査を通すこと、(2) 同じ組
(study, 記録された policy_sha256, current_pin の先頭 7 桁) の他の attempt が結果 footprint を
持たないこと。結果 footprint は `receipts/acquisition.json`、`receipts/completion.json`、
`raw-manifest.json`、`jobs/<workload>/raw/` 直下の regular file の論理和とする。

事前登録・receipt writer・投入 driver には gate を置かない。cohort claim 台帳、hash 鎖、
scheduler の終端再観測、attempt の扱いを宣言する CLI、成果物 bundle への一覧追加は採らない。

**記録された `policy_sha256` が現行 policy と一致することは要求しない。**

**理由:**
- 判定を必須経路の内側に置くので、呼び忘れが起きない。D431 が塞いだ「呼ばなければ効かない CLI」型に
  ならない。投入 driver 側に新しい呼び出しを足す必要も無い。
- 運用者の理由申告で解錠する設計は採れない。結果を見た後の虚偽分類をコードで検出できないため、
  宣言は事実上の素通しになる。解錠の根拠は機械が観測できる事実 (結果 footprint の不在) に置く。
- 「組に結果を出した attempt は最大 1 個」を要求すれば、選ぶ対象が 2 つ以上並ぶ状態が作れない。
  自動再試行は無く、手動再試行は「前が何も結果を出さなかったとき」に限られる、という
  `automatic_retry: false` の意味がそのまま機械の述語になる。
- 事前登録側に gate を置くと、gate 導入前に作られた既存 attempt が production 経路で
  事故停止する。実測で稼働中の A-6 attempt がこれに該当した。現行 policy との hash 一致を
  要求する案も同じ理由で採れない — 稼働中の attempt の記録は現行 policy と一致しない。
- pin の正規化を先頭 7 桁への切り詰めにするのは、実データに同じ commit が短縮 sha と 40 桁 full
  sha の両方で記録されているためである。prefix 一致の二値判定は推移律を満たさず組分けに使えない。
  7 桁が偶然衝突する別 commit は同じ組へ保守的にまとめられるが、それは受理集合を狭める側である。

**却下した選択肢:**
- 組ごとに連番 + hash 鎖の claim 台帳を作り、事前登録時に前 attempt の scheduler 終端を
  `qstat` で観測する — 本題に不要で、事前登録に外部 command 依存を持ち込み、
  台帳を持たない既存 attempt を止める。
- attempt の扱いを閉じた理由列挙で宣言する CLI を解錠条件にする — 結果を見た後の虚偽分類を
  機械で検出できない。記録として残す価値はあるが、受理条件にはしない。
- 成果物 bundle へ組の一覧 file を足す — 既存テストが bundle の file 名一覧を厳密に固定しており、
  本題の成立には不要である。
- 組に attempt は 1 個だけとする — 実在の durable base に同じ組の attempt が複数あり、
  到達不能な述語になる。

**閉じない残余:** filesystem を自由に書ける主体は、attempt root と結果 footprint を退避してから
測り直せる。`O_EXCL` は最初の作成競走を閉じるが、後からの削除・再構成を防ぐ外部の
append-only authority ではない。D387 と同じ限界であり、「選別を閉じた」とは主張しない。
