# [T-922] 測定装置の production 正例経路 — dev-wave-t922-measure-happypath

2026-08-12。base main `6331284e` → 実装 `4019cb4f` → 負例追加 `af3892ad`。
branch `worktree-dev-wave-t922-measure-happypath`。

## この wave が確かめたこと

**T-810 測定装置には launch intent / config を書く production producer が存在しない。**
`launch_intent` / `validator_kwargs` / `admission_policy_path` の非 test consumer は
`tools/pegasus/t810_coordinator.py` 自身しかなく、`.sh` / `.pbs` / `.json` からの
coordinator 呼び出しも 0 件である。これは設計上の意図で、D331 が witness の発行経路を
実装しないと定め、admission policy の ratify も [T-923] としてユーザー裁定 deny 中にある。

したがって「production 正例経路を 1 本通す」は、**実際に走らせる意味では本 wave で
原理的に達成できない**。達成できるのは「coordinator の production 関数を通って staged
wrapper CLI へ到達する統合経路が成立し、テストで実行される」ことに限られる。

## 実装した範囲 (caller 外 authority を要さないもの)

| 項 | 状態 | 内容 |
|---|---|---|
| (1) coordinator → wrapper CLI | 統合経路のみ | 生成 PBS script file 自体を subprocess 実行し、`--request` parse・静的 request decode・PBS runtime identity 補完まで到達。staged package は `PYTHONPATH` に repo を含めない |
| (2) staged file identity | 部分実施 | 宣言 digest と live bytes の一致を publication 時と qsub effect 直前に要求。wrapper file は同梱 `t810_pbs_wrapper.py` の bytes へ束縛 |
| (3) guard / budget | 未実施 | authority と 2 相結線を裁定へ返した |
| (4) repository roots | 実施 | coordinator の設置場所から live git identity を導き、caller roots とは和集合 |

**開いたまま:** 自己整合した任意 binary、staged package の依存閉包、qsub 後から node 読取までの
TOCTOU、guard の 2 相結線、budget の canonical ledger anchor、production producer の不在。

## 設計判断の要点

authority を **import 解決ではなく coordinator 自身の設置場所からパスで導く**。
`tools/pegasus` は `__init__.py` を持たない namespace package なので、
`pbs_wrapper.__file__` を authority にすると `PYTHONPATH` shadowing で authority ごと
差し替えられる。詳細は decisions の該当エントリ。

caller 提供の roots は捨てず**和集合**にする。caller は roots を増やせるが減らせない。
共有 repo では並行 wave が worktree を絶えず追加・撤去するため live registry が一瞬だけ
解決不能になりうるが、解決できない登録も**捨てず**その主張 root を非 strict 解決で保持する。
roots への操作を追加のみに保てば、外乱は過剰拒否にも受理拡大にも化けない。

## 変異結果

`mutation/mutation-spec.json` (6 変異) を HEAD `af3892ad` へ本走。
**KILLED 6 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0** (`mutation/mutation-result.json`)。

第 1 巡 (`mutation/mutation-result-round1.json`、HEAD `4019cb4f`) では
**M3 が SURVIVED**。roots の authority を live 導出から caller 申告値へ戻す変異が生き残った。
機序は等価変異で、fixture が `validator_kwargs.approved_git_identity` に live repo の
identity をそのまま入れていたため caller 申告値と live 導出値が全テストで一致していた。
既存の偽装テストは caller roots 側しか偽装していない。

**本 wave の中心的な主張「roots の authority を caller から奪った」を検証するテストが
1 件も無かった。段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本、合わせて静的レビュー 4 本が
これを検出しておらず、変異だけが捕まえた。** 別の実 git repository を自己整合させて
`approved_git_identity` へ与える負例 (`af3892ad`) で閉じた。

M1 の第 1 巡 MISMATCH は親の登録漏れ (期待 node が 1 件だったが実際は 2 件) であり、
実装側の問題ではない。M4 は M3 と同一 code region で独立適用できないため分離し直した。
旧 M5 (`--request` 束縛の削除) は既存の exact-argv assert に先取りされるため
`DW-M01` に従い登録から外した — **既存検査を外して単独帰属させる提案は棄却した** (検査の弱体化)。

## 逐語

`verbatim/` に段 2 プラン、段 3 敵対相談 2 本、段 5 実装、段 6 fix 3 巡、段 6 敵対レビュー 2 本。
段 3 の A レンズは初回 `guard_bash` により output 0 bytes で終了しており (下記)、
`verbatim/s3-lensA.md` は再投入分である。

## 運用上の実測

- **`guard_bash` が敵対レンズ 1 本を丸ごと殺した。** read-only の hash 計算のために
  `tools/pegasus/` を含む shell command を組み立てた瞬間に機械拒否され、
  codex が rc=1 / output 0 bytes で終了。model_calls 45、約 1,080 秒を空費した。
  hook は正しく動作している。prompt 側の指示で回収した。
- **並行 wave の worktree 増減で焦点走が 34 件赤になった。** 同一コードの再走で 1 件まで減り、
  親が独立に解決処理を再現して異常 0 件を実測して一過性と確定した。
- 焦点走の最終: `test_t810_coordinator.py` 40 passed / t810 系 9 file 285 passed、いずれも rc=0。
