---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t548-versioned-dep-procurement
seq: 2
---

## {{D:gflags-glog-versioned-procurement}}. gflags / glog の調達を url + pin の共通経路へ一本化し、機体固有の絶対 path を repo から消す

**決定:** 共有 `tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` (機体固有の
絶対 path) を `gflags_source_url` / `glog_source_url` へ置き換える。pin は既存の `*_expected_head` を
唯一の正本として据え置く。`tools/pegasus/fetch_third_party.py` の `fetch` / `hydrate` / `verify` は
既定で 5 source (FetchContent 3 本 + find_package 2 本) を対象にし、`verify-deps` は廃止する。
gflags / glog の列挙は FetchContent 側の `third_party_policy()` (CMake literal 同期検査つき) とは
別権威にし、url 規約 (`https://github.com/` 前置・`.git` 終端) と pin 形式 (40 hex) は同じ強さで課す。
旧 locator を読んでいた consumer (shell / PBS の job body 15 本、Python 5 本、data 1 本) は
すべて同じ wave で、hydrate 済み staging root 配下 (`<root>/gflags`、`<root>/glog`) を使う形へ付け替える。
staging root は既存の既定 (`silo_ladder_rung1.THIRD_PARTY_STAGING_RELATIVE`、repo 相対) と
既存の env seam (`IZANAGI_THIRDPARTY_SOURCE_ROOT`) で解決し、新しい env・argv・submit 入力を足さない。
凍結成果物の bytes は 1 byte も変えず、共有 policy の現行 bytes golden と silo 凍結 evidence の
`pbs_job` / `submitter` binding は D200 の先例どおり「歴史値 + 現行 bytes の明示 pin」の 2 本立てへ移す。

**理由:**

- 2026-08-16 の裁定 (択 (b)) は「versioned な共通調達経路を新設」と「機体固有 path 結合の除去を
  同じ wave で閉じる」を対にしている。段 3 の 2 レンズが独立に、「1 consumer だけ結線して残りを
  後続へ残す」案が D1737 の却下 (同じ依存を 2 経路で pin する) に当たり、裁定の「同一 wave」にも
  反すると結論した。
- 依存の identity は変更前から版で縛られていた (`submission._dependency()` は `{commit, tree}` を記録し、
  凍結 argv `REGISTERED_DEPENDENCY_BUILD_ARGV` は相対名)。機体固有だったのは locator だけで、
  置換点は「git repo をどこから得るか」の 1 点に閉じる。
- 廃止した `verify-deps` は `expected_url=None` / `allow_shallow=True` で、新 cache 経路
  (origin 照合・非 shallow) への統合は受理集合の縮小であって弱体化ではない。
- [T-2625] を通した「親が手で依存を建てて env で prefix を渡す」回避は、同裁定が択 (c) として
  却下した形そのものだった。恒久の経路へ置き換える。
- policy の bytes を変えると T-126 の series identity と campaign binding が変わる。これは D200 が
  同じ変更で受理済みの影響であり、過去の成果物は書き換えない。

**却下した選択肢:**

- opt-in の入口 (`--include-build-deps` 等) で新経路を足し旧経路を残す — D1737 の却下状態を作る。
- 別の task 別 policy file へ調達記述を置く — 凍結 policy の bytes は守れるが、gflags / glog の
  正本が 2 箇所に割れる。
- 既存 `third_party_policy()` の list へ gflags / glog を足す — 同関数は CMake の FetchContent literal
  との同期を要求し、gflags / glog は `find_package` なので ContractFailure になる。
- CCBench の `find_package` を optional にする — D1737 が却下済み。上流改変でありリンクで落ちる。
- `tools/pegasus/` 配下に共通 helper を新設して 15 本から source する — 未登録 Pegasus 実行体として
  機械防壁が拒否する (F660)。各 job body の同形 1 行で解決する。
- 凍結 evidence の binding を新しい hash へ書き換える — 歴史の改竄 (D200)。

## {{D:no-use-time-verify-source-gate}}. 依存 source の使用直前に hydrate と同等の検証を足すことは、本 wave では実装しない

**決定:** job body が gflags / glog を build する直前の検査は、変更前と同じ「HEAD 完全一致 +
`--untracked-files=all` を含む porcelain 空 + source 存在」のままとする。hydrate 時の
`_verify_source` (index の隠蔽 bit、origin、shallow、ignored artifact) と同等の検査を使用直前へ
足す案は、段 4 で一度採用 (R5) したが段 6 で訂正し、実装しない。
**hydrate 時の検証結果が job の使用時点まで保証されるとは主張しない。** これは既知の限界として記録する。

**理由:**

- 段 6 のレビューが 15 本すべてについて「変更前の検査を消していない」と判定した。同じ改変
  (`assume-unchanged` を立てた tracked 変更) は変更前も同じように見逃していた。本 wave の弱体化ではない。
- 段 4 の R5 は、出所の相談所見が原文で「現行 floor の最低線より弱くなると確認できた回帰ではない」と
  書いていたものを、親が scope 判定をせずに採ったものだった。
- 通常の調達・投入の流れで hydrate 済み tree に `assume-unchanged` を立てる経路は無い。
  ユーザーは本依頼で「仮想リスク向けの一般化・互換層の追加は scope 外」と明示し、D1736 は名指し外の
  gate・検査を足さないと定める。
- 規律 2 が禁じるのは正しさゲートを緩めることで、既存の検査は 1 つも緩めていない。

**却下した選択肢:**

- 使用直前に `_verify_source` 相当を全 15 本へ足す — 仮想リスクへの検査新設。規模も 15 本 × 契約テスト。
- silo だけ足す — 一部だけ強い検査を持つ非対称は、名乗りを実装より強く見せる。
