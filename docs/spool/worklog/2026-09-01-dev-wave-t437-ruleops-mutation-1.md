---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t437-ruleops-mutation
seq: 1
title: [T-437] 凍結済み変異 spec (M01-M12) を実走した — KILLED 9 / MISMATCH 3 / SURVIVED 0、MISMATCH は殺し手の事後保留と登録漏れに分かれた (実装面の差分なし、branch worktree-dev-wave-t437-ruleops-mutation)
---

## 本文

ユーザー裁定 (2026-08-25 /rulings 全件、択 (a)) に従い、[T-407] が 2026-08-04 に凍結した
変異 spec を書き換えずに実走した。実装面の差分はゼロで、成果物は insight と本エントリだけである。
逐語と台帳は `output/insights/2026-09-01_t437-frozen-mutation-run/` に凍結した
(`mutation-ledger.json.gz` / `attempt-ledger.json.gz`)。

**結果: KILLED 9 / MISMATCH 3 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0。**
baseline は PASSED (rc=0、失敗 node 0、32.4 秒)。**SURVIVED が 0 件なので、事前登録が突いた
12 方向のいずれにも D151 の受理集合の穴は無い。** 正例 M11 (全件非 UTF-8 でも成功する、を壊す
過剰拒否) も KILLED で、受理側の防壁も生きている。

MISMATCH 3 件はいずれも「変異が生き残った」のではなく期待集合と実測集合のずれで、
KILLED と読み替えていない (`DW-M08`)。原因は 2 種類に分かれ、どちらも変異の失敗でも
production の退行でもない。

**(a) 殺し手が事前登録の 8 日後に黙らされた (M01、M02)。** 欠落は同じ 1 node に集中する —
`test_real_checkout_independent_maximum_package_and_runner_preflight`。この node は
commit `16df3e4e3` (2026-08-12、成長比例テストの恒久保留機構を導入し 30 function を保留) で
`hold_axis=tracked_files` の growth hold に入り、専用の環境変数トークンが無い限り skip される。
事前登録は 2026-08-04 である。**流れたのは実装ではなくテストの統治層だった。** 変異注入自体は
実在する (`anchor_counts` 全件 1、`injection_diff_sha256` 12/12 相異なる)。
保留台帳は付帯損失として最大パッケージの固定サイズ検査・`MAX_CANDIDATES` 等・独立
inspect/pickaxe 証拠・45/60 秒の preflight 境界を挙げているが、本走はそこへ 1 項目を足した —
**実 checkout 規模での「非 UTF-8 blob で inventory が fail-closed へ倒れない」確認**も、
現行の既定 runner 形では誰も行っていない。合成 fixture 側は生きているので、性質そのものが
無防備になったのではなく、失われたのは実 checkout 規模での確認である。

**(b) 期待 node の登録漏れ (M02、M10)。** 期待に無い kill が出た
(`test_inventory_retains_oversize_valid_utf8_blob`、`test_git_read_closed_set_and_environment_scrub`)。
**事前登録 commit `7f767ee87` の版で当該 assert の実在を確認した** — どちらも当時から
同じ assert を持っており、当時走らせても同じ余分 kill が出た。よって drift ではなく登録漏れである。
漏れの構造は名前と性質のずれで、`test_inventory_retains_oversize_valid_utf8_blob` は名前が
「巨大な正当 UTF-8 blob の保持」を指しながら本文で件数の不変条件 (`skipped_non_utf8 == 0`) も
固定している。**期待 node を名前で選ぶと、性質でしか見つからない被覆を落とす。**
これは検出力の不足ではなく過剰であり、D151 の防壁は事前登録の見積もりより厚い。
ただし単一理由性はその分弱く、これらの node は当該変異の単独証拠には使えない。

素材: 事前登録の陳腐化は「対象コードが動いたか」だけでは測れない。本走では対象コード
(`tools/ruleops.py`) が 2026-08-10 に 2 回変更されていたが anchor 領域の外で、逐語は 12/12 無傷
だった。実際に事前登録を壊したのは、コードに触れないテスト統治の変更のほうである。

実行系の実測: 並行 wave が 20 本超動く時間帯だったため `--source-repo` に独立 clone を渡した。
wrapper receipt は `shared_snapshot_matches: true` / `teardown_completed: true` /
`terminal_ledger: true` / `failure: null` を返し、共有木観測による rc=125 は起きなかった。
12 変異 + baseline の実所要は 1 走あたり 32〜37 秒で、spec の見積り (1 走 900 秒、総計 11,700 秒) は
実測の 2 桁上だった。

裁定待ち: 凍結 spec は書き換えていない。期待集合を実測に合わせて書き換えれば事前登録は
何も拒否しない台帳になるため、是正案は裁定パッケージとして insight §6 に置き、
本エントリでは次の一手として起票するに留める。

## 次の一手差分

### 更新

- [T-437] **P2・裁定済み (2026-08-25 /rulings 全件) → 実走完了・残件あり**: 凍結 spec の
  変異 12 件は実走した (KILLED 9 / MISMATCH 3 / SURVIVED 0)。残るのは [T-407] 段 6 の
  焦点再レビュー未実施と、MISMATCH 3 件の扱いの裁定
  ({{T:mutation-prereg-vs-test-holds}}、{{T:mutation-expected-node-underregistration}} へ分離)。
  逐語は `output/insights/2026-09-01_t437-frozen-mutation-run/`
  base: 807f4643c2cce02b969612cbdd80424d2577927d5280450bcd8c03ab2c3d25f5

### 新規

- {{T:mutation-prereg-vs-test-holds}} **P2・ユーザー裁定待ち**: 凍結した変異 spec の期待 node が
  後から growth hold / flaky hold に入ると、その変異は永久に MISMATCH になる。現状これを知る
  経路は実走だけである。択 (a) 何もしない (実走時に判明すれば足りる)、(b) hold へ node を足す側で
  既存の凍結 spec を参照して警告する、(c) 変異 harness の preflight で期待 node の hold 状態を
  検査する。(b)(c) は新規 gate なので `DW-G03` の独立 2 例が要るが、**本走が観測したのは 1 例だけ**
  である。あわせて `test_real_checkout_independent_maximum_package_and_runner_preflight` の
  保留解除の是非も判断する — 保留理由は費用 (tracked file 数に比例) であって正しさではなく、
  代償には実 checkout 規模での非 UTF-8 fail-closed 検査も含まれる
- {{T:mutation-expected-node-underregistration}} **P3・ユーザー裁定待ち**: M02 / M10 の期待集合の
  登録漏れをどう扱うか。再登録して再走すれば MISMATCH は消えるが、実測に合わせて期待を書き換える
  前例を作る。凍結の趣旨を優先するなら erratum を残して現状のまま置く
