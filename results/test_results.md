
# Test Results

Run the tests on your machine using:

```bash
python -m unittest discover -s tests -v
```

## Test cases

| Test | Expected result |
|---|---|
| UCS finds a schedule | Pass if a legal complete schedule exists |
| A* finds a schedule | Pass if a legal complete schedule exists |
| UCS and A* cost comparison | Equal minimum costs |
| CSP schedule validation | Complete valid assignment |
| Capacity query | Correct true/false inference |
| Room/time collision detection | Invalid schedule detected |

## Actual results

Fill in this section after running the tests on your computer.

Do not report tests as passed until they have actually run.
