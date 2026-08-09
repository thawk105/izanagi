# 段 6 fix 3 巡目 裁定 (DW-O16 の上限巡)

親裁定。焦点再レビュー (`s6-refocus.md`) の残 must-fix 4 件を real と裁定し、F12〜F15 として閉じる。
**これが最終巡である。** 3 巡目後に残る所見は、親が変異で裏取りして real/refuted を裁定し閉じる。

親の実走 (`t3.log`) は現時点で **rc=0、26 passed、tree 汚染なし**。以下は退行させないこと。

## F12 — repo 外書込みを実効保証する (再レビュー #1)

現状は `tmp_path` の実体が repo 配下でないことを検査しておらず、E2E の subprocess は
`cwd=ROOT` で動くうえ `PYTHONDONTWRITEBYTECODE` も設定していないため、repo 内へ
`__pycache__` が生成される経路が残る (`-p no:cacheprovider` は `.pytest_cache` しか抑止しない)。

**裁定:**

1. 一時 root の `resolve()` が repo root 配下**でない**ことを assert する
2. 起動する全 subprocess の env に `PYTHONDONTWRITEBYTECODE=1` を設定する
3. subprocess へ渡す `--basetemp` も repo 配下でないことを固定する

## F13 — conftest コピーの検査を恒真でない形に直す (再レビュー #2)

`_copy_real_conftest()` は実ファイルをその場でコピーし、直後にコピー元と比較している。
**コピー元を変えても再コピーされるので常に一致する。陳腐化検査になっていない。**

**裁定: 恒真な assert と「陳腐化を検出する」という主張を撤去する。** 代わりに次の 2 点にする。

1. **subprocess 実行後**に、コピーした conftest が実 `conftest.py` と依然 byte 一致することを
   assert する (subprocess による変異の検出。コピー前後ではなく実行の前後で比較する)
2. 「実 conftest の hook 経路を通った」ことの根拠は **behavioral proof** に置く —
   digest marker が subprocess の stdout に現れることが、conftest の hook が
   自動 discovery 経由で走った証拠である。これをコメントと assert で明示する

**新しい機構を作らないこと。** 恒真な検査を「陳腐化検査」と呼ぶのをやめ、
実際に保証している内容へ名前と主張を合わせるのが本 F の目的である。

## F14 — 予算探索から manifest 再計算を外す (再レビュー #3)

block 描画は O(n) になったが、候補ごとに omitted 集合全体を sort・JSON 化・SHA-256 化して
おり、最悪 O(n² log n) である。

**裁定: 予算判定中は `omitted_manifest_sha256` を固定長 placeholder (64 文字) で
サイズ計算し、最終選択が確定した後に一度だけ実 manifest を生成する。**
placeholder と実 hash は同じ byte 長なので、会計行の byte 数は変わらない。
既存の block 描画回数カウンタに加え、**manifest 計算回数が選択件数に依存しない
(1 回である) ことを検査するテスト**を足せ。

## F15 — plain-runner probe を実際に repo root の外で走らせる (再レビュー #4)

`sys.path` から repo root を除いても、`cwd=ROOT` で `-c` 実行すると空文字 entry が
現 cwd を指すため repo root は import path に残る。**この probe は主張を実証していない。**

**裁定: 当該 probe を一時ディレクトリを cwd として起動し、`PYTHONPATH` も除去する。**
`_run_bounded_process()` に `cwd` を渡せるようにしてよい。probe が本当に
`ModuleNotFoundError(name="tools")` 経路を通り、digest が無言 fail-open することを固定せよ。

## 変異事前登録の再訂正 (再レビュー #5 を受けて。コード変更は不要)

`s6-fix-rulings.md` の M2 と M7 を次へ差し替える。M1・M3〜M6 は据え置き。

| ID | 変異位置 | 1 行変異 | 新テストの期待赤 |
|---|---|---|---|
| M2 | `conftest.py` の `_bounded_rendered_tail` | `reversed(value)` を forward iteration へ | (a), E2E |
| M7 | `conftest.py` の `pytest_runtest_logreport` の `if report.failed:` | `if False:` へ | (b) の実終了形テスト, E2E |

M7 は `pytest_collectreport` 側にも同名条件があるため、**`pytest_runtest_logreport` 側の行**に
一意化する。M3 の主な検出経路は consumer 抽出集合ではなく excerpt の literal assertion で
あることを台帳へ明記する (検出力の帰属を誇張しない)。

## 実走の要件

fix 2 巡目と同じく、次を**そのまま**実行し argv と結果を報告に書け。単一ファイルの実走で
緑を主張してはならない。実走の直前と直後の `git status --porcelain` が完全一致することも書け。

```
python3 -m pytest orchestrator/tests/test_pytest_failure_digest.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_real_repo_serialization.py
```

加えて、実走後に `find . -name __pycache__ -newer <実走開始時刻の基準ファイル>` 等で
**repo 内に新しい `__pycache__` が生じていないこと**を確認し、方法と結果を報告に書け。
