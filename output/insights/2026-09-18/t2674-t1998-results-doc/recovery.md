# T-2674 回収時の独立監査・是正

- authority: none / default_effect: no-state-change
- 起点: local main `b2037abfa1467507cf92c851c83f262239f81641`。
- 旧成果: `e3f4d277ff11471adf79a1b01ebfc637106260fb`。13 file、実装差分0。
- 回収用branch: `worktree-dev-wave-t2674-recovery-codex`。
- repo外一次記録: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-recovery-codex/`。

## 監査と裁定

独立Codex read-only監査は `verbatim/recovery-review.output.md`、promptも同directory。
launcher receiptは outcome=accepted / stop_reason=completed / validator_rc=0、13 model calls、wall 277.603秒。
記録modelはgpt-6-astra、effort medium。静的監査でありpytestやconsumer再実行ではない。
旧must-fix8の閉鎖、全40標本・8 median/CV・登録対のratio・改善率・原典hashが一致した。

| 所見 | 親裁定・対応 |
|---|---|
| 投入不存在の過剰断定 | real。READMEの読解上の追補で指定receiptとwave記録の範囲へ限定。凍結稿は維持 |
| insight末尾のJSON未保全断定 | real。insight §7で「参照保存先で未確認」へ追記訂正 |
| 旧受入を完了扱いする記述 | real。旧spool本文を訂正、insight §7で旧§5を撤回。rc70は不受理 |
| 完全な非帰属という親の推論 | 採用しない。test/probe変更なし・setup timeout・今回単独非再現までを記録。I/O根因は未分離 |
| 8点表の削除を着地条件にする | 不採用。推定量は登録2点に限定済みで、残りはproducer記録として表示 |

A-1の旧README差分はstale注記と同results表末尾の行追加。相手の未commit差分は回収しない。
mainに着地したA-1行があれば両方を保つ。旧T-2674成果の13 file以外の旧branch差分はない。

## 旧赤と今回の検査

旧 `acceptance-final-6.done=70`。同chainの3回は全てrc70。最終走のJUnitは
`ca6bf4a4062dfbc054d49ebf02fb703e` の2 testcaseを確認した。

- `test_r1_manifest_rejects_approval_that_does_not_equal_nonce`
- `test_submitter_preflight_parses_gen_s_semantic_state[enabled]`

共通module fixtureが `git ls-files --others --exclude-standard -z` の30秒TimeoutExpiredで失敗し、
assertion本文には未到達。旧tipと着手時mainで当該test/probeは同一。
回収木（HEAD=b2037abfa、旧docs13 fileをmergeしてstageした木）の単独file走は
`python3 tools/run_tests.py orchestrator/tests/test_t1259_qsub_env_delivery_probe.py -q`、
bounded local、51 passed / 12.23秒、rc0。ログは `verbatim/recovery-focus-t1259.log`。
これは最終受入全走ではない。timeout・fixture・除外は変えていない。
check_codex_agents / check_docs / spool_fold dry-runはrc0。

## 逐語の可逆正規化

DW-S07に従い、末尾ASCII spaceだけを除き、末尾LFを付した。可視文字と行順は不変。
原文は旧tipまたはrepo外job dirにも残す。下記の行番号は文書参照でなくbyte復元位置である。
復元は各指定行の末尾へ記載数のASCII spaceを戻し、final_newline=falseなら最終LFを除く。
元のbyte数・SHA-256と一致することを確認する。

```json
[
  {
    "path": "output/insights/2026-09-18/t2674-t1998-results-doc/verbatim/s6-review-lensA.output.md",
    "sha256": "7fb3cea5a2b6471188510030a8fded5c2379209c246ed41c363ce80bafb426d9",
    "bytes": 7229,
    "final_newline": false,
    "trailing": [
      [
        5,
        2
      ],
      [
        6,
        2
      ],
      [
        9,
        2
      ],
      [
        10,
        2
      ],
      [
        13,
        2
      ],
      [
        16,
        2
      ],
      [
        23,
        2
      ],
      [
        26,
        2
      ],
      [
        27,
        2
      ],
      [
        28,
        2
      ],
      [
        31,
        2
      ],
      [
        34,
        2
      ],
      [
        37,
        2
      ]
    ]
  },
  {
    "path": "output/insights/2026-09-18/t2674-t1998-results-doc/verbatim/s6-review-lensB.output.md",
    "sha256": "82066a24feaa1ea4d6648fac3f5cf0017bba18a6f7e3cda58924bffed4b0bdf8",
    "bytes": 9947,
    "final_newline": false,
    "trailing": [
      [
        15,
        2
      ],
      [
        34,
        2
      ],
      [
        49,
        2
      ],
      [
        66,
        2
      ],
      [
        85,
        2
      ],
      [
        91,
        2
      ],
      [
        101,
        2
      ]
    ]
  },
  {
    "path": "output/insights/2026-09-18/t2674-t1998-results-doc/verbatim/recovery-review.output.md",
    "sha256": "d2d096ff84fcc93f73cde6f32d1c3ac557b353eeb98ce18ccb7b3fd824432fab",
    "bytes": 6495,
    "final_newline": false,
    "trailing": [
      [
        7,
        2
      ],
      [
        8,
        2
      ],
      [
        9,
        2
      ],
      [
        12,
        2
      ],
      [
        13,
        2
      ],
      [
        14,
        2
      ],
      [
        17,
        2
      ]
    ]
  }
]
```
