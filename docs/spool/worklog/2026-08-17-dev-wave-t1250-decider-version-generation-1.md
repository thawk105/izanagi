---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1250-decider-version-generation
seq: 1
title: 版を束縛した第 4 世代の条件契約 record を発行し、改訂手続きへ版 bump 規範を書いた (docs + 凍結記録 + テスト、branch worktree-dev-wave-t1250-decider-version-generation、変異 matrix = 6/6 KILLED)
---

## 本文

### 発効判定は 1 点だけ動いた

候補 commit 上の実測で、freeze は valid・世代は 4・`decider-version-unbound` から
`decider-version-match` へ移り、**`effective` は False のままである**。§5 の記入 vector
(9 欄中 8 欄 UNFILLED) と 12 条件の status/reason vector は wave 前と 1 つも変わっていない。
§5 の欄名 hash・§6 の集約 hash・12 条件の hash・証拠契約 hash も第 3 世代と同一で、
動いたのは `normative_body_sha256` と `protected_sha256` だけである。

### 親が段 1 brief の不変条件を実測誤りで書いた

brief は「C01〜C12 は `evaluator-exception`」と書いたが誤りで、実際は条件ごとに
4 種の理由コードが出ている。根拠に使った `python3 -m orchestrator.campaign.s8c_preregistration
check` の出力が全件を潰していた。敵対相談レンズ A が指摘し、親が機序まで実コードで特定した
({{F:cli-double-import-collapses-diagnostics}})。CLI 欠陥そのものは判定器 module 内にあり
本 wave の no-touch 対象なので、{{T:s8c-cli-diagnostics-collapse}} として起票した。

### 敵対レビューが検出力の穴を 2 件出した

- **版束縛の検査は第 4 世代の変異では証明できない。** 候補 commit は HEAD を親に持つため、
  record の bytes を変えると「同一世代の blob は履歴全体で 1 つ」の検査が先に発火し、
  版の比較へ到達する前に freeze 無効で落ちる。版比較へ実際に到達する変異は
  「判定器の定数 `DECIDER_VERSION` だけを上げる」であり、これを事前登録へ足した (M06)。
- **第 4 世代の版を現在の定数と比べる assert は、将来の正当な版 bump を機械的に塞ぐ。**
  `DECIDER_VERSION` を上げて次世代を発行する正当な改訂が起きると、不変であるべき第 4 世代が
  現在の定数と食い違って必ず赤になる。D458 が作った仕組みそのものを塞ぐ形だったので、
  第 4 世代の schema と版は歴史的事実として literal で固定し、現行 tip と現行定数の照合は
  もう 1 本のテストへ寄せた。M06 がこの検査を倒さないことが、修正が効いた実測裏付けである。

### 契約継続性の検査には単独理由性が取れない

「§6 の条件を弱め、record も整合的に作り直す」攻撃は、freeze も版束縛も候補検査も通り抜ける。
親は変異前にこの整合的な record を計算で構成し、継続性検査だけが倒れる形を確かめた。
ただし固定 HEAD の変異 harness では、record の bytes を変えた時点で履歴不変検査が同時に発火する。
この検査を**単独理由**で殺す変異は構造的に作れない。着地後の改竄に対しては
`generation-mutated` と冗長であり、非冗長な価値は「発行の時点で条件を弱めていない」ことを
恒久記録として固定する点にある。harness が到達できない層なので、証明ではなく限界として記録する。

### 変異走行は node ID の空間差で 1 度中止した

harness は runner stdout の `FAILED ` 行から node を記録するが、`xdist_group` marker の付いた
test は並列 scheduler が nodeid へ `@<group>` を足すため、その形で記録される。一方
collection 照合は `--collect-only` の素の nodeid と突き合わせる。正規化はこの接尾辞を落とさない。
そのため probe の観測値をそのまま期待 node に書くと、実在する node が「不在」と判定されて
起動前に中止される。runner argv へ `-n 0` を足して直列化し、両経路を素の nodeid へ揃えて解決した。
中止した走では変異を 1 件も実行していない。

### 版束縛が効く層と効かない層

効く: 世代 record の妥当性と活性化報告、`effective_at()` の capability 発行、
registered launch と正式 acceptance の再導出、CLI が manifest の事前登録 commit に対して行う判定。
効かない: exploratory 経路 (明示 opt-in、非 certifying)、registered admission と
acceptance receipt (現状 `certifying=False` 固定)、外部 anchor、実行 bytes の同一性、
bump 忘れの検出、import 済みコードの束縛 ([T-1251])、認証閉包への取り込み ([T-1252])。
正本 doc の「起動と受入へまだ結線されていない」という一括表現は現コードの partial wiring に対して
広すぎるが、保護 doc の別改訂になるため本世代へ混ぜず据え置いた。

### [T-324] は land 対象として stale だった

「事前登録の 3 件の改訂と同一 wave で land」は、[T-1132]/[T-1133]/[T-1134] (D438) が
第 3 世代として既に main へ着地しており充足済みである。関係 4 branch の未着地 commit は
`git cherry` で 0 件、第 2・第 3 世代の revision_reason と ancestry でも確認した。
本 wave では [T-324] に触れず、台帳 carry の整理は別 transition に残す。

### 段 8 の裁定 — 予算が実測 1 件の反映を塞いだ (ユーザー裁定待ち)

改善候補は 1 件。`DW-M08` へ「xdist group を持つ test は記録側の nodeid にだけ `@<group>` が
付き collection 照合と食い違う。runner を `-n 0` で直列化して両経路を素の nodeid へ揃える」を
足したい。本 wave が実測した罠であり、他 wave も同じ形で 1 走を失いうる。
2 行 (195 bytes) を足して `tools/check_docs.py` を走らせたところ
`L1.5 unique footprint 9741 bytes > 予算 9566 bytes` で赤になった。追加前の footprint は
9546 bytes で**残り余裕は 20 bytes** しかない (main 取り込み後に再実測した値)。
意味を保った縮約は入らない。既存文の圧縮は exact pin を壊す。`DW-S08` に従い実装せず、
**予算値の引き上げか本候補の見送りかをユーザー裁定へ返す**。編集は revert 済みで
`check_docs` は緑に戻している。

### 子の工数と実走の帰属

codex 7 子 (plan 1・consult 2・review 2・author 1・fix 1)。いずれも rc=0。
実装子と fix 子は計算環境の queue 認証エラーで pytest を実走できず、
「実装済み・未実走」と正直に申告した。実走はすべて親が行った。

## 次の一手差分

### 完了

- [T-1250] 版を束縛した第 4 世代の条件契約 record を発行し、正本 doc の改訂手続きへ
  版 bump 規範と機械検出の限界を書いた。8c の発効を止めていた本項の閂は外れたが、
  発効そのものは §5 の未記入 8 欄と 12 条件の非充足が塞いだままである。
  remaining: none
  base: 63604b218710c8df0f56cc0bd88da98ec3fd365d7ae5fe6f60a4fabb60e15583

### 新規

- {{T:s8c-cli-diagnostics-collapse}} **P2・新規**: `python3 -m
  orchestrator.campaign.s8c_preregistration check` が判定器 module を `__main__` としても
  読み込むため、評価器の返す `PredicateResult` が `isinstance` で一致せず、全 12 条件が
  `evaluator-exception` へ潰れる。安全側には倒れるが、production の入口が
  「なぜ充足しないか」を返せない (規律 3)。判定器 module の変更を伴うため
  `DECIDER_VERSION` の bump 要否の裁定を含む。
- {{T:s8c-git-timeout-recalibration}} **P3・新規**: `GIT_TIMEOUT_CAP_SECONDS` の注記が定める
  再較正条件「generation が g2 以上」は第 2 世代の時点で既に成立しており、未処理のまま
  第 4 世代へ来た。計算ノードで再較正する。cap 不足は誤受理でなく誤拒否側へ倒れる。
