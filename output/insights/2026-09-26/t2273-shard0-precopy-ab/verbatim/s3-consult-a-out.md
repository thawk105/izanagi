## 所見

- **A1｜must-fix** — (P1) の原因帰属は一次資料に反する。第 4 回 README 結論 8 は pre 128.8〜130.2 秒の原因を「未分解」とし、plugin、資源標本、node・Lustre 状態を候補に挙げる。T-2243 の温 18.4／冷 84.6 秒は独立 process の collection で、受入の plugin・xdist・prewarm を含まない（同 README §8）。**放置すると温め後の pre と効果量を実受入へ過信する。** 「bytecode が原因」を仮説へ下げ、pre と各補助処理の時刻を記録する。

- **A2｜should** — login の collect-only は pyc を用意しうるが、実受入の「compute shard と並行する login collection」を再現しない（`tools/run_tests.py:1402–1455, 2344–2351`）。replica は `PYTHONDONTWRITEBYTECODE=1` を設定し、login 側 collection 自体も走らない（probe-source `:537–560, :641–656`）。plugin import、xdist、早期 memo の費用も温まるとは限らない。**放置すると pre が 55〜80 秒に入っても同条件だと誤認する。** 温め対象と未再現の並行処理を明記し、A の pre は有効性とは別の外挿条件として扱う。pyc は通常 Git ignored なので clean 判定と test の受理集合は原則変えないが、温め前後の HEAD・status・nodeid 集合を確認する。

- **A3｜must-fix** — (P2) の controller thread が worker の共有置き場へ書くなら、寿命の所有者が足りない。`_T080SharedBases` は worker が共有 lock を保持し、最後の worker が木を削除する（`test_s8b_oracle_driver.py:920–942, 974–992`）。controller が lock に参加しないまま生成中または待機中に worker が終了すると、写しが消えうる。**放置すると P の失敗や待ち時間を候補 (a) の性質と取り違える。** controller も同じ lifetime lock を保持して終了時に解放するか、snapshot を別の session 所有 dir に置き、終了時の join・削除を定義する。identity は `json.dumps([str(ROOT), testrunuid])` の SHA-256 を厳密に共用する（`:980–984`）。

- **A4｜should** — controller thread の開始時点は早期 memo と揃うが、Python での約 3 万 path の列挙・copytree は GIL と xdist controller loop を取り合う。既存 memo thread と同時に走る条件も、collection で memo が実際に選択された場合に限る（`conftest.py:2368–2385, 2583–2614`）。replica の shard spec は設定される（probe-source `:641–646`）ため発火条件の一部は満たすが、全条件成立と実際の発火はログで確認が必要。**放置すると短縮・悪化のどちらも写しの IO 効果へ誤帰属する。** controller の開始・終了、collection 完了、memo 発火・所要、最初の builder 開始を両腕で記録する。source_root が ROOT の全 builder に差し替える点は、非共有 builder 1 本にも効く自然な形である（第 4 回 README 結論 2・4）。

- **A5｜must-fix** — A の実関数が返す `visible_output` は除外対象も含む集合で、P の builder は実関数を呼ばない（`test_s8b_oracle_driver.py:847–899, 1458`）。builder の既存 span だけでは「各 builder の複製結果が同一」を検査できない。**放置すると欠落や古い snapshot を有効対として採用しうる。** A・P 各 builder の完成直後、後続の削除・Git 操作より前に、`root/output` の相対 path・file bytes・mode・mtime の digest と件数を同じ方法で採る。可視集合の digest は snapshot 生成時の実関数の戻り値として別に記録する。`copytree` の copy2 は metadata を引き継ぎ、mode は Git と実行可否、mtime は metadata snapshot 検査に影響しうる（`:1810–1814`、前回 README §4 M4）。

- **A6｜must-fix** — (P2') の「P の memo 待ち超過は P の失敗」は因果帰属として強すぎる。前回は A と B の両方で超過し、原因は未分解と記録された（前回 README §5、§7）。超過は 120 秒の共通待ちで、node・Lustre の時間変動でも起こる（`conftest.py:2469–2485`）。**放置すると偶然 P で起きた infra 失敗が (a) 不採用の根拠になる。** 超過は条件別件数を残して対の有効性から外し、P 固有の干渉と述べるのは memo 時間・資源標本・反復で裏付けられた場合に限る。

- **A7｜should** — 3 対・順序 A,P／P,A／A,P と逐次 job は D357 に沿うが、「1 対でも Δ≤0 なら効果が乏しい」は不確実性と効果ゼロを混同する。各 job の後走は page cache・Lustre client cache の利を受けうるため、今回の順序では P が後走 2 回、A が後走 1 回で P に有利な残差もある（第 4 回 README §4）。**放置すると境界付近で推奨が順序や偶然に左右される。** 事前登録の閾値は維持しつつ、未達の表現を「この基準では確認できない」とし、順序別対差、pre、写しの費用、W₀ と 300 秒の関係を併記する。

- **A8｜should** — (P4) は子の `-I -B -c`、`_CurrentSourceLoader`、`sys.path`・closure 検査を保って実現できるが、child の code 文字列へ計器を注入するなら `subprocess.run` へ渡す引数は同一ではない（`test_s8b_oracle_driver.py:1564–1715`）。**放置すると DW-O14 の「同じ引数を 1 回渡す観測」と誤表示し、計器費用も内訳に混ざる。** 両腕同じ child code に最小限の時刻・CPU 計器を埋め、結果は stderr の識別行へ出す。元の import、loader、`sys.path` 検査と stdout の document JSON を保ち、これは「対称な計測用 code 変換」と明記する。

- **A9｜nit** — brief の主要な file:line（`conftest.py:2583, :2388`、test file `:847, :920, :974, :1437, :1458, :1564, :1712`）に誤りは見当たらない。一方、P1 の「実受入 59〜66 秒」は直近の 3 対では **64.3〜65.9 秒**、第 4 回 pre 倍増の原因は未確定である（前回 README §5、第 4 回 README 結論 8）。**放置すると異なる標本を一つの基準域として一般化する。** 標本ごとの範囲と出典に書き分ける。

## brief への異議

| 項目 | 判定 | 必要な変更 |
|---|---|---|
| (P1) | **修正** | bytecode 原因説を仮説に下げ、温めても再現しない処理と外挿の限界を明記する。 |
| (P2) | **修正** | controller の寿命 lock・identity・失敗処理を定義し、全 builder の結果を観測する。 |
| (P2') | **撤回** | P での memo 超過を自動的に P の因果的失敗と数えない。 |
| (P3) | **修正** | 順序と閾値は維持できるが、未達を「効果なし」と断定しない。 |
| (P4) | **修正** | child 計器を両腕対称に入れ、同一引数の観測 wrapper とは呼ばない。 |

## 総括

**修正後 GO。** 前倒しの写しを repo 外の隣接対で測る方向は D2243 項 2 に合う。
現 brief のままでは、controller の写しの寿命、有効性検査、memo 超過の帰属が判定を歪めうる。
pre の温めは比較条件を近づける試みとして扱い、実受入の再現や倍増原因の確定とは書かない。