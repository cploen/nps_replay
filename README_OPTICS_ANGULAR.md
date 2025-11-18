# NPS HMS Optics – Angular Optimization Workspace

**Branch:** `optics-angular-  
**Purpose:** Long-term experimental development of angle reconstruction (xptar, yptar, xtar, ytar) for HMS/NPS optics.

This branch is NOT meant to merge into `develop.  It's a sandbox with Christine's angles updated within standard_coin.kinematics,
and zeroth order offsets added or removed as needed for the SVD process.   
It is safe to keep exploratory work, notes, failures, and scratch development here.

---

## Goals

- Optimize reconstruction of angular variables (xptar, yptar).
- Hold stable version of HMS spectrometer angle measurements- clearly indicated - in standard_coin.kinematics

---

## Strategy

1. **Start from upstream `develop` matrix.**
2. Replay optics runs using best available matrix (already optimized once using NPS sieve hole cuts), *with* zero order angular elements in place, 0th order delta removed
3. Run through optics optimization using existing sieve cuts
   - check that cuts still align, but they should, there's been no significant change that could affect this.
   - Recalculate matrix, compare zeroth order elements, compare final results.  This iteration 
      - Fixes ztar position (+/- 8cm instead of +/- 7.5 cm)
      - opens us to the rastered beam position instead of average.
4. Finalize angular matrix for NPS
   - Replay using *new* final angular matrix, and no zeroth order terms in delta, and move on to delta optimization.
   - Push updated matrix and zeroth order elements to this repo, delta repo, develop, and origin (JeffersonLab/nps_replay)
---

---

## Log of Experiments

### [DATE]

### [DATE]

---

## To-Do

- [ ]

---

## Final Output (when ready)


