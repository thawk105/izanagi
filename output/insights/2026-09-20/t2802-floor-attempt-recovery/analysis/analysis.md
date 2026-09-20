## Run table

|run|valid|F|F_mid|W_max|W_0|busiest worker by shard|
|---|---|---|---|---|---|---|
|01-A|True|2664.032|403.658|498.337|498.337|[{"worker": "gw40", "duration_s": 424.088562032, "items": 79}, {"worker": "gw0", "duration_s": 166.089171733, "items": 50}, {"worker": "gw1", "duration_s": 137.522228477, "items": 2}]|
|02-B|False|—|—|—|—|[]|

02-B: gate metadata

|03-A|False|—|—|—|—|[]|

03-A: rc/copy_ok

|04-A|False|—|—|—|—|[]|

04-A: rc/copy_ok

|05-A|True|1853.036|399.356|487.978|487.978|[{"worker": "gw1", "duration_s": 417.55078347, "items": 13}, {"worker": "gw0", "duration_s": 179.332451751, "items": 50}, {"worker": "gw1", "duration_s": 135.713745619, "items": 2}]|
|06-B|True|2467.208|122.622|547.851|547.851|[{"worker": "gw2", "duration_s": 477.560505713, "items": 75}, {"worker": "gw0", "duration_s": 180.029583183, "items": 50}, {"worker": "gw2", "duration_s": 136.630459166, "items": 2}]|
|07-B|True|3014.828|125.604|455.477|455.477|[{"worker": "gw40", "duration_s": 383.264745407, "items": 43}, {"worker": "gw0", "duration_s": 176.992043037, "items": 50}, {"worker": "gw2", "duration_s": 160.018896851, "items": 2}]|
|08-A|True|1699.611|400.737|480.519|480.519|[{"worker": "gw1", "duration_s": 410.750668511, "items": 13}, {"worker": "gw0", "duration_s": 174.515902639, "items": 50}, {"worker": "gw1", "duration_s": 135.243063145, "items": 2}]|
|09-A|True|1987.328|400.797|455.835|455.835|[{"worker": "gw40", "duration_s": 385.185745577, "items": 8}, {"worker": "gw0", "duration_s": 171.811806099, "items": 50}, {"worker": "gw1", "duration_s": 137.171017727, "items": 2}]|
|10-B|True|3322.375|123.979|563.669|563.669|[{"worker": "gw40", "duration_s": 488.449006924, "items": 33}, {"worker": "gw0", "duration_s": 176.885711249, "items": 50}, {"worker": "gw2", "duration_s": 169.377177775, "items": 2}]|

## Pair table

|slot/attempt|runs|valid|ΔF|ΔF_mid|ΔW_max|ΔW_0|median Δ_n|n ≥ 3|sum ≥ 3|
|---|---|---|---|---|---|---|---|---|---|
|1/1|01-A, 02-B|False|—|—|—|—|—|—|—|

invalid run in adjacent pair

|1/2|03-A|False|—|—|—|—|—|—|—|

incomplete/nonadjacent pair, wrong slot/order, or half reuse

|1/3|04-A|False|—|—|—|—|—|—|—|

incomplete/nonadjacent pair, wrong slot/order, or half reuse

|1/4|05-A, 06-B|True|-614.172|276.734|-59.873|-59.873|0.000|65.000|291.471|
|2/1|07-B, 08-A|True|-1315.217|275.133|25.042|25.042|0.000|64.000|285.031|
|3/1|09-A, 10-B|True|-1335.047|276.818|-107.834|-107.834|0.000|64.000|286.182|


## Decision

effect-not-established

valid_pairs=3; total_runs=10; over_12_runs=False; median ΔF=-1315.217

JSON retains calculation precision; tables display three decimal places. Floor excludes added admission tests; shared scheduling and fixture effects remain.
