## 実装した内容

1. v2-1: [_CarrySource と occurrence streaming](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:1059)を導入し、404,326件を保持せず逐次検査する構造へ変更しました。

2. v2-2: [digest対の既知違反台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:254)へ確定4件だけを登録し、総数を4に固定しました。

3. v2-3: [carry candidate検出](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:1936)を追加しました。不正3形を拒否し、実コーパスの通常括弧文や「前エントリ参照」は候補から除外します。

4. v2-4: [_validate_entry_universe](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:2177)で candidate数とparse数、universeとindexの集合一致、母数下限404,326を検査します。

5. v2-5: 同validatorで索引key不在、値None、空集合を別分類にしました。

6. v2-6: [分類別sample上限](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/tools/check_docs.py:2161)を20件とし、抑止件数を併記しながら全件の数え上げを継続します。

7. v2-7: 新規不一致へsource path:line、task ID、target、target H2所在、修正指針を追加しました。既知occurrence消失には凍結archiveを編集しない復旧指針を出します。

8. v2-8: [fold形carry鎖の焦点テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11095)を追加しました。

9. v2-9: [最悪赤経路のbounded fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11128)を用意しました。wall/maxrss計測は裁定どおり親の担当で、今回は測定していません。

10. v2-10: [確定4件を再現する合成archive](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:421)と、新規13 test functionを追加しました。許可された[current正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11161)・[採番archive正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11208)はassertionを変えず同一ID fixtureへ補正しました。

## 現行の受理・拒否挙動

受理するもの:

- `[T-1219] (953)`と正規legacy形で、参照先の次の一手に同じIDがあるcarry
- digest台帳に一致する確定4 occurrence
- carryではないprose
- 非採番archive内のcarry
- foldが生成する同一ID carry鎖

拒否するもの:

- 実在targetに別IDしかない新規carry
- 宙吊りtarget
- `(073)`、`(73 )`、`変わらず ( (73) 参照)`などの不正文法
- universe/index不一致と、索引key不在・None・空集合
- 台帳総数逸脱、登録occurrence消失・重複
- parse母数404,326未満

## 実走した検査

- `python3 tools/check_docs.py`: 実repo全域、最終rc=0、`check_docs: 違反なし`。
- `git diff --check -- tools/check_docs.py orchestrator/tests/test_check_docs.py`: rc=0。
- backlog/archiveの引数なし56 test function: manual diagnosticで56/56 pass。
- carryのparametrized入力12件とdirect validator入力7件: manual diagnosticで19/19 pass。
- `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py --collect-only -q`: rc=16。計算ノードpreflight失敗でpytest子は未起動です。
- したがって実走済みpytest nodeidはありません。全pytest nodeidは実装済み・未実走であり、pytest緑は主張しません。

runnerが生成した一時receiptディレクトリはexact pathを確認後に除去済みです。

## 期待どおり赤になる finding 集合

親docs未land状態の実repoについて、事前指定したfinding集合は空集合です。確定4件は台帳で受理され、非採番archive1件はscope外です。最終実走も空集合でした。

負例fixtureで期待する集合は次です。

- 新規同一ID不一致
- carry candidateとparse数の不一致
- 台帳総数・観測数不一致
- 母数下限割れ
- universe/index不一致
- 索引key不在・None・空集合
- 宙吊り参照

途中実走で出たcandidate過包含は回帰として扱い、述語を補正しました。最終実走には残っていません。

## 波及可能性の静的列挙

- 所有外caller: `_main`から`_check_backlog_guard`を経由する全check_docs利用者。
- producer: `tools/spool_fold.py`が生成するcarry形。編集・統合実走はしていません。
- 共有fixture: `_build_min_repo`、`_archive_readme`、`_write_archive_index`、`_load_fixture_checker`、`_run_check`。
- consumer test: backlog/archive族、`test_real_repo_clean`、`test_spool_fold_rotation_output_passes_real_check_docs`。
- plain `_run`もtest function集合を列挙するため波及対象ですが、pytest fixture注入の代替にはなりません。
- repo全域検索は禁止されていたため、列挙は射影された2ファイルと親資料が明記したconsumerに限定しています。

## 未完・未実装

実装できなかったv2項目はなし。

未完の検証は、pytest nodeid実走とv2-9のwall/maxrss測定です。親による全走・性能測定までは未完了扱いです。commit、git add、docs編集は行っていません。

## 総括

v2-1からv2-10を指定された2ファイルだけへ実装しました。  
実repo checkerは最終rc=0で、確定4件以外の新規findingはありません。  
manual diagnosticは75入力で通過しましたが、pytest子はrc=16で起動できていません。  
親のpytest全走と性能測定を残しており、closedとは申告しません。