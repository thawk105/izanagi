# [T-2545] D1881 — 事前登録が publication root を 1 つ名指しし、発行器がそれ以外を拒否する

wave `dev-wave-t2545-b4-publication-root` / branch `worktree-dev-wave-t2545-b4-publication-root`。
起点 `61e0e9c4a`。

## 何をしたか

B-4 prerun publication の発行先を、呼び手が実行時に選ぶ形から、事前登録が名指す 1 箇所へ変えた。

- `docs/phase3-b4-reflux-ablation-preregistration.md` の `## 6.` 見出し直後に名指しを 1 本置いた。
  値は repo 相対の `output/b4-prerun-publication`。
- `orchestrator/campaign/p3_b4_prerun_issuer.py` に型付き reason
  `publication_root_not_preregistered` を足し、canonical 化した root が名指しと一致しなければ
  CSPRNG 取得と publication root 作成より前に拒否する。名指しの不在・重複・書式不正・読取失敗・
  UTF-8 失敗も同じ reason で fail-closed にした。
- 発行器を呼ぶ test fixture 3 file を追従させた。

## 主張すること

- **新 issuer API を経由する発行は、発行器を置いた checkout の事前登録が名指す root 以外を拒否する。**
- 受理集合は縮小のみである。正常な宣言かつ名指し root では既存の拒否がそのまま残る。
- 凍結節 §5.1.1 の bytes は変えていない
  (sha256 `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`、変更前と一致)。
- producer-auth experiment が発行器へ持つ byte 逐語の錨 3 本は無傷で、実装後も各 1 回だけ存在する。

## 主張しないこと

- **系全体で別 root の publication を拒否した、とは言わない。**
  `p3_s4_loop` の bootstrap 束縛と `load_b4_prerun_publication` は呼び手から受け取った root を
  そのまま使う。別の checkout で名指しどおりに発行した bundle を、別の呼び手が絶対 path で指す
  経路は本変更では閉じない。
- したがって非保証列 `publication_under_a_different_root_is_not_prevented` は依然真であり、
  本 wave では 1 項も削っていない。同列の書き換えは [T-2546] の対象で、receipt bytes と
  材料レポートの provenance hash への束縛を伴うので文言だけの訂正にはならない。
- 「事前固定した集合であること」を証明したとは言わない。本変更が閉じたのは発行先の選択だけである。
- repository root の解決は `Path(__file__).resolve().parents[2]` であり、**本書を同梱する
  source checkout から import した場合にだけ成立する。** 同梱しない配置から import すると
  名指しを読めないので発行を拒否する。

## 実測した閉包 (置き場所を §6 に決めた根拠)

| 候補 | 判定 | 根拠 |
|---|---|---|
| §5.1.1 へ足す | 不可 | D2016 項 6 が「1 byte も触れない」。consumer が直下 H5 をちょうど 6 個・指紋順一致で要求 |
| §5 の表へ行を足す | 不可 | `p3_b4_admission_record` が 10 ラベルとの exact 集合一致と行数一致を要求。**行追加は集合比較の手前の行数検査で落ちる** |
| §6 へ項目を足す | 可 | 見出し逐語は consumer test が抽出終端として pin するが、見出しを変えなければ追記は通る |

`tools/check_docs.py` の B-4 固有検査は LIVING_DOCS 在籍 1 行だけで、文書全体の sha256 pin は無い。
解析 source closure `_CLOSURE_PATHS` の 5 module に発行器は含まれない。

事前登録文書**全体**の sha256 を束縛する経路は `p3_b4_admission_record` にあり、
`p3_b4_closed_critic` が sidecar へ転記する。文書全体の sha256 は
`5460dfc19dbad12724f8d99ad2c483f994f3a1bc22b85bebc367edac871db239` から
`09109bf472980fcceaa99b9aeab95f088b6d122d027aa62cd70d7031c4a4f47a` へ変わったが、
**base / sort / trigger の admission record は 3 種とも実在しない**ので無効化される対象は無い。
publication の固定名成果物 5 種も `output/` 配下に 0 件である。

## 変異 matrix

baseline PASSED (rc=0、failed_nodes 0)。**KILLED 5/5・SURVIVED 0・MISMATCH 0・
期待 node 完全一致** (`matching=5`)。spec sha256
`97c7a4641bbb9f4afef9565fbc7d0a820a40d0aefb6a64059d4ef6b2033e20ca`。

| ID | 変異 | 期待 node 数 |
|---|---|---:|
| M1 | 新検査の呼び出しを削除 | 7 |
| M2 | 完全一致比較を prefix 一致へ緩める | 1 |
| M3 | 宣言数検査 `!= 1` を `< 1` へ緩める | 1 |
| M4 | 照合対象を `line.strip()` にする | 1 |
| M5 | 新検査を publication root 作成の後ろへ移す | 7 |

観測 node は probe (全件 SURVIVED 登録) で集めてから本走へ登録した。
descendant は新検査が無くても親ディレクトリ不在で `PUBLICATION_ROOT_INVALID` になり
単一理由性が立たないので、受理集合縮小の証拠には既存の親を持つ sibling を使った。

## 段別成果物

- `s1-brief.md` — 段 1 brief
- `s4-adjudication.md` — 段 4 裁定 (real / refuted、plan v2、変異事前登録)

段 2 プラン・段 3 敵対相談 2 本・段 5 実装子報告・段 6 レビュー 2 本・段 6 台帳子報告は
job dir に残したもので repo へは複製していない。要点は `s4-adjudication.md` と本書に射影した。
