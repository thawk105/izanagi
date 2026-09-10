# 段 1 brief — [T-2067] D1325「戻さない・g1 のみ」の固定

**scope.** D1313 が列挙した 5 残余のうち設計択一 2 件 (削除された earlier run を戻す authority、
g2 以降の選択・投影) を D1325 のとおり固定し、worklog の持ち越しを閉じる。
**非 scope.** 残り 3 残余 (load-only consumer への選択強制、起動証明書の実時間性、s8c 本番配線)、
g2 向けの設計・gate・拒否枝、新規の検査・台帳・一般化、non-certifying 上限の解除。

**確定済みユーザー裁定.** D1325 (2 件は「戻さない・g1 のみ」、g2 は実在してから設計) /
D1313 (選択規則の実装だけでは上限を解除しない。追加主張は (a)(b)(c) の 3 点のみ) /
D1312 (強制点は candidate と launch、loader は投影だけ) / D95 (実装面は Codex author) /
引数 (仮想リスク向けの gate・検査・台帳・一般化は scope 外。t2027 の 4 file は非接触)。

**不変条件.** (i) 上限が解除された・弱まったと読める文言を一切書かない。
(ii) 既存の受理集合と既存テストの期待値を変えない。(iii) g2 の挙動を新たに定義しない (拒否枝も含む)。
(iv) 規律 2 を緩めない。

**親の実測 (段 1 前、worktree 24014bdb2).**
1. 選択規則の実体は `orchestrator/campaign/s8b_holdout_freeze.py:1928`
   `_assert_floor_selection_identity`。namespace を `os.listdir` で列挙するので、
   削除された earlier run は構造上不可視。復元機構・削除検知機構は 0 件。
   → 「戻さない」は現状の挙動と一致し、純増は「そう固定した記録」だけ。
2. 投影 equality は `orchestrator/campaign/s8b_ratified_freeze.py:1056`
   `if resolution.generation_number == 1:`。g2 以降は黙って非検査。→ 「g1 のみ」も挙動と一致。
3. **裁定の前提に対する新事実.** 選択 identity のもう一方の強制点
   `orchestrator/campaign/s8b_ratified_freeze.py:3305` (`_launch_validate` の current 分岐) は
   `v1=ratified.document` を**世代非依存**で渡す。g2 が実在すれば g1 用規則が黙って適用される。
   選択は g2 へ伝播し投影は伝播しない非対称が現にある。
4. 編集面の重複走査 (全 worktree の未 commit + branch 差分、pathspec 限定): 実質ゼロ。
   t2027 の 4 file とは交差なし。

**(P1) 親の provisional 裁定 — 攻撃対象.**
- (P1-1) 成果物は docs のみで足り、実装面の差分はゼロでよい。コード変更は受理集合・成果物の値・
  参照のいずれも変えず、`DW-G05` の影響行を書けない。
- (P1-2) 実測 3 の非対称は real だが、閉じるには g2 の挙動を定義する必要があり D1325 が禁じる。
  `DW-G04` の発火 artifact path も書けない。よって実装せず、記録に残して裁定へ返す。
- (P1-3) 本 wave が新たに主張してよいのは D1313 の (a)(b)(c) を超えない範囲だけ。

**成果物の形.** `docs/spool/` の worklog fragment 1 本 (T-2067 の持ち越しを「設計択一 2 件は
D1325 で固定済み、残るのは 3 件」へ改める)。実測 3 を裁定へ返すなら decisions fragment は作らず
worklog の次の一手へ新項として書く。実装面差分ゼロなら変異 matrix は `DW-S04` 免除、受入全走は実走する。

**分割方針.** 段 2 plan 1 本 (codex read-only)。段 3 敵対 2 本 — レンズ A =「docs-only で本当に
固定と言えるか。書く文言が上限解除・g2 設計を含意しないか」、レンズ B =「実測 3 の非対称と、
g1 限定を名乗る他の site の見落とし。親の実測値とその一般化」。
実装子は (P1-1) が覆ったときだけ起動する (D95)。

**受入.** `tools/dev_wave_wait.py acceptance --wave t2067-d1325-g1-only
--lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease -- python3 tools/run_tests.py`
(実行場所は Pegasus runbook §7 の既定判定に従う)。

**訂正 (段 2 投入後、親の追測で判明。段 3 以降はこちらを正とする).**
- **実測 3 は誤りだった。** `orchestrator/campaign/s8b_ratified_freeze.py:3107` が
  `if ratified.generation_number != 1:` で `certificate-generation-scope`
  (「launch certificate は generation_number==1 専用」) として fail-closed で拒否しており、
  選択 identity の呼出し (3305) はその**後**にある。したがって launch 側も g1 限定であり、
  親が挙げた「選択は g2 へ伝播し投影は伝播しない非対称」は**存在しない**。
- よって「g1 のみ」の成立点は 3 つで、すべて g1 限定である:
  (i) candidate 側 = `s8b_holdout_freeze.py:2084` が `generation_number: 1` を literal で書く、
  (ii) launch 側 = `s8b_ratified_freeze.py:3107` の明示 fail-closed、
  (iii) loader 側 = `s8b_ratified_freeze.py:1056` の g1 限定投影枝。
- この訂正は (P1-1)(P1-2) を**弱めない方向**に働く。段 3 のレンズは、この訂正自体も再測せよ。

**変更面アンカー.**
- `orchestrator/campaign/s8b_holdout_freeze.py`: 53 (規則版)、1792 (namespace 列挙)、1928 (規則本体)、2053 (candidate 側呼出)
- `orchestrator/campaign/s8b_ratified_freeze.py`: 1054-1085 (g1 投影枝)、3304-3322 (launch 側呼出)
- `docs/worklog.md` の T-2067 持ち越し (entry 1118 の次の一手)
- `docs/decisions.md` D1313 / D1325 は参照のみ・追記しない
