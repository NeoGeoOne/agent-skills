# Space-weather concepts — interpreting SWPC data

## The three NOAA scales (0/"none" = below level 1)

**G — Geomagnetic storms (from Kp):** G1=Kp5, G2=Kp6, G3=Kp7, G4=Kp8 (incl.
Kp 9−), G5=Kp9 (exactly 9.00).
| Level | Name | Effects | Aurora down to (geomag lat) | Freq/cycle |
|---|---|---|---|---|
| G1 | Minor | weak grid fluctuations | ~60° (n. Michigan/Maine) | 1700 |
| G2 | Moderate | high-lat voltage alarms; drag affects orbits | ~55° (New York/Idaho) | 600 |
| G3 | Strong | voltage corrections; surface charging; LEO drag | ~50° (Illinois/Oregon) | 200 |
| G4 | Severe | widespread voltage problems; tracking issues | ~45° (Alabama/n. California) | 100 |
| G5 | Extreme | possible grid collapse; transformer damage; sat-nav degraded days | ~40° (Florida/s. Texas) | 4 |

**R — Radio blackouts (from flare class):** R1=M1, R2=M5, R3=X1, R4=X10, R5=X20.
**Dayside-only and immediate** (X-rays ionize the D-layer; HF 3–30 MHz absorbed
while the flare lasts — minutes to ~hours; no advance warning possible). R3 =
wide-area dayside HF blackout ~1 h; GNSS only meaningfully hit at R4–R5.

**S — Solar radiation storms (≥10 MeV proton flux, pfu):** S1=10, S2=10²,
S3=10³, S4=10⁴, S5=10⁵. **Polar-focused, lasts days**: polar HF absorption,
aviation dose at high latitudes (S2+), satellite single-event upsets (S3+),
EVA hazard (S3+).

## Flare classes
Peak GOES 0.1–0.8 nm flux (W/m²), logarithmic ×10 per letter: A <1e-7, B, C, M
(1e-5), X (≥1e-4, open-ended; X2=2e-4). Suffix is linear (M5=5e-5, C3.7=3.7e-6).
A/B/C ≈ negligible; M → R1–R2; X → R3+ and often fast CMEs / proton events.

## Kp
0–9 global 3-hour index, reported in thirds (5− = 4.67, 5o = 5.00, 5+ = 5.33;
1-min JSON strings: `"5M"`=5−, `"5Z"`=5o, `"5P"`=5+). Real-time products use
**estimated** Kp (~8 stations); definitive Kp (GFZ Potsdam) arrives weeks later.
0–2 quiet, 3–4 unsettled/active, ≥5 storm (G1). `a_running` = linear a-index.

## Aurora visibility
| Kp | Geomag lat | Example locations |
|---|---|---|
| 3 | ~65° | Fairbanks, Tromsø, Iceland (routine) |
| 5 (G1) | ~60° | Oslo, Helsinki, Edmonton |
| 6 (G2) | ~57° | Stockholm, Glasgow, Calgary |
| 7 (G3) | ~55° | **Hamburg**, Copenhagen, Dublin, Seattle, Minneapolis |
| 8 (G4) | ~50° | London, Frankfurt, Chicago, Boston, Portland |
| 9 (G5) | ~45–50° | Munich/Vienna/Paris, n. California; historically ~40° |

Caveats that change answers:
- **Geomagnetic ≠ geographic.** The magnetic pole tilts toward North America:
  Edmonton (53.5°N geo) ≈ 60° geomag but Hamburg (53.6°N geo) ≈ only ~50°
  geomag — Hamburg realistically needs strong G3–G4, not G1. Approximate dipole
  conversion: `mlat = asin(sinφ·sinφ₀ + cosφ·cosφ₀·cos(λ−λ₀))`, pole ≈ 80.7°N,
  −72.7°E.
- Needs **darkness** (high-latitude aurora season ≈ late Aug–mid Apr; summer
  twilight kills it), clear skies, low light pollution; best ~22:00–02:00 local.
- For "should I go outside NOW": the OVATION 30-min grid
  (`/json/ovation_aurora_latest.json`), not Kp.

## Solar-wind drivers
- **Speed**: quiet 300–450 km/s; **>500–600 elevated**; CMEs can exceed 1000.
- **Bz (GSM)**: the master switch — sustained **southward (negative) Bz < −10 nT
  → G1–G2; < −20 nT → severe possible**. Northward Bz = weak coupling even in
  fast wind. High Bt (>15–20 nT) = high potential if it turns south.
- Timing: flare X-rays 8 min (radio blackout, no warning); protons tens of
  minutes–hours (S); **CMEs 1–3 days** (G storms — the forecastable ones); L1
  monitors (DSCOVR/ACE) give the final **15–60 min** warning. Coronal-hole
  high-speed streams recur on the ~27-day solar rotation.

## Sources & attribution
GOES satellites: X-rays (R) + protons (S); L1 spacecraft: solar wind; ground
magnetometer network: Kp (G). All NOAA SWPC data is US-government public
domain — credit "NOAA Space Weather Prediction Center". Real-time feeds are
preliminary. JPL side: credit NASA/JPL-Caltech.
