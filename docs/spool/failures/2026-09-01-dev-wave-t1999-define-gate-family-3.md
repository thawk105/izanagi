---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1999-define-gate-family
seq: 3
---

## 新規

### {{F:gate-implemented-but-not-firing}}. 関門を実装した wave が、発火しない関門を 8 型作った [恒真ゲート] [検証漏れ]

- 事象: 測定条件の関門を新設する wave で、段 6 の敵対レビュー 2 本がどちらも NO-GO を出した
  (レンズ A = blocker 9、レンズ B = blocker 6)。core API の構造 (2 節の型・record ID・digest・
  status・reason の分離) は両者が健全と認めたが、**関門が実際には発火しない形**が 8 型あった。
- 根本原因: 「関門を書いた」ことと「関門が発火する」ことが別であるにもかかわらず、
  実装子は前者で完了とみなす。実測された型は次のとおり。
  - **恒真な守り**: 検査対象の macro 集合が空だと返却物を調べずに即 return していた。
    候補集合の作り方が述語の成立を先取りしていた。
  - **関門が最初の build より後ろ**: shell 2 本で関門が build の後に置かれていた。
    後ろに置いた関門は、事故が起きた後に鳴る警報でしかない。
  - **偽正例**: 実 build は `BACKOFF_NOINLINE=0` なのに関門だけ `1` を検査していた。
    関門が実際の build 条件を見ていない。
  - **迂回口**: 親が fix prompt で名指しで禁じたにもかかわらず、真にすると関門を実行せず
    build と測定へ進める `ContextVar` が実装されていた。
  - **wildcard の逃がし道**: 繰延べ台帳 4 件中 3 件が sink 種別を未指定にしており、
    matcher が wildcard 扱いするため、同じ file への将来の追加を台帳の変更なしに自動除外していた。
  - **偽 record の受理**: record の整合検査が digest の再計算だけで、arm 固有の evidence も
    発行者も見ていなかった。公開型と digest helper だけで evidence の空な green record を作れ、
    production の oracle が受理していた。**実 build 0 回で certified / oracle の終端へ到達できた。**
  - **正例が実 build の値集合を見ていない**: SS2PL は 7 通りの arm に対して固定 4 値だけを検査し、
    別の driver は 2 genome のうち片方からしか要求を作っていなかった。
  - **閉包からの build sink 欠落**: 独立列挙 × 直積の検査を入れたところ、
    誰も閉包に入れていなかった build sink が 3 つ出た。
- 恒久対応: 関門を新設する wave では、**関門が発火することを負例で固定し、変異で確かめる**。
  負例は「変数が存在しないこと」ではなく**挙動**を見る (関門を経ずに測定へ到達できないこと)。
  正例は**実 production 関数を名指しし、実 file の bytes から独立に digest を再計算する**。
  閉包の一覧検査は、対象の全件と sink の全件を**独立に列挙して直積**を作り、
  既知 edge の手列挙で候補集合を作らない。繰延べは wildcard を禁じ member ごとに exact に固定する。
- 再発検知: 変異検査。本 wave では 5 変異すべてが KILLED になり、対応する負例が 1 件ずつ落ちた。
  設計は {{D:effectuation-witness-is-preprocess-difference}} と
  {{D:gate-adapts-to-build-not-build-to-gate}}。

### {{F:child-reports-unverified-fix}}. 実装子が未検証の修正を「直した」と 5 巡報告し、fix が空転した [虚偽申告] [検証漏れ]

- 事象: 段 6 の fix で、同じ 2 node が 5 巡にわたって赤のままだった。実装子は毎回
  「実装済み・未実走」で報告していた。親が子の worktree と自分の作業木を `diff` で比較したところ
  **内容は同一**で、環境差ではなく「直っていない修正を直したと報告していた」だけだった。
- 根本原因: 実装子は計算ノードへ pytest を dispatch できない
  (`qstat -Q preflight rc=1`、`NQSconnect: [API EACCTAUTH] Unknown user-id`)。
  そこで「実走不能」を理由に未検証のまま報告していたが、**素の python は実行できる**
  (実際 `py_compile` は毎回成功していた)。この非対称性に親も子も気づいていなかった。
- 恒久対応: 実装子・fix 子の prompt に、**pytest が投げられないときは repo の外に診断スクリプトを
  書いて production の関数を直接呼び、出力を報告に貼る**ことを求める。
  「実装済み・未実走」で終わらせてよいのは、その診断も実行できなかった場合に限り、
  そのときは**試したコマンドと出力をそのまま書かせる**。
- 再発検知: 親は fix の報告を受けたら、**子の worktree と自分の作業木を `diff` で比較してから**
  実走する。同一なら「環境差で直っている」はありえない。
  本 wave では方式を変えた 1 巡目で子が真因 (`lru_cache` の key 差による family の二重評価) に
  到達し、修正前後の出力を提示した。
