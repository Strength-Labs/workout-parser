### Strength Coaching Markup Language v2.1

The Strength Coaching Markup Language provides a human-readable plain text format for strength and conditioning workouts **and nutrition assignments**. It serves as an intermediate format for a two-way data conversion process:

1.  **JSON to Text (`format_tool.py`):** Converts workout and nutrition data downloaded from the Turnkey Coach API (JSON format) into this markup language. This generated text includes prescribed sets, accomplished sets, conversational comments between coach and client, and all associated metrics.
2.  **Text to JSON (`upload_tool.py`):** Converts workout programs and nutrition assignments written in this markup language back into the JSON format required by the Turnkey Coach API for uploading.

---

### Key Formatting Rules

#### Naming Requirements

> **Critical:** Names must match the official catalog. Stick to the canonical nutrition item titles from `exerciselist.json` (e.g., `Visual Food Diary`, `Calorie Tracking`) and metric tags that resolve to the Turnkey Coach metric catalog (`@weight`, `?waist`, `@sleep`, etc.). Any variation, abbreviation, or creative renaming will be treated as unknown data and skipped during upload.

Keep the reference lists from the Turnkey Coach app or internal guides nearby when drafting plans, and copy the entries verbatim—including spacing and capitalization.

#### Assignment Types

The markup language supports two types of assignments:

1. **Training Calendar Assignments** - Use `Workout Date:` header
2. **Nutrition Calendar Assignments** - Use `Nutrition Date:` header

Both types can be mixed in the same file and follow the same structural rules.

#### Workout Date

Each workout assignment begins with a `Workout Date:` line, followed by the date in YYYY-MM-DD format. This uploads to the **training calendar**.

* **Example**: `Workout Date: 2025-08-18`

#### Nutrition Date

Each nutrition assignment begins with a `Nutrition Date:` line, followed by the date in YYYY-MM-DD format. This uploads to the **nutrition calendar**.

* **Example**: `Nutrition Date: 2025-08-18`

> **Important for template generators/LLMs:** Never use `Workout Date:` for a nutrition entry. If the header is `Workout Date:`, the uploader treats the block as training and every nutrition item will be skipped. Always start nutrition blocks with `Nutrition Date: YYYY-MM-DD`.

#### Title

The first line after the date header (workout or nutrition), if it exists and is _not_ the name of an exercise or metric, is the title of the assignment.

* **Example for Workout**:
  ```
  Workout Date: 2025-08-18
  Upper Body Strength
  ```

* **Example for Nutrition**:
  ```
  Nutrition Date: 2025-08-18
  Weekly Meal Plan
  ```

#### Metrics

Metrics allow you to track client data such as body weight, body fat percentage, measurements, sleep, recovery scores, and other health/performance indicators. Metrics are associated with the date they appear under (either Workout Date or Nutrition Date).

**Metrics work with both workout and nutrition assignments.** There are two types of metrics distinguished by their leading symbol:

##### Prescriptive Metrics (Coach Assigns Targets)

Use the `@` symbol when the coach is setting a **target, goal, or recommendation** for the client to achieve.

* **Format**: `@metric_type: [NUMBER] unit [optional inline notes]`
* **Use for**: Targets, goals, recommendations that clients should aim for
* **Symbol meaning**: `@` = "at" (directive, "be at this level")

**Examples:**
```
@sleep: 8 hours target for recovery
@calories: 2400 cal daily target
@protein: 150 g daily goal
```

With indented notes:
```
@calories: 2800 cal daily target
    Higher than usual due to heavy training week
    Focus on post-workout meals

@protein: 180 g daily goal
```

##### Informational Metrics (Client Tracks/Reports)

Use the `?` symbol when the coach is **asking the client to report** their actual measurement or data.

* **Format**: `?metric_type: unit [optional inline notes]`
* **Use for**: Measurements, subjective ratings, actual data that only the client can provide
* **Symbol meaning**: `?` = question/inquiry (requesting information from client)

**Examples:**
```
?weight: kg morning weight, fasted
?waist: cm measure at navel
?stress: 1-10 current stress level
```

With indented notes:
```
?weight: lbs morning weight, fasted
    After bathroom, before eating
    Same time each day for consistency

?recovery: 1-10 how do you feel today?
    Overall body feeling, not just specific areas
    1 = completely exhausted, 10 = fully recovered

?energy: 1-10
```

##### Notes and Instructions for Metrics

Like exercises, metrics can have both **inline notes** (on the same line after the unit) and **indented notes** (on subsequent indented lines):

```
# Inline only
?weight: kg morning weight, fasted

# Indented only
?weight: kg
    Morning weight, fasted, post-bathroom

# Both inline and indented
?weight: kg morning weight, fasted
    Post-bathroom, before eating
    Same time each day for consistency

# Prescriptive with notes
@calories: 2800 cal higher than usual
    Heavy training week
    Focus on post-workout nutrition
```

All notes (inline and indented) are preserved during upload and download, providing context for both coach and client.

##### Client-Reported Metric Values

When workout data is downloaded from the API, the client's actual reported values are displayed in parentheses `()` on an unindented line immediately after the metric and its notes. The uploader ignores these lines during re-upload.

* **Format**: `(@metric_type: [CLIENT_VALUE] unit [optional notes])` or `(?metric_type: [CLIENT_VALUE] unit [optional notes])`
* **Examples**:

**Prescriptive metric with client response:**
```
@calories: 2400 cal daily target
(@calories: 2250 cal actual intake)

@sleep: 8 hours minimum for recovery
    Critical for CNS recovery
(@sleep: 7.5 hours)
```

**Informational metric with client response:**
```
?weight: kg morning weight, fasted
    After bathroom, before eating
(?weight: 82.3 kg)

?recovery: 1-10 how do you feel today?
(?recovery: 8 1-10)

?stress: 1-10 current stress level
[No client response - client skipped this metric]
```

**Key Distinction:**
- **`@metric:`** = Coach assigns a target/goal (prescriptive)
- **`?metric:`** = Coach asks for data (informational/inquiry)
- **`(@metric:)`** or **`(?metric:)`** = Client's actual reported value (only appears when client enters data)
- **No parentheses** = Client did not provide a value

**Complete Round-Trip Example:**

Coach uploads:
```
Workout Date: 2025-10-18

@calories: 3000 cal post-training day
?weight: lbs morning weight, fasted
    After bathroom, before eating
?recovery: 1-10 how do you feel?
```

Client completes in app (enters: calories 2850, weight 186.2, recovery 8)

Downloaded back:
```
Workout Date: 2025-10-18

@calories: 3000 cal post-training day
(@calories: 2850 cal)

?weight: lbs morning weight, fasted
    After bathroom, before eating
(?weight: 186.2 lbs)

?recovery: 1-10 how do you feel?
(?recovery: 8 1-10)
```

**Common Metric Types:**

| Metric | Typical Use | Symbol | Example |
|--------|-------------|--------|---------|
| `weight` | Body weight (lbs or kg) | Usually `?` | `?weight: kg fasted` |
| `body_fat` | Body fat percentage (%) | Usually `?` | `?body_fat: %` |
| `waist`, `chest`, `arms`, `thighs` | Body measurements | Usually `?` | `?waist: cm at navel` |
| `sleep` | Sleep duration (hours) | Either `@` or `?` | `@sleep: 8 hours` or `?sleep: hours` |
| `stress`, `recovery`, `energy` | Subjective scales (1-10) | Usually `?` | `?stress: 1-10` |
| `calories`, `protein`, `carbs`, `fat` | Nutrition targets | Usually `@` | `@calories: 2400 cal` |
| Custom metrics | Any trackable data | Either | `?resting_hr: bpm` or `@water: 128 oz` |

**Metric Placement:**

Metrics appear after the assignment title (if present) and before the exercises/nutrition items. They will be uploaded to the Turnkey Coach API along with the assignment data.

> **Exact naming matters:** Metrics must map to existing catalog entries in Turnkey Coach (e.g., `Body Weight`, `Waist (in)`, `Sleep Hours`). The parser supports fuzzy matching and aliases (e.g., `@weight:` maps to "Body Weight"), but ambiguous names may be skipped. Stick to canonical names from the metrics catalog.

> **Backwards Compatibility:** The old syntax `@metric:` without a value (for tracking metrics) is still supported but deprecated. New files should use `?metric:` for informational/tracking metrics to avoid ambiguity.

#### Exercises (Training Calendar)

For **Workout Date** assignments, exercises are training movements. The name of each exercise is on its own, unindented line. It must be a valid exercise name from `exerciselist.json` with `exercise_type: resistance` or `exercise_type: conditioning`.

* **Standard Example**: `Squat`
* **Failsafe by ID**: To avoid ambiguity with duplicate exercise names, you can specify the exercise by its numerical ID using the format `id: <exercise_id>`.
    * **Example**: `id: 7`

#### Nutrition Items (Nutrition Calendar)

For **Nutrition Date** assignments, nutrition items are meal/nutrition tracking tasks. Each item:

* **Must** be a valid entry from `exerciselist.json` whose `exercise_type` is `nutrition`. Training or conditioning exercises will be skipped automatically.
* Appears on its own unindented line, just like workouts do.
* Does **not** use prescribed sets, reps, load, distance, or time. Nutrition entries accept notes only.

* **Examples**:
    * `Meal Pictures`
    * `Visual Food Diary`
    * `Protein Intake`
    * `Calorie Tracking`

> **Tip:** If you need to create a new nutrition item, add it to the Turnkey Coach exercise catalog first (marking it as `exercise_type: nutrition`). Once the catalog is updated, the uploader will accept the name in your markup.

> **Exact naming matters:** Use the nutrition item names verbatim (e.g., `Visual Food Diary`, `Instructions`, `Meal Pictures`). Changing singular/plural forms or capitalization (such as `Instruction`) creates an unknown exercise that the uploader will skip. Keep a reference list of approved nutrition items handy when generating templates.

Nutrition items typically have instructions rather than sets/reps. Use indented notes to provide guidance (see **Comments and Notes** section below). Any line that looks like a traditional set prescription (`3x10 @ ...`, `5x00:30`, etc.) will be ignored for nutrition assignments, so keep coaching cues and expectations in note form.

> **LLM Hint:** When generating nutrition plans, follow this pattern exactly:
> ```
> Nutrition Date: 2025-10-13
> Title (optional)
> @metric: ... or ?metric: ...
> Nutrition Item Name
>     Guidance/notes (indented)
> ```
> Using `Workout Date:` or adding set prescriptions will cause the uploader to drop the nutrition items.

#### Exercise Groups (Pick-One Families)

An **exercise group** (also called an exercise family) is a coach-built bundle of exercises from which the client picks one per session. Use a `Group:` block when you want the client to choose between several movement options.

**Syntax:**

```
Group: <group name>
    <member exercise 1>
    <member exercise 2>
    <member exercise 3>
<prescribed sets line>
    <optional notes>
```

**Rules:**
- `Group:` must be unindented (same level as a regular exercise name)
- The group name must **exactly match** a group in the coach's exercise group catalog (same casing, same spacing). If the name is not found, the uploader will error.
- Indented lines directly after `Group:` are member exercise names — they are displayed for reference but are **not sent to the API separately**. You do not need to list members when writing new workouts (the group already exists in TKC); listing them is optional but helpful for readability.
- The prescribed sets line follows the same format as a regular exercise (weight-based, RPE-based, time-based, etc.)
- Notes work the same as for regular exercises (indented lines after the sets line)

**Upload example (coach writes):**

```
Workout Date: 2026-05-10
Lower Body Day

Group: Horizontal Push
    Floor Press 1.5
    Tempo Floor Press
    Crush Press
3 x 8 @ 25 lbs
    Pick the variation that matches your equipment today.
```

**Minimal form (members omitted — also valid):**

```
Workout Date: 2026-05-10

Group: Horizontal Push
3 x 8 @ 25 lbs
```

**Downloaded form (after client picks):**

When workout history is downloaded, groups render in full with the client's pick shown in parentheses:

```
Group: Horizontal Push
    Floor Press 1.5
    Tempo Floor Press
    Crush Press
(picked: Crush Press)
3 x 8 @ 25 lbs
(1x8 @ 25)
(1x8 @ 25)
(1x8 @ 25)
```

The `(picked: X)` line is ignored on re-upload, just like accomplished sets.

> **LLM Hint:** To assign an exercise group, use `Group: <exact group name>` followed by the sets line. Do **not** use the regular exercise name format for groups — using the exercise name alone assigns a single specific exercise, not a group pick. Only use group names that exist in the coach's TKC exercise group catalog. If unsure, list the group name and note that the coach should verify it matches their catalog exactly.

> **Important for LLMs analyzing history:** A `Group:` block with `(picked: X)` means the client already selected exercise X for that session. Treat the picked exercise as the actual movement performed. The group members listed above are the available options, not additional exercises in the workout.

#### Prescribed Sets

The prescribed number of sets, reps, weight, time, or distance are represented on a single, unindented line following the exercise name.

**Resistance Training Formats:**

* **Weight-Based:** `[sets] x [reps] @ [weight]`
    * Example: `3x5 @ 405` (or `3x5 @ 405 lbs`)
* **Percentage-Based:** `[sets] x [reps] @ [percentage]%`
    * Example: `2x5 @ 85%`
* **RPE-Based:** `[sets] x [reps] @ RPE [value]`
    * Example: `1x5 @ RPE 9`
* **AMRAP (As Many Reps As Possible):** Replace reps with `AMRAP`.
    * Example: `1xAMRAP @ 315`

**Conditioning Training Formats:**

* **Time-Based:** `[sets] x [duration] @ [intensity]`
    * Duration format can be `MM:SS` or `HH:MM:SS`. Intensity (e.g., `@ RPE 7`) is optional.
    * Example 1 (Time and Intensity): `1x20:00 @ RPE 7`
    * Example 2 (Time Intervals): `3x1:30`
* **Distance-Based:** `[sets] x [distance] [unit] @ [intensity]`
    * Supported units include `m` (meters), `km` (kilometers), `miles` (or `mi`), `yards`, `feet`. Intensity is optional.
    * Example 1 (Distance Intervals): `5x400m @ RPE 10`
    * Example 2 (Single Distance Run): `1x3 miles`

#### Accomplished Sets and Completion Logic

When workout data is generated from the API via `format_tool.py`, the lifter's actual performance is displayed on **unindented** lines enclosed in parentheses `()`. The `upload_tool.py` script ignores these lines during upload.

##### Completion Status Rules

The markup language uses two patterns to indicate exercise completion status for **past workouts** (dates on or before today):

1. **Parenthetical Sets Present = Exercise Was Performed**

   If parenthetical sets `()` appear below the prescription, **ONLY those sets were actually performed**.

   ```
   Squat
   3x5 @ 405           // Prescribed 3 sets
   (1x5 @ 405)         // Actually completed set 1
   (1x5 @ 405)         // Actually completed set 2
   (1x5 @ 405)         // Actually completed set 3
   ```

   If the actual sets differ from prescription:
   ```
   Squat
   3x5 @ 405           // Prescribed 3 sets
   (1x5 @ 405)         // Actually completed set 1
   (1x4 @ 405)         // Actually completed set 2 (only got 4 reps)
   ```
   In this example, only 2 sets were attempted (the third set was not done), and the second set only achieved 4 reps instead of the prescribed 5.

2. **`(skipped)` = Exercise Not Performed**

   If the notation `(skipped)` appears, the **entire exercise was not performed**.

   ```
   Bench Press
   3x5 @ 225
   (skipped)
   ```
   This explicitly marks that the exercise was skipped, either intentionally or due to injury/time constraints.

   **Important**: An exercise with NO parenthetical notation in downloaded workout history means it was skipped and will be marked as `(skipped)` by the formatter.

3. **Future Workouts (Not Yet Due)**

   Workouts with dates after today are planned programming that has not yet been performed. These workouts include a special private coach note:

   ```
   Workout Date: 2025-11-05
   	> Future workout (not yet completed)

   Squat
   3 x 5 @ 225 lbs

   Press
   3 x 5 @ 115 lbs
   ```

   **Important for LLMs/AI workout generation:**
   - Workouts with `> Future workout (not yet completed)` show planned programming, not historical performance
   - Do not treat these as evidence of completed work or performance trends
   - Use them to understand programming context, periodization, and upcoming training phases
   - Only past workouts (without this notation) represent actual training history

##### Accomplished Sets Examples

**Example 1: All sets completed as prescribed**
```
Deadlift
1x5 @ 495
(1x5 @ 495)
```

**Example 2: Partial completion with modifications**
```
Squat
3x5 @ 405           // Prescribed
(1x5 @ 405)         // Completed set 1 as prescribed
(1x5 @ 405)         // Completed set 2 as prescribed
(1x5 @ 385)         // Completed set 3 but reduced weight
```

**Example 3: Failed to complete all prescribed sets**
```
Press
5x5 @ 135           // Prescribed 5 sets
(1x5 @ 135)         // Completed
(1x5 @ 135)         // Completed
(1x3 @ 135)         // Only got 3 reps on set 3
```
The lifter only completed 3 sets total (sets 4 and 5 were not attempted).

**Example 4: Exercise completely skipped**
```
Chin-Up
3xAMRAP @ 0
(skipped)
    Shoulder felt tweaky, skipped to be safe
```

**Example 5: Client exceeded prescription**
```
Curls
2x12 @ 45           // Prescribed 2 sets
(1x12 @ 45)         // Completed set 1
(1x12 @ 45)         // Completed set 2
(1x10 @ 45)         // Client added a third set
```

##### Important Notes for LLM Analysis

When analyzing training history to inform workout design:

- **Parenthetical sets present** = Exercise was performed (use this data for training analysis)
- **Parenthetical sets with modifications** (weight changes, rep failures) = Adaptation or fatigue signals
- **Fewer parenthetical sets than prescribed** = Incomplete workout (fatigue, time, or injury)
- **`(skipped)` notation** = Exercise was not performed (injury, equipment, or time constraints)
- **No parenthetical notation** = Exercise was skipped (same as `(skipped)`)

This completion tracking allows AI systems to:
- Identify patterns of fatigue or overreaching (frequent rep failures)
- Detect injury concerns (specific exercises consistently skipped or modified)
- Assess program adherence (how often workouts are completed as prescribed)
- Adjust future programming based on actual performance vs. prescription
- **Only use exercises with parenthetical sets for estimating 1RMs and tracking progress**

#### Comments and Notes

* **Preserved Set/Metric Notes**: Any indented line that does *not* match the comment patterns below is treated as a custom note. The parser will attach this note to the preceding assigned set definition or metric.
    * **Example (exercise notes)**:
        ```
        Press
        3x5 @ 115
            This note is preserved and attached to the 3x5 Press set.
        ```
    * **Example (metric notes)**:
        ```
        ?weight: kg
            Morning weight, fasted, post-bathroom
            Same time each day for consistency
        ```

* **Ignored Comments**: These comments are for conversational purposes and are ignored by the `upload_tool.py` script during re-upload.
    * **Coach/Client Comments**: Lines beginning with a name in brackets.
        * Example: `[Coachy McCoach]: Great job on that lift!`
        * Example: `[Lifty McGee]: I felt a pinch in my shoulder.`
    * **Private Coach Notes**: Indented lines beginning with `>`.
        * Example: `> He should go up 5% on squats next week.`

#### Separators

Each individual workout block (representing a single day) should be separated by a horizontal rule `---`. The parser ignores this line.

---

### Sample Markup

This sample demonstrates various features of the markup language, including both training and nutrition calendar assignments with the new metric syntax.

#### Example 1: Training Calendar Workout

```markdown
Workout Date: 2025-10-18
Heavy Lower Body

@sleep: 8 hours minimum for recovery
    Critical for CNS recovery after heavy squats

@calories: 3000 cal post-training day

?weight: lbs morning weight, fasted
    After bathroom, before eating
    Same time each day for consistency

?recovery: 1-10 how do you feel today?
    Overall body feeling, not just legs

?soreness: 1-10 lower body only

Squat
3x5 @ 405
    Keep your chest up and focus on hitting depth.
(1x5 @ 405)
(1x5 @ 405)
(1x5 @ 405)

Bench Press
2x5 @ 85%
1x5 @ RPE 8
1xAMRAP @ 200
(1x7 @ 200)
   > Client reported left shoulder discomfort last week. Check video closely.
   [Coachy McCoach]: How did this feel compared to last week?
   [Lifty McGee]: Better this week. The final AMRAP felt solid.

---

Workout Date: 2025-10-20
Active Recovery

?weight: lbs
?energy: 1-10 average throughout day
?sleep: hours last night

Run
1x25:00 @ RPE 7
    Try to maintain a consistent pace across the whole duration.

Sled Push Intervals
8x100 feet @ RPE 10
```

#### Example 2: Nutrition Calendar Assignment

```markdown
Nutrition Date: 2025-10-18
Weekly Meal Plan - High Protein Focus

@calories: 2800 cal daily target
    Higher than usual due to heavy training week
    Focus on post-workout nutrition

@protein: 180 g daily goal
@carbs: 300 g
@fat: 85 g

?weight: kg morning weight, fasted
    Post-bathroom, before eating
    Same time each day for consistency

?sleep: hours last night
?hunger: 1-10 throughout the day
?energy: 1-10 average energy level

(@calories: 2650 cal)
(?weight: 84.2 kg)
(?sleep: 7.5 hours)
(?energy: 8 1-10)

Meal Pictures
    Upload photos of all meals and snacks throughout the day.
    Include timestamps for meal timing analysis.

Protein Intake
    Target: 180g protein daily
    Aim for 40g per meal, 4-5 meals per day

Visual Food Diary
    Log all food items with approximate portions
    Focus on hitting macros: 180g protein, 300g carbs, 85g fat
```

#### Example 3: Mixed File with Both Types

```markdown
Workout Date: 2025-10-18
Lower Body Strength

@sleep: 8 hours
?weight: lbs fasted
?recovery: 1-10

Squat
3x5 @ 405

Deadlift
1x5 @ 495

---

Nutrition Date: 2025-10-18
Monday Nutrition Plan

@calories: 2800 cal
@protein: 180 g

?weight: kg
?hunger: 1-10 throughout day

Meal Pictures
    Focus on breakfast and post-workout meal

Protein Intake
    Target 40g per meal

---

Workout Date: 2025-10-19
Upper Body

?weight: lbs
?soreness: 1-10

Bench Press
3x5 @ 315

Press
3x8 @ 135

---

Nutrition Date: 2025-10-19
Tuesday Nutrition - Lower Carb Day

@calories: 2400 cal
@carbs: 200 g

?energy: 1-10
?hunger: 1-10

Visual Food Diary
    Track all meals for carb intake monitoring
```

#### Example 4: Metrics with Various Note Styles

```markdown
Workout Date: 2025-10-18

# Prescriptive metric with inline note only
@sleep: 8 hours minimum for recovery

# Prescriptive metric with indented notes only
@calories: 3000 cal
    Post-training day
    Focus on protein timing

# Informational metric with inline note only
?weight: kg morning weight, fasted

# Informational metric with indented notes only
?recovery: 1-10
    Overall body feeling
    Rate honestly, not just what you think I want to hear

# Informational metric with both inline and indented notes
?soreness: 1-10 lower body only
    Focus specifically on quads and glutes
    1 = no soreness, 10 = can barely walk

# Mix of both types
@protein: 180 g daily goal
?stress: 1-10 current stress level
    Work, family, training combined

Squat
5x5 @ 315
```

---

### Version History

**v2.2 (2026-05-09)**
- **NEW:** Added `Group:` block syntax for exercise group (exercise family) assignments
- Groups render in downloaded history with all member options listed and `(picked: X)` when client has selected
- Uploader resolves group name against local exercise group catalog (`exercisegrouplist.json`) — group must exist in TKC
- Added LLM guidance for generating and interpreting group blocks

**v2.1 (2025-11-01)**
- **NEW:** Added `(skipped)` notation to explicitly mark exercises that were not performed
- **BREAKING CHANGE:** Simplified completion status rules:
  - Parenthetical sets present = exercise was performed
  - `(skipped)` or no parentheses = exercise was not performed
  - Removed assumption that "no parentheses = completed as prescribed"
- **NEW:** Format tool now automatically marks exercises as `(skipped)` when they have no actual_sets data
- **NEW:** PR tool skips exercises with no actual_sets from 1RM calculations
- Added comprehensive examples for partial completion, rep failures, and exercise skipping
- Added LLM-specific guidance for analyzing completion patterns in training history

**v2.0 (2025-10-18)**
- Added `?metric:` syntax for informational/tracking metrics (client reports data)
- Clarified `@metric:` is for prescriptive metrics (coach assigns targets)
- Added support for both inline and indented notes on metrics
- Improved round-trip examples showing client responses
- Backwards compatibility maintained for legacy `@metric:` syntax without values

**v1.2 (Previous)**
- Added nutrition calendar support
- Added metrics with `@` symbol
- Mixed workout and nutrition file support
