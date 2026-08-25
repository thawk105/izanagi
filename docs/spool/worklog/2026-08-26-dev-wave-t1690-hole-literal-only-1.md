---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1690-hole-literal-only
seq: 1
title: [T-1690] hole 初期化子を数値 literal 1 個へ限定し、接尾辞の二重丸めと判定順序の穴を実測で閉じた (コード + docs、branch worktree-dev-wave-t1690-hole-literal-only)
---

## 本文

- D836 (択 a) と D901 条項 1 の実装。受理文法へ `initializer-literal` と `statement-count` を
  決定順序の**末尾**へこの順で追加した。末尾に置いたのは、既存の
  `test_backoff_tier1_rejects_each_frozen_shape_with_fixed_rule` が
  `double now_backoff = 20; <禁止物>` 形 15 件の rule ID を exact に pin しており、
  前方へ置くと全件が新規則へ倒れて診断が粗くなると親が実測したため。

- **段 3 レンズが見つけ、親が実機で裏を取った穴 2 件。** どちらも literal-only を入れただけでは
  閉じない。
  1. **接尾辞の二重丸め。** Python 側の値解釈は 10 進 → binary64 → binary32 と丸め、実機 C++ は
     10 進 → binary32 と直接丸める。tie で結果が割れる。実測 (g++ 11.4.0, `-std=c++20`):
     `19.99999904632568349375f` は Python 側 20.0、実機 19.999998092651367。16 進版
     `0x1.3ffffeffffffffffp4f` も同じ。宣言値 20 のまま実効値が違う候補が通ってしまう。
     → 規則 A は接尾辞を一律に拒否する。16 進・8 進・2 進・桁区切り・指数は実機と解釈が
     一致することを実測したので拒否しない (正準化は D901 条項 3 = 別件)。
  2. **帰属検査が受理文法より先に走る。** `run_one_iteration` は preflight の直後に
     `assert_value_literal_consistent` を呼び、受理文法は `quarantine()` 内でしか走らない。
     帰属の fallback 枝を fail-closed にすると、`(20.0)` のような入力が新規則の固定 rule ID に
     到達せず未捕捉例外で campaign が落ちる。→ 全文法は帰属を実行するかだけを決め、
     rejection の選択は `quarantine()` に委ねる形にした。

- **親の裁定の実装が一度過剰になった。** 段 5 実装子は全文法の拒否を `quarantine()` より前に
  記録して return する形にし、既存の `HOLE_ESCAPE -> HOST_EFFECT -> backoff grammar` の外側順序を
  上書きしていた。段 6 のレンズ 2 本が独立に must-fix として検出。fix 後の実測で
  `double now_backoff = 20; std::system("ignored");` → `host-effect.process-shell.v1`、
  `#define EVIL 1` 入力 → `hole-escape` に戻ったことを確認した。

- **D901 条項 2 (文法版の束縛) と条項 3 (数値表記の正準化) は T-441 に残す。** 段 3 の 2 レンズは
  どちらも「本 wave に含めよ・単独で land するな」を must-fix としたが、親は scope 外と裁定した。
  根拠: (a) 依頼が「整合の確認」までであること、(b) 既存の自律 backoff campaign
  (`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387`、3 variant / 15 record) には条項 2 を
  今 land しても版が遡らないこと、(c) 本 wave は受理集合を狭めるだけで、旧文法時代の cache entry が
  新提案へ誤って再利用される経路が無いこと。**条件付きの裁定であり、条件は次の 2 つ。**
  - **C1: T-441 の条項 2 が land するまで、新しい自律 backoff campaign を走らせない。**
  - **C2: 本 wave は D836 の閉鎖であって D901 の完了ではない。**
  この判断そのものをユーザーへ裁定パッケージとして返す ({{D:hole-literal-only-scope}})。
  なお条項 3 が問題にする重複は実在する — 上記 WAL の 3 variant のうち 2 件は
  `BACKOFF_FIXED=40` が同じで `src_token` が異なる。

- **段 6 が real と判定したが scope 外へ返した所見 2 件** (裁定パッケージ)。
  - 値不一致・`implementation=None`・unpaired surrogate・`.5` の 4 経路が、構造化 rejection では
    なく未捕捉例外で落ちる。親が実読で「本 wave の変更が導入したものではない」ことを確認した。
    すべての fail-closed 経路を構造化する変更は別の変更単位。
  - dormant role policy に追加した意味検査には独立 pin が無く `POLICY_VERSION` も v1 のまま。
    adapter activation 前に裁定する。

- **producer 契約の閉包で新たに判明した機械的制約。** codex 実装子は `.codex/` 配下を
  構造的に書けない (sandbox が "writing outside of the project" として拒否する。
  子は「read-only mount」と申告したが親の実測では書き込み可能だった)。
  adapter 2 件の再描画だけ親が repository 自身の renderer 出力で行い、逸脱として記録した
  ({{F:codex-cannot-write-dot-codex}})。

- **エージェント工数。** 段 2 plan は 1 回目が既定の wall-clock 1 時間に当たって出力ゼロで落ちた
  (`failure_class=f45_missing_output`、model_calls=35)。親の実測 8 節を先渡しして再投入したところ
  10 分で完了した。段 5 実装子は `evidence_status=invalid` (既知の握り潰し例外) で
  `accepted=false` だったが、成果物は作業ツリーに入っており `check_codex_output.py` rc=0 で採用した。

- **親の手順ミス 2 件。** (a) 検査の rc をパイプに通して provenance の形式違反を一度見逃した。
  (b) 変異走行中に main を merge して HEAD を動かし、harness を fail-closed で止めた。
  どちらも未共有 commit の作り直しと再走で回復した。

## 次の一手差分

### 完了

- [T-1690] hole 初期化子を「接尾辞なしの数値 literal 1 個」へ限定し、hole を 1 文に限った。
  受理文法・帰属検査・producer 契約 (spec / leakproof context / role 2 件 / manifest /
  review ledger の pin / adapter 2 件 / critic の固定ヒント / dormant role policy) を
  同じ変更単位で整合させた。D901 条項 2・3 と T-1069 は scope 外で T-441 に残る。
  remaining: none
  base: d05fd498a3c225865efdadc22ae81b4de75d29db635868657dff2e2ea3c824b9

### 更新

- [T-441] **P2・Tier 1 と D836 / D901 条項 1 は実装済み → 条項 2・3 が未実装**: 受理文法は
  Tier 1 に加えて `initializer-literal` (接尾辞なしの数値 literal 1 個) と `statement-count`
  (ちょうど 1 文) を実装して land した。**残るのは D901 の条項 2 (文法版を identity / WAL /
  cache へ束縛) と条項 3 (数値表記の正準化) の 2 件。**
  条項 2 が land するまで新しい自律 backoff campaign を走らせない (T-1690 の条件 C1)。
  一次資料 = `output/insights/2026-08-25_t441-backoff-hole-grammar/` と
  `output/insights/2026-08-26_t1690-hole-literal-only/`
  base: ed2660fd987bf28e89a6ac703013d3f129677cf2e34fca9e8965321586e17761
