## 所見対応表

以下は静的判定です。pytest・変異実走は行っていません。`partial` には、現状維持された nit と、射影内では文書修正まで確認できない項目を含めます。

参照略号：

- P＝[tools/codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py)
- T＝[test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py)
- C＝[conftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/conftest.py)
- G＝[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_real_repo_serialization.py)
- R＝[stage4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1706-schedule-bytes-toctou/dev-wave-job-t1706/stage4-ruling.md)

| 所見 | closed / partial / regressed | 根拠 (file:line) | 残余 |
|---|---|---|---|
| 段3 A-1：固定入力と時間変化の区別 | closed | T:2103、P:8976。観測契約の変更を明記し、取得済み bytes を解析する。 | worklog への記載は射影外で未確認。 |
| 段3 A-2：source authority による frozen 観測消失 | closed | P:7634、P:7639、P:7640、P:7641。両枝とも frozen の取得値が SHA・解析入力。 | — |
| 段3 A-3：live consumer 不在の母集合 | partial | R:15 に限定記述の採用はあるが、元の brief の修正文は射影にない。 | 元文書の限定記述を独立確認できない。 |
| 段3 A-4：validator 参照数からの全数性主張 | partial | P:7649、P:11180、P:11746 の直接呼出しは確認。R:15 の文書措置の履行は未確認。 | この3呼出しから外部・動的 consumer 不在は導けない。 |
| 段3 A-5：frozen 観測維持を scope 外にしない | closed | P:7634、P:7639 に frozen の読取りが実装されている。 | — |
| 段3 B-1：helper 内再読を撃てない | closed | T:1958、T:1960、T:2145、P:9064。helper 内の追加 read も計数対象。 | SHA直後という時点指定との差は段6 A-1に残す。 |
| 段3 B-2：replay 後段 SHA 再読の計数漏れ | closed | T:2075、T:2145、P:11187。`verify_manifest` 呼出し全体を囲む。 | — |
| 段3 B-3：発火と拒否理由の帰属 | closed | T:2117、T:2118 で交換・復元各1回を要求。単一理由の証拠は T:2147 へ分離可能。 | 負例自体の拒否理由は単一になっていない。 |
| 段3 B-4：波及候補43定義の過大計上 | closed | R:20 で候補と検査数を区別。T:9503、T:10222 の validator 置換も確認。 | これらの緑を実 validator 通過の証拠には数えない。 |
| 段3 B-5：変異 kill の専属帰属 | closed | T:2145、T:2147 と下表の6経路で、指定正例内の失敗を計数に限定できる。 | suite 全体でこの正例だけが kill する、とは主張できない。 |
| 段3 B-6：certified 集計突破の断定 | partial | R:22 は未証明と限定。P:11188、P:11401 に後続 SHA 照合がある。 | 元 brief の修正は射影外で未確認。 |
| 段6 A-1：交換が SHA 算出直前 | partial | T:1965 の交換後に P:9057／P:7640 が SHA を計算する。 | 指定時点の証跡にはならない。nit 維持を覆す成果物上の反例はない。 |
| 段6 A-2：M4・M5 の単一理由性 | closed | T:2145 は replacement 無指定。P:9064／P:11187 の追加 read は同一 bytes を返し、T:2147 で失敗する。 | 負例側の過剰決定は残るが、単一理由の証拠から除外される。 |
| 段6 B-1：replay 負例の過剰決定 | closed | T:2012、T:2125 の問題は正例 T:2143 では発生しない。交換由来の mtime 変更もない。 | 負例を単一理由の変異証拠へ戻すことはできない。 |
| 段6 B-2：正例 SHA assertion の自己照合 | partial | T:2037→T:2163、T:2082→T:2167 は入力の再確認。 | 生成 receipt の SHA 検証証拠には数えられない。nit 維持を覆す影響はない。 |
| 段6 B-3：共有 fixture consumer 未登録 | closed | C:398、C:399、C:563、C:564、G:171、G:172。両関数が inventory・両 reader・独立 golden に存在する。 | access の根拠は下記。 |

## 変異再照準への攻撃

**指定した正例 node 内の単一理由性は、M1〜M6すべてで静的に成立します。** 負例を含む suite 全体の単独 kill という意味ではありません。

全行の対象は `test_schedule_authenticated_bytes_accept_static[entry]` です。

| 変異 | entry | 追加 read の経路 | T:2147 の判定 |
|---|---|---|---|
| M1 | supervisor | P:7641 の `data=` 削除 → P:8976 | frozen を2回読み、`2 != 1` |
| M2 | replay | P:11173 の `data=` 削除 → P:8976 | schedule を2回読み、`2 != 1` |
| M3 | packets | P:11738 の `data=` 削除 → P:8976 | schedule を2回読み、`2 != 1` |
| M4 | replay、または packets | P:9064 の return で再読 | schedule を2回読み、`2 != 1` |
| M5 | replay | P:11187 の SHA 入力を再読 | schedule を2回読み、`2 != 1` |
| M6 | supervisor | P:7640 の SHA 入力を再読 | frozen を2回読み、`2 != 1` |

M4を supervisor の正例へ割り当てると発火しません。supervisor は姉妹 helper を使わないためです（P:7634、P:7639）。**M4の登録先は replay または packets に限定する必要があります。**

副作用については次のように判断しました。

- **wrapper・mtime：** 正例は replacement が `None`（T:2145）。T:1965 の書込み、T:1968 と T:1987 の復元がすべて無効になり、追加 read による mtime 変更はありません。終了時の bytes・mtime assertion（T:1992、T:1993）も追加の失敗理由になりません。
- **file descriptor・atime：** T:1958 は元の `Path.read_bytes` に委譲し、descriptor を保持しません。追加の open/read/close や atime 更新はありえますが、schedule の atime・descriptor 番号を判定に使う経路はありません。replay が参照するのは mtime です（P:11399）。
- **キャッシュ：** wrapper は2回目にも実読し、保存した bytes を返すキャッシュではありません（T:1958、T:1969）。fixture の memoization は snapshot 構築用で、観測対象の呼出し前に context を抜けます（T:1703、T:1741、T:1763、T:1999）。
- **SHA・受理結果：** 追加 read が同じ bytes を返すため、P:11188 と P:11401 の照合値は変わりません。正例は invalid 化の枝にも入りません（T:2010、T:2143）。

「何も検査しなくても通る」恒真形でもありません。入口を呼ばなければ `reads=0` で T:2147 が失敗します。さらに生成 launch、replay の受理・理由なし、packet 数を要求しています（T:2152、T:2155、T:2158、T:2160、T:2165）。ただし、この正例だけで不正入力の拒否能力まで証明するものではありません。

## access 区分の独立確認

**両関数とも `parent/read・ccbench/read` が適切です。**

| 資源 | 実装から追跡したアクセス |
|---|---|
| parent/read | `benchmark_snapshots` が `_ROOT` の Git object を `show` で読む（T:889）。base 構築でも source に対する `rev-parse`・`show`・`pack-objects --stdout`・`diff` を使う（P:3294、P:3300、P:3313）。 |
| ccbench/read | base 構築から実 submodule の状態・local source を読み出す（P:3311、P:1020、P:1030）。submodule の config 更新・初期化の実行先は `snapshot_repo`（P:1048、P:1065）。 |
| 書込み先 | base・派生 snapshot は fixture の一時領域（T:864、T:914、T:915）。index-pack・checkout は base、派生コピーは snapshot に向く（P:3307、P:3310、P:3389）。 |

正負例ともこの module fixture を直接要求するため、packets の本体が軽くても両 reader が必要です（T:2100、T:2139）。

登録値は C:620 で両 read に変換され、G:307・G:312 の独立 golden も同じ区分になります。ロックはテスト本体だけでなく setup/call/teardown を囲むので、fixture 初回構築も区間内です（C:2208、C:2223）。

## 新規に見つけた所見

新規 must-fix はありません。M4の入口指定上の制約は上記の変異登録条件です。

## 総括

closed でない項目は **5件**：文書修正未確認3件、現状維持の nit 2件。regressed は0件です。

M1〜M6の正例への再照準と、両 fixture consumer の access 区分は静的に妥当です。

残る最大のリスクは、入力の自己照合である T:2163・T:2167 を、生成 receipt の SHA 検証証拠として過大計上することです。実測結果の独立再検証はしていません。