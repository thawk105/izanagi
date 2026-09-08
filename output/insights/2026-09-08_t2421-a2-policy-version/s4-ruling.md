# 段 4 裁定 — [T-2421] A-2 consumer の policy 版選択

基準 main: wave 開始時 `cc9bba523`。段 4 直前の再走査で main は `9fbb24290` へ進行 (4 commit)。
差分は docs のみ (`docs/worklog.md`、`docs/failures.md`、`docs/archive/`、`docs/spool/FOLDED.md`) で
本 wave の編集面・待ち手・launcher・runner の bytes に触れないため、取り込みは受入時の
post-claim merge に回す。裁定 inbox (`docs/handoff/`、`docs/spool/decisions/`) に本件の新規はない。

## 所見の裁定

### 採用 (blocker)

**[B-1] 旧世代の key 集合を差分で定義してはならない。real / 採用。**
プランの `POLICY_GENERATION_PRE_FETCHCONTENT_PATHS: (_TRACE0_CONFIGURE_ARGV_KEYS - {...})` は、
次に必須 key が足された時点で旧世代にもその key が混入し、**同じ再発を起こす**。
両世代とも独立した `frozenset` literal として凍結し、旧世代の定義が現行定数を参照しない形にする。
これは本 wave で最も重要な修正である。

**[A-1] / [B-4] 公開 `load_policy` に caller 選択の世代引数を足してはならない。real / 採用。**
足すと `load_policy(path, generation=...)` で、現行が拒否する 6-key policy 一般が受理される。
これは私自身が brief に書いた不変条件「受理集合を 1 件も増やさない」と正面衝突し、絶対規律 2 に触れる。
**`load_policy` の署名と受理集合は 1 byte も変えない。** 文法定数を受け取る共有本体を private 化し、
歴史読みは consumer 専用の private entry point から呼ぶ。

**[A-2] 歴史 Policy が producer の認証・実行経路へ流れてはならない。real / 機構部分は [A-1] の修正で閉じる。**
`collect_results` (P:2766-2773) と `_exact_trace0_configure_argv` (P:2193-2196) は世代を区別しない。
[A-1] の修正で歴史 Policy を得られる経路が plot consumer 1 本だけになるため、構造的に到達不能になる。
**却下する部分:** `Policy` dataclass への世代 field 追加 (frozen dataclass で、job-contract fixture の
`dataclasses.replace` へ波及する) と、preregister / 実行 / collect / materialize 入口への
current-only 強制 gate。後者は**どのコードも通らない経路への新設 gate**であり、ユーザーが scope 外と
명示した「仮想リスク向けの gate」に当たる。DW-G04 の発火条件を満たす既存 artifact path も書けない。
**代わりに限界を成果物へ明記する。**

### 採用 (must-fix)

**[A-6] 実 t2364 成果物での統合テスト。real / 採用。**
これは brief 自身が置いた完了条件である。測定 root
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b` が
**本機に実在することを親が実測で確認した** (`jobs`、`preregistration.json`、`raw-manifest.json`、
`receipts` を確認)。`expected_hashes` override なしで `load_measurements` を最後まで通す。
root 全体が不在のときだけ skip、部分欠損は failure とする。

**[B-3] canonical 成果物の閉包。採用するが、追加コストゼロの形に落とす。**
独立した閉包テストを新設するのではなく、[A-6] の正例を `CANONICAL_SHA256` の current-full entry を
走査する形で書く。テスト本数も gate も増えず、閉包が構造的に手に入る。
must-fix からは降格し、「構成によって無償で満たす」とする。

**[A-5] 歴史側だけ後段検査を飛ばす変異が現計画では生存する。real / 採用 (1 件に限定)。**
歴史世代を選択したまま後段検査 (`source_binding_status`) を壊す負例を 1 本足し、
対応する変異 M7 を登録する。**却下:** 後段検査 1 つずつに負例を足す案は本題を超える。

**[A-4] 世代 id の型検査。real / 一行だけ採用。**
lookup 前に `type(generation) is str` を要求する。これは本 file 全体が使っている exact-type の作法と
同じであり、新しい種類の検査ではない。負例は未知文字列と非 str の 2 件。
**却下:** 登録文字列へ擬態する hashable object の専用テストは仮想リスクであり作らない。

**[A-3] `override` による pin 表迂回。部分採用。**
`override` を production から外す案は**却下** — 既存の test 用機構であり本題を超える。
「override なしの実成果物テスト」の部分だけ採用し、[A-6] へ統合する。

**[B-7] ユーザー明示要求の文言。real / 採用。**
「過去成果物を読めるようにすることは、当時の測定を現行の正しさ主張へ昇格させることではない」を
`output/insights/2026-09-08_t2421-a2-policy-version/README.md` と decisions fragment の両方へ
逐語で書く。親が段 7 で行い、完了検査で両方を検索して確認する。

### real だが実装しない (限界として明記する)

**[B-2] 世代選択は configure key 集合しか覆っていない。real / 実装しない。**
`schema_version`、top-level key 集合、各値制約、`_protocol_preimage` は全世代共有のままなので、
次の締め付けがそれらに及べば**世代を正しく選べても t2364 は読めなくなる**。
世代ごとの完全な grammar contract を作る案は、ユーザーが scope 外と明示した一般化に当たり、
DW-G04 の発火条件 (該当する既存 artifact path または計測 ID) を書けない。
**したがって「再発を無くした」と主張してはならない。** 覆う次元と覆わない次元を成果物へ明記し、
裁定パッケージ候補として返す。

### nit (採用)

**[B-5] 親 brief の anchor 3 件がずれていた。** 正しくは `_historical_policy_view` = C:194-252、
`_load_current_policy` = C:255-307、`_expected_hashes` = C:125-144。

**[B-6] 既存 test 名を維持する。** `docs/failures.md:23024-23025` が
`test_historical_rejects_changed_certification_bytes` を再発検知先として参照しているので、
この名前は**改名せず本体だけ強化する**。`test_historical_exact_hash_pair_uses_the_historical_policy_view`
も維持する。他の test を改名する場合は、実装子が事前に `docs/` を grep して参照がないことを確かめる。

### 親 brief の訂正

- 事実 1 の表現を訂正する。`policy_bytes_base64` を**読む**箇所は producer 側 (P:4475-4483 の
  同一走行内の一致検査) にもある。正しくは「保存された policy bytes を **policy として parse する**
  production consumer が C:255-307 の 1 箇所だけ」である。
- (P1-a) は**現行実装の受理集合**については両レンズとも支持した。ただし「欠陥は正しさではなく
  再利用性だけ」という一般化を**設計へ持ち込んではならない** — 持ち込んだ結果が [A-1] である。

## プラン v2 (確定)

1. **P: 世代定数を 2 つの独立 literal で置く。**
   `POLICY_GENERATION_CURRENT` と `POLICY_GENERATION_PRE_FETCHCONTENT_PATHS`。
   key 集合表の値は**両方とも独立した `frozenset` literal**とし、旧世代は現行定数を参照しない。
2. **P: `load_policy(path=POLICY_PATH)` の署名・受理集合は変更しない。**
   文法定数を引数で受ける private な共有本体へ切り出し、`load_policy` は現行世代を渡すだけにする。
3. **P: 歴史読み専用の private entry point を足す。**
   世代 id を受け、`type(generation) is str` と登録済み世代であることを fail-closed で検査する。
   未知値・非 str は `CertificationError` で拒否し、現行への fallback を作らない。
4. **C: `HISTORICAL_CURRENT_POLICY_VIEWS` を、値が世代 id だけの表へ置換する。**
   主 key は D1754 のまま `(cert sha256, policy sha256)`。`source_commit` を第三の key にしない。
5. **C: `_historical_policy_view` を全削除し、歴史側も producer の完全な文法を通す。**
   重複していた `protocol_schema` / `protocol_sha256` の assert は C:291-294 が同値に覆うので削除する。
6. **T: 既存の歴史テスト群を世代表へ移行する。** 名前は [B-6] の裁定に従う。
   `observe(path)` は `observe(path, **kwargs)` にする。
7. **T: 正例を `CANONICAL_SHA256` の current-full 走査として書き、実 t2364 root で
   `load_measurements` を override なしで最後まで通す。**
8. **触らない:** producer の書き出し経路、shipped policy 2 本、`Policy` dataclass、
   `_protocol_preimage`、`CANONICAL_SHA256` の hash 値、committed figure と provenance、
   producer 内部の `load_policy` 呼び出し (世代引数を足さない — job-contract fixture の
   `load_fixture_policy(path=...)` が壊れる)。

## 変異事前登録 (実装前に確定)

| ID | 変異 | 位置 | 狙う nodeid | 期待 |
|---|---|---|---|---|
| M1 | 主 key から cert hash 成分を外す (policy hash だけで選ぶ) | C の世代 lookup | `test_historical_rejects_changed_certification_bytes` | KILLED |
| M2 | 主 key から policy hash 成分を外す (cert hash だけで選ぶ) | C の世代 lookup | policy-hash 成分の負例 | KILLED |
| M3 | consumer の世代受け渡しを消す | C の historical 分岐 | 実 t2364 正例 | KILLED |
| M4 | 旧世代の key 集合を現行と同一にする | P の世代表 | 実 t2364 正例 | KILLED |
| M5 | 未知世代を現行へ fallback させる | P の世代解決 | 未知世代の負例 | KILLED |
| M6 | 歴史世代のときだけ `tracked_destination` 検査を外す | P:398-400 | 不正 `tracked_destination` の負例 | KILLED |
| M7 | 歴史世代のときだけ `source_binding_status` の後段検査を飛ばす | C の後段照合 | 歴史側 evidence 負例 | KILLED |
| M8 | 旧世代の key 集合から別の key (`toolchain_arguments`) を落とす | P の世代表 | 実 t2364 正例 | KILLED |

**単一理由性の確認 (DW-M01)。** M1 と M2 は、既存の
`test_historical_rejects_unknown_bytes_with_the_same_v2_version` と
`test_historical_rejects_unknown_content_with_the_same_six_keys` が
**cert hash と policy hash を同時に変えていて、どちらの成分が効いたか帰属できない**ため、
成分ごとに片方だけを変える形へ置き換える。M4 と M8 は旧世代 literal を両方向から挟む。

**登録しない変異とその理由。** 「旧世代の key 集合を `現行 - {key}` の差分定義へ戻す」変異は、
現時点では**両定義が同じ値を返すので等価変異**であり、KILLED を期待できない。
差が出るのは将来 key が足された後だけである。[B-1] の修正は変異ではなく、
両世代の key 集合を literal で exact に検査するテストと、この記述で担保する。
**これを「変異で守られている」と報告してはならない。**

## 実装単位と分割

実装単位は 1 つ (P の世代化 + C の選択 + T)。所有 path:
`orchestrator/campaign/paper_story_a2_certification.py`、`tools/plotting/plot_a2_certification.py`、
`orchestrator/tests/test_plot_a2_certification.py`。Codex author 1 本、workspace-write。
docs 編集と commit は行わせない。新規 test file を作らせない。
