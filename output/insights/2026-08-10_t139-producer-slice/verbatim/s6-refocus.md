## 所見対応表

| 所見 ID | 判定 | 根拠 file:line | 一言 |
|---|---|---|---|
| A2-1 | `closed` | `orchestrator/preregistration/erratum.py:172-193,279-295,313-316` | `operations:` 直下の sequence のみ数え、`decoy:` 攻撃は 0 operation として拒否する。 |
| A2-2 | `closed` | `orchestrator/preregistration/erratum.py:364-375,396-401` | 空集合拒否と必須 keyword-only digest 照合は閉じた。digest の権威性は B-2 に残る。 |
| A2-3 | `closed` | `orchestrator/preregistration/addendum_envelope.py:31,83-111,121-148` | backtick/tilde fence 内の見出し・節終端を除外する。承認 blob の解釈も不変。 |
| A2-4 | `closed` | `orchestrator/preregistration/erratum.py:272-277,357-361,381-389` | validator registry に無い ID は parse 時と compose 時の二段で拒否され、検査を飛ばす経路はない。 |
| A2-5 | `partial` | mutation spec `:8-183`、`orchestrator/tests/test_t139_preregistration_binding.py:199-226,259-271` | M1′・M3a/b・M9′は clean。ただし旧 M9 の resolver fallback は空 erratum 検査へ置換されただけ。`s6-fix.md:11` の `closed` と不一致。 |
| A2-6 | `closed` | `orchestrator/tests/test_t139_preregistration_binding.py:52-55,396-403` | 404/424 行 digest は独立 literal として固定された。 |
| B-1 | `partial` | `orchestrator/preregistration/addendum_envelope.py:13-29,152-176`、test `:321-327,376-393` | exact-13 は既定値になったが、caller は任意 `expected` を明示して迂回可能。承認 blob の正例も明示 `EXPECTED_FIELDS` を渡している。`s6-fix.md:13` の `closed` と不一致。 |
| B-2 | `partial` | `orchestrator/preregistration/erratum.py:91-100,364-401`、`erratum-core-s15.md:129-155` | 引数省略は閉じたが、caller 自身が digest を供給する自己認証のまま。manifest/resolver は未実装。fix 申告と一致。 |
| B-3 | `closed` | `orchestrator/preregistration/erratum.py:298-361,381-395` | erratum 固有 validator と共通の非重複・適用処理が分離され、将来 ID は明示登録まで fail-closed。 |
| B-4 | `closed` | `orchestrator/preregistration/addendum_envelope.py:83-148` | A2-3 と同じ理由。 |
| B-5 | `partial` | `orchestrator/preregistration/blobref.py:81-115,135-166` | exact commit と regular mode は閉じたが、repo root・Git 環境・履歴安全性・blob size の水準は未達。`s6-fix.md:17` の `closed` と不一致。 |
| B-6 | `partial` | `orchestrator/tests/test_t139_preregistration_binding.py:330-338`、`orchestrator/preregistration/__init__.py:3-5` | 二つの低水準失敗は別 node になったが、resolver 自体を通らず fallback を検出できない。`s6-fix.md:18` の `closed` と不一致。 |
| B-7 | `closed` | `orchestrator/tests/test_t139_preregistration_binding.py:416-427` | 禁止 export と非 admission-gate docstring の両方を固定した。 |

## 残存・新規所見

### must-fix — exact-13 はまだ caller が上書きできる

`require_exact_fields(blob, frozenset({"a01", …, "a12"}))` は現在も正常な呼び方である（`addendum_envelope.py:152-159`）。

- 失敗シナリオ: future resolver が R12 を明示渡しし、production 既定値を使わない。
- 成果物影響: `a13` の有意水準を欠く追補が certified 系へ入る。B-1 は完全には閉じていない。

T139 の固定契約には、caller が期待集合を渡せない専用入口が必要である。

### must-fix — composed digest は実質的に自己認証できる

`expected_composed_sha256` は必須になったが、値の取得元を拘束していない。さらに mismatch 例外は actual digest を表示する（`erratum.py:96-100`）ため、誤値で一度呼び、表示された actual を再投入するだけでも通せる。

- 失敗シナリオ: caller が未承認 core/erratum の合成 digest を自分で計算または例外から取得して再実行する。
- 成果物影響: approval manifest の `composed_sha256` と無関係な合成 core が受理される。

必須引数化は「照合忘れ」を閉じただけで、B-2 の trust root を閉じていない。

### must-fix — Git 解決は hardened 実装の全水準に届いていない

commit 型と mode だけなら `trial_registry.py:692-705,755-785` と同水準で、commit identity は `s8c_preregistration.py:951-957` よりむしろ厳しい。一方で次が欠落する。

- `trial_registry.py:482-525` の Git 環境 allowlist、global config 無効化、literal pathspec、Git top-level exact 検査。
- `s8c_preregistration.py:86-104,901-928` の blob/output/input size 上限と量比例 timeout。
- `s8c_preregistration.py:938-948` の shallow・replace refs・grafts の fail-closed 検査。

現実装は `os.environ` をほぼそのまま継承する（`blobref.py:85-93`）。例えば外部 `GIT_DIR` が設定されていれば、引数の `repository_root` とは別 repository の object database を読む余地がある。

- 成果物影響: 指定 repository に属さない blob identity の受理、または巨大 blob による無制限メモリ消費。

### must-fix — resolver fallback の mutation 証明は依然存在しない

fields 節欠落と commit 不在は分離されたが、どちらも低水準関数の直接テストである。将来 resolver が `BlobResolutionError` を捕捉して R12 へ落としても、現在の二 node は緑のままである。

- 成果物影響: fail-closed を主張する mutation 証拠が、実 admission 経路の受理集合を保証しない。

### must-fix — mutation spec は M12 が過剰決定、positive が1件不足

M12 は `_require_commit_regular_blob()` 呼出し全体を外し、commit 型と blob mode を同時に緩める（mutation spec `:201-212`）。対象テストも tree と symlink を一 node に入れ、tree の `pytest.raises` が先に失敗するため symlink 検査まで到達しない（test `:351-373`）。

- 成果物影響: kill 1件で二つの防壁を検証したように過大計上される。
- 必要対応: commit 型と symlink mode を別 mutation・別 node に分離する。

## 焦点確認

### Fence と承認済み追補 A

固定 commit の blob と worktree file はともに SHA-256 `f7db96ce…cfec`。独立集計は次のとおりだった。

- `fields` 本文: 871行
- fence marker: 76行
- fence 内の `## `/`### ` 行: 0件
- 素朴な `### `: 13件
- parser 結果: `a01`〜`a13`

したがって fence 新設は承認済み追補の解釈を変えていない。意図しない受理拡大も確認できなかった。

### 未知 erratum ID

`parse_erratum()` が registry membership を要求し（`erratum.py:275-277`）、`compose_core()` も再照合する（`:381-388`）。未知 ID で validator を飛ばして通る経路は確認できない。

ただし registry allowlist を誤って拡張する変異、例えば `unknown-erratum-v1` を既存 validator へ登録する変異は spec に未登録である。既存 `test_erratum_unknown_id_is_rejected` を clean に KILL できるため、登録対象にすべきである。

## 変異 spec 検証

全14 mutationについて、全 `old` は対象 file に exact 1件、全 `expected_nodes` は実在した。以下は22 node 全体を読んだ静的 control-flow 判定であり、mutant pytest は実行していない。

| ID | old件数 / node | 単一理由帰属 | 判定 |
|---|---|---|---|
| M1-prime | 1 / 実在 | decoy subtree だけが通る。巻き添えなし | clean |
| M2 | 1 / 実在 | digest mismatch だけが通る。`old_text` は一致する | clean |
| M3a | 1 / 実在 | 3件出現の件数検査だけを外す | clean |
| M3b | 1 / 実在 | exact-2の行束縛だけを外す | clean |
| M4 | 1 / 実在 | multi-token delta だけを通す | clean |
| M5 | 1 / 実在 | composed digest mismatch だけを通す | clean |
| M6 | 1 / 実在 | fields 節外の heading だけが混入する | clean |
| M7 | 1 / 実在 | 余剰 key だけを通す | clean |
| M8 | 1 / 2 node実在 | 欠落理由で指定2 nodeのみ赤 | clean |
| M9-prime | 1 / 実在 | 空 erratum 集合だけを通す | clean。ただし旧 resolver fallback の代替ではない |
| M10 | 1 / 実在 | fence 内 heading/boundary だけを可視化 | clean |
| M11 | 1 / 実在 | exact-13をexact-12へ緩和 | clean |
| M12 | 1 / 実在 | commit 型と mode を同時に無効化 | **過剰決定・分割必須** |
| P2 | 1 / 実在 | 承認 blobを7 keyへ過剰拒否。他 nodeへの静的波及なし | clean positive |
| P1（未登録） | candidate old=1 | 承認正例 node は明示 expected のため生存 | **未収録穴** |

登録 JSON の category は実際には `negative=13 / positive=1` であり、「positive 2件」ではない。

登録すべき追加変異は少なくとも次の4種である。

1. P1: exact-13定数へ `a14` を追加する過剰拒否。
2. 未知 ID を既存 validator へ登録する allowlist 拡張。
3. M12a: exact commit 型検査のみ無効化。
4. M12b: symlink mode 拒否のみ無効化。

加えて、必須 digest 引数を optional にして照合を省略する変異も、`test_expected_composed_sha256_is_required_keyword_only` の登録対象にすべきである。

## P1 疑義の判定

読みは半分正しい。

- 正しい点: 承認済み追補の正例は `require_exact_fields(blob, EXPECTED_FIELDS)` と明示渡ししている（test `:376-393`）。production 既定値で承認 blobを受理する既存 node はない。
- 誤りとなる点: B-1 が完全に無効というのは強すぎる。既定値経路自体は `test_default_exact_fields_constant_rejects_a13_missing` が呼び、さらに定数を literal 集合と比較している（`:321-327`）。したがって P1 は全 suite ではこの assert に殺されるが、「承認 blobの過剰拒否」を検出した kill ではない。
- 独立実行では、P1後の承認 blobは既定値呼出しで `MissingFieldsError({'a14'})`、明示 `EXPECTED_FIELDS` 呼出しでは成功した。

必要な最小テストは次である。

```python
def test_approved_addendum_is_accepted_by_default_exact_fields():
    blob = read_pinned_blob(REPOSITORY_ROOT, ADDENDUM_REF)
    assert preregistration.require_exact_fields(blob) is None
```

nodeid案:

`orchestrator/tests/test_t139_preregistration_binding.py::test_approved_addendum_is_accepted_by_default_exact_fields`

これなら P1 だけで承認済み追補が `MissingFieldsError(a14)` となり、過剰拒否として clean に KILL できる。

## 総括

**NO-GO**  
A2-5、B-1、B-5、B-6 は fix の `closed` 申告に反して `partial` で、M12も単一理由帰属を満たさない。  
親実測22 passedは基準版の緑であり、欠落したP1・registry・分割M12の mutation 証拠を補わない。