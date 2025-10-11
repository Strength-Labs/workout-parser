### Strength Coaching Markup Language v1.2

The Strength Coaching Markup Language provides a human-readable plain text format for strength and conditioning workouts **and nutrition assignments**. It serves as an intermediate format for a two-way data conversion process:

1.  **JSON to Text (`format_tool.py`):** Converts workout and nutrition data downloaded from the Turnkey Coach API (JSON format) into this markup language. This generated text includes prescribed sets, accomplished sets, and conversational comments between coach and client.
2.  **Text to JSON (`upload_tool.py`):** Converts workout programs and nutrition assignments written in this markup language back into the JSON format required by the Turnkey Coach API for uploading.

---

### Key Formatting Rules

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

#### Title

The first line after the date header (workout or nutrition), if it exists and is _not_ the name of an exercise, is the title of the assignment.

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

**Metrics work with both workout and nutrition assignments.** They are specified using the `@` symbol followed by the metric type, a colon, the value, unit, and optional notes.

* **Format**: `@metric_type: value unit [optional notes]`
* **Examples**:
    * `@weight: 185.5 lbs`
    * `@body_fat: 15.2%`
    * `@sleep: 7.5 hours feeling well-rested`
    * `@waist: 34 inches`
    * `@stress: 6 1-10 work deadline this week`

**Common Metric Types:**
* `weight` - Body weight (lbs or kg)
* `body_fat` - Body fat percentage (%)
* `waist`, `chest`, `arms`, `thighs` - Body measurements (inches or cm)
* `sleep` - Sleep duration (hours)
* `stress`, `recovery`, `energy` - Subjective scales (1-10)
* `calories` - Caloric intake (cal)
* `protein`, `carbs`, `fat` - Macronutrients (grams)
* Custom types can be used (e.g., `resting_hr`, `hrv`, `vertical_jump`, `water_intake`)

Metrics appear after the assignment title (if present) and before the exercises/nutrition items. They will be uploaded to the Turnkey Coach API along with the assignment data.

#### Exercises (Training Calendar)

For **Workout Date** assignments, exercises are training movements. The name of each exercise is on its own, unindented line. It must be a valid exercise name from `exerciselist.json` with `exercise_type: resistance` or `exercise_type: conditioning`.

* **Standard Example**: `Squat`
* **Failsafe by ID**: To avoid ambiguity with duplicate exercise names, you can specify the exercise by its numerical ID using the format `id: <exercise_id>`.
    * **Example**: `id: 7`

#### Nutrition Items (Nutrition Calendar)

For **Nutrition Date** assignments, nutrition items are meal/nutrition tracking tasks. The name of each item is on its own, unindented line. It must be a valid nutrition exercise name from `exerciselist.json` with `exercise_type: nutrition`.

* **Examples**:
    * `Meal Pictures`
    * `Visual Food Diary`
    * `Protein Intake`
    * `Calorie Tracking`

Nutrition items typically have instructions rather than sets/reps. Use indented notes to provide guidance (see **Comments and Notes** section below).

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

#### Accomplished Sets

When workout data is generated from the API via `json2markup.py`, the lifter's actual performance is displayed on an **unindented** line enclosed in parentheses `()`. The `workout_parser.py` script ignores these lines during upload. the '//' comments in the following example are explanatory only, and are not part of the markup language. 

* **Example:**
    ```
    Squat
    3x5 @ 405       // Assigned set prescription
    (1x5 @ 405)     // Accomplished set 1 recorded by lifter
    (1x4 @ 405)     // Accomplished set 2 recorded by lifter
    (1x5 @ 385)     // Accomplished set 3 recorded by lifter
    ```

#### Comments and Notes

* **Preserved Set Notes**: Any indented line that does *not* match the comment patterns below is treated as a custom note. The parser will attach this note to the preceding assigned set definition.
    * **Example**:
        ```
        Press
        3x5 @ 115
            This note is preserved and attached to the 3x5 Press set.
        ```

* **Ignored Comments**: These comments are for conversational purposes and are ignored by the `workout_parser.py` script during re-upload.
    * **Coach/Client Comments**: Lines beginning with a name in brackets.
        * Example: `[Coachy McCoach]: Great job on that lift!`
        * Example: `[Lifty McGee]: I felt a pinch in my shoulder.`
    * **Private Coach Notes**: Indented lines beginning with `>`.
        * Example: `> He should go up 5% on squats next week.`

#### Separators

Each individual workout block (representing a single day) should be separated by a horizontal rule `---`. The parser ignores this line.

---

### Sample Markup

This sample demonstrates various features of the markup language, including both training and nutrition calendar assignments.

#### Example 1: Training Calendar Workout

```markdown
Workout Date: 2025-10-01
Intensity Day

@weight: 185.5 lbs
@sleep: 7.5 hours
@recovery: 8 1-10

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
   [ Lifty McGee]: Better this week. The final AMRAP felt solid.

---

Workout Date: 2025-10-03

Run
1x25:00 @ RPE 7
    Try to maintain a consistent pace across the whole duration.

Sled Push Intervals
8x100 feet @ RPE 10

id: 7
3x10
```

#### Example 2: Nutrition Calendar Assignment

```markdown
Nutrition Date: 2025-10-01
Weekly Meal Plan - High Protein Focus

@weight: 185.5 lbs
@calories: 2800 cal daily target
@protein: 180 g target

Meal Pictures
    Upload photos of all meals and snacks throughout the day.
    Include timestamps for meal timing analysis.

Protein Intake
    Target: 180g protein daily
    Aim for 40g per meal, 4-5 meals per day

Visual Food Diary
    Log all food items with approximate portions
    Focus on hitting macros: 180g protein, 350g carbs, 85g fat
```

#### Example 3: Mixed File with Both Types

```markdown
Workout Date: 2025-10-01
Lower Body Strength

@weight: 185.5 lbs
@sleep: 7.5 hours

Squat
3x5 @ 405

Deadlift
1x5 @ 495

---

Nutrition Date: 2025-10-01
Monday Nutrition Plan

@calories: 2800 cal
@protein: 180 g

Meal Pictures
    Focus on breakfast and post-workout meal

Protein Intake
    Target 40g per meal

---

Workout Date: 2025-10-02
Upper Body

Bench Press
3x5 @ 315

Press
3x8 @ 135

---

Nutrition Date: 2025-10-02
Tuesday Nutrition - Lower Carb Day

@calories: 2400 cal
@carbs: 200 g

Visual Food Diary
    Track all meals for carb intake monitoring
```
