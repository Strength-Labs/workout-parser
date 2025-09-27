### Strength Coaching Markup Language v1.1

The Strength Coaching Markup Language provides a human-readable plain text format for strength and conditioning workouts. It serves as an intermediate format for a two-way data conversion process:

1.  **JSON to Text (`json2markup.py`):** Converts workout data downloaded from the Turnkey Coach API (JSON format) into this markup language. This generated text includes prescribed sets, accomplished sets, and conversational comments between coach and client.
2.  **Text to JSON (`workout_parser.py`):** Converts workout programs written in this markup language back into the JSON format required by the Turnkey Coach API for uploading.

---

### Key Formatting Rules

#### Workout Date

Each workout begins with a `Workout Date:` line, followed by the date in YYYY-MM-DD format.

* **Example**: `Workout Date: 2025-08-18`

  
#### Workout Title
The first line after the workout date, if it exists and is _not_ the name of an exercise, is the title of the workout. 

#### Exercises

The name of each exercise is on its own, unindented line. It must be a valid exercise name from `exerciselist.json`.

* **Standard Example**: `Squat`
* **Failsafe by ID**: To avoid ambiguity with duplicate exercise names, you can specify the exercise by its numerical ID using the format `id: <exercise_id>`.
    * **Example**: `id: 7`

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

This sample demonstrates various features of the markup language.

```markdown
Workout Date: 2025-10-01
Intensity Day

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
