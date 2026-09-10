## 親の事実認識の裏取り

- **確認 — 5 session の不在。** 5 ID を現在の `/home/SFC/tanab/.codex/sessions` で個別検索し、すべて 0 件だった。`2026/07/29` directory も存在しない。

- **一部反証 — session store の exact 件数。** 現在は **7169 件**であり、親資料の 7136 件から増えている。最古 file の mtime は **2026-08-01 08:45:32 JST**なので最古日・時刻は確認した。filename 内時刻は 08:29:21。動く store のため、7136 という過去時点の値自体は反証できない。

- **一部確認 — pin の世代。** POS の固定 path は明示的に 2026-07-29。残り4件も同じ legacy benchmark に束縛されているが、元 file が無いため各 session の生成日時までは独立に再検証できない。

- **確認 — repo 内の写しなし。** 現 worktree の `output` 配下で `rollout-*.jsonl*` は 0 件。

- **確認 — skip 述語が粗い。** [test_codex_reasoning_ab.py:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_codex_reasoning_ab.py:787) は根 directory の `is_dir()` しか見ず、直後に POS/NEG の session 解決へ進む。現在は根だけ存在するため skip しない。

- **部分反証 — 「5 node が `_REAL_ROLLOUT` を直接読む」。** ガード無しの host 依存 node が5件ある点は正しい。しかし直接 `_REAL_ROLLOUT` を使うのは、3 parameter node と collector golden 1 nodeの **4 node**。[test_m2_production_golden_requires_both_routes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_codex_reasoning_ab.py:3119) は `_HISTORICAL_SESSIONS` を渡して間接的に session を解決する5件目である。

pytest は実走していない。21 errors・5 failed という実行結果自体は親資料による。

## 既裁定

主題語として `codex_reasoning_ab`、`rollout`、`session`、`host`、`skip`、`環境条件`、`恒真`、`golden`、`凍結`、`消える根` を検索し、該当節を読んだ。

最大の所見は、親資料が **D315を引いていないこと**である。

- **[D315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:14373)**: まさに同じ `tools/codex_reasoning_ab.py` の5 session 解決を扱い、「同一性の錨は `ROLLOUT_SHA256`」「5呼出は SHA 検証する」「`~/.codex/sessions` の比例走査は残す」と裁定している。歴史 test を単に撤去する案、別 session へ pin を張り替える案とは強く抵触する。

- **[D314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:14356)、[D700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:27653)、[D701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:27682)**: skip・opt-in へ外すなら、解除先が実際に到達可能であることが必要。「既定で走らず解除しても走らない」テストや、長期間走らないテストが腐ることを既に問題化している。したがって正確な skip は緊急隔離には使えるが、恒久完了とするのは抵触する。

- **[D1154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:38682)**: 環境の偶然の件数を静的に pin する gate を禁止。本件でも session store 全体の件数や根の存在を availability の代理にしてはならない。

- **[D1192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:39778)、[D1322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:42428)**: 消える job-local root の絶対 path を保存して後で壊れる問題に対し、根分類と根相対 pathへの変更を採用。完全同型ではないが、絶対 path を永続的な参照にしない方針を支持する近接先例。

- **[D1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:40192)**: 族一般化には独立2例が必要。2例があっても機械的禁止は自動承認されない。

- **[D1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:40862)、[D1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:41469)**: 歴史記録と現行認証を分け、再現不能を理由に歴史 pin を更新しない。失われた rollout の hashを新しい session へ差し替える案は不可。

- **[D1162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/docs/decisions.md:38820)**: 救出物の真に独立した二次保管先はユーザーが指定する。今後 raw rollout を保全するならこの境界が効く。

## 再発判定

`docs/failures.md` は必読射影に含まれていないため、単独段 dispatch の制約上、独立検索できなかった。したがってF番号は責任を持って引けない。

親の「同型 F 不在」は、親資料に書かれた検索結果としては読めたが、**独立には未確認**であり、正しいとも誤りとも判定できない。

ただし decisions には D1192/D1322 の「消える外部 rootを絶対 pathで保持して後から検査が壊れる」という近接事例がある。そこから参照される F151 は「別経路を同一障害として誤って束ねる」再発防止であり、今回の消失自体と同型のFだとは断定できない。

## いつから赤か

確認できる時間窓は次のとおり。

- pin と fixture は commit `d07142be55`、**2026-07-30**に導入された。
- D315 は **2026-08-12**に実 corpus 2799件を使って5 session 解決を実測している。
- D585 は **2026-08-20**に `benchmark_snapshots` を使う単一 node を実際に構築したと記録する。少なくともこの時点では必要 rollout が存在した。
- 現在は最古が2026-08-01で、5 session は消失済み。親の全走赤は2026-09-01までに発生している。

したがって赤化は **2026-08-20より後、2026-09-01まで**。気づかれずに居座った期間の上限は約12日である。約31日の rolling retention なら7月29世代が8月29日前後に消えた可能性が高いが、削除履歴を確認できていないため推測に留める。

`docs/worklog.md` も射影外なので、直近の受入全走記録と「最後に全走を通した wave」は未確認。D585は単一 node の実走であり、受入全走の緑とは扱っていない。

## 族かどうか

射影された2コードファイル内の検索結果は3箇所だった。

- [test_codex_reasoning_ab.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_codex_reasoning_ab.py:128): `/home/SFC/tanab/.codex/sessions` を実際に filesystem root として読む。本件。
- [codex_reasoning_ab.py:12091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/tools/codex_reasoning_ab.py:12091): CLI の既定を `CODEX_HOME/sessions` または `~/.codex/sessions` とする。外部 store 依存だが設定可能であり、固定 historical pin の別例ではない。
- [codex_reasoning_ab.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/tools/codex_reasoning_ab.py:190): 旧 worktree の絶対 path。ただし prompt 内文字列の置換対象で、filesystem 参照ではない。

同じ成果物への2表現を除けば、**独立した欠陥例は1件だけ**。射影範囲では族一般化の独立2例は成立しない。repo 全域検索は射影制約により未確認なので、現時点では局所修復として扱うべきである。

横断 docs 規律との関係では、test code は横断 docs そのものではないため形式的な直接違反ではない。しかし特定ユーザーの home を受入条件にする点は同じマシン密結合である。文書には symbolic な session root と可用性条件だけを書き、`/home/SFC/tanab` を規範値として昇格させるべきではない。`OLD_ROOT` のように「歴史入力内の文字列」として一切 dereference しない literal は別扱いにできる。

## 推す案

**緊急対応はA、恒久対応はAでもBでもない分割案**を推す。

1. まず全 host-dependent node を共通 availability fixture へ集約する。5 ID が exact-one で解決できない「不在」だけを明示 skip にする。複数件、異なる SHA、破損 file は skip へ潰さず赤にする。これで現在の決定的 setup error は隔離できる。

2. skip は「受入緑」ではなく「歴史証拠 unavailable」と集計する。D314/D700に従い、到達可能な実行先が無い状態を恒久完成とは呼ばない。

3. D315 の session ID・SHA pin は歴史記録として残し、新しい session へ張り替えない。歴史 bytes が失われた事実も残す。

4. 挙動検査は repo 内の小さい合成 rollout fixtureへ移す。これは歴史的 SHA の代替証拠ではなく、parser・prompt変換・snapshot機構の回帰検査専用とする。歴史由来の検査と機構検査を分離する。

5. raw rollout の backup が発見された場合だけ、ユーザー指定の独立保管先と digest manifestで歴史検証経路を復旧する。現状の bytes から再生成できたとは主張しない。

Bの全面撤去はD315/D1285と最も強く衝突し、検出力も失うため推さない。

## 総括

- 親の核となる原因認識は正しいが、「5 node が直接 `_REAL_ROLLOUT`」は4直接＋1間接が正確。
- 最大の見落としは、同じ5 session と SHA pin を直接裁定したD315を引いていないこと。
- pin は8月20日には利用可能で、赤化はその後9月1日まで。全走の最終成功日は未確認。
- exact skip は緊急隔離として妥当だが、恒久的な「緑」にしてはいけない。
- 歴史 pinを保存し、機構検査をrepo内合成fixtureへ分離する案が既裁定との整合性が最も高い。
- failures・worklog・repo全域の族検索は射影不足により未確認であり、F不在と独立2例不在は確定していない。