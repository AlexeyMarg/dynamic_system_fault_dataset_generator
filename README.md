# Dynamic systems fault dataset generator

Generator of datasets for linear dynamic systems under different types of Fault.

## Possible type of faults

- None
- Input (deviation of control signal)
- Output (deviation of measured output signals)
- Component (deviation of plant matrices)

## Possible forms of fault signals

- Stuck
- Multiplicative
- Constant

## Settings of generator

### Plant settings

- Matrices A, B, C, D
- Bounds of initial state
- Measurement noise mean and covariance
- Modeling and sampling time

### Fault settings

- Type
- Form
- Number of experiments
- Fault duration and start bounds
- Number of input or output for corresponding fault
- Bounds of component fault

### Input settings

- Constant ot harmonic
- Signal parameters

## Output

Desired number of csv-files with history of input signals, measured outputs anf fault statuses.

Fault statuses:
- 0 - None
- 1 - Stuck
- 2 - Multiplicative
- 3 - Constant