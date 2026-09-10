# T-2581 / T-2548 / T-2182 再投入条件

根拠はD1936項1・2と今回のユーザー指示。旧trace v1で停止した評価を、新pinと既存verifier v2で1本だけ再投入する。

- CCBench: `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
- 実行: 固定SHA専用checkout、既存 `tools/pegasus/p3_s4_loop_pegasus.sh`、Pegasus計算ノード。
- K2材料: 前回job root `dev-wave-t2182-k2-eval-run/materials/` の `knowledge-manifest-wal-only.json` と `proposal-wal-only.json`。
- ファイルSHA-256: manifest `68eb3d5f4bcdab1e91a379868d188493bda548c5f26d6c3965a00dc5c9a70977`、proposal `6aaeab4d87e330efd872141958906799dcc72c3c16fcdebd338be7f3b4419248`。
- resolverのmanifest digestは `396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`。ファイルbytesのhashとは異なる。
- 知識源はcommit `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の測定WAL1件。source digestは `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`。
- proposalは前回role出力を無変更で再利用し、値20を評価する。新しいrole合成や比較arm追加は行わない。
- 呼び手宣言は `reproduction_or_selection` / `de_novo_claim=false`。
- scaleは既存defaultのrecords=100000、threads=4、extime=1、reps=2。配線規模の評価で、headline性能やK2の因果的効果を主張しない。
- 判定は新campaignのWAL・verifier出力で確認する。job rc=0やcheckpointだけでterminal取得としない。trace parse errorやbuild abortでは第4条件未達。
- anomaly検出時のreject、trace/perf別build、K2指示検出を維持する。過去campaign・過去判定は再ラベルしない。

静的に導出された新K2 campaign IDは `p3-s4-loop-s4-autonomous-409e13f8`。実走のIDとterminalは実測後のREADMEへ記録する。
