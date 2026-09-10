## 読んだ資料

指定された9資料はすべて読取可能で、静的に確認した。

- `s4-adjudication.md`
- `s5-author.md`
- 実装子の完了報告 `s5-author.md`
- `s5-diff.txt`
- `condition_meaning_gate.py`
- `p3_s4_loop.py`
- `test_condition_meaning_gate.py`
- `test_p3_s4_loop.py`
- `CLAUDE.md`（絶対規律2 / 3 / 7を含む）

pytest は実行していない。

## must-fix (成果物影響つき)

1. **[セッション死・救出] [テスト代表性] 保存・診断の補助失敗が、元の gate 拒否を置き換え得る。**

   `p3_s4_loop.py:423-452` は `Exception` しか捕捉しないため、環境参照、serialize、open、write、flush、fsync 中の `KeyboardInterrupt`、`SystemExit`、`GeneratorExit` 等は `p3_s4_loop.py:458` の確定済み拒否へ到達しない。また、捕捉後の `evidence_write_failures.append()` と `",".join()` は境界外なので、そこでの `MemoryError` も元の拒否を置き換える。

   同型は `condition_meaning_gate.py:1593-1617` にもある。process が既に失敗した後で `_bounded_process_argv_detail()` を無防護に呼ぶため、`shlex.join`／encode の `MemoryError` 等で、本来の `ConditionMeaningGateError` と reason code が失われる。追加テストは通常の formatter 成功しか検査していない。

   **成果物影響:** candidate が certified へ進む fail-open ではないが、通常の gate 拒否とその reason code／arm record／admission recordが生成されず、driver rcも通常の `RuntimeError` 経路から変わり、最大3 JSONの途中集合だけが残り得る。

2. **[テスト代表性] `xb` への直接書込みは、失敗すると digest 名を永久に汚染する。**

   `p3_s4_loop.py:443-449` は最終パスを `xb` で作ってから write／flush／fsyncする。容量不足や途中write、close／fsync失敗では、短い、または耐久性未確定のファイルが digest 名で残る。例外後の除去・検証はなく、同じ record の再試行は `FileExistsError` になって修復できない。親directoryのfsyncもない。

   `test_p3_s4_loop.py:328-365` の「書込不能」は、同名directoryを先に作ってopen以前に失敗させるだけで、この実装上の失敗面を通らない。さらに保存テストは `test_p3_s4_loop.py:113-172` で issuer能力もcanonical digest整合もないrecordを作り、productionの `require_condition_gate_family` をfakeへ置換している。

   **成果物影響:** `condition-gate-<arm>-<digest>.json` が名前のdigestと一致しないbytesを持ち、その後の再試行でも正しいcanonical recordへ戻らない。certified選択は増えないが、レポート等が参照する拒否証拠が破損・欠落する。

3. **[テスト代表性] argv切詰めは異なるcommandを同じ証拠へ潰せる。**

   `condition_meaning_gate.py:1562-1573` は500 bytes上限と切詰め印・元サイズを持つが、保存するのは先頭prefixだけで、全argvのdigest等はない。同じ先頭prefixと同じ総byte数を持ち、末尾だけ異なる2 commandは、rc／stderrも同じなら同一detailになる。`configure_args` は実commandへ入る一方（同ファイル `:1691-1705`）、request digestには含まれない（`:988-1002`）。そのためred arm record digest、admission digest、保存file名まで衝突し得る。

   `test_condition_meaning_gate.py:2328-2351` は末尾が失われること自体を期待しており、異なるcommandを識別できるかは検査していない。

   **成果物影響:** 実際には異なるargvで落ちた2試行が同じcanonical red record／digestとして扱われ、2回目は `xb` の衝突により保存されない。「どのcommandが落ちたか」を証拠から復元できない。

## real だが scope 外

- generic CLI の `--configure-arg` は任意文字列を許し、失敗時には `_run_process` のargv detailを経てCLI stderrやred recordへ入る。したがってsecretをargvへ渡す利用では値が露出する。P3 S4の投影されたcallerが渡すのはdependency／FetchContentの絶対pathで、具体的なsecret源は見つからなかった。
  **成果物影響:** generic CLIのred canonical bytesとstderrにargv値が現れるが、P3 S4の受理集合は変わらない。

- `p3_s4_loop.py` のbytes変更によりB-4 projection closureの参照hashが変わる。これは親裁定どおり次回起動時のlive hash宣言で扱う事項。
  **成果物影響:** 古いhashを宣言した次回B-4起動は拒否されるが、現行condition gateの `admitted` 集合は変わらない。

## refuted (実装が正しい点)

- **green経路は不変。** `_run_process` の成功時は従来同様、同じlist(argv)を同じkwargsで `subprocess.run` へ渡し、同じ `CompletedProcess` を返す。argv整形は呼ばれない。`_require_condition_gate` の追加コードはすべて `if not admission.admitted` 内で、green時は環境変数参照、Path生成、file作成、追加statがない。戻りdict、arm canonical bytes、admission canonical bytes、rcに差はない。

- **通常入力で受理集合は不変。** reason code語彙、terminal status生成、`require_condition_gate_family`、`admitted = supply_green and meaning_not_red`（`condition_meaning_gate.py:4093-4098`）は未変更。argv追加はred evidence、record digest、admission digestを意図どおり変えるだけで、admitted判定には使われない。

- 射影された4実装・テストfileでは、変更対象だった旧process detailを完全等値比較または `match=` する既存consumerは見つからなかった。`test_condition_meaning_gate.py:598` の完全等値比較は別のCMake identityエラーで影響を受けない。

- 拒否本文の通常構築は保存より先に完了している（`p3_s4_loop.py:407-420`）。detailなしではreason codeとsorted evidence keyを出し、文字列 `"None"` は出さない。

- `test_condition_meaning_gate.py:2255-2290` は本当に `sys.executable` の実processを起動してrc=23／stderrを得ている。このテスト内では `_run_process` もsubprocessもpatchしていない。

- meaning-redのみの拒否は `test_p3_s4_loop.py:237-278` で論理的には検査され、3 recordのbytesも照合している。ただしproduction発行recordを通らない点は上のmust-fix 2のとおり。

- 追加期待値に時刻、pid、working-tree hash、固定された実環境の絶対pathはない。`sys.executable` と `tmp_path` は実行時値から期待値を組み立てているため、環境差だけでは赤にならない。

- argv上限は500 bytesで、`argv truncated`、limit、original byte数が入る。上限と切詰めの発生自体は判別可能。

- `[捏造/幻覚]` `[権限逸脱]` `[計測汚染]` に該当する差分はない。編集は許可された4 file内で、未実走を緑とも申告していない。

## nit

- `condition_meaning_gate.py:1590` で `list(argv)` がtryの外へ移ったため、独自`Sequence`のiterationが `OSError`／`SubprocessError`を送出する場合だけ、従来のstructured errorへ変換されなくなった。production callerは確認範囲ですべて通常のtuple/list[str]なので、成果物影響を示せずnit。

- **[手順漏れ]** 完了報告は `s5-author.md:50` で「追加8 nodeid」、`:57` で「追加9 nodeid」と不一致。差分上は9 test。成果物値・受理集合・参照への影響はなくnit。

## 総括

通常のgreen経路と受理集合は動いておらず、実process正例とmeaning-redの論理例もある。ただし、元の拒否を必ず送出する保証、保存artifactの完全性、切詰め後のcommand識別性に3件のmust-fixがある。現状は承認不可。静的レビューのみで、pytest緑は主張しない。